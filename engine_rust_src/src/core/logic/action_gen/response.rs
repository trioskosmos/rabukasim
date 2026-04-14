use crate::core::enums::*;
use crate::core::logic::ability_patterns::{
    pending_live_ability, pending_member_ability, pending_optional_mode_mask,
    pending_targeted_live_heart_bonus,
};
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::filter::{filter_attr_from_params, structured_filter_from_attr, CardFilter};
use crate::core::logic::constants::FILTER_COLOR_SHIFT_R5;
use crate::core::logic::interpreter::logging;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::interpreter::handlers::interaction_zone::{
    collect_zone_cards, selected_target_key,
};
use crate::core::logic::interpreter::suspension::resolve_target_player_from_filter;
use crate::core::logic::profiling::{env_flag_enabled, env_threshold_us};
use crate::core::logic::{
    Ability, AbilityContext, ActionReceiver, CardDatabase, ChoiceType, GameState,
    PendingInteraction,
};
use crate::core::models::CHOICE_DONE;
use crate::core::types::{MAX_LIVE_SET_SIZE, STAGE_SLOT_COUNT};
use std::time::Instant;

pub struct ResponseGenerator;

#[inline]
fn optional_skip_is_available(pi: &PendingInteraction) -> bool {
    pi.filter.is_optional
        || (pi.filter_attr & FILTER_IS_OPTIONAL) != 0
        || pi.choice_type == ChoiceType::Optional
}

#[inline]
fn add_cards_matching_filter<R: ActionReceiver + ?Sized>(
    state: &GameState,
    db: &CardDatabase,
    receiver: &mut R,
    cards: &[i32],
    filter_attr: u64,
    ctx: &AbilityContext,
    base_action: i32,
) {
    for (i, &cid) in cards.iter().enumerate() {
        if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
            receiver.add_action((base_action + i as i32) as usize);
        }
    }
}

#[inline]
fn add_indexed_actions<R, F>(receiver: &mut R, count: usize, base_action: i32, mut include: F)
where
    R: ActionReceiver + ?Sized,
    F: FnMut(usize) -> bool,
{
    for idx in 0..count {
        if include(idx) {
            receiver.add_action((base_action + idx as i32) as usize);
        }
    }
}

#[inline]
fn add_stage_slot_actions<R: ActionReceiver + ?Sized>(
    receiver: &mut R,
    player: &crate::core::logic::player::PlayerState,
    allow_moved: bool,
) {
    for slot_idx in 0..STAGE_SLOT_COUNT {
        let prevented = (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0;
        if !prevented && (allow_moved || !player.is_moved(slot_idx)) {
            receiver.add_action((ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as usize);
        }
    }
}

#[inline]
fn add_optional_done<R: ActionReceiver + ?Sized>(receiver: &mut R) {
    receiver.add_action((ACTION_BASE_CHOICE + CHOICE_DONE as i32) as usize);
}

#[inline]
fn add_optional_done_if_available<R: ActionReceiver + ?Sized>(
    receiver: &mut R,
    pi: &PendingInteraction,
) {
    if optional_skip_is_available(pi) {
        add_optional_done(receiver);
    }
}

#[inline]
fn add_matching_stage_actions<R: ActionReceiver + ?Sized>(
    receiver: &mut R,
    state: &GameState,
    db: &CardDatabase,
    player: &crate::core::logic::player::PlayerState,
    filter_attr: u64,
    ctx: &AbilityContext,
    allow_tapped: bool,
) -> bool {
    let mut added_any = false;
    for i in 0..STAGE_SLOT_COUNT {
        let cid = player.stage[i];
        if cid < 0 {
            continue;
        }
        if !allow_tapped && player.is_tapped(i) {
            continue;
        }
        if filter_attr != 0
            && !state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
        {
            continue;
        }
        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
        added_any = true;
    }
    added_any
}

fn card_groups<'a>(db: &'a CardDatabase, cid: i32) -> Option<&'a [u8]> {
    db.get_member(cid)
        .map(|card| card.groups.as_slice())
        .or_else(|| db.get_live(cid).map(|card| card.groups.as_slice()))
}

fn card_units<'a>(db: &'a CardDatabase, cid: i32) -> Option<&'a [u8]> {
    db.get_member(cid)
        .map(|card| card.units.as_slice())
        .or_else(|| db.get_live(cid).map(|card| card.units.as_slice()))
}

fn hand_card_has_same_group_partner(
    db: &CardDatabase,
    hand: &[i32],
    idx: usize,
) -> bool {
    let Some(candidate_groups) = card_groups(db, hand[idx]) else {
        return false;
    };

    let mut group_counts = std::collections::HashMap::<u8, usize>::new();
    for &cid in hand.iter() {
        if cid < 0 {
            continue;
        }
        if let Some(groups) = card_groups(db, cid) {
            for &group in groups {
                *group_counts.entry(group).or_insert(0) += 1;
            }
        }
    }

    candidate_groups
        .iter()
        .any(|group| group_counts.get(group).copied().unwrap_or(0) > 1)
}

fn add_same_group_hand_discard_actions<R: ActionReceiver + ?Sized>(
    _state: &GameState,
    db: &CardDatabase,
    receiver: &mut R,
    hand: &[i32],
    _filter_attr: u64,
    _ctx: &AbilityContext,
    base_action: i32,
    pi: &PendingInteraction,
) {
    let first_pick = pi.ctx.selected_cards.is_empty();
    let first_selected_groups = pi
        .ctx
        .selected_cards
        .first()
        .and_then(|cid| card_groups(db, *cid))
        .map(|groups| groups.to_vec());

    for (i, &cid) in hand.iter().enumerate() {
        if cid < 0 {
            continue;
        }
        if first_pick {
            if !hand_card_has_same_group_partner(db, hand, i) {
                continue;
            }
        } else if let Some(required_groups) = first_selected_groups.as_ref() {
            let Some(candidate_groups) = card_groups(db, cid) else {
                continue;
            };
            if !candidate_groups
                .iter()
                .any(|group| required_groups.contains(group))
            {
                continue;
            }
        }
        receiver.add_action((base_action + i as i32) as usize);
    }
    add_optional_done_if_available(receiver, pi);
}

fn hand_card_has_same_unit_partner(
    db: &CardDatabase,
    hand: &[i32],
    idx: usize,
) -> bool {
    let Some(candidate_units) = card_units(db, hand[idx]) else {
        return false;
    };

    let mut unit_counts = std::collections::HashMap::<u8, usize>::new();
    for &cid in hand.iter() {
        if cid < 0 {
            continue;
        }
        if let Some(units) = card_units(db, cid) {
            for &unit in units {
                *unit_counts.entry(unit).or_insert(0) += 1;
            }
        }
    }

    candidate_units
        .iter()
        .any(|unit| unit_counts.get(unit).copied().unwrap_or(0) > 1)
}

fn add_same_unit_hand_discard_actions<R: ActionReceiver + ?Sized>(
    _state: &GameState,
    db: &CardDatabase,
    receiver: &mut R,
    hand: &[i32],
    _filter_attr: u64,
    _ctx: &AbilityContext,
    base_action: i32,
    pi: &PendingInteraction,
) {
    let first_pick = pi.ctx.selected_cards.is_empty();
    let first_selected_units = pi
        .ctx
        .selected_cards
        .first()
        .and_then(|cid| card_units(db, *cid))
        .map(|units| units.to_vec());

    for (i, &cid) in hand.iter().enumerate() {
        if cid < 0 {
            continue;
        }
        if first_pick {
            if !hand_card_has_same_unit_partner(db, hand, i) {
                continue;
            }
        } else if let Some(required_units) = first_selected_units.as_ref() {
            let Some(candidate_units) = card_units(db, cid) else {
                continue;
            };
            if !candidate_units
                .iter()
                .any(|unit| required_units.contains(unit))
            {
                continue;
            }
        }
        receiver.add_action((base_action + i as i32) as usize);
    }
    add_optional_done_if_available(receiver, pi);
}

fn add_stage_empty_actions<R: ActionReceiver + ?Sized>(
    receiver: &mut R,
    player: &crate::core::logic::player::PlayerState,
    baton_only: bool,
) {
    for slot_idx in 0..STAGE_SLOT_COUNT {
        let prevented = (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0;
        let occupied = player.stage[slot_idx] >= 0;
        if !prevented && !occupied && (!baton_only || player.baton_source_slots.contains(&slot_idx))
        {
            receiver.add_action((ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as usize);
        }
    }
}

fn modal_option_is_legal(
    db: &CardDatabase,
    state: &GameState,
    p_idx: usize,
    ability: &Ability,
    option_idx: usize,
) -> bool {
    let Some(frames) = ability.get_modal_option_frames(option_idx) else {
        return ability.has_authored_frame_program() && option_idx < ability.modal_option_count();
    };

    if let Some(spec) = frames
        .first()
        .and_then(|frame| crate::core::logic::models::semantic_recovery_branch_spec_from_params(frame.components().params))
    {
        let mut distinct_names: Vec<&str> = Vec::new();
        let mut distinct_groups: Vec<u8> = Vec::new();

        for cid in state.players[p_idx].discard.iter().copied() {
            let Some(card) = db.get_live(cid) else {
                continue;
            };

            match spec.kind {
                crate::core::logic::models::SemanticRecoveryBranchKind::UniqueDiscardLiveNames => {
                    let name = card.name.as_str();
                    if !distinct_names.iter().any(|existing| *existing == name) {
                        distinct_names.push(name);
                    }
                }
                crate::core::logic::models::SemanticRecoveryBranchKind::UniqueDiscardLiveGroups => {
                    for group_id in card.groups.iter().copied() {
                        if !distinct_groups.contains(&group_id) {
                            distinct_groups.push(group_id);
                        }
                    }
                }
            }
        }

        return match spec.kind {
            crate::core::logic::models::SemanticRecoveryBranchKind::UniqueDiscardLiveNames => {
                distinct_names.len() >= spec.minimum
            }
            crate::core::logic::models::SemanticRecoveryBranchKind::UniqueDiscardLiveGroups => {
                distinct_groups.len() >= spec.minimum
            }
        };
    }

    let Some(first_frame) = frames.first() else {
        return false;
    };

    match first_frame.opcode() {
        O_PAY_ENERGY => {
            let required = first_frame.value().max(0) as usize;
            let available = state.players[p_idx]
                .energy_zone
                .iter()
                .enumerate()
                .filter(|(idx, _)| !state.players[p_idx].is_energy_tapped(*idx))
                .count();
            available >= required
        }
        _ => true,
    }
}

impl ActionGenerator for ResponseGenerator {
    fn generate<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        let _condition_cache_scope = crate::core::logic::interpreter::conditions::ConditionEvalCacheScope::activate();
        let profile_enabled = env_flag_enabled("BENCH_PROFILE_RESPONSE_ACTIONS");
        let profile_start = profile_enabled.then(Instant::now);
        let pending_desc = if profile_enabled {
            state
                .interaction_stack
                .last()
                .map(logging::describe_pending_interaction)
        } else {
            None
        };
        let used_prefilled_actions = state
            .interaction_stack
            .last()
            .map(|pi| !pi.actions.is_empty())
            .unwrap_or(false);
        let _filter_cache_scope = crate::core::logic::game_rules_ext::FilterMatchCacheScope::activate();

        self.generate_internal(db, p_idx, state, receiver);

        if let Some(profile_start) = profile_start {
            let total_us = profile_start.elapsed().as_nanos() as u64 / 1000;
            if total_us >= env_threshold_us("BENCH_PROFILE_STEP_THRESHOLD_US", 2000) {
                println!(
                    "[PROFILE] ResponseActions total_us={} p={} used_prefilled_actions={} empty_after_generate={} pending={}",
                    total_us,
                    p_idx,
                    used_prefilled_actions,
                    receiver.is_empty(),
                    pending_desc.as_deref().unwrap_or("pending[none]")
                );
            }
        }

        // Keep Pass(0) available for mandatory interactions so the game does not softlock
        // when a prompt path produces no legal actions.
        if receiver.is_empty() {
            receiver.add_action(0);
        }

    }
}

impl ResponseGenerator {
    fn is_targeted_select_member_cost(db: &CardDatabase, pi: &PendingInteraction) -> bool {
        if pi.effect_opcode != O_SELECT_MEMBER || !pi.has_structured_filter_constraints() {
            return false;
        }

        let ability = pending_live_ability(db, pi).or_else(|| {
            pending_member_ability(db, pi.card_id, pi.ability_index)
        });
        let Some(frame) = ability.and_then(|ab| ab.get_frame(pi.ctx.program_counter as usize)) else {
            return false;
        };
        let components = frame.components();
        components.opcode == O_SELECT_MEMBER
            && components.slot.target_slot == crate::core::logic::constants::TARGET_SLOT_STAGE
            && components.slot.source_zone == Zone::Default
    }

    fn add_filtered_stage_actions<R: ActionReceiver + ?Sized>(
        receiver: &mut R,
        state: &GameState,
        db: &CardDatabase,
        target_player: usize,
        filter_attr: u64,
        ctx: &AbilityContext,
        allow_tapped: bool,
    ) {
        for i in 0..STAGE_SLOT_COUNT {
            let cid = state.players[target_player].stage[i];
            if cid < 0 {
                continue;
            }
            if !allow_tapped && state.players[target_player].is_tapped(i) {
                continue;
            }
            if filter_attr != 0
                && !state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
            {
                continue;
            }
            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
        }
    }

    fn is_position_change_prompt(pi: &PendingInteraction) -> bool {
        pi.effect_opcode == O_MOVE_MEMBER
            || pi.effect_opcode == O_FORMATION_CHANGE
            || pi.choice_type == ChoiceType::MoveMemberDest
            || pi.choice_type == ChoiceType::RearrangeFormation
    }

    fn generate_position_change_destinations<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        _abilities: Option<&Vec<Ability>>,
        p_idx: usize,
    ) {
        let player = &state.players[p_idx];
        let filter_attr = pi.filter_attr;
        let source_slot = player
            .stage
            .iter()
            .position(|&cid| cid == pi.ctx.source_card_id);
        let allow_any_occupied_dest = filter_attr == 0;
        let mut added_dest = false;
        for i in 0..STAGE_SLOT_COUNT {
            let cid = player.stage[i];
            if source_slot == Some(i) {
                continue;
            }
            // Allow empty slots as valid destinations, or occupied slots that
            // match the filter (or any occupied slot when filter is zero).
            if cid < 0 {
                receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                added_dest = true;
            } else if allow_any_occupied_dest
                || state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx)
            {
                receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                added_dest = true;
            }
        }
        if !added_dest {
            receiver.add_action(0);
        }
    }

    fn effect_filter_attr_for_opcode(ab: &Ability, opcode: i32) -> Option<u64> {
        let matches_opcode = |effect: &crate::core::logic::Effect| {
            effect.runtime_opcode == opcode
                || (opcode == O_SELECT_MEMBER && effect.effect_type == EffectType::SelectMember)
                || (opcode == O_MOVE_MEMBER && effect.effect_type == EffectType::MoveMember)
        };

        ab.effects
            .iter()
            .find(|effect| matches_opcode(effect))
            .and_then(|effect| filter_attr_from_params(Some(&effect.params)))
    }

    fn generate_internal<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        let pi = if let Some(p) = state.interaction_stack.last() {
            p
        } else {
            return;
        };
        let ctx = &pi.ctx;
        let opcode = pi.effect_opcode;
        let choice_type = pi.choice_type;
        let source_card_id = pi.ctx.source_card_id;

        let expected_p_idx = ctx.player_id as usize;

        if expected_p_idx != p_idx {
            return;
        }

        if !pi.actions.is_empty() {
            for &action in &pi.actions {
                receiver.add_action(action as usize);
            }
            return;
        }

        let player = &state.players[p_idx];
        let offer_optional_skip = matches!(choice_type, ChoiceType::Optional)
            || (!matches!(
                choice_type,
                ChoiceType::MoveMemberDest
                    | ChoiceType::SelectStage
                    | ChoiceType::SelectStageEmpty
                    | ChoiceType::SelectStageEmptyBaton
            ) && optional_skip_is_available(pi));

        let member = db.get_member(source_card_id as i32);
        let live = db.get_live(source_card_id as i32);
        let abilities = if let Some(m) = member {
            Some(&m.abilities)
        } else {
            live.map(|l| &l.abilities)
        };
        let is_targeted_select_member_cost = Self::is_targeted_select_member_cost(db, pi);

        if pending_optional_mode_mask(db, pi).is_some() {
            self.generate_select_mode_actions(db, p_idx, state, receiver, pi, abilities);
            return;
        }

        let targeted_live_heart_bonus = pending_targeted_live_heart_bonus(db, pi)
            .filter(|_| {
                pi.ctx.trigger_type == TriggerType::OnLiveStart
                    && matches!(
                        pi.choice_type,
                        ChoiceType::SelectMember | ChoiceType::SelectHandDiscard
                    )
            });

        if let Some((filter_attr, _heart_color_idx)) = targeted_live_heart_bonus {
            let mut added_any = false;
            for (i, &cid) in state.players[p_idx].stage.iter().enumerate() {
                if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx) {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    added_any = true;
                }
            }
            if added_any {
                receiver.add_action(0);
                return;
            }
        }

        match choice_type {
            ChoiceType::Optional => {
                let should_offer_yes_no = pi.effect_opcode == O_PAY_ENERGY;
                let is_optional_deck_discard = pi.effect_opcode == O_MOVE_TO_DISCARD && {
                    let decoded_slot =
                        crate::core::logic::interpreter::instruction::DecodedSlot::decode(
                            pi.target_slot,
                        );
                    let is_deck = matches!(decoded_slot.source_zone, crate::core::enums::Zone::Deck | crate::core::enums::Zone::DeckTop | crate::core::enums::Zone::DeckBottom);
                    is_deck
                };
                if should_offer_yes_no || is_optional_deck_discard {
                    receiver.add_action((ACTION_BASE_CHOICE + 0) as usize); // Yes/Proceed
                    receiver.add_action((ACTION_BASE_CHOICE + 1) as usize); // No/Skip
                }
                if is_targeted_select_member_cost {
                    for i in 0..STAGE_SLOT_COUNT {
                        if state.players[p_idx].stage[i] >= 0 {
                            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                        }
                    }
                    add_optional_done(receiver);
                }
                if should_offer_yes_no {
                    if offer_optional_skip {
                        receiver.add_action(0);
                    }
                    return;
                }
            }
            ChoiceType::PayEnergy => {
                add_indexed_actions(
                    receiver,
                    player.energy_zone.len().min(16),
                    ACTION_BASE_ENERGY,
                    |i| {
                        pi.effect_opcode == O_PLACE_ENERGY_UNDER_MEMBER
                            || !player.is_energy_tapped(i)
                    },
                );
                if pi.v_remaining == -2 {
                    receiver.add_action((ACTION_BASE_CHOICE + 99) as usize);
                }
                return;
            }
            ChoiceType::RevealHand => {
                add_indexed_actions(
                    receiver,
                    player.hand.len(),
                    ACTION_BASE_HAND_SELECT,
                    |i| player.hand[i] >= 0,
                );
                return;
            }
            ChoiceType::TapO => {
                let decoded_slot = DecodedSlot::decode(pi.target_slot);
                let target_p_idx =
                    resolve_target_player_from_filter(decoded_slot, pi.filter, p_idx);
                Self::add_filtered_stage_actions(
                    receiver,
                    state,
                    db,
                    target_p_idx,
                    pi.filter_attr,
                    &pi.ctx,
                    false,
                );
                return;
            }
            ChoiceType::SelectDiscard => {
                let recover_base_cost = if pi.effect_opcode == O_RECOVER_MEMBER {
                    pi.ctx
                        .selected_cards
                        .last()
                        .and_then(|cid| db.get_member(*cid))
                        .map(|member| member.cost as i16)
                } else {
                    None
                };
                for (i, &cid) in player.discard.iter().enumerate() {
                    let discard_slot = (p_idx as u8, 100 + i as i16);
                    let candidate_matches = cid >= 0
                        && !pi.ctx.selected_cards.contains(&cid)
                        && state.card_matches_filter_with_ctx_at_slot(
                            db,
                            cid,
                            pi.filter_attr,
                            discard_slot,
                            &pi.ctx,
                        )
                        && recover_base_cost
                            .map(|base_cost| {
                                db.get_member(cid)
                                    .map(|member| member.cost as i16 == base_cost + 2)
                                    .unwrap_or(false)
                            })
                            .unwrap_or(true);
                    if candidate_matches {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectSwapSource => {
                let decoded_slot = DecodedSlot::decode(pi.target_slot);
                let source_zone = if decoded_slot.source_zone == Zone::Default {
                    Zone::SuccessPile
                } else {
                    decoded_slot.source_zone
                };
                for (i, &cid) in collect_zone_cards(state, p_idx, source_zone).iter().enumerate() {
                    if cid >= 0
                        && state.card_matches_filter_with_ctx(db, cid, pi.filter_attr, &pi.ctx)
                    {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectStage => {
                let is_position_change_choice = Self::is_position_change_prompt(pi);
                if is_position_change_choice {
                    self.generate_position_change_destinations(
                        db, state, receiver, pi, abilities, p_idx,
                    );
                } else {
                    add_stage_slot_actions(receiver, player, true);
                }
                return;
            }
            ChoiceType::SelectStageEmpty => {
                add_stage_empty_actions(receiver, player, false);
                return;
            }
            ChoiceType::SelectStageEmptyBaton => {
                add_stage_empty_actions(receiver, player, true);
                return;
            }
            ChoiceType::SelectLiveSlot => {
                add_indexed_actions(receiver, MAX_LIVE_SET_SIZE as usize, ACTION_BASE_CHOICE, |_| true);
                return;
            }
            ChoiceType::SelectSwapTarget => {
                let decoded_slot = DecodedSlot::decode(pi.target_slot);
                let target_zone = if decoded_slot.dest_zone == Zone::Default {
                    Zone::Discard
                } else {
                    decoded_slot.dest_zone
                };
                for (i, &cid) in collect_zone_cards(state, p_idx, target_zone).iter().enumerate() {
                    if cid >= 0
                        && state.card_matches_filter_with_ctx(db, cid, pi.filter_attr, &pi.ctx)
                    {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                return;
            }
            _ => {}
        }

        match opcode {
            O_TAP_MEMBER => {
                let decoded_slot = DecodedSlot::decode(pi.target_slot);
                let target_p_idx =
                    resolve_target_player_from_filter(decoded_slot, pi.filter, p_idx);
                Self::add_filtered_stage_actions(
                    receiver,
                    state,
                    db,
                    target_p_idx,
                    pi.filter_attr,
                    &pi.ctx,
                    true,
                );
                return;
            }
            O_TAP_OPPONENT => {
                let target_p_idx = 1 - (ctx.activator_id as usize);
                Self::add_filtered_stage_actions(
                    receiver,
                    state,
                    db,
                    target_p_idx,
                    pi.filter_attr,
                    &pi.ctx,
                    false,
                );
                return;
            }
            O_ORDER_DECK => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                receiver.add_action(
                    (crate::core::logic::ACTION_BASE_CHOICE
                        + crate::core::logic::constants::CHOICE_DONE as i32)
                        as usize,
                );
                return;
            }
            O_COLOR_SELECT => {
                let mut choices_to_show = vec![0, 1, 2, 3, 4, 5]; // Default to all 6 explicit colors

                // Check if color_mask is set in filter_attr to restrict choices
                let color_mask = ((pi.filter_attr >> FILTER_COLOR_SHIFT_R5) & 0x7F) as u8;
                if color_mask != 0 {
                    // Filter choices based on color_mask bits (0-6 for hearts 1-7 including ANY)
                    choices_to_show = (0..7)
                        .filter(|&c| (color_mask & (1 << c)) != 0)
                        .collect();
                }

                // Also try to extract from effect.params["choices"] if present (overrides color_mask)
                if let Some(abilities_list) = abilities {
                    if (pi.ability_index as usize) < abilities_list.len() {
                        let ability = &abilities_list[pi.ability_index as usize];
                        for effect in &ability.effects {
                            if effect.runtime_opcode == O_COLOR_SELECT {
                                if let Some(choices_val) = effect
                                    .params
                                    .get("choices")
                                    .or_else(|| effect.params.get("CHOICES"))
                                {
                                    if let Ok(choices_arr) =
                                        serde_json::from_value::<Vec<i32>>(choices_val.clone())
                                    {
                                        choices_to_show = choices_arr
                                            .into_iter()
                                            .filter(|&c| c >= 0 && c < 7)
                                            .collect();
                                    }
                                }
                                break;
                            }
                        }
                    }
                }

                for &c in &choices_to_show {
                    receiver.add_action((ACTION_BASE_COLOR + c) as usize);
                }
                return;
            }
            O_SET_TAPPED => {
                let resolved_slot = if (0..STAGE_SLOT_COUNT as i32).contains(&pi.target_slot) {
                    Some(pi.target_slot as usize)
                } else if (0..STAGE_SLOT_COUNT as i16).contains(&pi.ctx.area_idx) {
                    Some(pi.ctx.area_idx as usize)
                } else {
                    None
                };

                if let Some(slot_idx) = resolved_slot.filter(|slot_idx| player.stage[*slot_idx] >= 0) {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as usize);
                }
                if (pi.filter_attr & FILTER_IS_OPTIONAL) != 0 || pi.choice_type == ChoiceType::Optional {
                    receiver.add_action(0);
                }
                return;
            }
            O_LOOK_AND_CHOOSE => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
                }
                return;
            }
            O_MOVE_TO_DISCARD => {
                let masked_filter = pi.discard_selection_filter_attr();
                let decoded_slot =
                    crate::core::logic::interpreter::instruction::DecodedSlot::decode(
                        pi.target_slot,
                    );
                if !pi.is_hand_discard_prompt()
                    && decoded_slot.source_zone == crate::core::enums::Zone::Stage
                {
                    for (i, &cid) in player.stage.iter().enumerate() {
                        if cid >= 0
                            && state.card_matches_filter_with_ctx(db, cid, masked_filter, &pi.ctx)
                        {
                            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                        }
                    }
                } else {
                    for (i, &cid) in player.hand.iter().enumerate() {
                        let hand_slot = (p_idx as u8, 200 + i as i16);
                        if state.card_matches_filter_with_ctx_at_slot(
                            db,
                            cid,
                            masked_filter,
                            hand_slot,
                            &pi.ctx,
                        ) {
                            receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                        }
                    }
                }
                if (pi.filter_attr & FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
                return;
            }
            O_RECOVER_MEMBER | O_RECOVER_LIVE => {
                let count = player.looked_cards.len();
                let is_live_recovery = opcode == O_RECOVER_LIVE;
                for i in 0..count {
                    let cid = player.looked_cards[i];
                    if cid != -1
                        && ((is_live_recovery && db.get_live(cid).is_some())
                            || (!is_live_recovery && db.get_member(cid).is_some()))
                        && state.card_matches_filter_with_ctx(db, cid, pi.filter_attr, &pi.ctx)
                    {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
                }
                return;
            }
            O_PLAY_MEMBER_FROM_HAND => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, pi.filter_attr) {
                        receiver.add_action((ACTION_BASE_HAND + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(0);
                }
                return;
            }
            O_PLAY_MEMBER_FROM_DISCARD | O_PLAY_LIVE_FROM_DISCARD => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
                }
                return;
            }
            O_SELECT_MEMBER => {
                if Self::is_position_change_prompt(pi) {
                    self.generate_position_change_destinations(
                        db, state, receiver, pi, abilities, p_idx,
                    );
                    return;
                }
                self.generate_select_member_actions(
                    db,
                    p_idx,
                    state,
                    receiver,
                    pi,
                    abilities,
                    pi.filter_attr,
                );
                return;
            }
            O_SELECT_LIVE => {
                for (i, &cid) in player.live_zone.iter().enumerate() {
                    if cid >= 0 {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(0);
                }
                return;
            }
            O_SELECT_PLAYER => {
                receiver.add_action(0);
                receiver.add_action(1);
                return;
            }
            O_SELECT_MODE => {
                self.generate_select_mode_actions(db, p_idx, state, receiver, pi, abilities);
                return;
            }
            O_OPPONENT_CHOOSE => {
                self.generate_select_mode_actions(db, p_idx, state, receiver, pi, abilities);
                return;
            }
            O_SELECT_CARDS => {
                if state.debug.debug_mode || env_flag_enabled("TRACE_SELECT_CARDS_FLOW") {
                    eprintln!(
                        "[SELECT_CARDS_FLOW] looked_cards={:?} filter_attr={:#x} choice_type={:?} effect_opcode={} target_slot={} source_zone={:?} trigger={:?}",
                        player.looked_cards,
                        pi.filter_attr,
                        pi.choice_type,
                        pi.effect_opcode,
                        pi.target_slot,
                        DecodedSlot::decode(pi.target_slot).source_zone,
                        pi.ctx.trigger_type
                    );
                }
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
                }
                return;
            }
            O_LOOK_REORDER_DISCARD => {
                // This uses SELECT_CARDS_ORDER choice type
                // Similar to O_ORDER_DECK, we present the looked cards for selection/ordering
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                // Also add a "Done" action (99) to finalize the order if optional or once selections are complete
                receiver.add_action(
                    (crate::core::logic::ACTION_BASE_CHOICE
                        + crate::core::logic::constants::CHOICE_DONE as i32)
                        as usize,
                );
                return;
            }
            _ => {
                if choice_type == ChoiceType::SelectMember || choice_type == ChoiceType::TapMSelect
                {
                    self.generate_select_member_actions(
                        db,
                        p_idx,
                        state,
                        receiver,
                        pi,
                        abilities,
                        pi.filter_attr,
                    );
                    return;
                }
                if choice_type == ChoiceType::SelectStage {
                    add_stage_slot_actions(receiver, player, true);
                    return;
                }
                if choice_type == ChoiceType::LookAndChoose {
                    self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                    if optional_skip_is_available(pi) {
                        add_optional_done(receiver);
                    }
                    return;
                }
                if choice_type == ChoiceType::MoveMemberDest {
                    let filter_attr = abilities
                        .and_then(|abs| {
                            let ab_idx_real = if pi.ability_index == -1 {
                                abs.iter()
                                    .position(|ab| {
                                        (ab.choice_flags
                                            & (CHOICE_FLAG_LOOK
                                                | CHOICE_FLAG_MODE
                                                | CHOICE_FLAG_COLOR
                                                | CHOICE_FLAG_ORDER))
                                            != 0
                                    })
                                    .unwrap_or(0)
                            } else {
                                pi.ability_index as usize
                            };

                            abs.get(ab_idx_real)
                        })
                        .and_then(|ab| Self::effect_filter_attr_for_opcode(ab, O_MOVE_MEMBER))
                        .unwrap_or(
                            pi.filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK,
                        );
                    let source_slot = if pi.ctx.area_idx >= 0 && pi.ctx.area_idx < STAGE_SLOT_COUNT as i16 {
                        Some(pi.ctx.area_idx as usize)
                    } else {
                        player
                            .stage
                            .iter()
                            .position(|&cid| cid == pi.ctx.source_card_id)
                            .or_else(|| {
                                state.players[p_idx]
                                    .stage
                                    .iter()
                                    .position(|&cid| cid == pi.ctx.source_card_id)
                            })
                    };
                    let mut added_dest = false;
                    for i in 0..STAGE_SLOT_COUNT {
                        let cid = player.stage[i];
                        if source_slot != Some(i)
                            && cid >= 0
                            && state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx)
                        {
                            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                            added_dest = true;
                        }
                    }
                    if !added_dest {
                        receiver.add_action(0);
                    }
                    return;
                }
                if choice_type == ChoiceType::SelectLiveSlot {
                    for i in 0..player.live_zone.len().min(10) {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                    return;
                }
            }
        }

        if offer_optional_skip {
            receiver.add_action(0);
        }
    }
}

impl ResponseGenerator {
    fn generate_look_and_choose_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        abilities: Option<&Vec<Ability>>,
    ) {
        let player = &state.players[p_idx];
        let uses_select_mode_look_deck_prompt = abilities
            .and_then(|abs| {
                let ab_idx_real = if pi.ability_index == -1 {
                    abs.iter()
                        .position(|ab| {
                            (ab.choice_flags
                                & (CHOICE_FLAG_LOOK
                                    | CHOICE_FLAG_MODE
                                    | CHOICE_FLAG_COLOR
                                    | CHOICE_FLAG_ORDER))
                                != 0
                        })
                        .unwrap_or(0)
                } else {
                    pi.ability_index as usize
                };

                abs.get(ab_idx_real)
            })
            .map(|ab| {
                let has_look_and_choose =
                    (ab.opcodes_mask & (1u128 << (O_LOOK_AND_CHOOSE as u32 % 128))) != 0;
                let has_look_deck = (ab.opcodes_mask & (1u128 << (O_LOOK_DECK as u32 % 128))) != 0;
                pi.effect_opcode == O_LOOK_AND_CHOOSE && has_look_deck && !has_look_and_choose
            })
            .unwrap_or(false);
        let mut final_filter_attr = if pi.effect_opcode == O_LOOK_DECK
            || (uses_select_mode_look_deck_prompt && pi.filter_attr == 0)
        {
            0
        } else {
            pi.filter_attr
        };
        final_filter_attr &= !crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL;
        match pi.choice_type {
            ChoiceType::SelectHandDiscard => {
                let decoded_slot = DecodedSlot::decode(pi.target_slot);
                let target_player = resolve_target_player_from_filter(
                    decoded_slot,
                    pi.filter,
                    pi.ctx.activator_id as usize,
                );
                let mut filter_ctx = pi.ctx.clone();
                filter_ctx.player_id = pi.ctx.activator_id;
                let hand_filter_attr = pi.discard_selection_filter_attr();
                let hand_filter = CardFilter::from_attr(hand_filter_attr);
                if pi.same_unit_discard {
                    add_same_unit_hand_discard_actions(
                        state,
                        db,
                        receiver,
                        state.players[target_player].hand.as_slice(),
                        hand_filter_attr,
                        &filter_ctx,
                        ACTION_BASE_HAND_SELECT,
                        pi,
                    );
                } else if hand_filter.special_id == 7 && pi.ctx.selected_cards.is_empty() {
                    add_same_group_hand_discard_actions(
                        state,
                        db,
                        receiver,
                        state.players[target_player].hand.as_slice(),
                        hand_filter_attr,
                        &filter_ctx,
                        ACTION_BASE_HAND_SELECT,
                        pi,
                    );
                } else {
                    add_cards_matching_filter(
                        state,
                        db,
                        receiver,
                        state.players[target_player].hand.as_slice(),
                        hand_filter_attr,
                        &filter_ctx,
                        ACTION_BASE_HAND_SELECT,
                    );
                    add_optional_done_if_available(receiver, pi);
                }
            }
            ChoiceType::SelectDiscardPlay => {
                add_cards_matching_filter(
                    state,
                    db,
                    receiver,
                    player.looked_cards.as_slice(),
                    final_filter_attr,
                    &pi.ctx,
                    ACTION_BASE_CHOICE,
                );
                add_optional_done_if_available(receiver, pi);
            }
            ChoiceType::SelectStage => {
                let requires_waiting_member = abilities
                    .and_then(|abs| {
                        let resolved_ab_idx = if pi.ability_index == -1 {
                            abs.iter()
                                .position(|ab| {
                                    (ab.choice_flags
                                        & (CHOICE_FLAG_LOOK
                                            | CHOICE_FLAG_MODE
                                            | CHOICE_FLAG_COLOR
                                            | CHOICE_FLAG_ORDER))
                                        != 0
                                })
                                .unwrap_or(0)
                        } else {
                            pi.ability_index as usize
                        };
                        abs.get(resolved_ab_idx)
                    })
                    .map(|ab| {
                        let mut next_opcode = None;
                        for frame_idx in
                            (pi.ctx.program_counter as usize + 1)..ab.resolved_frames().len()
                        {
                            let opcode = ab.resolved_frames()[frame_idx].opcode();
                            if matches!(opcode, O_JUMP | O_JUMP_IF_FALSE | O_NOP) {
                                continue;
                            }
                            next_opcode = Some(opcode);
                            break;
                        }
                        next_opcode == Some(O_ACTIVATE_MEMBER)
                    })
                    .unwrap_or(false);
                if state.debug.debug_mode || env_flag_enabled("TRACE_SELECT_STAGE_FLOW") {
                    eprintln!(
                        "[SELECT_STAGE_FLOW] pc={} choice_type={:?} effect_opcode={} ab_idx={} requires_waiting_member={} target_slot={} filter=[{}] stage={:?}",
                        pi.ctx.program_counter,
                        pi.choice_type,
                        pi.effect_opcode,
                        pi.ability_index,
                        requires_waiting_member,
                        pi.target_slot,
                        logging::describe_filter_bits(pi.filter_attr),
                        player.stage
                    );
                }
                for i in 0..STAGE_SLOT_COUNT {
                    let prevented = (player.prevent_play_to_slot_mask() & (1 << i)) != 0;
                    if requires_waiting_member && !player.is_tapped(i) {
                        continue;
                    }
                    let legal = match pi.effect_opcode {
                        O_PLAY_MEMBER_FROM_HAND => {
                            !prevented && !player.is_moved(i)
                        }
                        O_PLAY_MEMBER_FROM_DISCARD => {
                            !prevented && !player.is_moved(i)
                        }
                        _ => !prevented,
                    };
                    if legal {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
            }
            ChoiceType::SelectLiveSlot => {
                add_indexed_actions(
                    receiver,
                    player.live_zone.len().min(10),
                    ACTION_BASE_STAGE_SLOTS,
                    |i| player.live_zone[i] >= 0,
                );
            }
            ChoiceType::PayEnergy => {
                add_indexed_actions(
                    receiver,
                    player.energy_zone.len().min(10),
                    ACTION_BASE_ENERGY,
                    |i| {
                        pi.effect_opcode == O_PLACE_ENERGY_UNDER_MEMBER
                            || !player.is_energy_tapped(i)
                    },
                );
            }
            _ => {
                let masked_filter = final_filter_attr
                    & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
                let no_filter = masked_filter == 0;
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if cid != -1
                        && (no_filter
                        || state.card_matches_filter_with_ctx(
                            db,
                            cid,
                            masked_filter,
                            &pi.ctx,
                        ))
                    {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                if pi.choice_type == ChoiceType::LookAndChoose && !player.looked_cards.is_empty()
                {
                    add_optional_done(receiver);
                }
            }
        }
    }

    fn generate_select_member_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        abilities: Option<&Vec<Ability>>,
        filter_attr: u64,
    ) {
        if state.debug.debug_mode {
            println!(
                "[DEBUG] generate_select_member_actions: p_idx={}, filter=[{}]",
                p_idx,
                logging::describe_filter_bits(filter_attr)
            );
        }
        let mut filter_attr = filter_attr;
        let is_targeted_select_member_cost = Self::is_targeted_select_member_cost(db, pi);
        if is_targeted_select_member_cost {
            filter_attr = (filter_attr & !0x3) | 1;
        }
        let mut ab_idx_real = None;
        if let Some(abs) = abilities {
            let resolved_ab_idx = if pi.ability_index == -1 {
                abs.iter()
                    .position(|ab| {
                        (ab.choice_flags
                            & (CHOICE_FLAG_LOOK
                                | CHOICE_FLAG_MODE
                                | CHOICE_FLAG_COLOR
                                | CHOICE_FLAG_ORDER))
                            != 0
                    })
                    .unwrap_or(0)
            } else {
                pi.ability_index as usize
            };
            ab_idx_real = Some(resolved_ab_idx);

            if let Some(ab) = abs.get(resolved_ab_idx) {
                if filter_attr == 0 {
                    if let Some(frame) = ab.get_frame(pi.ctx.program_counter as usize) {
                        let components = frame.components();
                        if components.opcode == O_SELECT_MEMBER {
                            let frame_attr = components.targeted_select_member_filter_attr();
                            if frame_attr != 0 {
                                filter_attr = frame_attr;
                            }
                        }
                    }
                }
                if filter_attr == 0 {
                    if let Some(attr) = Self::effect_filter_attr_for_opcode(ab, O_SELECT_MEMBER) {
                        if attr != 0 {
                            filter_attr = attr;
                        }
                    }
                }
            }
        }
        let filter_only = filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
        let requires_waiting_member = abilities
            .and_then(|abs| ab_idx_real.and_then(|idx| abs.get(idx)))
            .map(|ab| {
                let mut next_opcode = None;
                for frame_idx in (pi.ctx.program_counter as usize + 1)..ab.resolved_frames().len() {
                    let opcode = ab.resolved_frames()[frame_idx].opcode();
                    if matches!(opcode, O_JUMP | O_JUMP_IF_FALSE | O_NOP) {
                        continue;
                    }
                    next_opcode = Some(opcode);
                    break;
                }
                next_opcode == Some(O_ACTIVATE_MEMBER)
            })
            .unwrap_or(false);

        let targeted_live_heart_bonus = pending_targeted_live_heart_bonus(db, pi).filter(|_| {
            pi.ctx.trigger_type == TriggerType::OnLiveStart
                && matches!(
                    pi.choice_type,
                    ChoiceType::SelectMember | ChoiceType::SelectHandDiscard
                )
        });

        if let Some((filter_attr, _heart_color_idx)) = targeted_live_heart_bonus {
            let mut added_any = false;
            for (i, &cid) in state.players[p_idx].stage.iter().enumerate() {
                if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx) {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    added_any = true;
                }
            }
            if added_any {
                receiver.add_action(0);
                return;
            }
        }
        let decoded_slot = DecodedSlot::decode(pi.target_slot);
        let target_player = if is_targeted_select_member_cost {
            p_idx
        } else {
            resolve_target_player_from_filter(decoded_slot, pi.filter, p_idx)
        };
        let player = &state.players[target_player];

        if is_targeted_select_member_cost {
            if add_matching_stage_actions(
                receiver,
                state,
                db,
                player,
                filter_only,
                &pi.ctx,
                true,
            ) {
                add_optional_done(receiver);
            }
            return;
        }

        let target_slot = if let Some(target_zone) = pi.selection_target_zone() {
            target_zone
        } else {
            if pi.effect_opcode == O_SELECT_MEMBER
                || pi.choice_type == ChoiceType::TapMSelect
                || (pi.choice_type == ChoiceType::SelectMember && pi.effect_opcode == 0)
            {
                decoded_slot.source_zone as usize
            } else {
                crate::core::logic::interpreter::resolve_target_slot(pi.effect_opcode, &pi.ctx)
            }
        };

        let filter_struct = (filter_only != 0).then(|| structured_filter_from_attr(filter_attr));
        let source_slot = if pi.ctx.area_idx >= 0 && pi.ctx.area_idx < STAGE_SLOT_COUNT as i16 {
            Some(pi.ctx.area_idx as usize)
        } else {
            player
                .stage
                .iter()
                .position(|&cid| cid == pi.ctx.source_card_id)
        };
        let hand_cards = player.hand.as_slice();
        let discard_cards = player.discard.as_slice();
        let stage_cards = player.stage.as_slice();
        if state.debug.debug_mode || env_flag_enabled("TRACE_SELECT_MEMBER_FLOW") {
            eprintln!(
                "[SELECT_MEMBER_FLOW] pc={} choice_type={:?} effect_opcode={} ab_idx={:?} target_player={} source_zone={:?} target_slot={} requires_waiting_member={} filter=[{}]",
                pi.ctx.program_counter,
                pi.choice_type,
                pi.effect_opcode,
                ab_idx_real,
                target_player,
                decoded_slot.source_zone,
                target_slot,
                requires_waiting_member,
                logging::describe_filter_bits(filter_attr)
            );
        }
        let selected_target_keys = &pi.ctx.selected_target_keys;
        let has_selected_target_keys = !selected_target_keys.is_empty();

        match target_slot {
            x if x == Zone::Hand as usize => {
                // Hand
                if filter_only == 0 {
                    add_indexed_actions(receiver, hand_cards.len(), ACTION_BASE_HAND_SELECT, |_| true);
                } else if let Some(filter_struct) = filter_struct.as_ref() {
                    add_indexed_actions(receiver, hand_cards.len(), ACTION_BASE_HAND_SELECT, |i| {
                        let cid = hand_cards[i];
                        filter_struct.matches(
                            state,
                            db,
                            cid,
                            Some((target_player as u8, i as i16)),
                            false,
                            None,
                            &pi.ctx,
                        )
                    });
                }
            }
            x if x == Zone::Discard as usize => {
                // Discard
                if filter_only == 0 {
                    add_indexed_actions(receiver, discard_cards.len(), ACTION_BASE_CHOICE, |_| true);
                } else if let Some(filter_struct) = filter_struct.as_ref() {
                    add_indexed_actions(receiver, discard_cards.len(), ACTION_BASE_CHOICE, |i| {
                        let cid = discard_cards[i];
                        filter_struct.matches(
                            state,
                            db,
                            cid,
                            Some((target_player as u8, i as i16)),
                            false,
                            None,
                            &pi.ctx,
                        )
                    });
                }
            }
            _ => {
                // Stage (0-2) or Default
                add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                    let cid = stage_cards.get(i).copied().unwrap_or(player.stage[i]);
                    if cid < 0
                        || (has_selected_target_keys
                            && selected_target_keys.contains(&selected_target_key(Zone::Stage, i)))
                    {
                        return false;
                    }
                    let is_waiting_member = state.players[target_player].is_tapped(i);
                    if requires_waiting_member && !is_waiting_member {
                        return false;
                    }
                    if filter_only == 0 {
                        return true;
                    }
                    if let Some(filter_struct) = filter_struct.as_ref() {
                        let effective_hearts = state
                            .get_effective_hearts(target_player, i, db, 0)
                            .to_array();
                        filter_struct.matches(
                            state,
                            db,
                            cid,
                            Some((target_player as u8, i as i16)),
                            is_waiting_member,
                            Some(&effective_hearts),
                            &pi.ctx,
                        )
                    } else {
                        true
                    }
                });
                if receiver.is_empty()
                    && filter_struct.as_ref().is_some_and(|filter_struct| filter_struct.special_id == 3)
                {
                    add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                        player.stage[i] >= 0
                            && source_slot != Some(i)
                            && (!requires_waiting_member || state.players[target_player].is_tapped(i))
                    });
                }
                if receiver.is_empty()
                    && filter_only != 0
                    && !requires_waiting_member
                    && pi.choice_type != ChoiceType::TapMSelect
                {
                    add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                        player.stage[i] >= 0
                    });
                }
            }
        }
        receiver.add_action(0);
    }

    fn generate_select_mode_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        abilities: Option<&Vec<Ability>>,
    ) {
        if let Some(mask) = pending_optional_mode_mask(db, pi) {
            if let Some(ability) = pending_live_ability(db, pi) {
                for effect_idx in 0..ability.modal_option_count() {
                    let selected_bit = 1i16 << effect_idx;
                    if (mask & selected_bit) != 0 {
                        receiver.add_action((ACTION_BASE_MODE + effect_idx as i32) as usize);
                    }
                }
            } else {
                for effect_idx in 0..mask.count_ones() as i32 {
                    receiver.add_action((ACTION_BASE_MODE + effect_idx) as usize);
                }
            }
            return;
        }

        let count = abilities
            .and_then(|list| {
                usize::try_from(pi.ability_index)
                    .ok()
                    .and_then(|ability_index| list.get(ability_index))
                    .map(|ability| {
                        ability
                            .option_names
                            .len()
                            .max(ability.modal_option_count())
                            .max(pi.v_remaining.max(0) as usize)
                    })
            })
            .unwrap_or_else(|| pi.v_remaining.max(0) as usize)
            .max(1);
        if let Some(ability) = abilities.and_then(|list| {
            usize::try_from(pi.ability_index)
                .ok()
                .and_then(|ability_index| list.get(ability_index))
        }) {
            let option_count = count.max(ability.modal_option_count());
            for option_idx in 0..option_count {
                if modal_option_is_legal(db, state, p_idx, ability, option_idx) {
                    receiver.add_action((ACTION_BASE_MODE + option_idx as i32) as usize);
                }
            }
            return;
        }
        for i in 0..count {
            receiver.add_action((ACTION_BASE_MODE + i as i32) as usize);
        }
    }
}
