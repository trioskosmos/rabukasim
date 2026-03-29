//! Modern Effect System - DISABLED
//!
//! This module previously contained a structured effect representation that was
//! planned to replace the bytecode-based AbilityFrame system. It has been removed
//! to simplify the codebase. The AbilityFrame system is the single source of truth.

use crate::core::logic::models::AbilityFrame;

/// Stub function kept for API compatibility - always returns None
pub fn frame_to_effect(_frame: &AbilityFrame) -> Option<()> {
    None
}

/// Stub type kept for API compatibility
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EffectProgram;

impl EffectProgram {
    pub fn new() -> Self {
        Self
    }
    pub fn is_empty(&self) -> bool {
        true
    }
}
