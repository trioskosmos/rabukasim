use super::*;
use crate::core::logic::models::AbilityFrame;
#[path = "state_member_tap_member_prompt.rs"]
mod state_member_tap_member_prompt;
#[path = "state_member_tap_member_selected.rs"]
mod state_member_tap_member_selected;

pub fn handle_tap_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    if ctx.choice_index == -1 {
        return state_member_tap_member_prompt::handle_tap_member_prompt(
            state,
            db,
            ctx,
            frame,
            frame_idx,
            p_idx,
            a,
            resolved_slot,
        );
    } else {
        return state_member_tap_member_selected::handle_tap_member_selected(
            state,
            db,
            ctx,
            frame,
            frame_idx,
            p_idx,
            a,
            resolved_slot,
        );
    }
}
