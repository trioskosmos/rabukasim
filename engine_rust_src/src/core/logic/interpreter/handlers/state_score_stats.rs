use super::*;

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
    if effective_target == 1 {
        for t in 0..3 {
            state.players[target_p].blade_buffs[t] += final_v as i16;
            state.players[target_p].blade_buff_logs.push((
                ctx.source_card_id,
                final_v as i16,
                t as u8,
            ));
        }
    } else if effective_slot >= 0 && effective_slot < 3 {
        state.players[target_p].blade_buffs[effective_slot as usize] += final_v as i16;
        state.players[target_p].blade_buff_logs.push((
            ctx.source_card_id,
            final_v as i16,
            effective_slot as u8,
        ));
    }
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
    a: i64,
    v: i32,
    s: i32,
    resolved_slot: i32,
    target_slot: i32,
) -> HandlerResult {
    let mut color = (a as u64 & FILTER_MASK_LOWER) as usize;
    if color == 7 {
        color = ctx.selected_color as usize;
    }
    if color < 7 {
        if resolved_slot >= 0 && resolved_slot < 3 {
            let slot_idx = resolved_slot as usize;
            state.players[p_idx].heart_buffs[slot_idx].add_to_color(color, v as i32);
            state.players[p_idx].heart_buff_logs.push((
                ctx.source_card_id,
                v,
                color as u8,
                slot_idx as u8,
            ));
        } else if target_slot == 1 {
            for t in 0..3 {
                state.players[p_idx].heart_buffs[t].add_to_color(color, v as i32);
                state.players[p_idx].heart_buff_logs.push((
                    ctx.source_card_id,
                    v,
                    color as u8,
                    t as u8,
                ));
            }
        }
    }
    state.needs_stat_sync = true;
    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(O_ADD_HEARTS, v, a, s, 0) {
            state.log(msg);
        }
    }
    state.log_event(
        "EFFECT",
        &format!("+{} Heart(s)", v),
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
    p_idx: usize,
    a: i64,
    v: i32,
    resolved_slot: i32,
    target_slot: i32,
) -> HandlerResult {
    if (a as usize) < 7 {
        if resolved_slot >= 0 && resolved_slot < 3 {
            state.players[p_idx].heart_buffs[resolved_slot as usize]
                .set_color_count(a as usize, v as u8);
            state.needs_stat_sync = true;
        } else if target_slot == 1 {
            for t in 0..3 {
                state.players[p_idx].heart_buffs[t].set_color_count(a as usize, v as u8);
            }
            state.needs_stat_sync = true;
        }
    }
    HandlerResult::Continue
}

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
    if target_slot == 1 {
        for t in 0..3 {
            state.players[target_p].blade_overrides[t] = v as i16;
        }
    } else if resolved_slot < 3 {
        state.players[target_p].blade_overrides[resolved_slot as usize] = v as i16;
    }
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
