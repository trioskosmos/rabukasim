#![allow(unused_imports, unused_variables)]

use crate::core::logic::models::{AbilityFrame, AbilityFrameComponents};

// --- Modularized Opcode Handlers ---

pub mod flow;

pub mod flow_helpers;

pub mod interaction;

pub mod interaction_zone;

pub mod movement;

pub mod select_mode;

pub mod choice_prompt;

pub mod state;

pub mod state_helpers;

pub mod state_score_slots;

pub use flow::*;

pub use interaction::*;

pub use movement::*;

pub use state::*;

use crate::core::enums::*;

use crate::core::logic::interpreter::logging;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

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

/// A registry that dispatches opcodes to their respective handlers.

pub struct HandlerRegistry;

impl HandlerRegistry {
    pub fn new() -> Self {
        Self
    }

    /// Dispatches an opcode to its implementation.

    /// Returns a HandlerResult indicating how execution should proceed.

    pub fn dispatch(
        &self,

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

        if state.debug.debug_mode && !state.ui.silent {
            let sem = crate::core::logic::interpreter::logging::describe_frame_words(op, v, a, s as i32);
            println!(
                "[DISPATCH] {} | player={} choice={} phase={:?}",
                sem, ctx.player_id, ctx.choice_index, state.phase
            );
        }

        // Centralized Dispatch Match

        match op {
            O_NOP => choice_prompt::handle_optional_nop(state, db, ctx, frame, frame_idx),
            O_SELECT_MODE => {
                select_mode::handle_select_mode(state, db, ctx, frame, frame_idx, frames)
            }

            // 1. Meta / Control Handlers
            O_NEGATE_EFFECT
            | O_REDUCE_YELL_COUNT
            | O_RESTRICTION
            | O_SELECT_MEMBER
            | O_SELECT_LIVE
            | O_SELECT_PLAYER
            | O_OPPONENT_CHOOSE
            | O_PREVENT_ACTIVATE
            | O_PREVENT_BATON_TOUCH
            | O_PREVENT_SET_TO_SUCCESS_PILE
            | O_PREVENT_PLAY_TO_SLOT
            | O_TRIGGER_REMOTE
            | O_REDUCE_LIVE_SET_LIMIT
            | O_META_RULE
            | O_BATON_TOUCH_MOD
            | O_IMMUNITY
            | O_COLOR_SELECT
            | O_SWAP_AREA
            | O_REPEAT_ABILITY
            | O_SET_TARGET_SELF
            | O_SET_TARGET_OPPONENT
            | O_CALC_SUM_COST
            | O_DIV_VALUE => flow::handle_meta_control(state, db, ctx, frame, frame_idx),

            // 2. Draw / Hand
            O_DRAW | O_DRAW_UNTIL | O_ADD_TO_HAND => movement::handle_draw(state, db, ctx, frame),

            // 3. Member State
            O_ACTIVATE_MEMBER
            | O_SET_TAPPED
            | O_TAP_MEMBER
            | O_TAP_OPPONENT
            | O_MOVE_MEMBER
            | O_FORMATION_CHANGE
            | O_PLACE_UNDER
            | O_ADD_STAGE_ENERGY
            | O_GRANT_ABILITY
            | O_PLAY_MEMBER_FROM_HAND
            | O_PLAY_MEMBER_FROM_DISCARD
            | O_INCREASE_COST => state::handle_member_state(state, db, ctx, frame, frame_idx),

            // 4. Energy
            O_ENERGY_CHARGE
            | O_PAY_ENERGY
            | O_ACTIVATE_ENERGY
            | O_PAY_ENERGY_DYNAMIC
            | O_PLACE_ENERGY_UNDER_MEMBER => state::handle_energy(state, db, ctx, frame, frame_idx),

            // 5. Deck / Zones
            O_SEARCH_DECK
            | O_ORDER_DECK
            | O_MOVE_TO_DECK
            | O_SWAP_CARDS
            | O_REVEAL_UNTIL
            | O_LOOK_DECK
            | O_REVEAL_CARDS
            | O_CHEER_REVEAL
            | O_LOOK_DECK_DYNAMIC
            | O_MOVE_TO_DISCARD
            | O_LOOK_AND_CHOOSE
            | O_RECOVER_LIVE
            | O_RECOVER_MEMBER
            | O_PLAY_LIVE_FROM_DISCARD
            | O_SELECT_CARDS
            | O_LOOK_REORDER_DISCARD
            | O_SWAP_ZONE => movement::handle_deck_zones(state, db, ctx, frame, frame_idx),

            // 6. Score / Hearts
            O_BOOST_SCORE
            | O_REDUCE_COST
            | O_SET_SCORE
            | O_ADD_BLADES
            | O_BUFF_POWER
            | O_SET_BLADES
            | O_ADD_HEARTS
            | O_SET_HEARTS
            | O_TRANSFORM_COLOR
            | O_REDUCE_HEART_REQ
            | O_TRANSFORM_HEART
            | O_INCREASE_HEART_COST
            | O_SET_HEART_COST
            | O_REDUCE_SCORE
            | O_LOSE_EXCESS_HEARTS
            | O_TRANSFORM_BLADES
            | O_SKIP_ACTIVATE_PHASE => state::handle_score_hearts(state, db, ctx, frame),

            _ => {
                if state.debug.debug_mode {
                    println!(
                        "[WARN] Unhandled opcode: {} at IP {} | {}",
                        logging::get_opcode_name(op),
                        frame_idx,
                        logging::describe_words(op, v, a, s)
                    );
                }

                HandlerResult::Continue
            }
        }
    }
}
