use super::*;
use crate::core::logic::models::AbilityFrameComponents;

#[path = "state_member_play_discard.rs"]
mod state_member_play_discard;
#[path = "state_member_play_hand.rs"]
mod state_member_play_hand;
#[path = "state_member_play_resolve.rs"]
mod state_member_play_resolve;

pub use state_member_play_resolve::finalize_play_member_from_hand;
pub use state_member_play_resolve::finalize_play_member_from_discard;
pub use state_member_play_discard::handle_discard_placement;

#[allow(clippy::too_many_arguments)]
pub fn handle_play_member_from_hand(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
) -> HandlerResult {
    state_member_play_hand::handle_play_member_from_hand(
        state, db, ctx, frame_data, frame_idx, p_idx, v, a, s,
    )
}

#[allow(clippy::too_many_arguments)]
pub use state_member_play_discard::handle_play_member_from_discard;
