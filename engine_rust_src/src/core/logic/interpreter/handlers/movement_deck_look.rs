use super::*;
use crate::core::logic::models::AbilityFrame;

#[path = "movement_deck_look_cards.rs"]
mod movement_deck_look_cards;

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
            state.players[p_idx].set_flag(PlayerState::FLAG_DECK_REFRESHED, true);
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
            } else {
                v != 0 && check_condition_opcode(state, db, v, a as i32, a as u64, s, &new_ctx, 0)
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
    frame_idx: usize,
    resolved_slot: i32,
) -> HandlerResult {
    movement_deck_look_cards::handle_look_cards(
        state,
        db,
        ctx,
        p_idx,
        op,
        v,
        a,
        frame_idx,
        resolved_slot,
    )
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
