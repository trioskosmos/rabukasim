use super::super::HandlerResult;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

/// Draw handler - delegates to unified implementation
pub fn handle_draw(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> HandlerResult {
    // Direct delegation to unified handler
    super::super::unified::handle_draw(state, db, ctx, frame_data)
}
