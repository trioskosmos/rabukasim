use crate::core::enums::*;
use crate::core::logic::constants::{CHOICE_DONE, CHOICE_ALL, FILTER_IS_OPTIONAL};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, TriggerType};
use crate::core::models::interpreter::{get_choice_text, HandlerResult};
use crate::core::models::suspend_interaction;
use crate::core::generated_layout::*;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;


pub fn handle_play_live_from_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let target_p_idx = if instr.s.is_opponent {
        1 - (ctx.activator_id as usize)
    } else {
        ctx.activator_id as usize
    };

    let mut remaining = if ctx.v_remaining == -1 {
        v as i16 * 2
    } else {
        ctx.v_remaining
    };
    if remaining <= 0 {
        return HandlerResult::Continue;
    }

    if remaining % 2 == 0 {
        if ctx.choice_index == -1 {
            state.players[target_p_idx].looked_cards.clear();
            let filter_attr = a as u64;
            let matched_ids: Vec<i32> = state.players[target_p_idx].discard.iter()
                .filter(|&&cid| db.get_live(cid).is_some() && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)))
                .cloned()
                .collect();
            state.players[target_p_idx].looked_cards.extend(matched_ids);
            if state.players[target_p_idx].looked_cards.is_empty() {
                return HandlerResult::Continue;
            }
            let mut target_ctx = ctx.clone();
            target_ctx.player_id = target_p_idx as u8;
            let choice_text = get_choice_text(db, &target_ctx);
            if suspend_interaction(
                state,
                db,
                &target_ctx,
                instr_ip,
                O_PLAY_LIVE_FROM_DISCARD,
                s,
                ChoiceType::SelectDiscardPlay,
                &choice_text,
                a as u64,
                remaining,
            ) {
                return HandlerResult::Suspend;
            }
        }

        let choice = ctx.choice_index as i32;
        let real_idx = if choice >= 0
            && (choice as usize) < state.players[target_p_idx].looked_cards.len()
        {
            Some(choice as usize)
        } else {
            None
        };

        if let Some(idx) = real_idx {
            let chosen = state.players[target_p_idx].looked_cards[idx];
            if chosen != -1 {
                state.players[target_p_idx].looked_cards[idx] = -1;
                state.players[target_p_idx].looked_cards.clear();
                state.players[target_p_idx].looked_cards.push(chosen);

                remaining -= 1;
                let mut target_ctx = ctx.clone();
                target_ctx.player_id = target_p_idx as u8;
                if suspend_interaction(
                    state,
                    db,
                    &target_ctx,
                    instr_ip,
                    O_PLAY_LIVE_FROM_DISCARD,
                    s,
                    ChoiceType::SelectLiveSlot,
                    "",
                    a as u64,
                    remaining,
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    } else {
        if state.players[target_p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }
        let card_id = state.players[target_p_idx].looked_cards.remove(0);
        let slot_idx = ctx.choice_index as usize;

        if let Some(pos) = state.players[target_p_idx]
            .discard
            .iter()
            .position(|&cid| cid == card_id)
        {
            state.players[target_p_idx].discard.remove(pos);
            if slot_idx < 3 {
                let old = state.players[target_p_idx].live_zone[slot_idx];
                if old >= 0 {
                    state.players[target_p_idx].discard.push(old);
                }
                state.players[target_p_idx].live_zone[slot_idx] = card_id;
                state.players[target_p_idx].set_revealed(slot_idx, true);
            }
        }

        remaining -= 1;
        if remaining > 0 && !state.players[target_p_idx].discard.is_empty() {
            ctx.choice_index = -1;
            ctx.v_remaining = remaining;
            return handle_play_live_from_discard(state, db, ctx, instr, instr_ip);
        }
    }
    HandlerResult::Continue
}

pub fn handle_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 {
        let source_zone = instr.s.source_zone as u8;
        let ts = instr.s.target_slot;
        let effective_zone = if source_zone != 0 {
            source_zone
        } else if ts != 0 {
            ts
        } else {
            7
        };

        state.players[p_idx].looked_cards.clear();
        let cards_to_filter = match effective_zone {
            6 => state.players[p_idx].hand.to_vec(),
            7 => state.players[p_idx].discard.to_vec(),
            4 => state.players[p_idx]
                .stage
                .iter()
                .cloned()
                .filter(|&c| c >= 0)
                .collect(),
            _ => state.players[p_idx].discard.to_vec(),
        };

        let filter_attr = (a as u64) & 0x00000000FFFFFFFF;
        for cid in cards_to_filter {
            if state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
                state.players[p_idx].looked_cards.push(cid);
            }
        }

        if state.players[p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }

        let choice_type = match effective_zone {
            6 => ChoiceType::SelectHandDiscard,
            7 => ChoiceType::SelectDiscardPlay,
            _ => ChoiceType::LookAndChoose,
        };
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_SELECT_CARDS,
            0,
            choice_type,
            &choice_text,
            a as u64,
            v as i16,
        ) {
            return HandlerResult::Suspend;
        }
    }

    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 && (a as u64 & FILTER_IS_OPTIONAL) != 0 {
        return HandlerResult::Continue;
    }

    if choice != CHOICE_DONE as i32
        && choice >= 0
        && (choice as usize) < state.players[p_idx].looked_cards.len()
    {
        let chosen = state.players[p_idx].looked_cards[choice as usize];
        ctx.selected_cards.push(chosen);

        let dest_zone = instr.s.dest_zone as u8;
        if dest_zone != 0 {
            let source_zone = instr.s.source_zone as u8;
            let actual_source = if source_zone != 0 { source_zone } else { 7 };

            let mut found = false;
            match actual_source {
                6 => {
                    if let Some(pos) = state.players[p_idx]
                        .hand
                        .iter()
                        .position(|&c| c == chosen)
                    {
                        state.players[p_idx].hand.remove(pos);
                        found = true;
                    }
                }
                7 => {
                    if let Some(pos) = state.players[p_idx]
                        .discard
                        .iter()
                        .position(|&c| c == chosen)
                    {
                        state.players[p_idx].discard.remove(pos);
                        found = true;
                    }
                }
                4 => {
                    for i in 0..3 {
                        if state.players[p_idx].stage[i] == chosen {
                            state.handle_member_leaves_stage(p_idx, i, db, ctx);
                            found = true;
                            break;
                        }
                    }
                }
                _ => {}
            }

            if found {
                match dest_zone {
                    6 => {
                        state.players[p_idx].hand.push(chosen);
                        state.players[p_idx].hand_increased_this_turn = state.players
                            [p_idx]
                            .hand_increased_this_turn
                            .saturating_add(1);
                    }
                    7 => {
                        state.players[p_idx].discard.push(chosen);
                    }
                    8 | 0 => {
                        state.players[p_idx].deck.push(chosen);
                    }
                    13 => {
                        state.players[p_idx].success_lives.push(chosen);
                    }
                    _ => {
                        state.players[p_idx].hand.push(chosen);
                    }
                }
            }
        }

        let rem = if ctx.v_remaining > 0 {
            ctx.v_remaining - 1
        } else {
            (v as i16).saturating_sub(1)
        };
        if rem > 0 {
            state.players[p_idx]
                .looked_cards
                .remove(choice as usize);
            ctx.v_remaining = rem;
            ctx.choice_index = -1;
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                s,
                ChoiceType::LookAndChoose,
                "",
                a as u64,
                rem,
            ) {
                return HandlerResult::Suspend;
            }
        }
    }

    HandlerResult::Continue
}

pub fn handle_look_and_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let target_slot = instr.s.target_slot;
    let rem_dest = instr.s.dest_zone as u8;
    let source_zone_bits = instr.s.source_zone as u8;
    let source_zone = if source_zone_bits == 0 {
        8
    } else {
        source_zone_bits as i32
    };
    // --- New Layout Unpacking (V Layout: count=0-7, char_id_1=16-22, char_id_2=8-14, char_id_3=23-29, reveal=30, dest_discard=31) ---
    let (look_count, char_id_1, char_id_2, char_id_3, reveal_flag, dest_discard_v) = {
        let v_u32 = v as u32;
        let count = ((v_u32 >> V_LOOK_CHOOSE_COUNT_SHIFT) & V_LOOK_CHOOSE_COUNT_MASK) as usize;
        let char1 = ((v_u32 >> V_LOOK_CHOOSE_CHAR_ID_1_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_1_MASK) as u8;
        let char2 = ((v_u32 >> V_LOOK_CHOOSE_CHAR_ID_2_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_2_MASK) as u8;
        let char3 = ((v_u32 >> V_LOOK_CHOOSE_CHAR_ID_3_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_3_MASK) as u8;
        let reveal = ((v_u32 >> V_LOOK_CHOOSE_REVEAL_SHIFT) & V_LOOK_CHOOSE_REVEAL_MASK) != 0;
        let dest_d = ((v_u32 >> V_LOOK_CHOOSE_DEST_DISCARD_SHIFT) & V_LOOK_CHOOSE_DEST_DISCARD_MASK) != 0;
        (count, char1, char2, char3, reveal, dest_d)
    };

    if state.players[p_idx].looked_cards.is_empty() {
        let reveal_count = if source_zone == 6 {
            state.players[p_idx].hand.len()
        } else if source_zone == 7 {
            state.players[p_idx].discard.len()
        } else if source_zone == 15 {
            state.players[p_idx].yell_cards.len()
        } else {
            look_count
        };
        match source_zone {
            6 => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.players[p_idx].hand.pop() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            7 => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.players[p_idx].discard.pop() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            15 => {
                let y = std::mem::take(&mut state.players[p_idx].yell_cards);
                state.players[p_idx].looked_cards.extend(y);
            }
            _ => {
                if state.players[p_idx].deck.len() < reveal_count {
                    state.resolve_deck_refresh(p_idx);
                }
                for _ in 0..reveal_count.min(state.players[p_idx].deck.len()) {
                    if let Some(cid) = state.players[p_idx].deck.pop() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
        }
    }

    if ctx.choice_index == -1 {
        let choice_type = if source_zone == 6 {
            ChoiceType::SelectHandDiscard
        } else {
            ChoiceType::LookAndChoose
        };
        let choice_text = get_choice_text(db, ctx);
        
        let mut filter = crate::core::logic::filter::CardFilter::from_attr(a);
        filter.char_id_1 = char_id_1;
        filter.char_id_2 = char_id_2;
        filter.char_id_3 = char_id_3;
        
        let final_attr = filter.to_attr();
        let pick_count = 1;

        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_LOOK_AND_CHOOSE,
            s,
            choice_type,
            &choice_text,
            final_attr as u64,
            pick_count,
        ) {
            let is_optional = ((a as u64 >> A_STANDARD_IS_OPTIONAL_SHIFT) & A_STANDARD_IS_OPTIONAL_MASK) != 0;
            if is_optional && ctx.choice_index == CHOICE_DONE {
                let cards: Vec<i32> = state.players[p_idx].looked_cards.drain(..).collect();
                // Return cards to deck
                state.players[p_idx].deck.extend(cards.into_iter().rev());
                return HandlerResult::Continue;
            }
            return HandlerResult::Suspend;
        }
    }

    let choice = ctx.choice_index as i32;
    let mut revealed = std::mem::take(&mut state.players[p_idx].looked_cards);
    if choice == CHOICE_DONE as i32 {
        state.players[p_idx].looked_cards.retain(|c| *c != -1);
        return HandlerResult::Continue;
    }

    if choice != CHOICE_DONE as i32 {
        if choice >= 0 && (choice as usize) < revealed.len() && choice != CHOICE_ALL as i32 {
            let chosen = revealed[choice as usize];
            if chosen != -1 {
                revealed[choice as usize] = -1;
                let destination = if target_slot > 0 {
                    target_slot as i32
                } else {
                    6
                };
                match destination {
                    7 => {
                        state.players[p_idx].discard.push(chosen);
                    }
                    8 => {
                        state.players[p_idx].deck.push(chosen);
                    }
                    4 => {
                        let slot = (s as u32 & S_STANDARD_TARGET_SLOT_MASK) as usize;
                        if slot < 3 {
                            if let Some(cid) =
                                state.handle_member_leaves_stage(p_idx, slot, db, ctx)
                            {
                                state.players[p_idx].discard.push(cid as i32);
                            }
                            state.players[p_idx].stage[slot] = chosen;
                            state.players[p_idx].set_tapped(slot, false);
                            state.players[p_idx].set_moved(slot, true);
                            state.register_played_member(p_idx, chosen, db);
                            let new_ctx = AbilityContext {
                                source_card_id: chosen,
                                player_id: p_idx as u8,
                                activator_id: p_idx as u8,
                                area_idx: slot as i16,
                                ..Default::default()
                            };
                            state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        } else {
                            state.players[p_idx].hand.push(chosen);
                            state.players[p_idx].hand_increased_this_turn = state.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        }
                    }
                    13 => {
                        state.players[p_idx].success_lives.push(chosen);
                    }
                    _ => {
                        state.players[p_idx].hand.push(chosen);
                    }
                }
                if reveal_flag {
                    let new_ctx = AbilityContext {
                        source_card_id: chosen,
                        player_id: p_idx as u8,
                        activator_id: p_idx as u8,
                        ..Default::default()
                    };
                    state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
                }
                if source_zone == 15 {
                    for slot in 0..3 {
                        if let Some(pos) = state.players[p_idx].stage_energy[slot]
                            .iter()
                            .position(|&c| c == chosen)
                        {
                            state.players[p_idx].stage_energy[slot].remove(pos);
                            state.players[p_idx].sync_stage_energy_count(slot);
                            break;
                        }
                    }
                }
                
                // --- Multi-pick loop ---
                let rem = if ctx.v_remaining > 0 {
                    ctx.v_remaining - 1
                } else {
                    0
                };
                if rem > 0 && revealed.iter().any(|&c| c != -1) {
                    state.players[p_idx].looked_cards = revealed.clone();
                    let choice_type = if source_zone == 6 {
                        ChoiceType::SelectHandDiscard
                    } else {
                        ChoiceType::LookAndChoose
                    };
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_LOOK_AND_CHOOSE,
                        s,
                        choice_type,
                        "",
                        a as u64,
                        rem,
                    ) {
                        return HandlerResult::Suspend;
                    }
                }
            }
        }
    }
    revealed.retain(|c| *c != -1);
    if !revealed.is_empty() {
        let dest_bits = dest_discard_v;
        let dest = if dest_bits {
            7
        } else if rem_dest > 0 {
            rem_dest as i32
        } else {
            source_zone_bits as i32
        };
        match dest {
            6 => state.players[p_idx].hand.extend(revealed),
            7 => state.players[p_idx].discard.extend(revealed),
            15 => state.players[p_idx].yell_cards.extend(revealed),
            0 | 8 => {
                state.players[p_idx].deck.extend(revealed);
                let mut rng = Pcg64::from_os_rng();
                state.players[p_idx].deck.shuffle(&mut rng);
            }
            _ => state.players[p_idx].discard.extend(revealed),
        }
    }
    HandlerResult::Continue
}

pub fn handle_recovery(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
    real_op: i32,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let _s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let mut source_zone = instr.s.source_zone;
    if source_zone == Zone::Default {
        source_zone = Zone::Discard;
    }

    if ctx.choice_index == -1 && !state.players[p_idx].looked_cards.is_empty() {
        state.players[p_idx].looked_cards.clear();
    }

    if state.players[p_idx].looked_cards.is_empty() {
        let source_ids: Vec<i32> = match source_zone {
            Zone::Yell => state.players[p_idx].yell_cards.iter().copied().collect(),
            Zone::Hand => state.players[p_idx].hand.iter().copied().collect(),
            Zone::Deck => state.players[p_idx].deck.iter().copied().collect(),
            _ => state.players[p_idx].discard.iter().copied().collect(),
        };

        for cid in source_ids {
            let type_matches = if real_op == O_RECOVER_LIVE {
                db.get_live(cid).is_some()
            } else {
                db.get_member(cid).is_some()
            };
            if type_matches && (a == 0 || state.card_matches_filter_with_ctx(db, cid, a as u64, ctx)) {
                state.players[p_idx].looked_cards.push(cid);
            }
        }
        if state.players[p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }
    }

    if ctx.choice_index == -1 {
        let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
        // DISABLED auto-pick for O_RECOVER_MEMBER to satisfy tests (even with 1 choice, test wants the event)
        let is_single_choice_auto_pick = !is_optional && state.players[p_idx].looked_cards.len() == 1 && real_op != O_RECOVER_MEMBER;

        if is_single_choice_auto_pick {
            ctx.choice_index = 0;
        } else {
            let choice_type = if real_op == O_RECOVER_LIVE {
                ChoiceType::RecovL
            } else {
                ChoiceType::RecovM
            };
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                real_op,
                0,
                choice_type,
                &choice_text,
                0,
                -1,
            ) {
                return HandlerResult::Suspend;
            }
        }
    }

    let choice = ctx.choice_index as i32;
    let real_idx =
        if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len() {
            Some(choice as usize)
        } else {
            None
        };

    if let Some(idx) = real_idx {
        let cid = state.players[p_idx].looked_cards[idx];
        if cid != -1 {
            state.players[p_idx].looked_cards[idx] = -1;
            state.players[p_idx].hand.push(cid);
            state.players[p_idx].hand_increased_this_turn = state.players[p_idx]
                .hand_increased_this_turn
                .saturating_add(1);
            ctx.selected_cards.push(cid);

            let mut source_zone = instr.s.source_zone;
            if source_zone == Zone::Default {
                source_zone = Zone::Discard;
            }
            match source_zone {
                Zone::Yell => {
                    if let Some(pos) = state.players[p_idx]
                        .yell_cards
                        .iter()
                        .position(|&x| x == cid)
                    {
                        state.players[p_idx].yell_cards.remove(pos);
                    }
                }
                Zone::Hand => {
                    if let Some(pos) = state.players[p_idx].hand.iter().position(|&x| x == cid)
                    {
                        state.players[p_idx].hand.remove(pos);
                    }
                }
                Zone::Deck => {
                    if let Some(pos) = state.players[p_idx].deck.iter().position(|&x| x == cid)
                    {
                        state.players[p_idx].deck.remove(pos);
                    }
                }
                _ => {
                    if let Some(pos) = state.players[p_idx]
                        .discard
                        .iter()
                        .position(|&x| x == cid)
                    {
                        state.players[p_idx].discard.remove(pos);
                    }
                }
            }
            let remaining = if ctx.v_remaining == -1 {
                v as i16 - 1
            } else {
                ctx.v_remaining - 1
            };
            if remaining > 0
                && choice != CHOICE_ALL as i32
                && state.players[p_idx]
                    .looked_cards
                    .iter()
                    .any(|&c| c != -1)
            {
                let choice_type = if real_op == O_RECOVER_LIVE {
                    ChoiceType::RecovL
                } else {
                    ChoiceType::RecovM
                };
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    real_op,
                    0,
                    choice_type,
                    &choice_text,
                    0,
                    remaining,
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }
    state.players[p_idx].looked_cards.clear();
    HandlerResult::Continue
}
