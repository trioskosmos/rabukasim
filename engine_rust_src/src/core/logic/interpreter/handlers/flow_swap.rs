use super::HandlerResult;
use crate::core::logic::constants::TARGET_SLOT_STAGE;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, GameState};

pub fn handle_swap_area(
    state: &mut GameState,
    ctx: &AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let base_p = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let target_slot = frame_data.slot.target_slot as i32;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let v = frame_data.value;
    let target_p_idx = if slot_info.is_opponent || target_slot == 2 {
        1 - base_p
    } else {
        base_p
    };
    let p = &mut state.players[target_p_idx];
    let temp_stage = p.stage;
    let temp_energy = p.stage_energy_count;
    let temp_tapped = [p.is_tapped(0), p.is_tapped(1), p.is_tapped(2)];
    let temp_moved = [p.is_moved(0), p.is_moved(1), p.is_moved(2)];

    if v == 2 || (a == 1 && s == 0) {
        let src = ctx.area_idx as usize;
        let dst = a as usize;
        if src < 3 && dst < 3 {
            p.stage[src] = temp_stage[dst];
            p.stage[dst] = temp_stage[src];
            p.stage_energy_count[src] = temp_energy[dst];
            p.stage_energy_count[dst] = temp_energy[src];
            p.set_tapped(src, temp_tapped[dst]);
            p.set_tapped(dst, temp_tapped[src]);
            p.set_moved(src, temp_moved[dst]);
            p.set_moved(dst, temp_moved[src]);
        }
    } else if s == TARGET_SLOT_STAGE as i32 {
        p.stage[0] = temp_stage[1];
        p.stage[1] = temp_stage[2];
        p.stage[2] = temp_stage[0];
        p.stage_energy_count[0] = temp_energy[1];
        p.stage_energy_count[1] = temp_energy[2];
        p.stage_energy_count[2] = temp_energy[0];
        p.set_tapped(0, temp_tapped[1]);
        p.set_tapped(1, temp_tapped[2]);
        p.set_tapped(2, temp_tapped[0]);
        p.set_moved(0, temp_moved[1]);
        p.set_moved(1, temp_moved[2]);
        p.set_moved(2, temp_moved[0]);
    } else {
        p.stage[0] = temp_stage[2];
        p.stage[1] = temp_stage[0];
        p.stage[2] = temp_stage[1];
        p.stage_energy_count[0] = temp_energy[2];
        p.stage_energy_count[1] = temp_energy[0];
        p.stage_energy_count[2] = temp_energy[1];
        p.set_tapped(0, temp_tapped[2]);
        p.set_tapped(1, temp_tapped[0]);
        p.set_tapped(2, temp_tapped[1]);
        p.set_moved(0, temp_moved[2]);
        p.set_moved(1, temp_moved[0]);
        p.set_moved(2, temp_moved[1]);
    }

    HandlerResult::Continue
}
