use crate::core::logic::models::AbilityFrame;

/// State opcode handlers, split into focused submodules.

#[path = "state_energy.rs"]
mod state_energy;

#[path = "state_member.rs"]
mod state_member;

#[path = "state_score_hearts.rs"]
mod state_score_hearts;

pub use state_energy::handle_energy;

pub use state_member::finalize_play_member_from_discard;
pub use state_member::finalize_play_member_from_hand;
pub use state_member::handle_discard_placement;
pub use state_member::handle_member_state;

pub use state_score_hearts::handle_score_hearts;
