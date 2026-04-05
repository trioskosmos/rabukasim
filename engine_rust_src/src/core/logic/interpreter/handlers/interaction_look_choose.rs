use crate::core::enums::{TriggerType, Zone};
use crate::core::logic::constants::{CHOICE_ALL, CHOICE_DONE, TARGET_SLOT_STAGE};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::models::{AbilityFrameComponents, SemanticLookAndChooseSpec};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::O_LOOK_AND_CHOOSE;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

fn resolve_choose_count(db: &CardDatabase, ctx: &AbilityContext, frame_data: &AbilityFrameComponents<'_>) -> usize {
    let mut choose_count = frame_data.look_choose().choose_count.max(1) as usize;

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

    choose_count
}

fn semantic_spec(
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
) -> SemanticLookAndChooseSpec {
    let choose_count = resolve_choose_count(db, ctx, frame_data);
    frame_data.semantic_look_and_choose_spec(choose_count)
}

fn reveal_count_for_zone(state: &GameState, p_idx: usize, source_zone: Zone, look_count: usize) -> usize {
    match source_zone {
        Zone::Hand => state.players[p_idx].hand.len(),
        Zone::Discard => state.players[p_idx].discard.len(),
        Zone::Yell => state.players[p_idx].yell_cards.len(),
        _ => look_count,
    }
}

fn populate_looked_cards(
    state: &mut GameState,
    p_idx: usize,
    source_zone: Zone,
    reveal_count: usize,
) {
    match source_zone {
        Zone::Hand => {
            for _ in 0..reveal_count {
                if let Some(cid) = state.players[p_idx].pop_hand_card() {
                    state.players[p_idx].looked_cards.push(cid);
                }
            }
        }
        Zone::Discard => {
            for _ in 0..reveal_count {
                if let Some(cid) = state.players[p_idx].pop_discard_card() {
                    state.players[p_idx].looked_cards.push(cid);
                }
            }
        }
        Zone::Yell => {
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

fn target_slot_destination(target_slot: u8) -> Zone {
    match target_slot {
        TARGET_SLOT_STAGE => Zone::Stage,
        x if x == Zone::Discard as u8 => Zone::Discard,
        x if x == Zone::Deck as u8 => Zone::Deck,
        x if x == Zone::SuccessPile as u8 => Zone::SuccessPile,
        x if x == Zone::Hand as u8 || x == 0 => Zone::Hand,
        _ => Zone::Hand,
    }
}

fn resolved_finalize_destination(spec: &SemanticLookAndChooseSpec, ctx: &AbilityContext) -> Zone {
    let dest = spec.finalize_destination();
    if dest != spec.source_zone || spec.remainder_to_discard || spec.remainder_zone != Zone::Default {
        return dest;
    }

    let is_real_ability = ctx.ability_index >= 0
        || ctx.ability_card_id >= 0
        || ctx.trigger_type != TriggerType::None;
    if is_real_ability && matches!(spec.source_zone, Zone::Deck | Zone::DeckTop | Zone::DeckBottom) {
        Zone::Discard
    } else {
        dest
    }
}

pub fn handle_look_and_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let spec = semantic_spec(db, ctx, frame_data);
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let target_slot = slot_info.target_slot;
    let source_zone = spec.source_zone;
    let look_count = spec.look_count;
    let reveal_flag = spec.reveal;
    let compiled_choice_count = spec.choose_count;
    if ctx.choice_index == -1 {
        state.players[p_idx].looked_cards.clear();
    }
    if state.players[p_idx].looked_cards.is_empty() {
        let reveal_count = reveal_count_for_zone(state, p_idx, source_zone, look_count);
        populate_looked_cards(state, p_idx, source_zone, reveal_count);
    }

    if ctx.choice_index == -1 {
        let pick_count = i16::from(compiled_choice_count as i16);
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_LOOK_AND_CHOOSE,
                spec.suspend_slot,
                spec.choice_type(),
                spec.selection_filter_attr,
                pick_count,
            ),
            HandlerResult::Suspend
        ) {
            let is_optional = spec.selection_filter.is_optional;
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
    let allow_multi_pick = compiled_choice_count > 1 && compiled_choice_count < look_count;

    // Handle CHOICE_DONE (skip) by finalizing the remaining looked cards.
    if choice == CHOICE_DONE as i32 {
        return finalize_look_choice(
            state,
            db,
            ctx,
            p_idx,
            resolved_finalize_destination(&spec, ctx),
            source_zone,
            &mut revealed,
        );
    }

    // Apply chosen card
    if choice >= 0 && (choice as usize) < revealed.len() && choice != CHOICE_ALL as i32 {
        let chosen = revealed[choice as usize];
        if chosen != -1 {
            revealed[choice as usize] = -1;

            // Move chosen card to destination
            apply_look_choice(state, db, ctx, p_idx, slot_info, target_slot, source_zone, reveal_flag, chosen);

            // Update accumulated value for discard-to-play cost tracking
            if source_zone == Zone::Discard {
                if let Some(member) = db.get_member(chosen) {
                    ctx.v_accumulated = (ctx.v_accumulated - member.cost as i16).max(0);
                }
            }

            // Handle multi-pick remainder
            let rem = if ctx.v_remaining > 0 { ctx.v_remaining - 1 } else { 0 };
            if allow_multi_pick && rem > 0 && revealed.iter().any(|&c| c != -1) {
                state.players[p_idx].looked_cards = revealed.clone();
                if matches!(
                    suspend_choice(state, db, ctx, ctx, frame_idx, O_LOOK_AND_CHOOSE, spec.suspend_slot, spec.choice_type(), spec.selection_filter_attr, rem),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }

    // === Phase 4: Finalize (move unchosen cards to destination) ===
    finalize_look_choice(
        state,
        db,
        ctx,
        p_idx,
        resolved_finalize_destination(&spec, ctx),
        source_zone,
        &mut revealed,
    )
}

// === Inlined helper functions ===

fn apply_look_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    target_slot: u8,
    source_zone: Zone,
    reveal_flag: bool,
    chosen: i32,
) {
    let destination = target_slot_destination(target_slot);

    match destination {
        Zone::Discard => state.players[p_idx].push_discard_card(chosen),
        Zone::Deck | Zone::DeckTop | Zone::DeckBottom => state.players[p_idx].push_deck_card(chosen),
        Zone::Stage => {
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
        Zone::SuccessPile => state.players[p_idx].success_lives.push(chosen),
        _ => state.players[p_idx].push_hand_card(chosen),
    }

    if reveal_flag {
        if !state.players[p_idx].revealed_cards.contains(&chosen) {
            state.players[p_idx].revealed_cards.push(chosen);
        }
    }

    // Legacy stage-energy sources still arrive as a raw slot zone id, not a first-class enum.
    if source_zone as i32 == 15 {
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
    _db: &CardDatabase,
    _ctx: &AbilityContext,
    p_idx: usize,
    final_destination: Zone,
    source_zone: Zone,
    revealed: &mut smallvec::SmallVec<[i32; 16]>,
) -> HandlerResult {
    revealed.retain(|c| *c != -1);

    if !revealed.is_empty() {
        let dest = match final_destination {
            Zone::Default => source_zone,
            other => other,
        };

        match dest {
            Zone::Hand => {
                for cid in revealed.drain(..) {
                    state.players[p_idx].push_hand_card(cid);
                }
            }
            Zone::Discard => {
                for cid in revealed.drain(..) {
                    state.players[p_idx].push_discard_card(cid);
                }
            }
            Zone::Yell => {
                state.players[p_idx].yell_cards.extend(revealed.drain(..));
            }
            Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => {
                state.players[p_idx].deck.extend(revealed.drain(..));
                let mut rng = Pcg64::from_os_rng();
                state.players[p_idx].deck.shuffle(&mut rng);
            }
            _ => {
                for cid in revealed.drain(..) {
                    state.players[p_idx].push_discard_card(cid);
                }
            }
        }

        if state.players[p_idx].deck.is_empty() && !state.players[p_idx].discard.is_empty() {
            state.players[p_idx].set_flag(
                crate::core::logic::player::PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH,
                true,
            );
        }
    }

    HandlerResult::Continue
}
