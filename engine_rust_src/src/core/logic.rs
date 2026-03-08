pub mod action_factory;
pub mod action_gen;
pub mod ai_encoding;
pub mod card_db;
pub mod constants;
pub mod diagnostics;
pub mod execution;
pub mod filter;
pub mod game;
pub mod handlers;
pub mod interpreter;
pub mod models;
pub mod performance;
pub mod player;
pub mod rules;
pub mod state;
pub mod standard_state;

// Constants
pub use constants::*;

// Re-export core structures
pub use action_factory::ActionFactory;
pub use card_db::{CardDatabase, LiveCard, MemberCard, LOGIC_ID_MASK};
pub use handlers::{
    MainPhaseController, MulliganController, ResponseController, TurnController,
    TurnPhaseController,
};
pub use player::PlayerState;
pub use state::{ActionReceiver, CoreGameState, DebugState, GameState, UIState};
pub use standard_state::StandardizedState;

// Re-export models
pub use models::{
    Ability, AbilityContext, Condition, Cost, Effect, EnergyCard, PendingInteraction, TurnEvent,
};

// Re-export enums and constants
pub use crate::core::enums::*;

// Heuristic utility re-exports
pub use interpreter::conditions::{check_condition, check_condition_opcode};
pub use interpreter::costs::{check_cost, pay_cost};
pub use interpreter::suspension::suspend_interaction;
pub use interpreter::{
    check_once_per_turn, consume_once_per_turn, process_trigger_queue, resolve_bytecode,
};
pub use rules::get_effective_blades;
pub use performance::PerformanceResults;

// Heuristic flags (moved to constants.rs)
// They are re-exported via 'pub use constants::*;' above
