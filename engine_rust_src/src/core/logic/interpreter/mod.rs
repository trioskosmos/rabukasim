//! # Modular Bytecode Interpreter
//!
//! This module decouples the monolithic interpreter into smaller, maintainable components.

pub mod filter;
pub mod conditions;
pub mod costs;
pub mod constants;
pub mod suspension;
pub mod handlers;
pub mod logging;

use crate::core::logic::{GameState, CardDatabase, AbilityContext};
pub use handlers::{HandlerRegistry, HandlerResult};
pub use conditions::{check_condition_opcode, check_condition};
pub use costs::{check_cost, pay_cost};
pub use suspension::{suspend_interaction, resolve_target_slot, get_choice_text};

use once_cell::sync::Lazy;
use std::sync::Mutex;
use std::collections::HashSet;

pub static GLOBAL_OPCODE_TRACKER: Lazy<Mutex<HashSet<i32>>> = Lazy::new(|| Mutex::new(HashSet::<i32>::new()));

fn log_opcode_to_file(op: i32) {
    use std::io::Write;
    let thread_name = std::thread::current().name().unwrap_or("unknown").to_string();
    if let Ok(mut file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("reports/telemetry_raw.log") 
    {
        let _ = writeln!(file, "[OPCODE] {} | Test: {}", op, thread_name);
    }
}

/// The maximum depth of nested bytecode execution (e.g. via O_TRIGGER_REMOTE)
pub const MAX_DEPTH: usize = 8;

struct ExecutionFrame {
    bytecode: Vec<i32>,
    ip: usize,
    ctx: AbilityContext,
}

struct BytecodeExecutor {
    stack: Vec<ExecutionFrame>,
    cond: bool,
    steps: u32,
}

impl BytecodeExecutor {
    fn new(bytecode: &[i32], ctx: &AbilityContext) -> Self {
        Self {
            stack: vec![ExecutionFrame {
                bytecode: bytecode.to_vec(),
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
    bytecode: &[i32], 
    ctx_in: &AbilityContext
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
        if executor.steps >= 1000 {
            if state.debug.debug_mode {
                println!("[ERROR] Interpreter infinite loop detected (1000 steps)");
            }
            break;
        }
        executor.steps += 1;

        // Obtain mutable reference to the current frame
        let frame = executor.stack.last_mut().unwrap();
        
        let ip = frame.ip;
        if ip >= frame.bytecode.len() {
            executor.pop_frame();
            continue;
        }

        let op = frame.bytecode[ip];
        
        // Instruction decoding (standard 4-word format)
        let v = if ip + 1 < frame.bytecode.len() { frame.bytecode[ip+1] } else { 0 };
        let a = if ip + 2 < frame.bytecode.len() { frame.bytecode[ip+2] } else { 0 };
        let s = if ip + 3 < frame.bytecode.len() { frame.bytecode[ip+3] } else { 0 };

        frame.ip += 4; // Advance IP
        frame.ctx.program_counter = ip as u16;

        // Resumption logic: inject choice index if we're at the suspension point
        if ip == ctx_in.program_counter as usize && ctx_in.choice_index != -1 {
            frame.ctx.choice_index = ctx_in.choice_index;
        }

        // Logic for O_NOP and O_RETURN
        if op == crate::core::enums::O_NOP as i32 { 
            state.debug.executed_opcodes.insert(op);
            log_opcode_to_file(op);
            if let Ok(mut tracker) = GLOBAL_OPCODE_TRACKER.lock() {
                tracker.insert(op);
            }
            continue; 
        }
        if op == crate::core::enums::O_RETURN as i32 {
            state.debug.executed_opcodes.insert(op);
            log_opcode_to_file(op);
            if let Ok(mut tracker) = GLOBAL_OPCODE_TRACKER.lock() {
                tracker.insert(op);
            }
            if executor.pop_frame().is_none() {
                break;
            }
            continue;
        }

        // Handle negation
        let mut real_op = op;
        let mut is_negated = false;
        if real_op >= 1000 {
            is_negated = true;
            real_op -= 1000;
        }

        if state.debug.debug_mode {
            println!("[DEBUG] BC_STEP: ip={}, op={} (real={}), v={}, a={}, s={}, cond={}", 
                ip, op, real_op, v, a, s, executor.cond);
        }
        state.debug.executed_opcodes.insert(real_op);
        log_opcode_to_file(real_op);
        if let Ok(mut tracker) = GLOBAL_OPCODE_TRACKER.lock() {
            tracker.insert(real_op);
        }

        let mut target_slot = s & 0xFF;
        if target_slot == 10 { target_slot = frame.ctx.target_slot as i32; }

        // Condition opcodes (200-255)
        if real_op >= 200 && real_op <= 255 {
            let passed = conditions::check_condition_opcode(
                state, db, real_op, v, a as u32 as u64, target_slot, &frame.ctx, 0
            );
            executor.cond = executor.cond && if is_negated { !passed } else { passed };
            frame.ctx.choice_index = -1;
            continue;
        }

        // Control flow
        if real_op == crate::core::enums::O_JUMP as i32 {
            frame.ip = (ip as i32 + 4 + (v * 4)) as usize;
            frame.ctx.choice_index = -1;
            continue;
        }
        if real_op == crate::core::enums::O_JUMP_IF_FALSE as i32 {
            if !executor.cond {
                frame.ip = (ip as i32 + 4 + (v * 4)) as usize;
            }
            // Reset cond ONLY after JUMP_IF_FALSE (end of current condition block)
            executor.cond = true;
            frame.ctx.choice_index = -1;
            continue;
        }

        // Skip effect opcodes when condition is false
        // This handles cases where bytecode doesn't have explicit JUMP_IF_FALSE
        if !executor.cond {
            // Skip this opcode. cond will be reset by JUMP_IF_FALSE or end of scope.
            continue;
        }

        // Dispatch to handlers
        match registry.dispatch(state, db, &mut frame.ctx, real_op, v, a, s, ip, &frame.bytecode) {
            HandlerResult::Continue => {},
            HandlerResult::SetCond(c) => executor.cond = c,
            HandlerResult::Suspend => return, 
            HandlerResult::Return => {
                if executor.pop_frame().is_none() {
                    return;
                }
            },
            HandlerResult::Branch(new_ip) => {
                frame.ip = new_ip;
            },
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
            f.ctx.choice_index = -1; // Reset choice index after each instruction
        }
    }

    if _id.is_some() {
        state.clear_execution_id();
    }
}

/// Helper to check if an opcode is a condition
pub fn is_condition_opcode(op: i32) -> bool {
    let real_op = if op >= 1000 { op - 1000 } else { op };
    real_op >= 200 && real_op <= 255
}

pub fn process_trigger_queue(state: &mut GameState, db: &CardDatabase) {
    while let Some((cid, ab_idx, ctx, is_live, _trigger)) = state.core.trigger_queue.pop_front() {
        // Generate a new ID for the activation
        state.generate_execution_id();
        
        let (bytecode, costs) = if is_live {
            let ab = &db.get_live(cid).unwrap().abilities[ab_idx as usize];
            (&ab.bytecode, &ab.costs)
        } else {
            let ab = &db.get_member(cid).unwrap().abilities[ab_idx as usize];
            (&ab.bytecode, &ab.costs)
        };
        
        if costs::pay_costs_transactional(state, db, costs, &ctx) {
            resolve_bytecode(state, db, bytecode, &ctx);
        }
        
        state.clear_execution_id();
    }
}

pub fn get_ability_uid(source_type: u8, id: u32, ab_idx: u32) -> u32 {
    ((source_type as u32) << 24) | ((id & 0xFFFF) << 8) | (ab_idx & 0xFF)
}

pub fn check_once_per_turn(state: &GameState, p_idx: usize, source_type: u8, id: u32, ab_idx: usize) -> bool {
    let uid = get_ability_uid(source_type, id, ab_idx as u32);
    !state.core.players[p_idx].used_abilities.contains(&uid)
}

pub fn consume_once_per_turn(state: &mut GameState, p_idx: usize, source_type: u8, id: u32, ab_idx: usize) {
    let uid = get_ability_uid(source_type, id, ab_idx as u32);
    state.core.players[p_idx].used_abilities.push(uid);
}
