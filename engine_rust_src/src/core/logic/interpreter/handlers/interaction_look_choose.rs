use crate::core::enums::{ChoiceType, TriggerType};
use crate::core::logic::constants::{CHOICE_ALL, CHOICE_DONE};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::models::interpreter::get_choice_text;
use crate::core::models::suspend_interaction;
use crate::core::O_LOOK_AND_CHOOSE;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

pub fn handle_look_and_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let _v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let slot_info = instr.slot();
    let target_slot = slot_info.target_slot;
    let rem_dest = slot_info.dest_zone as u8;
    let source_zone_bits = slot_info.source_zone as u8;
    let source_zone = if source_zone_bits == 0 {
        8
    } else {
        source_zone_bits as i32
    };
    let lc = instr.look_choose();
    let look_count = lc.count as usize;
    let reveal_flag = lc.reveal;
    let dest_discard_v = lc.dest_discard;

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
                    if let Some(cid) = state.players[p_idx].pop_hand_card() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            7 => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.players[p_idx].pop_discard_card() {
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
                    if let Some(cid) = state.players[p_idx].pop_deck_card() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
        }
    }

    if ctx.choice_index == -1 {
        let choice_type = if source_zone == 6 {
            ChoiceType::SelectHandDiscard
        } else if source_zone == 7 {
            ChoiceType::SelectDiscardPlay
        } else {
            ChoiceType::LookAndChoose
        };
        let lc = instr.look_choose();
        let choice_text = get_choice_text(db, ctx);

        let mut filter_obj = instr.filter_attr();
        filter_obj.char_id_1 = lc.char_id_1;
        filter_obj.char_id_2 = lc.char_id_2;
        filter_obj.char_id_3 = lc.char_id_3;

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
            filter_obj.to_attr(),
            pick_count,
        ) {
            let is_optional = filter_obj.is_optional;
            if is_optional && ctx.choice_index == CHOICE_DONE {
                let cards: Vec<i32> = state.players[p_idx].looked_cards.drain(..).collect();
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
                let destination = if target_slot > 0 { target_slot as i32 } else { 6 };
                match destination {
                    7 => {
                        state.players[p_idx].push_discard_card(chosen);
                    }
                    8 => {
                        state.players[p_idx].push_deck_card(chosen);
                    }
                    4 => {
                        let slot = slot_info.target_slot as usize;
                        if slot < 3 {
                            if let Some(cid) =
                                state.handle_member_leaves_stage(p_idx, slot, db, ctx)
                            {
                                state.players[p_idx].push_discard_card(cid as i32);
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
                            state.players[p_idx].gain_hand_card(chosen);
                        }
                    }
                    13 => {
                        state.players[p_idx].success_lives.push(chosen);
                    }
                    _ => {
                        state.players[p_idx].push_hand_card(chosen);
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

                let rem = if ctx.v_remaining > 0 { ctx.v_remaining - 1 } else { 0 };
                if rem > 0 && revealed.iter().any(|&c| c != -1) {
                    state.players[p_idx].looked_cards = revealed.clone();
                    let choice_type = if source_zone == 6 {
                        ChoiceType::SelectHandDiscard
                    } else if source_zone == 7 {
                        ChoiceType::SelectDiscardPlay
                    } else {
                        ChoiceType::LookAndChoose
                    };
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_LOOK_AND_CHOOSE,
                        s,
                        choice_type,
                        &choice_text,
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
            6 => {
                for cid in revealed {
                    state.players[p_idx].push_hand_card(cid);
                }
            }
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
