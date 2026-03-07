// --- Modularized Opcode Handlers ---
pub mod movement;
pub mod interaction;
pub mod state;
pub mod flow;

pub use movement::*;
pub use interaction::*;
pub use state::*;
pub use flow::*;

use crate::core::enums::*;
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
    /// Branch to a specific program counter
    Branch(usize),
    /// Branch to a completely new piece of bytecode (e.g. for TRIGGER_REMOTE)
    BranchToBytecode(std::sync::Arc<Vec<i32>>),
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
        instr: &super::instruction::BytecodeInstruction,
        instr_ip: usize,
        bytecode: &[i32],
    ) -> HandlerResult {
        let op = instr.op;
        let v = instr.v;
        let a = instr.a;
        let s = instr.raw_s;
        println!("[DEBUG] DISPATCH: op={} v={} a={} s={}", op, v, a, s);
        // Centralized Dispatch Match
        match op {
            O_SELECT_MODE => handle_select_mode(state, db, ctx, instr, instr_ip, bytecode),
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
            | O_DIV_VALUE => flow::handle_meta_control(state, db, ctx, instr, instr_ip),
            // 2. Draw / Hand
            O_DRAW | O_DRAW_UNTIL | O_ADD_TO_HAND => {
                movement::handle_draw(state, db, ctx, instr)
            }
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
            | O_INCREASE_COST => state::handle_member_state(state, db, ctx, instr, instr_ip),
            // 4. Energy
            O_ENERGY_CHARGE
            | O_PAY_ENERGY
            | O_ACTIVATE_ENERGY
            | O_PAY_ENERGY_DYNAMIC
            | O_PLACE_ENERGY_UNDER_MEMBER => state::handle_energy(state, db, ctx, instr, instr_ip),
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
            | O_SWAP_ZONE => movement::handle_deck_zones(state, db, ctx, instr, instr_ip),
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
            | O_TRANSFORM_HEART
            | O_SKIP_ACTIVATE_PHASE => state::handle_score_hearts(state, db, ctx, instr),
            _ => {
                if state.debug.debug_mode {
                    println!(
                        "[WARN] Unhandled opcode: {} (v={}, a={}, s={}) at IP {}",
                        op, v, a, s, instr_ip
                    );
                }
                HandlerResult::Continue
            }
        }
    }
}

pub fn handle_select_mode(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::instruction::BytecodeInstruction,
    instr_ip: usize,
    bc: &[i32],
) -> HandlerResult {
    use super::suspension::{get_choice_text, suspend_interaction};
    let v = instr.v;
    if ctx.choice_index == -1 {
        let is_opponent = instr.s.is_opponent || instr.s.target_slot == 2;
        let choice_type = if is_opponent {
            crate::core::enums::ChoiceType::OpponentChoose
        } else {
            crate::core::enums::ChoiceType::SelectMode
        };
        let choice_text = get_choice_text(db, ctx);

        let mut flip_ctx = ctx.clone();
        if is_opponent {
            flip_ctx.player_id = 1 - (ctx.player_id as u8);
        }

        let suspended = suspend_interaction(
            state,
            db,
            if is_opponent { &flip_ctx } else { ctx },
            instr_ip,
            crate::core::enums::O_SELECT_MODE,
            0,
            choice_type,
            &choice_text,
            0,
            v as i16,
        );

        if suspended {
            return HandlerResult::Suspend;
        }
        return HandlerResult::Branch(instr_ip + 5);
    }

    let choice = ctx.choice_index as usize;
    if choice >= v as usize {
        return HandlerResult::Branch(instr_ip + 5 + ((v as usize).saturating_sub(1)) * 5);
    }

    let jump_instr_offset = instr_ip + 5 + (choice * 5);
    let target = jump_instr_offset as i32 + 5 + (bc[jump_instr_offset + 1] * 5);

    HandlerResult::Branch(target as usize)
}
