use crate::core::enums::*;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::models::interpreter::resolve_target_slot;

#[path = "state_score_bonus.rs"]
mod state_score_bonus;
#[path = "state_score_requirements.rs"]
mod state_score_requirements;
#[path = "state_score_stats.rs"]
mod state_score_stats;

pub fn handle_score_hearts(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.resolved_filter_attr() as i64;
    let s = frame_data.slot.to_raw();
    let p_idx = ctx.player_id as usize;

    if state.debug.debug_mode && op == O_ADD_HEARTS {
        println!("[DEBUG handle_score_hearts] O_ADD_HEARTS entered");
    }

    let slot_info = frame_data.slot;
    let target_p = if slot_info.is_opponent {
        1 - p_idx
    } else {
        p_idx
    };
    let target_slot = slot_info.target_slot as i32;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_BOOST_SCORE => {
            return state_score_bonus::handle_boost_score(state, db, ctx, frame_data, p_idx, target_p);
        }
        O_REDUCE_COST => {
            return state_score_bonus::handle_reduce_cost(state, db, ctx, frame_data, p_idx, v);
        }
        O_SET_SCORE => {
            return state_score_bonus::handle_set_score(state, db, ctx, target_p, v);
        }
        O_ADD_BLADES | O_BUFF_POWER => {
            return state_score_stats::handle_add_blades(
                state,
                ctx,
                p_idx,
                target_p,
                a,
                v,
                target_slot,
                resolved_slot,
            );
        }
        O_SET_BLADES => {
            return state_score_stats::handle_set_blades(state, p_idx, v, resolved_slot);
        }
        O_ADD_HEARTS => {
            if state.debug.debug_mode {
                println!("[DEBUG] O_ADD_HEARTS: value={}, resolved_slot={}, target_slot={}, source_card_id={}", v, resolved_slot, target_slot, ctx.source_card_id);
            }
            return state_score_stats::handle_add_hearts(
                state,
                db,
                ctx,
                target_p,
                &frame_data,
                resolved_slot,
                target_slot,
            );
        }
        O_SET_HEARTS => {
            return state_score_stats::handle_set_hearts(
                state,
                ctx,
                target_p,
                &frame_data,
                resolved_slot,
                target_slot,
            );
        }
        O_TRANSFORM_COLOR => {
            return state_score_stats::handle_transform_color(state, ctx, p_idx, v, a, s);
        }
        O_TRANSFORM_BLADES => {
            return state_score_stats::handle_transform_blades(
                state,
                p_idx,
                v,
                target_p,
                target_slot,
                resolved_slot,
                frame_data.slot,
            );
        }
        O_REDUCE_HEART_REQ => {
            return state_score_requirements::handle_reduce_heart_req(
                state,
                db,
                ctx,
                p_idx,
                &frame_data,
            );
        }
        O_TRANSFORM_HEART => {
            return state_score_requirements::handle_transform_heart(state, p_idx, a, s, v);
        }
        O_INCREASE_HEART_COST => {
            return state_score_requirements::handle_increase_heart_cost(
                state,
                db,
                ctx,
                p_idx,
                &frame_data,
            );
        }
        O_SET_HEART_COST => {
            return state_score_requirements::handle_set_heart_cost(
                state, ctx, frame_data, p_idx, target_p, s, v,
            );
        }
        O_REDUCE_SCORE => {
            return state_score_bonus::handle_reduce_score(state, target_p, v);
        }
        O_LOSE_EXCESS_HEARTS => {
            return state_score_bonus::handle_lose_excess_hearts(state, p_idx, v);
        }
        O_SKIP_ACTIVATE_PHASE => {
            return state_score_bonus::handle_skip_activate_phase(state, p_idx);
        }
        _ => return HandlerResult::Continue,
    }
}
