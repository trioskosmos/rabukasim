---
description: How to create a new QA test based on existing verified tests
---

# Creating a QA Test

When you need to create a new QA rule verification test or debug repro test, follow these steps to ensure consistency with previously successful tests.

0. Use analyze_card.md to analyse any cards needed.

1. **Find an Existing Test as a Template**
   Use `grep_search` or `view_file` to review an existing successful test file in `engine_rust_src/tests/`. For example, checking `repro_hime_rurino.rs` or `repro_pb1_018_exhaustive.rs`.

2. **Understand the Rust Test Setup**
   Notice how existing tests are structured:
   - They import dependencies: `use engine_rust::core::logic::*;` and `use engine_rust::test_helpers::*;`
   - They call `let db = load_real_db();` to get the production card database.
   - They call `let mut state = create_test_state();` to initialize a pristine game state.
   - They manipulate the state directly (e.g., `state.core.players[p_idx].hand = vec![card_id].into();`) to set up the scenario exactly where the interaction happens.
   - They inject a `PendingInteraction` or trigger `state.step(...)` to force the logic to execute.

3. **Locate the Target Card Data**
   Use the `unified_card_search` skill (e.g., evaluating the SKILL.md or running `uv run python tools/card_finder.py "<Card No>" -o reports/diag.md`) to find the exact internal engine IDs (`id`) of the cards involved in your test scenario from the DB.
   **CRITICAL POLICY**: YOU MUST USE REAL COMPILED BYTECODE FROM REAL CARDS. NEVER MOCK ABILITIES OR BYTECODE.

4. **Draft the Test in a Dedicated Rust File**
   If this test is for general QA rule verification, either add it to `engine_rust_src/src/qa_verification_tests.rs` or create an isolated file like `engine_rust_src/src/repro/repro_q103_catchu.rs`.
   - Setup the DB using `let db = load_real_db();` and State using `let mut state = create_test_state();`.
   - Look up definitions dynamically if needed: `db.id_by_no("PL!SP-pb1-023-L").unwrap_or(0)`
   - **MANDATORY DOCUMENTATION**: In the test comments, you MUST explicitly state the testing context:
     - **Ability**: The exact Japanese ability text (or english pseudocode) being tested.
     - **Intended Effect**: What the bytecode/engine is specifically trying to accomplish.
     - **QA**: The QA reference ID (e.g., Q103) and a brief summary of the official ruling.
   - Execute the test logic.
   - Assert the expected engine behavior explicitly.

5. **Run the Test**
   Execute the test using `cargo test --test <filename>` from `engine_rust_src`. Observe the output and reiterate on your test configuration if it panics unexpectedly.

6. **Update the QA Matrix**
   Once the test definitively proves the engine handles the rule correctly, update `.agent/skills/qa_rule_verification/qa_test_matrix.md` with an `[x]` to mark the specific Q&A rule as verified.
