use crate::core::logic::{GameState, CardDatabase, AbilityContext, TriggerType};
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::{suspend_interaction_with_db as suspend_interaction, resolve_target_slot, get_choice_text};

pub fn handle_member_state(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i32, s: i32, instr_ip: usize) -> HandlerResult {
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
                if (a & 0x02) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(state, db, ctx, instr_ip, O_TAP_MEMBER, 0, "OPTIONAL", &choice_text, a as u64, -1) {
                        return HandlerResult::Suspend;
                    }
                }
                if (a & 0x01) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(state, db, ctx, instr_ip, O_TAP_MEMBER, 0, "TAP_M_SELECT", &choice_text, a as u64, v as i16) {
                        return HandlerResult::Suspend;
                    }
                }
                if resolved_slot < 3 { state.core.players[p_idx].set_tapped(resolved_slot as usize, true); }
            } else {
                if (a & 0x02) != 0 {
                    if ctx.choice_index == 1 { return HandlerResult::Continue; }
                    if resolved_slot < 3 { state.core.players[p_idx].set_tapped(resolved_slot as usize, true); }
                } else {
                    let slot = ctx.choice_index as usize;
                    if slot < 3 { state.core.players[p_idx].set_tapped(slot, true); }
                }
            }
        },
        O_TAP_OPPONENT => {
            if ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(state, db, ctx, instr_ip, O_TAP_OPPONENT, 0, "TAP_O", &choice_text, 0, -1) {
                    return HandlerResult::Suspend;
                }
            } else {
                let slot_idx = ctx.choice_index as usize;
                if slot_idx < 3 { state.core.players[1 - p_idx].set_tapped(slot_idx, true); }
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
            if ctx.choice_index == -1 && !state.core.players[p_idx].hand.is_empty() {
                if suspend_interaction(state, db, ctx, instr_ip, O_PLAY_MEMBER_FROM_HAND, 0, "SELECT_HAND_PLAY", "", a as u64, -1) {
                    return HandlerResult::Suspend;
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
                        let mut new_ctx = AbilityContext { source_card_id: cid, player_id: p_idx as u8, area_idx: slot_idx as i16, ..Default::default() };
                        new_ctx.v_remaining = ctx.v_remaining; // Carry over if needed?
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                    } else {
                        state.core.players[p_idx].hand.insert(hand_idx, cid);
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
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}
