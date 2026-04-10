use crate::core::enums::{ChoiceType, Zone};
use crate::core::logic::constants::{CHOICE_ALL, CHOICE_DONE, FILTER_IS_OPTIONAL, FILTER_MASK_LOWER, FLAG_REVEAL_UNTIL_IS_LIVE};
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState, TriggerType};
use crate::core::models::interpreter::{check_condition_opcode, resolve_target_slot, HandlerResult};
use crate::core::{O_ADD_HEARTS, O_LOOK_DECK, O_ORDER_DECK, O_LOOK_REORDER_DISCARD, O_REVEAL_CARDS, O_REVEAL_UNTIL, O_SEARCH_DECK, O_MOVE_TO_DECK, O_SWAP_CARDS, O_MOVE_TO_DISCARD, O_LOOK_AND_CHOOSE, O_RECOVER_LIVE, O_RECOVER_MEMBER, O_PLAY_LIVE_FROM_DISCARD, O_SELECT_CARDS, O_SWAP_ZONE, O_LOOK_DECK_DYNAMIC, O_CHEER_REVEAL};
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

/// Import frequently used handler modules with shorter names
use crate::core::logic::interpreter::handlers::interaction::handle_look_and_choose;
use crate::core::logic::interpreter::handlers::interaction::handle_play_live_from_discard;
use crate::core::logic::interpreter::handlers::interaction::handle_recovery;
use crate::core::logic::interpreter::handlers::interaction::handle_select_cards;
use crate::core::logic::interpreter::handlers::interaction_zone::{
    collect_zone_cards, draw_zone_cards,
};
use crate::core::logic::interpreter::handlers::movement::handle_move_to_discard;
use crate::core::logic::interpreter::handlers::movement::handle_swap_zone;

fn prepend_cards_preserve_order(
    deck: &mut smallvec::SmallVec<[i32; 60]>,
    cards: impl IntoIterator<Item = i32>,
) {
    let mut new_deck = smallvec::SmallVec::<[i32; 60]>::new();
    new_deck.extend(cards);
    new_deck.extend(deck.drain(..));
    *deck = new_deck;
}

fn prepend_cards_reverse_order<I>(deck: &mut smallvec::SmallVec<[i32; 60]>, cards: I)
where
    I: IntoIterator<Item = i32>,
    I::IntoIter: DoubleEndedIterator,
{
    let mut new_deck = smallvec::SmallVec::<[i32; 60]>::new();
    new_deck.extend(cards.into_iter().rev());
    new_deck.extend(deck.drain(..));
    *deck = new_deck;
}

// Main router for deck-related opcodes
#[allow(clippy::too_many_arguments)]
pub fn handle_deck_zones(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.resolved_filter_attr() as i64;
    let s = frame_data.slot.to_raw();
    let p_idx = ctx.player_id as usize;
    let slot = frame_data.slot;
    let target_slot = slot.target_slot as i32;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };
    let look_resolved_slot = if op == O_REVEAL_CARDS {
        if s == Zone::Hand as i32
            || slot.source_zone == Zone::Hand
            || resolved_slot == Zone::Hand as i32
        {
            Zone::Hand as i32
        } else {
            resolved_slot
        }
    } else {
        resolved_slot
    };

    match op {
        O_SEARCH_DECK => handle_search_deck(state, db, ctx, p_idx, s, a),
        O_ORDER_DECK => handle_order_deck(state, db, ctx, p_idx, v, a, frame_idx),
        O_LOOK_REORDER_DISCARD => handle_look_reorder_discard(state, db, ctx, p_idx, v, a, frame_idx),
        O_MOVE_TO_DECK => handle_move_to_deck(state, db, ctx, p_idx, v, slot.remainder_zone as i32, a),
        O_SWAP_CARDS => handle_swap_cards(state, p_idx, v, resolved_slot),
        O_REVEAL_UNTIL => handle_reveal_until(state, db, ctx, p_idx, v, a, s, resolved_slot),
        O_LOOK_DECK | O_REVEAL_CARDS | O_CHEER_REVEAL => {
            handle_look_cards(state, db, ctx, &frame_data, p_idx, op, v, a, frame_idx, look_resolved_slot)
        }
        O_LOOK_DECK_DYNAMIC => handle_look_deck_dynamic(state, ctx, p_idx, v),
        O_MOVE_TO_DISCARD => handle_move_to_discard(state, db, ctx, &frame_data, frame_idx),
        O_LOOK_AND_CHOOSE => handle_look_and_choose(state, db, ctx, &frame_data, frame_idx),
        O_RECOVER_LIVE | O_RECOVER_MEMBER => handle_recovery(state, db, ctx, &frame_data, frame_idx, op),
        O_PLAY_LIVE_FROM_DISCARD => handle_play_live_from_discard(state, db, ctx, &frame_data, frame_idx),
        O_SELECT_CARDS => handle_select_cards(state, db, ctx, &frame_data, frame_idx),
        O_SWAP_ZONE => handle_swap_zone(state, db, ctx, &frame_data, frame_idx),
        _ => HandlerResult::Continue,
    }
}

// Search deck and play a specific card
fn handle_search_deck(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    s: i32,
    a: i64,
) -> HandlerResult {
    let search_target = ctx.target_slot as usize;
    if search_target >= state.players[p_idx].deck.len() {
        return HandlerResult::Continue;
    }

    let cid = state.players[p_idx].remove_deck_card(search_target).unwrap();
    match s {
        4 => {
            let slot = (a as u64 & FILTER_MASK_LOWER) as usize;
            if slot < 3 {
                if let Some(old) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                    state.players[p_idx].push_discard_card(old);
                }
                state.players[p_idx].stage[slot] = cid;
                state.players[p_idx].set_tapped(slot, false);
                state.players[p_idx].set_moved(slot, true);
                state.register_played_member(p_idx, cid, db);
                let new_ctx = AbilityContext {
                    source_card_id: cid,
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: slot as i16,
                    trigger_type: TriggerType::OnPlay,
                    ..Default::default()
                };
                state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
            } else {
                state.players[p_idx].gain_hand_card(cid);
            }
        }
        13 => state.push_success_live_card(p_idx, cid),
        _ => state.players[p_idx].gain_hand_card(cid),
    }

    let mut rng = Pcg64::from_os_rng();
    state.players[p_idx].deck.shuffle(&mut rng);
    HandlerResult::Continue
}

// Order cards on top of deck
pub fn handle_order_deck(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
    a: i64,
    frame_idx: usize,
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
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_ORDER_DECK, 0, ChoiceType::OrderDeck, 0, -1),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }

        let choice = ctx.choice_index as i32;
        let real_idx = if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len() {
            Some(choice as usize)
        } else {
            None
        };

        if let Some(idx) = real_idx {
            let cid = state.players[p_idx].looked_cards.remove(idx);
            state.players[p_idx].push_deck_card(cid);
            if !state.players[p_idx].looked_cards.is_empty() {
                if matches!(
                    suspend_choice(state, db, ctx, ctx, frame_idx, O_ORDER_DECK, 0, ChoiceType::OrderDeck, 0, -1),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
            let remainder_mode = (a as u64 & FILTER_MASK_LOWER) as u8;
            let looked = std::mem::take(&mut state.players[p_idx].looked_cards);
            if remainder_mode == 1 {
                state.players[p_idx].deck.extend(looked);
            } else if remainder_mode == 2 {
                prepend_cards_reverse_order(&mut state.players[p_idx].deck, looked);
            } else {
                state.players[p_idx].discard.extend(looked);
            }
        }
    }

    HandlerResult::Continue
}

// Look at cards and choose order, with optional cancel
pub fn handle_look_reorder_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
    a: i64,
    frame_idx: usize,
) -> HandlerResult {
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;

    if is_optional && state.players[p_idx].looked_cards.is_empty() && ctx.choice_index == -1 {
        if matches!(
            suspend_choice(state, db, ctx, ctx, frame_idx, O_LOOK_REORDER_DISCARD, 0, ChoiceType::Optional, a as u64, -1),
            HandlerResult::Suspend
        ) {
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
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_LOOK_REORDER_DISCARD, 0, ChoiceType::SelectCardsOrder, a as u64, -1),
                HandlerResult::Suspend
            ) {
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
                if matches!(
                    suspend_choice(state, db, ctx, ctx, frame_idx, O_LOOK_REORDER_DISCARD, 0, ChoiceType::SelectCardsOrder, a as u64, -1),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            } else {
                return HandlerResult::Continue;
            }
        }
    }

    HandlerResult::Continue
}

// Move cards to deck from various zones
fn handle_move_to_deck(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    v: i32,
    remainder_zone: i32,
    a: i64,
) -> HandlerResult {
    if !ctx.selected_cards.is_empty() || !state.players[p_idx].looked_cards.is_empty() {
        let move_count = if v > 0 {
            if !ctx.selected_cards.is_empty() {
                (v as usize).min(ctx.selected_cards.len())
            } else {
                (v as usize).min(state.players[p_idx].looked_cards.len())
            }
        } else {
            if !ctx.selected_cards.is_empty() {
                ctx.selected_cards.len()
            } else {
                state.players[p_idx].looked_cards.len()
            }
        };
        let moved_cards: Vec<i32> = if !ctx.selected_cards.is_empty() {
            ctx.selected_cards.iter().take(move_count).copied().collect()
        } else {
            state.players[p_idx]
                .looked_cards
                .iter()
                .take(move_count)
                .copied()
                .collect()
        };

        for &cid in &moved_cards {
            if let Some(pos) = state.players[p_idx].discard.iter().position(|&c| c == cid) {
                state.players[p_idx].remove_discard_card(pos);
            } else if let Some(pos) = state.players[p_idx].hand.iter().position(|&c| c == cid) {
                state.players[p_idx].remove_hand_card(pos);
            } else if let Some(pos) = state.players[p_idx].success_lives.iter().position(|&c| c == cid) {
                state.players[p_idx].success_lives.remove(pos);
            } else if let Some(slot) = state.players[p_idx].stage.iter().position(|&c| c == cid) {
                state.handle_member_leaves_stage(p_idx, slot, db, ctx);
            } else if let Some(pos) = state.players[p_idx].looked_cards.iter().position(|&c| c == cid) {
                state.players[p_idx].looked_cards.remove(pos);
            } else if let Some(pos) = state.players[p_idx].revealed_cards.iter().position(|&c| c == cid) {
                state.players[p_idx].revealed_cards.remove(pos);
            }
        }

        match remainder_zone {
            2 => {
                prepend_cards_preserve_order(&mut state.players[p_idx].deck, moved_cards);
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

// Swap cards from deck to hand/discard
fn handle_swap_cards(state: &mut GameState, p_idx: usize, v: i32, resolved_slot: i32) -> HandlerResult {
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

// Reveal cards from deck until condition met
fn handle_reveal_until(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
    resolved_slot: i32,
) -> HandlerResult {
    let mut found = false;
    let mut revealed_count = 0;
    let mut revealed_non_matches = Vec::new();
    let mut stop_after_refresh = false;

    while !found {
        if revealed_count > 60 {
            break;
        }
        if state.players[p_idx].deck.is_empty() {
            if state.players[p_idx].discard.is_empty() {
                if revealed_non_matches.is_empty() {
                    break;
                }
                for cid in revealed_non_matches.drain(..) {
                    state.players[p_idx].push_discard_card(cid);
                }
                stop_after_refresh = true;
            }

            if state.players[p_idx].discard.is_empty() {
                break;
            }
            state.players[p_idx].set_flag(PlayerState::FLAG_DECK_REFRESHED, true);
            state.resolve_deck_refresh(p_idx);
            if stop_after_refresh {
                break;
            }
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
                if dest_slot == Zone::Hand as i32 {
                    state.players[p_idx].gain_hand_card(cid);
                } else if dest_slot == Zone::Discard as i32 {
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
        state.players[p_idx].set_flag(PlayerState::FLAG_DECK_REFRESHED, true);
        state.players[p_idx].set_flag(PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH, true);
    }

    HandlerResult::Continue
}

// Look at deck cards (reveal to hand or look at top)
fn handle_look_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    p_idx: usize,
    op: i32,
    v: i32,
    a: i64,
    frame_idx: usize,
    _resolved_slot: i32,
) -> HandlerResult {
    let count = v as usize;
    let filter_attr = filter_attr_from_params(frame_data.params).unwrap_or(a as u64);
    let source_zone = frame_data.slot.source_zone;
    let sparse_choose_filter = state
        .interaction_stack
        .last()
        .filter(|interaction| {
            interaction.choice_type == ChoiceType::LookAndChoose
                && interaction.effect_opcode == O_LOOK_AND_CHOOSE
                && interaction.ctx.source_card_id == ctx.source_card_id
                && interaction.ctx.ability_index == ctx.ability_index
                && interaction.ctx.program_counter as usize == frame_idx
                && interaction.filter_attr != 0
        })
        .map(|interaction| interaction.filter_attr)
        .or_else(|| sparse_look_deck_choice_filter(db, ctx, frame_idx, op));

    if source_zone == crate::core::enums::Zone::Hand {
        // Reveal from hand
        if ctx.choice_index == -1 && ctx.v_remaining == -1 {
            state.players[p_idx].revealed_cards.clear();
        }
        if ctx.choice_index == -1 {
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, op, 0, ChoiceType::RevealHand, filter_attr, v as i16),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }

        let choice = ctx.choice_index as usize;
        let hand_cards = collect_zone_cards(state, p_idx, crate::core::enums::Zone::Hand);
        if choice != CHOICE_DONE as usize && choice != CHOICE_ALL as usize && choice < hand_cards.len() {
            let cid = hand_cards[choice];
            if !state.players[p_idx].looked_cards.contains(&cid) {
                state.players[p_idx].looked_cards.push(cid);
            }
            if !state.players[p_idx].revealed_cards.contains(&cid) {
                state.players[p_idx].revealed_cards.push(cid);
            }
        }

        if ctx.choice_index != CHOICE_DONE && ctx.choice_index != CHOICE_ALL && !(v > 0 && ctx.v_remaining == 1) {
            let next_v = if v > 0 {
                (if ctx.v_remaining > 0 { ctx.v_remaining } else { v as i16 }) - 1
            } else {
                0
            };
            if next_v > 0 || v == 0 {
                ctx.v_remaining = next_v;
                if matches!(
                    suspend_choice(state, db, ctx, ctx, frame_idx, op, 0, ChoiceType::RevealHand, filter_attr, next_v),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    } else {
        // Look at top of deck
        if state.players[p_idx].looked_cards.is_empty() {
            state.players[p_idx].revealed_cards.clear();
            let revealed_cids = draw_zone_cards(state, p_idx, crate::core::enums::Zone::Deck, count);
            state.players[p_idx].looked_cards.extend(revealed_cids.iter().copied());
            state.players[p_idx].revealed_cards.extend(revealed_cids.iter().copied());

            if op != O_LOOK_DECK {
                for cid in revealed_cids {
                    let mut new_ctx = ctx.clone();
                    new_ctx.source_card_id = cid;
                    state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
                }
            }
        }

        if (op == O_LOOK_DECK || op == O_LOOK_AND_CHOOSE)
            && source_zone != crate::core::enums::Zone::Hand
            && frame_data.slot.target_slot == Zone::Hand as u8
        {
            let compiled_choose_count = frame_data.look_choose().choose_count.max(1) as usize;
            if compiled_choose_count > 1 {
                return handle_look_and_choose(state, db, ctx, frame_data, frame_idx);
            }
            if ctx.choice_index == -1 {
                let mut target_ctx = ctx.clone();
                target_ctx.choice_index = -1;
                if matches!(
                    suspend_choice(
                        state,
                        db,
                        &target_ctx,
                        &target_ctx,
                        frame_idx,
                        O_LOOK_AND_CHOOSE,
                        frame_data.slot.to_raw(),
                        ChoiceType::LookAndChoose,
                        filter_attr,
                        1,
                    ),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }

            let choice = ctx.choice_index as usize;
            if choice < state.players[p_idx].looked_cards.len() {
                let chosen = state.players[p_idx].looked_cards.remove(choice);
                state.players[p_idx].gain_hand_card(chosen);
            }

            let remainder: Vec<i32> = state.players[p_idx].looked_cards.drain(..).collect();
            let remainder_zone = if frame_data.slot.dest_zone != Zone::Default {
                frame_data.slot.dest_zone
            } else if (ctx.ability_index >= 0
                || ctx.ability_card_id >= 0
                || ctx.trigger_type != TriggerType::None)
                && frame_data.slot.target_slot == Zone::Hand as u8
            {
                Zone::Discard
            } else {
                Zone::Default
            };
            match remainder_zone {
                Zone::Discard => {
                    for cid in remainder {
                        state.players[p_idx].push_discard_card(cid);
                    }
                }
                Zone::DeckBottom => {
                    prepend_cards_preserve_order(&mut state.players[p_idx].deck, remainder);
                }
                Zone::Deck | Zone::DeckTop | Zone::Default => {
                    for cid in remainder.into_iter().rev() {
                        state.players[p_idx].push_deck_card(cid);
                    }
                }
                Zone::Hand => {
                    for cid in remainder {
                        state.players[p_idx].gain_hand_card(cid);
                    }
                }
                _ => {
                    for cid in remainder {
                        state.players[p_idx].push_discard_card(cid);
                    }
                }
            }
            if state.players[p_idx].deck.is_empty() && !state.players[p_idx].discard.is_empty() {
                state.players[p_idx].set_flag(PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH, true);
            }
            ctx.choice_index = -1;
            ctx.v_remaining = -1;
            return HandlerResult::Continue;
        }

        if let Some(choice_filter) = sparse_choose_filter {
            if ctx.choice_index == -1 {
                let mut target_ctx = ctx.clone();
                target_ctx.choice_index = -1;
                if matches!(
                    suspend_choice(
                        state,
                        db,
                        &target_ctx,
                        &target_ctx,
                        frame_idx,
                        O_LOOK_AND_CHOOSE,
                        frame_data.slot.to_raw(),
                        ChoiceType::LookAndChoose,
                        choice_filter,
                        1,
                    ),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }

            let choice = ctx.choice_index as usize;
            let reveal_pool = if state.players[p_idx].looked_cards.is_empty() {
                &state.players[p_idx].revealed_cards
            } else {
                &state.players[p_idx].looked_cards
            };
            if choice < reveal_pool.len() {
                let chosen = reveal_pool[choice];
                if chosen >= 0 && !ctx.selected_cards.contains(&chosen) {
                    ctx.selected_cards.push(chosen);
                }
            }

            let remainder: Vec<i32> = if state.players[p_idx].looked_cards.is_empty() {
                state.players[p_idx].revealed_cards.drain(..).collect()
            } else {
                state.players[p_idx].revealed_cards.clear();
                state.players[p_idx].looked_cards.drain(..).collect()
            };
            for cid in remainder {
                state.players[p_idx].push_discard_card(cid);
            }
            ctx.choice_index = -1;
            ctx.v_remaining = -1;
            return HandlerResult::Continue;
        }
    }

    HandlerResult::Continue
}

fn sparse_look_deck_choice_filter(
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    op: i32,
) -> Option<u64> {
    if op != O_LOOK_DECK {
        return None;
    }

    let source_card_id = if ctx.ability_card_id >= 0 {
        ctx.ability_card_id
    } else {
        ctx.source_card_id
    };
    let ability_index = ctx.ability_index.max(0) as usize;
    let ability = db
        .get_member(source_card_id)
        .and_then(|member| member.abilities.get(ability_index))
        .or_else(|| db.get_live(source_card_id).and_then(|live| live.abilities.get(ability_index)))?;
    let frames = ability.resolved_frames();

    let mut tail = frames.iter().skip(frame_idx + 1);
    let has_color_copy_bonus = tail.clone().any(|frame| {
        let components = frame.components();
        components.opcode == O_ADD_HEARTS && components.value == 99
    });
    let has_stage_target = tail.clone().any(|frame| frame.opcode() == crate::core::O_SELECT_MEMBER);
    if !has_color_copy_bonus || !has_stage_target {
        return None;
    }

    tail.find_map(|frame| {
        let components = frame.components();
        let filter = components.filter;
        let has_character_filter = filter.char_id_1 != 0 || filter.char_id_2 != 0 || filter.char_id_3 != 0;
        if has_character_filter {
            Some(components.resolved_filter_attr())
        } else {
            None
        }
    })
}

// Dynamic look count based on performance score
fn handle_look_deck_dynamic(state: &mut GameState, ctx: &mut AbilityContext, p_idx: usize, v: i32) -> HandlerResult {
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
