/// Position and formation handlers routed through focused submodules.
use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

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
    // Resolve target slot based on resolution mode
    let slot = match resolved_slot {
        // Use context area index (self/same member)
        0 | 4 if ctx.area_idx >= 0 && ctx.area_idx < 3 => ctx.area_idx as usize,
        // Use context target slot (for selected member)
        10 if ctx.target_slot >= 0 && ctx.target_slot < 3 => ctx.target_slot as usize,
        // Explicit slot 1 or 2
        1 | 2 => resolved_slot as usize,
        _ => return HandlerResult::Continue,
    };

    let mut next_ctx = ctx.clone();
    next_ctx.player_id = p_idx as u8;

    // Handle optional choice
    if a & 0x01 != 0 && next_ctx.choice_index == -1 {
        if matches!(
            suspend_choice(
                state, db, ctx, &next_ctx, 0, O_PLACE_UNDER, 0,
                ChoiceType::Optional, a as u64, -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    // Place energy from zone 0 (energy zone) under the member
    if !state.players[p_idx].energy_zone.is_empty() {
        let selected_idx = if next_ctx.choice_index >= 0 {
            Some(next_ctx.choice_index as usize)
        } else {
            None
        };

        if let Some(idx) = selected_idx.filter(|&idx| idx < state.players[p_idx].energy_zone.len()) {
            let energy_cid = state.players[p_idx].remove_energy_card(idx).unwrap();
            state.players[p_idx].stage_energy[slot].push(energy_cid);
        } else if let Some(cid) = state.players[p_idx].pop_deck_card() {
            state.players[p_idx].stage_energy[slot].push(cid);
        }
    } else if let Some(cid) = state.players[p_idx].pop_deck_card() {
        state.players[p_idx].stage_energy[slot].push(cid);
    }

    HandlerResult::Continue
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
) -> HandlerResult {
    let slot = if resolved_slot >= 0 && resolved_slot < 3 {
        resolved_slot as usize
    } else if target_slot >= 0 && target_slot < 3 {
        target_slot as usize
    } else {
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
