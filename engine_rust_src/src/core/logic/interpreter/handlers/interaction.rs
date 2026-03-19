//! Interaction opcode handlers split into focused submodules.

#[path = "interaction_play_live.rs"]
mod interaction_play_live;
#[path = "interaction_select_cards.rs"]
mod interaction_select_cards;
#[path = "interaction_look_choose.rs"]
mod interaction_look_choose;
#[path = "interaction_recovery.rs"]
mod interaction_recovery;

pub use interaction_look_choose::handle_look_and_choose;
pub use interaction_play_live::handle_play_live_from_discard;
pub use interaction_recovery::handle_recovery;
pub use interaction_select_cards::handle_select_cards;
