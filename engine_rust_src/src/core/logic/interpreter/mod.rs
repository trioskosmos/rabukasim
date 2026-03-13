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
use super::Ability;
pub use conditions::{check_condition, check_condition_opcode};
pub use costs::{check_cost, pay_cost};
pub use handlers::{HandlerRegistry, HandlerResult};
pub use suspension::{get_choice_text, resolve_target_slot, suspend_interaction};

use once_cell::sync::Lazy;
use std::collections::HashSet;
use std::sync::Mutex;

pub static GLOBAL_OPCODE_TRACKER: Lazy<Mutex<HashSet<i32>>> =
    Lazy::new(|| Mutex::new(HashSet::<i32>::new()));

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

struct ExecutionFrame {
    bytecode: std::sync::Arc<Vec<i32>>,
    ip: usize,
    ctx: AbilityContext,
}

struct BytecodeExecutor {
    stack: Vec<ExecutionFrame>,
    cond: bool,
    steps: u32,
}

fn effect_has_modal_options(effect: &crate::core::logic::Effect) -> bool {
    match &effect.modal_options {
        serde_json::Value::Null => false,
        serde_json::Value::Array(values) => !values.is_empty(),
        serde_json::Value::Object(values) => !values.is_empty(),
        _ => true,
    }
}

fn ability_uses_structured_runtime(ability: &Ability) -> bool {
    if ability.effects.is_empty() {
        return false;
    }
    if ability.bytecode.len() != ability.effects.len() * 5 + 5 {
        return false;
    }

    for (idx, effect) in ability.effects.iter().enumerate() {
        if effect.runtime_opcode == 0 || effect_has_modal_options(effect) {
            return false;
        }

        let ip = idx * 5;
        let a_low = effect.runtime_attr as u32 as i32;
        let a_high = (effect.runtime_attr >> 32) as u32 as i32;

        if ability.bytecode[ip] != effect.runtime_opcode
            || ability.bytecode[ip + 1] != effect.runtime_value
            || ability.bytecode[ip + 2] != a_low
            || ability.bytecode[ip + 3] != a_high
            || ability.bytecode[ip + 4] != effect.runtime_slot
        {
            return false;
        }
    }

    ability.bytecode.last().copied() == Some(0)
        && ability.bytecode.get(ability.bytecode.len().saturating_sub(5)).copied() == Some(O_RETURN)
}

pub fn resolve_ability(
    state: &mut GameState,
    db: &CardDatabase,
    ability: &Ability,
    ctx_in: &AbilityContext,
) {
    if !ability_uses_structured_runtime(ability) {
        resolve_bytecode(state, db, std::sync::Arc::new(ability.bytecode.clone()), ctx_in);
        return;
    }

    let _id = if state.ui.current_execution_id.is_none() && ctx_in.program_counter == 0 {
        Some(state.generate_execution_id())
    } else {
        None
    };

    let registry = HandlerRegistry::new();
    let mut ctx = ctx_in.clone();
    let mut effect_idx = (ctx_in.program_counter as usize) / 5;

    while effect_idx < ability.effects.len() {
        let effect = &ability.effects[effect_idx];
        let ip = effect_idx * 5;
        ctx.program_counter = ip as u16;
        if effect_idx == (ctx_in.program_counter as usize) / 5 && ctx_in.choice_index != -1 {
            ctx.choice_index = ctx_in.choice_index;
        }

        let instr = instruction::BytecodeInstruction::new(
            effect.runtime_opcode,
            effect.runtime_value,
            effect.runtime_attr as i64,
            effect.runtime_slot,
        );

        match registry.dispatch(state, db, &mut ctx, &instr, ip, &[]) {
            HandlerResult::Continue => {
                ctx.choice_index = -1;
                ctx.v_remaining = -1;
                effect_idx += 1;
            }
            HandlerResult::SetCond(_) => {
                ctx.choice_index = -1;
                ctx.v_remaining = -1;
                effect_idx += 1;
            }
            HandlerResult::Suspend => return,
            HandlerResult::Return => break,
            HandlerResult::Branch(new_ip) => {
                ctx.choice_index = -1;
                ctx.v_remaining = -1;
                effect_idx = new_ip / 5;
            }
            HandlerResult::BranchToBytecode(new_bc) => {
                resolve_bytecode(state, db, new_bc, &ctx);
                if state.phase == Phase::Response {
                    return;
                }
                ctx.choice_index = -1;
                ctx.v_remaining = -1;
                effect_idx += 1;
            }
        }
    }

    state.players[ctx_in.player_id as usize].revealed_cards.clear();

    if _id.is_some() {
        state.clear_execution_id();
    }

    if ctx_in.choice_index != -1
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

impl BytecodeExecutor {
    fn new(bytecode: std::sync::Arc<Vec<i32>>, ctx: &AbilityContext) -> Self {
        Self {
            stack: vec![ExecutionFrame {
                bytecode,
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

/// Main entry point for bytecode execution
pub fn resolve_bytecode(
    state: &mut GameState,
    db: &CardDatabase,
    bytecode: std::sync::Arc<Vec<i32>>,
    ctx_in: &AbilityContext,
) {
    let _id = if state.ui.current_execution_id.is_none() && ctx_in.program_counter == 0 {
        Some(state.generate_execution_id())
    } else {
        None
    };

    let mut executor = BytecodeExecutor::new(bytecode, ctx_in);
    let registry = HandlerRegistry::new();

    if !state.ui.silent && _id.is_some() {
        state.log("Bytecode execution started.".to_string());
    }

    while !executor.stack.is_empty() {
        if executor.steps >= MAX_INTERPRETER_STEPS {
            if state.debug.debug_mode {
                if !state.ui.silent {
                    println!("[ERROR] Interpreter infinite loop detected (1000 steps)");
                }
            }
            break;
        }
        executor.steps += 1;

        let stack_depth = executor.stack.len();
        // Obtain mutable reference to the current frame
        let frame = executor.stack.last_mut().unwrap();

        let ip = frame.ip;
        if ip >= frame.bytecode.len() {
            executor.pop_frame();
            continue;
        }

        let instr = instruction::BytecodeInstruction::decode(&frame.bytecode, ip);
        let op = instr.op;
        let v = instr.v;
        let a = instr.a;
        let s = instr.raw_s;

        frame.ip += 5; // Advance IP
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
            let desc = logging::describe_bytecode(real_op, v, a, s);

            // Get card info for context
            let card_name = db.get_member(frame.ctx.source_card_id)
                .map(|c| c.name.as_str())
                .or_else(|| db.get_live(frame.ctx.source_card_id).map(|l| l.name.as_str()))
                .unwrap_or("System");

            let log_line = format!("BC_STEP: [depth={}] [card={}] ip={:<3} {}", stack_depth, card_name, ip, desc);
            println!("[DEBUG] {}", log_line);

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
                println!(
                    "[DEBUG] CALLING check_condition_opcode: op={}, a={:x}",
                    real_op, a
                );
            }
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
            executor.cond = executor.cond && if is_negated { !passed } else { passed };
            if state.debug.debug_mode {
                let cond_desc = format!(
                    "BC_COND: ip={:<3} {} -> passed={}, final={}",
                    ip,
                    logging::describe_condition(real_op, v, a as u64),
                    passed,
                    executor.cond
                );
                println!("      | [COND] {}", cond_desc);

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
            frame.ip = (ip as i32 + 5 + (v * 5)) as usize;
            frame.ctx.choice_index = -1;
            continue;
        }
        if real_op == crate::core::enums::O_JUMP_IF_FALSE as i32 {
            if !executor.cond {
                frame.ip = (ip as i32 + 5 + (v * 5)) as usize;
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
                println!(
                    "      | [SKIP] Opcode {} skipped (cond=false)",
                    logging::get_opcode_name(real_op)
                );
            }
            // Skip this opcode. cond will be reset by JUMP_IF_FALSE or end of scope.
            continue;
        }

        // Dispatch to handlers - Use 64-bit 'a' directly
        let mut do_reset = true;
        match registry.dispatch(
            state,
            db,
            &mut frame.ctx,
            &instr,
            ip,
            &frame.bytecode,
        ) {
            HandlerResult::Continue => {}
            HandlerResult::SetCond(c) => executor.cond = c,
            HandlerResult::Suspend => return,
            HandlerResult::Return => {
                if executor.pop_frame().is_none() {
                    return;
                }
            }
            HandlerResult::Branch(new_ip) => {
                frame.ip = new_ip;
                do_reset = false; // Branch explicitly loops back, requiring state like v_remaining to persist
            }
            HandlerResult::BranchToBytecode(new_bc) => {
                let next_ctx = frame.ctx.clone();
                executor.stack.push(ExecutionFrame {
                    bytecode: new_bc,
                    ip: 0,
                    ctx: next_ctx,
                });
            }
        }

        // Obtaining frame again after dispatch might be necessary if we popped, but the loop head handles it.
        if let Some(f) = executor.stack.last_mut() {
            // CRITICAL: Only reset these if we aren't suspended,
            // otherwise we lose the budget (v_remaining) and choice state for resumption.
            if do_reset {
                f.ctx.choice_index = -1; // Reset choice index after each instruction
                f.ctx.v_remaining = -1; // Reset v_remaining to prevent state leakage, UNLESS we are branching
            }
        }
    }

    // Cleanup revealed cards after ability finishes
    state.players[ctx_in.player_id as usize].revealed_cards.clear();

    if _id.is_some() {
        state.clear_execution_id();
    }

    // Restore phase if we finished a resumed execution and no new suspensions occurred
    if ctx_in.choice_index != -1 && (state.phase == Phase::Response || state.phase == Phase::Setup) && state.interaction_stack.is_empty() {
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

/// Helper to check if an opcode is a condition
pub fn is_condition_opcode(op: i32) -> bool {
    let real_op = if op >= 1000 { op - 1000 } else { op };
    (real_op >= 200 && real_op <= 255) || (real_op >= 301 && real_op <= 399)
}

pub fn process_trigger_queue(state: &mut GameState, db: &CardDatabase) {
    while let Some((cid, ab_idx, ctx, is_live, _trigger)) = state.trigger_queue.pop_front() {
        // Generate a new ID for the activation
        state.generate_execution_id();
        let execution_id = state.ui.current_execution_id.unwrap_or(0);

        let (ability, costs) = if is_live {
            let ab = &db.get_live(cid).unwrap().abilities[ab_idx as usize];
            (ab, &ab.costs)
        } else {
            let ab = &db.get_member(cid).unwrap().abilities[ab_idx as usize];
            (ab, &ab.costs)
        };

        if costs::pay_costs_transactional(state, db, costs, &ctx) {
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
            resolve_ability(state, db, ability, &ctx);

            let is_custom_live_override = is_live
                && db
                    .get_live(cid)
                    .map(|card| {
                        card.card_no.as_str() == "PL!-bp5-021-L"
                            || card.card_no.as_str() == "PL!N-bp4-030-L"
                    })
                    .unwrap_or(false);
            let suspended_execution = state.phase == Phase::Response
                && state
                    .interaction_stack
                    .last()
                    .map(|pi| pi.execution_id == execution_id)
                    .unwrap_or(false);
            if suspended_execution && !is_custom_live_override {
                continue;
            }

            // Fire resolution triggers
            let res_trigger = match _trigger {
                crate::core::enums::TriggerType::OnLiveStart => Some(crate::core::enums::TriggerType::OnAbilityResolve),
                crate::core::enums::TriggerType::OnLiveSuccess => Some(crate::core::enums::TriggerType::OnAbilitySuccess),
                _ => None,
            };

            if let Some(t) = res_trigger {
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

            let top_original_phase = state.interaction_stack.last().map(|pi| pi.original_phase);
            let top_original_player = state.interaction_stack.last().map(|pi| pi.original_current_player);
            let clear_same_card_interactions = |state: &mut GameState, card_id: i32| {
                while state
                    .interaction_stack
                    .last()
                    .map(|pi| pi.card_id == card_id)
                    .unwrap_or(false)
                {
                    state.interaction_stack.pop();
                }
            };

            let stage_count = state.players[ctx.player_id as usize]
                .stage
                .iter()
                .filter(|&&card_id| card_id >= 0)
                .count();

            if is_live
                && ctx.trigger_type == crate::core::enums::TriggerType::OnLiveStart
                && db
                    .get_live(cid)
                    .map(|card| card.card_no.as_str() == "PL!-bp5-021-L")
                    .unwrap_or(false)
                && stage_count >= 2
            {
                clear_same_card_interactions(state, cid);
                let mut follow_ctx = ctx.clone();
                follow_ctx.choice_index = -1;
                follow_ctx.v_accumulated = 211;
                follow_ctx.original_phase = Some(top_original_phase.unwrap_or(Phase::Main));
                follow_ctx.original_current_player = Some(top_original_player.unwrap_or(state.current_player));
                let choice_text = get_choice_text(db, &follow_ctx);
                if suspend_interaction(
                    state,
                    db,
                    &follow_ctx,
                    0,
                    O_SELECT_MEMBER,
                    0,
                    crate::core::enums::ChoiceType::SelectMember,
                    &choice_text,
                    17,
                    -1,
                ) {
                    continue;
                }
            }

            if is_live
                && ctx.trigger_type == crate::core::enums::TriggerType::OnLiveSuccess
                && db
                    .get_live(cid)
                    .map(|card| card.card_no.as_str() == "PL!N-bp4-030-L")
                    .unwrap_or(false)
                && state.players[ctx.player_id as usize]
                    .success_lives
                    .iter()
                    .copied()
                    .any(|success_cid| state.card_matches_filter(db, success_cid, 80))
            {
                let mut mask = 0i16;
                mask |= 0x1;
                if state.players[ctx.player_id as usize]
                    .discard
                    .iter()
                    .copied()
                    .any(|discard_cid| db.get_member(discard_cid).is_some())
                {
                    mask |= 0x2;
                }
                if mask != 0 {
                    clear_same_card_interactions(state, cid);
                    let mut follow_ctx = ctx.clone();
                    follow_ctx.choice_index = -1;
                    follow_ctx.v_accumulated = 1900 + mask;
                    follow_ctx.original_phase = Some(top_original_phase.unwrap_or(Phase::Main));
                    follow_ctx.original_current_player = Some(top_original_player.unwrap_or(state.current_player));
                    let choice_text = get_choice_text(db, &follow_ctx);
                    if suspend_interaction(
                        state,
                        db,
                        &follow_ctx,
                        0,
                        O_SELECT_MODE,
                        0,
                        crate::core::enums::ChoiceType::SelectMode,
                        &choice_text,
                        0,
                        mask.count_ones() as i16,
                    ) {
                        continue;
                    }
                }
            }
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
