---
description: Unified workflow for end-to-end verification of card abilities, emphasizing QA coverage and bytecode decoding.
---
# Ability Verification Workflow

> [!IMPORTANT]
> The biggest risk in the engine is the gap between the Japanese ability text and the intended behavior. The parser cannot verify semantics. Tests are the absolute source of truth.

## Phase 1: Identify the Intended Behavior
1. Use `uv run python tools/card_finder.py <card_no>` to pull up the card's full profile.
2. Read the Japanese ability text (`ability`).
3. **CRITICAL**: Check if the card has any associated QA data in `data/qa_data.json` or by using the `/analyze_card` workflow. QA items (e.g., `Q123`) define the edge-case rulings you *must* test.
4. **View Coverage Databases**: 
   - Open `reports/qa_coverage_matrix.md` to see which official QA rulings have existing engine tests and what those tests test. 
   - Open `data/consolidated_abilities.md` to find known Rust test functions for every card sharing an ability text.
   - Run `uv run python tools/analysis/audit_qa_coverage.py` to regenerate the QA matrix if needed.
   - Run `uv run python tools/analysis/generate_consolidated_file.py` to regenerate the abilities reference if needed.

## Phase 2: Check the Compilation Pipeline
1. In the `card_finder.py` output, review the `Decoded Bytecode`.
   - The engine uses `tools/verify/bytecode_decoder.py` to translate raw integers into human-readable operations (e.g., `DRAW | v(Count):1`).
2. Ask yourself: *Does this decoded sequence logically match the Japanese text and QA rulings?*
3. If the bytecode is wrong or empty, the pseudocode is incorrect or the parser missed something (e.g., an unrecognized alias).
4. **Fixing Pseudocode**:
   - For standard abilities, update `data/consolidated_abilities.json`.
   - For unique variants (e.g., cards with identical text but different trait filters), use `data/manual_pseudocode.json` as an override.
   - Run `uv run python -m compiler.main` to recompile.
   - Run `card_finder.py` again to verify the new decoded bytecode.

## Phase 3: Rust Test Verification (The Source of Truth)
If the card has multiple triggers (complex) or associated QA rulings, it **MUST** have a Rust test.

1. **Check Existing Tests**:
   - Use `grep_search` in `engine_rust_src/src` for the card number (`PL!...`) OR the QA ID (`Q123`).
   - Many QA tests are in `engine_rust_src/src/qa_verification_tests.rs` or `repro_flags.rs`.
2. **Write a New Test**:
   - If no test exists, create one in the appropriate test file.
   - Set up the exact board state required to trigger the ability or recreate the QA scenario.
   - Assert the state deltas (e.g., did the hand size increase? Was the energy tapped?).
3. **Run the Test**:
   - `cd engine_rust_src && cargo test <test_name>`

## Phase 4: Hardcoded Bypass Check
> [!WARNING]
> The engine uses an optimization file (`hardcoded.rs`) for simple abilities.
- If you fixed a broken "simple" ability (like a flat buff) and made it complex (added a condition), the engine will silently ignore your new bytecode.
- **Always run**: `uv run python tools/codegen_abilities.py` after modifying abilities to regenerate the optimization overrides.
