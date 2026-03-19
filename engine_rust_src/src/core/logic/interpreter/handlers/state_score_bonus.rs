use super::*;

pub fn handle_boost_score(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    p_idx: usize,
    target_p: usize,
) -> HandlerResult {
    if ctx.v_accumulated >= 0 {
        if let Some(min_required) = inline_value_ge_threshold(db, ctx) {
            if (ctx.v_accumulated as i32) < min_required {
                return HandlerResult::Continue;
            }
        }
    }

    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;

    let mut final_v = v;
    if instr.is_dynamic() {
        let divisor = instr.scalar_dynamic_divisor().max(1);
        let base = instr.scalar_dynamic_base();
        let paid = ctx.v_accumulated as i32;
        final_v = base * (paid / divisor);
    } else if instr.filter_attr().compare_accumulated {
        let count = resolve_count(
            state,
            db,
            instr.raw_s,
            (instr.filter_attr().to_attr() & 0xFFFFFFFF) as u64,
            p_idx as i32,
            ctx,
            0,
        );
        final_v = v * count;
    }
    state.players[target_p].live_score_bonus += final_v;
    state.players[target_p]
        .live_score_bonus_logs
        .push((ctx.source_card_id, final_v));

    if state.phase == Phase::PerformanceP1
        || state.phase == Phase::PerformanceP2
        || state.phase == Phase::LiveResult
    {
        state.players[target_p].score =
            (state.players[target_p].score as i32 + final_v).max(0) as u32;
    }
    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(O_BOOST_SCORE, final_v, a, s, 0) {
            state.log(msg);
        }
    }
    HandlerResult::Continue
}

pub fn handle_reduce_cost(
    state: &mut GameState,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    let mut final_v = v;

    if instr.filter_attr().compare_accumulated {
        let filter_attr = instr.filter_attr().to_attr() & 0xFFFFFFFF;
        let filter = crate::core::logic::filter::CardFilter::from_attr(filter_attr as i64);
        let mut count = 0i32;
        let player = &state.players[p_idx];
        let zone_mask = filter.zone_mask as u64;
        if zone_mask == 0 {
            for &card_id in player.hand.iter() {
                if card_id >= 0 && card_id as i32 != ctx.source_card_id {
                    count += 1;
                }
            }
        } else {
            if (zone_mask & crate::core::enums::ZONE_HAND as u64) != 0 {
                for &card_id in player.hand.iter() {
                    if card_id >= 0 && card_id as i32 != ctx.source_card_id {
                        count += 1;
                    }
                }
            }
            if (zone_mask & crate::core::enums::ZONE_STAGE as u64) != 0 {
                for &card_id in player.stage.iter() {
                    if card_id >= 0 && card_id as i32 != ctx.source_card_id {
                        count += 1;
                    }
                }
            }
        }
        final_v = v * count;
    }
    state.players[p_idx].cost_reduction += final_v as i16;
    HandlerResult::Continue
}

pub fn handle_set_score(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    target_p: usize,
    v: i32,
) -> HandlerResult {
    let mut applied_to_live_snapshot = false;
    if db.get_live(ctx.source_card_id).is_some() {
        applied_to_live_snapshot =
            update_live_score_snapshot(state, target_p, ctx.source_card_id, ctx.area_idx, v);
    }

    if !applied_to_live_snapshot {
        state.players[target_p].score = v.max(0) as u32;
    } else {
        state.players[target_p].score = v.max(0) as u32;
    }
    HandlerResult::Continue
}

pub fn handle_reduce_score(state: &mut GameState, target_p: usize, v: i32) -> HandlerResult {
    let reduction = v.min(state.players[target_p].live_score_bonus);
    state.players[target_p].live_score_bonus -= reduction;
    HandlerResult::Continue
}

pub fn handle_lose_excess_hearts(
    state: &mut GameState,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    let player = &mut state.players[p_idx];
    let reduction = if v == 0 { player.excess_hearts } else { v as u32 };
    player.excess_hearts = player.excess_hearts.saturating_sub(reduction);
    HandlerResult::Continue
}

pub fn handle_skip_activate_phase(state: &mut GameState, p_idx: usize) -> HandlerResult {
    state.players[p_idx].skip_next_activate = true;
    HandlerResult::Continue
}
