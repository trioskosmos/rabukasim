use super::*;
use crate::core::logic::heart_semantics::decode_heart_type_from_params;
use crate::core::logic::models::AbilityFrameComponents;

#[path = "state_score_slots.rs"]
mod state_score_slots;
#[path = "state_score_transforms.rs"]
mod state_score_transforms;

fn decode_heart_color(frame: &AbilityFrameComponents<'_>, ctx: &AbilityContext) -> usize {
    if let Some(color) = decode_heart_type_from_params(frame.params) {
        return color;
    }

    let color_mask = frame.filter.color_mask as usize;
    if color_mask != 0 {
        if color_mask.count_ones() == 1 {
            return color_mask.trailing_zeros() as usize;
        }
        if color_mask == 0x7F {
            return ctx.selected_color as usize;
        }
    }

    match frame.raw_attr {
        0 => ctx.selected_color as usize,
        7 => 6,
        raw if raw <= 6 => raw as usize,
        _ => ctx.selected_color as usize,
    }
}

#[allow(clippy::too_many_arguments)]
pub fn handle_add_blades(
    state: &mut GameState,
    ctx: &AbilityContext,
    p_idx: usize,
    target_p: usize,
    a: i64,
    v: i32,
    target_slot: i32,
    resolved_slot: i32,
) -> HandlerResult {
    let _ = p_idx;
    let effective_target = target_slot & 0x7F;
    let effective_slot = if effective_target == 10 {
        ctx.target_slot as i32
    } else if effective_target == 0 && ctx.area_idx >= 0 {
        ctx.area_idx as i32
    } else {
        resolve_target_slot(effective_target, ctx) as i32
    };
    let mut final_v = v;
    if (a as u64 & DYNAMIC_VALUE) != 0 {
        let count = ctx.selected_cards.len() as i32;
        final_v = v * count;
    }
    state_score_slots::apply_to_target_slots(effective_target, effective_slot, |slot_idx| {
        state.players[target_p].blade_buffs[slot_idx] += final_v as i16;
        state.players[target_p].blade_buff_logs.push((
            ctx.source_card_id,
            final_v as i16,
            slot_idx as u8,
        ));
    });
    state.needs_stat_sync = true;
    state.log_event(
        "EFFECT",
        &format!("+{} Appeal", final_v),
        ctx.source_card_id,
        ctx.ability_index,
        target_p as u8,
        None,
        true,
    );
    let _ = resolved_slot;
    HandlerResult::Continue
}

pub fn handle_set_blades(
    state: &mut GameState,
    p_idx: usize,
    v: i32,
    resolved_slot: i32,
) -> HandlerResult {
    if resolved_slot < 3 {
        state.players[p_idx].blade_buffs[resolved_slot as usize] = v as i16;
        state.needs_stat_sync = true;
    }
    HandlerResult::Continue
}

#[allow(clippy::too_many_arguments)]
pub fn handle_add_hearts(
    state: &mut GameState,
    ctx: &AbilityContext,
    p_idx: usize,
    frame: &AbilityFrameComponents<'_>,
    resolved_slot: i32,
    target_slot: i32,
) -> HandlerResult {
    let color = decode_heart_color(frame, ctx);
    if color < 7 {
        state_score_slots::apply_to_target_slots(target_slot, resolved_slot, |slot_idx| {
            state.players[p_idx].heart_buffs[slot_idx].add_to_color(color, frame.value as i32);
            state.players[p_idx].heart_buff_logs.push((
                ctx.source_card_id,
                frame.value,
                color as u8,
                slot_idx as u8,
            ));
        });
    }
    state.needs_stat_sync = true;
    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(
            O_ADD_HEARTS,
            frame.value,
            frame.raw_attr as i64,
            frame.raw_slot,
            0,
        ) {
            state.log(msg);
        }
    }
    state.log_event(
        "EFFECT",
        &format!("+{} Heart(s)", frame.value),
        ctx.source_card_id,
        ctx.ability_index,
        p_idx as u8,
        None,
        true,
    );
    HandlerResult::Continue
}

#[allow(clippy::too_many_arguments)]
pub fn handle_set_hearts(
    state: &mut GameState,
    ctx: &AbilityContext,
    p_idx: usize,
    frame: &AbilityFrameComponents<'_>,
    resolved_slot: i32,
    target_slot: i32,
) -> HandlerResult {
    let color = decode_heart_color(frame, ctx);
    if color < 7 {
        state_score_slots::apply_to_target_slots(target_slot, resolved_slot, |slot_idx| {
            state.players[p_idx].heart_buffs[slot_idx].set_color_count(color, frame.value as u8);
        });
        state.needs_stat_sync = true;
    }
    HandlerResult::Continue
}

pub use state_score_transforms::{handle_transform_blades, handle_transform_color};
