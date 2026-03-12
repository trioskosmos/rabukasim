---
name: qa_rule_verification
description: Unified workflow for extracting official Q&A data, maintaining the verification matrix, and implementing engine-level rule tests.
---

# Q&A Rule Verification Skill

This skill provides a standardized approach to ensuring the LovecaSim engine aligns with official "Love Live! School Idol Collection" Q&A rulings.

## 1. Components
- **Data Source**: `data/qa_data.json`.
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
2. Verify the Rust test harness still compiles: `cargo test --manifest-path engine_rust_src/Cargo.toml --no-run`.

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

## 7. Troubleshooting Common Test Failures

### Compilation Errors

#### Error: `cannot find function 'load_real_db'`
**Cause**: Missing import or function not exposed in test scope.
**Fix**: Ensure `qa_verification_tests.rs` is in the correct module path and has:
```rust
use crate::prelude::*; // Brings in load_real_db()
use crate::qa::*;      // Brings in test utilities
```

#### Error: `PlayerState` field does not exist
**Cause**: Field name changed or does not exist in the current schema.
**Fix**:
1. Check `engine_rust_src/src/state.rs` for actual field names
2. Use `cargo doc --open` and navigate to `PlayerState` struct
3. Common renames: `stage_members` → `stage`, `live_cards` → `live_zone`

### Runtime Panics

#### Panic: `index out of bounds: the len is 3 but the index is 5`
**Cause**: Attempting to access a fixed-size array beyond its bounds.
**Fix**:
```rust
// Before (unsafe):
state.players[0].stage[5] = card_id;  // stage only has 3 slots

// After (correct):
state.players[0].stage[0] = card_id;  // Valid indices: 0, 1, 2
```

#### Panic: `called 'Option::unwrap()' on a 'None' value`
**Cause**: Card lookup failed (card number not found in database).
**Fix**:
```rust
// Use card_finder.py to verify the card number exists:
// python tools/card_finder.py "PL!N-bp1-012-R"

// Use unwrap_or() with a known fallback:
let card_id = db.id_by_no("PL!N-bp1-012-R＋")
    .unwrap_or_else(|| {
        eprintln!("[TEST] Card ID not found, using fallback");
        0
    });
```

### Assertion Failures

#### Assertion: `assertion failed: state.players[0].live_zone[0] == card_id`
**Cause**: Card was not placed in the expected zone; engine may have discarded or rejected it.
**Fix**:
1. Add debug output to trace state changes:
```rust
println!("[DEBUG] Before: live_zone = {:?}", state.players[0].live_zone);
state.do_live_result(&db);
println!("[DEBUG] After: live_zone = {:?}", state.players[0].live_zone);
```
2. Check if the card is in discard or a different zone:
```rust
let in_discard = state.players[0].discard.contains(&card_id);
assert!(!in_discard, "Card was discarded instead");
```

#### Assertion: `assertion failed: state.players[0].score == expected_score`
**Cause**: Scoring calculation incorrect; card ability text may override base scoring.
**Fix**:
1. Verify card ability in `data/consolidated_abilities.json`:
```bash
python tools/card_finder.py "Q89" | grep -A5 "name.*description"
```
2. Check `data/cards_compiled.json` for the compiled bytecode of the card:
```bash
cat data/cards_compiled.json | jq '.[] | select(.id == 1234) | .bytecode'
```

### Matrix Inconsistencies

#### Issue: Matrix shows ✅ but test actually fails
**Cause**: Test was passing before, but recent changes broke it; or matrix cache is stale.
**Fix**:
```bash
# Rebuild the matrix from scratch:
python tools/gen_full_matrix.py --rebuild

# Run all tests to identify failures:
cargo test --lib qa_verification_tests 2>&1 | grep -E "test.*FAILED|error"
```

#### Issue: Matrix shows ℹ️ (no test) for a ruled QA, but I wrote a test
**Cause**: Test name does not match naming convention or is in the wrong file.
**Fix**: Ensure:
1. Test filename follows: `test_q{ID}_{descriptor}`
2. Test is located in `engine_rust_src/src/qa/batch_card_specific.rs` or `qa_verification_tests.rs`
3. Re-run: `python tools/gen_full_matrix.py --rebuild`

## 8. Integration with Continuous Verification

### Pre-Commit Hook
To verify test integrity before committing changes:

```bash
# Run lightweight checks:
cargo test --lib qa_verification_tests --quiet
python tools/gen_full_matrix.py --validate

# If either fails, abort commit with:
echo "FAILED: QA tests did not pass" && exit 1
```

### CI Pipeline Integration
When pushing to a repository, the following workflow runs automatically:
1. **Compile Rust Tests**: `cargo test --lib qa_verification_tests --no-run`
2. **Run QA Tests**: `cargo test --lib qa_verification_tests -- --nocapture`
3. **Regenerate Matrix**: `python tools/gen_full_matrix.py`
4. **Check Coverage**: Abort if coverage drops below committed minimum (e.g., 95/237)

### Local Verification Command
Before submitting QA test work, run:
```bash
# Full validation suite
python tools/gen_full_matrix.py && \
cargo test --lib qa_verification_tests --nocapture && \
echo "✅ All QA checks passed"
```

## 9. Common Pitfalls & Prevention

### Pitfall 1: "Manual Setup is Faster than Engine Calls"
**Why It's Wrong**: Bypassing the engine prevents discovering bugs in the actual game flow.
**Prevention**:
- Rule #1: If the test doesn't call `do_*()` or `play_*()`, it's not testing the engine.
- Refactor any test that manually sets state variables without corresponding engine calls.

### Pitfall 2: "This Test Passes, So the Rule Must Be Implemented"
**Why It's Wrong**: A passing test may exercise a shortcut rather than the real code path.
**Prevention**:
- Use `cargo test qa_verification_tests -- --nocapture` to see all debug output.
- Add `println!("[Q{ID}] Engine path taken: ...")` assertions in your test.
- Verify the actual engine function was invoked by grepping the source.

### Pitfall 3: "Using Simplified Card IDs (My Test Uses Card 0)"
**Why It's Wrong**: Tests must exercise the real bytecode; simplified cards may not have the ability text.
**Prevention**:
- **ALWAYS** use `load_real_db()`.
- Look up the real card ID via `db.id_by_no("CARD_NUMBER")`.
- If a card number doesn't exist, report it as a data bug, not a test problem.

### Pitfall 4: "The QA Says 'Yes', But I Don't Know How to Test It"
**Why It's Wrong**: Uncertainty is resolved by understanding the engine architecture, not by skipping the test.
**Prevention**:
- Examine existing tests in `batch_card_specific.rs` that cover similar rules.
- Use `card_finder.py` to identify real cards that trigger the rule.
- Ask: "What engine state change should happen if this rule is true?"
- Build a minimal test around that state change.

### Pitfall 5: "Score Calculation Test Always Passes Because I'm Just Checking the Numbers"
**Why It's Wrong**: If you don't call the scoring engine, you're not testing scoring.
**Prevention**:
- Call `do_live_result()` or the appropriate scoring phase function.
- Verify both the intermediate state (`ui.performance_results`) and the final score.

## 10. Hands-On Command Reference

### Discovering Q&A Information
```bash
# Find all Q&A rulings mentioning "baton"
python tools/card_finder.py "baton"

# Find Q147 specifically
python tools/card_finder.py "Q147"

# List related cards for Q89
python tools/card_finder.py "Q89" | grep -i "related\|card_no"
```

### Test Execution & Debugging
```bash
# Run a single test with output
cargo test --lib qa_verification_tests::test_q147_* -- --nocapture

# Run all Q147 variants
cargo test --lib qa_verification_tests test_q147 -- --nocapture

# Run and capture output to file for analysis
cargo test --lib qa_verification_tests -- --nocapture >> qa_test_output.log 2>&1

# Show all panic messages (no truncation)
cargo test --lib qa_verification_tests -- --nocapture --diag-format=short 2>&1 | head -200
```

### Matrix Operations
```bash
# Generate matrix with detailed coverage breakdown
python tools/gen_full_matrix.py --verbose

# Force rebuild from source (ignores cache)
python tools/gen_full_matrix.py --rebuild --verbose

# Export matrix in JSON for parsing
python tools/gen_full_matrix.py --output-json

# Compare coverage before/after a change
python tools/gen_full_matrix.py > before.txt
# ... make your changes ...
python tools/gen_full_matrix.py > after.txt
diff before.txt after.txt
```

### Interactive Testing (God Mode)
```bash
# Start interactive CLI with full state injection
python tools/play_interactive.py exec

# Within the REPL:
# >> state.players[0].score = 999
# >> state.draw_card(42)
# >> state.do_live_result(db)
# >> print(state.players[0].discard)
```

## 11. Decision Tree: Should I Write a Test?

```
START: You found an unmapped QA ruling (marked ℹ️ in matrix)
  │
  ├─ Does it reference a specific card number or ability?
  │   ├─ YES → Look up card via card_finder.py
  │   │         ├─ Can I resolve it to a real card? → YES: Continue to "Define Setup"
  │   │         └─ NO: Mark as "Data Gap" and skip (report separately)
  │   │
  │   └─ NO (ruling is generic/procedural)
  │       └─ Example: "How are ties broken?" → Jump to "Define Setup" with db.get_rules()
  │
  └─ [Define Setup] What engine state must be true for this ruling to apply?
      ├─ Can I construct it via player zone assignments (stage, live, hand)?
      │   └─ YES → Proceed to "Choose Engine Path"
      │
      └─ NO (requires specific game phase or event)
          ├─ Is it during LiveResult phase?
          │   └─ YES: Use do_live_result() + finalize_live_result()
          ├─ Is it during Performance?
          │   └─ YES: Use handle_performance_phase()
          └─ Other → Consult existing test patterns in batch_card_specific.rs

      [Choose Engine Path]
      ├─ Call the MOST SPECIFIC engine function for this ruling
      ├─ Example: For member placement, call play_member() not a general step()
      └─ If unsure, grep for similar QA IDs in batch_card_specific.rs

      [Write Test]
      └─ Document: QA ID, original text, ability text, expected result
      └─ Assert: Final state matches QA answer
      └─ Verify: test_q{ID}_* naming and module placement
      └─ Run: cargo test --lib qa_verification_tests::test_q* -- --nocapture

  [After Running]
  ├─ Test PASSED
  │   └─ Run: python tools/gen_full_matrix.py
  │   └─ Confirm: ℹ️ changed to ✅
  │   └─ Done!
  │
  └─ Test FAILED
      ├─ Is it a missing import or function not found?
      │   └─ YES: Check compiler/prelude sections
      ├─ Is it an assertion failure after engine call?
      │   └─ YES: Review troubleshooting section 7
      └─ Is the test hanging?
          └─ Likely infinite loop in engine; add timeout and debug
```

## 12. Session Workflow

### 1-Hour Focused Session (Single QA Implementation)
1. **Pick Target**: Choose one unmapped QA from matrix (5 min)
2. **Research**: Use `card_finder.py` to understand scope (5 min)
3. **Write Test**: Implement in `batch_card_specific.rs` (30 min)
4. **Debug**: Run and fix test errors (15 min)
5. **Verify**: Re-run matrix and document findings (5 min)

### Multi-Hour Batch Session (5-10 QAs)
1. **Identify Cluster**: Pick 5-10 related unmapped QAs (e.g., all member placement rules) (10 min)
2. **Plan Order**: Sequence by dependency (foundational first) (5 min)
3. **Implement Batch**: Write all tests, minimal documentation (60–90 min)
4. **Test**: Run full suite, fix compilation errors (15 min)
5. **Matrix Update**: Single `gen_full_matrix.py` run covers all (2 min)
6. **Document**: Record any engine/data issues discovered (10 min)
7. **Summary**: Update `SKILL.md` or session notes with findings (5 min)

## 13. Advanced Card-Specific Test Patterns (Remaining 59 QAs)

### Overview
**59 card-specific QAs remain untested** (as of March 2026). These tests require advanced patterns beyond simple state verification. This section provides templates for the most common card ability types.

### Pattern Category 1: Conditional Activation (15 QAs)
**Examples**: Q122, Q132, Q144, Q148, Q151–153, Q163–164, Q166–167

**Pattern**:
```rust
#[test]
fn test_q122_deck_peek_refresh_logic() {
    // Q122: 『登場 自分のデッキの上からカードを3枚見る。
    //       その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。』
    // If deck has 3 cards, does refresh occur? A: No.

    let db = load_real_db();
    let mut state = create_test_state();

    // Setup: Deck with exactly 3 cards (boundary condition)
    state.players[0].deck = SmallVec::from_slice(&[db.id_by_no("PL!N-bp1-001-R").unwrap(),
                                                    db.id_by_no("PL!N-bp1-002-R").unwrap(),
                                                    db.id_by_no("PL!N-bp1-003-R").unwrap()]);
    let initial_deck_len = state.players[0].deck.len();
    let initial_discard_len = state.players[0].discard.len();

    // Action: Play member with peek-3 ability
    let member_id = db.id_by_no("PL!N-bp1-002-R＋").unwrap();
    state.play_member(0, member_id, 0, &db); // Slot 0

    // Assert: No refresh occurred (discard pile unchanged)
    assert_eq!(state.players[0].discard.len(), initial_discard_len,
        "Q122: Refresh should NOT occur when peeking entire deck");
}
```

**Key Points**:
- Boundary conditions: Peek amount = Deck size, Peek > Deck size
- Refresh flag tracking: Verify `refresh_pending` state
- Deck reorganization: Check that cards returned to top are in correct order

### Pattern Category 2: Score Modification (12 QAs)
**Examples**: Q132, Q148–150, Q155, Q157–158

**Pattern**:
```rust
#[test]
fn test_q149_member_heart_total_comparison() {
    // Q149: 『ライブ成功時 自分のステージにいるメンバーが持つハートの総数が、
    //       相手のステージにいるメンバーが持つハートの総数より多い場合、
    //       このカードのスコアを＋１する。』
    // "Total heart count" ignores color, counts all hearts.

    let db = load_real_db();
    let mut state = create_test_state();

    // Setup: Both players with specific member configurations
    let aqours_card_1 = db.id_by_no("PL!-bp3-026-L").unwrap(); // Example Aqours live card
    let member_p0_1 = db.id_by_no("PL!N-bp3-011-R").unwrap(); // 3 hearts
    let member_p0_2 = db.id_by_no("PL!N-bp3-012-R").unwrap(); // 5 hearts
    let member_p1_1 = db.id_by_no("PL!N-bp3-013-R").unwrap(); // 2 hearts
    let member_p1_2 = db.id_by_no("PL!N-bp3-014-R").unwrap(); // 2 hearts

    state.players[0].stage[0] = member_p0_1;
    state.players[0].stage[1] = member_p0_2;
    state.players[1].stage[0] = member_p1_1;
    state.players[1].stage[1] = member_p1_2;

    let base_score = state.players[0].score;

    // Action: Execute LiveResult with player 0 winning
    state.phase = Phase::LiveResult;
    state.players[0].live_zone[0] = aqours_card_1;
    state.ui.performance_results.insert(0, serde_json::json!({
        "success": true, "lives": [{"passed": true, "score": 5}]
    }));
    state.do_live_result(&db);

    // Assert: Score increased by 1 for heart comparison
    assert_eq!(state.players[0].score, base_score + 1 + 5,
        "Q149: Score should increase due to heart comparison + base live score");
}
```

**Key Points**:
- Real card member data: Fetch actual heart counts from `db.members`
- Score delta calculation: Verify only the delta, not absolute score
- Condition verification: Test both true and false branches

### Pattern Category 3: Ability Interaction (11 QAs)
**Examples**: Q151–154, Q156, Q159, Q163–165

**Pattern**:
```rust
#[test]
fn test_q151_center_ability_grant() {
    // Q151: 『起動 センター ターン1回 メンバー1人をウェイトにする：
    //       ライブ終了時まで、これによってウェイト状態になったメンバーは、
    //       『常時 ライブの合計スコアを＋１する。』を得る。』
    // If center member leaves stage, granted ability is lost.

    let db = load_real_db();
    let mut state = create_test_state();

    // Setup: Center member with activate ability
    let center_member_id = db.id_by_no("PL!S-bp3-001-R＋").unwrap();
    let target_member_id = db.id_by_no("PL!S-bp3-002-R").unwrap();

    state.players[0].stage[1] = center_member_id; // Center slot
    state.players[0].stage[2] = target_member_id; // Right slot

    // Action 1: Activate center ability to grant bonus
    state.activate_ability(0, center_member_id, vec![target_member_id], &db);
    let score_before = state.players[0].score;

    // Trigger live result with member on stage
    state.phase = Phase::LiveResult;
    state.players[0].live_zone[0] = db.id_by_no("PL!S-bp3-020-L").unwrap();
    state.do_live_result(&db);

    let score_with_bonus = state.players[0].score;
    assert!(score_with_bonus > score_before, "Q151: Score should increase with granted ability");

    // Action 2: Verify bonus is lost if member leaves
    state.players[0].stage[2] = -1; // Remove member
    state.phase = Phase::LiveResult;
    state.do_live_result(&db);

    // Bonus would no longer apply (manual check since state was modified)
}
```

**Key Points**:
- Ability grant lifecycle: Verify abilities exist only while conditions hold
- Scope of effects: Live-end, turn-end, permanent
- Cleanup on zone change: Abilities granted to members remove when member leaves

### Pattern Category 4: Zone Management (8 QAs)
**Examples**: Q145, Q146, Q157, Q160–161, Q169–170

**Pattern**:
```rust
#[test]
fn test_q146_member_count_for_draw() {
    // Q146: 『登場 自分のステージにいるメンバー1人につき、
    //       カードを1枚引く。その後、手札を1枚控え室に置く。』
    // Does count include the member activating the ability?

    let db = load_real_db();
    let mut state = create_test_state();

    // Setup: 3 members on stage (including the one activating)
    let activating_member = db.id_by_no("PL!-bp3-004-R＋").unwrap();
    let other_member_1 = db.id_by_no("PL!-bp3-005-R").unwrap();
    let other_member_2 = db.id_by_no("PL!-bp3-006-R").unwrap();

    state.players[0].stage[0] = activating_member;
    state.players[0].stage[1] = other_member_1;
    state.players[0].stage[2] = other_member_2;

    let initial_hand = state.players[0].hand.len();

    // Action: Activate ability
    state.activate_ability(0, activating_member, vec![], &db);

    // Assert: Drew 3 cards (including activator), discarded 1
    assert_eq!(state.players[0].hand.len(), initial_hand + 3 - 1,
        "Q146: Should draw 3 (one per stage member) then discard 1");
}
```

**Key Points**:
- Zone state verification: Count members correctly
- Self-reference: Does count include the source?
- Effect resolution order: Draw before discard

### Pattern Category 5: LiveResult Phase Specifics (7 QAs)
**Examples**: Q132, Q153–154, Q156

**Pattern**:
```rust
#[test]
fn test_q132_aqours_heart_excess_check() {
    // Q132: 『ライブ成功時 自分のステージにいる『Aqours』のメンバーが持つハートに、
    //       ❤が合計4個以上あり、このターン、相手が余剰のハートを持たずに
    //       ライブを成功させていた場合、このカードのスコアを＋２する。』
    // Does this activate even if I'm first (opponent hasn't acted)?

    let db = load_real_db();
    let mut state = create_test_state();

    // Setup: P0 (first player) wins, P1 (second player) has no excess hearts
    state.first_player = 0;
    state.phase = Phase::LiveResult;

    // P0 members with hearts
    let live_card_p0 = db.id_by_no("PL!S-pb1-021-L").unwrap();
    state.players[0].live_zone[0] = live_card_p0;

    // Simulate both players executing performance
    state.ui.performance_results.insert(0, serde_json::json!({
        "success": true,
        "live": {"lives": [], "passed": true},
        "excess_hearts": 2
    }));
    state.ui.performance_results.insert(1, serde_json::json!({
        "success": true,
        "live": {"lives": [], "passed": true},
        "excess_hearts": 0  // No excess
    }));

    let score_before = state.players[0].score;

    // Action: Finalize live result
    state.do_live_result(&db);
    state.finalize_live_result();

    // Assert: Bonus applied (+2 to score)
    assert_eq!(state.players[0].score - score_before,
        expected_base_score + 2,
        "Q132: Score bonus should apply even if P0 is first player");
}
```

**Key Points**:
- Turn order independence: Bonuses work regardless of first/second player
- Excess heart tracking: Use `ui.performance_results` snapshots
- LiveStart vs LiveSuccess timing: Execute at correct phase

### Remaining Categories Summary

| Category | Count | Key Challenges |
|----------|-------|---|
| Conditional Activation | 15 | Boundary conditions, state flags |
| Score Modification | 12 | Real card data, delta calculations |
| Ability Interaction | 11 | Ability lifecycle, scope validation |
| Zone Management | 8 | State consistency, count accuracy |
| LiveResult Specifics | 7 | Phase-locked rules, turn-order-independent |
| Cost & Resource | 4 | Energy accounting, partial resolution |
| Deck Manipulation | 2 | Refresh triggers, deck ordering |

## 14. Batch Implementation Roadmap (59 Remaining QAs)

### Sprint 1: Foundation (Q122–Q125) – 2 hours
**Goal**: Establish patterns for deck peek/manipulation tests.
- **Q122**: Refresh logic on exact-size peek ✓ Pattern above
- **Q123**: Related card discovery during peek
- **Q124**: Deck shuffling side effects
- **Q125**: Refresh during active skill resolution

**Success Criteria**: All 4 tests compile, ≥2 points each, deck manipulation paths verified.

### Sprint 2: Score Mechanics (Q132, Q148–150, Q155, Q157–158) – 3 hours
**Goal**: Implement all score-delta tests with real member data.
- Use `db.members.get(card_id)` to fetch actual heart/blade counts
- Real LiveResult phase execution
- Multi-condition bonus stacking

**Success Criteria**: Score tests account for >50% coverage increase.

### Sprint 3: Ability Lifecycle (Q151–154, Q156, Q159) – 4 hours
**Goal**: Verify ability grant/revoke mechanics.
- Granted abilities removed on zone change
- Center-locked abilities
- Turn-once ability boundaries

**Success Criteria**: Ability state transitions fully specified.

### Sprint 4: Zone & Interaction (Q146, Q160–165, Q169–170) – 3 hours
**Goal**: Complete zone state management and card interaction tests.
- Member count for effects (self-inclusive)
- Deck manipulation with refresh
- Partial resolution handling

**Success Criteria**: >80% coverage target reached.

### Sprint 5: Edge Cases & Hardening (Q166–170, remaining if >170) – 2 hours
**Goal**: Complex multi-effect scenarios.
- Nested ability resolution
- Refresh during active effect
- Multiple choice scenarios

**Success Criteria**: Coverage reaches 95%+, all tests ≥2 points.

## 15. Real Card ID Reference (For Most Common Test Patterns)

```rust
// Multi-name members (Q62, Q65, Q69, Q90)
const TRIPLE_NAME_CARD: &str = "PL!N-bp1-001-R＋";  // 上原歩夢&澁谷かのん&日野下花帆

// Aqours members (Q132, Q148–150, Q151–154, Q157–158)
const AQOURS_LIVE_CARD: &str = "PL!S-pb1-021-L";

// Liella! condition checks (Q64, Q74)
const LIELLA_MEMBER: &str = "PL!N-bp3-011-R";

// Niji condition checks (Q67, Q81)
const NIJI_MEMBER: &str = "PL!N-bp3-001-R＋";

// Common peek-ability card
const PEEK_CARD: &str = "PL!N-bp1-002-R＋";

// Center-lock ability cards
const CENTER_CARD: &str = "PL!S-bp3-001-R＋";

// Deck-to-bottom shuffle
const SHUFFLE_CARD: &str = "LL-bp3-001-R＋";
```

**Usage**:
```rust
let card_id = db.id_by_no(TRIPLE_NAME_CARD)
    .unwrap_or_else(|| panic!("Card {} not found", TRIPLE_NAME_CARD));
```

## 16. Coverage Projection

### Current State (March 2026)
- **Total**: 237 QAs
- **Verified**: 179 (75.5%)
- **Remaining**: 59 (24.5%)

### Projected Milestones
| Phase | Hours | QAs | Coverage | Target |
|-------|-------|-----|----------|--------|
| Now | – | 0 | 75.5% | – |
| Sprint 1 | 2 | 4 | 76.4% | Foundation |
| Sprint 2 | 3 | 8 | 79.0% | Score mechanics |
| Sprint 3 | 4 | 9 | 82.9% | Ability lifecycle |
| Sprint 4 | 3 | 16 | 89.9% | Zone management |
| Sprint 5 | 2 | 20 | 100% | Complete |
| **Total** | **14** | **59** | **100%** | ✅ |

**Estimated Time to 100%**: 14 focused hours (distributed over multiple sessions).

## 17. Quality Assurance Checklist

Before marking a test as "ready for merge":

- [ ] Test name follows `test_q{ID}_{descriptor}` convention
- [ ] Test calls at least one engine function (`do_*()`, `play_*()`, etc.)
- [ ] Test uses `load_real_db()` and real card IDs
- [ ] Assertions verify final state, not just initial setup
- [ ] Comments include: QA ID, original Japanese, English translation,

 intended effect
- [ ] Test compiles without warnings
- [ ] Test passes: `cargo test --lib qa_verification_tests::test_q{ID}`
- [ ] Matrix regenerates: `python tools/gen_full_matrix.py`
- [ ] Test score ≥ 2 points (verified by matrix scanner)
- [ ] No test regression: All 500+ existing tests still pass
- [ ] Debug output includes `[Q{ID}] PASS` message

## 18. Getting to 100%: Action Plan

**Immediate Next Steps** (for next user session):

1. **Pick First Batch**: Choose 5 QAs from Sprint 1 above
2. **Implement Tests**: Use patterns from Section 13
3. **Run Test Suite**:
   ```bash
   cd engine_rust_src
   cargo test --lib qa_verification_tests --no-fail-fast -- --nocapture
   python ../tools/gen_full_matrix.py
   ```
4. **Record Results**: Document coverage delta
5. **Iterate**: Move to next batch

**Completion Timeline**: With consistent 1-2 hour sessions, **100% coverage achievable in 2-3 weeks**.
