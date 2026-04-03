use super::*;
use crate::core::enums::Zone;
use crate::core::logic::constants::{
    C_COUNT_DISCARD, C_COUNT_HAND, C_COUNT_STAGE, C_COUNT_SUCCESS_LIVE,
};
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::handlers::state_helpers::{
    inline_value_ge_threshold, update_live_score_snapshot,
};

fn resolve_dynamic_multiplier(
    state: &GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_data: &crate::core::logic::models::AbilityFrameComponents<'_>,
) -> Option<i32> {
    // Determine which counting opcode to use based on source_zone or per_card config
    let count_opcode = match frame_data.slot.source_zone {
        Zone::Hand => C_COUNT_HAND,
        Zone::Discard => C_COUNT_DISCARD,
        Zone::Stage => C_COUNT_STAGE,
        Zone::SuccessPile => C_COUNT_SUCCESS_LIVE,
        Zone::Default => {
            // Legacy/default-slot reduce-cost frames often encode dynamic hand counting
            // in structured slot/filter bits instead of JSON params.
            let has_dynamic_config = frame_data.opcode == O_REDUCE_COST
                && (frame_data.slot.is_dynamic
                    || frame_data.filter.compare_accumulated
                    || frame_data.filter.special_id == 3
                    || frame_data.slot.remainder_zone >= 200
                    || frame_data.params.as_ref().map_or(false, |p| !p.is_null()));
            if has_dynamic_config {
                C_COUNT_HAND
            } else {
                return None; // No dynamic config, use static value
            }
        }
        _ => return None, // Other zones don't support dynamic counting
    };

    let filter_attr = frame_data.filter.to_attr();
    let mut count = resolve_count(
        state,
        db,
        count_opcode,
        frame_data.raw_attr,
        frame_data.raw_slot,
        ctx,
        0,
    );

    // Exclude source card from count when it's part of the counted zone
    if frame_data.opcode == O_REDUCE_COST && count > 0 {
        let p_idx = ctx.player_id as usize;
        let source_card_id = ctx.source_card_id;
        let source_is_counted = match frame_data.slot.source_zone {
            Zone::Hand | Zone::Default => state.players[p_idx]
                .hand
                .iter()
                .any(|&id| id == source_card_id),
            Zone::Discard => state.players[p_idx]
                .discard
                .iter()
                .any(|&id| id == source_card_id),
            Zone::Stage => state.players[p_idx]
                .stage
                .iter()
                .any(|&id| id == source_card_id),
            Zone::SuccessPile => state.players[p_idx]
                .success_lives
                .iter()
                .any(|&id| id == source_card_id),
            _ => false,
        };
        let source_matches_filter = filter_attr == 0
            || state.card_matches_filter_with_ctx(db, source_card_id, filter_attr, ctx);
        if source_is_counted && source_matches_filter {
            count -= 1;
        }
    }

    Some(count)
}

/// Checks if activation requirements are met for keyword-based boosts
fn check_activation_keyword(params: &serde_json::Value, state: &GameState, p_idx: usize) -> bool {
    let keyword = match params.get("keyword").and_then(|v| v.as_str()) {
        Some(k) => k,
        None => return true, // No keyword condition, allow through
    };
    
    let group_id = params.get("group_id").and_then(|v| v.as_u64()).map(|v| v as u32);
    
    match keyword {
        "activated_energy" | "DID_ACTIVATE_ENERGY" => {
            let mask = state.players[p_idx].activated_energy_group_mask;
            match group_id {
                Some(gid) => (mask & (1 << gid)) != 0,
                None => mask != 0,
            }
        }
        "activated_member" | "DID_ACTIVATE_MEMBER" => {
            let mask = state.players[p_idx].activated_member_group_mask;
            match group_id {
                Some(gid) => (mask & (1 << gid)) != 0,
                None => mask != 0,
            }
        }
        _ => true, // Unknown keyword, allow through
    }
}

pub fn handle_boost_score(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    p_idx: usize,
    target_p: usize,
) -> HandlerResult {
    // Check minimum required accumulated value
    if ctx.v_accumulated >= 0 {
        if let Some(min_required) = inline_value_ge_threshold(db, ctx) {
            if (ctx.v_accumulated as i32) < min_required {
                return HandlerResult::Continue;
            }
        }
    }

    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;

    // Q203 Fix: Check activated keyword conditions
    if let Some(params) = frame_data.params {
        if !check_activation_keyword(params, state, p_idx) {
            return HandlerResult::Continue;
        }
    }

    let mut final_v = v;
    if frame_data.is_dynamic() {
        let divisor = frame_data.scalar_dynamic_divisor().max(1);
        let base = frame_data.scalar_dynamic_base();
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
    frame_data: &AbilityFrameComponents<'_>,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    // Try dynamic multiplier first - if resolve_dynamic_multiplier returns Some(count),
    // use v * count. Otherwise fall back to static value v.
    let final_v = resolve_dynamic_multiplier(state, db, ctx, frame_data)
        .map(|count| v * count)
        .unwrap_or(v);
    
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
