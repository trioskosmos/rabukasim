use crate::core::logic::{GameState, CardDatabase, AbilityContext, TriggerType};
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::{suspend_interaction, resolve_target_slot, get_choice_text};

pub fn handle_meta_control(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i64, s: i32, instr_ip: usize) -> HandlerResult {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let _resolved_slot = if target_slot == 10 { ctx.target_slot as i32 } else { resolve_target_slot(target_slot, ctx) as i32 };

    match op {
        O_NEGATE_EFFECT => {
            let trigger_type = match v {
                1 => TriggerType::OnPlay, 2 => TriggerType::OnLiveStart, 3 => TriggerType::OnLiveSuccess,
                4 => TriggerType::TurnStart, 5 => TriggerType::TurnEnd, 6 => TriggerType::Constant,
                7 => TriggerType::Activated, 8 => TriggerType::OnLeaves, 9 => TriggerType::OnReveal,
                10 => TriggerType::OnPositionChange, _ => TriggerType::None,
            };
            if target_slot >= 0 && (target_slot as usize) < 3 {
                let cid = state.core.players[p_idx].stage[target_slot as usize];
                if cid >= 0 { state.core.players[p_idx].negated_triggers.push((cid, trigger_type, a.max(1) as i32)); }
            }
        },
        O_REDUCE_YELL_COUNT => { state.core.players[p_idx].yell_count_reduction = v as i16; },
        O_RESTRICTION => {
            state.core.players[p_idx].restrictions.push(a as u8);
            if a == 1 { state.core.players[p_idx].set_flag(crate::core::logic::player::PlayerState::FLAG_CANNOT_LIVE, true); }
        },
        O_SELECT_MEMBER | O_SELECT_LIVE | O_SELECT_PLAYER => {
            if ctx.choice_index == -1 {
                let choice_type = if op == O_SELECT_MEMBER { "SELECT_MEMBER" } 
                                  else if op == O_SELECT_LIVE { "SELECT_LIVE" }
                                  else if op == O_SELECT_PLAYER { "SELECT_PLAYER" }
                                  else { "UNKNOWN" };
                let mut flip_ctx = ctx.clone();
                if s == 2 { flip_ctx.player_id = 1 - (p_idx as u8); }
                else if s == 3 { flip_ctx.player_id = 1; }
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(state, db, &flip_ctx, instr_ip, op, s, choice_type, &choice_text, a as u64, -1) {
                    return HandlerResult::Suspend;
                }
            } else {
                // DEBUG: Log selection resolution
                if state.debug.debug_mode {
                    println!("[DEBUG O_SELECT_MEMBER] Resolved: choice_index={}, setting area_idx={}", ctx.choice_index, ctx.choice_index);
                }
                ctx.target_slot = ctx.choice_index;
                if ctx.choice_index < 3 { ctx.area_idx = ctx.choice_index; }
            }
        },
        O_OPPONENT_CHOOSE => {
             if ctx.choice_index == -1 {
                  let mut flip_ctx = ctx.clone(); flip_ctx.player_id = 1 - (p_idx as u8);
                  let old_cp = state.current_player; state.current_player = 1 - ctx.player_id;
                  let choice_text = get_choice_text(db, ctx);
                  if suspend_interaction(state, db, &flip_ctx, instr_ip, O_OPPONENT_CHOOSE, 0, "OPPONENT_CHOOSE", &choice_text, 0, -1) {
                      return HandlerResult::Suspend;
                  }
                  state.current_player = old_cp;
             }
             // On resumption, ctx.player_id is already flipped (stored as flip_ctx)
             // Subsequent opcodes will use the flipped player_id (opponent's perspective)
        },
        O_PREVENT_ACTIVATE => {
            let target_p_idx = if s == 1 { 1 - p_idx } else { p_idx };
            state.core.players[target_p_idx].prevent_activate = 1;
        },
        O_PREVENT_BATON_TOUCH => {
            let target_p_idx = if s == 1 { 1 - p_idx } else { p_idx };
            state.core.players[target_p_idx].prevent_baton_touch = 1;
        },
        O_PREVENT_SET_TO_SUCCESS_PILE => {
            let target_p_idx = if s == 1 { 1 - p_idx } else { p_idx };
            state.core.players[target_p_idx].prevent_success_pile_set = 1;
        },
        O_PREVENT_PLAY_TO_SLOT => {
            let target_p_idx = if a == 1 { 1 - p_idx } else { p_idx };
            if target_slot >= 0 && target_slot < 3 { state.core.players[target_p_idx].prevent_play_to_slot_mask |= 1 << target_slot; }
        },
        O_TRIGGER_REMOTE => {
             let target_cid = if target_slot >= 0 && target_slot < 3 { state.core.players[p_idx].stage[target_slot as usize] } else { -1 };
             if target_cid >= 0 {
                 if let Some(m) = db.get_member(target_cid as i32) {
                     if (v as usize) < m.abilities.len() {
                        return HandlerResult::BranchToBytecode(m.abilities[v as usize].bytecode.clone());
                     }
                 }
             }
        },
        O_REDUCE_LIVE_SET_LIMIT => { state.core.players[p_idx].prevent_success_pile_set = state.core.players[p_idx].prevent_success_pile_set.saturating_add(v as u8); },
        O_META_RULE => {
            if a == 0 { state.core.players[p_idx].cheer_mod_count = state.core.players[p_idx].cheer_mod_count.saturating_add(v as u16); }
        },
        O_BATON_TOUCH_MOD => state.core.players[p_idx].baton_touch_limit = v as u8,
        O_IMMUNITY => state.core.players[p_idx].set_flag(crate::core::logic::player::PlayerState::FLAG_IMMUNITY, v != 0),
        O_COLOR_SELECT => {
            if ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(state, db, ctx, instr_ip, O_COLOR_SELECT, 0, "COLOR_SELECT", &choice_text, 0, -1) {
                    return HandlerResult::Suspend;
                }
            } else {
                ctx.selected_color = ctx.choice_index;
            }
        },
        O_SWAP_AREA => {
             let p = &mut state.core.players[p_idx];
             let temp_stage = p.stage;
             let temp_energy = p.stage_energy_count;
             let temp_tapped = [p.is_tapped(0), p.is_tapped(1), p.is_tapped(2)];
             let temp_moved = [p.is_moved(0), p.is_moved(1), p.is_moved(2)];
             if v == 2 || (a == 1 && s == 0) {
                 let src = ctx.area_idx as usize;
                 let dst = a as usize;
                 if src < 3 && dst < 3 {
                    p.stage[src] = temp_stage[dst]; p.stage[dst] = temp_stage[src];
                    p.stage_energy_count[src] = temp_energy[dst]; p.stage_energy_count[dst] = temp_energy[src];
                    p.set_tapped(src, temp_tapped[dst]); p.set_tapped(dst, temp_tapped[src]);
                    p.set_moved(src, temp_moved[dst]); p.set_moved(dst, temp_moved[src]);
                 }
             } else {
                 p.stage[0] = temp_stage[2]; p.stage[1] = temp_stage[0]; p.stage[2] = temp_stage[1];
                 p.stage_energy_count[0] = temp_energy[2]; p.stage_energy_count[1] = temp_energy[0]; p.stage_energy_count[2] = temp_energy[1];
                 p.set_tapped(0, temp_tapped[2]); p.set_tapped(1, temp_tapped[0]); p.set_tapped(2, temp_tapped[1]);
                 p.set_moved(0, temp_moved[2]); p.set_moved(1, temp_moved[0]); p.set_moved(2, temp_moved[1]);
             }
         },
        O_REPEAT_ABILITY => {
            // v = max repeat count (0 = infinite, N = repeat N more times)
            // Returns Branch(0) to restart ability from beginning, or Continue if limit reached
            let max_repeats = v;
            if max_repeats == 0 || ctx.repeat_count < max_repeats as i16 {
                ctx.repeat_count = ctx.repeat_count.saturating_add(1);
                if state.debug.debug_mode {
                    println!("[DEBUG] O_REPEAT_ABILITY: repeating ability (count={}/{})", ctx.repeat_count, max_repeats);
                }
                return HandlerResult::Branch(0);  // Jump back to start of ability
            } else {
                if state.debug.debug_mode {
                    println!("[DEBUG] O_REPEAT_ABILITY: limit reached (count={}/{})", ctx.repeat_count, max_repeats);
                }
            }
        },
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}
