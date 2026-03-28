use crate::core::enums::*;
use crate::core::logic::constants::{CHOICE_DONE, CHOICE_NO, FILTER_IS_OPTIONAL};
use crate::core::logic::interpreter::handlers::choice_prompt::{suspend_choice, suspend_choice_with_options};
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

/// Energy operation router - dispatches to specific handlers based on opcode
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
    let p_idx = ctx.player_id as usize;

    match op {
        O_ENERGY_CHARGE => handle_energy_charge(state, p_idx, frame.dslot(), frame_data.value),
        O_PAY_ENERGY => handle_pay_energy(state, db, ctx, frame_idx, p_idx, &frame, frame.raw_value()),
        O_ACTIVATE_ENERGY => handle_activate_energy(state, db, ctx, p_idx, frame_data.value),
        O_PAY_ENERGY_DYNAMIC => handle_pay_energy_dynamic(state, p_idx, frame_data.value),
        O_PLACE_ENERGY_UNDER_MEMBER => handle_place_energy_under_member(state, db, ctx, frame_idx, p_idx, &frame, frame_data.raw_attr as i64),
        _ => HandlerResult::Continue,
    }
}

// =============================================================================
// ENERGY CHARGE
// =============================================================================

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
                state.log(format!(
                    "Rule 6.1, Rule 6.1.1: [エナジーを送る] (Energy Charge) for Player {}.",
                    target_p
                ));
            }
            state.players[target_p].push_energy_card(cid, is_wait);
        }
    }
    HandlerResult::Continue
}

// =============================================================================
// ENERGY PAYMENT
// =============================================================================

fn handle_pay_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
    frame: &AbilityFrame,
    v: i32,
) -> HandlerResult {
    let available = count_untapped_energy(state, p_idx);
    let requires_explicit_selection = state.phase == Phase::Response || ctx.v_remaining > 0 || ctx.choice_index >= 0;
    let frame_data = frame.components();
    let is_optional = frame_data.filter.is_optional;

    // Variable energy payment mode (v == -1)
    if v == -1 {
        return handle_variable_energy_payment(state, db, ctx, frame_idx, p_idx);
    }

    // Optional payment with confirmation prompt
    if is_optional && ctx.choice_index == -1 {
        if available < v {
            return HandlerResult::SetCond(false);
        }
        return suspend_for_optional_choice(state, db, ctx, frame_idx, frame_data.raw_attr);
    }

    // Handle optional choice resumption
    if is_optional && ctx.v_remaining == -1 {
        return resume_optional_payment(state, ctx, p_idx, v);
    }

    // Calculate remaining payment
    let remaining = if ctx.v_remaining > 0 { ctx.v_remaining } else { v as i16 };

    if available < remaining as i32 {
        return HandlerResult::SetCond(false);
    }

    // Auto-tap if no explicit selection needed
    if !requires_explicit_selection {
        let paid = tap_energy_cards_with_logging(state, p_idx, remaining as usize);
        ctx.v_accumulated += paid as i16;
        reset_payment_context(ctx);
        return HandlerResult::SetCond(paid == remaining as usize);
    }

    // Interactive selection mode
    if ctx.choice_index == -1 {
        return suspend_for_energy_selection(state, db, ctx, frame_idx, remaining);
    }

    // Process selected energy card
    process_energy_selection(state, ctx, p_idx, remaining, frame_idx, db)
}

fn handle_variable_energy_payment(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
) -> HandlerResult {
    if ctx.choice_index == -1 {
        ctx.v_accumulated = 0;
        ctx.v_remaining = -2;

        let options = vec![serde_json::json!({
            "name": "Done",
            "text": "Finish paying energy"
        })];
        let actions = vec![11099];

        return suspend_choice_with_options(
            state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
            ChoiceType::PayEnergy, 0, -2, options, actions,
        );
    }

    if ctx.choice_index == CHOICE_DONE {
        ctx.choice_index = -1;
        ctx.v_remaining = -1;
        return HandlerResult::Continue;
    }

    if ctx.choice_index >= 0 {
        let e_idx = ctx.choice_index as usize;
        if e_idx < state.players[p_idx].energy_zone.len() && !state.players[p_idx].is_energy_tapped(e_idx) {
            state.players[p_idx].set_energy_tapped(e_idx, true);
            ctx.v_accumulated += 1;
        }

        ctx.choice_index = -1;
        let options = vec![serde_json::json!({
            "name": "Done",
            "text": "Finish paying energy"
        })];
        let actions = vec![11099];

        return suspend_choice_with_options(
            state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0,
            ChoiceType::PayEnergy, 0, -2, options, actions,
        );
    }

    HandlerResult::Continue
}

fn resume_optional_payment(
    state: &mut GameState,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    if ctx.choice_index == CHOICE_NO || ctx.choice_index == CHOICE_DONE {
        ctx.choice_index = -1;
        return HandlerResult::SetCond(false);
    }

    let paid = tap_energy_cards_with_logging(state, p_idx, v as usize);
    reset_payment_context(ctx);
    ctx.v_accumulated = paid as i16;
    HandlerResult::SetCond(paid == v as usize)
}

fn process_energy_selection(
    state: &mut GameState,
    ctx: &mut AbilityContext,
    p_idx: usize,
    remaining: i16,
    frame_idx: usize,
    db: &CardDatabase,
) -> HandlerResult {
    let e_idx = ctx.choice_index as usize;

    if e_idx >= state.players[p_idx].energy_zone.len() || state.players[p_idx].is_energy_tapped(e_idx) {
        return HandlerResult::SetCond(false);
    }

    if !state.ui.silent {
        eprintln!(
            "Rule 6.3, Rule 6.3.1: Selected Tapping Energy at Index {} for Player {}.",
            e_idx, p_idx
        );
    }

    state.players[p_idx].set_energy_tapped(e_idx, true);
    ctx.v_accumulated += 1;
    ctx.choice_index = -1;

    let next_remaining = remaining - 1;
    if next_remaining > 0 {
        ctx.v_remaining = next_remaining;
        return suspend_for_energy_selection(state, db, ctx, frame_idx, next_remaining);
    }

    ctx.v_remaining = -1;
    HandlerResult::SetCond(true)
}

fn count_untapped_energy(state: &GameState, p_idx: usize) -> i32 {
    (0..state.players[p_idx].energy_zone.len())
        .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
        .count() as i32
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

fn reset_payment_context(ctx: &mut AbilityContext) {
    ctx.v_remaining = -1;
    ctx.choice_index = -1;
}

fn suspend_for_optional_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    raw_attr: u64,
) -> HandlerResult {
    if matches!(
        suspend_choice(state, db, ctx, ctx, frame_idx, O_PAY_ENERGY, 0, ChoiceType::Optional, raw_attr, -1),
        HandlerResult::Suspend
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}

fn suspend_for_energy_selection(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    remaining: i16,
) -> HandlerResult {
    let mut suspend_ctx = ctx.clone();
    suspend_ctx.v_remaining = remaining;

    if matches!(
        suspend_choice(state, db, ctx, &suspend_ctx, frame_idx, O_PAY_ENERGY, 0, ChoiceType::PayEnergy, 0, remaining),
        HandlerResult::Suspend
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}

// =============================================================================
// ENERGY ACTIVATION
// =============================================================================

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
        if count >= v { break; }
        if state.players[p_idx].is_energy_tapped(i) {
            state.players[p_idx].set_energy_tapped(i, false);
            state.players[p_idx].activated_energy_group_mask |= group_bits;
            count += 1;
        }
    }

    HandlerResult::Continue
}

// =============================================================================
// DYNAMIC ENERGY PAYMENT
// =============================================================================

fn handle_pay_energy_dynamic(state: &mut GameState, p_idx: usize, v: i32) -> HandlerResult {
    let base_score = state.players[p_idx].score as i32;
    let total_cost = (base_score + v) as usize;
    let available = count_untapped_energy(state, p_idx) as usize;

    if available < total_cost {
        return HandlerResult::SetCond(false);
    }

    let mut paid = 0;
    for i in 0..state.players[p_idx].energy_zone.len() {
        if paid >= total_cost { break; }
        if !state.players[p_idx].is_energy_tapped(i) {
            state.players[p_idx].set_energy_tapped(i, true);
            paid += 1;
        }
    }

    HandlerResult::SetCond(true)
}

// =============================================================================
// PLACE ENERGY UNDER MEMBER
// =============================================================================

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

    let slot = resolve_target_slot(ctx, slot_info.target_slot);
    let Some(slot) = slot else { return HandlerResult::Continue };

    if src_zone == 3 {
        return handle_place_energy_from_zone(state, db, ctx, frame_idx, p_idx, slot, a);
    }

    match src_zone {
        7 => { // Discard
            if let Some(cid) = state.players[p_idx].pop_discard_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        8 => { // Deck
            if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        0 => { // Energy zone with selection
            handle_energy_zone_placement(state, ctx, p_idx, slot);
        }
        _ => { // Untapped energy
            place_untapped_energy(state, p_idx, slot);
        }
    }

    HandlerResult::Continue
}

fn resolve_target_slot(ctx: &AbilityContext, target_slot: u8) -> Option<usize> {
    match target_slot {
        0 | 4 if ctx.area_idx >= 0 && ctx.area_idx < 3 => Some(ctx.area_idx as usize),
        10 if ctx.target_slot >= 0 && ctx.target_slot < 3 => Some(ctx.target_slot as usize),
        1 | 2 => Some(target_slot as usize),
        _ => None,
    }
}

fn handle_energy_zone_placement(state: &mut GameState, ctx: &AbilityContext, p_idx: usize, slot: usize) {
    if state.players[p_idx].energy_zone.is_empty() {
        return;
    }

    let selected_idx = if ctx.choice_index >= 0 {
        Some(ctx.choice_index as usize)
    } else {
        None
    };

    if let Some(idx) = selected_idx.filter(|&idx| idx < state.players[p_idx].energy_zone.len()) {
        // Use selected energy from zone
        let energy_cid = state.players[p_idx].remove_energy_card(idx).unwrap();
        state.players[p_idx].stage_energy[slot].push(energy_cid);
    } else {
        // No selection - take first available from energy_zone (not deck)
        let energy_cid = state.players[p_idx].remove_energy_card(0).unwrap();
        state.players[p_idx].stage_energy[slot].push(energy_cid);
    }
}

fn place_untapped_energy(state: &mut GameState, p_idx: usize, slot: usize) {
    if state.players[p_idx].energy_zone.is_empty() {
        return;
    }

    for i in 0..state.players[p_idx].energy_zone.len() {
        if !state.players[p_idx].is_energy_tapped(i) {
            let energy_cid = state.players[p_idx].remove_energy_card(i).unwrap();
            state.players[p_idx].stage_energy[slot].push(energy_cid);
            break;
        }
    }
}

fn handle_place_energy_from_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
    slot: usize,
    a: i64,
) -> HandlerResult {
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;

    if is_optional && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        if matches!(
            suspend_choice(state, db, ctx, ctx, frame_idx, O_PLACE_ENERGY_UNDER_MEMBER, 0, ChoiceType::Optional, a as u64, -1),
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
            suspend_choice(state, db, ctx, &next_ctx, frame_idx, O_PLACE_ENERGY_UNDER_MEMBER, 0, ChoiceType::PayEnergy, a as u64, 1),
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
