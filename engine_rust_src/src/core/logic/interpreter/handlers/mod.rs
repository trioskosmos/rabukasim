#![allow(unused_imports, unused_variables)]

use crate::core::logic::models::{AbilityFrame, AbilityFrameComponents};

// --- Modularized Opcode Handlers ---
pub mod flow;
pub mod flow_context;
pub mod flow_effects;
pub mod flow_helpers;
pub mod flow_select;
pub mod flow_state_mod;
pub mod flow_swap;
pub mod interaction;
pub mod interaction_zone;
pub mod movement;
pub mod select_mode;
pub mod choice_prompt;
pub mod state;
pub mod state_helpers;
pub mod state_score_slots;
pub mod unified;

pub use flow::*;
pub use interaction::*;
pub use movement::*;
pub use select_mode::handle_select_mode;
pub use state::*;

use crate::core::enums::*;
use crate::core::logic::interpreter::logging;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

// Helper functions for dispatch
fn p_idx(ctx: &AbilityContext) -> usize {
    ctx.player_id as usize
}

fn base_p(ctx: &AbilityContext) -> usize {
    ctx.activator_id as usize
}

/// Result of an opcode handler execution
#[derive(Debug)]
pub enum HandlerResult {
    /// Continue to next opcode
    Continue,
    /// Set the interpreter's condition flag
    SetCond(bool),
    /// Suspend execution for user choice
    Suspend,
    /// Return from current execution frame
    Return,
    /// Branch to a specific frame index
    Branch(usize),
    /// Branch to a completely new semantic frame sequence (e.g. for TRIGGER_REMOTE)
    BranchToFrames(std::sync::Arc<Vec<AbilityFrame>>),
}

/// Dispatches an opcode to its implementation.
/// Returns a HandlerResult indicating how execution should proceed.
pub fn dispatch(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    frames: &[AbilityFrame],
) -> HandlerResult {
    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;

    // FLAT DISPATCH: Direct opcode-to-handler mapping with explicit parameters
    match op {
            // Meta/Control - Direct handlers (no delegation)
            O_CALC_SUM_COST => unified::handle_calc_sum_cost(state, db, ctx, frame),
            O_NEGATE_EFFECT => unified::handle_negate_effect(state, db, ctx, frame),
            O_SET_TARGET_SELF => unified::handle_set_target_self(state, db, ctx, frame),
            O_SET_TARGET_OPPONENT => unified::handle_set_target_opponent(state, db, ctx, frame),
            O_REPEAT_ABILITY => unified::handle_repeat_ability(state, db, ctx, frame),
            O_FLAVOR_ACTION => unified::handle_flavor_action(state, db, ctx, frame),

            // Draw/Hand - Direct handlers
            O_DRAW | O_DRAW_UNTIL | O_ADD_TO_HAND => unified::handle_draw(state, db, ctx, frame),

            // Energy - Direct unified handlers
            O_ENERGY_CHARGE => unified::handle_energy_charge(state, db, ctx, frame),
            O_PAY_ENERGY => unified::handle_pay_energy(state, db, ctx, frame, frame_idx),
            O_ACTIVATE_ENERGY => unified::handle_activate_energy(state, db, ctx, frame),
            O_PAY_ENERGY_DYNAMIC => unified::handle_pay_energy_dynamic(state, db, ctx, frame),
            O_PLACE_ENERGY_UNDER_MEMBER => unified::handle_place_energy_under_member(state, db, ctx, frame, frame_idx),

            // Member State - Delegated for now
            O_ACTIVATE_MEMBER | O_SET_TAPPED | O_TAP_MEMBER | O_TAP_OPPONENT | O_MOVE_MEMBER | O_FORMATION_CHANGE | O_PLACE_UNDER | O_ADD_STAGE_ENERGY | O_GRANT_ABILITY | O_PLAY_MEMBER_FROM_HAND | O_PLAY_MEMBER_FROM_DISCARD | O_INCREASE_COST => {
                state::handle_member_state(state, db, ctx, frame.clone(), frame_idx)
            }

            // Deck/Zones - Delegated for now
            O_SEARCH_DECK | O_ORDER_DECK | O_MOVE_TO_DECK | O_SWAP_CARDS | O_REVEAL_UNTIL | O_LOOK_DECK | O_REVEAL_CARDS | O_CHEER_REVEAL | O_LOOK_DECK_DYNAMIC | O_MOVE_TO_DISCARD | O_LOOK_AND_CHOOSE | O_RECOVER_LIVE | O_RECOVER_MEMBER | O_PLAY_LIVE_FROM_DISCARD | O_SELECT_CARDS | O_LOOK_REORDER_DISCARD | O_SWAP_ZONE => {
                movement::handle_deck_zones(state, db, ctx, frame, frame_idx)
            }

            // Score/Hearts - Delegated for now
            O_BOOST_SCORE | O_REDUCE_COST | O_SET_SCORE | O_ADD_BLADES | O_BUFF_POWER | O_SET_BLADES | O_ADD_HEARTS | O_SET_HEARTS | O_TRANSFORM_COLOR | O_REDUCE_HEART_REQ | O_TRANSFORM_HEART | O_INCREASE_HEART_COST | O_SET_HEART_COST | O_REDUCE_SCORE | O_TRANSFORM_BLADES | O_SKIP_ACTIVATE_PHASE => {
                state::handle_score_hearts(state, db, ctx, frame)
            }

            // Select Mode, NOP, and remaining flow opcodes
            O_SELECT_MODE => select_mode::handle_select_mode(state, db, ctx, frame, frame_idx, frames),
            O_NOP => choice_prompt::handle_optional_nop(state, db, ctx, frame, frame_idx),

            // Selection operations (from flow.rs)
            O_SELECT_MEMBER | O_SELECT_LIVE | O_SELECT_PLAYER => {
                flow_select::handle_select_ops(state, db, ctx, frame, frame_idx, op, frame_data.value, frame_data.raw_attr as i64, frame_data.raw_slot, p_idx(ctx), frame_data.slot)
            }

            // Opponent choose (from flow.rs)
            O_OPPONENT_CHOOSE => flow_context::handle_opponent_choose(state, db, ctx, frame_idx),

            // Color select (from flow.rs)
            O_COLOR_SELECT => flow_context::handle_color_select(state, db, ctx, frame_idx),

            // Effects (from flow.rs)
            O_TRIGGER_REMOTE => flow_effects::handle_trigger_remote(state, db, ctx, frame, frame_idx, frame_data.value, p_idx(ctx), frame_data.slot),
            O_META_RULE => flow_effects::handle_meta_rule(state, db, ctx, frame, frame_idx, frame_data.raw_attr as i64, frame_data.value, p_idx(ctx), base_p(ctx), frame_data.slot, frame_data.slot.target_slot as i32),

            // Swap area (from flow.rs)
            O_SWAP_AREA => flow_swap::handle_swap_area(state, ctx, base_p(ctx), frame_data.slot, frame_data.slot.target_slot as i32, frame_data.raw_attr as i64, frame_data.raw_slot, frame_data.value),

            // State modifiers (from flow.rs)
            O_LOSE_EXCESS_HEARTS | O_DIV_VALUE | O_RESTRICTION | O_PREVENT_ACTIVATE | O_PREVENT_BATON_TOUCH | O_PREVENT_SET_TO_SUCCESS_PILE | O_PREVENT_PLAY_TO_SLOT | O_REDUCE_LIVE_SET_LIMIT | O_REDUCE_YELL_COUNT | O_BATON_TOUCH_MOD | O_IMMUNITY => {
                flow_state_mod::handle_state_modifiers(state, db, ctx, frame, op, frame_data.value, frame_data.raw_attr as i64, frame_data.raw_slot, p_idx(ctx), base_p(ctx), frame_data.slot, frame_data.slot.target_slot as i32)
            }

            // No more fallbacks - all opcodes handled directly
            _ => {
                if state.debug.debug_mode {
                    eprintln!("[WARN] Unhandled opcode: {} - returning Continue", op);
                }
                HandlerResult::Continue
            }
        }
}
