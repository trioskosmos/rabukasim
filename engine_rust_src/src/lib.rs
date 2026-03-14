//! Love Live Card Game Rust Engine - Test Suite Organization
//!
//! # Test Architecture Overview
//!
//! This engine includes 568 comprehensive tests organized into multiple categories:
//!
//! ## Test Categories
//!
//! ### 1. QA Verification Tests (163 tests)
//! - **Location**: `qa/` module and `qa_verification_tests.rs`
//! - **Purpose**: Official Q&A rule clarifications from game documentation
//! - **Coverage**: Q1-Q300+ official rulings
//! - **Command**: `cargo test --lib qa`
//!
//! ### 2. Opcode & Bytecode Tests (~150 tests)
//! - **Locations**: `opcode_*.rs` modules (opcode_tests, opcode_coverage_gap_2, etc.)
//! - **Purpose**: Individual bytecode instruction validation
//! - **Coverage**: O_DRAW, O_REVEAL_UNTIL, O_LOOK_DECK, etc.
//! - **Command**: `cargo test --lib opcode`
//!
//! ### 3. Mechanics & Game Flow Tests (~180 tests)
//! - **Locations**: `*_tests.rs` modules (mechanics_tests, game_flow_tests, etc.)
//! - **Purpose**: High-level game mechanics and interactions
//! - **Coverage**: Phase transitions, card interactions, state consistency
//! - **Command**: `cargo test --lib mechanics`
//!
//! ### 4. Edge Cases & Stress Tests (~75 tests)
//! - **Locations**: Various regression and special-case test files
//! - **Purpose**: Rare scenarios, stress tests, regression prevention
//! - **Coverage**: Complex bytecode sequences, boundary conditions
//! - **Command**: `cargo test --lib edge` or `cargo test --lib stress`
//!
//! ## Performance Metrics
//!
//! - **Full Suite**: 568 tests in ~17-18 seconds (parallelized)
//! - **Single-threaded**: ~70 seconds (deterministic ordering)
//! - **Parallelization**: Auto-scales to CPU core count (4-8 threads typical)
//! - **Memory**: ~200MB peak during execution
//!
//! ## Running Tests
//!
//! ```bash
//! # All tests with parallelization (default, ~18s)
//! cargo test --lib
//!
//! # Single category
//! cargo test --lib qa
//! cargo test --lib opcode
//! cargo test --lib mechanics
//!
//! # Deterministic (single-threaded, ~70s)
//! cargo test --lib -- --test-threads=1
//!
//! # Specific test
//! cargo test --lib test_q166_reveal_until_refresh
//!
//! # With output
//! cargo test --lib test_opcode_draw -- --nocapture
//! ```
//!
//! ## Test File Organization
//!
//! **Current Structure** (src/ directory):
//! ```text
//! src/
//! ├── qa/                          # QA rule verification (mod)
//! │   ├── batch_1.rs
//! │   ├── batch_2.rs
//! │   ├── batch_3.rs
//! │   ├── batch_4_unmapped_qa.rs
//! │   └── ...
//! ├── qa_verification_tests.rs     # Additional QA tests
//! ├── opcode_tests.rs              # Basic opcode tests
//! ├── opcode_coverage_gap_2.rs     # Coverage gap analysis
//! ├── opcode_missing_tests.rs      # Missing opcode implementations
//! ├── opcode_rigor_tests.rs        # Rigorous opcode validation
//! ├── mechanics_tests.rs           # Game mechanics
//! ├── game_flow_tests.rs           # Phase transitions
//! ├── card_interaction_tests.rs    # Card interactions
//! ├── regression_tests.rs          # Regression prevention
//! └── [other test files]
//! ```
//!
//! **Planned Structure** (tests/ directory reference):
//! See `../tests/README.md` for future reorganization planning.
//! This provides a blueprint for scaling test organization.
//!
//! ## Adding New Tests
//!
//! ### For a New Q&A Ruling (Q301+)
//! 1. Add test to `src/qa/batch_4_unmapped_qa.rs` or create `batch_5.rs`
//! 2. Name: `test_q###_descriptive_name`
//! 3. Add official Q&A reference as comment
//! 4. Test command: `cargo test --lib test_q###`
//!
//! ### For a New Opcode Feature
//! 1. Add test to appropriate `opcode_*.rs` file
//! 2. Name: `test_opcode_name_scenario`
//! 3. Add opcode documentation comment
//! 4. Test command: `cargo test --lib test_opcode_name`
//!
//! ### For Regression Testing
//! 1. Add test to `regression_tests.rs`
//! 2. Name: `test_regression_issue_number` or `test_regression_card_name`
//! 3. Reference the issue/bug fixed
//! 4. Test command: `cargo test --lib test_regression`
//!
//! ### For Stress/Edge Cases
//! 1. Add test to `../tests/edge_cases/stress_rare_bytecode_sequences.rs`
//! 2. Name: `test_stress_scenario_name`
//! 3. Document complexity metrics (bytecode length, nesting depth, etc.)
//! 4. Test command: `cargo test --lib test_stress`
//!
//! ## Test Isolation Issue (Known)
//!
//! Q166 test currently fails in full suite due to test state contamination
//! but passes in isolation. Investigation ongoing. Workaround:
//! ```bash
//! cargo test --lib test_q166
//! ```
//! All 567 other tests pass independently.

// Incremental build verification comment
pub mod core;
#[cfg(feature = "extension-module")]
pub mod py_bindings;
pub mod repro;
pub mod test_helpers;
#[cfg(feature = "wasm")]
pub mod wasm_bindings;

#[cfg(test)]
mod ability_tests;
#[cfg(test)]
mod baton_pass_tests;
#[cfg(test)]
mod card_interaction_tests;
#[cfg(test)]
mod comprehensive_tests;
#[cfg(test)]
mod coverage_gap_tests;
#[cfg(test)]
mod database_tests;
#[cfg(test)]
mod deck_refresh_tests;
#[cfg(test)]
mod game_end_tests;
#[cfg(test)]
mod game_flow_tests;
#[cfg(test)]
mod mechanics_tests;
#[cfg(test)]
mod meta_rule_tests;
#[cfg(test)]
mod opcode_coverage_gap_2;
#[cfg(test)]
mod opcode_missing_tests;
#[cfg(test)]
mod opcode_tests;
#[cfg(test)]
mod phase_transition_tests;
#[cfg(test)]
mod regression_tests;
#[cfg(test)]
mod response_flow_tests;
#[cfg(test)]
mod rule_parity_regression_tests;
#[cfg(test)]
mod size_test;
#[cfg(test)]
mod stabilized_tests;
#[cfg(test)]
mod structural_tests;
#[cfg(test)]
mod tests;
#[cfg(test)]
mod tie_breaker_tests;
#[cfg(test)]
mod trigger_tests;
#[cfg(test)]
mod verification_tests;
#[cfg(test)]
mod wave2_tests;
#[cfg(test)]
mod wave6_tests;
// #[cfg(test)]
// // mod archetype_runner;
#[cfg(test)]
mod count_group_tests;
#[cfg(test)]
mod enforcement_tests;
#[cfg(test)]
mod filter_audit_tests;
#[cfg(test)]
mod qa_verification_tests;
#[cfg(test)]
mod rule_alignment_tests;
#[cfg(test)]
mod semantic_assertions;
#[cfg(test)]
mod qa;

#[cfg(test)]
mod meta_rule_card_tests;

#[cfg(test)]
mod opcode_rigor_tests;

#[cfg(test)]
mod untested_opcode_tests;

#[cfg(test)]
mod new_opcode_tests;

#[cfg(test)]
mod alphazero_verification_tests;
#[cfg(test)]
mod debug_q203;
#[cfg(test)]
mod unique_ability_tests;

// #[cfg(test)]
// mod gpu_smoke_tests;  // Requires gpu_manager module (not yet implemented)

#[cfg(test)]
mod manual_verification_tests;

#[cfg(test)]
mod vanilla_encoding_tests;

#[cfg(test)]
mod debug_consts;

// #[cfg(test)]
// mod gpu_parity_tests;

// pub mod repro_pl_bp3_004; // Deleted

#[cfg(feature = "extension-module")]
use pyo3::prelude::*;

#[cfg(feature = "extension-module")]
#[pymodule]
fn engine_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    py_bindings::register_python_module(m)
}
