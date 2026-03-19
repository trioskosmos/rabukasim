use crate::core::enums::ChoiceType;
use crate::core::logic::constants::FILTER_MASK_LOWER;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::models::interpreter::HandlerResult;
use crate::core::O_ORDER_DECK;

#[allow(clippy::too_many_arguments)]
pub fn handle_order_deck(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
    a: i64,
    instr_ip: usize,
) -> HandlerResult {
    if state.players[p_idx].looked_cards.is_empty() && v > 0 {
        if state.players[p_idx].deck.len() < v as usize {
            state.resolve_deck_refresh(p_idx);
        }
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
                O_ORDER_DECK,
                0,
                ChoiceType::OrderDeck,
                0,
                -1,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }
        let choice = ctx.choice_index as i32;
        let real_idx = if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len()
        {
            Some(choice as usize)
        } else {
            None
        };

        if let Some(idx) = real_idx {
            let cid = state.players[p_idx].looked_cards.remove(idx);
            state.players[p_idx].push_deck_card(cid);
            if !state.players[p_idx].looked_cards.is_empty() {
                if matches!(suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    O_ORDER_DECK,
                    0,
                    ChoiceType::OrderDeck,
                    0,
                    -1,
                ), HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            }
            let remainder_mode = (a as u64 & FILTER_MASK_LOWER) as u8;
            let looked = std::mem::take(&mut state.players[p_idx].looked_cards);
            if remainder_mode == 1 {
                state.players[p_idx].deck.extend(looked);
            } else if remainder_mode == 2 {
                for cid in looked {
                    state.players[p_idx].deck.insert(0, cid);
                }
            } else {
                state.players[p_idx].discard.extend(looked);
            }
        }
    }

    HandlerResult::Continue
}
