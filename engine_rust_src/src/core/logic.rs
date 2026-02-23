pub mod game;
pub mod player;
pub mod rules;
pub mod action_gen;
pub mod interpreter;
pub mod performance;
pub mod models;
pub mod ai_encoding;
pub mod handlers;
pub mod card_db;
pub mod execution;
pub mod diagnostics;
pub mod filter;
pub mod action_factory;
pub mod state;

// Constants
pub const ACTION_SPACE: usize = 8192;

// Re-export core structures
pub use state::{GameState, CoreGameState, UIState, DebugState, ActionReceiver};
pub use action_factory::ActionFactory;
pub use player::PlayerState;
pub use handlers::PhaseHandlers;
pub use card_db::{CardDatabase, MemberCard, LiveCard, LOGIC_ID_MASK};

// Re-export models
pub use models::{Ability, AbilityContext, PendingInteraction, Effect, Condition, Cost, TurnEvent, EnergyCard};

// Re-export enums and constants
pub use crate::core::enums::*;

// Heuristic utility re-exports
pub use interpreter::{resolve_bytecode, process_trigger_queue, check_once_per_turn, consume_once_per_turn};
pub use interpreter::conditions::{check_condition, check_condition_opcode};
pub use interpreter::costs::{check_cost, pay_cost};
pub use interpreter::suspension::suspend_interaction_with_db as suspend_interaction;
pub use performance::PerformanceResults;

// Heuristic flags (matching generated_constants.rs types)
pub const FLAG_DRAW: u64 = 1;
pub const FLAG_SEARCH: u64 = 2;
pub const FLAG_RECOVER: u64 = 4;
pub const FLAG_BUFF: u64 = 8;
pub const FLAG_CHARGE: u64 = 16;
pub const FLAG_TEMPO: u64 = 32;
pub const FLAG_REDUCE: u64 = 64;
pub const FLAG_BOOST: u64 = 128;
pub const FLAG_TRANSFORM: u64 = 256;
pub const FLAG_WIN_COND: u64 = 512;
