use super::*;
use crate::core::logic::constants::CHOICE_DONE;

#[allow(clippy::too_many_arguments)]
pub fn handle_discard_placement(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    target_p_idx: usize,
    filter_attr_base: u64,
    empty_slot_only: bool,
    baton_slot_only: bool,
    is_total_cost: bool,
    frame_idx: usize,
    remaining: i16,
    s: i32,
) -> HandlerResult {
    if state.players[target_p_idx].looked_cards.is_empty() {
        return HandlerResult::Continue;
    }
    if ctx.choice_index == CHOICE_DONE {
        return HandlerResult::Continue;
    }

    let card_id = if ctx.target_card_id >= 0 {
        ctx.target_card_id
    } else {
        state.players[target_p_idx]
            .looked_cards
            .first()
            .copied()
            .unwrap_or(-1)
    };
    if card_id < 0 {
        return HandlerResult::Continue;
    }

    if let Some(pos) = state.players[target_p_idx]
        .looked_cards
        .iter()
        .position(|&cid| cid == card_id)
    {
        state.players[target_p_idx].looked_cards.remove(pos);
    } else {
        return HandlerResult::Continue;
    }

    let resolved_slot = if ctx.choice_index >= 600 && ctx.choice_index < 603 {
        ctx.choice_index - 600
    } else if ctx.choice_index >= 10 && ctx.choice_index < 13 {
        ctx.choice_index - 10
    } else if ctx.choice_index >= 11000 && ctx.choice_index < 11003 {
        // ACTION_BASE_CHOICE + slot_idx
        ctx.choice_index - 11000
    } else {
        ctx.choice_index
    };

    let slot_idx = if ctx.choice_index >= 0 && ctx.choice_index < 3 {
        ctx.choice_index as usize
    } else {
        resolved_slot as usize
    };
    
    if state.debug.debug_mode && !state.ui.silent {
        println!("[DEBUG] handle_discard_placement: choice_index={}, resolved_slot={}, slot_idx={}, card_id={}", 
            ctx.choice_index, resolved_slot, slot_idx, card_id);
    }
    
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
                        next_remaining > 0
                    }
                })
                .unwrap_or(false)
                && !ctx.selected_cards.contains(&cid)
        })
    } else {
        false
    };
    let should_continue = if is_total_cost {
        ctx.v_accumulated > 0 && next_remaining > 0 && has_more_candidates
    } else {
        next_remaining > 0 && has_more_candidates
    };
    if should_continue {
        ctx.choice_index = -1;
        ctx.target_card_id = -1;
        ctx.v_remaining = next_remaining;
        return state_member_play_discard_select::handle_discard_selection(
            state,
            db,
            ctx,
            frame_idx,
            target_p_idx,
            filter_attr_base,
            empty_slot_only,
            baton_slot_only,
            is_total_cost,
            next_remaining,
            s,
        );
    }

    HandlerResult::Continue
}
