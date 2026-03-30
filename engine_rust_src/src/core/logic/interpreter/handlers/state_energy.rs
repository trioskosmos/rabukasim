use crate::core::enums::*;
use crate::core::logic::constants::{CHOICE_DONE, CHOICE_NO};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

/// Main energy handler dispatch
pub fn handle_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: impl Into<AbilityFrame>,
    frame_idx: usize,
) -> HandlerResult {
    let frame: AbilityFrame = frame.into();
    let frame_data = frame.components();
    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let p_idx = ctx.player_id as usize;

    match op {
        O_ENERGY_CHARGE => handle_energy_charge(state, p_idx, frame_data.slot, v),
        O_PAY_ENERGY => handle_pay_energy(state, db, ctx, frame_idx, p_idx, &frame, v),
        O_ACTIVATE_ENERGY => handle_activate_energy(state, db, ctx, p_idx, v),
        O_PAY_ENERGY_DYNAMIC => handle_pay_energy_dynamic(state, p_idx, v),
        O_PLACE_ENERGY_UNDER_MEMBER => handle_place_energy_under_member(state, db, ctx, frame_idx, p_idx, &frame, a),
        _ => HandlerResult::Continue,
    }
}

fn handle_energy_charge(
    state: &mut GameState,
    p_idx: usize,
    slot: crate::core::logic::interpreter::instruction::DecodedSlot,
    v: i32,
) -> HandlerResult {
    let target_p = if slot.is_opponent { 1 - p_idx } else { p_idx };
    let is_wait = slot.is_wait;
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

fn suspend_pay_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    remaining: i16,
) -> HandlerResult {
    suspend_choice(
        state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
        ChoiceType::PayEnergy, 0, remaining,
    )
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

#[allow(unused_variables)]
fn handle_pay_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
    frame: &AbilityFrame,
    _v: i32,
) -> HandlerResult {
    let v = frame.value();
    let available = (0..state.players[p_idx].energy_zone.len())
        .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
        .count() as i32;
    let requires_explicit_selection = state.phase == Phase::Response || ctx.v_remaining > 0 || ctx.choice_index >= 0;
    let frame_data = frame.components();
    let is_optional = frame_data.filter.is_optional;

    if v == -1 {
        if ctx.choice_index == -1 {
            ctx.v_accumulated = 0;
            ctx.v_remaining = -2;
            let options = vec![serde_json::json!({"name": "Done", "text": "Finish paying energy"})];
            let actions = vec![11099];
            return crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice_with_options(
                state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
                ChoiceType::PayEnergy, 0, -2, options, actions,
            );
        } else if ctx.choice_index == CHOICE_DONE {
            ctx.choice_index = -1;
            ctx.v_remaining = -1;
            return HandlerResult::Continue;
        } else if ctx.choice_index >= 0 {
            let e_idx = ctx.choice_index as usize;
            if e_idx < state.players[p_idx].energy_zone.len() && !state.players[p_idx].is_energy_tapped(e_idx) {
                state.players[p_idx].set_energy_tapped(e_idx, true);
                ctx.v_accumulated += 1;
            }
            ctx.choice_index = -1;
            let options = vec![serde_json::json!({"name": "Done", "text": "Finish paying energy"})];
            let actions = vec![11099];
            return crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice_with_options(
                state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
                ChoiceType::PayEnergy, 0, -2, options, actions,
            );
        }
    }

    if is_optional && ctx.choice_index == -1 {
        if available < v {
            return HandlerResult::SetCond(false);
        } else {
            return suspend_choice(
                state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
                ChoiceType::Optional, frame_data.raw_attr, -1,
            );
        }
    }

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
        let mut suspend_ctx = ctx.clone();
        suspend_ctx.v_remaining = remaining;
        return suspend_pay_energy(state, db, &suspend_ctx, frame_idx, remaining);
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
        let mut suspend_ctx = ctx.clone();
        suspend_ctx.v_remaining = next_remaining;
        return suspend_pay_energy(state, db, &suspend_ctx, frame_idx, next_remaining);
    }

    ctx.v_remaining = -1;
    HandlerResult::SetCond(true)
}

fn handle_activate_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
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

fn handle_pay_energy_dynamic(state: &mut GameState, p_idx: usize, v: i32) -> HandlerResult {
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

fn handle_place_energy_under_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
    frame: &AbilityFrame,
    a: i64,
) -> HandlerResult {
    let slot_info = frame.dslot();
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

    if src_zone == 3 {
        return handle_place_energy_from_zone(state, db, ctx, frame_idx, p_idx, slot, a);
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

#[allow(clippy::too_many_arguments)]
fn handle_place_energy_from_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
    slot: usize,
    a: i64,
) -> HandlerResult {
    let is_optional = (a as u64 & crate::core::generated_constants::FILTER_IS_OPTIONAL) != 0;

    if is_optional && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        if matches!(
            suspend_choice(
                state, db, ctx, ctx, frame_idx, O_PLACE_ENERGY_UNDER_MEMBER, 0,
                ChoiceType::Optional, a as u64, -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    if ctx.choice_index == CHOICE_DONE {
        return HandlerResult::SetCond(false);
    }

    let mut next_ctx = ctx.clone();
    if is_optional && ctx.choice_index != -1 && ctx.v_remaining == -1 {
        if ctx.choice_index == 1 {
            return HandlerResult::SetCond(false);
        }
        next_ctx.choice_index = -1;
        next_ctx.v_remaining = 1;
    }

    if next_ctx.choice_index == -1 {
        if state.players[p_idx].energy_zone.is_empty() {
            return HandlerResult::SetCond(false);
        }

        if matches!(
            suspend_choice(
                state, db, ctx, &next_ctx, frame_idx, O_PLACE_ENERGY_UNDER_MEMBER, 0,
                ChoiceType::PayEnergy, a as u64, 1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    let idx = next_ctx.choice_index as usize;
    if idx >= state.players[p_idx].energy_zone.len() || slot >= 3 {
        return HandlerResult::SetCond(false);
    }

    let energy_cid = state.players[p_idx].remove_energy_card(idx).unwrap();
    state.players[p_idx].stage_energy[slot].push(energy_cid);
    HandlerResult::SetCond(true)
}
