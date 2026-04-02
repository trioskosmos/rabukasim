use super::super::HandlerResult;
use crate::core::*;
use crate::core::enums::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

pub fn handle_swap_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let _s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 && ctx.v_remaining == -1 {
        let cards = state.players[p_idx].success_lives.clone();
        if cards.is_empty() {
            return HandlerResult::Continue;
        }
        state.players[p_idx].looked_cards.clear();
        state.players[p_idx].looked_cards.extend(cards);
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_SWAP_ZONE,
                0,
                ChoiceType::SelectSwapSource,
                0,
                1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }
    if ctx.v_remaining == 1 {
        let picked_idx = ctx.choice_index as usize;
        if picked_idx < state.players[p_idx].looked_cards.len() {
            let cid = state.players[p_idx].looked_cards[picked_idx];
            state.players[p_idx].looked_cards.clear();
            state.players[p_idx].looked_cards.push(cid);
            let mut next_ctx = ctx.clone();
            next_ctx.choice_index = -1;
            next_ctx.v_remaining = 0;
            if matches!(
                suspend_choice(
                    state,
                    db,
                    &next_ctx,
                    &next_ctx,
                    frame_idx,
                    O_SWAP_ZONE,
                    0,
                    ChoiceType::SelectHandPlay,
                    0,
                    1,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }
    } else if ctx.v_remaining == 0 {
        let hand_idx = ctx.choice_index as usize;
        if hand_idx < state.players[p_idx].hand.len()
            && !state.players[p_idx].looked_cards.is_empty()
        {
            let Some(hand_cid) = state.players[p_idx].remove_hand_card(hand_idx) else {
                state.players[p_idx].looked_cards.clear();
                return HandlerResult::Continue;
            };
            let success_cid = state.players[p_idx].looked_cards.remove(0);
            if let Some(pos) = state.players[p_idx]
                .success_lives
                .iter()
                .position(|&x| x == success_cid)
            {
                state.players[p_idx].success_lives[pos] = hand_cid;
                state.players[p_idx].gain_hand_card(success_cid);
            }
        }
    }
    state.players[p_idx].looked_cards.clear();
    HandlerResult::Continue
}
