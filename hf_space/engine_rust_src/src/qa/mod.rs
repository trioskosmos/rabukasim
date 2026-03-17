//! Official Q&A Rule Verification Test Suite (163 tests)
//!
//! This module contains automated tests for every official Q&A ruling
//! from the Love Live Card Game documentation. Each test validates
//! a specific game rule, edge case clarification, or interaction.
//!
//! # Structure
//!
//! Tests are organized into batches by question number and coverage area:
//!
//! - **batch_1.rs**: Q1-Q50 - Early clarifications (basic rules, common scenarios)
//! - **batch_2.rs**: Q51-Q100 - Mid-game mechanics (phase transitions, interactions)
//! - **batch_3.rs**: Q101-Q150 - Advanced interactions (complex card abilities)
//! - **batch_4_unmapped_qa.rs**: Q151+ - Latest rulings and edge cases
//! - **batch_card_specific.rs**: Card-specific ability clarifications
//! - **card_specific_ability_tests.rs**: Real database card edge cases
//!
//! # Coverage Metrics
//!
//! - **Total Q&A Entries**: 300+
//! - **Automated Tests**: 163
//! - **Coverage**: ~54% of official Q&A entries
//! - **Priority**: Tests focus on high-impact mechanics
//!
//! # Key Test Examples
//!
//! | Test | Q# | Topic | Impact |
//! |------|----|----|--------|
//! | test_q166_reveal_until_refresh | Q166 | REVEAL_UNTIL refresh semantics | High |
//! | test_q211_sunny_day_song | Q211 | Live ability targeting | High |
//! | test_q191_daydream_mermaid | Q191 | Mode selection | Medium |
//! | test_q149_heart_total_count | Q149 | Stat calculations | High |
//!
//! # Running QA Tests
//!
//! ```bash
//! # All QA tests
//! cargo test --lib qa
//!
//! # Specific batch
//! cargo test --lib qa::batch_4
//!
//! # Single Q&A test
//! cargo test --lib test_q166
//! cargo test --lib test_q211
//!
//! # With output
//! cargo test --lib qa::batch_4 -- --nocapture
//! ```
//!
//! # Adding New Q&A Tests
//!
//! When a new official Q&A ruling is published:
//!
//! 1. **Identify Q# and topic** from official documentation
//! 2. **Create test** in appropriate batch file
//! 3. **Name** as `test_q###_brief_topic_description`
//! 4. **Document** the official Q&A reference and expected outcome
//! 5. **Implement** minimal test harness to verify the ruling
//! 6. **Run** `cargo test --lib test_q###` to verify
//!
//! ## Example Test Template
//!
//! ```rust
//! #[test]
//! fn test_q###_rulling_topic() {
//!     // Q###: [Official Japanese ruling text]
//!     // A###: [Official answer/clarification]
//!
//!     let db = load_real_db();
//!     let mut state = create_test_state();
//!
//!     // ... setup game state ...
//!
//!     // Verify expected behavior
//!     assert_eq!(expected, actual);
//! }
//! ```
//!
//! # Known Gaps
//!
//! - Some Q&A entries are declarative (no actionable test)
//! - Some entries require real card database (implemented)
//! - Some entries require complex state setup (backlog)
//!
//! See `batch_card_specific_real_gaps.rs` for coverage gaps analysis.
//!
//! # Performance
//!
//! - **QA Tests Only**: ~5 seconds (163 tests parallelized)
//! - **Per Test**: Average 30ms
//! - **DB Load**: ~0.5 seconds (one-time)

mod batch_1;
mod batch_2;
mod batch_3;
mod batch_4_unmapped_qa;
mod batch_card_specific;
mod batch_card_specific_real_gaps;
mod card_specific_ability_tests;
mod comprehensive_qa_suite;
mod drafts;
mod test_rule_gaps;
mod test_critical_gaps;
