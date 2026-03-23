use super::*;
use crate::core::logic::models::AbilityFrame;
#[path = "state_member_play_discard_place.rs"]
mod state_member_play_discard_place;
#[path = "state_member_play_discard_select.rs"]
mod state_member_play_discard_select;

#[allow(clippy::too_many_arguments)]
pub fn handle_play_member_from_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
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
        let is_opp = filter_target == 2 || frame.dslot().is_opponent;
        let t_idx = if is_opp {
            1 - (ctx.activator_id as usize)
        } else {
            ctx.activator_id as usize
        };
        (a as u64, t_idx)
    };

    let empty_slot_only = ((s as u64) & FLAG_EMPTY_SLOT_ONLY) != 0;
    let baton_slot_only = ((s as u64) & FLAG_BATON_SLOT_ONLY) != 0;

    // Total Cost detection:
    // Support modern bit 60 (compare_accumulated)
    // Support legacy bit 50 (FILTER_TOTAL_COST)
    // Support bit 31 (FILTER_COST_TYPE_FLAG) + bit 30 (FILTER_COST_LE) for legacy compiled cards
    let is_total_cost = (filter_attr_base & (1u64 << 60)) != 0
        || (filter_attr_base & (1u64 << 50)) != 0
        || ((filter_attr_base & FILTER_COST_TYPE_FLAG) != 0
            && (filter_attr_base & 1073741824) != 0);

    let remaining = if ctx.v_remaining == -1 {
        if is_total_cost {
            ctx.v_accumulated = ((filter_attr_base
                >> crate::core::logic::constants::FILTER_VALUE_THRESHOLD_SHIFT)
                & 0x1F) as i16;
        }
        v as i16 * 2
    } else {
        ctx.v_remaining
    };

    if remaining <= 0 {
        return HandlerResult::Continue;
    }

    if remaining % 2 == 0 {
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
            remaining,
            s,
        );
    } else {
        return state_member_play_discard_place::handle_discard_placement(
            state,
            db,
            ctx,
            target_p_idx,
            empty_slot_only,
            is_total_cost,
            frame_idx,
            remaining,
        );
    }
}
