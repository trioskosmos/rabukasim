use crate::core::logic::{GameState, CardDatabase, AbilityContext};
use crate::core::enums::*;

pub mod draw_hand;
pub mod member_state;
pub mod deck_zones;
pub mod score_hearts;
pub mod energy;
pub mod meta_control;

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
        op: i32,
        v: i32,
        a: i64,
        s: i32,
        instr_ip: usize,
        bytecode: &[i32]
    ) -> HandlerResult {
        // Centralized Dispatch Match
        match op {
            O_SELECT_MODE => {
                match handle_select_mode(state, db, ctx, v, a, s, instr_ip, bytecode) {
                    Some(new_ip) => HandlerResult::Branch(new_ip),
                    None => HandlerResult::Suspend,
                }
            },
            // 1. Meta / Control Handlers
            O_NEGATE_EFFECT | O_REDUCE_YELL_COUNT | O_RESTRICTION | O_SELECT_MEMBER | O_SELECT_LIVE |
            O_SELECT_PLAYER | O_OPPONENT_CHOOSE | O_PREVENT_ACTIVATE | O_PREVENT_BATON_TOUCH |
            O_PREVENT_SET_TO_SUCCESS_PILE | O_PREVENT_PLAY_TO_SLOT | O_TRIGGER_REMOTE |
            O_REDUCE_LIVE_SET_LIMIT | O_META_RULE | O_BATON_TOUCH_MOD | O_IMMUNITY | O_COLOR_SELECT |
            O_SWAP_AREA | O_REPEAT_ABILITY | O_SET_TARGET_SELF | O_SET_TARGET_OPPONENT => {
                meta_control::handle_meta_control(state, db, ctx, op, v, a, s, instr_ip).unwrap_or(HandlerResult::Continue)
            },
            // 2. Draw / Hand
            O_DRAW | O_DRAW_UNTIL | O_ADD_TO_HAND => {
                draw_hand::handle_draw(state, db, ctx, op, v, a, s).unwrap_or(HandlerResult::Continue)
            },
            // 3. Member State
            O_ACTIVATE_MEMBER | O_SET_TAPPED | O_TAP_MEMBER | O_TAP_OPPONENT | O_MOVE_MEMBER |
            O_FORMATION_CHANGE | O_PLACE_UNDER | O_ADD_STAGE_ENERGY | O_GRANT_ABILITY |
            O_PLAY_MEMBER_FROM_HAND | O_PLAY_MEMBER_FROM_DISCARD | O_INCREASE_COST => {
                member_state::handle_member_state(state, db, ctx, op, v, a, s, instr_ip).unwrap_or(HandlerResult::Continue)
            },
            // 4. Energy
            O_ENERGY_CHARGE | O_PAY_ENERGY | O_ACTIVATE_ENERGY | O_PAY_ENERGY_DYNAMIC |
            O_PLACE_ENERGY_UNDER_MEMBER => {
                energy::handle_energy(state, db, ctx, op, v, a, s, instr_ip).unwrap_or(HandlerResult::Continue)
            },
            // 5. Deck / Zones
            O_SEARCH_DECK | O_ORDER_DECK | O_MOVE_TO_DECK | O_SWAP_CARDS | O_REVEAL_UNTIL |
            O_LOOK_DECK | O_REVEAL_CARDS | O_CHEER_REVEAL | O_LOOK_DECK_DYNAMIC | O_MOVE_TO_DISCARD |
            O_LOOK_AND_CHOOSE | O_RECOVER_LIVE | O_RECOVER_MEMBER | O_PLAY_LIVE_FROM_DISCARD |
            O_SELECT_CARDS | O_SWAP_ZONE => {
                deck_zones::handle_deck_zones(state, db, ctx, op, v, a, s, instr_ip).unwrap_or(HandlerResult::Continue)
            },
            // 6. Score / Hearts
            O_BOOST_SCORE | O_REDUCE_COST | O_SET_SCORE | O_ADD_BLADES | O_BUFF_POWER |
            O_SET_BLADES | O_ADD_HEARTS | O_SET_HEARTS | O_TRANSFORM_COLOR | O_REDUCE_HEART_REQ |
            O_TRANSFORM_HEART | O_INCREASE_HEART_COST | O_SET_HEART_COST | O_REDUCE_SCORE |
            O_LOSE_EXCESS_HEARTS | O_SKIP_ACTIVATE_PHASE => {
                score_hearts::handle_score_hearts(state, db, ctx, op, v, a, s).unwrap_or(HandlerResult::Continue)
            },
            _ => {
                if state.debug.debug_mode {
                    println!("[WARN] Unhandled opcode: {} (v={}, a={}, s={}) at IP {}", op, v, a, s, instr_ip);
                }
                HandlerResult::Continue
            }
        }
    }
}

fn handle_select_mode(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    v: i32,
    _a: i64,
    _s: i32,
    instr_ip: usize,
    bc: &[i32]
) -> Option<usize> {
    use super::suspension::{suspend_interaction, get_choice_text};
    if ctx.choice_index == -1 {
        let is_opponent = (_s & (1 << 24)) != 0 || (_s & 0xFF) == 2;
        let choice_type = if is_opponent { "OPPONENT_CHOOSE" } else { "SELECT_MODE" };
        let choice_text = get_choice_text(db, ctx);

        let mut flip_ctx = ctx.clone();
        if is_opponent {
            flip_ctx.player_id = 1 - (ctx.player_id as u8);
        }

        let old_cp = state.current_player;
        if is_opponent { state.current_player = 1 - ctx.player_id; }

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
            v as i16
        );

        if is_opponent { state.current_player = old_cp; }

        if suspended { return None; }
        return Some(instr_ip + 5);
    }

    let choice = ctx.choice_index as usize;
    if choice >= v as usize {
        return Some(instr_ip + 5 + ((v as usize).saturating_sub(1)) * 5);
    }

    let jump_instr_offset = instr_ip + 5 + (choice * 5);
    let target = jump_instr_offset as i32 + 5 + (bc[jump_instr_offset + 1] * 5);

    Some(target as usize)
}
