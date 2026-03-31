use super::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

pub fn handle_opponent_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
) -> HandlerResult {
    if ctx.choice_index == -1 {
        // Flip player_id BEFORE suspension so that the interaction is attributed to the opponent
        ctx.player_id = 1 - ctx.player_id;

        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_OPPONENT_CHOOSE,
                0,
                ChoiceType::OpponentChoose,
                0,
                -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }
    HandlerResult::Continue
}

pub fn handle_color_select(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
) -> HandlerResult {
    if ctx.choice_index == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_COLOR_SELECT,
                0,
                ChoiceType::ColorSelect,
                0,
                -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    } else {
        ctx.selected_color = ctx.choice_index;
    }
    HandlerResult::Continue
}

// Note: handle_repeat_ability, handle_set_target_self, handle_set_target_opponent,
// and handle_flavor_action have been moved to unified.rs

/// Simplified version - same as original since it doesn't need frame
pub fn handle_opponent_choose_simple(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
) -> HandlerResult {
    handle_opponent_choose(state, db, ctx, frame_idx)
}

/// Simplified version - same as original since it doesn't need frame
pub fn handle_color_select_simple(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
) -> HandlerResult {
    handle_color_select(state, db, ctx, frame_idx)
}
