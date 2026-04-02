use crate::core::logic::constants::{CHOICE_DONE, FILTER_IS_OPTIONAL, FILTER_MASK_LOWER};
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::suspension::finish_pending_interaction;
use crate::core::logic::models::{AbilityFrameComponents, Ability};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState, Zone};
use crate::core::enums::ChoiceType;
use crate::core::{O_MOVE_TO_DISCARD, O_NOP};
use super::super::HandlerResult;

pub fn handle_move_to_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    
    // Resolve count (handle compare_accumulated and UNTIL_SIZE)
    let v = if frame_data.filter.compare_accumulated {
        resolve_count(state, db, s, frame_data.raw_attr & FILTER_MASK_LOWER, p_idx as i32, ctx, 0) as i32
    } else {
        frame_data.value
    };
    
    let base_p = ctx.activator_id as usize;
    let slot = frame_data.slot;
    
    // Resolve source zone from slot - inlined from helper
    let mut source_zone = match slot.source_zone {
        Zone::Default => {
            // Infer from target slot - SLOT_CONTEXT=Stage, SLOT_HAND=Hand, live slots=LiveSet, else Deck
            let ts = slot.target_slot;
            if ts == 4 { Zone::Stage }
            else if ts == 6 { Zone::Hand }
            else if (9..=11).contains(&ts) { Zone::LiveSet }  // SLOT_LIVE_0..=SLOT_LIVE_2
            else { Zone::Deck }
        }
        Zone::Hand => Zone::Hand,
        Zone::Stage => Zone::Stage,
        Zone::Discard => Zone::Discard,
        Zone::Yell => Zone::Yell,
        _ => Zone::Deck,
    };
    
    // Determine target player from slot
    let target_player_idx = if slot.is_opponent { 1 - base_p } else { base_p };

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
    if source_zone == Zone::Stage {
        let is_until_size = frame_data.params.as_ref()
            .and_then(|p| p.get("operation"))
            .and_then(|v| v.as_str())
            .map(|s| s.eq_ignore_ascii_case("UNTIL_SIZE"))
            .unwrap_or(false);
        if is_until_size {
            source_zone = Zone::Hand;
        }
    }

    // Immunity check
    if target_player_idx != p_idx && state.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY) {
        return HandlerResult::Continue;
    }

    let filter_attr = (a as u64) & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
    let is_optional = frame_data.filter.is_optional
        || (a as u64 & FILTER_IS_OPTIONAL) != 0
        || ((ctx.source_card_id == 122 || ctx.source_card_id == 4331)
            && source_zone == Zone::Hand
            && frame_data.value == 1);

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
            // Optional deck discard - ask yes/no
            if matches!(
                suspend_choice(state, db, ctx, &mut next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, ChoiceType::Optional, filter_attr, count as i16),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else if count > 0 && !is_deck_zone(source_zone) {
            // Need specific card selection from hand/stage/discard
            let mut filter_obj = CardFilter::default();
            match source_zone {
                Zone::Stage => filter_obj.zone_mask = 4,  // Stage mask
                Zone::Hand => filter_obj.zone_mask = 6,   // Hand mask
                Zone::Discard => filter_obj.zone_mask = 7, // Discard mask
                _ => {}
            }
            let filter_attr_with_mask =
                filter_obj.to_attr() | frame_data.filter.to_attr();

            if matches!(
                suspend_choice(state, db, ctx, &mut next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, choice_type, filter_attr_with_mask as u64, v as i16),
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
                if matches!(
                    suspend_choice(state, db, ctx, &mut next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, choice_type, filter_attr, remaining),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
            return HandlerResult::Continue;
        }

        // Remove selected card by index - inlined from remove_card_by_index
        let idx = next_ctx.choice_index as usize;
        let allow_under_member = (s & (1 << 25)) != 0;
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
            let still_available = has_available_filtered(state, db, target_player_idx, source_zone, filter_attr, &next_ctx);

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
            if matches!(
                suspend_choice(state, db, ctx, &mut next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, choice_type, filter_attr, v_remaining),
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
    match zone {
        Zone::Hand => state.players[player_idx].hand.iter().any(|&c| {
            CardFilter::from_attr_legacy(filter_attr as i64).matches(state, db, c, None, false, None, ctx)
        }),
        Zone::Stage => state.players[player_idx].stage.iter().any(|&c| {
            if c < 0 { return false; }
            CardFilter::from_attr_legacy(filter_attr as i64).matches(state, db, c, None, false, None, ctx)
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
                state.players[player_idx].stage[slot] = -1;
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
                Some(state.players[player_idx].hand.remove(idx))
            } else {
                None
            }
        }
        Zone::Discard => {
            if idx < state.players[player_idx].discard.len() {
                Some(state.players[player_idx].discard.remove(idx))
            } else {
                None
            }
        }
        Zone::Stage => {
            let cards: Vec<i32> = state.players[player_idx].stage.iter().copied().filter(|&c| c >= 0).collect();
            if idx < cards.len() {
                let cid = cards[idx];
                if let Some(pos) = state.players[player_idx].stage.iter().position(|&c| c == cid) {
                    state.players[player_idx].stage[pos] = -1;
                }
                Some(cid)
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
