use super::*;
use crate::core::logic::models::AbilityFrame;

#[path = "state_member_tap_member_logic.rs"]
mod state_member_tap_member_logic;

pub use state_member_tap_member_logic::handle_tap_member;
