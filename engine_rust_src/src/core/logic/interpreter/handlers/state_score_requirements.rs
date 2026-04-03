
use super::*;

pub fn handle_reduce_heart_req(
    state: &mut GameState,

    ctx: &AbilityContext,

    p_idx: usize,

    s: i32,

    v: i32,
) -> HandlerResult {
    if (s as usize) < 7 {
        state.players[p_idx]
            .heart_req_reductions
            .add_to_color(s as usize, v);

        state.players[p_idx]
            .heart_req_reduction_logs
            .push((ctx.source_card_id, s as u8, v as u8));

        if !state.ui.silent {
            if let Some(msg) = logging::get_opcode_log(O_REDUCE_HEART_REQ, v, 0, s, 0) {
                state.log(msg);
            }
        }
    }

    HandlerResult::Continue
}

pub fn handle_transform_heart(
    state: &mut GameState,

    p_idx: usize,

    a: i64,

    s: i32,

    v: i32,
) -> HandlerResult {
    let src = if v == 7 {
        6
    } else if (v as usize) <= 6 {
        v as usize - 1
    } else {
        99
    };

    let dst = if a == 0 || a == 7 {
        6
    } else if (a as usize) <= 6 {
        a as usize - 1
    } else {
        99
    };

    if src < 7 && dst < 7 {
        let amt = v.abs();

        if state.players[p_idx]
            .heart_req_reductions
            .get_color_count(src)
            >= amt as u8
        {
            state.players[p_idx]
                .heart_req_reductions
                .add_to_color(src, -(amt as i32));

            state.players[p_idx]
                .heart_req_reductions
                .add_to_color(dst, amt as i32);

            if !state.ui.silent {
                if let Some(msg) = logging::get_opcode_log(O_TRANSFORM_HEART, v, a, s, 0) {
                    state.log(msg);
                }
            }
        }
    }

    HandlerResult::Continue
}

pub fn handle_increase_heart_cost(
    state: &mut GameState,

    ctx: &AbilityContext,

    p_idx: usize,

    frame: &crate::core::logic::models::AbilityFrameComponents<'_>,
) -> HandlerResult {
    let target_slot = frame.slot.target_slot as usize;
    let color = if let Some(color) =
        crate::core::logic::heart_semantics::decode_heart_type_from_params(frame.params)
    {
        color
    } else if ctx.source_card_id == 4632 {
        6
    } else if matches!(target_slot, 4 | 7) {
        6
    } else if frame.filter.color_mask != 0 {
        if frame.filter.color_mask == 0x7F {
            6
        } else {
            frame.filter.color_mask.trailing_zeros() as usize
        }
    } else {
        match target_slot {
            0..=6 => target_slot,
            _ => 6,
        }
    };

    if color < 7 {
        state.players[p_idx]
            .heart_req_additions
            .add_to_color(color, frame.value);

        state.players[p_idx].heart_req_addition_logs.push((
            ctx.source_card_id,
            color as u8,
            frame.value as u8,
        ));

        if !state.ui.silent {
            if let Some(msg) =
                logging::get_opcode_log(O_INCREASE_HEART_COST, frame.value, 0, color as i32, 0)
            {
                state.log(msg);
            }
        }
    }

    HandlerResult::Continue
}

pub fn handle_set_heart_cost(
    state: &mut GameState,
    ctx: &AbilityContext,
    frame: &crate::core::logic::models::AbilityFrameComponents<'_>,
    p_idx: usize,
    target_p: usize,
    s: i32,
    v: i32,
) -> HandlerResult {
    let mut reqs = Vec::new();

    let (hearts_req, hearts_cost) = frame.heart_requirements();
    
    // Convert tuple to array format for compatibility
    if hearts_req > 0 {
        reqs.push(hearts_req as u8);
    }
    if hearts_cost > 0 {
        reqs.push(hearts_cost as u8);
    }

    if !reqs.is_empty() {
        state.score_req_list = reqs;

        state.score_req_player = target_p as i8;
    }

    let player = &mut state.players[p_idx];

    if v > 0 && v < 16 && (s as usize) < 7 {
        let color_idx = s as usize;

        let old = player.heart_req_additions.get_color_count(color_idx);

        player
            .heart_req_additions
            .set_color_count(color_idx, old.saturating_add(v as u8));

        player
            .heart_req_addition_logs
            .push((ctx.source_card_id, color_idx as u8, v as u8));
    } else {
        // Use the struct version to get proper individual color counts
        let hc = frame.heart_counts_struct();

        let counts = [
            hc.pink as u32,
            hc.red as u32,
            hc.yellow as u32,
            hc.green as u32,
            hc.blue as u32,
            hc.purple as u32,
            hc.any as u32,
        ];

        for (i, &count) in counts.iter().enumerate() {
            if count > 0 {
                let old = player.heart_req_additions.get_color_count(i);

                player
                    .heart_req_additions
                    .set_color_count(i, old.saturating_add(count as u8));

                player
                    .heart_req_addition_logs
                    .push((ctx.source_card_id, i as u8, count as u8));
            }
        }
    }

    HandlerResult::Continue
}
