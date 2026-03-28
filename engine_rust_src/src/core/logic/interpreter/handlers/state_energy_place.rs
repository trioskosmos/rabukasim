use super::*;
use crate::core::logic::models::AbilityFrame;
#[path = "state_energy_place_select.rs"]
mod state_energy_place_select;

pub fn handle_place_energy_under_member(
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
    let slot = match slot_info.target_slot {
        0 | 4 => {
            if ctx.area_idx >= 0 && ctx.area_idx < 3 {
                Some(ctx.area_idx as usize)
            } else {
                None
            }
        }
        10 => {
            if ctx.target_slot >= 0 && ctx.target_slot < 3 {
                Some(ctx.target_slot as usize)
            } else {
                None
            }
        }
        1 | 2 => Some(slot_info.target_slot as usize),
        _ => None,
    };

    let Some(slot) = slot else {
        return HandlerResult::Continue;
    };

    if src_zone == 3 {
        return state_energy_place_select::handle_place_energy_from_zone(
            state, db, ctx, frame_idx, p_idx, slot, a,
        );
    }

    match src_zone {
        7 => {
            if let Some(cid) = state.players[p_idx].pop_discard_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        8 => {
            if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        0 => {
            if !state.players[p_idx].energy_zone.is_empty() {
                let selected_idx = if ctx.choice_index >= 0 {
                    Some(ctx.choice_index as usize)
                } else {
                    None
                };

                if let Some(idx) =
                    selected_idx.filter(|&idx| idx < state.players[p_idx].energy_zone.len())
                {
                    let energy_cid = state.players[p_idx].remove_energy_card(idx).unwrap();
                    state.players[p_idx].stage_energy[slot].push(energy_cid);
                } else {
                    let energy_cid = state.players[p_idx].remove_energy_card(0).unwrap();
                    state.players[p_idx].stage_energy[slot].push(energy_cid);
                }
            } else if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].stage_energy[slot].push(cid);
            }
        }
        _ => {
            if !state.players[p_idx].energy_zone.is_empty() {
                for i in 0..state.players[p_idx].energy_zone.len() {
                    if !state.players[p_idx].is_energy_tapped(i) {
                        let energy_cid = state.players[p_idx].remove_energy_card(i).unwrap();
                        state.players[p_idx].stage_energy[slot].push(energy_cid);
                        break;
                    }
                }
            }
        }
    }
    HandlerResult::Continue
}
