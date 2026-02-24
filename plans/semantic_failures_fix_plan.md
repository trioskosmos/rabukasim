# Semantic Test Failures Fix Plan

## Overview

Audit Results: **902/926 Abilities Passed (97.4%)** - 24 failures across 3 categories

## Failure Categories and Root Causes

### 1. HAND_DELTA Failures (14 failures)

**Affected Cards:**
- `PL!-sd1-019-SD` - `LOOK_AND_CHOOSE_REVEAL(3, choose_count=1)`
- `PL!HS-bp2-007-P/R/SEC` - `RECOVER_LIVE(1)`

**Root Cause:**
The `RECOVER_LIVE` and `LOOK_AND_CHOOSE_REVEAL` effects require:
1. Live cards in the discard pile for RECOVER_LIVE
2. Deck to have cards for LOOK_AND_CHOOSE_REVEAL
3. Proper interaction resolution to select and move cards to hand

The `setup_oracle_environment` already adds live cards to discard, but the issue is that:
- `ZoneSnapshot` captures P0 state but the `OPPONENT_MEMBER_TAP_DELTA` is expected from P1 state changes
- The interaction resolution may not be completing fully

**Fix Location:** [`semantic_assertions.rs:760-842`](engine_rust_src/src/semantic_assertions.rs:760) - `diff_snapshots`

---

### 2. SEGMENT_STUCK Failures (6 failures) - TAP_OPPONENT

**Affected Cards:**
- `PL!N-bp3-017-N` Ab2 - `TAP_OPPONENT(ALL)`
- `PL!N-bp3-023-N` Ab2 - `TAP_OPPONENT(ALL)`
- `PL!SP-bp4-011-P/R` Ab1 - `TAP_OPPONENT(1)`

**Root Cause:**
`TAP_OPPONENT` requires tracking opponent member tap state, but `diff_snapshots` only captures P0's tap state:

```rust
// Current code only tracks P0 tap state
let mut tap_delta = 0;
for i in 0..3 {
    if !baseline.tapped_members[i] && current.tapped_members[i] {
        tap_delta += 1;
    }
}
```

The `OPPONENT_MEMBER_TAP_DELTA` is expected but **not tracked at all** in `ZoneSnapshot` or `diff_snapshots`.

**Fix Required:**
1. Add `opponent_tapped_members: [bool; 3]` to `ZoneSnapshot`
2. Capture P1's tap state in `ZoneSnapshot::capture`
3. Add `OPPONENT_MEMBER_TAP_DELTA` delta calculation in `diff_snapshots`

**Fix Location:** 
- [`semantic_assertions.rs:760-842`](engine_rust_src/src/semantic_assertions.rs:760) - `diff_snapshots`
- [`test_helpers.rs`](engine_rust_src/src/test_helpers.rs) - `ZoneSnapshot` struct

---

### 3. DISCARD Failures (4 failures)

**Affected Cards:**
- `PL!-pb1-017-P/R` - `TAP_MEMBER(1)` expects DISCARD_DELTA +1
- `PL!N-pb1-006-P/R` - `MOVE_TO_DECK(1)` expects DISCARD_DELTA -1

**Root Cause:**
These appear to be **semantic truth parsing issues**:
- `TAP_MEMBER` should NOT cause discard changes - the truth file may have incorrect annotations
- `MOVE_TO_DECK` moving from discard should decrease discard, but the test expects this

**Investigation Needed:**
1. Check the semantic truth file for these cards
2. Verify if the effect text parsing is correct
3. May need to fix truth file or parser

---

## Implementation Plan

### Step 1: Add OPPONENT_MEMBER_TAP_DELTA Tracking

**File:** `engine_rust_src/src/test_helpers.rs`

```rust
// In ZoneSnapshot struct, add:
pub opponent_tapped_members: [bool; 3],

// In ZoneSnapshot::capture, add:
opponent_tapped_members: [
    state.core.players[1].is_tapped(0),
    state.core.players[1].is_tapped(1),
    state.core.players[1].is_tapped(2),
],
```

**File:** `engine_rust_src/src/semantic_assertions.rs`

```rust
// In diff_snapshots, add after MEMBER_TAP_DELTA:
// Opponent Tap Members
let mut opp_tap_delta = 0;
for i in 0..3 {
    if !baseline.opponent_tapped_members[i] && current.opponent_tapped_members[i] {
        opp_tap_delta += 1;
    }
}
if opp_tap_delta > 0 {
    deltas.push(SemanticDelta { tag: "OPPONENT_MEMBER_TAP_DELTA".to_string(), value: serde_json::json!(opp_tap_delta) });
}
```

### Step 2: Verify RECOVER_LIVE Test Environment

Ensure the test environment has live cards in discard for `RECOVER_LIVE` tests:

**File:** `engine_rust_src/src/semantic_assertions.rs`

In `setup_oracle_environment`, verify lines 580-586 are adding live cards correctly.

### Step 3: Fix Semantic Truth or Parser for DISCARD Issues

Investigate the semantic truth file entries for:
- `PL!-pb1-017-P/R`
- `PL!N-pb1-006-P/R`

If the truth file is correct, the issue may be in effect parsing.

---

## Files to Modify

| File | Changes |
|------|---------|
| `engine_rust_src/src/test_helpers.rs` | Add `opponent_tapped_members` to `ZoneSnapshot` |
| `engine_rust_src/src/semantic_assertions.rs` | Add `OPPONENT_MEMBER_TAP_DELTA` tracking in `diff_snapshots` |
| `reports/semantic_truth_v3.json` | Verify/fix truth entries for DISCARD failure cards |

---

## Expected Outcome

After fixes:
- **HAND_DELTA**: Should pass if environment has correct cards
- **SEGMENT_STUCK**: Should pass with opponent tap tracking
- **DISCARD**: May need truth file fixes or further investigation

Target: **>98% pass rate** (from current 97.4%)
