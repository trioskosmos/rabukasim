/// Position and formation handlers routed through focused submodules.
use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;

#[path = "state_energy_place.rs"]
mod state_energy_place;
#[path = "state_member_formation.rs"]
mod state_member_formation;
#[path = "state_member_move.rs"]
mod state_member_move;

pub use state_member_formation::handle_formation_change;
pub use state_member_move::handle_move_member;

#[allow(clippy::too_many_arguments)]
pub fn handle_place_under(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let slot = if ctx.area_idx >= 0 {
        ctx.area_idx as usize
    } else {
        resolved_slot as usize
    };
    if slot >= 3 {
        return HandlerResult::Continue;
    }

    let mut next_ctx = ctx.clone();
    next_ctx.player_id = p_idx as u8;
    if a & 0x01 != 0 && next_ctx.choice_index == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                &next_ctx,
                0,
                O_PLACE_UNDER,
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

    return state_energy_place::handle_place_energy_under_member(
        state,
        db,
        &mut next_ctx,
        0,
        p_idx,
        &AbilityFrame::new(O_PLACE_ENERGY_UNDER_MEMBER, 0, a, 0, true),
        a,
    );
}

pub fn handle_add_stage_energy(
    state: &mut GameState,
    p_idx: usize,
    v: i32,
    resolved_slot: i32,
) -> HandlerResult {
    if resolved_slot < 0 || resolved_slot >= 3 {
        return HandlerResult::Continue;
    }
    let slot = resolved_slot as usize;
    for _ in 0..v.max(0) {
        if let Some(cid) = state.players[p_idx].deck.pop() {
            state.players[p_idx].stage_energy[slot].push(cid);
        }
    }
    state.players[p_idx].sync_stage_energy_count(slot);
    HandlerResult::Continue
}

pub fn handle_grant_ability(
    state: &mut GameState,
    p_idx: usize,
    source_cid: i32,
    v: i32,
    target_slot: i32,
    resolved_slot: i32,
    selected_target_cid: Option<i32>,
) -> HandlerResult {
    let slot = if let Some(selected_cid) = selected_target_cid {
        state.players[p_idx]
            .stage
            .iter()
            .position(|&cid| cid == selected_cid)
            .or_else(|| {
                if resolved_slot >= 0 && resolved_slot < 3 {
                    Some(resolved_slot as usize)
                } else if target_slot >= 0 && target_slot < 3 {
                    Some(target_slot as usize)
                } else {
                    None
                }
            })
    } else if resolved_slot >= 0 && resolved_slot < 3 {
        Some(resolved_slot as usize)
    } else if target_slot >= 0 && target_slot < 3 {
        Some(target_slot as usize)
    } else {
        None
    };
    let Some(slot) = slot else {
        return HandlerResult::Continue;
    };
    let target_cid = state.players[p_idx].stage[slot];
    if target_cid < 0 {
        return HandlerResult::Continue;
    }

    if v >= 0 {
        state.players[p_idx]
            .granted_abilities
            .push((target_cid, source_cid, v as u16));
    }
    HandlerResult::Continue
}
