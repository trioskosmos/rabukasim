//! # Modular Bytecode Interpreter
//!
//! This module decouples the monolithic interpreter into smaller, maintainable components.

pub mod conditions;
pub mod constants;
pub mod costs;
pub mod handlers;
pub mod logging;
pub mod instruction;
pub mod suspension;

use crate::core::enums::Phase;
use crate::core::models::{GameState, AbilityContext};
use crate::core::logic::constants::*;
use super::CardDatabase;
use super::models::{Ability, AbilityFrame};
use self::instruction::BytecodeProgram;
pub use conditions::{check_condition, check_condition_opcode};
pub use costs::{check_cost, pay_cost};
pub use handlers::{HandlerRegistry, HandlerResult};
pub use suspension::{get_choice_text, resolve_target_slot, suspend_interaction};

use std::collections::HashSet;
use std::fmt;
use std::sync::{Arc, Mutex, OnceLock};

pub static GLOBAL_OPCODE_TRACKER: OnceLock<Mutex<HashSet<i32>>> = OnceLock::new();

pub fn get_global_opcode_tracker() -> &'static Mutex<HashSet<i32>> {
    GLOBAL_OPCODE_TRACKER.get_or_init(|| Mutex::new(HashSet::<i32>::new()))
}

// fn log_opcode_to_file(_op: i32) {
//     use std::io::Write;
//     let thread_name = std::thread::current().name().unwrap_or("unknown").to_string();
//     if let Ok(mut file) = std::fs::OpenOptions::new()
//         .create(true)
//         .append(true)
//         .open("reports/telemetry_raw.log")
//     {
//         let _ = writeln!(file, "[OPCODE] {} | Test: {}", _op, thread_name);
//     }
// }

/// The maximum depth of nested bytecode execution (e.g. via O_TRIGGER_REMOTE)
pub const MAX_DEPTH: usize = 8;
pub const MAX_BYTECODE_LOG_SIZE: usize = 500;

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
                write!(f, "invalid bytecode instruction at ip {}", ip)
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

fn finish_execution(state: &mut GameState, ctx_in: &AbilityContext, execution_started: bool) {
    state.players[ctx_in.player_id as usize].revealed_cards.clear();

    if execution_started {
        state.clear_execution_id();
    }

    if (state.phase == Phase::Response || state.phase == Phase::Setup)
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

struct ExecutionFrame {
    program: BytecodeProgram,
    ip: usize,
    ctx: AbilityContext,
}

struct BytecodeExecutor {
    stack: Vec<ExecutionFrame>,
    cond: bool,
    steps: u32,
}

pub fn resolve_ability(
    state: &mut GameState,
    db: &CardDatabase,
    ability: &Ability,
    ctx_in: &AbilityContext,
) -> Result<(), InterpreterError> {
    // VANILLA MODE: Skip all ability execution
    if db.is_truly_vanilla() {
        return Ok(());
    }

    if let Some(frame_prog) = &ability.frame_program {
        return resolve_semantic_frames(state, db, &frame_prog.frames, ctx_in);
    }

    if let Some(sparse) = &ability.sparse_frame_index {
        let frame_prog = CardDatabase::sparse_entry_to_frame_program(sparse);
        if !frame_prog.frames.is_empty() {
            return resolve_semantic_frames(state, db, &frame_prog.frames, ctx_in);
        }
    }

    let frame_prog = crate::core::logic::models::FrameProgram::from_bytecode(&ability.bytecode());
    resolve_semantic_frames(state, db, &frame_prog.frames, ctx_in)
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

    let execution_started = begin_execution(state, ctx_in);

    let registry = HandlerRegistry::new();
    let mut ctx = ctx_in.clone();
    let mut effect_idx = BytecodeProgram::effect_idx(ctx_in.program_counter as usize);
    let mut cond = true;
    let mut steps = 0;

    while effect_idx < frames.len() {
        if steps >= MAX_INTERPRETER_STEPS {
            finish_execution(state, ctx_in, execution_started);
            return Err(InterpreterError::InfiniteLoop { steps, limit: MAX_INTERPRETER_STEPS });
        }
        steps += 1;
        let frame = &frames[effect_idx];
        let ip = BytecodeProgram::effect_ip(effect_idx);
        let op = frame.opcode();
        let v = frame.value();
        let a = frame.attr() as i64;
        let s = frame.slot();

        ctx.program_counter = ip as u16;
        if effect_idx == BytecodeProgram::effect_idx(ctx_in.program_counter as usize) && ctx_in.choice_index != -1 {
            ctx.choice_index = ctx_in.choice_index;
        }

        if op == crate::core::enums::O_NOP as i32 {
            if let Some(ref mut set) = state.debug.executed_opcodes {
                set.insert(op);
            }
            effect_idx += 1;
            continue;
        }
        if op == crate::core::enums::O_RETURN as i32 {
            if let Some(ref mut set) = state.debug.executed_opcodes {
                set.insert(op);
            }
            break;
        }

        let mut real_op = op;
        let is_negated = frame.is_negated();
        if real_op >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET && !is_negated {
            real_op -= crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        }

        if state.debug.debug_mode {
            let desc = logging::describe_trace_step(real_op, v, a, s, is_negated);
            let card_name = db.get_member(ctx.source_card_id)
                .map(|c| c.name.as_str())
                .or_else(|| db.get_live(ctx.source_card_id).map(|l| l.name.as_str()))
                .unwrap_or("System");
            let log_line = format!("BC_STEP: [depth={}] [card={}] ip={:<3} {}", 0, card_name, ip, desc);
            if !state.ui.silent {
                println!("[DEBUG] {}", log_line);
            }

            let b_log = &mut state.ui.bytecode_log;
            if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                b_log.push(log_line.clone());
            }
            state.trace_internal(&log_line);
        }
        if let Some(ref mut set) = state.debug.executed_opcodes {
            set.insert(real_op);
        }

        let mut target_slot = s;
        if (s & 0xFF) == crate::core::generated_constants::SLOT_CONTEXT {
            target_slot = (s & !0xFF) | (ctx.target_slot as i32);
        }

        if (real_op >= crate::core::logic::constants::CONDITION_START_1 && real_op <= crate::core::logic::constants::CONDITION_END_1)
            || (real_op >= crate::core::logic::constants::CONDITION_START_2 && real_op <= crate::core::logic::constants::CONDITION_END_2) {
            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!(
                        "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",
                        real_op, a
                    );
                }
            }
            let accumulated_count = match real_op {
                crate::core::generated_constants::C_COUNT_STAGE
                | crate::core::generated_constants::C_COUNT_HAND
                | crate::core::generated_constants::C_COUNT_DISCARD
                | crate::core::generated_constants::C_COUNT_ENERGY
                | crate::core::generated_constants::C_COUNT_HEARTS
                | crate::core::generated_constants::C_COUNT_BLADES
                | crate::core::generated_constants::C_COUNT_GROUP
                | crate::core::generated_constants::C_COUNT_SUCCESS_LIVE
                | 307 => Some(conditions::resolve_count(
                    state,
                    db,
                    real_op,
                    a as u64,
                    target_slot,
                    &ctx,
                    0,
                )),
                _ => None,
            };
            let passed = if !cond {
                false
            } else {
                conditions::check_condition_opcode(
                    state,
                    db,
                    real_op,
                    v,
                    a as u64,
                    target_slot,
                    &ctx,
                    0,
                )
            };
            if let Some(count) = accumulated_count {
                ctx.v_accumulated = count as i16;
            }
            if state.debug.debug_mode {
                let result_line = format!(
                    "BC_RESULT: ip={:<3} {}",
                    ip,
                    if is_negated { !passed } else { passed }
                );
                if !state.ui.silent {
                    println!("[DEBUG] {}", result_line);
                }
                let b_log = &mut state.ui.bytecode_log;
                if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                    b_log.push(result_line.clone());
                }
                state.trace_internal(&result_line);
            }
            cond = cond && if is_negated { !passed } else { passed };
            if state.debug.debug_mode {
                let cond_desc = format!(
                    "BC_COND: ip={:<3} {} -> passed={}, final={}",
                    ip,
                    logging::describe_condition(real_op, v, a as u64),
                    passed,
                    cond
                );
                if !state.ui.silent {
                    println!("      | [COND] {}", cond_desc);
                }

                let b_log = &mut state.ui.bytecode_log;
                if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                    b_log.push(cond_desc.clone());
                }
                state.trace_internal(&cond_desc);
            }
            ctx.choice_index = -1;
            effect_idx += 1;
            continue;
        }

        if real_op == crate::core::enums::O_JUMP as i32 {
            effect_idx = (effect_idx as i64 + 1 + v as i64).max(0) as usize;
            ctx.choice_index = -1;
            continue;
        }
        if real_op == crate::core::enums::O_JUMP_IF_FALSE as i32 {
            if !cond {
                effect_idx = (effect_idx as i64 + 1 + v as i64).max(0) as usize;
            } else {
                effect_idx += 1;
            }
            cond = true;
            ctx.choice_index = -1;
            continue;
        }

        if !cond || is_negated {
            effect_idx += 1;
            continue;
        }

        let mut advance_effect = true;
        match registry.dispatch(state, db, &mut ctx, frame, effect_idx, frames) {
            HandlerResult::Continue => {}
            HandlerResult::SetCond(new_cond) => cond = new_cond,
            HandlerResult::Suspend => return Ok(()),
            HandlerResult::Return => break,
            HandlerResult::Branch(new_effect_idx) => {
                effect_idx = new_effect_idx;
                advance_effect = false;
            }
            HandlerResult::BranchToFrames(new_frames) => {
                if let Err(err) = resolve_semantic_frames(state, db, new_frames.as_slice(), &ctx) {
                    finish_execution(state, ctx_in, execution_started);
                    return Err(err);
                }
                if state.phase == Phase::Response {
                    return Ok(());
                }
            }
        }

        if advance_effect {
            effect_idx += 1;
        }
    }

    finish_execution(state, ctx_in, execution_started);
    Ok(())
}

impl BytecodeExecutor {
    fn new(bytecode: std::sync::Arc<Vec<i32>>, ctx: &AbilityContext) -> Self {
        Self {
            stack: vec![ExecutionFrame {
                program: BytecodeProgram::new(bytecode),
                ip: ctx.program_counter as usize,
                ctx: ctx.clone(),
            }],
            cond: true,
            steps: 0,
        }
    }

    fn pop_frame(&mut self) -> Option<ExecutionFrame> {
        self.stack.pop()
    }
}

pub fn resolve_frames(
    state: &mut GameState,
    db: &CardDatabase,
    frames: &[AbilityFrame],
    ctx_in: &AbilityContext,
) -> Result<(), InterpreterError> {
    resolve_semantic_frames(state, db, frames, ctx_in)
}

/// Main entry point for bytecode execution
pub fn resolve_bytecode(
    state: &mut GameState,
    db: &CardDatabase,
    bytecode: Arc<Vec<i32>>,
    ctx_in: &AbilityContext,
) -> Result<(), InterpreterError> {
    println!("[DEBUG] resolve_bytecode starting. Bytecode len: {}", bytecode.len());
    // VANILLA MODE: Skip all bytecode execution
    if db.is_vanilla {
        return Ok(());
    }

    let execution_started = begin_execution(state, ctx_in);

    let mut executor = BytecodeExecutor::new(bytecode, ctx_in);
    let registry = HandlerRegistry::new();

    while !executor.stack.is_empty() {
        if executor.steps >= MAX_INTERPRETER_STEPS {
            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!("[ERROR] Interpreter infinite loop detected (1000 steps)");
                }
            }
            finish_execution(state, ctx_in, execution_started);
            return Err(InterpreterError::InfiniteLoop { steps: executor.steps, limit: MAX_INTERPRETER_STEPS });
        }
        executor.steps += 1;

        let stack_depth = executor.stack.len();
        // Obtain mutable reference to the current frame
        let frame = executor.stack.last_mut().unwrap();

        let ip = frame.ip;
        if ip >= frame.program.len_words() {
            executor.pop_frame();
            continue;
        }

        let instr = match frame.program.instruction_at(ip) {
            Some(instr) => instr,
            None => {
                finish_execution(state, ctx_in, execution_started);
                return Err(InterpreterError::InvalidInstruction { ip });
            }
        };

        let op = instr.op;
        let v = instr.v;
        let a = instr.a;
        let s = instr.raw_s;

        frame.ip = frame.program.next_ip(ip);
        frame.ctx.program_counter = ip as u16;

        // Resumption logic: inject choice index if we're at the suspension point
        if ip == ctx_in.program_counter as usize && ctx_in.choice_index != -1 {
            frame.ctx.choice_index = ctx_in.choice_index;
        }

        // Logic for O_NOP and O_RETURN
        if op == crate::core::enums::O_NOP as i32 {
            if let Some(ref mut set) = state.debug.executed_opcodes {
                set.insert(op);
            }
            // log_opcode_to_file(op);
            // if let Ok(mut tracker) = GLOBAL_OPCODE_TRACKER.lock() {
            //     tracker.insert(op);
            // }
            continue;
        }
        if op == crate::core::enums::O_RETURN as i32 {
            if let Some(ref mut set) = state.debug.executed_opcodes {
                set.insert(op);
            }
            // log_opcode_to_file(op);
            // if let Ok(mut tracker) = GLOBAL_OPCODE_TRACKER.lock() {
            //     tracker.insert(op);
            // }
            if executor.pop_frame().is_none() {
                break;
            }
            continue;
        }

        // Handle negation
        let mut real_op = op;
        let mut is_negated = false;
        if real_op >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET {
            is_negated = true;
            real_op -= crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        }

        if state.debug.debug_mode {
            let desc = logging::describe_trace_step(real_op, v, a, s, is_negated);

            // Get card info for context
            let card_name = db.get_member(frame.ctx.source_card_id)
                .map(|c| c.name.as_str())
                .or_else(|| db.get_live(frame.ctx.source_card_id).map(|l| l.name.as_str()))
                .unwrap_or("System");

            let log_line = format!("BC_STEP: [depth={}] [card={}] ip={:<3} {}", stack_depth, card_name, ip, desc);
            if !state.ui.silent {
                println!("[DEBUG] {}", log_line);
            }

            let b_log = &mut state.ui.bytecode_log;
            if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                b_log.push(log_line.clone());
            }
            state.trace_internal(&log_line);
        }
        if let Some(ref mut set) = state.debug.executed_opcodes {
            set.insert(real_op);
        }
        // log_opcode_to_file(real_op);
        // if let Ok(mut tracker) = GLOBAL_OPCODE_TRACKER.lock() {
        //     tracker.insert(real_op);
        // }

        let mut target_slot = s;
        if (s & 0xFF) == crate::core::generated_constants::SLOT_CONTEXT {
            // Resolve Choice Target (10) while preserving upper bits (flags/area)
            target_slot = (s & !0xFF) | (frame.ctx.target_slot as i32);
        }

        // Condition opcodes (200-255 and 301-399 for extended conditions)
        if (real_op >= crate::core::logic::constants::CONDITION_START_1 && real_op <= crate::core::logic::constants::CONDITION_END_1)
            || (real_op >= crate::core::logic::constants::CONDITION_START_2 && real_op <= crate::core::logic::constants::CONDITION_END_2) {
            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!(
                        "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",
                        real_op, a
                    );
                }
            }
            let accumulated_count = match real_op {
                crate::core::generated_constants::C_COUNT_STAGE
                | crate::core::generated_constants::C_COUNT_HAND
                | crate::core::generated_constants::C_COUNT_DISCARD
                | crate::core::generated_constants::C_COUNT_ENERGY
                | crate::core::generated_constants::C_COUNT_HEARTS
                | crate::core::generated_constants::C_COUNT_BLADES
                | crate::core::generated_constants::C_COUNT_GROUP
                | crate::core::generated_constants::C_COUNT_SUCCESS_LIVE
                | 307 => Some(conditions::resolve_count(
                    state,
                    db,
                    real_op,
                    a as u64,
                    target_slot,
                    &frame.ctx,
                    0,
                )),
                _ => None,
            };
            let passed = if !executor.cond {
                false // Already failed, no need to check
            } else {
                conditions::check_condition_opcode(
                    state,
                    db,
                    real_op,
                    v,
                    a as u64,
                    target_slot,
                    &frame.ctx,
                    0,
                )
            };
            if let Some(count) = accumulated_count {
                frame.ctx.v_accumulated = count as i16;
            }
            if state.debug.debug_mode {
                let result_line = format!(
                    "BC_RESULT: ip={:<3} {}",
                    ip,
                    if is_negated { !passed } else { passed }
                );
                if !state.ui.silent {
                    println!("[DEBUG] {}", result_line);
                }
                let b_log = &mut state.ui.bytecode_log;
                if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                    b_log.push(result_line.clone());
                }
                state.trace_internal(&result_line);
            }
            executor.cond = executor.cond && if is_negated { !passed } else { passed };
            if state.debug.debug_mode {
                let cond_desc = format!(
                    "BC_COND: ip={:<3} {} -> passed={}, final={}",
                    ip,
                    logging::describe_condition(real_op, v, a as u64),
                    passed,
                    executor.cond
                );
                if !state.ui.silent {
                    println!("      | [COND] {}", cond_desc);
                }

                let b_log = &mut state.ui.bytecode_log;
                if b_log.len() < MAX_BYTECODE_LOG_SIZE {
                    b_log.push(cond_desc.clone());
                }
                state.trace_internal(&cond_desc);
            }
            frame.ctx.choice_index = -1;
            continue;
        }

        // Control flow
        if real_op == crate::core::enums::O_JUMP as i32 {
            frame.ip = frame
                .program
                .jump_target(ip, v)
                .unwrap_or(frame.program.len_words());
            frame.ctx.choice_index = -1;
            continue;
        }
        if real_op == crate::core::enums::O_JUMP_IF_FALSE as i32 {
            if !executor.cond {
                frame.ip = frame
                    .program
                    .jump_target(ip, v)
                    .unwrap_or(frame.program.len_words());
            }
            // Reset cond ONLY after JUMP_IF_FALSE (end of current condition block)
            executor.cond = true;
            frame.ctx.choice_index = -1;
            continue;
        }

        // Skip effect opcodes when condition is false
        // This handles cases where bytecode doesn't have explicit JUMP_IF_FALSE
        if !executor.cond {
            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!(
                        "      | [SKIP] Opcode {} skipped (cond=false)",
                        logging::get_opcode_name(real_op)
                    );
                }
            }
            // Skip this opcode. cond will be reset by JUMP_IF_FALSE or end of scope.
            continue;
        }

        // Dispatch to handlers - Use 64-bit 'a' directly
        let mut do_reset = true;
        let frame_idx = ip / crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION;
        let dispatch_frame = AbilityFrame::new(instr.op, instr.v, instr.a, instr.raw_s);
        match registry.dispatch(
            state,
            db,
            &mut frame.ctx,
            &dispatch_frame,
            frame_idx,
            &[],
        ) {
            HandlerResult::Continue => {}
            HandlerResult::SetCond(c) => executor.cond = c,
            HandlerResult::Suspend => return Ok(()),
            HandlerResult::Return => {
                if executor.pop_frame().is_none() {
                    break;
                }
            }
            HandlerResult::Branch(new_effect_idx) => {
                frame.ip = BytecodeProgram::effect_ip(new_effect_idx);
                do_reset = false; // Branch explicitly loops back, requiring state like v_remaining to persist
            }
            HandlerResult::BranchToFrames(new_frames) => {
                let next_ctx = frame.ctx.clone();
                executor.stack.push(ExecutionFrame {
                    program: BytecodeProgram::from_frames(new_frames.as_slice()),
                    ip: 0,
                    ctx: next_ctx,
                });
            }
        }

        // Obtaining frame again after dispatch might be necessary if we popped, but the loop head handles it.
        if let Some(_f) = executor.stack.last_mut() {
            // Handlers are responsible for clearing their own step state once they consume it.
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

    while let Some((cid, ab_idx, ctx, is_live, _trigger)) = state.trigger_queue.pop_front() {
        let mut ctx = ctx;
        // Generate a new ID for the activation
        state.generate_execution_id();
        let execution_id = state.ui.current_execution_id.unwrap_or(0);
        println!("[DEBUG] processing trigger: cid={}, ab_idx={}, execution_id={}, trigger={:?}", cid, ab_idx, execution_id, _trigger);

        let (ability, costs) = if is_live {
            let ab = &db.get_live(cid).unwrap().abilities[ab_idx as usize];
            (ab, &ab.costs)
        } else {
            let ab = &db.get_member(cid).unwrap().abilities[ab_idx as usize];
            (ab, &ab.costs)
        };

        if costs::pay_costs_transactional(state, db, costs, &mut ctx) {
            let p_idx = ctx.player_id as usize;
            let source_type = if is_live { 2 } else { 0 };
            let instance_key = state.get_once_per_turn_instance_key(
                p_idx,
                source_type,
                ctx.area_idx,
                cid,
            );

            if ability.is_once_per_turn
                && !check_once_per_turn(state, p_idx, source_type, instance_key, cid as u32, ab_idx as usize)
            {
                state.clear_execution_id();
                continue;
            }

            if ability.is_once_per_turn {
                consume_once_per_turn(state, p_idx, source_type, instance_key, cid as u32, ab_idx as usize);
            }

            if state.phase == Phase::PerformanceP1 || state.phase == Phase::PerformanceP2 || state.phase == Phase::LiveResult {
                state.players[p_idx].perf_triggered_abilities.push((cid, ab_idx as i16, _trigger));
            }
            let _ = resolve_ability(state, db, ability, &ctx);

            // Fire resolution triggers
            let res_trigger = match _trigger {
                crate::core::enums::TriggerType::OnLiveStart => Some(crate::core::enums::TriggerType::OnAbilityResolve),
                crate::core::enums::TriggerType::OnLiveSuccess => Some(crate::core::enums::TriggerType::OnAbilitySuccess),
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
                res_ctx.target_card_id = cid; // The member/card whose ability resolved

                // CRITICAL FIX: Update area_idx to the physical slot where the card is.
                // SLOT_CONTEXT (4) relies on area_idx pointing to the member's slot.
                if !is_live {
                    let p_idx = ctx.player_id as usize;
                    if let Some(pos) = state.players[p_idx].stage.iter().position(|&slot_cid| slot_cid == cid) {
                        res_ctx.area_idx = pos as i16;
                    }
                }

                state.trigger_abilities(db, t, &res_ctx);
            }

            let _top_original_phase = state.interaction_stack.last().map(|pi| pi.original_phase);
            let _top_original_player = state.interaction_stack.last().map(|pi| pi.original_current_player);
            let _clear_same_card_interactions = |state: &mut GameState, card_id: i32| {
                while state
                    .interaction_stack
                    .last()
                    .map(|pi| pi.card_id == card_id)
                    .unwrap_or(false)
                {
                    state.interaction_stack.pop();
                }
            };

            let _stage_count = state.players[ctx.player_id as usize]
                .stage
                .iter()
                .filter(|&&card_id| card_id >= 0)
                .count();

        }

        state.clear_execution_id();

        // If the interpreter suspended, we must stop processing the queue
        if state.phase == Phase::Response {
            break;
        }
    }
}

pub fn get_ability_uid(source_type: u8, instance_key: u8, id: u32, ab_idx: u32) -> u32 {
    ((source_type as u32) << 28)
        | ((instance_key as u32 & 0x0F) << 24)
        | ((id & 0xFFFF) << 8)
        | (ab_idx & 0xFF)
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
    state.players[p_idx].used_abilities.push(uid);
}




