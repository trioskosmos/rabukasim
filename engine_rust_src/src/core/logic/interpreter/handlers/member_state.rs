use crate::core::logic::{GameState, CardDatabase, AbilityContext, TriggerType};
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::{suspend_interaction, resolve_target_slot, get_choice_text};

pub fn handle_member_state(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i64, s: i32, instr_ip: usize) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let resolved_slot = if target_slot == 10 { ctx.target_slot as i32 } else { resolve_target_slot(target_slot, ctx) as i32 };

    match op {
        O_ACTIVATE_MEMBER => {
            if target_slot == 1 {
                for i in 0..3 { state.core.players[p_idx].set_tapped(i, false); }
            } else if resolved_slot < 3 {
                state.core.players[p_idx].set_tapped(resolved_slot as usize, false);
            }
        },
        O_SET_TAPPED => {
            if resolved_slot < 3 { state.core.players[p_idx].set_tapped(resolved_slot as usize, v != 0); }
        },
        O_TAP_MEMBER => {
            if ctx.choice_index == -1 {
                if (a & 0x01) != 0 {
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
                if (a & 0x01) != 0 {
                    // 1 and 99 are both mapped to "No" for optional costs
                    if ctx.choice_index == 1 || ctx.choice_index == 99 { return Some(HandlerResult::SetCond(false)); }
                    if resolved_slot < 3 { state.core.players[p_idx].set_tapped(resolved_slot as usize, true); }
                    return Some(HandlerResult::SetCond(true));
                } else {
                    let slot = ctx.choice_index as usize;
                    if slot < 3 { state.core.players[p_idx].set_tapped(slot, true); }
                    return Some(HandlerResult::SetCond(true));
                }
            }
        },
        O_TAP_OPPONENT => {
            let target_p_idx = 1 - (ctx.activator_id as usize);
            println!("[DEBUG] O_TAP_OPPONENT handler: v={}, a={}, s={}", v, a, s);
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
            println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: p_idx={}, activator_id={}, choice_index={}", p_idx, ctx.activator_id, ctx.choice_index);
            if ctx.choice_index == -1 && !state.core.players[p_idx].hand.is_empty() {
                if suspend_interaction(state, db, ctx, instr_ip, O_PLAY_MEMBER_FROM_HAND, 0, "SELECT_HAND_PLAY", "", a as u64, -1) {
                    return Some(HandlerResult::Suspend);
                }
            }
            if ctx.choice_index != -1 && ctx.choice_index != 99 {
                let hand_idx = ctx.choice_index as usize;
                if hand_idx < state.core.players[p_idx].hand.len() {
                    let cid = state.core.players[p_idx].hand.remove(hand_idx);
                    let slot_idx = resolved_slot as usize;
                    if slot_idx < 3 {
                        if let Some(old) = state.handle_member_leaves_stage(p_idx, slot_idx, db, ctx) {
                            state.core.players[p_idx].discard.push(old);
                        }
                        state.core.players[p_idx].stage[slot_idx] = cid;
                        state.core.players[p_idx].set_tapped(slot_idx, false);
                        state.core.players[p_idx].set_moved(slot_idx, true);
                        state.register_played_member(p_idx, cid, db);
                        ctx.target_slot = slot_idx as i16;
                        ctx.area_idx = slot_idx as i16;
                        let mut new_ctx = AbilityContext { source_card_id: cid, player_id: p_idx as u8, activator_id: p_idx as u8, area_idx: slot_idx as i16, ..Default::default() };
                        new_ctx.v_remaining = ctx.v_remaining; // Carry over if needed?
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                    } else {
                        state.core.players[p_idx].hand.insert(hand_idx, cid);
                    }
                }
            }
        },
        O_PLAY_MEMBER_FROM_DISCARD => {
            let opponent_bit = (s >> 24) & 1;
            let target_p_idx = if opponent_bit != 0 { 1 - (ctx.activator_id as usize) } else { ctx.activator_id as usize };
            let empty_slot_only = ((s as u64) & crate::core::logic::interpreter::constants::FLAG_EMPTY_SLOT_ONLY) != 0;
            
            let mut remaining = if ctx.v_remaining == -1 { v as i16 * 2 } else { ctx.v_remaining };
            if remaining <= 0 { return Some(HandlerResult::Continue); }

            if remaining % 2 == 0 {
                if ctx.choice_index == -1 {
                    state.core.players[target_p_idx].looked_cards.clear();
                    let filter_attr = a as u64;
                    for &cid in &state.core.players[target_p_idx].discard {
                        if db.get_member(cid).is_some() && (filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr)) {
                            state.core.players[target_p_idx].looked_cards.push(cid);
                        }
                    }
                    if state.core.players[target_p_idx].looked_cards.is_empty() { return Some(HandlerResult::Continue); }
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    let choice_text = get_choice_text(db, &target_ctx);
                    if suspend_interaction(state, db, &target_ctx, instr_ip, O_PLAY_MEMBER_FROM_DISCARD, s, "SELECT_DISCARD_PLAY", &choice_text, a as u64, remaining) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                
                let choice = ctx.choice_index as usize;
                if choice < state.core.players[target_p_idx].looked_cards.len() {
                    let cid = state.core.players[target_p_idx].looked_cards[choice];
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
                
                if let Some(pos) = state.core.players[target_p_idx].discard.iter().position(|&cid| cid == card_id) {
                    state.core.players[target_p_idx].discard.remove(pos);
                    let slot_idx = if ctx.choice_index >= 0 && ctx.choice_index < 3 { ctx.choice_index as usize } else { resolved_slot as usize };
                    
                    if slot_idx < 3 {
                        // Validate slot restriction
                        if (state.core.players[target_p_idx].prevent_play_to_slot_mask & (1 << slot_idx)) != 0 {
                            // If the slot is locked, we abort the play and put the card back in discard
                            state.core.players[target_p_idx].discard.push(card_id);
                            return Some(HandlerResult::Continue);
                        }

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
                            ..Default::default() 
                        };
                        new_ctx.v_remaining = ctx.v_remaining;
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                    }
                }
                
                remaining -= 1;
                if remaining > 0 {
                    // Start next pair
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    target_ctx.choice_index = -1;
                    if suspend_interaction(state, db, &target_ctx, instr_ip, O_PLAY_MEMBER_FROM_DISCARD, s, "SELECT_DISCARD_PLAY", "", a as u64, remaining) {
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
