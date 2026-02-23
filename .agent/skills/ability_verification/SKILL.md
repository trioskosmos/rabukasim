---
name: ability_verification
description: Unified skill for auditing, analyzing, debugging, and reproducing card abilities.
---

# Ability Verification Skill

This skill unifies all workflows for ensuring card abilities are correctly implemented, translated, and presented in the UI.

## Core Capabilities

### 1. Visual Auditing (`generate_report.py`)
Generates an interactive HTML report comparing raw card text, manual pseudocode, and compiled bytecode.
- **Usage**: `uv run python .agent/skills/ability_verification/scripts/generate_report.py`
- **Output**: `reports/ability_audit_visual.html` and `reports/ability_index.json`.

### 2. Card Analysis (`card_analyzer.py` / `card_finder.py`)
Centralized analysis of a card's lifecycle across JSON source files.
- **Usage**: `uv run python tools/card_finder.py <card_no_or_text>`
- **Purpose**: Unified view of Raw JP, Manual Pseudo, and Compiled Bytecode with integrated decoding.

### 2.1 Bytecode Decoding (`bytecode_decoder.py`)
Decodes raw bytecode arrays into human-readable logic.
- **Usage**: `uv run python tools/verify/bytecode_decoder.py "[41, 3, ...]" `
- **Purpose**: Fast understanding of complex attribute filters and opcode sequences.

### 3. Debugging & Reproduction
Systematic workflow for fixing card abilities using reproduction scripts.
- **Workflow**: 
  1. Research with Analyzer.
  2. Create Reproduction (`uv run python tools/create_reproduction.py [CID]`).
  3. Verify conditions (Positive/Negative/Optional).
- **Fast Repro Build**: `cargo build --release; del ..\engine\engine_rust.pyd; copy target\release\engine_rust.dll ..\engine\engine_rust.pyd`

### 4. UI Button Auditing
Ensures button labels are consistent and match premium aesthetics.
- **Usage**: `cargo run --bin audit_buttons` (from `launcher/`)
- **Standard**: Full-width brackets `【】` for JP action types.

## Engine Reference Tables

### Trigger Types
| ID | Name | Japanese | Description |
| :--- | :--- | :--- | :--- |
| 1 | `ON_PLAY` | 登場時 | Played from hand to stage |
| 7 | `ACTIVATED` | 起動 | Manual trigger (usually requires cost/tap) |
| 8 | `ON_LEAVES` | 離脱時 | When member leaves stage/is discarded |

### Effect Types (Common)
| ID | Name | Interaction | Description |
| :--- | :--- | :--- | :--- |
| 0 | `DRAW` | Automatic | Draw cards |
| 17 | `SELECT_MODE`| Choice (MODAL) | Branching logic selection |
| 27 | `LOOK_AND_CHOOSE`| Choice (LIST) | Look at top X and pick |
| 37 | `COLOR_SELECT` | Choice (MODAL) | Select a color for buffs |
| 57 | `OPP_CHOOSE` | Opponent Choice| Forces opponent to select |
| 81 | `ACTIVATE_ENERGY`| Automatic | Untap energy |
| 90 | `PREVENT_BATON_TOUCH`| Automatic | Block baton pass |

## Interaction Patterns

| Type | Examples | UI Component | Resumption Range |
| :--- | :--- | :--- | :--- |
| **Automatic** | `DRAW`, `BUFF`, `ACTIVATE` | None (Overlay) | N/A |
| **Optional** | `PAY_ENERGY(Attr & 0x82)`| Modal (Yes/No) | `550-551` |
| **Modal** | `SELECT_MODE`, `COLOR_SELECT`| Selection Grid | `580+` |
| **List** | `LOOK_AND_CHOOSE` | Card List | `600+` |
| **Targeting** | `TAP_O`, `SELECT_STAGE` | On-Stage Selection | `600-602` |

### Resumption IDs
- `0`: Skip / Done / No
- `500+`: Hand selection
- `550-551`: Yes/No (Generic Optional)
- `570+`: Mode selection
- `580+`: Color selection
- `600+`: On-stage (0-2) or Discard list selection


### Ability Costs
| ID | Name | Description |
| :--- | :--- | :--- |
| 1 | `ENERGY` | Pay/Tap Energy |
| 5 | `SACRIFICE_SELF`| Move self to discard |

### Target Types
| ID | Name | Description |
| :--- | :--- | :--- |
| 0 | `SELF` | Current card / Player |
| 1 | `PLAYER` | The active player |
| 2 | `OPPONENT` | The opponent |

## Best Practices
- **Standard Terminonology**: Always use "Discard" (EN) and "控え室" (JP).
- **Proxy Verification**: Check `reports/all_unique_abilities.md` to see if an identical logic pattern is already verified.
- **Optionality**: marked with `(Optional)` suffix in pseudocode; sets `attr |= 0x02` in bytecode.

## Test Creation Gotchas
- **Empty Deck Auto-Refresh**: If you initialize a test with `GameState::default()`, the deck is empty. The engine's `auto_step` logic will trigger an immediate deck refresh (shuffling discard into deck) if it detects an empty deck during certain phases.
    - **Symptom**: Discard pile "disappears" or resets unexpectedly.
    - **Fix**: Always populate the deck with dummy cards in your test setup if you rely on the discard pile remaining stable.
    ```rust
    // Example: Prevent auto-refresh
    for i in 200..210 { state.players[0].deck.push(i); }
    ```

## 11. Engine Debugging Patterns

Keep these engine-specific behaviors in mind when debugging or writing new tests:

### 11.1 Indexing Conventions
- **Opcode `C_AREA_CHECK` (234)**: Uses **1-based** indexing.
    - `val=1` -> Slot 0 (Left)
    - `val=2` -> Slot 1 (Center)
- **Opcode `C_CTR` (223)**: Direct check for Center (Slot 1).
- **Slot IDs (600-602)**: Used in `Phase::LiveResult` and `O_MOVE_TO_DISCARD` target selection.

### 11.2 Energy Order of Operations
- When `play_member` is called, the **Core Play Cost** is paid *before* the `OnPlay` triggers are executed.
- **Consequence**: If an `OnPlay` ability has an energy cost, the test setup must provide enough untapped energy to cover **both** the play cost and the ability cost.
- **Symptom**: If the test tries to reuse energy indices already tapped by the play cost, the interpreter will stall at `O_PAY_ENERGY` because the selection is ignored.

### 11.3 The universal "Skip" Signal (Choice 99)
- Choice index **`99`** is the standard engine signal for "Skip", "Done", or "Decline".
- Opcode handlers like `O_MOVE_TO_DISCARD` (for costs) and `O_LOOK_AND_CHOOSE` must handle `99` to correctly process optional branches.
- Bytecode with the `Optional` bit set (`attr & 0x02`) will usually suspend for a `YES/NO` (Choice 550/551) before proceeding to the choice index `99` logic.

### 11.4 Manual Bytecode Maintenance
- When writing repro tests with manual bytecode, always check `compiler/parser_v2.py` or `engine/models/opcodes.py` to ensure opcode signatures match.
- **JUMP Pointers**: Always double-check relative jump offsets. One-byte errors can cause the interpreter to land on illegal data or skip intended instructions.

### 11.5 Suspension & Resumption Flow
When debugging softlocks or "double-suspension" bugs:
1. **Instruction Pointer (IP) Alignment**: Verify that `suspend_interaction` saves the `instr_ip` exactly at the current opcode. `resolve_bytecode` must then restore the `choice_index` specifically for that IP.
2. **Interaction Pop Timing**: High-level resumption functions (`activate_ability_with_choice`) MUST pop the interaction stack *before* calling `resolve_bytecode`. If the resumed opcode triggers a new suspension (e.g. for a target slot), it will push its own new interaction. Popping too late causes "shadow" interactions that block the stack.
3. **Choice String Parity**: Resumption logic often hinges on exact string matches (e.g., `OPTIONAL`, `PAY_ENERGY`, `TAP_O`). Ensure the `interpreter.rs` string exactly matches the test's `assert_eq!`.

### 11.6 Hardcoded Ability Compiler Bypass
**CRITICAL**: The Engine uses an auto-generated optimization file (`engine_rust_src/src/core/hardcoded.rs`) to bypass the bytecode interpreter for "simple" abilities (like flat buffs or draws).
- **The Bug**: If you fix a broken or "simple" ability in `cards.json` and it becomes complex (e.g., adding `SELECT_MEMBER` or conditionals), the engine will **silently ignore your new bytecode** and continue executing the old, hardcoded simple logic.
- **The Fix**: ALWAYS run `uv run python tools/codegen_abilities.py` after modifying card abilities to regenerate the hardcoded mappings and ensure complex abilities are correctly handed back to the bytecode interpreter.

## Scale Strategy (High-Speed Verification)

To verify all 755+ cards efficiently, use this three-phase approach.

### Phase 1: Compile-Time Structural Validation
The compiler (`main.py`) runs a structural check on every bytecode array generated.
- **Checks**: Unknown opcodes, JUMP bounds, multiple of 4 length, trailing `O_RETURN`.
- **Location**: `validate_bytecode()` in `compiler/main.py`.

### Phase 2: Crash Triage (Fault Isolation)
Run a batch execution of **every** unique ability signature to catch engine panics.
1.  **Command**: `cd engine_rust_src && cargo test crash_triage -- --nocapture`
2.  **Mechanism**: Uses `std::panic::catch_unwind` to execute all 287+ unique signatures in a single run without aborting on failure.
3.  **Outputs**: 
    - `reports/state_delta_verification.md`: Full audit logs.
    - `reports/crashed_abilities.txt`: Targeted list of crashing cards.

### Phase 3: Semantic Assertion Verification (High Fidelity)
Advanced meaning-driven verification using sequential delta assertions.
1. **Generate Semantic Truth**: `uv run python tools/verify/generate_semantic_truth.py`.
2. **Run Mass Audit**: `cd engine_rust_src && cargo test --lib test_semantic_mass_verification -- --nocapture`
    - Module: `engine_rust_src/src/semantic_assertions.rs`.
    - Logic: Compares real game state deltas (Hand, Energy, Score) against segments interpreted directly from JP text via `SemanticOracleV2`.
3. **Report**: `reports/COMPREHENSIVE_SEMANTIC_AUDIT.md` — Per-card pass/fail with error details.
    - **Baseline (2026-02-23)**: 235 Pass / 297 Fail out of 532 cards (44% pass).

> [!TIP]
> Use `--lib` flag to avoid scanning all binary targets (avoids the noisy "running 0 tests" spam from `src/bin/*.rs`).

### Phase 4: Semantic Audit Triage (Generalized Failure Categories)

The 297 failures from the mass audit generalize into **6 systemic root causes**. Fixing these categories in order of impact will raise the pass rate most efficiently.

#### Category 1: Condition Not Met — 102 cards (34%)
- **Symptom**: `Mismatch HAND_DELTA: Exp 1, Got 0` for abilities with conditions.
- **Root Cause**: The synthetic board state (`setup_oracle_environment`) does not satisfy the ability's condition. E.g., "if you have 2+ success lives" or "if opponent has a tapped member" — the oracle environment doesn't set up the opponent's state or specific card names.
- **Fix**: Enrich `setup_oracle_environment` to populate both players with realistic state (opponent cards, specific group names, baton touch flags, etc.), OR make the oracle skip conditional abilities it can't satisfy.

#### Category 2: Score Delta Zero — 87 cards (29%)
- **Symptom**: `Mismatch SCORE_DELTA: Exp X, Got 0` for live card scoring abilities.
- **Root Cause**: Two sub-problems:
  1. **Constant abilities**: `TriggerType::Constant` effects (e.g., "Score +1 while X") are handled via a shortcut that only checks `live_score_bonus`, but many score bonuses are gated by complex conditions (blade counts, group filters) that the synthetic state doesn't satisfy.
  2. **Live-context abilities**: Score bonuses during `ON_LIVE_SUCCESS` require the game to be in `Phase::Live` with cards in `live_zone`, which the oracle doesn't set up.
- **Fix**: For Constant abilities, pre-populate the state to satisfy common filters. For live-context, transition the game into `Phase::Live` before executing the ability.

#### Category 3: Optional Not Resolved — 43 cards (14%)
- **Symptom**: `Mismatch HAND_DELTA: Exp -1, Got 0` for "手札を1枚控え室に置いてもよい" (you may discard 1).
- **Root Cause**: Optional discard abilities suspend the engine (waiting for user choice). The `resolve_interaction` helper auto-resolves with action `8000`, but the `SELECT_HAND_DISCARD` interaction isn't being picked up — the ability may not fire at all due to a failed precondition (e.g., it's an Activated ability requiring a tap cost that wasn't paid).
- **Fix**: Ensure `resolve_interaction` handles `SELECT_HAND_DISCARD` correctly, and that activated ability costs (tap, energy) are pre-paid in the oracle environment.

#### Category 4: Discard+Draw Hand Mismatch — 25 cards (8%)
- **Symptom**: `Mismatch HAND (Discard Expected): Exp -1, Got 1` or `Got 2`.
- **Root Cause**: Cards with "Draw X, Discard Y" patterns. The oracle expects a net delta of `X-Y`, but the engine draws cards and then suspends for the discard selection. The `resolve_interaction` auto-picks action `8000`, which may not correctly resolve the discard, leaving the hand size at `+X` instead of `X-Y`.
- **Fix**: Improve `resolve_interaction` to properly resolve `SELECT_HAND_DISCARD` interactions by selecting valid hand indices instead of a generic action.

#### Category 5: Heart/Blade Delta Zero — 14 cards (4%)
- **Symptom**: `Mismatch HEART_DELTA: Exp 1, Got 0`.
- **Root Cause**: Heart/blade buffs are often gated by live-phase conditions or specific heart-color filters. The oracle environment doesn't place the game in live context or populate heart metadata on stage members.
- **Fix**: Same as Category 2 — enrich the oracle environment with live-phase context and heart data.

#### Category 6: Energy Cost Zero — 10 cards (3%)
- **Symptom**: `Mismatch ENERGY_COST: Exp 2, Got 0`.
- **Root Cause**: Activated abilities with energy costs require the player to explicitly pay. The oracle auto-resolves interactions but doesn't simulate the "pay energy" step, so the ability never fires.
- **Fix**: In `record_card`, when trigger is `Activated`, ensure the test pre-pays or auto-resolves the energy cost interaction.

#### Oracle Parse Bugs — 6 cards (2%)
- **Symptom**: Wildly wrong expectations like `Exp 7` or `Exp 47`.
- **Root Cause**: The Python `SemanticOracleV2` regex misparses JP text. E.g., "エネルギーが7枚以上ある場合、カードを1枚引く" extracts `7` instead of `1` because it grabs the condition value, not the draw count.
- **Fix**: Improve `SemanticOracleV2.map_expectations()` regex to distinguish condition thresholds from effect quantities.

## 9. Crate-Wide Reliability Audit (Systematic Fix)

When multiple tests fail across different modules, avoid "running in circles" with ad-hoc patches. Follow this systematic process:

### Step 1: Full-Suite Capture
Do not rely on filtered test runs. Capture the entire state of the crate.
- **Command**: `cargo test > all_test_failures.log 2>&1`
- **Categorization**: Extract all `FAILED` lines to `failed_test_list.txt`.

### Step 2: Identify Systematic Threads
Review logs for recurring pattern errors:
- **String Mismatch**: `left: "SELECT_HAND_DISCARD", right: "OPTIONAL"` (Common in interpreter refactors).
- **Turn-State Dependency**: `C_HAS_KWD` failures usually mean `played_group_mask` isn't seeded.
- **Group Dependency**: `C_GRP` failures usually mean mock card groups are missing in `create_test_db`.

### Step 3: Phase 1 - String Standardization
Standardize the `choice_type` strings in `interpreter.rs` FIRST. Sync all test assertions BEFORE moving to logic fixes.
- **Goal**: Clear the "clutter" of string-mismatch failures to reveal actual logic bugs.

### Step 4: Phase 2 - Metadata Seeding
Update `create_test_db` and individual test setups to satisfy requirements (Groups, Attributes, Turn Masks).

### Step 5: Phase 3 - Interaction Logic
Fix interaction leakage (e.g., `choice_index = -1` resets) and opcode branch bugs.
## Gaps & Limitations (Future Audits)

Current auditing tools (`audit_buttons.rs`, `generate_report.py`) have the following known blind spots:

1. **Passive Effect Auditing**:
   - `TriggerType::Constant` abilities are not "Actions". They do not generate buttons or descriptions.
   - **Verification Requirement**: Requires state diffing (comparing `GameState` before and after adding a card to stage) to verify stat modifications like +1 Blade from a passive.

2. **Trigger Queue Visibility**:
   - When multiple `OnPlay` abilities trigger, they enter `pending_abilities`.
   - **Gap**: The launcher only surfaces the *current* active ability. The depth and order of the remaining queue are hidden from the frontend.

3. **Bitmask Filter Clarity**:
   - Attribute filters (`C_GRP`, `MATCH_FILTER`) are processed as raw integers in bytecode.
   - **Gap**: Human auditors must manually translate `0x10000` to "Unit Filter" using `logic.rs`.

4. **Multi-Pick Resumption State**:
   - For opcodes like `O_LOOK_AND_CHOOSE(v=3)`, the interpreter uses `v_remaining` to track progress.
   - **Gap**: The button labels (e.g., "Select Slot 1") do not always include "Pick 1 of 3" context, which can be confusing for actors (Humans/Agents).

## 10. Safe Bulk Operations (Speed & Reversibility)

To maintain high velocity without introducing irreversible desk-rot:

### Tenet 1: Git-Backed Reversibility
- **Rule**: Never run a bulk-fix script on a dirty working directory.
- **Workflow**:
    1. `git stash` or `git commit` current work.
    2. Run fix script.
    3. `cargo test` and `git diff` to verify.
    4. `git checkout -- .` if result is undesirable.

### Tenet 2: Pattern-Based Sync
Instead of manual string replacement, use `tools/verify/bulk_sync_strings.py` to identify and update all test assertions concurrently.

### Tenet 3: Systematic Triage
When faced with 50+ failures, do not look at individual failures. Look at the **Failure Delta**:
1. Run `cargo test > base.log`.
2. Apply systemic fix (e.g., standardizing `IT_OPTIONAL`).
3. Run `cargo test > after.log`.
4. Compare `grep FAILED` counts. A successful systemic fix should drop failure counts by 10-20% across the entire crate.
