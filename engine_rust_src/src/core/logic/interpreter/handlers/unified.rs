//! Unified Opcode Handlers
//!
//! Direct handlers - no context wrapper, parameters passed explicitly

use crate::core::enums::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::instruction::{DecodedFilterAttr, DecodedSlot};
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::{AbilityFrame, AbilityFrameComponents};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, TriggerType};
use crate::core::models::interpreter::resolve_target_slot;
use crate::core::logic::interpreter::handlers::HandlerResult;

// Helper to get player index
fn p_idx(ctx: &AbilityContext) -> usize {
    ctx.player_id as usize
}


// ============================================================================
// META / CONTROL HANDLERS
// ============================================================================

pub fn handle_calc_sum_cost(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let sum: i32 = ctx.selected_cards
        .iter()
        .filter(|&&cid| cid >= 0)
        .filter_map(|&cid| db.get_member(cid))
        .map(|member| member.cost as i32)
        .sum();
    
    ctx.v_accumulated = sum as i16;
    
    if state.debug.debug_mode {
        let selected_names: Vec<String> = ctx.selected_cards
            .iter()
            .filter_map(|&cid| {
                db.get_member(cid)
                    .map(|card| card.name.clone())
                    .or_else(|| db.get_live(cid).map(|card| card.name.clone()))
            })
            .collect();
        println!("[DEBUG] CALC_SUM_COST: total_sum={} cards={:?}", sum, selected_names);
    }
    HandlerResult::Continue
}

pub fn handle_negate_effect(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let p_idx = p_idx(ctx);
    let target_slot = frame_data.slot.target_slot as i32;

    let trigger_type = match v {
        1 => TriggerType::OnPlay,
        2 => TriggerType::OnLiveStart,
        3 => TriggerType::OnLiveSuccess,
        4 => TriggerType::TurnStart,
        5 => TriggerType::TurnEnd,
        6 => TriggerType::Constant,
        7 => TriggerType::Activated,
        8 => TriggerType::OnLeaves,
        9 => TriggerType::OnReveal,
        10 => TriggerType::OnPositionChange,
        _ => TriggerType::None,
    };

    if target_slot >= 0 && (target_slot as usize) < 3 {
        let cid = state.players[p_idx].stage[target_slot as usize];
        if cid >= 0 {
            let count = (a as u64 & 0xFF).max(1) as i32;
            if let Some(entry) = state.players[p_idx]
                .negated_triggers
                .iter_mut()
                .find(|entry| entry.0 == cid && entry.1 == trigger_type)
            {
                entry.2 += count;
            } else {
                state.players[p_idx]
                    .negated_triggers
                    .push((cid, trigger_type, count));
            }
        }
    }
    HandlerResult::Continue
}

pub fn handle_set_target_self(_state: &mut GameState, _db: &CardDatabase, ctx: &mut AbilityContext, _frame_data: &AbilityFrameComponents<'_>) -> HandlerResult {
    ctx.player_id = ctx.activator_id;
    HandlerResult::Continue
}

pub fn handle_set_target_opponent(_state: &mut GameState, _db: &CardDatabase, ctx: &mut AbilityContext, _frame_data: &AbilityFrameComponents<'_>) -> HandlerResult {
    ctx.player_id = 1 - ctx.activator_id;
    HandlerResult::Continue
}

pub fn handle_repeat_ability(_state: &mut GameState, _db: &CardDatabase, ctx: &mut AbilityContext, frame_data: &AbilityFrameComponents<'_>) -> HandlerResult {
    let max_repeats = frame_data.value;
    if max_repeats == 0 || ctx.repeat_count < max_repeats as i16 {
        ctx.repeat_count = ctx.repeat_count.saturating_add(1);
        HandlerResult::Branch(0)
    } else {
        HandlerResult::Continue
    }
}

pub fn handle_flavor_action(state: &mut GameState, _db: &CardDatabase, _ctx: &mut AbilityContext, frame_data: &AbilityFrameComponents<'_>) -> HandlerResult {
    if state.debug.debug_mode {
        println!(
            "[DEBUG] FLAVOR_ACTION: {}",
            logging::describe_words(0, frame_data.value, frame_data.raw_attr as i64, frame_data.raw_slot)
        );
    }
    HandlerResult::Continue
}

// ============================================================================
// DRAW / HAND HANDLERS
// ============================================================================

pub fn handle_draw(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let v = frame_data.value;
    let p_idx = p_idx(ctx);
    let count = if frame_data.filter.compare_accumulated {
        use crate::core::logic::interpreter::conditions::resolve_count_frame;
        resolve_count_frame(state, db, &frame_data, ctx, 0) as u32
    } else {
        v as u32
    };
    let slot = frame_data.slot;
    let raw_is_opponent = ((frame_data.raw_slot as u32 >> 24) & 1) != 0;
    let target_p = if slot.is_opponent || raw_is_opponent {
        1 - p_idx
    } else {
        p_idx
    };

    match frame_data.opcode {
        O_DRAW => {
            for _ in 0..count {
                if state.players[target_p].deck.is_empty() {
                    state.resolve_deck_refresh(target_p);
                }
                if let Some(card_id) = state.players[target_p].pop_deck_card() {
                    let t = state.turn as i32;
                    match slot.dest_zone {
                        crate::core::enums::Zone::Discard => state.players[target_p].push_discard_card(card_id),
                        _ => state.players[target_p].draw_hand_card(card_id, t),
                    }
                }
            }
        }
        O_DRAW_UNTIL => {
            let target_hand_size = v as usize;
            let current_hand_size = state.players[p_idx].hand.len();
            if current_hand_size < target_hand_size {
                let to_draw = (target_hand_size - current_hand_size) as u32;
                state.draw_cards(p_idx, to_draw);
            }
        }
        O_ADD_TO_HAND => {
            if frame_data.raw_slot == 90 || frame_data.raw_slot == 6 {
                for _ in 0..v as usize {
                    if let Some(cid) = state.players[p_idx].looked_cards.pop() {
                        state.players[p_idx].gain_hand_card(cid);
                    }
                }
            } else {
                state.draw_cards(p_idx, v as u32);
            }
        }
        _ => {}
    }
    HandlerResult::Continue
}

// ============================================================================
// ENERGY HANDLERS
// ============================================================================

pub fn handle_energy_charge(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let op = frame_data.opcode;
    let v = frame_data.value;
    let p_idx = p_idx(ctx);
    let target_p = if frame_data.slot.is_opponent { 1 - p_idx } else { p_idx };
    let is_wait = frame_data.slot.is_wait;
    
    for _ in 0..v {
        if let Some(cid) = state.players[target_p].energy_deck.pop() {
            if !state.ui.silent {
                state.log(format!("Rule 6.1, Rule 6.1.1: [エナジーを送る] (Energy Charge) for Player {}.", target_p));
            }
            state.players[target_p].push_energy_card(cid, is_wait);
        }
    }
    HandlerResult::Continue
}

fn tap_energy_cards_with_logging(state: &mut GameState, p_idx: usize, count: usize) -> usize {
    let tapped_indices = crate::core::logic::interpreter::costs::tap_first_untapped_energy(state, p_idx, count);
    if !state.ui.silent {
        for idx in &tapped_indices {
            eprintln!("Rule 6.3, Rule 6.3.1: Tapping Energy at Index {} for Player {}.", idx, p_idx);
        }
    }
    for idx in &tapped_indices {
        state.players[p_idx].set_energy_tapped(*idx, true);
    }
    tapped_indices.len()
}

fn suspend_pay_energy(state: &mut GameState, db: &CardDatabase, ctx: &AbilityContext, frame_idx: usize, remaining: i16) -> HandlerResult {
    use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
    suspend_choice(state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0, ChoiceType::PayEnergy, 0, remaining)
}

pub fn handle_pay_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    use crate::core::logic::constants::{CHOICE_DONE, CHOICE_NO};
    use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice_with_options;
    
    let v = frame_data.value;
    let is_optional = frame_data.filter.is_optional;
    let p_idx = p_idx(ctx);
    
    let available = (0..state.players[p_idx].energy_zone.len())
        .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
        .count() as i32;
    let requires_explicit_selection =
        state.phase == Phase::Response || ctx.v_remaining > 0 || ctx.choice_index >= 0;
    
    // CASE 1: Variable Energy Payment
    if v == -1 {
        if ctx.choice_index == -1 {
            ctx.v_accumulated = 0;
            ctx.v_remaining = -2;
            let options = vec![serde_json::json!({"name": "Done", "text": "Finish paying energy"})];
            let actions = vec![11099];
            return suspend_choice_with_options(
                state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
                ChoiceType::PayEnergy, 0, -2, options, actions,
            );
        } else if ctx.choice_index == CHOICE_DONE {
            ctx.choice_index = -1;
            ctx.v_remaining = -1;
            return HandlerResult::Continue;
        } else if ctx.choice_index >= 0 {
            let e_idx = ctx.choice_index as usize;
            if e_idx < state.players[p_idx].energy_zone.len()
                && !state.players[p_idx].is_energy_tapped(e_idx) {
                state.players[p_idx].set_energy_tapped(e_idx, true);
                ctx.v_accumulated += 1;
            }
            ctx.choice_index = -1;
            let options = vec![serde_json::json!({"name": "Done", "text": "Finish paying energy"})];
            let actions = vec![11099];
            return suspend_choice_with_options(
                state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
                ChoiceType::PayEnergy, 0, -2, options, actions,
            );
        }
    }
    
    // CASE 2: Optional energy payment
    if is_optional && ctx.choice_index == -1 {
        if available < v {
            return HandlerResult::SetCond(false);
        } else {
            use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
            return suspend_choice(
                state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
                ChoiceType::Optional, frame_data.raw_attr, -1,
            );
        }
    }
    
    // Resumption logic for optional choice
    if is_optional && ctx.v_remaining == -1 {
        if ctx.choice_index == CHOICE_NO || ctx.choice_index == CHOICE_DONE {
            ctx.choice_index = -1;
            return HandlerResult::SetCond(false);
        }
        let paid = tap_energy_cards_with_logging(state, p_idx, v as usize);
        ctx.choice_index = -1;
        ctx.v_accumulated = paid as i16;
        ctx.v_remaining = -1;
        return HandlerResult::SetCond(paid == v as usize);
    }
    
    let remaining = if ctx.v_remaining > 0 { ctx.v_remaining } else { v as i16 };
    
    if available < remaining as i32 {
        return HandlerResult::SetCond(false);
    }
    
    if !requires_explicit_selection {
        let paid = tap_energy_cards_with_logging(state, p_idx, remaining as usize);
        ctx.v_accumulated += paid as i16;
        ctx.v_remaining = -1;
        ctx.choice_index = -1;
        return HandlerResult::SetCond(paid == remaining as usize);
    }
    
    if ctx.choice_index == -1 {
        ctx.v_remaining = remaining;
        return suspend_pay_energy(state, db, ctx, frame_idx, remaining);
    }
    
    let e_idx = ctx.choice_index as usize;
    if e_idx >= state.players[p_idx].energy_zone.len() || state.players[p_idx].is_energy_tapped(e_idx) {
        return HandlerResult::SetCond(false);
    }
    
    if !state.ui.silent {
        eprintln!("Rule 6.3, Rule 6.3.1: Selected Tapping Energy at Index {} for Player {}.", e_idx, p_idx);
    }
    state.players[p_idx].set_energy_tapped(e_idx, true);
    ctx.v_accumulated += 1;
    ctx.choice_index = -1;
    
    let next_remaining = remaining - 1;
    if next_remaining > 0 {
        ctx.v_remaining = next_remaining;
        return suspend_pay_energy(state, db, ctx, frame_idx, next_remaining);
    }
    
    ctx.v_remaining = -1;
    HandlerResult::SetCond(true)
}

pub fn handle_activate_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let v = frame_data.value;
    let p_idx = p_idx(ctx);
    let mut count = 0;
    let mut group_bits = 0u32;
    
    if let Some(card) = db.get_member(ctx.source_card_id) {
        for &g in &card.groups {
            if g < 32 {
                group_bits |= 1 << g;
            }
        }
    }
    
    for i in 0..state.players[p_idx].energy_zone.len() {
        if count >= v {
            break;
        }
        if state.players[p_idx].is_energy_tapped(i) {
            state.players[p_idx].set_energy_tapped(i, false);
            state.players[p_idx].activated_energy_group_mask |= group_bits;
            count += 1;
        }
    }
    HandlerResult::Continue
}

pub fn handle_pay_energy_dynamic(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let v = frame_data.value;
    let p_idx = p_idx(ctx);
    let base_score = state.players[p_idx].score as i32;
    let total_cost = (base_score + v) as usize;
    
    let available = (0..state.players[p_idx].energy_zone.len())
        .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
        .count();
    
    if available < total_cost {
        return HandlerResult::SetCond(false);
    }
    
    let mut paid = 0;
    for i in 0..state.players[p_idx].energy_zone.len() {
        if paid >= total_cost {
            break;
        }
        if !state.players[p_idx].is_energy_tapped(i) {
            state.players[p_idx].set_energy_tapped(i, true);
            paid += 1;
        }
    }
    HandlerResult::SetCond(true)
}

pub fn handle_place_energy_under_member(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let p_idx = p_idx(ctx);
    let slot_info = frame_data.slot;
    let src_zone = slot_info.source_zone as u8;
    
    let slot = match slot_info.target_slot {
        0 | 4 => {
            if ctx.area_idx >= 0 && ctx.area_idx < 3 {
                Some(ctx.area_idx as usize)
            } else {
                None
            }
        }
        10 => {
            if ctx.target_slot >= 0 && ctx.target_slot < 3 {
                Some(ctx.target_slot as usize)
            } else {
                None
            }
        }
        1 | 2 => Some(slot_info.target_slot as usize),
        _ => None,
    };
    
    let Some(slot) = slot else {
        return HandlerResult::Continue;
    };
    
    if src_zone as i32 == crate::core::enums::Zone::Hand as i32 {
        if let Some(cid) = state.players[p_idx].hand.pop() {
            state.players[p_idx].stage_energy[slot].push(cid);
        }
        return HandlerResult::Continue;
    }
    
    match src_zone {
        7 => {
            if let Some(cid) = state.players[p_idx].pop_discard_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        8 => {
            if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        0 => {
            if !state.players[p_idx].energy_zone.is_empty() {
                let selected_idx = if ctx.choice_index >= 0 {
                    Some(ctx.choice_index as usize)
                } else {
                    None
                };
                
                if let Some(idx) = selected_idx.filter(|&idx| idx < state.players[p_idx].energy_zone.len()) {
                    let energy_cid = state.players[p_idx].remove_energy_card(idx).unwrap();
                    state.players[p_idx].stage_energy[slot].push(energy_cid);
                } else {
                    let energy_cid = state.players[p_idx].remove_energy_card(0).unwrap();
                    state.players[p_idx].stage_energy[slot].push(energy_cid);
                }
            } else if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        _ => {
            if !state.players[p_idx].energy_zone.is_empty() {
                for i in 0..state.players[p_idx].energy_zone.len() {
                    if !state.players[p_idx].is_energy_tapped(i) {
                        let energy_cid = state.players[p_idx].remove_energy_card(i).unwrap();
                        state.players[p_idx].stage_energy[slot].push(energy_cid);
                        break;
                    }
                }
            }
        }
    }
    HandlerResult::Continue
}

// ============================================================================
// END OF UNIFIED HANDLERS
// ============================================================================

// HandlerRegistry and dispatch moved to mod.rs to avoid duplication
// All handlers above are accessed via unified::handler_name() from mod.rs dispatch
