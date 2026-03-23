use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;

#[allow(clippy::too_many_arguments)]
pub fn handle_place_energy_from_zone(
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
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_PLACE_ENERGY_UNDER_MEMBER,
                0,
                ChoiceType::Optional,
                a as u64,
                -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    if ctx.choice_index == 99 {
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
                state,
                db,
                ctx,
                &next_ctx,
                frame_idx,
                O_PLACE_ENERGY_UNDER_MEMBER,
                0,
                ChoiceType::PayEnergy,
                a as u64,
                1,
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
