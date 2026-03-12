---
name: qa_rule_verification
description: Unified workflow for extracting official Q&A data, maintaining the verification matrix, and implementing engine-level rule tests.
---

# Q&A Rule Verification Skill

This skill provides a standardized approach to ensuring the LovecaSim engine aligns with official "Love Live! School Idol Collection" Q&A rulings.

## 1. Components
- **Data Source**: `data/qa_data.json` (Managed by `tools/qa_scraper.py`).
- **Matrix**: [.agent/skills/qa_rule_verification/qa_test_matrix.md](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/.agent/skills/qa_rule_verification/qa_test_matrix.md) (Comprehensive 206-item matrix).
- **Test Suites**:
    - **Engine (Rust)**: `engine_rust_src/src/qa_verification_tests.rs`.
    - **Data (Python)**: `tests/test_qa_data.py`.
- **Tools**:
    - `tools/gen_full_matrix.py`: Re-generates the comprehensive matrix from JSON.

## 2. Workflows

### Phase 1: Data Update
1. Run `uv run python tools/qa_scraper.py` to fetch latest rulings.
2. Verify the Rust test harness still compiles: `cargo test --manifest-path engine_rust_src/Cargo.toml --no-run`.

### Phase 2: Categorization
1. Sync the matrix: `uv run python tools/qa_matrix_gen.py`.
2. Review `qa_test_matrix.md` to identify new testable rules (`Engine (Rule)` category).

### Phase 3: Engine Verification (Rust)
1. Identify the rule ID (e.g., Q195).
2. Implement a focused test in `qa_verification_tests.rs`.
3. Run `cargo test qa_verification_tests` to verify compliance.
4. Update `qa_test_matrix.md` status to `[x]`.

## 3. Best Practices
- **Isolation**: Use `create_test_state()` and `create_test_db()` for each test to avoid side effects.
- **Card IDs**: Use `add_card()` to mock specific card abilities if the exact card isn't in the test DB.
- **Traceability**: Always link tests to their QID in doc comments or test names.
- **Negative Tests**: When the official answer is "No", ensure the engine rejects the action or condition.
