use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use super::*;

#[allow(clippy::too_many_arguments)]
pub fn handle_look_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    op: i32,
    v: i32,
    a: i64,
    instr_ip: usize,
    resolved_slot: i32,
) -> HandlerResult {
    let count = v as usize;
    if resolved_slot == 6 {
        if ctx.choice_index == -1 {
            if state.players[p_idx].hand.len() == 1 {
                ctx.choice_index = 0;
            } else if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                op,
                0,
                ChoiceType::RevealHand,
                (a as u32) as u64,
                v as i16,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }
        let choice = ctx.choice_index as usize;
        if choice != CHOICE_DONE as usize
            && choice != CHOICE_ALL as usize
            && choice < state.players[p_idx].hand.len()
        {
            let cid = state.players[p_idx].hand[choice];
            if !state.players[p_idx].looked_cards.contains(&cid) {
                state.players[p_idx].looked_cards.push(cid);
            }
        }
        if ctx.choice_index == CHOICE_DONE
            || ctx.choice_index == CHOICE_ALL
            || (v > 0 && ctx.v_remaining == 1)
        {
        } else {
            let next_v = if v > 0 {
                (if ctx.v_remaining > 0 {
                    ctx.v_remaining
                } else {
                    v as i16
                }) - 1
            } else {
                0
            };
            if next_v > 0 || v == 0 {
                ctx.v_remaining = next_v;
                if matches!(suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    op,
                    0,
                    ChoiceType::RevealHand,
                    (a as u32) as u64,
                    next_v,
                ), HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            }
        }
    } else {
        if state.players[p_idx].deck.len() < count {
            state.resolve_deck_refresh(p_idx);
        }
        let deck_len = state.players[p_idx].deck.len();
        let mut revealed_cids = Vec::new();
        for _ in 0..count.min(deck_len) {
            if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].looked_cards.push(cid);
                revealed_cids.push(cid);
            }
        }
        if op != O_LOOK_DECK {
            for cid in revealed_cids {
                let mut new_ctx = ctx.clone();
                new_ctx.source_card_id = cid;
                state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
            }
        }
    }

    HandlerResult::Continue
}
