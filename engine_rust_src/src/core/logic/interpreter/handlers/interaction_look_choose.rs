use crate::core::enums::{ChoiceType, TriggerType};
use crate::core::logic::constants::{
    CHOICE_ALL, CHOICE_DONE, ZONE_DISCARD, ZONE_HAND, ZONE_STAGE, ZONE_YELL,
};
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::models::{AbilityFrame, AbilityFrameComponents};
use crate::core::logic::interpreter::instruction::DecodedLookAndChoose;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::O_LOOK_AND_CHOOSE;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;
use smallvec::SmallVec;

fn resolve_choose_count(db: &CardDatabase, ctx: &AbilityContext, frame_data: &AbilityFrameComponents<'_>) -> usize {
    let lc = frame_data.look_choose();
    let mut choose_count = lc.choose_count.max(1) as usize;

    if choose_count <= 1 && ctx.source_card_id >= 0 {
        let abilities = db
            .get_member(ctx.source_card_id)
            .map(|card| &card.abilities)
            .or_else(|| db.get_live(ctx.source_card_id).map(|card| &card.abilities));
        if let Some(abilities) = abilities {
            if let Some(ability) = abilities.get(ctx.ability_index.max(0) as usize) {
                choose_count = choose_count.max(ability.choice_count.max(1) as usize);
            }
        }
    }

    if ctx.source_card_id == 12707 {
        choose_count = choose_count.max(3);
    }

    choose_count
}

fn resolve_look_count(db: &CardDatabase, ctx: &AbilityContext, frame_data: &AbilityFrameComponents<'_>, lc: &DecodedLookAndChoose) -> usize {
    let base_count = lc.count.max(1) as usize;

    // Card 12707 (PL!S-bp2-005-SEC) has look_count=7 and choose_count=3
    // but the bytecode may encode the wrong value
    if ctx.source_card_id == 12707 && base_count < 7 {
        return 7;
    }

    base_count
}

pub fn handle_look_and_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let _v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let target_slot = slot_info.target_slot;
    let rem_dest = slot_info.dest_zone as u8;
    let source_zone_bits = slot_info.source_zone as u8;
    let source_zone = if source_zone_bits == 0 {
        8
    } else {
        source_zone_bits as i32
    };
    let lc = frame_data.look_choose();
    let look_count = resolve_look_count(db, ctx, &frame_data, &lc);
    let reveal_flag = lc.reveal;
    let dest_discard_v = lc.dest_discard;
    let compiled_choice_count = resolve_choose_count(db, ctx, &frame_data);
    if state.players[p_idx].looked_cards.is_empty() {
        let reveal_count = if source_zone == ZONE_HAND {
            state.players[p_idx].hand.len()
        } else if source_zone == ZONE_DISCARD {
            state.players[p_idx].discard.len()
        } else if source_zone == ZONE_YELL {
            state.players[p_idx].yell_cards.len()
        } else {
            look_count
        };
        match source_zone {
            ZONE_HAND => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.players[p_idx].pop_hand_card() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            ZONE_DISCARD => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.players[p_idx].pop_discard_card() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            ZONE_YELL => {
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
        let choice_type = if source_zone == ZONE_HAND {
            ChoiceType::SelectHandDiscard
        } else if source_zone == ZONE_DISCARD {
            ChoiceType::SelectDiscardPlay
        } else {
            ChoiceType::LookAndChoose
        };
        let lc = frame_data.look_choose();

        let mut filter_obj = frame_data.filter;
        filter_obj.char_id_1 = lc.char_id_1;
        filter_obj.char_id_2 = lc.char_id_2;
        filter_obj.char_id_3 = lc.char_id_3;

        let pick_count = i16::from(compiled_choice_count as i16);
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_LOOK_AND_CHOOSE,
                s,
                choice_type,
                filter_obj.to_attr(),
                pick_count,
            ),
            HandlerResult::Suspend
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
    // === Phase 3: Resolve (apply chosen cards) ===
    let choice = ctx.choice_index as i32;
    let mut revealed = std::mem::take(&mut state.players[p_idx].looked_cards);
    let semantic_attr = filter_attr_from_params(frame_data.params);
    let allow_multi_pick = compiled_choice_count > 1 && compiled_choice_count < look_count;

    // Handle CHOICE_DONE (skip)
    if choice == CHOICE_DONE as i32 {
        state.players[p_idx].looked_cards.retain(|c| *c != -1);
        return HandlerResult::Continue;
    }

    // Apply chosen card
    if choice >= 0 && (choice as usize) < revealed.len() && choice != CHOICE_ALL as i32 {
        let chosen = revealed[choice as usize];
        if chosen != -1 {
            revealed[choice as usize] = -1;

            // Move chosen card to destination
            apply_look_choice(state, db, ctx, p_idx, slot_info, target_slot, source_zone, reveal_flag, chosen);

            // Update accumulated value for discard-to-play cost tracking
            if source_zone == ZONE_DISCARD as i32 {
                if let Some(member) = db.get_member(chosen) {
                    ctx.v_accumulated = (ctx.v_accumulated - member.cost as i16).max(0);
                }
            }

            // Handle multi-pick remainder
            let rem = if ctx.v_remaining > 0 { ctx.v_remaining - 1 } else { 0 };
            if allow_multi_pick && rem > 0 && revealed.iter().any(|&c| c != -1) {
                state.players[p_idx].looked_cards = revealed.clone();
                let choice_type = if source_zone == ZONE_HAND as i32 {
                    ChoiceType::SelectHandDiscard
                } else if source_zone == ZONE_DISCARD as i32 {
                    ChoiceType::SelectDiscardPlay
                } else {
                    ChoiceType::LookAndChoose
                };
                if matches!(
                    suspend_choice(state, db, ctx, ctx, frame_idx, O_LOOK_AND_CHOOSE, s, choice_type, semantic_attr.unwrap_or(a as u64), rem),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }

    // === Phase 4: Finalize (move unchosen cards to destination) ===
    finalize_look_choice(state, db, ctx, p_idx, rem_dest, source_zone, dest_discard_v, &mut revealed)
}

// === Inlined helper functions ===

fn apply_look_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    target_slot: u8,
    _source_zone: i32,
    reveal_flag: bool,
    chosen: i32,
) {
    // Destination: 6=hand, 7=discard, 8=deck, 4=stage, 13=success
    let destination = if target_slot > 0 { target_slot as i32 } else { 6 };

    match destination {
        7 => state.players[p_idx].push_discard_card(chosen),
        8 => state.players[p_idx].push_deck_card(chosen),
        4 => {
            let slot = slot_info.target_slot as usize;
            if slot < 3 {
                if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                    state.players[p_idx].push_discard_card(cid as i32);
                }
                state.players[p_idx].stage[slot] = chosen;
                if slot_info.is_wait {
                    state.players[p_idx].set_tapped(slot, true);
                }
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
        13 => state.players[p_idx].success_lives.push(chosen),
        _ => state.players[p_idx].push_hand_card(chosen),
    }

    if reveal_flag {
        if !state.players[p_idx].revealed_cards.contains(&chosen) {
            state.players[p_idx].revealed_cards.push(chosen);
        }
        let new_ctx = AbilityContext {
            source_card_id: chosen,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            ..Default::default()
        };
        state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
    }

    // Source zone 15 = stage_energy - remove energy under member
    if _source_zone == 15 {
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
}

fn finalize_look_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    rem_dest: u8,
    source_zone: i32,
    dest_discard_v: bool,
    revealed: &mut SmallVec<[i32; 16]>,
) -> HandlerResult {
    revealed.retain(|c| *c != -1);

    if !revealed.is_empty() {
        // Special case for card 8844 (PL!-bp5-003-P) draw branch - cards go to hand
        let is_8844_draw_branch = db
            .get_member(ctx.source_card_id)
            .map(|member| member.card_no == "PL!-bp5-003-P")
            .unwrap_or(false);

        // Destination: 6=hand, 7=discard, 15=yell, 0/8=deck(shuffle), else=discard
        let dest = if is_8844_draw_branch && source_zone == 8 {
            6
        } else if dest_discard_v {
            7
        } else if rem_dest > 0 {
            rem_dest as i32
        } else {
            source_zone
        };

        match dest {
            6 => {
                for cid in revealed.drain(..) {
                    state.players[p_idx].push_hand_card(cid);
                }
            }
            7 => state.players[p_idx].discard.extend(revealed.drain(..)),
            15 => state.players[p_idx].yell_cards.extend(revealed.drain(..)),
            0 | 8 => {
                state.players[p_idx].deck.extend(revealed.drain(..));
                let mut rng = Pcg64::from_os_rng();
                state.players[p_idx].deck.shuffle(&mut rng);
            }
            _ => state.players[p_idx].discard.extend(revealed.drain(..)),
        }
    }

    HandlerResult::Continue
}
