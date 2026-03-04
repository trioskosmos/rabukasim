---
description: Comprehensive workflow for end-to-end debugging of card logic issues, from identification to verification.
---

# Debug Card Workflow

Use this workflow when a card effect is not triggering, behaving incorrectly, or causing crashes. This process ensures you identify the disconnect between the source data, the compiled logic, and the engine execution.

## Phase 1: Identification & Analysis

1. **Instant Triage**: Use `test_pseudocode.py` to check the current logic, JP text, and test coverage in one shot.
   ```powershell
   uv run python tools/test_pseudocode.py --card "<ID_OR_NO>"
   ```

2. **Full Analysis**: If you need cross-references like QA rulings or shared cards, use `card_finder.py`.
   ```powershell
   uv run python tools/card_finder.py "<ID_OR_NO>" --output "reports/debug_<ID>.md"
   ```

2. **Verify against Metadata**: Compare the opcodes in the report with [generated_metadata.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/generated_metadata.py).
   - Check if the opcode name (e.g., `RECOVER_LIVE`) matches the intended manual pseudocode.
   - If the report shows `META_RULE` (29) for a specific trigger/effect, it likely means the compiler failed to match a pattern.

## Phase 2: Compiler Verification

1. **Check Parser Aliases**: Look at [parser_v2.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/parser_v2.py) constants:
   - `TRIGGER_ALIASES`
   - `EFFECT_ALIASES`
   - `EFFECT_ALIASES_WITH_PARAMS`
   - `CONDITION_ALIASES`

2. **Verify Patterns**: If the alias exists but the bytecode is still wrong, check the regex patterns in `compiler/patterns/`.

3. **Recompile**: After making changes, always recompile:
   ```powershell
   uv run python -m compiler.main --cards "<CARD_NO>"
   ```

## Phase 3: Engine Verification (Rust)

1. **Create Repro Test**: If the logic compiles correctly but fails at runtime, create a Rust repro test in `engine_rust_src/src/repro/` (or `qa_verification_tests.rs`).
   - Use existing repro files as templates.
   - Run the test: `cd engine_rust_src; cargo test --bin test_repro_<NAME> -- --nocapture`

2. **Advanced Engine Tracing (Suspension & Handlers)**: If a test fails due to incorrect phase transitions or silent fall-throughs:
   - **Enable Debug Mode in Test**: Add `state.debug.debug_mode = true;` to your test setup. This enables verbose logging in handlers.
   - **Inject Printlns**: Temporarily inject `println!` statements into the core execution handlers (`interpreter.rs` or `suspension.rs`) to trace the interaction stack and `ctx` state.
   - **Common Suspects**: Check if `suspend_interaction` is incorrectly returning `false` (skipping a prompt), or if action IDs (like `HAND_SELECT` vs `STAGE_SLOTS`) in `handle_response` are misaligned with expected opcode inputs.

3. **Check Logs**: If using the web UI, check the `launcher` console or use `PerformanceMonitor` to see execution steps.

## Phase 4: Verification

1. **Regenerate Report**: Run Phase 1 Step 1 again to confirm the bytecode now matches the intended logic.
2. **Standard Tests**: Run `uv run pytest` and `cd engine_rust_src; cargo test` to ensure no regressions.
