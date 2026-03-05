use crate::core::enums::*;
use crate::core::logic::constants::{FILTER_MASK_LOWER, FILTER_IS_OPTIONAL, FLAG_REVEAL_UNTIL_IS_LIVE, CHOICE_DONE, CHOICE_ALL};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, TriggerType, PlayerState};
use crate::core::models::interpreter::{resolve_target_slot, check_condition_opcode, get_choice_text};
use crate::core::models::suspend_interaction;
use crate::core::logic::interpreter::logging;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;
use super::HandlerResult;
use super::interaction::*;

pub fn handle_draw(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
) -> Option<HandlerResult> {
    let op = instr.op;
    let v = instr.v;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let count = v as u32;
    let target_p = if s == 2 {
        1 - p_idx
    } else if s == 3 {
        0
    } else {
        p_idx
    };

    match op {
        O_DRAW => {
            if s == 3 {
                state.draw_cards(0, count);
                state.draw_cards(1, count);
            } else {
                state.draw_cards(target_p, count);
            }
            state.log_event(
                "EFFECT",
                &format!("Draw {} card(s)", count),
                ctx.source_card_id,
                ctx.ability_index,
                p_idx as u8,
                None,
                true,
            );
        }
        O_DRAW_UNTIL => {
            let target_hand_size = v as usize;
            let current_hand_size = state.players[p_idx].hand.len();
            if current_hand_size < target_hand_size {
                let to_draw = (target_hand_size - current_hand_size) as u32;
                state.draw_cards(p_idx, to_draw);
            }
        }
        O_ADD_TO_HAND => {
            if s == 90 || s == 6 {
                for _ in 0..v as usize {
                    if !state.players[p_idx].looked_cards.is_empty() {
                        let cid = state.players[p_idx].looked_cards.remove(0);
                        state.players[p_idx].hand.push(cid);
                        state.players[p_idx].hand_increased_this_turn = state.players
                            [p_idx]
                            .hand_increased_this_turn
                            .saturating_add(1);
                    }
                }
            } else {
                state.draw_cards(p_idx, v as u32);
            }
        }
        _ => return None,
    }
    Some(HandlerResult::Continue)
}

pub fn handle_move_to_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> Option<bool> {
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let base_p = ctx.activator_id as usize;
    let p_idx = ctx.player_id as usize;
    let mut source_zone = instr.s.source_zone;
    if source_zone == Zone::Default {
        let ts = instr.s.target_slot;
        if ts == 4 {
            source_zone = Zone::Stage;
        } else if ts == 6 {
            source_zone = Zone::Hand;
        } else if ts == 13 {
            source_zone = Zone::LiveSet;
        } else {
            source_zone = Zone::Deck;
        }
    }
    let target_player_idx = if instr.s.is_opponent {
        1 - base_p
    } else {
        base_p
    };

    let count = if (v as u32 & (1 << 31)) != 0 {
        let target_size = v & 0x7FFFFFFF;
        let current_size = match source_zone {
            Zone::Hand => state.players[target_player_idx].hand.len() as i32,
            Zone::Stage => state.players[target_player_idx]
                .stage
                .iter()
                .filter(|&&c| c >= 0)
                .count() as i32,
            Zone::LiveSet | Zone::SuccessPile => state.players[target_player_idx].success_lives.len() as i32,
            Zone::Deck | Zone::Default => state.players[target_player_idx].deck.len() as i32,
            Zone::Energy => state.players[target_player_idx].energy_zone.len() as i32,
            _ => 0,
        };
        (current_size - target_size).max(0)
    } else {
        v
    };
    if target_player_idx != p_idx
        && state.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY)
    {
        return Some(false);
    }

    let filter_attr = (a as u64) & 0xFFFFFFFFFFFF0FFF;
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;

    if state.debug.debug_mode {
        println!("[DEBUG_MOV] h_m_t_d: cid={}, choice={}, optional={}, attr={:x}", ctx.source_card_id, ctx.choice_index, is_optional, a as u64);
    }

    if is_optional && ctx.choice_index == -1 {
        let available_count = match source_zone {
            Zone::Hand => state.players[target_player_idx].hand.len() as i32,
            Zone::Stage => state.players[target_player_idx]
                .stage
                .iter()
                .filter(|&&c| c >= 0)
                .count() as i32,
            Zone::LiveSet | Zone::SuccessPile => state.players[target_player_idx].success_lives.len() as i32,
            Zone::Energy => state.players[target_player_idx].energy_zone.len() as i32,
            Zone::Deck | Zone::Default => state.players[target_player_idx].deck.len() as i32,
            _ => 99,
        };
        if available_count < v {
            return Some(false);
        }
    }

    let mut next_ctx = ctx.clone();
    let choice_type = if source_zone == Zone::Hand {
        ChoiceType::SelectHandDiscard
    } else {
        ChoiceType::SelectDiscard
    };

    if source_zone == Zone::Stage && next_ctx.choice_index == -1 && count == 1 {
        let slot = if next_ctx.area_idx >= 0 {
            next_ctx.area_idx as usize
        } else {
            0
        };
        if slot < 3 && state.players[p_idx].stage[slot] == ctx.source_card_id {
            next_ctx.choice_index = slot as i16;
        }
    }

    if next_ctx.choice_index == -1 && count > 0 && source_zone != Zone::Default && source_zone != Zone::Deck {
        // Auto-pick shortcut for single mandatory target
        if state.players[p_idx].looked_cards.len() == 1 && !is_optional && count == 1 {
            next_ctx.choice_index = 0;
        }

        if next_ctx.choice_index == -1 {
            if suspend_interaction(
                state,
                db,
                &next_ctx,
                instr_ip,
                O_MOVE_TO_DISCARD,
                s,
                choice_type,
                "",
                filter_attr,
                count as i16,
            ) {
                return None;
            }
        }
    }

    if next_ctx.choice_index != -1 {
        if next_ctx.choice_index == CHOICE_DONE {
            if is_optional {
                return Some(false);
            } else {
                if (next_ctx.v_remaining > 0) || (next_ctx.v_remaining == -1 && count > 0) {
                    if suspend_interaction(
                        state,
                        db,
                        &next_ctx,
                        instr_ip,
                        O_MOVE_TO_DISCARD,
                        s,
                        choice_type,
                        "You must select more cards",
                        filter_attr,
                        if next_ctx.v_remaining > 0 {
                            next_ctx.v_remaining
                        } else {
                            count as i16
                        },
                    ) {
                        return None;
                    }
                    return Some(true);
                }
            }
        }

        let idx = next_ctx.choice_index as usize;
        let mut removed_cid = -1;
        match source_zone {
            Zone::Hand => {
                if idx < state.players[target_player_idx].hand.len() {
                    removed_cid = state.players[target_player_idx].hand[idx];
                    if removed_cid != -1 {
                        if (s & (1 << 25)) != 0 {
                            if let Some(m) = db.get_member(removed_cid) {
                                ctx.v_accumulated = m.cost as i16;
                            }
                        }
                        state.players[target_player_idx].hand[idx] = -1;
                        state.players[target_player_idx].hand.retain(|c| *c != -1);
                    }
                }
            }
            Zone::Stage => {
                let slot = if idx < 3 {
                    idx
                } else if next_ctx.area_idx >= 0 {
                    next_ctx.area_idx as usize
                } else {
                    0
                };
                if let Some(cid) = state.handle_member_leaves_stage(target_player_idx, slot, db, &next_ctx) {
                    removed_cid = cid;
                }
            }
            Zone::LiveSet | Zone::SuccessPile => {
                if !state.players[target_player_idx].success_lives.is_empty() {
                    removed_cid = state.players[target_player_idx].success_lives.pop().unwrap() as i32;
                }
            }
            Zone::Deck | Zone::Default => {
                if !state.players[target_player_idx].deck.is_empty() {
                    removed_cid = state.players[target_player_idx].deck.pop().unwrap() as i32;
                }
            }
            Zone::Energy => {
                if !state.players[target_player_idx].energy_zone.is_empty() {
                    removed_cid = state.players[target_player_idx].energy_zone.pop().unwrap() as i32;
                }
            }
            _ => {}
        }
        if removed_cid >= 0 {
            state.players[target_player_idx].discard.push(removed_cid as i32);
            next_ctx.v_remaining = if next_ctx.v_remaining > 0 {
                next_ctx.v_remaining - 1
            } else {
                (count as i16) - 1
            };
            if next_ctx.v_remaining > 0 {
                next_ctx.choice_index = -1;
                if suspend_interaction(
                    state,
                    db,
                    &next_ctx,
                    instr_ip,
                    O_MOVE_TO_DISCARD,
                    s,
                    choice_type,
                    "",
                    filter_attr,
                    next_ctx.v_remaining,
                ) {
                    return None;
                }
            }
        }
    } else {
        for _ in 0..count {
            match source_zone {
                Zone::Hand => {
                    if let Some(cid) = state.players[target_player_idx].hand.pop() {
                        state.players[target_player_idx].discard.push(cid);
                    }
                }
                Zone::Stage => {
                    let slot = if next_ctx.area_idx >= 0 {
                        next_ctx.area_idx as usize
                    } else {
                        0
                    };
                    if let Some(cid) = state.handle_member_leaves_stage(target_player_idx, slot, db, &next_ctx)
                    {
                        state.players[target_player_idx].discard.push(cid as i32);
                    }
                }
                Zone::LiveSet | Zone::SuccessPile => {
                    if let Some(cid) = state.players[target_player_idx].success_lives.pop() {
                        state.players[target_player_idx].discard.push(cid);
                    }
                }
                Zone::Deck | Zone::Default => {
                    if let Some(cid) = state.players[target_player_idx].deck.pop() {
                        state.players[target_player_idx].discard.push(cid);
                    }
                }
                Zone::Energy => {
                    if let Some(cid) = state.players[target_player_idx].energy_zone.pop() {
                        state.players[target_player_idx].discard.push(cid);
                    }
                }
                _ => {}
            }
        }
    }

    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(O_MOVE_TO_DISCARD, v, a, s, 0) {
            state.log(msg);
        }
    }

    state.players[target_player_idx].hand.retain(|c| *c != -1);
    Some(true)
}

pub fn handle_deck_zones(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> Option<HandlerResult> {
    let op = instr.op;
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let target_slot = instr.s.target_slot as i32;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_SEARCH_DECK => {
            let search_target = ctx.target_slot as usize;
            if search_target < state.players[p_idx].deck.len() {
                let cid = state.players[p_idx].deck.remove(search_target);
                match s {
                    4 => {
                        let slot = (a as u64 & FILTER_MASK_LOWER) as usize;
                        if slot < 3 {
                            if let Some(old) =
                                state.handle_member_leaves_stage(p_idx, slot, db, ctx)
                            {
                                state.players[p_idx].discard.push(old);
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
                            state.players[p_idx].hand.push(cid);
                            state.players[p_idx].hand_increased_this_turn = state.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        }
                    }
                    13 => {
                        state.players[p_idx].success_lives.push(cid);
                    }
                    _ => {
                        state.players[p_idx].hand.push(cid);
                        state.players[p_idx].hand_increased_this_turn = state.players
                            [p_idx]
                            .hand_increased_this_turn
                            .saturating_add(1);
                    }
                }
                let mut rng = Pcg64::from_os_rng();
                state.players[p_idx].deck.shuffle(&mut rng);
            }
        }
        O_ORDER_DECK => {
            if state.players[p_idx].looked_cards.is_empty() && v > 0 {
                if state.players[p_idx].deck.len() < v as usize {
                    state.resolve_deck_refresh(p_idx);
                }
                for _ in 0..(v as usize).min(state.players[p_idx].deck.len()) {
                    if let Some(cid) = state.players[p_idx].deck.pop() {
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
                        return Some(HandlerResult::Suspend);
                    }
                }
                let choice = ctx.choice_index as i32;
                let real_idx = if choice >= 0
                    && (choice as usize) < state.players[p_idx].looked_cards.len()
                {
                    Some(choice as usize)
                } else {
                    None
                };

                if let Some(idx) = real_idx {
                    let cid = state.players[p_idx].looked_cards.remove(idx);
                    state.players[p_idx].deck.push(cid);
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
                            return Some(HandlerResult::Suspend);
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
        }
        O_LOOK_REORDER_DISCARD => {
            if state.players[p_idx].looked_cards.is_empty() && v > 0 {
                for _ in 0..(v as usize).min(state.players[p_idx].deck.len()) {
                    if let Some(cid) = state.players[p_idx].deck.pop() {
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
                        0,
                        -1,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let choice = ctx.choice_index as i32;
                if choice == 99 {
                    let looked = std::mem::take(&mut state.players[p_idx].looked_cards);
                    for &cid in looked.iter() {
                        state.players[p_idx].deck.push(cid);
                    }
                    return Some(HandlerResult::Continue);
                }

                if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len() {
                    let cid = state.players[p_idx].looked_cards.remove(choice as usize);
                    state.players[p_idx].deck.push(cid);

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
                            0,
                            -1,
                        ) {
                            return Some(HandlerResult::Suspend);
                        }
                    } else {
                        return Some(HandlerResult::Continue);
                    }
                }
            }
        }
        O_MOVE_TO_DECK => {
            for _ in 0..(v as usize) {
                match a as u64 & FILTER_MASK_LOWER {
                    1 => {
                        if let Some(cid) = state.players[p_idx].discard.pop() {
                            state.players[p_idx].deck.push(cid);
                        }
                    }
                    4 => {
                        let slot = ctx.area_idx as usize;
                        if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                            state.players[p_idx].deck.push(cid);
                        }
                    }
                    13 => {
                        if let Some(cid) = state.players[p_idx].success_lives.pop() {
                            state.players[p_idx].deck.push(cid);
                        }
                    }
                    _ => {
                        if let Some(cid) = state.players[p_idx].hand.pop() {
                            state.players[p_idx].deck.push(cid);
                        }
                    }
                }
            }
            let mut rng = Pcg64::from_os_rng();
            state.players[p_idx].deck.shuffle(&mut rng);
        }
        O_SWAP_CARDS => {
            for _ in 0..(v as usize) {
                if state.players[p_idx].deck.is_empty() {
                    state.resolve_deck_refresh(p_idx);
                }
                if let Some(cid) = state.players[p_idx].deck.pop() {
                    match resolved_slot {
                        7 => state.players[p_idx].discard.push(cid),
                        8 => state.players[p_idx].deck.push(cid),
                        6 => {
                            state.players[p_idx].hand.push(cid);
                            state.players[p_idx].hand_increased_this_turn = state.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        }
                        _ => state.players[p_idx].discard.push(cid),
                    }
                }
            }
        }
        O_REVEAL_UNTIL => {
            let mut found = false;
            let mut revealed_count = 0;
            while !found && !state.players[p_idx].deck.is_empty() {
                if revealed_count > 60 {
                    break;
                }
                if let Some(cid) = state.players[p_idx].deck.pop() {
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
                            state.players[p_idx].hand.push(cid);
                            state.players[p_idx].hand_increased_this_turn = state.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        } else if dest_slot == 7 {
                            state.players[p_idx].discard.push(cid);
                        }
                        found = true;
                    } else {
                        state.players[p_idx].discard.push(cid);
                    }
                }
            }
        }
        O_LOOK_DECK | O_REVEAL_CARDS | O_CHEER_REVEAL => {
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
                        return Some(HandlerResult::Suspend);
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
                            return Some(HandlerResult::Suspend);
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
                    if let Some(cid) = state.players[p_idx].deck.pop() {
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
        }
        O_LOOK_DECK_DYNAMIC => {
            let mut total_score = 0;
            if let Some(res) = state.ui.performance_results.get(&(p_idx as u8)) {
                total_score = res.get("total_score").and_then(|v| v.as_u64()).unwrap_or(0) as i32;
            } else if let Some(res) = state.ui.last_performance_results.get(&(p_idx as u8)) {
                total_score = res.get("total_score").and_then(|v| v.as_u64()).unwrap_or(0) as i32;
            }

            if total_score == 0 {
                total_score = (state.players[p_idx].score as i32)
                    + state.players[p_idx].live_score_bonus;
            }

            let count = (total_score + v) as usize;

            if count > 0 {
                if state.players[p_idx].deck.len() < count {
                    state.resolve_deck_refresh(p_idx);
                }
                let deck_len = state.players[p_idx].deck.len();
                for _ in 0..count.min(deck_len) {
                    if let Some(cid) = state.players[p_idx].deck.pop() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
        }
        O_MOVE_TO_DISCARD => {
            return match handle_move_to_discard(state, db, ctx, instr, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_LOOK_AND_CHOOSE => {
            return match handle_look_and_choose(state, db, ctx, instr, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_RECOVER_LIVE | O_RECOVER_MEMBER => {
            return match handle_recovery(state, db, ctx, instr, instr_ip, op) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_PLAY_LIVE_FROM_DISCARD => {
            return match handle_play_live_from_discard(state, db, ctx, instr, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_SELECT_CARDS => {
            return match handle_select_cards(state, db, ctx, instr, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_SWAP_ZONE => match handle_swap_zone(state, db, ctx, instr, instr_ip) {
            Some(_) => {}
            None => return Some(HandlerResult::Suspend),
        },
        _ => return None,
    }
    Some(HandlerResult::Continue)
}

pub fn handle_swap_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> Option<bool> {
    let _s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 && ctx.v_remaining == -1 {
        let cards = state.players[p_idx].success_lives.clone();
        if cards.is_empty() {
            return Some(true);
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
            return None;
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
                return None;
            }
        }
    } else if ctx.v_remaining == 0 {
        let hand_idx = ctx.choice_index as usize;
        if hand_idx < state.players[p_idx].hand.len()
            && !state.players[p_idx].looked_cards.is_empty()
        {
            let hand_cid = state.players[p_idx].hand.remove(hand_idx);
            let success_cid = state.players[p_idx].looked_cards.remove(0);
            if let Some(pos) = state.players[p_idx]
                .success_lives
                .iter()
                .position(|&x| x == success_cid)
            {
                state.players[p_idx].success_lives[pos] = hand_cid;
                state.players[p_idx].hand.push(success_cid);
                state.players[p_idx].hand_increased_this_turn = state.players[p_idx]
                    .hand_increased_this_turn
                    .saturating_add(1);
            }
        }
    }
    state.players[p_idx].looked_cards.clear();
    Some(true)
}
