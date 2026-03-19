//! Movement opcode handlers split into focused submodules.

#[path = "movement_draw.rs"]
mod movement_draw;
#[path = "movement_discard.rs"]
mod movement_discard;
#[path = "movement_discard_helpers.rs"]
mod movement_discard_helpers;
#[path = "movement_deck_zones.rs"]
mod movement_deck_zones;
#[path = "movement_swap_zone.rs"]
mod movement_swap_zone;

pub use movement_deck_zones::handle_deck_zones;
pub use movement_discard::handle_move_to_discard;
pub use movement_draw::handle_draw;
pub use movement_swap_zone::handle_swap_zone;
