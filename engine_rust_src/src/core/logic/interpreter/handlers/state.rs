use crate::core::enums::*;
use crate::core::logic::constants::{FILTER_MASK_LOWER, DYNAMIC_VALUE, CHOICE_DONE, FLAG_IS_WAIT, FLAG_EMPTY_SLOT_ONLY, FILTER_TOTAL_COST};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, TriggerType};
use crate::core::models::interpreter::{resolve_target_slot, get_choice_text};
use crate::core::models::suspend_interaction;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::logging;
use super::HandlerResult;

pub fn handle_energy(
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

    match op {
        O_ENERGY_CHARGE => {
            let target_p = if instr.s.target_slot == 2 { 1 - p_idx } else { p_idx };
            let is_wait = (s as u64 & FLAG_IS_WAIT) != 0;
            for _ in 0..v {
                if let Some(cid) = state.players[target_p].energy_deck.pop() {
                    state.players[target_p].energy_zone.push(cid);
                    let new_idx = state.players[target_p].energy_zone.len() - 1;
                    state.players[target_p].set_energy_tapped(new_idx, is_wait);
                }
            }
            Some(HandlerResult::Continue)
        }
        O_PAY_ENERGY => {
            let available = (0..state.players[p_idx].energy_zone.len())
                .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
                .count() as i32;

            let is_optional =
                (a as u64 & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0;
            if is_optional && ctx.choice_index == -1 {
                if available < v {
                    if state.debug.debug_mode {
                        println!("[DEBUG] O_PAY_ENERGY: cannot afford optional cost.");
                    }
                    return Some(HandlerResult::SetCond(false));
                } else {
                    if state.debug.debug_mode {
                        println!(
                            "[DEBUG] O_PAY_ENERGY: attempting optional suspension (instr_ip={}).",
                            instr_ip
                        );
                    }
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_PAY_ENERGY,
                        0,
                        ChoiceType::Optional,
                        "",
                        a as u64,
                        -1,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }

            if ctx.choice_index == 99 {
                return Some(HandlerResult::SetCond(false));
            }

            let mut next_ctx = ctx.clone();
            if is_optional && ctx.choice_index != -1 && ctx.v_remaining == -1 {
                if ctx.choice_index == 1 {
                    return Some(HandlerResult::SetCond(false));
                }
                next_ctx.choice_index = -1;
                next_ctx.v_remaining = v as i16;
            }

            if next_ctx.choice_index == 99 {
                return Some(HandlerResult::SetCond(false));
            } else if available < v {
                return Some(HandlerResult::SetCond(false));
            } else {
                if next_ctx.choice_index != -1 {
                    let idx = next_ctx.choice_index as usize;
                    if idx < state.players[p_idx].energy_zone.len()
                        && !state.players[p_idx].is_energy_tapped(idx)
                    {
                        state.players[p_idx].set_energy_tapped(idx, true);
                        next_ctx.v_remaining -= 1;
                        if next_ctx.v_remaining > 0 {
                            next_ctx.choice_index = -1;
                            if suspend_interaction(
                                state,
                                db,
                                &next_ctx,
                                instr_ip,
                                O_PAY_ENERGY,
                                0,
                                ChoiceType::PayEnergy,
                                "",
                                0,
                                next_ctx.v_remaining,
                            ) {
                                return Some(HandlerResult::Suspend);
                            }
                        }
                    }
                } else {
                    let mut paid = 0;
                    let player = &mut state.players[p_idx];
                    for i in 0..player.energy_zone.len() {
                        if paid >= v {
                            break;
                        }
                        if !player.is_energy_tapped(i) {
                            player.set_energy_tapped(i, true);
                            paid += 1;
                        }
                    }
                }
            }
            Some(HandlerResult::SetCond(true))
        }
        O_ACTIVATE_ENERGY => {
            let mut count = 0;
            let mut group_bits = 0u32;
            if let Some(card) = db.get_member(ctx.source_card_id) {
                if state.debug.debug_mode {
                    println!(
                        "[ENERGY_DEBUG] source_card_id={}, card_no={}, groups={:?}",
                        ctx.source_card_id, card.card_no, card.groups
                    );
                }
                for &g in &card.groups {
                    if g < 32 {
                        group_bits |= 1 << g;
                    }
                }
            } else {
                if state.debug.debug_mode {
                    println!(
                        "[ENERGY_DEBUG] card NOT FOUND for id={}",
                        ctx.source_card_id
                    );
                }
            }

            for i in 0..state.players[p_idx].energy_zone.len() {
                if count >= v {
                    break;
                }
                if state.players[p_idx].is_energy_tapped(i) {
                    state.players[p_idx].set_energy_tapped(i, false);
                    state.players[p_idx].activated_energy_group_mask |= group_bits;
                    count += 1;
                }
            }
            Some(HandlerResult::Continue)
        }
        O_PAY_ENERGY_DYNAMIC => {
            let base_score = state.players[p_idx].score as i32;
            let total_cost = (base_score + v) as usize;

            if state.debug.debug_mode {
                println!(
                    "[DEBUG] O_PAY_ENERGY_DYNAMIC: base_score={}, v={}, total_cost={}",
                    base_score, v, total_cost
                );
            }

            let available = (0..state.players[p_idx].energy_zone.len())
                .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
                .count();

            if available < total_cost {
                return Some(HandlerResult::SetCond(false));
            }

            let mut paid = 0;
            for i in 0..state.players[p_idx].energy_zone.len() {
                if paid >= total_cost {
                    break;
                }
                if !state.players[p_idx].is_energy_tapped(i) {
                    state.players[p_idx].set_energy_tapped(i, true);
                    paid += 1;
                }
            }
            Some(HandlerResult::SetCond(true))
        }
        O_PLACE_ENERGY_UNDER_MEMBER => {
            let src_zone = instr.s.source_zone as u8;
            let slot = if ctx.area_idx >= 0 {
                ctx.area_idx as usize
            } else {
                0
            };

            if slot < 3 {
                match src_zone {
                    7 => {
                        if let Some(cid) = state.players[p_idx].discard.pop() {
                            state.players[p_idx].stage_energy[slot].push(cid);
                        }
                    }
                    8 | 0 => {
                        if let Some(cid) = state.players[p_idx].deck.pop() {
                            state.players[p_idx].stage_energy[slot].push(cid);
                        }
                    }
                    _ => {
                        if !state.players[p_idx].energy_zone.is_empty() {
                            for i in 0..state.players[p_idx].energy_zone.len() {
                                if !state.players[p_idx].is_energy_tapped(i) {
                                    let energy_cid =
                                        state.players[p_idx].energy_zone.remove(i);
                                    state.players[p_idx].stage_energy[slot].push(energy_cid);
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            Some(HandlerResult::Continue)
        }
        _ => None,
    }
}

pub fn handle_member_state(
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
        O_ACTIVATE_MEMBER => {
            let mut group_bits = 0u32;
            if let Some(card) = db.get_member(ctx.source_card_id) {
                for &g in &card.groups {
                    if g < 32 {
                        group_bits |= 1 << g;
                    }
                }
            }

            if target_slot == 1 {
                for i in 0..3 {
                    if state.players[p_idx].is_tapped(i) {
                        state.players[p_idx].set_tapped(i, false);
                        state.players[p_idx].activated_member_group_mask |= group_bits;
                    }
                }
            } else if resolved_slot < 3 {
                if state.players[p_idx].is_tapped(resolved_slot as usize) {
                    state.players[p_idx].set_tapped(resolved_slot as usize, false);
                    state.players[p_idx].activated_member_group_mask |= group_bits;
                }
            }
        }
        O_SET_TAPPED => {
            if resolved_slot < 3 {
                state.players[p_idx].set_tapped(resolved_slot as usize, v != 0);
            }
        }
        O_TAP_MEMBER => {
            let resolved_slot = resolve_target_slot(target_slot, ctx);
            let _target_p_idx = if instr.s.is_opponent() { 1 - ctx.player_id } else { ctx.player_id };

            if v == 0 && resolved_slot == 4 && a & 0x02 == 0 {
                if a & 0x01 != 0 || a & 0x80 != 0 {
                    let mod_a = a | 0x02;
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_TAP_MEMBER,
                        0,
                        ChoiceType::TapMSelect,
                        &choice_text,
                        mod_a as u64,
                        v as i16,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }

            let is_optional =
                (a as u64 & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0;
            if ctx.choice_index == -1 {
                if is_optional || (a & 0x01) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_TAP_MEMBER,
                        0,
                        ChoiceType::Optional,
                        &choice_text,
                        a as u64,
                        -1,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                if (a & 0x02) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_TAP_MEMBER,
                        0,
                        ChoiceType::TapMSelect,
                        &choice_text,
                        a as u64,
                        v as i16,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                if (a & 0x03) == 0 && resolved_slot < 3 {
                    state.players[p_idx].set_tapped(resolved_slot as usize, true);
                }
            } else {
                let is_choice_done = ctx.choice_index == CHOICE_DONE;
                if is_optional || (a & 0x01) != 0 {
                    if is_choice_done || ctx.choice_index == 1 {
                        return Some(HandlerResult::SetCond(false));
                    }
                    if resolved_slot < 3 {
                        state.players[p_idx].set_tapped(resolved_slot as usize, true);
                    }
                    return Some(HandlerResult::SetCond(true));
                } else {
                    let slot = ctx.choice_index as usize;
                    if slot < 3 {
                        state.players[p_idx].set_tapped(slot, true);
                    }
                    return Some(HandlerResult::SetCond(true));
                }
            }
        }
        O_TAP_OPPONENT => {
            let target_p_idx = 1 - (ctx.activator_id as usize);
            let count = if ctx.v_remaining == -1 {
                v as i16
            } else {
                ctx.v_remaining
            };
            if count <= 0 {
                return Some(HandlerResult::Continue);
            }

            if ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                if state.debug.debug_mode {
                    println!("[DEBUG] O_TAP_OPPONENT: Suspending for opponent.");
                }

                let suspended = suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_TAP_OPPONENT,
                    0,
                    ChoiceType::TapO,
                    &choice_text,
                    a as u64,
                    count,
                );

                if suspended {
                    return Some(HandlerResult::Suspend);
                }
            } else {
                let slot_idx = ctx.choice_index as usize;
                if slot_idx < 3 {
                    state.players[target_p_idx].set_tapped(slot_idx, true);
                    ctx.v_remaining = count - 1;
                    ctx.choice_index = -1;
                    if ctx.v_remaining > 0 {
                        let choice_text = get_choice_text(db, ctx);
                        let suspended = suspend_interaction(
                            state,
                            db,
                            ctx,
                            instr_ip,
                            O_TAP_OPPONENT,
                            0,
                            ChoiceType::TapO,
                            &choice_text,
                            a as u64,
                            ctx.v_remaining,
                        );

                        if suspended {
                            return Some(HandlerResult::Suspend);
                        }
                    }
                }
            }
        }
        O_MOVE_MEMBER | O_FORMATION_CHANGE => {
            let src_slot = if op == O_FORMATION_CHANGE && target_slot == 4 {
                ctx.area_idx as usize
            } else if op == O_MOVE_MEMBER && ctx.area_idx >= 0 {
                ctx.area_idx as usize
            } else {
                resolved_slot as usize
            };

            if op == O_MOVE_MEMBER && a == 99 && ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_MOVE_MEMBER,
                    s,
                    ChoiceType::MoveMemberDest,
                    &choice_text,
                    0,
                    -1,
                ) {
                    return Some(HandlerResult::Suspend);
                }
            }

            let dst_slot = if op == O_MOVE_MEMBER && a == 99 && ctx.choice_index != -1 {
                let slot = ctx.choice_index as usize;
                ctx.choice_index = -1;
                slot
            } else if ctx.target_slot != -1 && a != 99 {
                ctx.target_slot as usize
            } else {
                a as usize
            };
            if src_slot < 3 && dst_slot < 3 && src_slot != dst_slot {
                state.players[p_idx].swap_slot_data(src_slot, dst_slot);
                for &slot in &[src_slot, dst_slot] {
                    let cid = state.players[p_idx].stage[slot];
                    if cid >= 0 {
                        let mut pos_ctx = ctx.clone();
                        pos_ctx.source_card_id = cid;
                        pos_ctx.area_idx = slot as i16;
                        state.trigger_abilities(db, TriggerType::OnPositionChange, &pos_ctx);
                    }
                }
            }
        }
        O_PLACE_UNDER => {
            let slot = if ctx.target_slot != -1 {
                ctx.target_slot as usize
            } else {
                resolved_slot as usize
            };
            if slot < 3 {
                if a == 0 && !state.players[p_idx].hand.is_empty() {
                    let hand_idx = if ctx.choice_index != -1 {
                        ctx.choice_index as usize
                    } else {
                        state.players[p_idx].hand.len() - 1
                    };
                    if hand_idx < state.players[p_idx].hand.len() {
                        let cid = state.players[p_idx].hand.remove(hand_idx);
                        state.players[p_idx].stage_energy[slot].push(cid);
                    }
                } else if a == 1 {
                    if let Some(cid) = state.players[p_idx].energy_zone.pop() {
                        state.players[p_idx].stage_energy[slot].push(cid);
                    }
                }
                state.players[p_idx].stage_energy_count[slot] =
                    state.players[p_idx].stage_energy[slot].len() as u8;
            }
        }
        O_ADD_STAGE_ENERGY => {
            if resolved_slot < 3 {
                for _ in 0..v {
                    state.players[p_idx].stage_energy[resolved_slot as usize].push(2000);
                }
                state.players[p_idx].sync_stage_energy_count(resolved_slot as usize);
            }
        }
        O_GRANT_ABILITY => {
            let ab_idx = v as u16;
            let source_cid = ctx.source_card_id;
            let mut targets = smallvec::SmallVec::<[i32; 3]>::new();
            if target_slot == 4 && resolved_slot < 3 {
                let cid = state.players[p_idx].stage[resolved_slot as usize];
                if cid >= 0 {
                    targets.push(cid);
                }
            } else if target_slot == 1 {
                for i in 0..3 {
                    let cid = state.players[p_idx].stage[i];
                    if cid >= 0 {
                        targets.push(cid);
                    }
                }
            } else if target_slot >= 0 && target_slot < 3 {
                let cid = state.players[p_idx].stage[target_slot as usize];
                if cid >= 0 {
                    targets.push(cid);
                }
            }

            for t_cid in targets {
                state.players[p_idx]
                    .granted_abilities
                    .push((t_cid, source_cid, ab_idx));
            }
        }
        O_PLAY_MEMBER_FROM_HAND => {
            let remaining = if ctx.v_remaining == -1 {
                if v == 1 { 1 } else { 2 }
            } else {
                ctx.v_remaining
            };

            if remaining == 2 {
                if ctx.choice_index == -1 {
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_HAND,
                        0,
                        ChoiceType::SelectHandPlay,
                        "",
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                let h_idx = ctx.choice_index as usize;
                if h_idx < state.players[p_idx].hand.len() {
                    ctx.target_slot = h_idx as i16;
                    ctx.v_remaining = 1;
                    ctx.choice_index = -1;
                    return handle_member_state(state, db, ctx, instr, instr_ip);
                }
            } else if remaining == 1 {
                if ctx.choice_index == -1 {
                    let mut next_ctx = ctx.clone();
                    next_ctx.player_id = p_idx as u8;
                    if suspend_interaction(
                        state,
                        db,
                        &next_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_HAND,
                        s,
                        ChoiceType::SelectStage,
                        "",
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let slot_idx = ctx.choice_index as usize;
                if slot_idx < 3 {
                    let h_idx = ctx.target_slot as usize;
                    if h_idx < state.players[p_idx].hand.len() {
                        let cid = state.players[p_idx].hand.remove(h_idx);
                        if let Some(old) =
                            state.handle_member_leaves_stage(p_idx, slot_idx, db, ctx)
                        {
                            state.players[p_idx].discard.push(old);
                        }
                        state.players[p_idx].stage[slot_idx] = cid;
                        state.players[p_idx].set_tapped(slot_idx, false);
                        state.players[p_idx].set_moved(slot_idx, true);
                        state.register_played_member(p_idx, cid, db);

                        let new_ctx = AbilityContext {
                            source_card_id: cid,
                            player_id: p_idx as u8,
                            activator_id: p_idx as u8,
                            area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        ctx.choice_index = -1;
                        ctx.v_remaining = 0;
                        return Some(HandlerResult::Continue);
                    }
                }
            }
        }
        O_PLAY_MEMBER_FROM_DISCARD => {
            let opponent_bit = (s >> 24) & 1;
            let target_p_idx = if opponent_bit != 0 {
                1 - (ctx.activator_id as usize)
            } else {
                ctx.activator_id as usize
            };
            let empty_slot_only = ((s as u64) & FLAG_EMPTY_SLOT_ONLY) != 0;

            let filter_attr_base = a as u64;
            let is_total_cost = (filter_attr_base & FILTER_TOTAL_COST) != 0;

            let mut remaining = if ctx.v_remaining == -1 {
                if is_total_cost {
                    ctx.v_accumulated = ((filter_attr_base
                        >> crate::core::generated_constants::FILTER_COST_SHIFT)
                        & 0x1F) as i16;
                }
                v as i16 * 2
            } else {
                ctx.v_remaining
            };
            if remaining <= 0 {
                return Some(HandlerResult::Continue);
            }

            if remaining % 2 == 0 {
                if empty_slot_only
                    && state.players[target_p_idx]
                        .stage
                        .iter()
                        .all(|&c| c >= 0)
                {
                    return Some(HandlerResult::Continue);
                }

                if state.players[target_p_idx].looked_cards.is_empty() {
                    let mut filter_attr = filter_attr_base;
                    if is_total_cost {
                        filter_attr = (filter_attr
                            & !(0x1F << crate::core::generated_constants::FILTER_COST_SHIFT))
                            | ((ctx.v_accumulated as u64)
                                << crate::core::generated_constants::FILTER_COST_SHIFT);
                    }
                    let matched_ids: Vec<i32> = state.players[target_p_idx].discard.iter()
                        .filter(|&&cid| db.get_member(cid).is_some() && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)))
                        .cloned()
                        .collect();
                    state.players[target_p_idx].looked_cards.extend(matched_ids);
                    if state.players[target_p_idx].looked_cards.is_empty() {
                        return Some(HandlerResult::Continue);
                    }

                    ctx.choice_index = -1;
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    let choice_text = get_choice_text(db, &target_ctx);
                    if suspend_interaction(
                        state,
                        db,
                        &target_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_DISCARD,
                        s,
                        ChoiceType::SelectDiscardPlay,
                        &choice_text,
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let idx = ctx.choice_index as usize;
                let cards_len = state.players[target_p_idx].looked_cards.len();

                if idx < cards_len {
                    let cid = state.players[target_p_idx].looked_cards[idx];
                    state.players[target_p_idx].looked_cards.clear();
                    state.players[target_p_idx].looked_cards.push(cid);

                    remaining -= 1;
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    let choice_type = if empty_slot_only {
                        ChoiceType::SelectStageEmpty
                    } else {
                        ChoiceType::SelectStage
                    };
                    if suspend_interaction(
                        state,
                        db,
                        &target_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_DISCARD,
                        s,
                        choice_type,
                        "",
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            } else {
                if state.players[target_p_idx].looked_cards.is_empty() {
                    return Some(HandlerResult::Continue);
                }
                let card_id = state.players[target_p_idx].looked_cards.remove(0);

                if ctx.choice_index == 99 {
                    return Some(HandlerResult::Continue);
                }

                if let Some(pos) = state.players[target_p_idx]
                    .discard
                    .iter()
                    .position(|&cid| cid == card_id)
                {
                    let slot_idx = if ctx.choice_index >= 0 && ctx.choice_index < 3 {
                        ctx.choice_index as usize
                    } else {
                        resolved_slot as usize
                    };

                    if slot_idx < 3 {
                        if (state.players[target_p_idx].prevent_play_to_slot_mask
                            & (1 << slot_idx))
                            != 0
                            || (empty_slot_only
                                && state.players[target_p_idx].stage[slot_idx] != -1)
                        {
                            return Some(HandlerResult::Continue);
                        }

                        if is_total_cost {
                            if let Some(m) = db.get_member(card_id) {
                                ctx.v_accumulated = (ctx.v_accumulated - m.cost as i16).max(0);
                            }
                        }

                        state.players[target_p_idx].discard.remove(pos);

                        if let Some(old) =
                            state.handle_member_leaves_stage(target_p_idx, slot_idx, db, ctx)
                        {
                            state.players[target_p_idx].discard.push(old);
                        }
                        state.players[target_p_idx].stage[slot_idx] = card_id;
                        state.players[target_p_idx].set_tapped(slot_idx, true);
                        state.players[target_p_idx].set_moved(slot_idx, true);
                        state.register_played_member(target_p_idx, card_id, db);
                        state.players[target_p_idx].prevent_play_to_slot_mask |= 1 << slot_idx;

                        let mut new_ctx = AbilityContext {
                            source_card_id: card_id,
                            player_id: target_p_idx as u8,
                            activator_id: target_p_idx as u8,
                            area_idx: slot_idx as i16,
                            v_accumulated: ctx.v_accumulated,
                            ..Default::default()
                        };
                        new_ctx.v_remaining = ctx.v_remaining;
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                    }
                }

                remaining -= 1;
                if remaining > 0 {
                    let mut filter_attr = filter_attr_base;
                    if is_total_cost {
                        filter_attr = (filter_attr
                            & !(0x1F << crate::core::generated_constants::FILTER_COST_SHIFT))
                            | ((ctx.v_accumulated as u64)
                                << crate::core::generated_constants::FILTER_COST_SHIFT);
                    }
                    state.players[target_p_idx].looked_cards.clear();
                    let matched_ids: Vec<i32> = state.players[target_p_idx].discard.iter()
                        .filter(|&&cid| db.get_member(cid).is_some() && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)))
                        .cloned()
                        .collect();
                    state.players[target_p_idx].looked_cards.extend(matched_ids);
                    if state.players[target_p_idx].looked_cards.is_empty() {
                        return Some(HandlerResult::Continue);
                    }
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    target_ctx.choice_index = -1;
                    let choice_text = get_choice_text(db, &target_ctx);
                    if suspend_interaction(
                        state,
                        db,
                        &target_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_DISCARD,
                        s,
                        ChoiceType::SelectDiscardPlay,
                        &choice_text,
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }
        }
        O_INCREASE_COST => {
            state.players[p_idx].cost_modifiers.push((
                crate::core::logic::Condition {
                    condition_type: ConditionType::None,
                    value: 0,
                    attr: 0,
                    target_slot: 0,
                    is_negated: false,
                    params: serde_json::Value::Null,
                },
                v,
            ));
        }
        _ => return None,
    }
    Some(HandlerResult::Continue)
}

pub fn handle_score_hearts(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
) -> Option<HandlerResult> {
    let op = instr.op;
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;

    let target_p = if instr.s.is_opponent() { 1 - p_idx } else { p_idx };
    let target_slot = instr.s.target_slot as i32;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_BOOST_SCORE => {
            let mut final_v = v;
            if (a as u64 & DYNAMIC_VALUE) != 0 {
                let count = resolve_count(
                    state,
                    db,
                    s,
                    a as u64 & !DYNAMIC_VALUE & FILTER_MASK_LOWER,
                    0,
                    ctx,
                    0,
                );
                final_v = v * count;
            }
            state.players[target_p].live_score_bonus += final_v;
            state.players[target_p]
                .live_score_bonus_logs
                .push((ctx.source_card_id, final_v));
            if !state.ui.silent {
                if let Some(msg) = logging::get_opcode_log(O_BOOST_SCORE, final_v, a, s, 0) {
                    state.log(msg);
                }
            }
        }
        O_REDUCE_COST => state.players[p_idx].cost_reduction += v as i16,
        O_SET_SCORE => state.players[p_idx].score = v as u32,
        O_ADD_BLADES | O_BUFF_POWER => {
            if target_slot == 1 {
                for t in 0..3 {
                    state.players[p_idx].blade_buffs[t] += v as i16;
                    state.players[p_idx].blade_buff_logs.push((
                        ctx.source_card_id,
                        v as i16,
                        t as u8,
                    ));
                }
            } else if resolved_slot < 3 {
                state.players[p_idx].blade_buffs[resolved_slot as usize] += v as i16;
                state.players[p_idx].blade_buff_logs.push((
                    ctx.source_card_id,
                    v as i16,
                    resolved_slot as u8,
                ));
            }
            state.log_event(
                "EFFECT",
                &format!("+{} Appeal", v),
                ctx.source_card_id,
                ctx.ability_index,
                p_idx as u8,
                None,
                true,
            );
        }
        O_SET_BLADES => {
            if target_slot == 4 && ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                state.players[p_idx].blade_buffs[ctx.area_idx as usize] = v as i16;
            }
        }
        O_ADD_HEARTS => {
            let mut color = (a as u64 & FILTER_MASK_LOWER) as usize;
            if color == 0 {
                color = ctx.selected_color as usize;
            }
            if color < 7 {
                if (target_slot == 4 || target_slot == 0) && ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    state.players[p_idx].heart_buffs[ctx.area_idx as usize]
                        .add_to_color(color, v as i32);
                    state.players[p_idx].heart_buff_logs.push((
                        ctx.source_card_id,
                        v,
                        color as u8,
                        ctx.area_idx as u8,
                    ));
                } else if target_slot == 1 {
                    for t in 0..3 {
                        state.players[p_idx].heart_buffs[t].add_to_color(color, v as i32);
                        state.players[p_idx].heart_buff_logs.push((
                            ctx.source_card_id,
                            v,
                            color as u8,
                            t as u8,
                        ));
                    }
                }
            }
            if !state.ui.silent {
                if let Some(msg) = logging::get_opcode_log(O_ADD_HEARTS, v, a, s, 0) {
                    state.log(msg);
                }
            }
            state.log_event(
                "EFFECT",
                &format!("+{} Heart(s)", v),
                ctx.source_card_id,
                ctx.ability_index,
                p_idx as u8,
                None,
                true,
            );
        }
        O_SET_HEARTS => {
            if (a as usize) < 7 {
                let targets = if target_slot == 4 && ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    vec![ctx.area_idx as usize]
                } else if target_slot == 1 {
                    vec![0, 1, 2]
                } else {
                    vec![]
                };
                for t in targets {
                    state.players[p_idx].heart_buffs[t].set_color_count(a as usize, v as u8);
                }
            }
        }
        O_TRANSFORM_COLOR => {
            state.players[p_idx]
                .color_transforms
                .push((ctx.source_card_id, 0, v as u8));
        }
        O_REDUCE_HEART_REQ => {
            if (s as usize) < 7 {
                state.players[p_idx]
                    .heart_req_reductions
                    .add_to_color(s as usize, v);
                state.players[p_idx].heart_req_reduction_logs.push((
                    ctx.source_card_id,
                    s as u8,
                    v as u8,
                ));
            }
        }
        O_TRANSFORM_HEART => {
            let src = a as usize;
            let dst = s as usize;
            if src < 7 && dst < 7 {
                let amt = v.abs();
                if state.players[p_idx]
                    .heart_req_reductions
                    .get_color_count(src)
                    >= amt as u8
                {
                    state.players[p_idx]
                        .heart_req_reductions
                        .add_to_color(src, -(amt as i32));
                    state.players[p_idx]
                        .heart_req_reductions
                        .add_to_color(dst, amt as i32);
                }
            }
        }
        O_INCREASE_HEART_COST => {
            if (s as usize) < 7 {
                state.players[p_idx]
                    .heart_req_additions
                    .add_to_color(s as usize, v);
                state.players[p_idx].heart_req_addition_logs.push((
                    ctx.source_card_id,
                    s as u8,
                    v as u8,
                ));
            }
        }
        O_SET_HEART_COST => {
            let player = &mut state.players[p_idx];
            if v > 15 || s == -1 {
                for i in 0..7 {
                    let count = ((v >> (i * 4)) & 0xF) as u8;
                    if count > 0 {
                        let old = player.heart_req_additions.get_color_count(i);
                        player.heart_req_additions.set_color_count(i, old.saturating_add(count));
                        player
                            .heart_req_addition_logs
                            .push((ctx.source_card_id, i as u8, count));
                    }
                }
            } else if (s as usize) < 7 {
                player
                    .heart_req_additions
                    .set_color_count(s as usize, v as u8);
                player
                    .heart_req_addition_logs
                    .push((ctx.source_card_id, s as u8, v as u8));
            }
        }
        O_REDUCE_SCORE => {
            let reduction = v.min(state.players[target_p].live_score_bonus);
            state.players[target_p].live_score_bonus -= reduction;
        }
        O_LOSE_EXCESS_HEARTS => {
            let player = &mut state.players[p_idx];
            let reduction = if v == 0 {
                player.excess_hearts
            } else {
                v as u32
            };
            player.excess_hearts = player.excess_hearts.saturating_sub(reduction);
        }
        O_SKIP_ACTIVATE_PHASE => {
            state.players[p_idx].skip_next_activate = true;
        }
        _ => return None,
    }
    Some(HandlerResult::Continue)
}
