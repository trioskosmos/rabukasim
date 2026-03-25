use super::*;
use crate::core::logic::models::AbilityFrame;

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
    if ctx.choice_index == 99 {
        return HandlerResult::Continue;
    }

    let card_id = state.players[target_p_idx].looked_cards.remove(0);
    state.players[target_p_idx].looked_cards.clear();

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

    let next_remaining = if is_total_cost {
        remaining
    } else {
        remaining.saturating_sub(1)
    };

    ctx.v_remaining = next_remaining;
    let has_more_candidates = if next_remaining > 0 {
        state.players[target_p_idx].discard.iter().any(|&cid| {
            db.get_member(cid)
                .map(|member| {
                    if is_total_cost {
                        member.cost as i16 <= next_remaining
                    } else {
                        // For count-based play, we need at least 2 steps (select card + select slot)
                        // This check is used to decide if we should branch back to selection.
                        // If we only have 1 step left, we can't select another card.
                        next_remaining >= 2
                    }
                })
                .unwrap_or(false)
                && !ctx.selected_cards.contains(&cid)
        })
    } else {
        false
    };
    let should_continue = if is_total_cost {
        ctx.v_accumulated > 0
            && next_remaining > 0
            && has_more_candidates
            && ctx.repeat_count > 0
    } else {
        next_remaining > 0 && has_more_candidates && ctx.repeat_count > 0
    };
    if should_continue {
        ctx.choice_index = -1;
        return HandlerResult::Branch(frame_idx);
    }

    HandlerResult::Continue
}
