use super::*;
use crate::core::logic::models::AbilityFrame;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

#[allow(clippy::too_many_arguments)]
pub fn handle_move_to_deck(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
    remainder_zone: i32,
    a: i64,
    slot_target: i32,
) -> HandlerResult {
    let _ = db;
    let _ = a;
    let _ = slot_target;
    if !ctx.selected_cards.is_empty() {
        let move_count = if v > 0 {
            (v as usize).min(ctx.selected_cards.len())
        } else {
            ctx.selected_cards.len()
        };
        let moved_cards: Vec<i32> = ctx
            .selected_cards
            .iter()
            .take(move_count)
            .copied()
            .collect();

        for &cid in &moved_cards {
            if let Some(pos) = state.players[p_idx].discard.iter().position(|&c| c == cid) {
                state.players[p_idx].remove_discard_card(pos);
            } else if let Some(pos) = state.players[p_idx].hand.iter().position(|&c| c == cid) {
                state.players[p_idx].remove_hand_card(pos);
            } else if let Some(pos) = state.players[p_idx]
                .success_lives
                .iter()
                .position(|&c| c == cid)
            {
                state.players[p_idx].success_lives.remove(pos);
            } else if let Some(slot) = state.players[p_idx].stage.iter().position(|&c| c == cid) {
                state.handle_member_leaves_stage(p_idx, slot, db, ctx);
            }
        }

        match remainder_zone {
            2 => {
                for &cid in moved_cards.iter().rev() {
                    state.players[p_idx].deck.insert(0, cid);
                }
            }
            1 => {
                for &cid in moved_cards.iter().rev() {
                    state.players[p_idx].push_deck_card(cid);
                }
            }
            _ => {
                for &cid in &moved_cards {
                    state.players[p_idx].push_deck_card(cid);
                }
                let mut rng = Pcg64::from_os_rng();
                state.players[p_idx].deck.shuffle(&mut rng);
            }
        }
        return HandlerResult::Continue;
    }

    for _ in 0..(v as usize) {
        match a as u64 & FILTER_MASK_LOWER {
            1 => {
                if let Some(cid) = state.players[p_idx].pop_discard_card() {
                    state.players[p_idx].push_deck_card(cid);
                }
            }
            4 => {
                let slot = ctx.area_idx as usize;
                if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                    state.players[p_idx].push_deck_card(cid);
                }
            }
            13 => {
                if let Some(cid) = state.players[p_idx].success_lives.pop() {
                    state.players[p_idx].push_deck_card(cid);
                }
            }
            _ => {
                if let Some(cid) = state.players[p_idx].pop_hand_card() {
                    state.players[p_idx].push_deck_card(cid);
                }
            }
        }
    }
    let mut rng = Pcg64::from_os_rng();
    state.players[p_idx].deck.shuffle(&mut rng);
    HandlerResult::Continue
}

#[allow(clippy::too_many_arguments)]
pub fn handle_swap_cards(
    state: &mut GameState,
    p_idx: usize,
    v: i32,
    resolved_slot: i32,
) -> HandlerResult {
    for _ in 0..(v as usize) {
        if state.players[p_idx].deck.is_empty() {
            state.resolve_deck_refresh(p_idx);
        }
        if let Some(cid) = state.players[p_idx].pop_deck_card() {
            match resolved_slot {
                7 => state.players[p_idx].push_discard_card(cid),
                8 => state.players[p_idx].push_deck_card(cid),
                6 => state.players[p_idx].gain_hand_card(cid),
                _ => state.players[p_idx].push_discard_card(cid),
            }
        }
    }
    HandlerResult::Continue
}
