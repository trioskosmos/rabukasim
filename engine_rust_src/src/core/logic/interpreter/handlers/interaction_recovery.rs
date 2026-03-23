use crate::core::enums::ChoiceType;
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::logic::constants::{CHOICE_ALL, FILTER_IS_OPTIONAL};
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::{O_RECOVER_LIVE, O_RECOVER_MEMBER};

#[path = "interaction_recovery_resolve.rs"]
mod interaction_recovery_resolve;

pub fn handle_recovery(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    real_op: i32,
) -> HandlerResult {
    interaction_recovery_resolve::resolve_recovery(state, db, ctx, frame, frame_idx, real_op)
}
