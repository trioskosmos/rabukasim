use super::*;
use crate::core::logic::models::AbilityFrameComponents;
#[path = "state_member_play_discard_place.rs"]
mod state_member_play_discard_place;
#[path = "state_member_play_discard_select.rs"]
mod state_member_play_discard_select;

pub use state_member_play_discard_place::handle_discard_placement;

pub fn discard_play_choice_type(target_slot_flags: i32) -> ChoiceType {
    if ((target_slot_flags as u64) & FLAG_BATON_SLOT_ONLY) != 0 {
        ChoiceType::SelectStageEmptyBaton
    } else {
        ChoiceType::SelectStageEmpty
    }
}

pub fn discard_play_slot_is_legal(
    player: &crate::core::logic::PlayerState,
    slot_idx: usize,
    target_slot_flags: i32,
) -> bool {
    if slot_idx >= 3 {
        return false;
    }

    let prevented = (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0;
    let occupied = player.stage[slot_idx] >= 0;
    let baton_only = ((target_slot_flags as u64) & FLAG_BATON_SLOT_ONLY) != 0;

    !prevented
        && !player.is_moved(slot_idx)
        && !occupied
        && (!baton_only || player.baton_source_slots.contains(&slot_idx))
}

pub fn clear_discard_play_buffer(state: &mut GameState, target_p_idx: usize) {
    state.players[target_p_idx].looked_cards.clear();
}

#[allow(clippy::too_many_arguments)]
pub fn handle_play_member_from_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    v: i32,
    a: i64,
    s: i32,
) -> HandlerResult {
    // Distinguish legacy vs modern:
    // Nico (Legacy): a=1 or 2, s=filter_attr
    // Modern: a=filter_attr, s=flags
    let (filter_attr_base, target_p_idx) = if a >= 1 && a <= 2 && (s as u32) > 1000 {
        (
            0, // Legacy player-targeted variant often lacks explicit filter, s contains flags.
            if a == 2 {
                1 - (ctx.activator_id as usize)
            } else {
                ctx.activator_id as usize
            },
        )
    } else {
        let filter_target = (a as u64) & 0x03;
        let is_opp = filter_target == 2 || frame_data.slot.is_opponent;
        let t_idx = if is_opp {
            1 - (ctx.activator_id as usize)
        } else {
            ctx.activator_id as usize
        };
        (a as u64, t_idx)
    };

    let baton_slot_only = ((s as u64) & FLAG_BATON_SLOT_ONLY) != 0;
    let requires_empty_stage_slot = true;

    // Total Cost detection:
    // Support modern bit 60 (compare_accumulated)
    // Support legacy bit 50 (FILTER_TOTAL_COST)
    // Support bit 31 (FILTER_COST_TYPE_FLAG) + bit 30 (FILTER_COST_LE) for legacy compiled cards
    let is_total_cost =
        (filter_attr_base & (1u64 << 60)) != 0 || (filter_attr_base & (1u64 << 50)) != 0;

    let remaining = if ctx.v_remaining == -1 {
        if ctx.repeat_count <= 0 {
            ctx.repeat_count = v as i16;
        }
        if is_total_cost {
            ctx.v_accumulated = ((filter_attr_base
                >> crate::core::logic::constants::FILTER_VALUE_THRESHOLD_SHIFT)
                & 0x1F) as i16;
            ctx.v_accumulated
        } else {
            v as i16
        }
    } else {
        ctx.v_remaining
    };

    if remaining < 0 {
        return HandlerResult::Continue;
    }

    let needs_discard_selection = state.players[target_p_idx].looked_cards.is_empty();

    if needs_discard_selection {
        let selection_result = state_member_play_discard_select::handle_discard_selection(
            state,
            db,
            ctx,
            frame_idx,
            target_p_idx,
            filter_attr_base,
            requires_empty_stage_slot,
            baton_slot_only,
            is_total_cost,
            remaining,
            s,
        );
        if matches!(selection_result, HandlerResult::Continue)
            && !state.players[target_p_idx].looked_cards.is_empty()
            && ctx.choice_index != -1
        {
            return state_member_play_discard_select::handle_discard_selection(
                state,
                db,
                ctx,
                frame_idx,
                target_p_idx,
                filter_attr_base,
                requires_empty_stage_slot,
                baton_slot_only,
                is_total_cost,
                remaining,
                s,
            );
        }
        return selection_result;
    }

    return state_member_play_discard_place::handle_discard_placement(
        state,
        db,
        ctx,
        target_p_idx,
        filter_attr_base,
        requires_empty_stage_slot,
        baton_slot_only,
        is_total_cost,
        frame_idx,
        remaining,
        s,
    );
}
