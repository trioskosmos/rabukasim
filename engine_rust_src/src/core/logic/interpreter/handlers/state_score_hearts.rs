use crate::core::logic::interpreter::handlers::state_helpers::{
    inline_value_ge_threshold, tap_opponent_chooser_player, update_live_score_snapshot,
};
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::logging;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::models::interpreter::{get_choice_text, resolve_target_slot};
use crate::core::models::suspend_interaction;

#[path = "state_score_bonus.rs"]
mod state_score_bonus;
#[path = "state_score_stats.rs"]
mod state_score_stats;
#[path = "state_score_requirements.rs"]
mod state_score_requirements;
pub fn handle_score_hearts(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
) -> HandlerResult {
    let op = instr.op;
    let v = instr.v;
    let a = instr.a;
    #[allow(unused_variables)]
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;

    let slot_info = instr.slot();
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
            return state_score_bonus::handle_boost_score(state, db, ctx, instr, p_idx, target_p);
        }
        O_REDUCE_COST => {
            return state_score_bonus::handle_reduce_cost(state, ctx, instr, p_idx, v);
        }
        O_SET_SCORE => {
            return state_score_bonus::handle_set_score(state, db, ctx, target_p, v);
        }
        O_ADD_BLADES | O_BUFF_POWER => {
            return state_score_stats::handle_add_blades(
                state, ctx, p_idx, target_p, a, v, target_slot, resolved_slot,
            );
        }
        O_SET_BLADES => {
            return state_score_stats::handle_set_blades(state, p_idx, v, resolved_slot);
        }
        O_ADD_HEARTS => {
            return state_score_stats::handle_add_hearts(
                state, ctx, p_idx, a, v, s, resolved_slot, target_slot,
            );
        }
        O_SET_HEARTS => {
            return state_score_stats::handle_set_hearts(
                state, p_idx, a, v, resolved_slot, target_slot,
            );
        }
        O_TRANSFORM_COLOR => {
            return state_score_stats::handle_transform_color(state, ctx, p_idx, v, a, s);
        }
        O_TRANSFORM_BLADES => {
            return state_score_stats::handle_transform_blades(
                state, p_idx, v, target_p, target_slot, resolved_slot, instr.slot(),
            );
        }
        O_REDUCE_HEART_REQ => {
            return state_score_requirements::handle_reduce_heart_req(
                state, ctx, p_idx, s, v,
            );
        }
        O_TRANSFORM_HEART => {
            return state_score_requirements::handle_transform_heart(
                state, p_idx, a, s, v,
            );
        }
        O_INCREASE_HEART_COST => {
            return state_score_requirements::handle_increase_heart_cost(
                state, ctx, p_idx, s, v,
            );
        }
        O_SET_HEART_COST => {
            return state_score_requirements::handle_set_heart_cost(
                state, ctx, instr, p_idx, target_p, s, v,
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

