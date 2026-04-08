use crate::core::logic::constants::{CHOICE_DONE, TARGET_SLOT_AREA_IDX};
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::suspension::finish_pending_interaction;
use crate::core::logic::models::{AbilityFrameComponents, Ability};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState, Zone};
use crate::core::enums::ChoiceType;
use crate::core::{O_MOVE_TO_DISCARD, O_NOP};
use super::super::HandlerResult;

fn prompt_ctx_for_target(ctx: &AbilityContext, target_player_idx: usize) -> AbilityContext {
    let mut prompt_ctx = ctx.clone();
    prompt_ctx.player_id = target_player_idx as u8;
    prompt_ctx
}

pub fn handle_move_to_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let p_idx = ctx.player_id as usize;
    let discard = frame_data.semantic_discard_spec();
    
    // Resolve count (handle compare_accumulated and UNTIL_SIZE)
    let v = if frame_data.uses_total_cost_budget() {
        let count_op = discard.embedded_count_opcode.unwrap_or(discard.suspend_slot);
        resolve_count(state, db, count_op, frame_data.count_filter_attr(), p_idx as i32, ctx, 0) as i32
    } else {
        discard.requested_count
    };
    
    let base_p = ctx.activator_id as usize;
    let slot = frame_data.slot;
    let mut source_zone = discard.source_zone;
    
    // Determine target player from slot
    let target_filter = CardFilter::from_attr(discard.filter_attr);
    let target_player_idx = match target_filter.target_player {
        x if x == crate::core::generated_constants::TARGET_PLAYER_OPPONENT as u8 => 1 - base_p,
        x if x == crate::core::generated_constants::TARGET_PLAYER_BOTH as u8 => base_p,
        _ if slot.is_opponent => 1 - base_p,
        _ => base_p,
    };

    // Handle UNTIL_SIZE operation (discard down to N cards) - inlined
    let count = if (v as u32 & (1 << 31)) != 0 {
        let target_size = v & 0x7FFFFFFF;
        let current_size = match source_zone {
            Zone::Hand => state.players[target_player_idx].hand.len(),
            Zone::Stage => state.players[target_player_idx].stage.iter().filter(|&&c| c >= 0).count(),
            Zone::Discard => state.players[target_player_idx].discard.len(),
            Zone::Deck | Zone::DeckTop | Zone::DeckBottom => state.players[target_player_idx].deck.len(),
            _ => 0,
        };
        (current_size as i32 - target_size).max(0)
    } else {
        v
    };
    
    // Special case: Stage UNTIL_SIZE means Hand
    if source_zone == Zone::Stage && discard.is_until_size_operation {
        source_zone = Zone::Hand;
    }

    // Immunity check
    if target_player_idx != p_idx && state.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY) {
        return HandlerResult::Continue;
    }

    let filter_attr = discard.filter_attr;
    let is_optional = discard.is_optional;

    // Handle skip of optional discard (CHOICE_DONE = user declined)
    if is_optional && ctx.choice_index == CHOICE_DONE {
        return HandlerResult::Return;
    }

    let mut next_ctx = ctx.clone();
    let choice_type = if source_zone == Zone::Hand { 
        ChoiceType::SelectHandDiscard 
    } else { 
        ChoiceType::SelectDiscard 
    };
    
    // Calculate available cards - inlined from zone_available_count
    let available_count = match source_zone {
        Zone::Hand => state.players[target_player_idx].hand.len(),
        Zone::Stage => state.players[target_player_idx].stage.iter().filter(|&&c| c >= 0).count(),
        Zone::Discard => state.players[target_player_idx].discard.len(),
        Zone::Deck | Zone::DeckTop | Zone::DeckBottom => state.players[target_player_idx].deck.len(),
        _ => 0,
    } as i32;

    // Self-discarding from a stage ability should always resolve against the
    // activated member itself, not ask the player to choose another stage slot.
    let self_stage_discard = source_zone == Zone::Stage
        && frame_data.slot.target_slot == TARGET_SLOT_AREA_IDX as u8
        && ctx.area_idx >= 0
        && ctx.area_idx < 3;

    if self_stage_discard {
        let idx = ctx.area_idx as usize;
        if let Some(removed_cid) = remove_card_at_index(state, target_player_idx, Zone::Stage, idx, discard.allow_under_member_selection) {
            state.players[target_player_idx].push_discard_card(removed_cid);
            let mut next_ctx = ctx.clone();
            next_ctx.selected_cards.push(removed_cid);
            next_ctx.v_remaining = (count - 1).max(0) as i16;
            ctx.selected_cards = next_ctx.selected_cards.clone();
            ctx.v_accumulated = next_ctx.selected_cards.len() as i16;
            ctx.choice_index = -1;
            ctx.v_remaining = -1;

            let should_tap_self = db.get_live(removed_cid).is_some()
                && ctx.area_idx >= 0
                && source_ability(db, ctx).map(|ability| {
                    ability.effects.iter().any(|effect| {
                        effect.runtime_opcode == O_NOP
                            && effect.params.get("raw_effect").and_then(|v| v.as_str()) == Some("TAP_SELF")
                    })
                }).unwrap_or(false);

            if should_tap_self {
                state.players[p_idx].set_tapped(ctx.area_idx as usize, true);
            }

            state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &[removed_cid]);
            return HandlerResult::Continue;
        }
    }

    // === Prompt phase: determine if we need player input ===
    if next_ctx.choice_index == -1 {
        // Not enough cards available
        if available_count < count || available_count == 0 {
            return HandlerResult::Continue;
        }

        // Auto-pick when forced (only 1 valid choice and not optional)
        if !is_optional && count == 1 && available_count == 1 {
            next_ctx.choice_index = 0;
        } else if is_optional && is_deck_zone(source_zone) {
            let prompt_ctx = prompt_ctx_for_target(&next_ctx, target_player_idx);
            // Optional deck discard - ask yes/no
            if matches!(
                suspend_choice(state, db, &prompt_ctx, &prompt_ctx, frame_idx, O_MOVE_TO_DISCARD, discard.suspend_slot, ChoiceType::Optional, filter_attr, count as i16),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else if count > 0 && !is_deck_zone(source_zone) {
            let prompt_ctx = prompt_ctx_for_target(&next_ctx, target_player_idx);
            if matches!(
                suspend_choice(state, db, &prompt_ctx, &prompt_ctx, frame_idx, O_MOVE_TO_DISCARD, discard.suspend_slot, choice_type, discard.prompt_filter_attr, count as i16),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }
    }

    // Handle optional deck discard "no" choice
    if is_optional && is_deck_zone(source_zone) && next_ctx.choice_index == 0 {
        next_ctx.choice_index = -1;
    }

    // === Execute the discard ===
    let mut moved_cards = Vec::new();

    if next_ctx.choice_index != -1 {
        // === Multi-select discard path ===
        // Handle optional skip
        if is_optional && next_ctx.choice_index == CHOICE_DONE {
            finish_pending_interaction(state);
            return HandlerResult::Return;
        }

        // Handle CHOICE_DONE with remaining cards
        if next_ctx.choice_index == CHOICE_DONE {
            if next_ctx.v_remaining > 0 || (next_ctx.v_remaining == -1 && count > 0) {
                let remaining = if next_ctx.v_remaining > 0 { next_ctx.v_remaining } else { count as i16 };
                let prompt_ctx = prompt_ctx_for_target(&next_ctx, target_player_idx);
                if matches!(
                    suspend_choice(state, db, &prompt_ctx, &prompt_ctx, frame_idx, O_MOVE_TO_DISCARD, discard.suspend_slot, choice_type, discard.prompt_filter_attr, remaining),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
            return HandlerResult::Continue;
        }

        // Remove selected card by index - inlined from remove_card_by_index
        let idx = next_ctx.choice_index as usize;
        let allow_under_member = discard.allow_under_member_selection;
        let removed_cid = remove_card_at_index(state, target_player_idx, source_zone, idx, allow_under_member).unwrap_or(-1);
        if removed_cid < 0 {
            return HandlerResult::Continue;
        }

        state.players[target_player_idx].push_discard_card(removed_cid as i32);
        moved_cards.push(removed_cid as i32);
        
        next_ctx.v_remaining = if next_ctx.v_remaining > 0 {
            next_ctx.v_remaining - 1
        } else {
            (count as i16) - 1
        };
        
        if !next_ctx.selected_cards.contains(&removed_cid) {
            next_ctx.selected_cards.push(removed_cid);
        }

        // Check if more cards needed
        if next_ctx.v_remaining > 0 {
            let still_available = has_available_filtered(
                state,
                db,
                target_player_idx,
                source_zone,
                discard.prompt_filter_attr,
                &next_ctx,
            );

            if !still_available {
                finish_pending_interaction(state);
                return HandlerResult::Continue;
            }

            next_ctx.choice_index = -1;

            // Auto-pick for forced discards
            let is_forced = !is_optional && (count as usize) >= state.players[target_player_idx].hand.len();
            if (ctx.auto_pick || is_forced) && !is_optional {
                let has_cards = match source_zone {
                    Zone::Hand => !state.players[target_player_idx].hand.is_empty(),
                    Zone::Stage => state.players[target_player_idx].stage.iter().any(|&c| c >= 0),
                    _ => true,
                };

                if has_cards {
                    next_ctx.choice_index = 0;
                    return handle_move_to_discard(state, db, &mut next_ctx, frame_data, frame_idx);
                }
            }

            let v_remaining = next_ctx.v_remaining;
            let prompt_ctx = prompt_ctx_for_target(&next_ctx, target_player_idx);
            if matches!(
                suspend_choice(state, db, &prompt_ctx, &prompt_ctx, frame_idx, O_MOVE_TO_DISCARD, discard.suspend_slot, choice_type, discard.prompt_filter_attr, v_remaining),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }
    } else {
        // === Auto-discard path (no player choice needed) ===
        for _ in 0..count {
            if let Some(cid) = pop_card_from_zone(state, target_player_idx, source_zone, next_ctx.area_idx as i32) {
                state.players[target_player_idx].push_discard_card(cid);
                moved_cards.push(cid);
                next_ctx.selected_cards.push(cid);
            }
        }
    }

    // Finalization
    if next_ctx.selected_cards.is_empty() && !moved_cards.is_empty() {
        next_ctx.selected_cards.extend(moved_cards.iter().copied());
    }
    if !next_ctx.selected_cards.is_empty() {
        ctx.selected_cards = next_ctx.selected_cards.clone();
    }
    ctx.v_accumulated = next_ctx.selected_cards.len() as i16;
    ctx.choice_index = -1;
    ctx.v_remaining = -1;

    // TAP_SELF check: if ability has TAP_SELF effect and we discarded from a member slot, tap it
    let should_tap_self = moved_cards.iter().any(|&cid| db.get_live(cid).is_some())
        && ctx.area_idx >= 0 && ctx.area_idx < 3
        && source_ability(db, ctx).map(|ability| {
            ability.effects.iter().any(|effect| {
                effect.runtime_opcode == O_NOP
                    && effect.params.get("raw_effect").and_then(|v| v.as_str()) == Some("TAP_SELF")
            })
        }).unwrap_or(false);
    
    if should_tap_self {
        state.players[p_idx].set_tapped(ctx.area_idx as usize, true);
    }

    // Fire triggers for discarded cards
    if !next_ctx.selected_cards.is_empty() {
        state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &next_ctx.selected_cards);
    } else if !moved_cards.is_empty() {
        state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &moved_cards);
    }

    state.players[target_player_idx].hand.retain(|c| *c != -1);
    HandlerResult::Continue
}

// === Helper functions ===

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_helpers::create_test_state;

    #[test]
    fn stage_removal_uses_actual_slot_index_even_when_prior_slots_are_empty() {
        let mut state = create_test_state();
        state.players[0].stage = [-1, 4192, 104].into();

        let removed = remove_card_at_index(&mut state, 0, Zone::Stage, 2, false);

        assert_eq!(removed, Some(104));
        assert_eq!(
            state.players[0].stage.iter().copied().collect::<Vec<_>>(),
            vec![-1, 4192, -1]
        );
    }
}

fn is_deck_zone(zone: Zone) -> bool {
    matches!(zone, Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default)
}

fn has_available_filtered(
    state: &GameState,
    db: &CardDatabase,
    player_idx: usize,
    zone: Zone,
    filter_attr: u64,
    ctx: &AbilityContext,
) -> bool {
    let filter = CardFilter::from_attr(filter_attr);
    match zone {
        Zone::Hand => {
            let hand_filter_attr = filter_attr
                & !0x3
                & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
            if hand_filter_attr == 0 {
                state.players[player_idx].hand.iter().any(|&card_id| card_id >= 0)
            } else {
                let hand_filter = CardFilter::from_attr(hand_filter_attr);
                let mut filter_ctx = ctx.clone();
                filter_ctx.player_id = ctx.activator_id;
                state.players[player_idx]
                    .hand
                    .iter()
                    .enumerate()
                    .any(|(idx, &card_id)| {
                        hand_filter.matches(
                            state,
                            db,
                            card_id,
                            Some((player_idx as u8, 200 + idx as i16)),
                            false,
                            None,
                            &filter_ctx,
                        )
                    })
            }
        }
        Zone::Stage => state.players[player_idx]
            .stage
            .iter()
            .enumerate()
            .any(|(idx, &card_id)| {
                if card_id < 0 {
                    return false;
                }
                filter.matches(
                    state,
                    db,
                    card_id,
                    Some((player_idx as u8, idx as i16)),
                    false,
                    None,
                    ctx,
                )
            }),
        _ => true,
    }
}

fn pop_card_from_zone(
    state: &mut GameState,
    player_idx: usize,
    zone: Zone,
    area_idx: i32,
) -> Option<i32> {
    match zone {
        Zone::Hand => state.players[player_idx].pop_hand_card(),
        Zone::Stage => {
            let slot = if area_idx >= 0 && area_idx < 3 { area_idx as usize } else { 0 };
            let cid = state.players[player_idx].stage[slot];
            if cid >= 0 {
                state.players[player_idx].clear_stage_card(slot);
                state.mark_stats_dirty(player_idx);
                Some(cid)
            } else {
                None
            }
        }
        Zone::Discard => state.players[player_idx].pop_discard_card(),
        Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => {
            state.players[player_idx].pop_deck_card()
        }
        _ => None,
    }
}

fn remove_card_at_index(
    state: &mut GameState,
    player_idx: usize,
    zone: Zone,
    idx: usize,
    _allow_under: bool,
) -> Option<i32> {
    match zone {
        Zone::Hand => {
            if idx < state.players[player_idx].hand.len() {
                state.players[player_idx].remove_hand_card(idx)
            } else {
                None
            }
        }
        Zone::Discard => {
            if idx < state.players[player_idx].discard.len() {
                state.players[player_idx].remove_discard_card(idx)
            } else {
                None
            }
        }
        Zone::Stage => {
            if idx < 3 {
                let cid = state.players[player_idx].stage[idx];
                if cid >= 0 {
                    state.players[player_idx].clear_stage_card(idx);
                    state.mark_stats_dirty(player_idx);
                    Some(cid)
                } else {
                    None
                }
            } else {
                None
            }
        }
        _ => None,
    }
}

fn source_ability(db: &CardDatabase, ctx: &AbilityContext) -> Option<Ability> {
    db.get_card(ctx.source_card_id).and_then(|card| {
        card.abilities().get(ctx.ability_index as usize).cloned()
    })
}
