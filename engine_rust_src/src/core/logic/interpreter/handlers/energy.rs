use crate::core::logic::{GameState, CardDatabase, AbilityContext};
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::suspend_interaction_with_db as suspend_interaction;

pub fn handle_energy(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i32, s: i32, instr_ip: usize) -> HandlerResult {
    let p_idx = ctx.player_id as usize;

    match op {
        O_ENERGY_CHARGE => {
            let target_p = if s == 2 { 1 - p_idx } else { p_idx };
            let is_wait = (a & 0x01) != 0;
            for _ in 0..v {
                if let Some(cid) = state.core.players[target_p].energy_deck.pop() {
                    state.core.players[target_p].energy_zone.push(cid);
                    let new_idx = state.core.players[target_p].energy_zone.len() - 1;
                    state.core.players[target_p].set_energy_tapped(new_idx, is_wait);
                }
            }
        },
        O_PAY_ENERGY => {
            let available = (0..state.core.players[p_idx].energy_zone.len())
                .filter(|&i| !state.core.players[p_idx].is_energy_tapped(i))
                .count() as i32;

            if (a & 0x82) != 0 && ctx.choice_index == -1 {
                if available < v {
                    return HandlerResult::Continue; // Failed cond (logic handled in mod.rs via cond)
                } else {
                    if suspend_interaction(state, db, ctx, instr_ip, O_PAY_ENERGY, 0, "OPTIONAL", "", a as u64, -1) {
                        return HandlerResult::Suspend;
                    }
                }
            }
            
            let mut next_ctx = ctx.clone();
            if (a & 0x82) != 0 && ctx.choice_index != -1 && ctx.v_remaining == -1 {
                 if ctx.choice_index == 1 { return HandlerResult::Continue; } // Declined
                 next_ctx.choice_index = -1;
                 next_ctx.v_remaining = v as i16;
            }
            
            if next_ctx.choice_index == 99 {
                return HandlerResult::Continue;
            } else if available < v {
                return HandlerResult::Continue;
            } else {
                 if next_ctx.choice_index != -1 {
                    let idx = next_ctx.choice_index as usize;
                    if idx < state.core.players[p_idx].energy_zone.len() && !state.core.players[p_idx].is_energy_tapped(idx) {
                        state.core.players[p_idx].set_energy_tapped(idx, true);
                        next_ctx.v_remaining -= 1;
                        if next_ctx.v_remaining > 0 {
                            next_ctx.choice_index = -1;
                            if suspend_interaction(state, db, &next_ctx, instr_ip, O_PAY_ENERGY, 0, "PAY_ENERGY", "", 0, next_ctx.v_remaining) {
                                return HandlerResult::Suspend;
                            }
                        }
                    }
                } else {
                    // Auto-pay
                    let mut paid = 0;
                    let player = &mut state.core.players[p_idx];
                    for i in 0..player.energy_zone.len() {
                        if paid >= v { break; }
                        if !player.is_energy_tapped(i) {
                            player.set_energy_tapped(i, true);
                            paid += 1;
                        }
                    }
                }
            }
        },
        O_ACTIVATE_ENERGY => {
             let mut count = 0;
             for i in 0..state.core.players[p_idx].energy_zone.len() {
                 if count >= v { break; }
                 if state.core.players[p_idx].is_energy_tapped(i) {
                     state.core.players[p_idx].set_energy_tapped(i, false);
                     count += 1;
                 }
             }
        },
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}
