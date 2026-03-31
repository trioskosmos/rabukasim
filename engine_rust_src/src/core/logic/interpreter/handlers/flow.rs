use super::{
    flow_context, flow_effects, flow_select, flow_state_mod, flow_swap, HandlerResult,
};
use crate::core::logic::models::AbilityFrameComponents;

use crate::core::enums::*;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

pub fn handle_meta_control(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let base_p = ctx.activator_id as usize;
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let target_slot = slot_info.target_slot as i32;

    match op {
        // State modification operations - delegate to specialized handler
        O_LOSE_EXCESS_HEARTS
        | O_DIV_VALUE
        | O_RESTRICTION
        | O_PREVENT_ACTIVATE
        | O_PREVENT_BATON_TOUCH
        | O_PREVENT_SET_TO_SUCCESS_PILE
        | O_PREVENT_PLAY_TO_SLOT
        | O_REDUCE_LIVE_SET_LIMIT
        | O_REDUCE_YELL_COUNT
        | O_BATON_TOUCH_MOD
        | O_IMMUNITY => {
            return flow_state_mod::handle_state_modifiers(
                state, db, ctx, frame_data, op, v, a, s, p_idx, base_p, slot_info, target_slot,
            );
        }

        // Selection operations - delegate to specialized handler
        O_SELECT_MEMBER | O_SELECT_LIVE | O_SELECT_PLAYER => {
            return flow_select::handle_select_ops(
                state, db, ctx, frame_data, frame_idx, op, v, a, s, p_idx, slot_info,
            );
        }
        O_OPPONENT_CHOOSE => {
            return flow_context::handle_opponent_choose(state, db, ctx, frame_idx);
        }
        O_TRIGGER_REMOTE => {
            return flow_effects::handle_trigger_remote(
                state, db, ctx, frame_data, frame_idx, v, p_idx, slot_info,
            );
        }
        O_META_RULE => {
            return flow_effects::handle_meta_rule(
                state,
                db,
                ctx,
                frame_data,
                frame_idx,
                a,
                v,
                p_idx,
                base_p,
                slot_info,
                target_slot,
            );
        }
        O_COLOR_SELECT => {
            return flow_context::handle_color_select(state, db, ctx, frame_idx);
        }
        O_SWAP_AREA => {
            return flow_swap::handle_swap_area(
                state,
                ctx,
                frame_data,
                base_p,
                slot_info,
                target_slot,
                a,
                s,
                v,
            );
        }
        // O_CALC_SUM_COST, O_NEGATE_EFFECT, O_REPEAT_ABILITY, O_SET_TARGET_SELF,
        // O_SET_TARGET_OPPONENT, O_FLAVOR_ACTION now handled by unified.rs
        _ => return HandlerResult::Continue,
    }
}
