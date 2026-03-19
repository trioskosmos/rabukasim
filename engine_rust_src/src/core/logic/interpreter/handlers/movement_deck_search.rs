use super::*;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

#[allow(clippy::too_many_arguments)]
pub fn handle_search_deck(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    s: i32,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let search_target = ctx.target_slot as usize;
    if search_target < state.players[p_idx].deck.len() {
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
                        ..Default::default()
                    };
                    state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                } else {
                    state.players[p_idx].gain_hand_card(cid);
                }
            }
            13 => {
                state.players[p_idx].success_lives.push(cid);
            }
            _ => {
                state.players[p_idx].gain_hand_card(cid);
            }
        }
        let mut rng = Pcg64::from_os_rng();
        state.players[p_idx].deck.shuffle(&mut rng);
    }

    let _ = resolved_slot;
    HandlerResult::Continue
}

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
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_ORDER_DECK,
                0,
                ChoiceType::OrderDeck,
                &choice_text,
                0,
                -1,
            ) {
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
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_ORDER_DECK,
                    0,
                    ChoiceType::OrderDeck,
                    "",
                    0,
                    -1,
                ) {
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
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_LOOK_REORDER_DISCARD,
            0,
            ChoiceType::Optional,
            &choice_text,
            a as u64,
            -1,
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
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_LOOK_REORDER_DISCARD,
                0,
                ChoiceType::SelectCardsOrder,
                &choice_text,
                a as u64,
                -1,
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
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_LOOK_REORDER_DISCARD,
                    0,
                    ChoiceType::SelectCardsOrder,
                    "",
                    a as u64,
                    -1,
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
