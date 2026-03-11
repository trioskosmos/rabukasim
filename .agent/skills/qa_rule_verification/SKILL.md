---
name: qa_rule_verification
description: Unified workflow for extracting official Q&A data, maintaining the verification matrix, and implementing engine-level rule tests.
---

# Q&A Rule Verification Skill

This skill provides a standardized approach to ensuring the LovecaSim engine aligns with official "Love Live! School Idol Collection" Q&A rulings.

## 1. Components
- **Data Source**: `data/qa_data.json` (Managed by `tools/qa_scraper.py`).
- **Card Text / Translation Inputs**: `data/consolidated_abilities.json` and the compiler/parser under `compiler/`.
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

## Priority Rule
The first priority of QA verification is **not** to write tests that merely pass with the current engine.

The first priority is to:
1. Write tests that expose real engine, compiler, card-data, or bytecode defects.
2. Fix the root cause when a ruling and the current implementation disagree.
3. Only count coverage after the test is exercising the real rule path with the correct card behavior.

If a ruling appears to fail, check all of these before assuming the Rust runtime is correct:
- `data/consolidated_abilities.json` may show that the card-text simplification or translation is wrong.
- `compiler/` may show that the parser/compiler translated the pseudocode to conditions/effects incorrectly.
- The compiled `bytecode` in `data/cards_compiled.json` may not actually represent the behavior printed on the card.

Do not prefer “easy passing coverage” over finding defects. A good QA test is allowed to fail first if that failure exposes a real engine or card-data bug.

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
3. Cross-check the ruling against `data/consolidated_abilities.json`, `compiler/`, and the compiled `bytecode` for the referenced card before assuming the current data is correct.
3. Implement a focused test in `qa_verification_tests.rs`.
   - **CRITICAL:** Include original ability text and QA ruling as comments.
4. Run `cargo test qa_verification_tests` to verify compliance.
5. Re-run `tools/gen_full_matrix.py` to update the ✅ status.

## 3. Systematic Test Creation Process

### Overview
**Systematic Test Creation** is an iterative, batch-oriented process for converting unmapped Q&A rulings into engine-level tests. The goal is to close the gap from X% to 100% test coverage by methodically implementing tests for all 237 QA entries.

### High-Level Process
1. **Identify Unmapped QAs**: Review `qa_test_matrix.md` and filter for entries marked with `ℹ️` (no test) that have card-specific references
2. **Prioritize by Defect Exposure**: Prefer tests most likely to uncover engine/runtime bugs, parser/compiler mistranslations, or bad compiled bytecode before chasing easy green coverage
3. **Group by Category**: Create test batches organized by theme (e.g., "Live Card Mechanics", "Activation Rules", "Member Placement")
4. **Implement Tests**: Write tests in `engine_rust_src/src/qa/batch_card_specific.rs` following the pattern below
5. **Update Matrix**: Run `python tools/gen_full_matrix.py` to verify coverage increase
6. **Document Findings**: Record engine issues or assumptions discovered during testing

### Test Implementation Pattern

#### Step 1: Identify Target QA
```rust
// Get QA details from data/qa_data.json
// Example: Q38 - "Live Card Definition"
// Q38: 「ライブ中のカード」とはどのようなカードですか？
// A38: ライブカード置き場に表向きに置かれているライブカードです。
```

#### Step 2: Locate Real Cards
```rust
// Use db.id_by_no("CARD_NUMBER") to find real references
// Example: Cards listed in qa_data.json related_cards field
let live_card_id = db.id_by_no("PL!N-bp1-012-R＋").unwrap_or(100);
```

#### Step 3: Build Minimal Test
```rust
#[test]
fn test_q38_live_card_definition() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Setup: Initialize game state with required conditions
    let live_card_id = db.id_by_no("PL!N-bp1-012-R＋").unwrap_or(100);

    // Verify: Initial state matches expectation (per QA)
    assert_eq!(state.players[0].live_zone[0], -1, "Q38: Zone empty initially");

    // Action: Perform the operation described in QA
    state.players[0].live_zone[0] = live_card_id;

    // Assert: Final state matches QA expectation
    assert_eq!(state.players[0].live_zone[0], live_card_id, "Q38: Card placed");

    println!("[Q38] PASS: Live card correctly placed");
}
```

#### Step 4: Verify Compilation
```bash
cargo test --lib qa::batch_card_specific::test_q38
# Expected: ok. 1 passed
```

#### Step 5: Update Coverage
```bash
python tools/gen_full_matrix.py
# Coverage increases from X% to (X+Y)%
```

### Key PlayerState Fields for Testing

| Field | Type | Purpose |
|-------|------|---------|
| `stage[0..2]` | `[i32; 3]` | Member cards on stage (3 slots) |
| `live_zone[0..2]` | `[i32; 3]` | Live cards (-1 = empty) |
| `hand` | `SmallVec<[i32; 16]>` | Cards in hand |
| `deck` | `SmallVec<[i32; 60]>` | Main deck |
| `discard` | `SmallVec<[i32; 32]>` | Discard pile |
| `energy_zone` | `SmallVec<[i32; 16]>` | Energy cards |
| `baton_touch_count` | `u8` | Times baton touched this turn |
| `score` | `u32` | Current score |
| `stage_energy` | `[SmallVec<[i32; 4]>; 3]` | Energy cost per slot |

### Real Database Access Pattern
```rust
// Load real card database
let db = load_real_db();

// Lookup card by card number (from qa_data.json related_cards)
let card_id = db.id_by_no("PL!N-bp3-005-R＋").unwrap_or(4369);

// Access card properties
if let Some(card) = db.members.get(&card_id) {
    let name = &card.name;
    let cost = card.cost;
    // ... use card data
}
```

### Example: Batch Creation (Q38, Q63, Q68, Q89)
In one session, 4 tests were created covering:
- **Q38**: Live card zone placement (foundational definition)
- **Q63**: Effect-based member placement without card costs (rule interaction)
- **Q68**: Cannot-live game state definition (conditional logic)
- **Q89**: Card group/unit identification (data validation)

**Result**: Coverage increased from 95/237 (40.1%) → 98/237 (41.4%)

### Systematic Batch Strategy
1. **Batch 1-10 QAs**: Lowest-numbered unmapped, often foundational
2. **Identify blocking dependencies**: Some Q&As depend on others being correct first
3. **Group by system**: All member-placement QAs together, all live-mechanics together, etc.
4. **Test in priority order**:
   - Foundational rules (definitions, conditions) = HIGH
   - Complex interactions = MEDIUM
   - Edge cases = LOW

### Known Limitations & Findings
- `entered_this_turn` field does NOT exist; use game flow flags instead
- `live_zone` is on `PlayerState`, not `GameState`
- Some QA rulings require engine-level fixes, compiler/parser fixes, or card-data/bytecode fixes before the final test should be accepted
- Document such findings via `println!("[QA_ID] ISSUE: description")` in test

## 4. Test Fidelity Scoring System

The QA matrix uses a **fidelity scoring system** to distinguish high-quality engine-driven tests from placeholder tests:

### Score Calculation
- **Base**: 0 points
- **Assertions**: +1 per assertion_* (max 4) = **4 points**
- **Engine Signals**: +3 per engine call found (max 12) = **12 points**
  - Direct engine calls: `do_live_result()`, `do_draw_phase()`, `do_performance_phase()`, `play_member()`, `auto_step()`, `handle_liveresult()`, `generate_legal_actions()`, etc.
- **Real DB**: +3 bonus for `load_real_db()`
- **Penalties**: -6 per suspicious pattern (simplified, structural verification, no actual placement needed, etc.)
- **Penalties**: -5 if no engine signals, -4 if no assertions

### Minimum Threshold: 2 points
Tests scoring below 2 are excluded from coverage.

### Examples
- ✅ `test_q83_choose_exactly_one_success_live` (Score: 10) – sets up state, calls `do_live_result()`, calls `handle_liveresult()`, verifies discard, asserts
- ❌ `test_q50_both_success_same_score_order_unchanged` (Score: < 2) – manually sets flags, no real game flow
- ❌ Legacy setup tests – manual vector manipulation, comment-based rules, no engine interaction

## 5. Weak Test Audit & Remediation

### Identified Weak Tests (March 2026)

| Test ID | Current Score | Issue | Status |
|---------|---------------|-------|--------|
| Q14 | -3 | Manual deck/energy vectors, no engine calls | **TO FIX** |
| Q15 | -2 | Energy zone orientation only validated via comment | **TO FIX** |
| Q27 | -1 | Baton touch – no actual play_member() call | **TO FIX** |
| Q30 | 1 | Duplicate checking – manual assertion only | **TO FIX** |
| Q31 | 1 | Live zone duplicates – structural only | **TO FIX** |
| Q50 | -2 | Turn order – manually set obtained_success_live | **TO FIX** |
| Q51 | -2 | Turn order – manually set obtained_success_live | **TO FIX** |
| Q83 | 10 | ✅ FIXED – real selection flow with handle_liveresult() | **DONE** |
| Q139 | 0 | Placeholder – needs real two-player baton mechanics | **TO FIX** |
| Q141 | -1 | Under-member energy – needs engine flow verification | **TO FIX** |

### Weak Test Remediation Strategy

Each weak test is **replaced** (not patched) with a **high-fidelity engine-driven test**:

1. **Identify Real Engine Path**: Use `grep` to find existing tests that drive the same code path
2. **Build Minimal Repro**: Set up minimal state needed to trigger the ruling
3. **Call Real Engine**: Drive `do_live_result()`, `play_member()`, `handle_member_leaves_stage()`, etc.
4. **Assert State Changes**: Verify both forward and side effects
5. **Document QA**: Include original Japanese + English + intended engine behavior

### Example Remediation: Q50

**Before (Weak)**:
```rust
#[test]
fn test_q50_both_success_same_score_order_unchanged() {
    let db = load_real_db();
    let mut state = create_test_state();

    // No actual placement needed - just check logic
    state.players[0].live_score_bonus = 10;
    state.players[1].live_score_bonus = 10;
    state.players[0].success_lives.push(live_card);
    state.players[1].success_lives.push(live_card);
    // Not calling finalize_live_result() - just comment-based verification
}
```

**After (Fixed)**:
```rust
#[test]
fn test_q50_both_success_same_score_order_unchanged() {
    // Q50: 両方のプレイヤーがスコアが同じためライブに勝利して、
    //      両方のプレイヤーが成功ライブカード置き場にカードを置きました。
    //      次のターンの先攻・後攻はどうなりますか？
    // A50: Aさんが先攻、Bさんが後攻のままです。

    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.phase = Phase::LiveResult;
    state.first_player = 0;

    // Setup: Both players with identical performance results
    let live_id = 6;
    state.players[0].live_zone[0] = live_id;
    state.players[1].live_zone[0] = live_id;

    state.ui.performance_results.insert(0, serde_json::json!({
        "success": true, "lives": [{"passed": true, "score": 10}]
    }));
    state.ui.performance_results.insert(1, serde_json::json!({
        "success": true, "lives": [{"passed": true, "score": 10}]
    }));
    state.live_result_processed_mask = [0x80, 0x80];

    // Action: Call real engine finalization
    state.do_live_result(&db);
    state.finalize_live_result();

    // Assert: Turn order unchanged (first_player still 0)
    assert_eq!(state.first_player, 0, "Q50: Turn order should remain unchanged when both win");
}
```

## 6. Best Practices
- **Real Data Only**: **CRITICAL POLICY:** Always use `load_real_db()` and real card IDs. NEVER mock card abilities or bytecode manually via `add_card()` or similar methods.
- **Isolation**: Use `create_test_state()` to ensure a pristine game state for each test.
- **Engine Calls Required**: Every QA test MUST call at least one engine function (`do_*()`, `play_member()`, `handle_*()`, etc.)
- **Documentation**: Every test MUST include comments detailing:
  - **QA**: Q&A ID, original Japanese, English translation
  - **Ability**: The relevant card text or pseudocode (if applicable)
  - **Intended Effect**: What the engine logic is supposed to do
- **Traceability**: Always link tests to their QID in doc comments or test names
- **Negative Tests**: When the official answer is "No", ensure the engine rejects or doesn't apply the action/condition
- **State Snapshots**: For complex phases (Performance, LiveResult), always set up `ui.performance_results` snapshots that the engine trusts
- **Fidelity Scoring**: Target tests with score >= 4 to ensure coverage counts in the matrix
