use crate::core::logic::{GameState, CardDatabase, AbilityContext, TriggerType};
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::{suspend_interaction, resolve_target_slot, get_choice_text};
use crate::core::logic::interpreter::constants::CHOICE_DONE;

pub fn handle_member_state(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i64, s: i32, instr_ip: usize) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let resolved_slot = if target_slot == 10 { ctx.target_slot as i32 } else { resolve_target_slot(target_slot, ctx) as i32 };

    match op {
        O_ACTIVATE_MEMBER => {
            let mut group_bits = 0u32;
            if let Some(card) = db.get_member(ctx.source_card_id) {
                for &g in &card.groups {
                    if g < 32 {
                        group_bits |= 1 << g;
                    }
                }
            }

            if target_slot == 1 {
                for i in 0..3 {
                    if state.core.players[p_idx].is_tapped(i) {
                        state.core.players[p_idx].set_tapped(i, false);
                        state.core.players[p_idx].activated_member_group_mask |= group_bits;
                    }
                }
            } else if resolved_slot < 3 {
                if state.core.players[p_idx].is_tapped(resolved_slot as usize) {
                    state.core.players[p_idx].set_tapped(resolved_slot as usize, false);
                    state.core.players[p_idx].activated_member_group_mask |= group_bits;
                }
            }
        },
        O_SET_TAPPED => {
            if resolved_slot < 3 { state.core.players[p_idx].set_tapped(resolved_slot as usize, v != 0); }
        },
        O_TAP_MEMBER => {
            let is_optional = (a as u64 & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0;
            if ctx.choice_index == -1 {
                if is_optional || (a & 0x01) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(state, db, ctx, instr_ip, O_TAP_MEMBER, 0, "OPTIONAL", &choice_text, a as u64, -1) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                if (a & 0x02) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(state, db, ctx, instr_ip, O_TAP_MEMBER, 0, "TAP_M_SELECT", &choice_text, a as u64, v as i16) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                // Only auto-tap if it was NOT an optional handler that just suspended or was bypassed
                if (a & 0x03) == 0 && resolved_slot < 3 {
                    state.core.players[p_idx].set_tapped(resolved_slot as usize, true);
                }
            } else {
                if is_optional || (a & 0x01) != 0 {
                    // 1 and 99 are both mapped to "No" for optional costs
                    if ctx.choice_index == CHOICE_DONE || ctx.choice_index == 1 { return Some(HandlerResult::SetCond(false)); }
                    if resolved_slot < 3 { state.core.players[p_idx].set_tapped(resolved_slot as usize, true); }
                    return Some(HandlerResult::SetCond(true));
                } else {
                    let slot = ctx.choice_index as usize;
                    if slot < 3 {
                        state.core.players[p_idx].set_tapped(slot, true);
                    }
                    return Some(HandlerResult::SetCond(true));
                }
            }
        },
        O_TAP_OPPONENT => {
            let target_p_idx = 1 - (ctx.activator_id as usize);
            // println!("[DEBUG] O_TAP_OPPONENT handler: v={}, a={}, s={}", v, a, s);
            let count = if ctx.v_remaining == -1 { v as i16 } else { ctx.v_remaining };
            if count <= 0 { return Some(HandlerResult::Continue); }

            if ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                 if suspend_interaction(state, db, ctx, instr_ip, O_TAP_OPPONENT, 0, "TAP_O", &choice_text, a as u64, count) {
                    return Some(HandlerResult::Suspend);
                }
            } else {
                let slot_idx = ctx.choice_index as usize;
                if slot_idx < 3 {
                    state.core.players[target_p_idx].set_tapped(slot_idx, true);
                    ctx.v_remaining = count - 1;
                    ctx.choice_index = -1;
                    if ctx.v_remaining > 0 {
                        let choice_text = get_choice_text(db, ctx);
                         if suspend_interaction(state, db, ctx, instr_ip, O_TAP_OPPONENT, 0, "TAP_O", &choice_text, a as u64, ctx.v_remaining) {
                            return Some(HandlerResult::Suspend);
                        }
                    }
                }
            }
        },
        O_MOVE_MEMBER | O_FORMATION_CHANGE => {
            let src_slot = if op == O_FORMATION_CHANGE && target_slot == 4 { ctx.area_idx as usize }
                           else if op == O_MOVE_MEMBER && ctx.area_idx >= 0 { ctx.area_idx as usize }
                           else { resolved_slot as usize };

            let dst_slot = if ctx.target_slot != -1 { ctx.target_slot as usize } else { a as usize };
            if src_slot < 3 && dst_slot < 3 && src_slot != dst_slot {
                state.core.players[p_idx].swap_slot_data(src_slot, dst_slot);
                for &slot in &[src_slot, dst_slot] {
                    let cid = state.core.players[p_idx].stage[slot];
                    if cid >= 0 {
                        let mut pos_ctx = ctx.clone();
                        pos_ctx.source_card_id = cid; pos_ctx.area_idx = slot as i16;
                        state.trigger_abilities(db, TriggerType::OnPositionChange, &pos_ctx);
                    }
                }
            }
        },
        O_PLACE_UNDER => {
            let slot = if ctx.target_slot != -1 { ctx.target_slot as usize } else { resolved_slot as usize };
            if slot < 3 {
                if a == 0 && !state.core.players[p_idx].hand.is_empty() {
                    let hand_idx = if ctx.choice_index != -1 { ctx.choice_index as usize } else { state.core.players[p_idx].hand.len() - 1 };
                    if hand_idx < state.core.players[p_idx].hand.len() {
                        let cid = state.core.players[p_idx].hand.remove(hand_idx);
                        state.core.players[p_idx].stage_energy[slot].push(cid);
                    }
                } else if a == 1 {
                    if let Some(cid) = state.core.players[p_idx].energy_zone.pop() {
                        state.core.players[p_idx].stage_energy[slot].push(cid);
                    }
                }
                state.core.players[p_idx].stage_energy_count[slot] = state.core.players[p_idx].stage_energy[slot].len() as u8;
            }
        },
        O_ADD_STAGE_ENERGY => {
            if resolved_slot < 3 {
                for _ in 0..v { state.core.players[p_idx].stage_energy[resolved_slot as usize].push(2000); }
                state.core.players[p_idx].sync_stage_energy_count(resolved_slot as usize);
            }
        },
        O_GRANT_ABILITY => {
            let ab_idx = v as u16;
            let source_cid = ctx.source_card_id;
            let mut targets = smallvec::SmallVec::<[i32; 3]>::new();
            if target_slot == 4 && resolved_slot < 3 {
                let cid = state.core.players[p_idx].stage[resolved_slot as usize];
                if cid >= 0 { targets.push(cid); }
            } else if target_slot == 1 {
                for i in 0..3 {
                    let cid = state.core.players[p_idx].stage[i];
                    if cid >= 0 { targets.push(cid); }
                }
            } else if target_slot >= 0 && target_slot < 3 {
                let cid = state.core.players[p_idx].stage[target_slot as usize];
                if cid >= 0 { targets.push(cid); }
            }

            for t_cid in targets {
                state.core.players[p_idx].granted_abilities.push((t_cid, source_cid, ab_idx));
            }
        },
        O_PLAY_MEMBER_FROM_HAND => {
            let remaining = if ctx.v_remaining == -1 {
                if v == 1 { 1 } else { 2 } // v=1 means card pre-selected, just need slot
            } else { ctx.v_remaining };

            if state.debug.debug_mode {
                println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: v={}, remaining={}, target_slot={}, choice_index={}", v, remaining, ctx.target_slot, ctx.choice_index);
            }

            if remaining == 2 {
                // Step 1: Select Card from Hand
                if ctx.choice_index == -1 {
                    if suspend_interaction(state, db, ctx, instr_ip, O_PLAY_MEMBER_FROM_HAND, 0, "SELECT_HAND_PLAY", "", a as u64, remaining) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                let h_idx = ctx.choice_index as usize;
                
                if h_idx < state.core.players[p_idx].hand.len() {
                    ctx.target_slot = h_idx as i16;
                    ctx.v_remaining = 1;
                    ctx.choice_index = -1;
                    if state.debug.debug_mode {
                        println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: Step 1 Done. Selected real hand_idx={}", h_idx);
                    }
                    // Move to Step 2
                    return handle_member_state(state, db, ctx, op, v, a, s, instr_ip);
                }
            } else if remaining == 1 {
                // Step 2: Select Slot
                if ctx.choice_index == -1 {
                    let mut next_ctx = ctx.clone();
                    next_ctx.player_id = p_idx as u8;
                    if suspend_interaction(state, db, &next_ctx, instr_ip, O_PLAY_MEMBER_FROM_HAND, s, "SELECT_STAGE", "", a as u64, remaining) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let slot_idx = ctx.choice_index as usize;
                if state.debug.debug_mode {
                    println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: Step 2 Selection. slot_idx={}", slot_idx);
                }

                if slot_idx < 3 {
                    // Execute Play
                    let h_idx = ctx.target_slot as usize;
                    if h_idx < state.core.players[p_idx].hand.len() {
                        let cid = state.core.players[p_idx].hand.remove(h_idx);
                        if state.debug.debug_mode {
                            println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: Executing Play of cid={} to slot={}", cid, slot_idx);
                        }
                        if let Some(old) = state.handle_member_leaves_stage(p_idx, slot_idx, db, ctx) {
                            state.core.players[p_idx].discard.push(old);
                        }
                        state.core.players[p_idx].stage[slot_idx] = cid;
                        state.core.players[p_idx].set_tapped(slot_idx, false);
                        state.core.players[p_idx].set_moved(slot_idx, true);
                        state.register_played_member(p_idx, cid, db);

                        let new_ctx = AbilityContext {
                            source_card_id: cid, player_id: p_idx as u8, activator_id: p_idx as u8, area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        ctx.choice_index = -1;
                        ctx.v_remaining = 0;
                        return Some(HandlerResult::Continue);
                    }
                }
            }
        },
        O_PLAY_MEMBER_FROM_DISCARD => {
            let opponent_bit = (s >> 24) & 1;
            let target_p_idx = if opponent_bit != 0 { 1 - (ctx.activator_id as usize) } else { ctx.activator_id as usize };
            let empty_slot_only = ((s as u64) & crate::core::logic::interpreter::constants::FLAG_EMPTY_SLOT_ONLY) != 0;

            let filter_attr_base = a as u64;
            let is_total_cost = (filter_attr_base & crate::core::logic::interpreter::constants::FILTER_TOTAL_COST) != 0;

            let mut remaining = if ctx.v_remaining == -1 {
                if is_total_cost {
                    ctx.v_accumulated = ((filter_attr_base >> crate::core::generated_constants::FILTER_COST_SHIFT) & 0x1F) as i16;
                }
                v as i16 * 2
            } else {
                ctx.v_remaining
            };
            if remaining <= 0 { return Some(HandlerResult::Continue); }

            if remaining % 2 == 0 {
                // Softlock Prevention: If empty_slot_only is set, check if any slot is actually empty
                if empty_slot_only && state.core.players[target_p_idx].stage.iter().all(|&c| c >= 0) {
                    return Some(HandlerResult::Continue);
                }

                // Step 1: Choose Card
                if state.core.players[target_p_idx].looked_cards.is_empty() {
                    let mut filter_attr = filter_attr_base;
                    if is_total_cost {
                        filter_attr = (filter_attr & !(0x1F << crate::core::generated_constants::FILTER_COST_SHIFT)) | ((ctx.v_accumulated as u64) << crate::core::generated_constants::FILTER_COST_SHIFT);
                    }
                    for &cid in &state.core.players[target_p_idx].discard {
                        if db.get_member(cid).is_some() && (filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr)) {
                            state.core.players[target_p_idx].looked_cards.push(cid);
                        }
                    }
                    if state.core.players[target_p_idx].looked_cards.is_empty() { return Some(HandlerResult::Continue); }

                    // Reset stale choice_index from previous round and re-suspend
                    ctx.choice_index = -1;
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    let choice_text = get_choice_text(db, &target_ctx);
                    if suspend_interaction(state, db, &target_ctx, instr_ip, O_PLAY_MEMBER_FROM_DISCARD, s, "SELECT_DISCARD_PLAY", &choice_text, a as u64, remaining) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let idx = ctx.choice_index as usize;
                let cards_len = state.core.players[target_p_idx].looked_cards.len();

                if idx < cards_len {
                    let cid = state.core.players[target_p_idx].looked_cards[idx];
                    state.core.players[target_p_idx].looked_cards.clear();
                    state.core.players[target_p_idx].looked_cards.push(cid);

                    remaining -= 1;
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    let choice_type = if empty_slot_only { "SELECT_STAGE_EMPTY" } else { "SELECT_STAGE" };
                    if suspend_interaction(state, db, &target_ctx, instr_ip, O_PLAY_MEMBER_FROM_DISCARD, s, choice_type, "", a as u64, remaining) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            } else {
                if state.core.players[target_p_idx].looked_cards.is_empty() { return Some(HandlerResult::Continue); }
                let card_id = state.core.players[target_p_idx].looked_cards.remove(0);

                // If the player passed the stage selection (choice 99), we stop here and DON'T remove from discard.
                if ctx.choice_index == 99 {
                    return Some(HandlerResult::Continue);
                }

                if let Some(pos) = state.core.players[target_p_idx].discard.iter().position(|&cid| cid == card_id) {
                    let slot_idx = if ctx.choice_index >= 0 && ctx.choice_index < 3 { ctx.choice_index as usize } else { resolved_slot as usize };

                    if slot_idx < 3 {
                        // Validate slot restriction or overlap
                        if (state.core.players[target_p_idx].prevent_play_to_slot_mask & (1 << slot_idx)) != 0 || (empty_slot_only && state.core.players[target_p_idx].stage[slot_idx] != -1) {
                            // If the slot is locked or occupied (when empty only is req), we abort the play and DON'T remove from discard
                            return Some(HandlerResult::Continue);
                        }

                        if is_total_cost {
                            if let Some(m) = db.get_member(card_id) {
                                ctx.v_accumulated = (ctx.v_accumulated - m.cost as i16).max(0);
                            }
                        }

                        state.core.players[target_p_idx].discard.remove(pos);

                        if let Some(old) = state.handle_member_leaves_stage(target_p_idx, slot_idx, db, ctx) {
                            state.core.players[target_p_idx].discard.push(old);
                        }
                        state.core.players[target_p_idx].stage[slot_idx] = card_id;
                        state.core.players[target_p_idx].set_tapped(slot_idx, true); // WAIT state
                        state.core.players[target_p_idx].set_moved(slot_idx, true);
                        state.register_played_member(target_p_idx, card_id, db);

                        // Rule Check: Slot is locked for the rest of the turn (Q169)
                        state.core.players[target_p_idx].prevent_play_to_slot_mask |= 1 << slot_idx;

                        let mut new_ctx = AbilityContext {
                            source_card_id: card_id,
                            player_id: target_p_idx as u8,
                            activator_id: target_p_idx as u8,
                            area_idx: slot_idx as i16,
                            v_accumulated: ctx.v_accumulated,
                            ..Default::default()
                        };
                        new_ctx.v_remaining = ctx.v_remaining;
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                    }
                }

                remaining -= 1;
                if remaining > 0 {
                    // Start next pair: repopulate looked_cards for the next card selection
                    let mut filter_attr = filter_attr_base;
                    if is_total_cost {
                        filter_attr = (filter_attr & !(0x1F << crate::core::generated_constants::FILTER_COST_SHIFT)) | ((ctx.v_accumulated as u64) << crate::core::generated_constants::FILTER_COST_SHIFT);
                    }
                    state.core.players[target_p_idx].looked_cards.clear();
                    for &cid in &state.core.players[target_p_idx].discard {
                        if db.get_member(cid).is_some() && (filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr)) {
                            state.core.players[target_p_idx].looked_cards.push(cid);
                        }
                    }
                    if state.core.players[target_p_idx].looked_cards.is_empty() {
                        // No more eligible cards in discard
                        return Some(HandlerResult::Continue);
                    }
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    target_ctx.choice_index = -1;
                    let choice_text = get_choice_text(db, &target_ctx);
                    if suspend_interaction(state, db, &target_ctx, instr_ip, O_PLAY_MEMBER_FROM_DISCARD, s, "SELECT_DISCARD_PLAY", &choice_text, a as u64, remaining) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }
        },
        O_INCREASE_COST => {
            state.core.players[p_idx].cost_modifiers.push((crate::core::logic::Condition {
                condition_type: crate::core::enums::ConditionType::None,
                value: 0,
                attr: 0,
                target_slot: 0,
                is_negated: false,
                params: serde_json::Value::Null,
            }, v));
        },
        _ => return None,
    }
    Some(HandlerResult::Continue)
}
