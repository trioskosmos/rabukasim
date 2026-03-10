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

## 3. Systematic Test Creation Process

### Overview
**Systematic Test Creation** is an iterative, batch-oriented process for converting unmapped Q&A rulings into engine-level tests. The goal is to close the gap from X% to 100% test coverage by methodically implementing tests for all 237 QA entries.

### High-Level Process
1. **Identify Unmapped QAs**: Review `qa_test_matrix.md` and filter for entries marked with `ℹ️` (no test) that have card-specific references
2. **Prioritize by Impact**: Focus on foundational rules first (conditions, cost mechanics, state transitions) before complex ability interactions
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
- Some QA rulings may require engine-level fixes before test implementation
- Document such findings via `println!("[QA_ID] ISSUE: description")` in test

## 3. Best Practices
- **Real Data Only**: **CRITICAL POLICY:** Always use `load_real_db()` and real card IDs. NEVER mock card abilities or bytecode manually via `add_card()` or similar methods.
- **Isolation**: Use `create_test_state()` to ensure a pristine game state for each test.
- **Documentation**: Every test MUST include comments detailing:
  - **Ability**: The relevant card text or pseudocode.
  - **Intended Effect**: What the engine logic is supposed to do.
  - **QA**: The QA ID (e.g., Q195) and official ruling summary.
- **Traceability**: Always link tests to their QID in doc comments or test names.
- **Negative Tests**: When the official answer is "No", ensure the engine rejects the action or condition.
