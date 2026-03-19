use crate::core::enums::*;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::models::interpreter::get_choice_text;
use crate::core::models::suspend_interaction;
use super::super::HandlerResult;
pub fn handle_swap_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &crate::core::logic::interpreter::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let _s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 && ctx.v_remaining == -1 {
        let cards = state.players[p_idx].success_lives.clone();
        if cards.is_empty() {
            return HandlerResult::Continue;
        }
        state.players[p_idx].looked_cards.clear();
        state.players[p_idx].looked_cards.extend(cards);
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_SWAP_ZONE,
            0,
            ChoiceType::SelectSwapSource,
            &choice_text,
            0,
            1,
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
            if suspend_interaction(
                state,
                db,
                &next_ctx,
                instr_ip,
                O_SWAP_ZONE,
                0,
                ChoiceType::SelectHandPlay,
                "",
                0,
                1,
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


