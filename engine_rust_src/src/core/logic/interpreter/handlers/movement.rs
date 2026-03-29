use crate::core::logic::models::AbilityFrame;

/// Movement opcode handlers.

#[path = "movement_draw.rs"]
mod movement_draw;

#[path = "movement_discard.rs"]
mod movement_discard;

#[path = "movement_deck.rs"]
mod movement_deck;

#[path = "movement_swap_zone.rs"]
mod movement_swap_zone;

pub use movement_deck::{
    handle_deck_zones,
    handle_order_deck,
    handle_look_reorder_discard,
};

pub use movement_discard::handle_move_to_discard;

pub use movement_draw::handle_draw;

pub use movement_swap_zone::handle_swap_zone;
