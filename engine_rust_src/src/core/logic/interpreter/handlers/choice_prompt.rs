use crate::core::logic::models::AbilityFrame;
use super::HandlerResult;
use crate::core::enums::ChoiceType;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::models::interpreter::get_choice_text;
use crate::core::models::suspend_interaction;
use crate::core::logic::interpreter::instruction::BytecodeProgram;

#[allow(clippy::too_many_arguments)]
#[allow(clippy::too_many_arguments)]
pub fn suspend_choice(
    state: &mut GameState,
    db: &CardDatabase,
    choice_ctx: &AbilityContext,
    suspend_ctx: &AbilityContext,
    frame_idx: usize,
    op: i32,
    s: i32,
    choice_type: ChoiceType,
    attr: u64,
    remaining: i16,
) -> HandlerResult {
    suspend_choice_with_options(
        state,
        db,
        choice_ctx,
        suspend_ctx,
        frame_idx,
        op,
        s,
        choice_type,
        attr,
        remaining,
        Vec::new(),
        Vec::new(),
    )
}

#[allow(clippy::too_many_arguments)]
pub fn suspend_choice_with_options(
    state: &mut GameState,
    db: &CardDatabase,
    choice_ctx: &AbilityContext,
    suspend_ctx: &AbilityContext,
    frame_idx: usize,
    op: i32,
    s: i32,
    choice_type: ChoiceType,
    attr: u64,
    remaining: i16,
    options: Vec<serde_json::Value>,
    actions: Vec<i32>,
) -> HandlerResult {
    let choice_text = get_choice_text(db, choice_ctx);
    if suspend_interaction(
        state,
        db,
        suspend_ctx,
        frame_idx,
        op,
        s,
        choice_type,
        &choice_text,
        attr,
        remaining,
        options,
        actions,
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}
