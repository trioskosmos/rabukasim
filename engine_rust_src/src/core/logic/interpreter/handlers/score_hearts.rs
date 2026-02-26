use crate::core::logic::{GameState, CardDatabase, AbilityContext};
use crate::core::hearts::HeartBoard;
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::resolve_target_slot;
use super::super::conditions::resolve_count;
use super::super::constants::DYNAMIC_VALUE;
use super::super::logging;

pub fn handle_score_hearts(state: &mut GameState, _db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i64, s: i32) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let resolved_slot = if target_slot == 10 { ctx.target_slot as i32 } else { resolve_target_slot(target_slot, ctx) as i32 };

    match op {
        O_BOOST_SCORE => {
            let mut final_v = v;
            if (a as u64 & DYNAMIC_VALUE) != 0 {
                // slot (s) contains the count opcode
                let count = resolve_count(state, _db, s, a as u64 & !DYNAMIC_VALUE, ctx, 0);
                final_v = v * count;
            }
            state.core.players[p_idx].live_score_bonus += final_v;
            state.core.players[p_idx].live_score_bonus_logs.push((ctx.source_card_id, final_v));
            if !state.ui.silent {
                if let Some(msg) = logging::get_opcode_log(O_BOOST_SCORE, final_v, a, s, 0) {
                    state.log(msg);
                }
            }
        },
        O_REDUCE_COST => state.core.players[p_idx].cost_reduction += v as i16,
        O_SET_SCORE => state.core.players[p_idx].score = v as u32,
        O_ADD_BLADES | O_BUFF_POWER => {
            if target_slot == 1 {
                for t in 0..3 { state.core.players[p_idx].blade_buffs[t] += v as i16; }
            } else if resolved_slot < 3 {
                state.core.players[p_idx].blade_buffs[resolved_slot as usize] += v as i16;
            }
            // Unified logging: EFFECT events now go to both turn_history and rule_log
            state.log_event("EFFECT", &format!("+{} Appeal", v), ctx.source_card_id, ctx.ability_index, p_idx as u8, None, true);
        },
        O_SET_BLADES => {
            if target_slot == 4 && ctx.area_idx >= 0 {
                state.core.players[p_idx].blade_buffs[ctx.area_idx as usize] = v as i16;
            }
        },
        O_ADD_HEARTS => {
            let mut color = a as usize;
            if color == 0 { color = ctx.selected_color as usize; }
            if color < 7 {
                // DEBUG: Log heart buff application
                if state.debug.debug_mode {
                    println!("[DEBUG O_ADD_HEARTS] target_slot={}, area_idx={}, color={}, v={}", target_slot, ctx.area_idx, color, v);
                }
                if (target_slot == 4 || target_slot == 0) && ctx.area_idx >= 0 {
                    state.core.players[p_idx].heart_buffs[ctx.area_idx as usize].add_to_color(color, v as i32);
                } else if target_slot == 1 {
                    for t in 0..3 { state.core.players[p_idx].heart_buffs[t].add_to_color(color, v as i32); }
                }
            }
            if !state.ui.silent {
                if let Some(msg) = logging::get_opcode_log(O_ADD_HEARTS, v, a, s, 0) {
                    state.log(msg);
                }
            }
            // Unified logging: EFFECT events now go to both turn_history and rule_log
            state.log_event("EFFECT", &format!("+{} Heart(s)", v), ctx.source_card_id, ctx.ability_index, p_idx as u8, None, true);
        },
        O_SET_HEARTS => {
            if (a as usize) < 7 {
                let targets = if target_slot == 4 && ctx.area_idx >= 0 { vec![ctx.area_idx as usize] } else if target_slot == 1 { vec![0, 1, 2] } else { vec![] };
                for t in targets { state.core.players[p_idx].heart_buffs[t].set_color_count(a as usize, v as u8); }
            }
        },
        O_TRANSFORM_COLOR => { state.core.players[p_idx].color_transforms.push((ctx.source_card_id, 0, v as u8)); },
        O_REDUCE_HEART_REQ => {
             if (s as usize) < 7 {
                 state.core.players[p_idx].heart_req_reductions.add_to_color(s as usize, v);
                 state.core.players[p_idx].heart_req_reduction_logs.push((ctx.source_card_id, s as u8, v as u8));
             }
        },
        O_TRANSFORM_HEART => {
            let src = a as usize;
            let dst = s as usize;
            if src < 7 && dst < 7 {
                let amt = v.abs();
                if state.core.players[p_idx].heart_req_reductions.get_color_count(src) >= amt as u8 {
                    state.core.players[p_idx].heart_req_reductions.add_to_color(src, -(amt as i32));
                    state.core.players[p_idx].heart_req_reductions.add_to_color(dst, amt as i32);
                }
            }
        },
        O_INCREASE_HEART_COST => {
             if (s as usize) < 7 {
                 state.core.players[p_idx].heart_req_additions.add_to_color(s as usize, v);
             }
        },
        O_SET_HEART_COST => {
            // Set heart cost for a specific color or full map override
            if (a & 0x01) != 0 {
                // Packed map: v contains counts (4 bits per color)
                // When using packed map, we assume it's an OVERRIDE, so we clear base by setting reductions to 255.
                let player = &mut state.core.players[p_idx];
                player.heart_req_additions = HeartBoard::default();
                player.heart_req_reductions = HeartBoard(0x00FFFFFFFFFFFFFF); // Clear base (0..6)
                
                for color_idx in 0..7 {
                    let count = ((v >> (color_idx * 4)) & 0xF) as u8;
                    if count > 0 {
                        player.heart_req_additions.set_color_count(color_idx, count);
                    }
                }
            } else {
                // Legacy single-color behavior: v = amount to set, s = color index
                if (s as usize) < 7 {
                    state.core.players[p_idx].heart_req_additions.set_color_count(s as usize, v as u8);
                }
            }
        },
        O_REDUCE_SCORE => {
            // Reduce live score bonus by v
            // Used by cards that penalize the player's live score
            let reduction = v.min(state.core.players[p_idx].live_score_bonus);
            state.core.players[p_idx].live_score_bonus -= reduction;
            if state.debug.debug_mode {
                println!("[DEBUG] O_REDUCE_SCORE: reduced by {} to {}", reduction, state.core.players[p_idx].live_score_bonus);
            }
        },
        O_LOSE_EXCESS_HEARTS => {
            // Lose excess hearts beyond what's required for the live
            // v = number of excess hearts to lose (0 = lose all excess)
            let player = &mut state.core.players[p_idx];
            let reduction = if v == 0 { player.excess_hearts } else { v as u32 };
            player.excess_hearts = player.excess_hearts.saturating_sub(reduction);
            
            if state.debug.debug_mode {
                println!("[DEBUG] O_LOSE_EXCESS_HEARTS: reduced by {} to {}", reduction, player.excess_hearts);
            }
        },
        O_SKIP_ACTIVATE_PHASE => {
            // Skip the next activate phase
            // Used by cards that prevent member activation
            state.core.players[p_idx].skip_next_activate = true;
            if state.debug.debug_mode {
                println!("[DEBUG] O_SKIP_ACTIVATE_PHASE: set skip_next_activate=true");
            }
        },
        _ => return None,
    }
    Some(HandlerResult::Continue)
}
