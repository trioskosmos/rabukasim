use crate::core::enums::*;
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::handlers::state_helpers::tap_opponent_chooser_player;
use crate::core::O_TAP_MEMBER;

// =============================================================================
// CONSTANTS
// =============================================================================

/// Special value indicating "activate all" members
const ACTIVATE_ALL_VALUE: i32 = 99;

/// Attribute bit flags for tap operations
const ATTR_SELECT_MEMBER: i64 = 0x02;
const ATTR_OPTIONAL: i64 = 0x01;
const ATTR_TARGET_SLOT_ALL: i32 = 1;

/// Slot constants
const SLOT_USE_CONTEXT: i32 = 4;
const SLOT_INVALID: i32 = 3;

// =============================================================================
// ACTIVATE MEMBER
// =============================================================================

pub fn handle_activate_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    resolved_slot: i32,
    target_slot: i32,
    v: i32,
    a: i64,
) -> HandlerResult {
    let resolved_slot = resolve_slot_with_context(resolved_slot, ctx.area_idx);
    let group_bits = compute_group_bits(db, ctx.source_card_id);

    match determine_activation_mode(v, a, resolved_slot, target_slot) {
        ActivationMode::AllMatching => activate_all_matching(state, p_idx, a as u64, group_bits, db, ctx),
        ActivationMode::AllTapped => activate_all_tapped(state, p_idx, group_bits),
        ActivationMode::SingleSlot => activate_single_slot(state, p_idx, resolved_slot as usize, group_bits),
        ActivationMode::None => {}
    }

    HandlerResult::Continue
}

#[derive(Clone, Copy, Debug)]
enum ActivationMode {
    AllMatching,
    AllTapped,
    SingleSlot,
    None,
}

fn determine_activation_mode(v: i32, a: i64, resolved_slot: i32, target_slot: i32) -> ActivationMode {
    let activate_all = v == ACTIVATE_ALL_VALUE || (a != 0 && resolved_slot >= SLOT_INVALID);

    if activate_all {
        ActivationMode::AllMatching
    } else if target_slot == ATTR_TARGET_SLOT_ALL {
        ActivationMode::AllTapped
    } else if resolved_slot < SLOT_INVALID {
        ActivationMode::SingleSlot
    } else {
        ActivationMode::None
    }
}

fn resolve_slot_with_context(resolved_slot: i32, area_idx: i16) -> i32 {
    if resolved_slot == SLOT_USE_CONTEXT && area_idx >= 0 && area_idx < 3 {
        area_idx as i32
    } else {
        resolved_slot
    }
}

fn compute_group_bits(db: &CardDatabase, source_card_id: i32) -> u32 {
    db.get_member(source_card_id)
        .map(|card| {
            card.groups.iter()
                .filter(|&&g| g < 32)
                .fold(0u32, |acc, &g| acc | (1 << g))
        })
        .unwrap_or(0)
}

fn activate_all_matching(
    state: &mut GameState,
    p_idx: usize,
    filter_attr: u64,
    group_bits: u32,
    db: &CardDatabase,
    ctx: &AbilityContext,
) {
    for i in 0..3 {
        let cid = state.players[p_idx].stage[i];
        if cid < 0 { continue; }
        if filter_attr != 0 && !state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) { continue; }
        if state.players[p_idx].is_tapped(i) {
            state.players[p_idx].set_tapped(i, false);
            state.players[p_idx].activated_member_group_mask |= group_bits;
        }
    }
}

fn activate_all_tapped(state: &mut GameState, p_idx: usize, group_bits: u32) {
    for i in 0..3 {
        if state.players[p_idx].is_tapped(i) {
            state.players[p_idx].set_tapped(i, false);
            state.players[p_idx].activated_member_group_mask |= group_bits;
        }
    }
}

fn activate_single_slot(state: &mut GameState, p_idx: usize, slot: usize, group_bits: u32) {
    if state.players[p_idx].is_tapped(slot) {
        state.players[p_idx].set_tapped(slot, false);
        state.players[p_idx].activated_member_group_mask |= group_bits;
    }
}

// =============================================================================
// TAP MEMBER
// =============================================================================

pub fn handle_tap_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let frame_data = frame.components();
    let is_optional = frame_data.filter.is_optional;
    let is_select_member_choice = detect_select_member_choice(&frame_data);
    let self_source_is_on_stage = ctx.area_idx >= 0 && ctx.area_idx < 3;
    let filter_attr = compute_filter_attr(&frame_data);

    let resolved_slot = resolve_slot_with_context(resolved_slot, ctx.area_idx);

    if ctx.choice_index == -1 {
        handle_tap_prompt_phase(
            state, db, ctx, frame_idx, p_idx, resolved_slot, is_optional,
            is_select_member_choice, filter_attr, frame_data.value, a,
        )
    } else {
        handle_tap_selection_phase(
            state, ctx, p_idx, resolved_slot, is_optional, is_select_member_choice,
            self_source_is_on_stage, filter_attr, a, db,
        )
    }
}

fn detect_select_member_choice(frame_data: &crate::core::logic::models::AbilityFrameComponents) -> bool {
    frame_data.params.map(|params| {
        params.get("FILTER").is_some()
            || params.get("filter").is_some()
            || params.get("destination")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("target"))
                .unwrap_or(false)
            || params.get("cost_type_name")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("SELECT_MEMBER"))
                .unwrap_or(false)
    }).unwrap_or(false)
}

fn compute_filter_attr(frame_data: &crate::core::logic::models::AbilityFrameComponents) -> u64 {
    filter_attr_from_params(frame_data.params)
        .unwrap_or(frame_data.raw_attr.max(frame_data.filter.to_attr()))
        & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK
}

fn handle_tap_prompt_phase(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    p_idx: usize,
    resolved_slot: i32,
    is_optional: bool,
    is_select_member_choice: bool,
    filter_attr: u64,
    value: i32,
    a: i64,
) -> HandlerResult {
    // Optional choice flow
    if is_optional && ctx.v_remaining == -1 {
        return handle_optional_prompt(
            state, db, ctx, frame_idx, resolved_slot,
            is_select_member_choice, filter_attr, value, a, p_idx,
        );
    }

    // Direct selection or fixed slot
    let needs_member_selection = is_select_member_choice || (a & ATTR_SELECT_MEMBER) != 0;
    if needs_member_selection {
        return suspend_for_member_selection(state, db, ctx, frame_idx, 0, filter_attr, value);
    }

    if resolved_slot < SLOT_INVALID {
        state.players[p_idx].set_tapped(resolved_slot as usize, true);
        return HandlerResult::SetCond(true);
    }

    HandlerResult::Continue
}

fn handle_optional_prompt(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    resolved_slot: i32,
    is_select_member_choice: bool,
    filter_attr: u64,
    value: i32,
    a: i64,
    p_idx: usize,
) -> HandlerResult {
    // Choice already made: decline
    if ctx.choice_index == 1 {
        return HandlerResult::SetCond(false);
    }

    // Choice already made: accept
    if ctx.choice_index == 0 {
        ctx.choice_index = -1;
        let needs_selection = is_select_member_choice || (a & ATTR_SELECT_MEMBER) != 0;

        if needs_selection {
            ctx.v_remaining = value as i16;
            return suspend_for_member_selection(state, db, ctx, frame_idx, resolved_slot, filter_attr, value);
        }

        if resolved_slot < SLOT_INVALID {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::Continue;
    }

    // Initial prompt
    suspend_for_optional_choice(state, db, ctx, frame_idx, resolved_slot, filter_attr)
}

fn handle_tap_selection_phase(
    state: &mut GameState,
    ctx: &mut AbilityContext,
    p_idx: usize,
    resolved_slot: i32,
    is_optional: bool,
    is_select_member_choice: bool,
    self_source_is_on_stage: bool,
    filter_attr: u64,
    a: i64,
    db: &CardDatabase,
) -> HandlerResult {
    let is_choice_done = ctx.choice_index == CHOICE_DONE;
    let fixed_slot_matches = check_fixed_slot_matches(state, p_idx, resolved_slot, filter_attr, db, ctx);
    let needs_selection = is_select_member_choice || (a & ATTR_SELECT_MEMBER) != 0 || (!fixed_slot_matches && filter_attr != 0);

    // Validation checks
    if !self_source_is_on_stage && resolved_slot == SLOT_USE_CONTEXT && !needs_selection {
        return HandlerResult::SetCond(false);
    }

    if is_optional && !needs_selection && ctx.v_remaining == -1 {
        return HandlerResult::SetCond(false);
    }

    // Handle optional/skip logic
    if is_optional || (a & ATTR_OPTIONAL) != 0 {
        if is_optional && ctx.v_remaining != -1 {
            if ctx.choice_index >= 0 && ctx.choice_index < 3 {
                state.players[p_idx].set_tapped(ctx.choice_index as usize, true);
                return HandlerResult::SetCond(true);
            }
        }
        if is_choice_done || (ctx.v_remaining == -1 && ctx.choice_index == 1) {
            return HandlerResult::SetCond(false);
        }
    }

    // Apply tap to resolved slot
    if resolved_slot < SLOT_INVALID {
        state.players[p_idx].set_tapped(resolved_slot as usize, true);
    }

    HandlerResult::SetCond(true)
}

fn check_fixed_slot_matches(
    state: &GameState,
    p_idx: usize,
    resolved_slot: i32,
    filter_attr: u64,
    db: &CardDatabase,
    ctx: &AbilityContext,
) -> bool {
    if resolved_slot < 0 || resolved_slot >= SLOT_INVALID {
        return false;
    }
    let cid = state.players[p_idx].stage[resolved_slot as usize];
    cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
}

fn suspend_for_optional_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    resolved_slot: i32,
    filter_attr: u64,
) -> HandlerResult {
    if matches!(
        suspend_choice(state, db, ctx, ctx, frame_idx, O_TAP_MEMBER, resolved_slot, ChoiceType::Optional, filter_attr, -1),
        HandlerResult::Suspend
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}

fn suspend_for_member_selection(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    resolved_slot: i32,
    filter_attr: u64,
    value: i32,
) -> HandlerResult {
    if matches!(
        suspend_choice(state, db, ctx, ctx, frame_idx, O_TAP_MEMBER, resolved_slot, ChoiceType::TapMSelect, filter_attr, value as i16),
        HandlerResult::Suspend
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}

// =============================================================================
// SET TAPPED
// =============================================================================

pub fn handle_set_tapped(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    resolved_slot: i32,
) -> HandlerResult {
    let frame_data = frame.components();
    let is_optional = frame_data.filter.is_optional;

    trace_set_tapped(state, p_idx, resolved_slot, frame_data.value, is_optional, ctx);

    // Handle decline
    if is_optional && ctx.v_remaining == -1 && ctx.choice_index == 1 {
        cancel_execution(state);
        return HandlerResult::Continue;
    }

    // Handle accept
    if is_optional && ctx.v_remaining == -1 && ctx.choice_index == 0 {
        apply_tap_state(state, p_idx, resolved_slot, frame_data.value != 0);
        ctx.choice_index = -1;
        return HandlerResult::Continue;
    }

    // Initial prompt
    if is_optional && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        return suspend_for_set_tapped_optional(state, db, ctx, frame_idx, resolved_slot, frame_data.raw_attr);
    }

    // Direct application
    let should_tap = frame_data.value != 0;
    let tap_slot = determine_tap_slot(is_optional, ctx, resolved_slot);

    if let Some(slot) = tap_slot {
        log_tap_action(state, p_idx, slot, should_tap);
        state.players[p_idx].set_tapped(slot, should_tap);
    }

    HandlerResult::Continue
}

fn trace_set_tapped(state: &GameState, p_idx: usize, resolved_slot: i32, value: i32, is_optional: bool, ctx: &AbilityContext) {
    if !state.ui.silent {
        eprintln!("[TRACE] SET_TAPPED: p_idx={} resolved_slot={} v={} optional={} {}",
            p_idx, resolved_slot, value, is_optional, logging::describe_context(ctx));
    }
}

fn cancel_execution(state: &mut GameState) {
    if let Some(execution_id) = state.ui.current_execution_id {
        state.ui.cancelled_execution_ids.insert(execution_id);
    }
}

fn determine_tap_slot(is_optional: bool, ctx: &AbilityContext, resolved_slot: i32) -> Option<usize> {
    if is_optional && ctx.v_remaining == -1 {
        (resolved_slot >= 0 && resolved_slot < SLOT_INVALID).then_some(resolved_slot as usize)
    } else if is_optional && ctx.choice_index >= 0 && ctx.choice_index < 3 {
        Some(ctx.choice_index as usize)
    } else if resolved_slot >= 0 && resolved_slot < SLOT_INVALID {
        Some(resolved_slot as usize)
    } else {
        None
    }
}

fn apply_tap_state(state: &mut GameState, p_idx: usize, resolved_slot: i32, should_tap: bool) {
    if resolved_slot >= 0 && resolved_slot < SLOT_INVALID {
        state.players[p_idx].set_tapped(resolved_slot as usize, should_tap);
    }
}

fn log_tap_action(state: &mut GameState, p_idx: usize, slot: usize, should_tap: bool) {
    if !state.ui.silent {
        let msg = if should_tap {
            format!("Rule 5.1, Rule 5.1.1: [メンバーをアピール済みにする] (Tapping) Member at Player {} Slot {}.", p_idx, slot + 1)
        } else {
            format!("Rule 5.2, Rule 5.2.1: [メンバーをアピール済みから元に戻す] (Untapping) Member at Player {} Slot {}.", p_idx, slot + 1)
        };
        state.log(msg);
    }
}

fn suspend_for_set_tapped_optional(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    resolved_slot: i32,
    raw_attr: u64,
) -> HandlerResult {
    if matches!(
        suspend_choice(state, db, ctx, ctx, frame_idx, crate::core::O_SET_TAPPED, resolved_slot, ChoiceType::Optional, raw_attr, -1),
        HandlerResult::Suspend
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}

// =============================================================================
// TAP OPPONENT
// =============================================================================

pub fn handle_tap_opponent(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _instr: &AbilityFrame,
    frame_idx: usize,
    a: i64,
    v: i32,
) -> HandlerResult {
    let target_p_idx = 1 - (ctx.activator_id as usize);
    let count = if ctx.v_remaining == -1 { v as i16 } else { ctx.v_remaining };

    if count <= 0 {
        return HandlerResult::Continue;
    }

    if ctx.choice_index == -1 {
        handle_tap_opponent_initial(state, db, ctx, frame_idx, target_p_idx, a, count)
    } else {
        handle_tap_opponent_selection(state, db, ctx, frame_idx, target_p_idx, count, a)
    }
}

fn handle_tap_opponent_initial(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    target_p_idx: usize,
    a: i64,
    count: i16,
) -> HandlerResult {
    let occupied_slots: Vec<usize> = state.players[target_p_idx]
        .stage.iter()
        .enumerate()
        .filter_map(|(idx, &cid)| (cid >= 0).then_some(idx))
        .collect();

    // Auto-select if only one target
    if occupied_slots.len() == 1 {
        state.set_member_tapped(target_p_idx, occupied_slots[0], true, db);
        return HandlerResult::Continue;
    }

    suspend_for_opponent_tap(state, db, ctx, frame_idx, a as u64, count)
}

fn handle_tap_opponent_selection(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    target_p_idx: usize,
    count: i16,
    a: i64,
) -> HandlerResult {
    let slot_idx = ctx.choice_index as usize;
    if slot_idx >= 3 {
        return HandlerResult::Continue;
    }

    state.set_member_tapped(target_p_idx, slot_idx, true, db);

    let next_count = count - 1;
    ctx.v_remaining = next_count;
    ctx.choice_index = -1;

    if next_count > 0 {
        return suspend_for_opponent_tap(state, db, ctx, frame_idx, a as u64, next_count);
    }

    HandlerResult::Continue
}

fn suspend_for_opponent_tap(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    filter_attr: u64,
    count: i16,
) -> HandlerResult {
    let mut choice_ctx = ctx.clone();
    choice_ctx.player_id = tap_opponent_chooser_player(db, ctx);

    if matches!(
        suspend_choice(state, db, &choice_ctx, &choice_ctx, frame_idx, crate::core::O_TAP_OPPONENT, 0, ChoiceType::TapO, filter_attr, count),
        HandlerResult::Suspend
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}
