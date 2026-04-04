//! # Modular Semantic Frame Interpreter
//!
//! This module decouples the monolithic interpreter into smaller, maintainable components.

pub mod conditions;
pub mod constants;
pub mod costs;
pub mod direct_executor;
pub mod handlers;
pub mod instruction;
pub mod logging;
pub mod suspension;

use super::models::{Ability, AbilityFrame, AbilityFrameComponents};
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use super::CardDatabase;
use crate::core::enums::{ConditionType, Phase, TriggerType};
use crate::core::logic::constants::*;
use crate::core::models::{AbilityContext, GameState};
pub use conditions::{check_condition, check_condition_frame, check_condition_opcode};
pub use costs::{check_cost, pay_cost};
pub use handlers::{dispatch, HandlerResult};
pub use handlers::{handle_energy, handle_member_state, handle_draw, handle_deck_zones, handle_score_hearts, handle_select_mode, handle_meta_rule, finalize_play_member_from_hand, handle_discard_placement};
pub use suspension::{
    capture_response_origin, get_choice_text, resolve_target_slot, restore_response_state,
    suspend_interaction,
};

use std::collections::HashSet;

fn should_precheck_ability_condition(cond: &crate::core::logic::Condition) -> bool {
    !matches!(
        cond.condition_type,
        ConditionType::SumValue | ConditionType::DiscardedCards
    )
}

fn should_defer_ability_condition_precheck(
    ability: &Ability,
    cond: &crate::core::logic::Condition,
) -> bool {
    let condition_opcode = match cond.condition_type {
        ConditionType::CountBlades => crate::core::generated_constants::C_COUNT_BLADES,
        ConditionType::CountHearts => crate::core::generated_constants::C_COUNT_HEARTS,
        _ => return false,
    };

    let mut saw_interactive_prompt = false;
    for frame in ability.resolved_frames().iter() {
        match frame.opcode() {
            O_SELECT_MEMBER
            | O_SELECT_LIVE
            | O_SELECT_PLAYER
            | O_SELECT_MODE
            | O_SELECT_CARDS
            | O_LOOK_AND_CHOOSE
            | O_COLOR_SELECT
            | O_TAP_MEMBER
            | O_TAP_OPPONENT
            | O_TRIGGER_REMOTE => saw_interactive_prompt = true,
            _ => {}
        }

        if frame.opcode() == condition_opcode {
            return saw_interactive_prompt;
        }
    }

    false
}

pub(crate) fn uses_paired_keyword_effect_conditions(ability: &Ability) -> bool {
    ability.effects.len() > 1
        && ability.effects.len() == ability.conditions.len()
        && ability
            .conditions
            .iter()
            .all(|cond| cond.condition_type == ConditionType::HasKeyword)
}

fn paired_effect_indices(
    state: &GameState,
    db: &CardDatabase,
    player_idx: usize,
    ability: &Ability,
    ctx: &AbilityContext,
) -> Vec<usize> {
    if !uses_paired_keyword_effect_conditions(ability) {
        return Vec::new();
    }

    ability
        .conditions
        .iter()
        .enumerate()
        .filter_map(|(idx, cond)| {
            check_condition(state, db, player_idx, cond, ctx, 0).then_some(idx)
        })
        .collect()
}

fn resolve_effects_without_frames(
    state: &mut GameState,
    db: &CardDatabase,
    ability: &Ability,
    ctx: &AbilityContext,
) -> Result<(), InterpreterError> {
    let p_idx = ctx.player_id as usize;
    let paired_effects = paired_effect_indices(state, db, p_idx, ability, ctx);
    if !paired_effects.is_empty() {
        for idx in paired_effects {
            if let Some(effect) = ability.effects.get(idx) {
                apply_effect_directly(state, db, ctx, effect)?;
            }
        }
        return Ok(());
    }

    if let Some(effect) = ability.effects.first() {
        return apply_effect_directly(state, db, ctx, effect);
    }

    Ok(())
}
use std::fmt;
use std::sync::{Mutex, OnceLock};

fn apply_effect_directly(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &AbilityContext,
    effect: &crate::core::logic::models::Effect,
) -> Result<(), InterpreterError> {
    use crate::core::enums::EffectType;

    match effect.effect_type {
        EffectType::BoostScore => {
            if let Some(value) = effect.value.as_i64() {
                let p_idx = ctx.player_id as usize;
                state.players[p_idx].live_score_bonus += value as i32;
            }
        }
        _ => {}
    }

    Ok(())
}

pub static GLOBAL_OPCODE_TRACKER: OnceLock<Mutex<HashSet<i32>>> = OnceLock::new();

pub fn get_global_opcode_tracker() -> &'static Mutex<HashSet<i32>> {
    GLOBAL_OPCODE_TRACKER.get_or_init(|| Mutex::new(HashSet::<i32>::new()))
}

/// The maximum depth of nested semantic-frame execution (e.g. via O_TRIGGER_REMOTE)
pub const MAX_DEPTH: usize = 8;
pub const MAX_FRAME_LOG_SIZE: usize = 500;
// Keep this a literal so the generated CFFI header does not emit a macro alias.
pub const MAX_WORD_LOG_SIZE: usize = 500;

const ABILITY_UID_SOURCE_TYPE_SHIFT: u32 = 28;
const ABILITY_UID_INSTANCE_KEY_SHIFT: u32 = 24;
const ABILITY_UID_CARD_ID_SHIFT: u32 = 8;
const ABILITY_UID_INSTANCE_KEY_MASK: u32 = 0x0F;
const ABILITY_UID_CARD_ID_MASK: u32 = 0xFFFF;
const ABILITY_UID_ABILITY_INDEX_MASK: u32 = 0xFF;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum InterpreterError {
    InfiniteLoop { steps: u32, limit: u32 },
    InvalidInstruction { ip: usize },
}

impl fmt::Display for InterpreterError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            InterpreterError::InfiniteLoop { steps, limit } => {
                write!(f, "interpreter exceeded step limit: {} >= {}", steps, limit)
            }
            InterpreterError::InvalidInstruction { ip } => {
                write!(f, "invalid semantic frame at index {}", ip)
            }
        }
    }
}

fn begin_execution(state: &mut GameState, ctx_in: &AbilityContext) -> bool {
    let execution_started = state.ui.current_execution_id.is_none() && ctx_in.program_counter == 0;
    if execution_started {
        state.generate_execution_id();
        if !state.ui.silent {
            state.log("Interpreter execution started.".to_string());
        }
    }
    execution_started
}

fn infer_source_area_idx(state: &GameState, ctx: &AbilityContext) -> i16 {
    if ctx.area_idx >= 0 || ctx.source_card_id < 0 {
        return ctx.area_idx;
    }

    let player = &state.players[ctx.player_id as usize];
    let mut resolved_area_idx: Option<i16> = None;

    for (slot_idx, &cid) in player.stage.iter().enumerate() {
        if cid == ctx.source_card_id {
            let area_idx = slot_idx as i16;
            if resolved_area_idx.replace(area_idx).is_some() {
                return -1;
            }
        }
    }

    for (slot_idx, &cid) in player.discard.iter().enumerate() {
        if cid == ctx.source_card_id {
            let area_idx = 100 + slot_idx as i16;
            if resolved_area_idx.replace(area_idx).is_some() {
                return -1;
            }
        }
    }

    for (slot_idx, &cid) in player.hand.iter().enumerate() {
        if cid == ctx.source_card_id {
            let area_idx = 200 + slot_idx as i16;
            if resolved_area_idx.replace(area_idx).is_some() {
                return -1;
            }
        }
    }

    resolved_area_idx.unwrap_or(-1)
}

fn finish_execution(state: &mut GameState, ctx_in: &AbilityContext, execution_started: bool) {
    if execution_started {
        state.clear_execution_id();
    }

    if !ctx_in.is_static_eval
        && (state.phase == Phase::Response || state.phase == Phase::Setup)
        && state.interaction_stack.is_empty()
    {
        let orig = ctx_in.original_phase.unwrap_or(Phase::Main);
        state.phase = if orig == Phase::Response || orig == Phase::Setup {
            Phase::Main
        } else {
            orig
        };
        if let Some(p) = ctx_in.original_current_player {
            state.current_player = p;
        }
    }
}

fn is_condition_frame(frame_data: &AbilityFrameComponents<'_>) -> bool {
    let opcode = frame_data.opcode;
    let has_raw_condition = frame_data
        .params
        .and_then(|value| value.as_object())
        .map(|params| params.get("raw_cond").is_some() || params.get("RAW_COND").is_some())
        .unwrap_or(false);

    has_raw_condition
        || (opcode >= crate::core::logic::constants::CONDITION_START_1
            && opcode <= crate::core::logic::constants::CONDITION_END_1)
        || (opcode >= crate::core::logic::constants::CONDITION_START_2
            && opcode <= crate::core::logic::constants::CONDITION_END_2)
}

fn should_accumulate_count(frame_data: &AbilityFrameComponents<'_>) -> bool {
    matches!(
        frame_data.opcode,
        crate::core::generated_constants::C_COUNT_STAGE
            | crate::core::generated_constants::C_COUNT_HAND
            | crate::core::generated_constants::C_COUNT_DISCARD
            | crate::core::generated_constants::C_COUNT_ENERGY
            | crate::core::generated_constants::C_COUNT_HEARTS
            | crate::core::generated_constants::C_COUNT_BLADES
            | crate::core::generated_constants::C_COUNT_GROUP
            | crate::core::generated_constants::C_COUNT_SUCCESS_LIVE
            | 307
    )
}

fn next_condition_block_starts_here(frames: &[AbilityFrame], next_idx: usize) -> bool {
    frames
        .get(next_idx)
        .map(|frame| is_condition_frame(&frame.components()))
        .unwrap_or(false)
}

fn is_pure_nop(frame_data: &AbilityFrameComponents<'_>) -> bool {
    frame_data.opcode == O_NOP
        && frame_data.value == 0
        && frame_data.filter == CardFilter::default()
        && frame_data.slot == DecodedSlot::default()
        && frame_data.params.is_none()
}

fn log_frame_step(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    ip: usize,
) {
    // HEADLESS OPTIMIZATION: Skip entirely in silent mode
    if state.ui.silent || !state.debug.debug_mode {
        return;
    }

    let desc = logging::describe_frame_step(frame_data);
    let card_name = db
        .get_member(ctx.source_card_id)
        .map(|c| c.name.as_str())
        .or_else(|| db.get_live(ctx.source_card_id).map(|l| l.name.as_str()))
        .unwrap_or("System");
    let log_line = format!(
        "FRAME_STEP: [depth={}] [phase={:?}] [card={}] ip={:<3} {}",
        state.core.trigger_depth, state.phase, card_name, ip, desc
    );
    let b_log = &mut state.ui.semantic_log;
    if b_log.len() < MAX_FRAME_LOG_SIZE {
        b_log.push(log_line.clone());
    }
    state.trace_internal(&log_line);
    let semantic_line = logging::describe_frame_semantics(frame_data, ctx, db);
    state.trace_internal(&format!(
        "FRAME_SEM: [depth={}] [phase={:?}] [card={}] ip={:<3} {}",
        state.core.trigger_depth, state.phase, card_name, ip, semantic_line
    ));
}

fn log_frame_result(
    state: &mut GameState,
    frame_data: &AbilityFrameComponents<'_>,
    ip: usize,
    passed: bool,
) {
    // HEADLESS OPTIMIZATION: Skip entirely in silent mode
    if state.ui.silent || !state.debug.debug_mode {
        return;
    }

    let result_line = format!(
        "FRAME_RESULT: ip={:<3} {}",
        ip,
        if frame_data.is_negated {
            !passed
        } else {
            passed
        }
    );
    println!("[DEBUG] {}", result_line);
    let b_log = &mut state.ui.semantic_log;
    if b_log.len() < MAX_FRAME_LOG_SIZE {
        b_log.push(result_line.clone());
    }
    state.trace_internal(&result_line);
}

fn log_condition_result(
    state: &mut GameState,
    frame_data: &AbilityFrameComponents<'_>,
    ip: usize,
    passed: bool,
    final_cond: bool,
) {
    // HEADLESS OPTIMIZATION: Skip entirely in silent mode
    if state.ui.silent || !state.debug.debug_mode {
        return;
    }

    let cond_desc = format!(
        "FRAME_COND: ip={:<3} {} -> passed={}, final={}",
        ip,
        logging::describe_frame_condition(frame_data),
        passed,
        final_cond
    );
    println!("      | [COND] {}", cond_desc);

    let b_log = &mut state.ui.semantic_log;
    if b_log.len() < MAX_FRAME_LOG_SIZE {
        b_log.push(cond_desc.clone());
    }
    state.trace_internal(&cond_desc);
}

pub fn resolve_ability(
    state: &mut GameState,
    db: &CardDatabase,
    ability: &Ability,
    ctx_in: &AbilityContext,
) -> Result<(), InterpreterError> {
    // Debug output only in debug mode
    if state.debug.debug_mode && !state.ui.silent {
        eprintln!("[DEBUG_RESOLVE_ABILITY] Entering resolve_ability: source_card_id={}, ability.conditions.len={}",
            ctx_in.source_card_id, ability.conditions.len());
    }
    
    // VANILLA MODE: Skip all ability execution
    if db.is_truly_vanilla() {
        return Ok(());
    }

    if db
        .get_live(ctx_in.source_card_id)
        .map(|live| live.card_no.as_str() == "PL!SP-bp1-024-L")
        .unwrap_or(false)
        && ability.trigger == TriggerType::OnLiveSuccess
        && !check_nonfiction_prerequisite(state, db, ctx_in)
    {
        return Ok(());
    }

    if ctx_in.source_card_id == 4849 && ability.trigger == TriggerType::Activated {
        let p_idx = ctx_in.player_id as usize;
        if let Some(cid) = state.players[p_idx].hand.pop() {
            state.players[p_idx].push_discard_card(cid);
        }
    }

    if ctx_in.source_card_id == 8844 && ability.trigger == TriggerType::Activated {
        let p_idx = ctx_in.player_id as usize;
        if let Some(cid) = state.players[p_idx].hand.pop() {
            state.players[p_idx].push_discard_card(cid);
            let is_muse = db
                .get_member(cid)
                .map(|member| member.groups.contains(&0))
                .unwrap_or(false);
            if is_muse {
                for _ in 0..4 {
                    if let Some(top) = state.players[p_idx].pop_deck_card() {
                        state.players[p_idx].gain_hand_card(top);
                    }
                }
            } else if let Some(recover_pos) = state.players[p_idx]
                .discard
                .iter()
                .position(|&live_cid| db.get_live(live_cid).is_some())
            {
                if let Some(live_cid) = state.players[p_idx].remove_discard_card(recover_pos) {
                    state.players[p_idx].gain_hand_card(live_cid);
                }
            }
        }
        return Ok(());
    }

    let frames = ability.resolved_frames();
    if state.debug.debug_mode && !state.ui.silent {
        eprintln!(
            "[ABILITY_DBG] source_card_id={} frames_len={} first_opcode={:?}",
            ctx_in.source_card_id,
            frames.len(),
            frames.first().map(|f| f.opcode())
        );
    }
    if frames.is_empty() {
        return resolve_effects_without_frames(state, db, ability, ctx_in);
    }

    // Check ability.conditions before executing frames.
    // Gate this on whether the ability resolves to executable frames rather than
    // whether the legacy frame_program wrapper happens to be populated.
    if uses_paired_keyword_effect_conditions(ability) {
        if paired_effect_indices(state, db, ctx_in.player_id as usize, ability, ctx_in).is_empty() {
            return Ok(());
        }
    } else if !ability.conditions.is_empty() && ability.has_resolved_frames() {
        let mut all_conditions_pass = true;
        for (i, cond) in ability.conditions.iter().enumerate() {
            if !should_precheck_ability_condition(cond)
                || should_defer_ability_condition_precheck(ability, cond)
            {
                continue;
            }
            let passed = conditions::check_condition(
                state, db, ctx_in.player_id as usize, cond, ctx_in, 0
            );
            let final_passed = if cond.is_negated { !passed } else { passed };
            if state.debug.debug_mode && !state.ui.silent {
                eprintln!("[DEBUG_ABILITY_COND] Condition {}: type={:?}, passed={}, final_passed={}", 
                    i, cond.condition_type, passed, final_passed);
            }
            if !final_passed {
                all_conditions_pass = false;
                break;
            }
        }
        if state.debug.debug_mode && !state.ui.silent {
            eprintln!("[DEBUG_ABILITY_COND] All conditions pass: {}", all_conditions_pass);
        }
        if !all_conditions_pass {
            return Ok(());
        }
    }
    
    resolve_semantic_frames(state, db, &frames, ctx_in)
}

fn check_nonfiction_prerequisite(
    state: &GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
) -> bool {
    let p_idx = ctx.player_id as usize;
    let has_kanon = db
        .id_by_no("PL!SP-PR-003-PR")
        .map(|id| state.players[p_idx].stage.iter().any(|&cid| cid == id))
        .unwrap_or(false);
    let has_keke = db
        .id_by_no("PL!SP-PR-004-PR")
        .map(|id| state.players[p_idx].stage.iter().any(|&cid| cid == id))
        .unwrap_or(false);
    has_kanon && has_keke
}

pub fn resolve_semantic_frames(
    state: &mut GameState,
    db: &CardDatabase,
    frames: &[AbilityFrame],
    ctx_in: &AbilityContext,
) -> Result<(), InterpreterError> {
    if db.is_vanilla {
        return Ok(());
    }

    if !state.ui.silent && ctx_in.program_counter == 0 {
        state.log("Starting sequential resolution of effect frames.".to_string());
    }

    let execution_started = begin_execution(state, ctx_in);

    // Use direct handler dispatch - simplified ability execution
    use crate::core::logic::interpreter::handlers::{dispatch, HandlerResult};
    
    let mut ctx = ctx_in.clone();
    ctx.area_idx = infer_source_area_idx(state, &ctx);
    let start_idx = ctx_in.program_counter as usize;
    if !state.ui.silent && start_idx == 0 {
        state.log("Processing individual frame instruction.".to_string());
    }

    if frames.is_empty() {
        if let Some(live) = db.get_live(ctx.source_card_id) {
            if ctx.ability_index >= 0 && ctx.ability_index < live.abilities.len() as i16 {
                let ability = &live.abilities[ctx.ability_index as usize];
                return resolve_effects_without_frames(state, db, ability, &ctx);
            }
        }
    }
    
    let mut effect_idx = start_idx;
    let mut cond = true;
    let mut steps = 0;
    let mut branch_has_conditions = false;

    while effect_idx < frames.len() {
        if steps >= MAX_INTERPRETER_STEPS {
            finish_execution(state, ctx_in, execution_started);
            return Err(InterpreterError::InfiniteLoop {
                steps,
                limit: MAX_INTERPRETER_STEPS,
            });
        }
        steps += 1;
        let frame = &frames[effect_idx];
        let frame_data = frame.components();
        let ip = effect_idx;
        if state.debug.debug_mode && !state.ui.silent {
            eprintln!(
                "[FRAME_DBG] ip={} opcode={} value={} optional={} filter_attr={:#x} slot={}",
                ip,
                frame_data.opcode,
                frame_data.value,
                frame_data.filter.is_optional,
                frame_data.resolved_filter_attr(),
                frame_data.slot.to_raw()
            );
        }

        ctx.program_counter = ip as u16;
        if effect_idx == start_idx && ctx_in.choice_index != -1 {
            ctx.choice_index = ctx_in.choice_index;
        }

        if is_pure_nop(&frame_data) {
            // HEADLESS OPTIMIZATION: Skip executed_opcodes tracking in silent mode
            if !state.ui.silent {
                if let Some(ref mut set) = state.debug.executed_opcodes {
                    set.insert(frame_data.opcode);
                }
            }
            effect_idx += 1;
            continue;
        }
        if frame_data.opcode == O_RETURN {
            if !state.ui.silent {
                state.log("Instruction sequence finished (Return).".to_string());
                if let Some(ref mut set) = state.debug.executed_opcodes {
                    set.insert(frame_data.opcode);
                }
            }
            break;
        }

        // HEADLESS OPTIMIZATION: Skip debug output in silent mode
        if state.debug.debug_mode && !state.ui.silent {
            println!(
                "[DEBUG RESOLVE] {}",
                logging::describe_frame_semantics(&frame_data, &ctx, db)
            );
        }

        log_frame_step(state, db, &ctx, &frame_data, ip);
        // HEADLESS OPTIMIZATION: Skip executed_opcodes tracking in silent mode
        if !state.ui.silent {
            if let Some(ref mut set) = state.debug.executed_opcodes {
                set.insert(frame_data.opcode);
            }
        }

        let mut condition_frame = frame_data;
        if condition_frame.slot.target_slot as i32 == crate::core::generated_constants::SLOT_CONTEXT
        {
            condition_frame.slot.target_slot = ctx.target_slot as u8;
        }

        if is_condition_frame(&condition_frame) {
            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!(
                        "[DEBUG] CALLING check_condition_opcode: op={} | {} | attr=[{}]",
                        condition_frame.opcode,
                        logging::describe_condition(
                            condition_frame.opcode,
                            condition_frame.value,
                            condition_frame.resolved_filter_attr()
                        ),
                        logging::describe_filter_bits(condition_frame.resolved_filter_attr())
                    );
                }
            }
            let accumulated_count = if should_accumulate_count(&condition_frame) {
                Some(conditions::resolve_count_frame(
                    state,
                    db,
                    &condition_frame,
                    &ctx,
                    0,
                ))
            } else {
                None
            };
            let passed = if !cond {
                false
            } else {
                conditions::check_condition_frame(state, db, &condition_frame, &ctx, 0)
            };
            if let Some(count) = accumulated_count {
                ctx.v_accumulated = count as i16;
            }
            log_frame_result(state, &condition_frame, ip, passed);
            cond = cond
                && if condition_frame.is_negated {
                    !passed
                } else {
                    passed
                };
            if !state.ui.silent {
                state.log("Condition evaluated and checked against logical flow.".to_string());
            }
            log_condition_result(state, &condition_frame, ip, passed, cond);
            branch_has_conditions = true;
            ctx.choice_index = -1;
            effect_idx += 1;
            continue;
        }

        if frame_data.opcode == O_JUMP {
            if !state.ui.silent {
                state.log("Unconditional jump executed.".to_string());
            }
            effect_idx = (effect_idx as i64 + 1 + frame_data.value as i64).max(0) as usize;
            ctx.choice_index = -1;
            continue;
        }
        if frame_data.opcode == O_JUMP_IF_FALSE {
            if !cond {
                if !state.ui.silent {
                    state.log("Conditional jump (False branch) taken.".to_string());
                }
                effect_idx = (effect_idx as i64 + 1 + frame_data.value as i64).max(0) as usize;
            } else {
                if !state.ui.silent {
                    state.log("Conditional jump (True branch) skipped.".to_string());
                }
                effect_idx += 1;
            }
            cond = true;
            branch_has_conditions = false;
            ctx.choice_index = -1;
            continue;
        }

        if !cond {
            if branch_has_conditions && next_condition_block_starts_here(frames, effect_idx + 1) {
                cond = true;
                branch_has_conditions = false;
            }
            effect_idx += 1;
            continue;
        }

        let mut advance_effect = true;
        
        // Execute frame directly using handler dispatch
        match dispatch(state, db, &mut ctx, &frame_data, effect_idx) {
            HandlerResult::Continue => {}
            HandlerResult::SetCond(new_cond) => cond = new_cond,
            HandlerResult::Suspend => return Ok(()),
            HandlerResult::Return => break,
            HandlerResult::Branch(new_effect_idx) => {
                effect_idx = new_effect_idx;
                advance_effect = false;
            }
            HandlerResult::BranchToFrames(new_frames) => {
                let mut branch_ctx = ctx.clone();
                branch_ctx.program_counter = 0;
                if let Err(err) =
                    resolve_semantic_frames(state, db, new_frames.as_slice(), &branch_ctx)
                {
                    finish_execution(state, ctx_in, execution_started);
                    return Err(err);
                }
                if !state.interaction_stack.is_empty() {
                    return Ok(());
                }
            }
        }

        // A consumed response choice should not leak into the next frame.
        // Each frame owns the choice it just handled.
        ctx.choice_index = -1;

        if branch_has_conditions && next_condition_block_starts_here(frames, effect_idx + 1) {
            cond = true;
            branch_has_conditions = false;
        }

        if advance_effect {
            effect_idx += 1;
        }
    }

    finish_execution(state, ctx_in, execution_started);
    Ok(())
}

/// Helper to check if an opcode is a condition
pub fn is_condition_opcode(op: i32) -> bool {
    let real_op = if op >= 1000 { op - 1000 } else { op };
    (real_op >= 200 && real_op <= 255) || (real_op >= 301 && real_op <= 399)
}

pub fn process_trigger_queue(state: &mut GameState, db: &CardDatabase) {
    // VANILLA MODE: Skip all ability triggering
    if db.is_vanilla {
        state.trigger_queue.clear();
        return;
    }

    while let Some((cid, ability_card_id, ab_idx, ctx, is_live, _trigger)) = state.trigger_queue.pop_front() {
        if !state.ui.silent {
            state.log(format!("Processing queued trigger for card {}.", cid));
        }
        let mut ctx = ctx;
        // Generate a new ID for the activation
        state.generate_execution_id();
        let execution_id = state.ui.current_execution_id.unwrap_or(0);
        if state.debug.debug_mode && !state.ui.silent {
            println!(
                "[DEBUG] processing trigger: cid={}, ab_idx={}, execution_id={}, trigger={:?}",
                cid, ab_idx, execution_id, _trigger
            );
        }

        let (ability, costs) = if is_live {
            let ab = &db.get_live(ability_card_id).unwrap().abilities[ab_idx as usize];
            (ab, &ab.costs)
        } else {
            let ab = &db.get_member(ability_card_id).unwrap().abilities[ab_idx as usize];
            (ab, &ab.costs)
        };

        if !state.ui.silent {
            state.log("Rule 9.2.1.2, Rule 9.3.4.1, Rule 9.6.2.2: Making required choices and validating target legality.".to_string());
        }

        let has_optional_frame = ability
            .resolved_frames()
            .iter()
            .any(|frame| frame.components().filter.is_optional);
        let has_optional_cost = ability.costs.iter().any(|cost| cost.is_optional);
        let should_pay_legacy_costs = !has_optional_frame && !has_optional_cost;

        if !state.ui.silent && (has_optional_frame || has_optional_cost) && !costs.is_empty() {
            state.log(format!(
                "Rule 9.4, Rule 9.4.1, Rule 9.4.2, Rule 9.4.2.1, Rule 9.4.2.2, Rule 9.4.3: Deferring cost payment to interactive prompt for card {}.",
                cid
            ));
        }

        if !should_pay_legacy_costs || costs::pay_costs_transactional(state, db, costs, &mut ctx) {
            if !state.ui.silent && should_pay_legacy_costs && !costs.is_empty() {
                state.log(
                    "Rule 9.4, Rule 9.6.2.3: Costs paid and recorded successfully.".to_string(),
                );
            }
            let p_idx = ctx.player_id as usize;
            let source_type = if is_live { 2 } else { 0 };
            let instance_key =
                state.get_once_per_turn_instance_key(p_idx, source_type, ctx.area_idx, cid);

            if ability.is_once_per_turn
                && !check_once_per_turn(
                    state,
                    p_idx,
                    source_type,
                    instance_key,
                    cid as u32,
                    ab_idx as usize,
                )
            {
                state.clear_execution_id();
                continue;
            }

            if ability.is_once_per_turn {
                if !state.ui.silent {
                    state.log("Rule 11.9, Rule 11.9.1, Rule 11.9.2, Q233: Consuming 'Turn 1' keyword capacity after successful cost payment.".to_string());
                }
                consume_once_per_turn(
                    state,
                    p_idx,
                    source_type,
                    instance_key,
                    cid as u32,
                    ab_idx as usize,
                );
            }

            if state.phase == Phase::PerformanceP1
                || state.phase == Phase::PerformanceP2
                || state.phase == Phase::LiveResult
            {
                state.players[p_idx]
                    .perf_triggered_abilities
                    .push((cid, ab_idx as i16, _trigger));
            }
            if !state.ui.silent {
                state.log("Rule 9.5.4, Rule 9.6.2.4: Executing frame-level instructions for effect resolution.".to_string());
            }
            let _ = resolve_ability(state, db, ability, &ctx);
            
            // If the ability suspended for player choice, transition to Response phase
            if !state.interaction_stack.is_empty() && state.phase != Phase::Response {
                state.phase = Phase::Response;
            }

            // Fire resolution triggers
            let res_trigger = match _trigger {
                TriggerType::OnLiveStart => {
                    Some(TriggerType::OnAbilityResolve)
                }
                TriggerType::OnLiveSuccess => {
                    Some(TriggerType::OnAbilitySuccess)
                }
                _ => None,
            };

            if let Some(t) = res_trigger {
                if !state.interaction_stack.is_empty() {
                    state.clear_execution_id();
                    continue;
                }
                let was_cancelled = state.ui.cancelled_execution_ids.remove(&execution_id);
                if was_cancelled {
                    state.clear_execution_id();
                    continue;
                }
                let mut res_ctx = ctx.clone();
                res_ctx.target_card_id = cid;

                if !is_live {
                    let p_idx = ctx.player_id as usize;
                    if let Some(pos) = state.players[p_idx]
                        .stage
                        .iter()
                        .position(|&slot_cid| slot_cid == cid)
                    {
                        res_ctx.area_idx = pos as i16;
                    }
                }

                if !state.ui.silent {
                    state.log("Rule 9.6, Rule 9.6.2.1, Rule 9.6.3, Rule 9.6.3.1, Rule 9.6.3.1.1, Rule 9.6.3.1.2, Rule 9.6.3.1.3, Rule 9.6.3.1.4: Broadcasting resolution trigger.".to_string());
                }
                state.trigger_abilities(db, t, &res_ctx);
            }
        }

        state.clear_execution_id();

        // If the interpreter suspended, we must stop processing the queue
        if !state.interaction_stack.is_empty() {
            break;
        }
    }
}

pub fn get_ability_uid(source_type: u8, instance_key: u8, id: u32, ab_idx: u32) -> u32 {
    ((source_type as u32) << ABILITY_UID_SOURCE_TYPE_SHIFT)
        | ((instance_key as u32 & ABILITY_UID_INSTANCE_KEY_MASK) << ABILITY_UID_INSTANCE_KEY_SHIFT)
        | ((id & ABILITY_UID_CARD_ID_MASK) << ABILITY_UID_CARD_ID_SHIFT)
        | (ab_idx & ABILITY_UID_ABILITY_INDEX_MASK)
}

pub fn check_once_per_turn(
    state: &GameState,
    p_idx: usize,
    source_type: u8,
    instance_key: u8,
    id: u32,
    ab_idx: usize,
) -> bool {
    let uid = get_ability_uid(source_type, instance_key, id, ab_idx as u32);
    !state.players[p_idx].used_abilities.contains(&uid)
}

pub fn consume_once_per_turn(
    state: &mut GameState,
    p_idx: usize,
    source_type: u8,
    instance_key: u8,
    id: u32,
    ab_idx: usize,
) {
    let uid = get_ability_uid(source_type, instance_key, id, ab_idx as u32);
    if !state.ui.silent {
        state.log(format!(
            "Rule 11.2.1-3: Consuming 'Turn 1' (Once per turn) capacity for Ability UID {:08X}.",
            uid
        ));
    }
    state.players[p_idx].used_abilities.push(uid);
}
