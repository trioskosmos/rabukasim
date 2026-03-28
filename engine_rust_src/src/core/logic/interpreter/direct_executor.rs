//! Direct Effect Executor - Simplified interpreter without VM dispatch
//! 
//! This module provides direct execution of AbilityFrame variants without
//! the HandlerRegistry indirection, replacing the VM loop with simple
//! sequential execution.

use crate::core::logic::interpreter::handlers::{HandlerRegistry, HandlerResult};
use crate::core::logic::models::AbilityFrame;
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
    frame_idx: usize,
    frames: &[AbilityFrame],
) -> EffectResult {
    let frame_data = frame.components();
    let handler_result = HandlerRegistry::new().dispatch(state, db, ctx, frame, &frame_data, frame_idx, frames);
    
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
