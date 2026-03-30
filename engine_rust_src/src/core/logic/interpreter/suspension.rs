//! # Suspension and Choice Logic
//!
//! This module contains the logic for suspending execution for user input
//! and resolving target slots.

use crate::core::enums::ChoiceType;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::interpreter::logging;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PendingInteraction, Phase};

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
    if final_actions.is_empty() {
        let saved_phase = state.phase;
        let saved_current_player = state.current_player;
        state.phase = Phase::Response;
        state.current_player = chooser_p_idx;
        state.generate_legal_actions(db, chooser_p_idx as usize, &mut final_actions);
        state.phase = saved_phase;
        state.current_player = saved_current_player;
    }
    if choice_type == ChoiceType::Optional || choice_type == ChoiceType::PayEnergy || ctx.source_card_id == 4331 {
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
    if final_actions.is_empty()
        && matches!(
            choice_type,
            ChoiceType::SelectMember | ChoiceType::SelectStage
        )
    {
        for i in 0..3 {
            if state.players[chooser_p_idx as usize].stage[i] >= 0 {
                final_actions.push((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as i32);
            }
        }
    }
    if choice_type == ChoiceType::Optional
        && (final_actions.is_empty() || final_actions.iter().all(|action| *action == 0))
    {
        final_actions.clear();
        final_actions.push(crate::core::logic::ACTION_BASE_CHOICE as i32);
        final_actions.push(crate::core::logic::ACTION_BASE_CHOICE as i32 + 1);
    }

    let is_optional = choice_type == ChoiceType::Optional
        || (filter_attr & crate::core::logic::filter::FILTER_IS_OPTIONAL) != 0;
    let has_only_pass = final_actions.is_empty() || final_actions.iter().all(|action| *action == 0);
    if choice_type == ChoiceType::SelectMember
        && has_only_pass
        && (is_optional || ctx.source_card_id == 448)
    {
        return false;
    }
    if choice_type == ChoiceType::Optional && has_only_pass {
        return false;
    }

    state.interaction_stack.push(PendingInteraction {
        ctx: p_ctx,
        card_id: ctx.source_card_id,
        ability_index: ctx.ability_index,
        effect_opcode,
        target_slot,
        choice_type,
        filter_attr,
        choice_text: choice_text.to_string(),
        v_remaining,
        original_phase,
        original_current_player: original_cp,
        options: options.clone(),
        actions: final_actions.clone(),
        execution_id,
        ..Default::default()
    });
    if !state.ui.silent {
        state.log("Rule 11.2.2: Pushing new interaction to stack.".to_string());
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
    if target_slot == 4 && ctx.area_idx >= 0 {
        ctx.area_idx as usize
    } else if target_slot == -1 || target_slot == 4 {
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
