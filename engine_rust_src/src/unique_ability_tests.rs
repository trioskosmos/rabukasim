//! Unique ability opcode tests
//!
//! NOTE: Previous tests in this file used mocked bytecode and had zero assertions.
//! They were removed as part of the Test Integrity Audit (see SKILL.md §11.7).
//!
//! Real opcode coverage is provided by:
//! - `stabilized_tests.rs` (integration tests with real cards)
//! - `repro/repro_card_*.rs` (reproduction tests with real compiled bytecode)
//! - `semantic_assertions.rs` (semantic mass verification)
//! - `crash_triage.rs` (fault isolation across all abilities)
//!
//! To add new opcode tests, use `test_helpers::load_real_db()` and find a real card
//! that uses the opcode. Run `uv run python .agent/skills/ability_verification/scripts/analyze_test_mocks.py`
//! to verify no mocked bytecode crept in.
