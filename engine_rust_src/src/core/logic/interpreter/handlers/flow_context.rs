use super::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
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
    } else {
        // Opponent has made a choice - copy the chosen card to looked_cards for ADD_TO_HAND
        let choice_idx = ctx.choice_index as usize;
        if choice_idx < ctx.selected_cards.len() {
            let chosen_card = ctx.selected_cards[choice_idx];
            let original_player = 1 - ctx.player_id; // ctx.player_id was flipped, so original is the other one
            state.players[original_player as usize].looked_cards.push(chosen_card);
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

