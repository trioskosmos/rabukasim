//! Legacy compatibility exports for code that still imports `crate::core::types`.

pub use crate::core::logic::constants::STAGE_SLOT_COUNT;

/// Main-phase action generation only exposes the first seven hand slots.
pub const MAX_HAND_SIZE: usize = 7;

/// Live selection prompts address the three success-live slots.
pub const MAX_LIVE_SET_SIZE: usize = 3;