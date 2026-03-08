---
description: Unified workflow for end-to-end development, debugging, and verification of card abilities.
---

# Ability Development Workflow

Use this workflow to implement new cards, fix broken logic, or verify bytecode.

## Phase 1: Research & Triage
1. **Analyze Card**: `uv run python tools/card_finder.py "<ID>"`
2. **Check Current Status**: `uv run python tools/test_pseudocode.py --card "<ID>"`
3. **Check Official Rules**: Verify against `data/qa_data.json` or `reports/qa_coverage_matrix.md`.

## Phase 2: Logic Refinement
1. **Update Pseudocode**:
   - Edit `data/consolidated_abilities.json` (Standard) or `data/manual_pseudocode.json` (Override).
2. **Compile**: `uv run python -m compiler.main`
3. **Verify Bytecode**: check the "Decoded Bytecode" in `card_finder.py`.

## Phase 3: Engine Verification
1. **Create Repro Test**:
   - Add a test case in `engine_rust_src/src/repro/` or `qa_verification_tests.rs`.
   - Use `load_real_db()` - **NEVER** mock bytecode in high-level tests.
2. **Trace Execution**:
   - Add `state.debug.debug_mode = true` to the test.
   - Run: `cargo test <test_name> --nocapture`.
3. **Check Hardcoded Optimization**:
   - If change isn't reflected, run `uv run python tools/codegen_abilities.py`.

## Phase 4: Final Audit
1. **Semantic Audit**: `cargo test test_semantic_mass_verification`.
2. **Verify Parity**: If parity is critical, use `GpuParityHarness`.
3. **Commit**: Ensure `pre-commit` hooks pass.
