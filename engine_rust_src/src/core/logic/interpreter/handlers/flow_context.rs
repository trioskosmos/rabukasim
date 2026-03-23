use crate::core::logic::models::AbilityFrame;
use super::HandlerResult;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::enums::*;
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

        if matches!(suspend_choice(
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
        ), HandlerResult::Suspend) {
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
        if matches!(suspend_choice(
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
        ), HandlerResult::Suspend) {
            return HandlerResult::Suspend;
        }
    } else {
        ctx.selected_color = ctx.choice_index;
    }
    HandlerResult::Continue
}

pub fn handle_repeat_ability(ctx: &mut AbilityContext, v: i32) -> HandlerResult {
    let max_repeats = v;
    if max_repeats == 0 || ctx.repeat_count < max_repeats as i16 {
        ctx.repeat_count = ctx.repeat_count.saturating_add(1);
        return HandlerResult::Branch(0);
    }
    HandlerResult::Continue
}

pub fn handle_set_target_self(ctx: &mut AbilityContext) {
    ctx.player_id = ctx.activator_id;
}

pub fn handle_set_target_opponent(ctx: &mut AbilityContext) {
    ctx.player_id = 1 - ctx.activator_id;
}

pub fn handle_flavor_action(state: &GameState, v: i32, a: i64, s: i32) {
    if state.debug.debug_mode {
        println!("[DEBUG] FLAVOR_ACTION: v={}, a={}, s={}", v, a, s);
    }
}
