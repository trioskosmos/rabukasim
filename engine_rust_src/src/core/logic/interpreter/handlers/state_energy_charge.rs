use crate::core::logic::models::AbilityFrame;
use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::constants::CHOICE_DONE;

fn suspend_pay_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    remaining: i16,
) -> HandlerResult {
    suspend_choice(
        state,
        db,
        ctx,
        ctx,
        frame_idx,
        O_PAY_ENERGY,
        0,
        ChoiceType::PayEnergy,
        0,
        remaining,
    )
}

pub fn handle_energy_charge(
    state: &mut GameState,
    p_idx: usize,
    slot: crate::core::logic::interpreter::instruction::DecodedSlot,
    v: i32,
) -> HandlerResult {
    let target_p = if slot.is_opponent { 1 - p_idx } else { p_idx };
    let is_wait = slot.is_wait;
    for _ in 0..v {
        if let Some(cid) = state.players[target_p].energy_deck.pop() {
            state.players[target_p].push_energy_card(cid, is_wait);
        }
    }
    HandlerResult::Continue
}

pub fn handle_pay_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
    frame: &AbilityFrame,
    _v: i32, // Ignore param v, use frame.raw_value()
) -> HandlerResult {
    let v = frame.raw_value();
    let available = (0..state.players[p_idx].energy_zone.len())
        .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
        .count() as i32;
    let requires_explicit_selection = state.phase == Phase::Response;

    let is_optional = frame.filter().is_optional;

    // --- CASE 1: Variable Energy Payment (e.g. Card 878) ---
    if v == -1 {
        if ctx.choice_index == -1 {
            // Initial call: Reset accumulation and suspend
            ctx.v_accumulated = 0;
            ctx.v_remaining = -2; // Marker for "variable mode"

            let options = vec![serde_json::json!({
                "name": "Done",
                "text": "Finish paying energy"
            })];
            let actions = vec![11099]; // ChoiceIndices::DONE (99) + ACTION_BASE_CHOICE (11000)

            return crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice_with_options(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                crate::core::enums::O_PAY_ENERGY,
                0,
                crate::core::enums::ChoiceType::PayEnergy,
                0,
                -2,
                options,
                actions,
            );
        } else if ctx.choice_index == 99 {
            // "Done" button pressed
            ctx.choice_index = -1;
            ctx.v_remaining = -1; // Reset marker
            return HandlerResult::Continue;
        } else if ctx.choice_index >= 0 {
            // An energy card was selected
            let e_idx = ctx.choice_index as usize;
            if e_idx < state.players[p_idx].energy_zone.len() && !state.players[p_idx].is_energy_tapped(e_idx) {
                state.players[p_idx].set_energy_tapped(e_idx, true);
                ctx.v_accumulated += 1;
            }

            // Loop back to suspension
            ctx.choice_index = -1;
            let options = vec![serde_json::json!({
                "name": "Done",
                "text": "Finish paying energy"
            })];
            let actions = vec![11099];

            return crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice_with_options(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                crate::core::enums::O_PAY_ENERGY,
                0,
                crate::core::enums::ChoiceType::PayEnergy,
                0,
                -2,
                options,
                actions,
            );
        }
    }

    // --- CASE 2: Fixed Energy Payment (Normal) ---
    if is_optional && ctx.choice_index == -1 {
        if available < v {
            return HandlerResult::SetCond(false);
        } else {
            return suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_PAY_ENERGY,
                0,
                ChoiceType::Optional,
                frame.filter().to_attr(),
                -1,
            );
        }
    }

    // Resumption logic for optional choice
    let actual_v = v;
    if is_optional && ctx.v_remaining == -1 {
        if ctx.choice_index == 1 || ctx.choice_index == CHOICE_DONE {
            ctx.choice_index = -1;
            return HandlerResult::SetCond(false);
        }

        let mut paid = 0;
        let player = &mut state.players[p_idx];
        for i in 0..player.energy_zone.len() {
            if paid >= actual_v {
                break;
            }
            if !player.is_energy_tapped(i) {
                player.set_energy_tapped(i, true);
                paid += 1;
            }
        }

        ctx.choice_index = -1;
        ctx.v_accumulated = paid as i16;
        return HandlerResult::SetCond(paid == actual_v);
    }

    let remaining = if ctx.v_remaining > 0 {
        ctx.v_remaining
    } else {
        actual_v as i16
    };

    if available < remaining as i32 {
        return HandlerResult::SetCond(false);
    }

    if !requires_explicit_selection {
        let mut paid = 0;
        let player = &mut state.players[p_idx];
        for i in 0..player.energy_zone.len() {
            if paid >= remaining as i32 {
                break;
            }
            if !player.is_energy_tapped(i) {
                player.set_energy_tapped(i, true);
                paid += 1;
            }
        }

        ctx.v_accumulated += paid as i16;
        ctx.v_remaining = -1;
        ctx.choice_index = -1;
        return HandlerResult::SetCond(paid == remaining as i32);
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
