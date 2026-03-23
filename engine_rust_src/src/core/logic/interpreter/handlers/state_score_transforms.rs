use super::*;
use crate::core::logic::interpreter::handlers::state_score_slots::apply_to_target_slots;
use crate::core::logic::models::AbilityFrame;

pub fn handle_transform_color(
    state: &mut GameState,
    ctx: &AbilityContext,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
) -> HandlerResult {
    state.players[p_idx]
        .color_transforms
        .push((ctx.source_card_id, 0, v as u8));
    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(O_TRANSFORM_COLOR, v, a, s, 0) {
            state.log(msg);
        }
    }
    HandlerResult::Continue
}

#[allow(clippy::too_many_arguments)]
pub fn handle_transform_blades(
    state: &mut GameState,
    p_idx: usize,
    v: i32,
    target_p: usize,
    target_slot: i32,
    resolved_slot: i32,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
) -> HandlerResult {
    let _ = p_idx;
    if !state.ui.silent && state.debug.debug_mode {
        println!(
            "[DEBUG] O_TRANSFORM_BLADES: target_p={}, target_slot={}, resolved_slot={}, v={}",
            target_p, target_slot, resolved_slot, v
        );
    }
    apply_to_target_slots(target_slot, resolved_slot, |slot_idx| {
        state.players[target_p].blade_overrides[slot_idx] = v as i16;
    });
    if !state.ui.silent && state.debug.debug_mode {
        println!(
            "[DEBUG] O_TRANSFORM_BLADES Result: slot_0_override={}, slot_1_override={}, slot_2_override={}",
            state.players[target_p].blade_overrides[0],
            state.players[target_p].blade_overrides[1],
            state.players[target_p].blade_overrides[2]
        );
    }
    let _ = slot_info;
    HandlerResult::Continue
}
