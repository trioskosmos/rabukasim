use super::*;

#[allow(clippy::too_many_arguments)]
pub fn handle_reveal_until(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
    resolved_slot: i32,
) -> HandlerResult {
    let mut found = false;
    let mut revealed_count = 0;
    let mut revealed_non_matches = Vec::new();
    while !found {
        if revealed_count > 60 {
            break;
        }
        if state.players[p_idx].deck.is_empty() {
            if state.players[p_idx].discard.is_empty() {
                break;
            }
            state.resolve_deck_refresh(p_idx);
            if state.players[p_idx].deck.is_empty() {
                break;
            }
        }

        if let Some(cid) = state.players[p_idx].pop_deck_card() {
            revealed_count += 1;
            let mut new_ctx = ctx.clone();
            new_ctx.source_card_id = cid;
            state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);

            let is_live_only = (s as u32 & FLAG_REVEAL_UNTIL_IS_LIVE as u32) != 0;
            let matches = if is_live_only {
                db.get_live(cid).is_some()
            } else if v == 0 {
                state.card_matches_filter_with_ctx(db, cid, a as u64, ctx)
            } else {
                check_condition_opcode(state, db, v, a as i32, a as u64, s, &new_ctx, 0)
            };

            if matches {
                let dest_slot = resolved_slot & 0x0F;
                if dest_slot == 6 {
                    state.players[p_idx].gain_hand_card(cid);
                } else if dest_slot == 7 {
                    state.players[p_idx].push_discard_card(cid);
                }
                found = true;
            } else {
                revealed_non_matches.push(cid);
            }
        }
    }

    for cid in revealed_non_matches {
        state.players[p_idx].push_discard_card(cid);
    }
    if found && state.players[p_idx].deck.is_empty() && !state.players[p_idx].discard.is_empty() {
        state.players[p_idx].set_flag(PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH, true);
    }

    HandlerResult::Continue
}

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
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                op,
                0,
                ChoiceType::RevealHand,
                "",
                (a as u32) as u64,
                v as i16,
            ) {
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
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    op,
                    0,
                    ChoiceType::RevealHand,
                    "",
                    (a as u32) as u64,
                    next_v,
                ) {
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

#[allow(clippy::too_many_arguments)]
pub fn handle_look_deck_dynamic(
    state: &mut GameState,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    let mut total_score = 0;
    if let Some(res) = state.ui.performance_results.get(&(p_idx as u8)) {
        total_score = res.get("total_score").and_then(|v| v.as_u64()).unwrap_or(0) as i32;
    } else if let Some(res) = state.ui.last_performance_results.get(&(p_idx as u8)) {
        total_score = res.get("total_score").and_then(|v| v.as_u64()).unwrap_or(0) as i32;
    }

    if total_score == 0 {
        total_score = (state.players[p_idx].score as i32) + state.players[p_idx].live_score_bonus;
    }

    let count = (total_score + v) as usize;

    if count > 0 {
        if state.players[p_idx].deck.len() < count {
            state.resolve_deck_refresh(p_idx);
        }
        let deck_len = state.players[p_idx].deck.len();
        for _ in 0..count.min(deck_len) {
            if let Some(cid) = state.players[p_idx].pop_deck_card() {
                state.players[p_idx].looked_cards.push(cid);
            }
        }
    }

    let _ = ctx;
    HandlerResult::Continue
}
