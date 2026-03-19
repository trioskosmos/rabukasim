use crate::core::enums::*;
use crate::core::logic::constants::{CHOICE_DONE, FILTER_MASK_LOWER};
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState};
use crate::core::models::suspend_interaction;
use crate::core::logic::interpreter::logging;
use super::movement_discard_helpers::{
    pop_card_from_zone, remove_card_by_index, resolve_source_zone, zone_available_count,
    zone_card_count,
};
use super::super::HandlerResult;
pub fn handle_move_to_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &crate::core::logic::interpreter::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let v = if instr.filter_attr().compare_accumulated {
        resolve_count(
            state,
            db,
            s,
            (instr.filter_attr().to_attr() & FILTER_MASK_LOWER) as u64,
            p_idx as i32,
            ctx,
            0,
        ) as i32
    } else {
        instr.v
    };
    let base_p = ctx.activator_id as usize;
    let slot = instr.slot();
    let source_zone = resolve_source_zone(&slot);
    let target_player_idx = if slot.is_opponent { 1 - base_p } else { base_p };

    let count = if (v as u32 & (1 << 31)) != 0 {
        let target_size = v & 0x7FFFFFFF;
        let current_size = zone_card_count(state, target_player_idx, source_zone);
        (current_size - target_size).max(0)
    } else {
        v
    };
    if target_player_idx != p_idx
        && state.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY)
    {
        return HandlerResult::Continue;
    }

    let filter_attr = (a as u64) & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
    let is_optional = instr.filter_attr().is_optional;

    if state.debug.debug_mode {
        println!(
            "[DEBUG_MOV] h_m_t_d: cid={}, choice={}, optional={}, attr={:x}",
            ctx.source_card_id, ctx.choice_index, is_optional, a as u64
        );
    }

    let available_count = zone_available_count(state, target_player_idx, source_zone);

    if is_optional && ctx.choice_index == -1 {
        if available_count < v {
            return HandlerResult::Continue;
        }
    }

    let mut next_ctx = ctx.clone();
    let choice_type = if source_zone == Zone::Hand {
        ChoiceType::SelectHandDiscard
    } else {
        ChoiceType::SelectDiscard
    };

    if is_optional
        && next_ctx.choice_index == -1
        && matches!(
            source_zone,
            Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
        )
    {
        if suspend_interaction(
            state,
            db,
            &next_ctx,
            instr_ip,
            O_MOVE_TO_DISCARD,
            s,
            ChoiceType::Optional,
            "",
            filter_attr,
            count as i16,
        ) {
            return HandlerResult::Suspend;
        }
    }

    if source_zone == Zone::Stage && next_ctx.choice_index == -1 && count == 1 {
        let slot = if ctx.target_slot >= 0 {
            ctx.target_slot as usize
        } else if next_ctx.area_idx >= 0 {
            next_ctx.area_idx as usize
        } else {
            0
        };
        if slot < 3 && state.players[target_player_idx].stage[slot] >= 0 {
            next_ctx.choice_index = slot as i16;
        }
    }

    if next_ctx.choice_index == -1
        && count > 0
        && source_zone != Zone::Default
        && source_zone != Zone::Deck
        && source_zone != Zone::DeckTop
        && source_zone != Zone::DeckBottom
    {
        if state.players[p_idx].looked_cards.len() == 1 && !is_optional && count == 1 {
            next_ctx.choice_index = 0;
        }

        // Auto-pick all if mandatory and we have fewer than or equal to count
        if !is_optional && next_ctx.choice_index == -1 {
            if source_zone == Zone::Hand {
                let hand_len = state.players[p_idx].hand.len();
                if hand_len > 0 && (count as usize) >= hand_len {
                    next_ctx.choice_index = 0; // Auto-pick first index (interpreter will loop)
                }
            } else {
                let available_indices = state.get_card_ids_in_zone(p_idx as u8, source_zone as u8);
                let mut matching_indices = Vec::new();
                for &card_idx in &available_indices {
                    if state.card_matches_filter_with_ctx(db, card_idx, filter_attr, &next_ctx) {
                        matching_indices.push(card_idx);
                    }
                }

                if !matching_indices.is_empty() && (count as usize) >= matching_indices.len() {
                    // For Stage/Live, find the slot index
                    if source_zone == Zone::Stage {
                        if let Some(pos) = state.players[p_idx]
                            .stage
                            .iter()
                            .position(|&c| c == matching_indices[0])
                        {
                            next_ctx.choice_index = pos as i16;
                        }
                    } else {
                        next_ctx.choice_index = 0;
                    }
                }
            }
        }

        if next_ctx.choice_index == -1 {
            let mut filter_obj = instr.filter_attr();
            if source_zone == Zone::Stage {
                filter_obj.zone_mask = 4; // ZONE_MASK_STAGE
            } else if source_zone == Zone::Hand {
                filter_obj.zone_mask = 6; // ZONE_MASK_HAND
            } else if source_zone == Zone::Discard {
                filter_obj.zone_mask = 7; // ZONE_MASK_DISCARD
            }
            let filter_attr_with_mask = filter_obj.to_attr();

            // AUTO-PICK FIX: If mandatory and no choices remain (count >= items), auto-pick first item.
            let items_count = match source_zone {
                Zone::Hand => state.players[target_player_idx].hand.len(),
                _ => state
                    .get_card_ids_in_zone(target_player_idx as u8, source_zone as u8)
                    .len(),
            };

            if !is_optional && (count as usize) >= items_count && items_count > 0 {
                next_ctx.choice_index = 0;
            } else if ctx.auto_pick && !is_optional && available_count > 0 {
                next_ctx.choice_index = 0;
            } else if suspend_interaction(
                state,
                db,
                &next_ctx,
                instr_ip,
                O_MOVE_TO_DISCARD,
                s,
                choice_type,
                "",
                filter_attr_with_mask,
                v as i16,
            ) {
                return HandlerResult::Suspend;
            }
        }
    }

    let mut moved_cards = Vec::new();

    if next_ctx.choice_index != -1 {
        if is_optional
            && matches!(
                source_zone,
                Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
            )
            && next_ctx.choice_index == 1
        {
            return HandlerResult::SetCond(false);
        }
        if next_ctx.choice_index == CHOICE_DONE {
            if is_optional {
                return HandlerResult::SetCond(false);
            } else {
                if (next_ctx.v_remaining > 0) || (next_ctx.v_remaining == -1 && count > 0) {
                    if suspend_interaction(
                        state,
                        db,
                        &next_ctx,
                        instr_ip,
                        O_MOVE_TO_DISCARD,
                        s,
                        choice_type,
                        "You must select more cards",
                        filter_attr,
                        if next_ctx.v_remaining > 0 {
                            next_ctx.v_remaining
                        } else {
                            count as i16
                        },
                    ) {
                        return HandlerResult::Suspend;
                    }
                    return HandlerResult::Continue;
                }
            }
        }

        let idx = next_ctx.choice_index as usize;
        let mut removed_cid = -1;
        if let Some(cid) = remove_card_by_index(
            state,
            db,
            ctx,
            target_player_idx,
            source_zone,
            idx,
            next_ctx.area_idx as i32,
            (s & (1 << 25)) != 0,
        ) {
            removed_cid = cid;
        }
        if removed_cid >= 0 {
            state.players[target_player_idx].push_discard_card(removed_cid as i32);
            moved_cards.push(removed_cid as i32);
            next_ctx.v_remaining = if next_ctx.v_remaining > 0 {
                next_ctx.v_remaining - 1
            } else {
                (count as i16) - 1
            };
            if next_ctx.v_remaining > 0 {
                // BUG FIX: Check if there are ANY cards left in the source zone matching the filter.
                let still_available = match source_zone {
                    Zone::Hand => state.players[target_player_idx].hand.iter().any(|&c| {
                        let cf =
                            crate::core::logic::filter::CardFilter::from_attr(filter_attr as i64);
                        cf.matches(state, db, c, None, false, None, &next_ctx)
                    }),
                    Zone::Stage => state.players[target_player_idx].stage.iter().any(|&c| {
                        if c < 0 {
                            return false;
                        }
                        let cf =
                            crate::core::logic::filter::CardFilter::from_attr(filter_attr as i64);
                        cf.matches(state, db, c, None, false, None, &next_ctx)
                    }),
                    _ => true,
                };

                if !still_available {
                    return HandlerResult::Continue;
                }

                next_ctx.choice_index = -1;
                // BATCH CONTEXT PRESERVATION: Accumulate all moved cards in selected_cards across recursion
                next_ctx.selected_cards.push(removed_cid);

                // If auto_pick is true and it's mandatory, try to move the next card immediately
                // Or if it's mandatory and count >= items, we also auto-pick
                let is_forced_pick = !is_optional
                    && (count as usize) >= (state.players[target_player_idx].hand.len()); // simplified for hand
                if (ctx.auto_pick || is_forced_pick) && !is_optional {
                    // Safety check: is there another card?
                    let still_available = match source_zone {
                        Zone::Hand => !state.players[target_player_idx].hand.is_empty(),
                        Zone::Stage => state.players[target_player_idx]
                            .stage
                            .iter()
                            .any(|&c| c >= 0),
                        _ => true,
                    };

                    if still_available {
                        next_ctx.choice_index = 0;
                        // LOOP: Recursive-style but safe because we already removed one card
                        // NOTE: selected_cards persists across recursion via next_ctx
                        return crate::core::logic::interpreter::handlers::movement::handle_move_to_discard(state, db, &mut next_ctx, instr, instr_ip);
                    }
                }

                if suspend_interaction(
                    state,
                    db,
                    &next_ctx,
                    instr_ip,
                    O_MOVE_TO_DISCARD,
                    s,
                    choice_type,
                    "",
                    filter_attr,
                    next_ctx.v_remaining,
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    } else {
        for _ in 0..count {
            if let Some(cid) = pop_card_from_zone(
                state,
                target_player_idx,
                source_zone,
                next_ctx.area_idx as i32,
                db,
                &next_ctx,
            ) {
                state.players[target_player_idx].push_discard_card(cid);
                moved_cards.push(cid);
                next_ctx.selected_cards.push(cid);
            }
        }
    }

    if next_ctx.selected_cards.is_empty() && !moved_cards.is_empty() {
        next_ctx.selected_cards.extend(moved_cards.iter().copied());
    }

    // Preserve the moved-card batch on the current execution context so
    // subsequent DISCARDED_CARDS conditions in the same ability can see it.
    if !next_ctx.selected_cards.is_empty() {
        ctx.selected_cards = next_ctx.selected_cards.clone();
    }

    // BATCH CONTEXT PRESERVATION: Use accumulated selected_cards from context, not local moved_cards
    // This ensures all cards accumulated across recursive calls are in the trigger batch
    if !next_ctx.selected_cards.is_empty() {
        state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &next_ctx.selected_cards);
    } else if !moved_cards.is_empty() {
        // Fallback for non-recursive (multi-pop) case
        state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &moved_cards);
    }

    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(O_MOVE_TO_DISCARD, v, a, s, 0) {
            state.log(msg);
        }
    }

    state.players[target_player_idx].hand.retain(|c| *c != -1);
    HandlerResult::Continue
}



