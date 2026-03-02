---
description: Advanced workflow for professional QA testing and card logic verification
---

# Professional QA Testing Workflow

This workflow encapsulates the "First-Principles" approach to verifying card logic in RabukaSim. Use this when a card "isn't working" or when implementing complex QA rules.

## 1. The "Source of Truth" Investigation
Before writing a single line of test code, you must understand exactly what the engine sees.

1.  **Generate a UTF-8 Report**: NEVER trust terminal output for Japanese characters or complex bytecode.
    ```bash
    uv run python tools/card_finder.py "<CARD_NO>" --output reports/analysis.md
    ```
2.  **Verify the Stack**: Open the report and check the chain:
    - **JP Text**: What is the literal intent?
    - **Pseudocode**: How did the compiler translate it?
    - **Bytecode**: What are the literal opcodes and parameters? (e.g., `C_HAS_KEYWORD`, `Val:3`)
3.  **Cross-Reference Logic**: Find the opcode in `engine_rust_src/src/core/enums.rs` and then find its handler in `interpreter/mod.rs` or `conditions.rs`.

## 2. Differentiating "Test Errors" vs "Engine Gaps"
When a test fails (e.g., `Hand size 0 != 5`), follow this diagnostic tree:

1.  **Was the Ability Triggered?**
    - Check if `trigger_event` was called for the correct `TriggerType` (e.g., `OnPlay`).
    - Use `--nocapture` to see if the engine logged "TRIGGER: [OnPlay] Triggered for...".
2.  **Did the Conditions Pass?**
    - Note that there are TWO layers of conditions:
        - **JSON Conditions**: Checked at the trigger level in `game.rs`.
        - **Bytecode Opcodes**: Check inline within `resolve_bytecode`.
    - If a condition failed, investigate `conditions.rs`. **CRITICAL**: Check if the engine field (e.g., `play_count_this_turn`) even exists!
3.  **Was the Setup Valid?**
    - **Energy**: Use real energy IDs from `db.energy_db` to ensure cost payment logic works.
    - **Deck**: Ensure the deck has enough cards for effects like `DRAW_UNTIL(5)`.
    - **Slots**: Remember that playing a card often "locks" a slot for that turn. Play to an open slot (e.g., slot 2) if testing multiple plays.

## 3. Implementation First, Assertion Second
If you discover a missing engine field or a broken opcode handler:

1.  **Implement the missing logic**: (e.g., Adding `play_count_this_turn` to `PlayerState`).
2.  **Verify Reset Logic**: Ensure the new field is reset at turn start in `untap_all` and copied in `copy_from`.
3.  **Update Handlers**: Adjust `conditions.rs` or `handlers/` to use the new field.
4.  **Run the Test Again**: Only assert success once the engine is physically capable of achieving the result.

## 4. Test Case Robustness Policy
- **Prefer No-Ability Fillers**: When simulating multiple plays, use filler cards with `card.abilities.is_empty()` to prevent side-effects.
- **Dynamic Lookups**: Use `db.id_by_no()` instead of hardcoded numbers.
- **Explicit Logging**: Set `state.ui.silent = true` but use `println!` for controlled debugging inside the test.
- **Safety**: Always run with `--no-default-features` on Windows to avoid `onnxruntime.dll` issues unless specifically testing AI.

## 5. Completing the Loop
1. **Remove Ignored Status**: If you temporarily added `#[ignore]` during the gap analysis, remove it.
2. **Verify Full Suite**: Run the whole QA module to ensure no regressions.
3. **Update Matrix**: Mark the rule as verified in `qa_test_matrix.md`.
