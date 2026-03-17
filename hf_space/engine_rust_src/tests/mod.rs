//! Engine Test Suite - Organization Guide
//!
//! # Test Categorization Strategy
//!
//! This test suite is organized into four primary categories:
//! 1. **QA Tests** - Official rules and clarifications
//! 2. **Opcode Tests** - Bytecode instruction validation
//! 3. **Mechanics Tests** - Game flow and interactions
//! 4. **Edge Cases** - Stress tests and rare scenarios
//!
//! # Directory Structure
//!
//! ```
//! tests/
//! ├── README.md               # This directory's documentation
//! ├── qa/                     # Official Q&A rule tests (reference)
//! │   └── mod.rs              # QA test organization notes
//! ├── opcodes/                # Opcode instruction tests
//! │   └── mod.rs              # Opcode test documentation
//! ├── mechanics/              # Game mechanics tests
//! │   └── mod.rs              # Mechanics test documentation
//! └── edge_cases/             # Stress and rare scenario tests
//!     ├── mod.rs              # Edge case documentation
//!     └── stress_rare_bytecode_sequences.rs  # Complex bytecode stress tests
//! ```
//!
//! **Note**: The actual QA tests remain in `src/qa/` because they depend on
//! internal module access and the real card database. This organization serves
//! as a reference and planning structure for future reorganization.
//!
//! # Performance Characteristics
//!
//! - **Full Suite**: 568 tests in ~17 seconds (parallelized)
//! - **Single-threaded**: ~70 seconds (for deterministic debugging)
//! - **Memory**: ~200MB peak during execution
//! - **Parallelization**: 4-8 threads (adjustable with --test-threads=N)
//!
//! # Adding New Tests
//!
//! 1. Determine category (qa, opcodes, mechanics, or edge_cases)
//! 2. Create test file in appropriate subdirectory
//! 3. Add detailed doc comments explaining what is tested
//! 4. Use existing test helpers from crate root
//! 5. Run `cargo test --lib` to verify discovery
//!
//! ## Test Naming Conventions
//!
//! - QA tests: `test_q###_brief_description`
//! - Opcode tests: `test_opcode_name_scenario`
//! - Mechanics tests: `test_mechanic_name_scenario`
//! - Stress tests: `test_stress_scenario_name`
//! - Regression tests: `test_regression_issue_number`

// pub mod qa;
// pub mod opcodes;
// pub mod mechanics;
// pub mod edge_cases;
