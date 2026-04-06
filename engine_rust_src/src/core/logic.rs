// Ability system entry point.
// Runtime execution is frame-first in Rust, with semantic/effect data loaded
// from compiled JSON and legacy bytecode/interpreter compatibility still present
// in some tests and fallback paths.

pub mod ability_patterns;
mod ability_hydration;
pub mod action_factory;
pub mod action_gen;
pub mod ai_encoding;
pub mod card_db;
pub mod constants;
pub mod diagnostics;
pub mod execution;
pub mod filter;
pub mod game;
mod game_action_processor;
mod game_logging;
mod game_rules_ext;
mod game_setup;
mod game_trigger;
pub mod handlers;
pub mod heart_semantics;
pub mod interpreter;
pub mod models;
pub mod performance;
pub mod performance_allocation;
pub mod performance_requirements;
pub mod player;
pub mod rules;
pub mod standard_state;
pub mod state;
pub mod test_coverage;
pub mod turn_sequencer;

// Constants
pub use constants::*;

// Re-export core structures
pub use card_db::{CardDatabase, LiveCard, MemberCard, LOGIC_ID_MASK};
pub use action_factory::ActionFactory;
pub use handlers::{
    MainPhaseController, MulliganController, ResponseController, TurnController,
    TurnPhaseController,
};
pub use player::PlayerState;
pub use standard_state::StandardizedState;
pub use state::{ActionReceiver, CoreGameState, DebugState, GameState, UIState};
pub use models::{
    Ability, AbilityContext, PendingInteraction, Effect, AbilityFrame, Condition, Cost,
    DeckStats, EnergyCard, FrameProgram,
};
pub use interpreter::suspension::suspend_interaction;

// Re-export enums and constants
pub use crate::core::enums::*;
pub use crate::core::hearts::HeartBoard;

// Heuristic utility re-exports
pub use performance::PerformanceResults;
pub use rules::get_effective_blades;
