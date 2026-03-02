use crate::core::logic::{GameState, CardDatabase, AbilityContext};
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::suspend_interaction;

pub fn handle_energy(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i64, s: i32, instr_ip: usize) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;

    match op {
        O_ENERGY_CHARGE => {
            let target_p = if (s & 0xFF) == 2 { 1 - p_idx } else { p_idx };
            // Read "Wait" flag from Slot bit 27 (FLAG_IS_WAIT) instead of Attr bit 31
            let is_wait = (s as u64 & crate::core::logic::interpreter::constants::FLAG_IS_WAIT) != 0;
            for _ in 0..v {
                if let Some(cid) = state.core.players[target_p].energy_deck.pop() {
                    state.core.players[target_p].energy_zone.push(cid);
                    let new_idx = state.core.players[target_p].energy_zone.len() - 1;
                    state.core.players[target_p].set_energy_tapped(new_idx, is_wait);
                }
            }
            Some(HandlerResult::Continue)
        },
        O_PAY_ENERGY => {
            let available = (0..state.core.players[p_idx].energy_zone.len())
                .filter(|&i| !state.core.players[p_idx].is_energy_tapped(i))
                .count() as i32;

            let is_optional = (a as u64 & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0;
            if is_optional && ctx.choice_index == -1 {
                if available < v {
                    if state.debug.debug_mode { println!("[DEBUG] O_PAY_ENERGY: cannot afford optional cost."); }
                    return Some(HandlerResult::SetCond(false)); // Can't afford optional -> SetCond(false)
                } else {
                    if state.debug.debug_mode { println!("[DEBUG] O_PAY_ENERGY: attempting optional suspension (instr_ip={}).", instr_ip); }
                    if suspend_interaction(state, db, ctx, instr_ip, O_PAY_ENERGY, 0, "OPTIONAL", "", a as u64, -1) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }

            if ctx.choice_index == 99 {
                return Some(HandlerResult::SetCond(false));
            }

            let mut next_ctx = ctx.clone();
            if is_optional && ctx.choice_index != -1 && ctx.v_remaining == -1 {
                 if ctx.choice_index == 1 { return Some(HandlerResult::SetCond(false)); } // Declined -> SetCond(false)
                 next_ctx.choice_index = -1;
                 next_ctx.v_remaining = v as i16;
            }

            if next_ctx.choice_index == 99 {
                return Some(HandlerResult::SetCond(false));
            } else if available < v {
                return Some(HandlerResult::SetCond(false));
            } else {
                 if next_ctx.choice_index != -1 {
                    let idx = next_ctx.choice_index as usize;
                    if idx < state.core.players[p_idx].energy_zone.len() && !state.core.players[p_idx].is_energy_tapped(idx) {
                        state.core.players[p_idx].set_energy_tapped(idx, true);
                        next_ctx.v_remaining -= 1;
                        if next_ctx.v_remaining > 0 {
                            next_ctx.choice_index = -1;
                            if suspend_interaction(state, db, &next_ctx, instr_ip, O_PAY_ENERGY, 0, "PAY_ENERGY", "", 0, next_ctx.v_remaining) {
                                return Some(HandlerResult::Suspend);
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
            Some(HandlerResult::SetCond(true))
        },
        O_ACTIVATE_ENERGY => {
            // Readies up to `v` tapped energy.
            let mut count = 0;
            let mut group_bits = 0u32;
            if let Some(card) = db.get_member(ctx.source_card_id) {
                if state.debug.debug_mode {
                    println!("[ENERGY_DEBUG] source_card_id={}, card_no={}, groups={:?}", ctx.source_card_id, card.card_no, card.groups);
                }
                for &g in &card.groups {
                    if g < 32 {
                        group_bits |= 1 << g;
                    }
                }
            } else {
                if state.debug.debug_mode {
                    println!("[ENERGY_DEBUG] card NOT FOUND for id={}", ctx.source_card_id);
                }
            }

            for i in 0..state.core.players[p_idx].energy_zone.len() {
                if count >= v { break; }
                if state.core.players[p_idx].is_energy_tapped(i) {
                    state.core.players[p_idx].set_energy_tapped(i, false);
                    state.core.players[p_idx].activated_energy_group_mask |= group_bits;
                    count += 1;
                }
            }
            Some(HandlerResult::Continue)
        },
        O_PAY_ENERGY_DYNAMIC => {
            // Pay energy equal to card score + v
            // Used by cards that have dynamic energy costs based on card properties
            let base_score = state.core.players[p_idx].score as i32;
            let total_cost = (base_score + v) as usize;

            if state.debug.debug_mode {
                println!("[DEBUG] O_PAY_ENERGY_DYNAMIC: base_score={}, v={}, total_cost={}", base_score, v, total_cost);
            }

            let available = (0..state.core.players[p_idx].energy_zone.len())
                .filter(|&i| !state.core.players[p_idx].is_energy_tapped(i))
                .count();

            if available < total_cost {
                return Some(HandlerResult::SetCond(false));
            }

            // Auto-pay the energy
            let mut paid = 0;
            for i in 0..state.core.players[p_idx].energy_zone.len() {
                if paid >= total_cost { break; }
                if !state.core.players[p_idx].is_energy_tapped(i) {
                    state.core.players[p_idx].set_energy_tapped(i, true);
                    paid += 1;
                }
            }
            Some(HandlerResult::SetCond(true))
        },
        O_PLACE_ENERGY_UNDER_MEMBER => {
            // Place energy card under a member
            // Source zone shifted to Slot bits 16-23
            let src_zone = (s >> 16) & 0xFF;
            let slot = if ctx.area_idx >= 0 { ctx.area_idx as usize } else { 0 };

            if slot < 3 {
                match src_zone {
                    7 => { // From Discard
                        if let Some(cid) = state.core.players[p_idx].discard.pop() {
                            state.core.players[p_idx].stage_energy[slot].push(cid);
                        }
                    },
                    8 | 0 => { // From Deck (0 default is deck in this context)
                        if let Some(cid) = state.core.players[p_idx].deck.pop() {
                            state.core.players[p_idx].stage_energy[slot].push(cid);
                        }
                    },
                    _ => { // From Energy (Default 1 or other)
                        if !state.core.players[p_idx].energy_zone.is_empty() {
                            // Find an untapped energy to move
                            for i in 0..state.core.players[p_idx].energy_zone.len() {
                                if !state.core.players[p_idx].is_energy_tapped(i) {
                                    let energy_cid = state.core.players[p_idx].energy_zone.remove(i);
                                    state.core.players[p_idx].stage_energy[slot].push(energy_cid);
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            Some(HandlerResult::Continue)
        },
        _ => None,
    }
}
