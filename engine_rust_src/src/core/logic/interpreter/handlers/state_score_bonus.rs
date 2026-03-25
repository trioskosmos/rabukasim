use super::*;
use crate::core::enums::Zone;
use crate::core::logic::constants::{
    C_COUNT_DISCARD, C_COUNT_HAND, C_COUNT_STAGE, C_COUNT_SUCCESS_LIVE,
};
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::models::AbilityFrame;

fn resolve_dynamic_multiplier(
    state: &GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_data: &crate::core::logic::models::AbilityFrameComponents<'_>,
) -> Option<i32> {
    let count_opcode = frame_data
        .params
        .and_then(|value| value.as_object())
        .and_then(|params| params.get("per_card").or_else(|| params.get("PER_CARD")))
        .and_then(|value| value.as_str())
        .map(|per_card| match per_card.to_ascii_uppercase().as_str() {
            "HAND" => C_COUNT_HAND,
            "DISCARD" | "DISCARD_COUNT" => C_COUNT_DISCARD,
            "SUCCESS_LIVE" | "SUCCESS_PILE" | "COUNT" | "COUNT_VAL" => C_COUNT_SUCCESS_LIVE,
            "STAGE" => C_COUNT_STAGE,
            _ => 0,
        })
        .filter(|opcode| *opcode != 0)
        .or_else(|| match frame_data.slot.source_zone {
            Zone::Hand => Some(C_COUNT_HAND),
            Zone::Discard => Some(C_COUNT_DISCARD),
            Zone::Stage => Some(C_COUNT_STAGE),
            Zone::SuccessPile => Some(C_COUNT_SUCCESS_LIVE),
            _ => None,
        });

    count_opcode.map(|opcode| {
        let mut count = resolve_count(
            state,
            db,
            opcode,
            frame_data.raw_attr,
            frame_data.raw_slot,
            ctx,
            0,
        );

        // Some legacy bytecode paths dropped NOT_SELF metadata for dynamic
        // REDUCE_COST effects in hand. Keep the authored-frame semantics by
        // excluding the source card when it is part of the counted zone.
        if frame_data.opcode == O_REDUCE_COST
            && frame_data.filter.special_id == 0
            && frame_data.raw_attr == 0
            && count > 0
        {
            let p_idx = ctx.player_id as usize;
            let owner_idx = if frame_data.slot.is_opponent {
                1 - p_idx
            } else {
                p_idx
            };
            let source_card_id = ctx.source_card_id;
            let source_is_counted = match frame_data.slot.source_zone {
                Zone::Hand => state.players[owner_idx]
                    .hand
                    .iter()
                    .any(|&id| id == source_card_id),
                Zone::Stage => state.players[owner_idx]
                    .stage
                    .iter()
                    .any(|&id| id == source_card_id),
                Zone::Discard => state.players[owner_idx]
                    .discard
                    .iter()
                    .any(|&id| id == source_card_id),
                Zone::SuccessPile => state.players[owner_idx]
                    .success_lives
                    .iter()
                    .any(|&id| id == source_card_id),
                _ => false,
            };
            if source_is_counted {
                count -= 1;
            }
        }

        count
    })
}

pub fn handle_boost_score(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
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

    let frame_data = frame.components();
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;

    let mut final_v = v;
    if frame.is_dynamic() {
        let divisor = frame.scalar_dynamic_divisor().max(1);
        let base = frame.scalar_dynamic_base();
        let paid = ctx.v_accumulated as i32;
        final_v = base * (paid / divisor);
    } else if frame_data.filter.compare_accumulated || frame_data.slot.is_dynamic {
        let count = resolve_dynamic_multiplier(state, db, ctx, &frame_data).unwrap_or(0);
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
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    let mut final_v = v;

    let frame_data = frame.components();

    if frame_data.filter.compare_accumulated || frame_data.slot.is_dynamic {
        let count = resolve_dynamic_multiplier(state, db, ctx, &frame_data).unwrap_or(0);
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

pub fn handle_lose_excess_hearts(state: &mut GameState, p_idx: usize, v: i32) -> HandlerResult {
    let player = &mut state.players[p_idx];
    let reduction = if v == 0 {
        player.excess_hearts
    } else {
        v as u32
    };
    player.excess_hearts = player.excess_hearts.saturating_sub(reduction);
    HandlerResult::Continue
}

pub fn handle_skip_activate_phase(state: &mut GameState, p_idx: usize) -> HandlerResult {
    state.players[p_idx].set_skip_next_activate(true);
    HandlerResult::Continue
}
