# Opcode Rigor Audit Skill

Unified workflow for assessing the rigor of opcode tests in the LovecaSim engine.

## Context
Opcodes are the core of the card ability logic. While broad "dry run" tests (like `test_dry_run_all_cards`) satisfy coverage metrics, they often lack the rigor to ensure deep behavioral correctness (e.g., proper state transitions, edge case handling, interaction stack resolution).

## Workflow

### 1. Filter Telemetry
Identify opcodes that rely solely on broad sanity checks.
```bash
uv run python -c "log_path = 'engine_rust_src/reports/telemetry_raw.log'; filtered = [l for l in open(log_path, 'r', encoding='utf-8') if 'database_tests::test_dry_run_all_cards' not in l]; open('engine_rust_src/reports/telemetry_filtered.log', 'w', encoding='utf-8').writelines(filtered)"
```

### 2. Map Opcodes to Specialized Tests
Run the analysis script to see which specialized tests hit which opcodes.
```bash
uv run python tools/analyze_filtered_telemetry.py
```

### 3. Assess Rigor Levels
Categorize tests by their depth of verification:
- **Level 1 (Property Check)**: Simply verifies a value changed (e.g., `coverage_gap_tests`).
- **Level 2 (Parity Check)**: Compares outputs between two implementations (e.g., `semantic_assertions`).
- **Level 3 (Functional Behavior)**: Verifies gameplay flow, phase transitions, and interaction stack (e.g., `opcode_missing_tests`, `repro_card_fixes`).

### 4. Identify Gaps
Opcodes with only Level 1 coverage are candidates for "Behavioral Regression" bugs.
## Creating Level 3 Tests (The "Recipe")

A high-rigor (Level 3) test does not just verify state changes; it verifies that the opcode behaves correctly within the context of the game's complex systems (Interaction Stack, Phase Transitions, Trigger Queue).

### Recipe 1: The "Interaction Cycle"
Use this for opcodes that cause pauses or choices (e.g., `O_SELECT_MEMBER`, `O_LOOK_AND_CHOOSE`).
1. **Setup**: Initialize `GameState` and `CardDatabase`.
2. **Execute**: Call `state.resolve_bytecode` or `state.activate_ability`.
3. **Verify Suspension**: Assert `state.phase == Phase::Response` and `state.interaction_stack.len() > 0`.
4. **Action Generation**: Call `state.generate_legal_actions` to ensure the correct action IDs are available.
5. **Resume**: Call `state.step(db, action_id)` or `state.activate_ability_with_choice`.
6. **Final Verify**: Assert the expected end state (e.g., card moved, score changed) AND `state.phase == Phase::Main`.

### Recipe 2: The "Effect Ripple"
Use this for meta-rules or global modifiers (e.g., `O_MODIFY_SCORE_RULE`, `O_GRANT_ABILITY`).
1. **Setup**: Apply the modifier opcode inside a dry execution.
2. **Action**: Perform a standard game action that *should* be modified by the opcode (e.g., score a live, activate an ability).
3. **Assert Modification**: Verify the outcome differs from the default behavior.
4. **Assert Persistence**: Verify if the effect persists or expires correctly across phases/turns.

### Recipe 3: The "Edge Boundary"
Use this for movement or resource opcodes (e.g., `O_SWAP_CARDS`, `O_PAY_ENERGY`).
1. **Empty State**: Test behavior when source/destination zones are empty.
2. **Full State**: Test behavior when destination zones are full (if limits exist).
3. **Insufficient Resources**: Verify correct error handling or "best effort" execution.
## One-Shot Ready Principles
To ensure tests pass on the first attempt ("One-Shot"), follow these heuristics before execution:

### 1. Unified Dispatch Awareness
The engine has transitioned to a **Modular Interpreter** (`src/core/logic/interpreter/handlers/`).
- **Legacy check**: Always verify if the opcode is also implemented in `interpreter_legacy.rs` and check `execution.rs` to see which dispatch path is active.
- **Action**: Apply fixes to BOTH legacy and modular handlers during transitions to avoid stealth bypassing.

### 2. ID Validation (The "Cid-3000" Rule)
Never use arbitrary or "magic" card IDs (e.g., `19`, `99`) in unit tests unless explicitly mapped.
- **Source of Truth**: Consult `create_test_db` in `src/test_helpers.rs` for available unit test archetypes.
- **Rule of Thumb**: Use IDs in the `3000-3500` range (standard members with base cost 1) to avoid `get_member(cid).is_none()` early-return failures.

### 3. State Sanitization
Tests often inherit `GameState::default()`, but specific opcodes require hydrated state.
- **Draw/Move**: Ensure `p.deck` and `p.discard` are populated (default deck is often empty).
- **Cost**: Ensure the target card exists in the `CardDatabase` used by the state.

### 4. Visibility (No-Capture)
Always include debug prints for state transitions (Phase, InteractionStack) and use `Out-File -Encoding utf8` when redirecting output on Windows to prevent `utf-16le` parsing errors in AI tools.
