//! # Suspension and Choice Logic
//!
//! This module contains the logic for suspending execution for user input
//! and resolving target slots.

use crate::core::enums::ChoiceType;
use crate::core::logic::constants::TARGET_SLOT_STAGE;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::filter::structured_filter_from_attr;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::interpreter::logging;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PendingInteraction, Phase};
use std::collections::HashMap;
use std::time::Instant;

fn suspend_profile_enabled() -> bool {
    std::env::var("BENCH_PROFILE_RESPONSE_ACTIONS")
        .ok()
        .map(|value| {
            let value = value.trim();
            !matches!(value, "0" | "false" | "FALSE" | "off" | "OFF")
        })
        .unwrap_or(false)
}

fn suspend_profile_threshold_us() -> u64 {
    std::env::var("BENCH_PROFILE_STEP_THRESHOLD_US")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(2000)
}

fn try_build_prefilled_actions(
    state: &GameState,
    db: &CardDatabase,
    chooser_p_idx: usize,
    effect_opcode: i32,
    target_slot: i32,
    choice_type: ChoiceType,
    filter_attr: u64,
    ctx: &AbilityContext,
) -> Option<Vec<i32>> {
    let optional = (filter_attr
        & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
        != 0
        || choice_type == ChoiceType::Optional;

    fn card_groups<'a>(db: &'a CardDatabase, cid: i32) -> Option<&'a [u8]> {
        db.get_member(cid)
            .map(|card| card.groups.as_slice())
            .or_else(|| db.get_live(cid).map(|card| card.groups.as_slice()))
    }

    fn same_group_partner_exists(db: &CardDatabase, hand: &[i32], idx: usize) -> bool {
        let Some(groups) = card_groups(db, hand[idx]) else {
            return false;
        };

        let mut counts = HashMap::<u8, usize>::new();
        for &cid in hand.iter() {
            if cid < 0 {
                continue;
            }
            if let Some(candidate_groups) = card_groups(db, cid) {
                for &group in candidate_groups {
                    *counts.entry(group).or_insert(0) += 1;
                }
            }
        }

        groups.iter().any(|group| counts.get(group).copied().unwrap_or(0) > 1)
    }

    match choice_type {
        ChoiceType::SelectHandDiscard
            if effect_opcode == crate::core::generated_constants::O_MOVE_TO_DISCARD => {
            let masked_filter = filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
            let filter = CardFilter::from_attr(masked_filter);
            let first_selected_groups = ctx
                .selected_cards
                .first()
                .and_then(|cid| card_groups(db, *cid))
                .map(|groups| groups.to_vec());
            let mut actions = Vec::new();

            for (idx, &cid) in state.players[chooser_p_idx].hand.iter().enumerate() {
                let hand_slot = (chooser_p_idx as u8, 200 + idx as i16);
                let same_group_ok = if ctx.selected_cards.is_empty() {
                    same_group_partner_exists(db, state.players[chooser_p_idx].hand.as_slice(), idx)
                } else if let Some(required_groups) = first_selected_groups.as_ref() {
                    card_groups(db, cid)
                        .map(|candidate_groups| {
                            candidate_groups
                                .iter()
                                .any(|candidate_group| required_groups.contains(candidate_group))
                        })
                        .unwrap_or(false)
                } else {
                    true
                };
                if !same_group_ok {
                    continue;
                }
                let mut candidate_filter = filter;
                candidate_filter.special_id = 0;
                let candidate_attr = candidate_filter.to_attr();
                if candidate_attr != 0
                    && !state.card_matches_filter_with_ctx_at_slot(
                        db,
                        cid,
                        candidate_attr,
                        hand_slot,
                        ctx,
                    )
                {
                    continue;
                }
                actions.push((crate::core::logic::ACTION_BASE_HAND_SELECT + idx as i32) as i32);
            }

            if actions.is_empty() {
                return None;
            }
            if optional {
                actions.push(0);
            }
            Some(actions)
        }
        ChoiceType::SelectDiscard
            if effect_opcode == crate::core::generated_constants::O_MOVE_TO_DISCARD => {
            let decoded_slot = DecodedSlot::decode(target_slot);
            if decoded_slot.source_zone != crate::core::enums::Zone::Stage {
                return None;
            }

            let target_player = resolve_target_player(decoded_slot, filter_attr, chooser_p_idx);
            let masked_filter = filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
            let mut actions = Vec::new();

            for (slot_idx, &cid) in state.players[target_player].stage.iter().enumerate() {
                if cid >= 0
                    && state.card_matches_filter_with_ctx(db, cid, masked_filter, ctx)
                {
                    actions.push((crate::core::logic::ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as i32);
                }
            }

            if actions.is_empty() {
                return None;
            }
            if optional {
                actions.push(0);
            }
            Some(actions)
        }
        ChoiceType::SelectMember if effect_opcode == crate::core::generated_constants::O_SELECT_MEMBER => {
            if !ctx.selected_target_keys.is_empty() {
                return None;
            }

            let requires_waiting_member = usize::try_from(ctx.ability_index)
                .ok()
                .and_then(|ability_idx| {
                    db.get_member(ctx.source_card_id)
                        .map(|card| &card.abilities)
                        .or_else(|| db.get_live(ctx.source_card_id).map(|card| &card.abilities))
                        .and_then(|abilities| abilities.get(ability_idx))
                })
                .and_then(|ability| {
                    ability
                        .resolved_frames()
                        .iter()
                        .skip(ctx.program_counter as usize + 1)
                        .find(|frame| {
                            !matches!(
                                frame.opcode(),
                                crate::core::generated_constants::O_JUMP
                                    | crate::core::generated_constants::O_JUMP_IF_FALSE
                                    | crate::core::generated_constants::O_NOP
                            )
                        })
                        .map(|frame| frame.opcode() == crate::core::generated_constants::O_ACTIVATE_MEMBER)
                })
                .unwrap_or(false);

            let decoded_slot = DecodedSlot::decode(target_slot);
            let target_player = resolve_target_player(decoded_slot, filter_attr, chooser_p_idx);
            let filter_attr =
                filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
            let filter_struct = (filter_attr != 0).then(|| structured_filter_from_attr(filter_attr));
            let mut actions = Vec::new();

            for slot_idx in 0..3 {
                let cid = state.players[target_player].stage[slot_idx];
                if cid < 0 {
                    continue;
                }
                if requires_waiting_member && !state.players[target_player].is_tapped(slot_idx) {
                    continue;
                }

                let matches = if let Some(filter_struct) = filter_struct.as_ref() {
                    let effective_hearts = state
                        .get_effective_hearts(target_player, slot_idx, db, 0)
                        .to_array();
                    filter_struct.matches(
                        state,
                        db,
                        cid,
                        Some((target_player as u8, slot_idx as i16)),
                        state.players[target_player].is_tapped(slot_idx),
                        Some(&effective_hearts),
                        ctx,
                    )
                } else {
                    true
                };

                if matches {
                    actions.push((crate::core::logic::ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as i32);
                }
            }

            if actions.is_empty() {
                return None;
            }
            if optional {
                actions.push(0);
            }
            Some(actions)
        }
        ChoiceType::LookAndChoose | ChoiceType::SelectDiscardPlay if matches!(
            effect_opcode,
            crate::core::generated_constants::O_LOOK_AND_CHOOSE
                | crate::core::generated_constants::O_PLAY_MEMBER_FROM_DISCARD
                | crate::core::generated_constants::O_PLAY_LIVE_FROM_DISCARD
                | crate::core::generated_constants::O_RECOVER_MEMBER
                | crate::core::generated_constants::O_RECOVER_LIVE
        ) => {
            let filter_attr =
                filter_attr & !crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL;
            let mut actions = Vec::new();

            for (idx, &cid) in state.players[chooser_p_idx].looked_cards.iter().enumerate() {
                if cid < 0 {
                    continue;
                }
                if filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
                    actions.push((crate::core::logic::ACTION_BASE_CHOICE + idx as i32) as i32);
                }
            }

            if actions.is_empty() {
                return None;
            }
            if optional {
                actions.push(0);
            }
            Some(actions)
        }
        _ => None,
    }
}

pub fn get_choice_text(db: &CardDatabase, ctx: &AbilityContext) -> String {
    crate::core::logic::ActionFactory::get_choice_text(db, ctx)
}

fn normalize_visible_phase(original_phase: Phase) -> Phase {
    if original_phase == Phase::Response || original_phase == Phase::Setup {
        Phase::Main
    } else {
        original_phase
    }
}

fn sync_interaction_phase(
    state: &mut GameState,
    original_phase: Phase,
    original_current_player: u8,
) {
    if let Some(player_id) = state.interaction_stack.last().map(|pi| pi.ctx.player_id) {
        state.phase = Phase::Response;
        state.current_player = player_id;
    } else {
        state.phase = normalize_visible_phase(original_phase);
        state.current_player = original_current_player;
        state.clear_execution_id();
    }
}

pub fn finish_pending_interaction(state: &mut GameState) {
    let popped = state.interaction_stack.pop();
    if !state.ui.silent && popped.is_some() {
        state.log("Rule 11.2.1: Popping interaction from stack (LIFO).".to_string());
    }
    let original_phase = popped
        .as_ref()
        .map(|pi| pi.original_phase)
        .unwrap_or(state.phase);
    let original_current_player = popped
        .as_ref()
        .map(|pi| pi.original_current_player)
        .unwrap_or(state.current_player);
    sync_interaction_phase(state, original_phase, original_current_player);
}

pub fn restore_response_state(
    state: &mut GameState,
    original_phase: Phase,
    original_current_player: u8,
) {
    sync_interaction_phase(state, original_phase, original_current_player);
}

pub fn capture_response_origin(state: &GameState) -> (Phase, u8) {
    if let Some(pi) = state
        .interaction_stack
        .iter()
        .find(|pi| pi.original_phase != Phase::Response && pi.original_phase != Phase::Setup)
    {
        (pi.original_phase, pi.original_current_player)
    } else if let Some(pi) = state.interaction_stack.last() {
        (pi.original_phase, pi.original_current_player)
    } else {
        (state.phase, state.current_player)
    }
}

#[allow(clippy::too_many_arguments)]
pub fn suspend_interaction(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    instr_ip: usize,
    effect_opcode: i32,
    target_slot: i32,
    choice_type: ChoiceType,
    choice_text: &str,
    filter_attr: u64,
    v_remaining: i16,
    options: Vec<serde_json::Value>,
    actions: Vec<i32>,
) -> bool {
    let store_ui_metadata = !(state.ui.silent && state.ui.headless);
    let original_phase = if let Some(p) = ctx.original_phase {
        p
    } else if state.phase == Phase::Response {
        state
            .interaction_stack
            .last()
            .map(|pi| pi.original_phase)
            .unwrap_or(state.phase)
    } else {
        state.phase
    };

    let original_cp = state.current_player;
    let execution_id = state.ui.current_execution_id.unwrap_or(0);

    let mut p_ctx = ctx.clone();
    p_ctx.program_counter = instr_ip as u16;
    p_ctx.choice_index = -1;
    p_ctx.v_remaining = v_remaining;
    p_ctx.original_phase = Some(original_phase);
    let chooser_p_idx = ctx.player_id;
    let mut final_actions = actions.clone();
    let profile_enabled = suspend_profile_enabled();
    let profile_start = profile_enabled.then(Instant::now);
    let _filter_cache_scope = crate::core::logic::game_rules_ext::FilterMatchCacheScope::activate();
    state.interaction_stack.push(PendingInteraction {
        ctx: p_ctx,
        card_id: ctx.source_card_id,
        ability_card_id: if ctx.ability_card_id >= 0 {
            ctx.ability_card_id
        } else {
            ctx.source_card_id
        },
        ability_index: ctx.ability_index,
        effect_opcode,
        target_slot,
        choice_type,
        filter: crate::core::logic::filter::structured_filter_from_attr(filter_attr),
        filter_attr,
        choice_text: if store_ui_metadata {
            choice_text.to_string()
        } else {
            String::new()
        },
        v_remaining,
        original_phase,
        original_current_player: original_cp,
        options: if store_ui_metadata {
            options.clone()
        } else {
            Vec::new()
        },
        actions: Vec::new(),
        execution_id,
        ..Default::default()
    });
    if !state.ui.silent {
        state.log("Rule 11.2.2: Pushing new interaction to stack.".to_string());
    }

    let mut action_gen_us = 0u64;
    let mut fast_prefill_us = 0u64;
    if final_actions.is_empty() {
        let fast_prefill_start = profile_enabled.then(Instant::now);
        if let Some(prefilled_actions) = try_build_prefilled_actions(
            state,
            db,
            chooser_p_idx as usize,
            effect_opcode,
            target_slot,
            choice_type,
            filter_attr,
            ctx,
        ) {
            final_actions = prefilled_actions;
        }
        fast_prefill_us = fast_prefill_start
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);
    }
    if final_actions.is_empty() {
        let action_gen_start = profile_enabled.then(Instant::now);
        let saved_phase = state.phase;
        let saved_current_player = state.current_player;
        state.phase = Phase::Response;
        state.current_player = chooser_p_idx;
        state.generate_legal_actions(db, chooser_p_idx as usize, &mut final_actions);
        state.phase = saved_phase;
        state.current_player = saved_current_player;
        action_gen_us = action_gen_start
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);
    }
    if let Some(profile_start) = profile_start {
        let total_us = profile_start.elapsed().as_nanos() as u64 / 1000;
        if total_us >= suspend_profile_threshold_us() || action_gen_us >= suspend_profile_threshold_us() {
            let pending_desc = state
                .interaction_stack
                .last()
                .map(logging::describe_pending_interaction)
                .unwrap_or_else(|| "pending[none]".to_string());
            println!(
                "[PROFILE] SuspendInteraction total_us={} fast_prefill_us={} action_gen_us={} chooser={} prefilled_actions={} generated_actions={} pending={}",
                total_us,
                fast_prefill_us,
                action_gen_us,
                chooser_p_idx,
                actions.len(),
                final_actions.len(),
                pending_desc
            );
        }
    }
    if state.debug.debug_mode {
        eprintln!(
            "[SUSP_DBG] choice_type={:?} actions={:?} final_actions={:?} has_only_pass={} phase={:?} cp={} choice_text={}",
            choice_type,
            actions,
            final_actions,
            final_actions.is_empty() || final_actions.iter().all(|action| *action == 0),
            state.phase,
            state.current_player,
            choice_text
        );
    }
    if final_actions.is_empty() && matches!(choice_type, ChoiceType::SelectStage) {
        for i in 0..3 {
            if state.players[chooser_p_idx as usize].stage[i] >= 0 {
                final_actions.push((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as i32);
            }
        }
    }
    if choice_type == ChoiceType::Optional
        && (final_actions.is_empty() || final_actions.iter().all(|action| *action == 0))
    {
        let decoded_slot = DecodedSlot::decode(target_slot);
        let is_hand_discard_prompt =
            effect_opcode == crate::core::logic::constants::O_MOVE_TO_DISCARD
                && decoded_slot.source_zone == crate::core::enums::Zone::Hand;
        if !is_hand_discard_prompt {
            final_actions.clear();
            final_actions.push(crate::core::logic::ACTION_BASE_CHOICE as i32);
            final_actions.push(crate::core::logic::ACTION_BASE_CHOICE as i32 + 1);
        }
    }

    let has_only_pass = final_actions.is_empty() || final_actions.iter().all(|action| *action == 0);
    let decoded_slot = DecodedSlot::decode(target_slot);
    let is_stage_member_prompt = matches!(
        decoded_slot.source_zone,
        crate::core::enums::Zone::Default | crate::core::enums::Zone::Stage
    );
    if state.debug.debug_mode
        && matches!(choice_type, ChoiceType::SelectCards | ChoiceType::SelectDiscardPlay)
    {
        eprintln!(
            "[SUSP_SELECT_CARDS] op={} choice_type={:?} decoded_source={:?} has_only_pass={} final_actions={:?} filter_attr={:#x} v_remaining={}",
            effect_opcode,
            choice_type,
            decoded_slot.source_zone,
            has_only_pass,
            final_actions,
            filter_attr,
            v_remaining
        );
    }
    if choice_type == ChoiceType::SelectMember && is_stage_member_prompt && has_only_pass {
        state.interaction_stack.pop();
        return false;
    }
    if choice_type == ChoiceType::Optional && has_only_pass {
        let is_hand_discard_prompt =
            effect_opcode == crate::core::logic::constants::O_MOVE_TO_DISCARD
                && decoded_slot.source_zone == crate::core::enums::Zone::Hand;
        if is_hand_discard_prompt {
            state.interaction_stack.last_mut().unwrap().actions = final_actions.clone();
            return false;
        }
        state.interaction_stack.pop();
        return false;
    }
    if state.debug.debug_mode {
        if let Some(interaction) = state.interaction_stack.last() {
            state.trace_internal(&format!(
                "FRAME_SUSPEND: [phase={:?}] {}",
                state.phase,
                logging::describe_pending_interaction(interaction)
            ));
        }
    }
    state.interaction_stack.last_mut().unwrap().actions = final_actions.clone();

    if state.debug.debug_mode {
        state.trace_internal(&format!(
            "FRAME_SUSPEND_ACTIONS: choice_type={:?} len={} chooser={}",
            choice_type,
            final_actions.len(),
            chooser_p_idx
        ));
    }

    state.phase = Phase::Response;
    state.current_player = chooser_p_idx;

    true
}

/// Resolves the effective slot index based on the opcode's target_slot and the current context.
/// Slot 4 often acts as a proxy for the 'Area Index' stored in the context.
pub fn resolve_target_slot(target_slot: i32, ctx: &AbilityContext) -> usize {
    if target_slot == 0 && ctx.target_slot >= 0 {
        return ctx.target_slot as usize;
    }
    if target_slot == TARGET_SLOT_STAGE as i32 && ctx.area_idx >= 0 {
        ctx.area_idx as usize
    } else if target_slot == -1 || target_slot == TARGET_SLOT_STAGE as i32 {
        if ctx.area_idx >= 0 {
            ctx.area_idx as usize
        } else {
            0
        }
    } else {
        target_slot.max(0) as usize
    }
}

/// Resolves which player a selection prompt should operate on from semantic slot/filter data.
pub fn resolve_target_player(
    decoded_slot: DecodedSlot,
    filter_attr: u64,
    default_player: usize,
) -> usize {
    let raw_target = (filter_attr & 0x3) as u8;

    if decoded_slot.is_opponent || decoded_slot.target_slot == 2 || raw_target == 2 {
        1 - default_player
    } else {
        default_player
    }
}

pub fn resolve_target_player_from_filter(
    decoded_slot: DecodedSlot,
    filter: CardFilter,
    default_player: usize,
) -> usize {
    if decoded_slot.is_opponent || decoded_slot.target_slot == 2 || filter.target_player == 2 {
        1 - default_player
    } else {
        default_player
    }
}
