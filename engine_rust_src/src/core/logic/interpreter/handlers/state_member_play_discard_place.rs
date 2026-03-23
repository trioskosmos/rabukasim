use crate::core::logic::models::AbilityFrame;
use super::*;

#[allow(clippy::too_many_arguments)]
pub fn handle_discard_placement(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    target_p_idx: usize,
    empty_slot_only: bool,
    is_total_cost: bool,
    frame_idx: usize,
    remaining: i16,
) -> HandlerResult {
    if state.players[target_p_idx].looked_cards.is_empty() {
        return HandlerResult::Continue;
    }
    let card_id = state.players[target_p_idx].looked_cards.remove(0);

    if ctx.choice_index == 99 {
        return HandlerResult::Continue;
    }

    let resolved_slot = if ctx.choice_index >= 600 && ctx.choice_index < 603 {
        ctx.choice_index - 600
    } else if ctx.choice_index >= 10 && ctx.choice_index < 13 {
        ctx.choice_index - 10
    } else {
        ctx.choice_index
    };

    let slot_idx = if ctx.choice_index >= 0 && ctx.choice_index < 3 {
        ctx.choice_index as usize
    } else {
        resolved_slot as usize
    };
    if slot_idx < 3 {
        let _ = state_member_play_resolve::finalize_play_member_from_discard(
            state,
            db,
            ctx,
            target_p_idx,
            card_id,
            slot_idx,

            empty_slot_only,
            is_total_cost,
        );
    }

    let remaining = remaining - 1;
    ctx.v_remaining = remaining;
    if remaining > 0 {
        ctx.choice_index = -1;
        return HandlerResult::Branch(frame_idx);
    }

    HandlerResult::Continue
}
