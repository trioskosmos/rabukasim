//! # Cost Logic
//!
//! This module contains the logic for checking and paying ability costs.

use crate::core::logic::{GameState, CardDatabase, AbilityContext, Cost, TriggerType};
use crate::core::enums::*;
use super::filter::map_filter_string_to_attr;

pub fn check_cost(state: &GameState, db: &CardDatabase, p_idx: usize, cost: &Cost, ctx: &AbilityContext) -> bool {
    let player = &state.core.players[p_idx];
    let val = cost.value as usize;
    let mut attr: u64 = 0;
    if let Some(params) = cost.params.as_object() {
        if let Some(filter_str) = params.get("filter").and_then(|v| v.as_str()) {
            attr = map_filter_string_to_attr(filter_str);
        }
    }
     let result = match cost.cost_type {
         AbilityCostType::None => true,
         AbilityCostType::Energy => {
              let available = (0..player.energy_zone.len()).filter(|&i| !player.is_energy_tapped(i)).count() as i32;
              available >= cost.value
         },
         AbilityCostType::TapSelf => {
              if ctx.area_idx >= 0 {
                  !player.is_tapped(ctx.area_idx as usize)
              } else { false }
         },
         AbilityCostType::TapMember => {
            if val == 0 {
                // FALLBACK: TapMember(0) refers to self (Wait self) - used by some Activated patterns
                if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    player.stage[ctx.area_idx as usize] >= 0 && !player.is_tapped(ctx.area_idx as usize)
                } else { false }
            } else {
                let untapped_count = (0..3).filter(|&i| player.stage[i] >= 0 && !player.is_tapped(i)).count();
                untapped_count >= val
            }
        },
        AbilityCostType::TapEnergy => {
            let untapped_energy = (0..player.energy_zone.len()).filter(|&i| !player.is_energy_tapped(i)).count();
            untapped_energy >= val
        },
         AbilityCostType::DiscardHand => {
             if attr != 0 {
                 player.hand.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr)).count() >= val
             } else {
                 player.hand.len() >= val
             }
         },
         AbilityCostType::SacrificeSelf => {
             if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                 player.stage[ctx.area_idx as usize] >= 0
             } else { false }
         },
         AbilityCostType::RevealHand => {
             player.hand.len() >= val
         },
         AbilityCostType::SacrificeUnder => {
             if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                 player.stage_energy[ctx.area_idx as usize].len() >= val
             } else { false }
         },
         AbilityCostType::DiscardEnergy => {
             player.energy_zone.len() >= val
         },
         AbilityCostType::ReturnMemberToDeck => {
             if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                 player.stage[ctx.area_idx as usize] >= 0
             } else { false }
         },
         AbilityCostType::ReturnDiscardToDeck => {
             player.discard.len() >= val
         },
         AbilityCostType::ReturnHand => {
             if attr != 0 {
                 player.stage.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr)).count() >= val
             } else {
                 player.stage.iter().filter(|&&id| id >= 0).count() >= val
             }
         },
         AbilityCostType::DiscardMember => {
             if attr != 0 {
                 player.stage.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr)).count() >= val
             } else {
                 player.stage.iter().filter(|&&id| id >= 0).count() >= val
             }
         },
         AbilityCostType::DiscardSuccessLive => {
             if attr != 0 {
                 player.success_lives.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr)).count() >= val
             } else {
                 player.success_lives.len() >= val
             }
         },
         _ => true
     };

    if !result && state.debug.debug_ignore_conditions {
        if let Ok(mut bypassed) = state.debug.bypassed_conditions.0.lock() {
            bypassed.push(format!("BYPASS Cost: Type {:?}, Value {}", cost.cost_type, cost.value));
        }
        return true;
    }
    result
}

pub fn pay_cost(state: &mut GameState, db: &CardDatabase, p_idx: usize, cost: &Cost, ctx: &AbilityContext) -> bool {
    let mut attr = 0;
    if let Some(params) = cost.params.as_object() {
        if let Some(filter_str) = params.get("filter").and_then(|v| v.as_str()) {
            attr = map_filter_string_to_attr(filter_str);
        }
    }

    if state.debug.debug_mode {
        println!("[DEBUG] Paying Cost: {:?}, Value: {}, Card: {}", cost.cost_type, cost.value, ctx.source_card_id);
    }
    let result = match cost.cost_type {
        AbilityCostType::None => true,
        AbilityCostType::Energy => {
            let untap_indices: Vec<usize> = (0..state.core.players[p_idx].energy_zone.len())
                .filter(|&i| !state.core.players[p_idx].is_energy_tapped(i))
                .take(cost.value as usize).collect();
            if untap_indices.len() < cost.value as usize { return false; }
            for idx in untap_indices { state.core.players[p_idx].set_energy_tapped(idx, true); }
            true
        }
        AbilityCostType::TapSelf => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                state.core.players[p_idx].set_tapped(ctx.area_idx as usize, true);
                true
            } else { false }
        },
        AbilityCostType::TapMember => {
            let player = &mut state.core.players[p_idx];
            let mut needed = cost.value as usize;
            if needed == 0 { 
                // FALLBACK: Value 0 means "Tap Self"
                if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    player.set_tapped(ctx.area_idx as usize, true);
                    return true;
                }
                return false;
            }
            for i in 0..3 {
                if !player.is_tapped(i) && player.stage[i] >= 0 {
                    player.set_tapped(i, true);
                    needed -= 1;
                    if needed == 0 { break; }
                }
            }
            needed == 0
        },
        AbilityCostType::TapEnergy => {
            let player = &mut state.core.players[p_idx];
            let mut needed = cost.value as usize;
            if needed == 0 { return true; }
            for i in 0..player.energy_zone.len() {
                if !player.is_energy_tapped(i) {
                    player.set_energy_tapped(i, true);
                    needed -= 1;
                    if needed == 0 { break; }
                }
            }
            needed == 0
        },
        AbilityCostType::DiscardHand => {
            let count = cost.value as usize;
            let filter_attr = attr;
            
            if filter_attr != 0 {
                let mut to_discard = Vec::new();
                for &cid in &state.core.players[p_idx].hand {
                    if state.card_matches_filter(db, cid, filter_attr) {
                        to_discard.push(cid);
                        if to_discard.len() >= count { break; }
                    }
                }
                
                if to_discard.len() < count { return false; }
                
                for cid in to_discard {
                    if let Some(pos) = state.core.players[p_idx].hand.iter().position(|&x| x == cid) {
                        state.core.players[p_idx].hand.remove(pos);
                        state.core.players[p_idx].discard.push(cid);
                    }
                }
                true
            } else {
                let player = &mut state.core.players[p_idx];
                if player.hand.len() < count { return false; }
                for _ in 0..count {
                    if let Some(cid) = player.hand.pop() {
                        player.discard.push(cid);
                    }
                }
                true
            }
        },
        AbilityCostType::SacrificeSelf => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                let slot = ctx.area_idx as usize;
                let cid = state.core.players[p_idx].stage[slot];
                if cid >= 0 {
                    let mut leave_ctx = ctx.clone();
                    leave_ctx.source_card_id = cid;
                    leave_ctx.area_idx = ctx.area_idx;
                    state.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);

                    let player = &mut state.core.players[p_idx];
                    player.stage[slot] = -1;
                    player.discard.push(cid as i32);
                    let under_cards = std::mem::take(&mut player.stage_energy[slot]);
                    player.discard.extend(under_cards);
                    player.stage_energy_count[slot] = 0;
                    true
                } else { false }
            } else { false }
        },
        AbilityCostType::RevealHand => true,
        AbilityCostType::SacrificeUnder => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                let player = &mut state.core.players[p_idx];
                let count = cost.value as usize;
                let slot = ctx.area_idx as usize;
                if player.stage_energy[slot].len() < count { return false; }
                for _ in 0..count {
                    if let Some(cid) = player.stage_energy[slot].pop() {
                        player.discard.push(cid);
                    }
                }
                player.stage_energy_count[slot] = player.stage_energy[slot].len() as u8;
                true
            } else { false }
        },
        AbilityCostType::DiscardEnergy => {
            let player = &mut state.core.players[p_idx];
            let count = cost.value as usize;
            if player.energy_zone.len() < count { return false; }
            for _ in 0..count {
                if let Some(cid) = player.energy_zone.pop() {
                    // tapped_energy_mask doesn't strictly need popping, 
                    // but we should ensure bit is clear if we reuse index
                    // Actually, energy_zone.len() handles the bounds.
                    player.discard.push(cid);
                }
            }
            true
        },
        AbilityCostType::ReturnMemberToDeck => {
             if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                 let slot = ctx.area_idx as usize;
                 let cid = state.core.players[p_idx].stage[slot];
                 if cid >= 0 {
                     let mut leave_ctx = ctx.clone();
                     leave_ctx.source_card_id = cid;
                     leave_ctx.area_idx = slot as i16;
                     state.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);

                     let player = &mut state.core.players[p_idx];
                     player.stage[slot] = -1;
                     player.deck.insert(0, cid as i32);
                     true
                 } else { false }
             } else { false }
        },
        AbilityCostType::ReturnDiscardToDeck => {
            let player = &mut state.core.players[p_idx];
            let count = cost.value as usize;
            if player.discard.len() < count { return false; }
            for _ in 0..count {
                if let Some(cid) = player.discard.pop() {
                    player.deck.push(cid);
                }
            }
            true
        },
        AbilityCostType::ReturnHand | AbilityCostType::DiscardMember | AbilityCostType::ReturnMemberToHand | AbilityCostType::ReturnMemberToDiscard => {
            let count = cost.value as usize;
            let filter_attr = attr;
            let is_discard = cost.cost_type == AbilityCostType::DiscardMember;
            let mut slots_to_move = Vec::new();
            for i in 0..3 {
                let cid = state.core.players[p_idx].stage[i];
                if cid >= 0 && (filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr)) {
                    slots_to_move.push(i);
                    if slots_to_move.len() >= count { break; }
                }
            }
            if slots_to_move.len() < count { return false; }
            for slot in slots_to_move {
                if let Some(old) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                    if is_discard { state.core.players[p_idx].discard.push(old); }
                    else { state.core.players[p_idx].hand.push(old); }
                }
            }
            true
        },
        AbilityCostType::DiscardSuccessLive => {
            let count = cost.value as usize;
            let filter_attr = attr as i32;
            let mut indices = Vec::new();
            for (idx, &cid) in state.core.players[p_idx].success_lives.iter().enumerate() {
                if filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr as u64) {
                    indices.push(idx);
                    if indices.len() >= count { break; }
                }
            }
            if indices.len() < count { return false; }
            for &idx in indices.iter().rev() {
                let cid = state.core.players[p_idx].success_lives.remove(idx);
                state.core.players[p_idx].discard.push(cid);
            }
            true
        },
        _ => false,
    };
    if !result && state.debug.debug_ignore_conditions {
        return true;
    }
    if state.debug.debug_mode && !result {
        println!("[DEBUG] Cost Payment FAILED");
    }
    result
}
