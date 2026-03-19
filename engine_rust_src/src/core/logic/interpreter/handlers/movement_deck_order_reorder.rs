use crate::core::enums::ChoiceType;
use crate::core::logic::constants::FILTER_IS_OPTIONAL;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::models::interpreter::HandlerResult;
use crate::core::O_LOOK_REORDER_DISCARD;

#[allow(clippy::too_many_arguments)]
pub fn handle_look_reorder_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
    a: i64,
    instr_ip: usize,
) -> HandlerResult {
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;

    if is_optional && state.players[p_idx].looked_cards.is_empty() && ctx.choice_index == -1 {
        if matches!(suspend_choice(
            state,
            db,
            ctx,
            ctx,
            instr_ip,
            O_LOOK_REORDER_DISCARD,
            0,
            ChoiceType::Optional,
            a as u64,
            -1,
        ), HandlerResult::Suspend) {
            return HandlerResult::Suspend;
        }
    }

    if is_optional && state.players[p_idx].looked_cards.is_empty() && ctx.choice_index != -1 {
        if ctx.choice_index == 1 {
            if let Some(execution_id) = state.ui.current_execution_id {
                state.ui.cancelled_execution_ids.insert(execution_id);
            }
            return HandlerResult::Continue;
        }
        if ctx.choice_index == 0 {
            ctx.choice_index = -1;
        }
    }

    if state.players[p_idx].looked_cards.is_empty() && v > 0 {
        for _ in 0..(v as usize).min(state.players[p_idx].deck.len()) {
            if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].looked_cards.push(cid);
            }
        }
    }

    if !state.players[p_idx].looked_cards.is_empty() {
        if ctx.choice_index == -1 {
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_LOOK_REORDER_DISCARD,
                0,
                ChoiceType::SelectCardsOrder,
                a as u64,
                -1,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }

        let choice = ctx.choice_index as i32;
        if choice == 99 {
            let looked = std::mem::take(&mut state.players[p_idx].looked_cards);
            for &cid in looked.iter() {
                state.players[p_idx].push_deck_card(cid);
            }
            return HandlerResult::Continue;
        }

        if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len() {
            let cid = state.players[p_idx].looked_cards.remove(choice as usize);
            state.players[p_idx].push_deck_card(cid);

            if !state.players[p_idx].looked_cards.is_empty() {
                if matches!(suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    O_LOOK_REORDER_DISCARD,
                    0,
                    ChoiceType::SelectCardsOrder,
                    a as u64,
                    -1,
                ), HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            } else {
                return HandlerResult::Continue;
            }
        }
    }

    HandlerResult::Continue
}
