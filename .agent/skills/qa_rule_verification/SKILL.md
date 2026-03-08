---
name: qa_rule_verification
description: Unified workflow for extracting official Q&A data, maintaining the verification matrix, and implementing engine-level rule tests.
---

# Q&A Rule Verification Skill

This skill provides a standardized approach to ensuring the LovecaSim engine aligns with official "Love Live! School Idol Collection" Q&A rulings.

## 1. Components
- **Data Source**: `data/qa_data.json` (Managed by `tools/qa_scraper.py`).
- **Matrix**: [.agent/skills/qa_rule_verification/qa_test_matrix.md](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/.agent/skills/qa_rule_verification/qa_test_matrix.md) (Automated via `tools/gen_full_matrix.py`).
- **Test Suites**:
    - **Engine (Rust)**: `engine_rust_src/src/qa_verification_tests.rs`, `engine_rust_src/src/qa/batch_card_specific.rs`.
    - **Data (Python)**: `tests/test_qa_data.py`.
- **Tools**:
    - `tools/gen_full_matrix.py`: **[Updater Path]** Re-generates the comprehensive matrix and coverage dashboard.
    - `tools/play_interactive.py`: CLI tool for manual state injection and verification (use `exec` for god-mode).
    - `tools/card_finder.py`: Multi-layer lookup tool for cards and related Q&A rulings.

## 2. Tagging & Identification
- **Test Tags**: Every Rust test MUST be tagged with `#[test]` and follow the naming convention `test_q{ID}_{descriptor}`.
- **Updater**: Always run `uv run python tools/gen_full_matrix.py` after test modifications to sync the matrix.

## 2. Workflows

### Phase 1: Data Update
1. Run `uv run python tools/qa_scraper.py` to fetch latest rulings.
2. Verify JSON integrity: `uv run pytest tests/test_qa_data.py`.

### Phase 2: Matrix Synchronization
1. Sync the matrix: `uv run python tools/gen_full_matrix.py`.
2. Review the **Coverage Summary** at the top of `qa_test_matrix.md`.
3. Identify new testable rules (`Engine (Rule)` category with ℹ️ icon).

### Phase 3: Engine Verification (Rust)
1. Identify the rule ID (e.g., Q195).
2. Use `card_finder.py "Q195"` to find related cards and original ability text.
3. Implement a focused test in `qa_verification_tests.rs`.
   - **CRITICAL:** Include original ability text and QA ruling as comments.
4. Run `cargo test qa_verification_tests` to verify compliance.
5. Re-run `tools/gen_full_matrix.py` to update the ✅ status.

## 3. Best Practices
- **Real Data Only**: **CRITICAL POLICY:** Always use `load_real_db()` and real card IDs. NEVER mock card abilities or bytecode manually via `add_card()` or similar methods.
- **Isolation**: Use `create_test_state()` to ensure a pristine game state for each test.
- **Documentation**: Every test MUST include comments detailing:
  - **Ability**: The relevant card text or pseudocode.
  - **Intended Effect**: What the engine logic is supposed to do.
  - **QA**: The QA ID (e.g., Q195) and official ruling summary.
- **Traceability**: Always link tests to their QID in doc comments or test names.
- **Negative Tests**: When the official answer is "No", ensure the engine rejects the action or condition.
