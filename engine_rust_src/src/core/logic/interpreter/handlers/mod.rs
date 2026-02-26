use crate::core::logic::{GameState, CardDatabase, AbilityContext};
use crate::core::enums::*;

pub mod draw_hand;
pub mod member_state;
pub mod deck_zones;
pub mod score_hearts;
pub mod energy;
pub mod meta_control;

/// Result of an opcode handler execution
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
    BranchToBytecode(Vec<i32>),
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
        // 1. Meta / Control Handlers (includes Branching/Selection)
        if op == O_SELECT_MODE {
            match handle_select_mode(state, db, ctx, v, a, s, instr_ip, bytecode) {
                Some(new_ip) => return HandlerResult::Branch(new_ip),
                None => return HandlerResult::Suspend,
            }
        }

        if let Some(res) = meta_control::handle_meta_control(state, db, ctx, op, v, a, s, instr_ip) { return res; }
        if let Some(res) = draw_hand::handle_draw(state, db, ctx, op, v, a, s) { return res; }
        if let Some(res) = member_state::handle_member_state(state, db, ctx, op, v, a, s, instr_ip) { return res; }
        if let Some(res) = energy::handle_energy(state, db, ctx, op, v, a, s, instr_ip) { return res; }
        if let Some(res) = deck_zones::handle_deck_zones(state, db, ctx, op, v, a, s, instr_ip) { return res; }
        if let Some(res) = score_hearts::handle_score_hearts(state, db, ctx, op, v, a, s) { return res; }

        if state.debug.debug_mode {
            println!("[WARN] Unhandled opcode: {} (v={}, a={}, s={}) at IP {}", op, v, a, s, instr_ip);
        }

        HandlerResult::Continue
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
