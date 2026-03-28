//! Direct Effect Executor - Simplified interpreter without VM dispatch
//! 
//! This module provides direct execution of AbilityFrame variants without
//! the HandlerRegistry indirection, replacing the VM loop with simple
//! sequential execution.

use crate::core::logic::models::AbilityFrame;
use crate::core::logic::interpreter::handlers::{HandlerResult};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

/// Result of executing a single effect
#[derive(Debug, Clone, PartialEq)]
pub enum EffectResult {
    /// Continue to next effect
    Continue,
    /// Suspend for user interaction
    Suspend,
    /// Return from ability early
    Return,
    /// Branch to a specific frame index
    Branch(usize),
    /// Set condition flag
    SetCond(bool),
    /// Branch to new frames
    BranchToFrames(std::sync::Arc<Vec<AbilityFrame>>),
}

/// Execute a single AbilityFrame directly by delegating to existing handlers
/// This is the first step in the migration - wraps existing handlers with
/// a simpler interface
pub fn execute_frame_direct(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    _frame_idx: usize,
    _frames: &[AbilityFrame],
) -> EffectResult {
    use crate::core::logic::interpreter::handlers::*;
    
    // Extract frame data for dispatch
    let frame_data = frame.components();
    let op = frame_data.opcode;
    
    // Create semantic frame for handlers that need it
    let semantic_frame = || -> AbilityFrame {
        AbilityFrame::Semantic {
            opcode: frame_data.opcode,
            value: frame_data.value,
            filter: frame_data.filter,
            slot: frame_data.slot,
            is_negated: frame_data.is_negated,
            is_cost: frame_data.is_cost,
            params: frame_data.params.cloned().unwrap_or_default(),
        }
    };
    
    // Direct dispatch without registry indirection
    let handler_result = match op {
        // Simple returns
        crate::core::enums::O_RETURN => return EffectResult::Return,
        crate::core::enums::O_NOP => return EffectResult::Continue,
        
        // Draw / Hand operations
        crate::core::enums::O_DRAW |
        crate::core::enums::O_DRAW_UNTIL |
        crate::core::enums::O_ADD_TO_HAND => {
            movement::handle_draw(state, db, ctx, &semantic_frame())
        }
        
        // Energy operations
        crate::core::enums::O_ENERGY_CHARGE |
        crate::core::enums::O_PAY_ENERGY |
        crate::core::enums::O_ACTIVATE_ENERGY |
        crate::core::enums::O_PAY_ENERGY_DYNAMIC |
        crate::core::enums::O_PLACE_ENERGY_UNDER_MEMBER => {
            state::handle_energy(state, db, ctx, &semantic_frame(), _frame_idx)
        }
        
        // Score / Hearts operations
        crate::core::enums::O_BOOST_SCORE |
        crate::core::enums::O_REDUCE_COST |
        crate::core::enums::O_SET_SCORE |
        crate::core::enums::O_ADD_BLADES |
        crate::core::enums::O_BUFF_POWER |
        crate::core::enums::O_SET_BLADES |
        crate::core::enums::O_ADD_HEARTS |
        crate::core::enums::O_SET_HEARTS |
        crate::core::enums::O_TRANSFORM_COLOR |
        crate::core::enums::O_REDUCE_HEART_REQ |
        crate::core::enums::O_TRANSFORM_HEART |
        crate::core::enums::O_INCREASE_HEART_COST |
        crate::core::enums::O_SET_HEART_COST |
        crate::core::enums::O_REDUCE_SCORE |
        crate::core::enums::O_LOSE_EXCESS_HEARTS |
        crate::core::enums::O_TRANSFORM_BLADES |
        crate::core::enums::O_SKIP_ACTIVATE_PHASE => {
            state::handle_score_hearts(state, db, ctx, &semantic_frame())
        }
        
        // Member state operations
        crate::core::enums::O_ACTIVATE_MEMBER |
        crate::core::enums::O_SET_TAPPED |
        crate::core::enums::O_TAP_MEMBER |
        crate::core::enums::O_TAP_OPPONENT |
        crate::core::enums::O_MOVE_MEMBER |
        crate::core::enums::O_FORMATION_CHANGE |
        crate::core::enums::O_PLACE_UNDER |
        crate::core::enums::O_ADD_STAGE_ENERGY |
        crate::core::enums::O_GRANT_ABILITY |
        crate::core::enums::O_PLAY_MEMBER_FROM_HAND |
        crate::core::enums::O_PLAY_MEMBER_FROM_DISCARD |
        crate::core::enums::O_INCREASE_COST => {
            state::handle_member_state(state, db, ctx, &semantic_frame(), _frame_idx)
        }
        
        // Deck / Zone operations
        crate::core::enums::O_SEARCH_DECK |
        crate::core::enums::O_ORDER_DECK |
        crate::core::enums::O_MOVE_TO_DECK |
        crate::core::enums::O_SWAP_CARDS |
        crate::core::enums::O_REVEAL_UNTIL |
        crate::core::enums::O_LOOK_DECK |
        crate::core::enums::O_REVEAL_CARDS |
        crate::core::enums::O_CHEER_REVEAL |
        crate::core::enums::O_LOOK_DECK_DYNAMIC |
        crate::core::enums::O_MOVE_TO_DISCARD |
        crate::core::enums::O_RECOVER_LIVE |
        crate::core::enums::O_RECOVER_MEMBER |
        crate::core::enums::O_PLAY_LIVE_FROM_DISCARD |
        crate::core::enums::O_SELECT_CARDS |
        crate::core::enums::O_LOOK_REORDER_DISCARD |
        crate::core::enums::O_SWAP_ZONE => {
            movement::handle_deck_zones(state, db, ctx, &semantic_frame(), _frame_idx)
        }
        
        // LOOK_AND_CHOOSE needs the original frame to preserve look_choose() data
        crate::core::enums::O_LOOK_AND_CHOOSE => {
            movement::handle_deck_zones(state, db, ctx, frame, _frame_idx)
        }
        
        // Select mode - needs frames slice
        crate::core::enums::O_SELECT_MODE => {
            select_mode::handle_select_mode(state, db, ctx, &semantic_frame(), _frame_idx, _frames)
        }
        
        // Meta control operations - use flow handler
        _ => {
            flow::handle_meta_control(state, db, ctx, &semantic_frame(), _frame_idx)
        }
    };
    
    // Convert HandlerResult to EffectResult
    match handler_result {
        HandlerResult::Continue => EffectResult::Continue,
        HandlerResult::Suspend => EffectResult::Suspend,
        HandlerResult::Return => EffectResult::Return,
        HandlerResult::Branch(idx) => EffectResult::Branch(idx),
        HandlerResult::SetCond(cond) => EffectResult::SetCond(cond),
        HandlerResult::BranchToFrames(frames) => EffectResult::BranchToFrames(frames),
    }
}
