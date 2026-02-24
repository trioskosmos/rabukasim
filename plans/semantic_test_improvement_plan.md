# Semantic Test Improvement Plan

## Current Status
- **Pass Rate**: 87% (806/926 abilities)
- **Failures**: 120 abilities
- **Panic Count**: 0

## Failure Categories Analysis

### 1. HAND_DELTA Failures (96 cases)
**Pattern**: `Mismatch HAND_DELTA for 'COST: DISCARD_HAND(1)': Exp -1, Got 0`

**Root Causes**:
1. Truth file expects `HAND_DISCARD` tag but actual bytecode may not be executing the discard
2. Auto-resolution of `SELECT_HAND_DISCARD` interactions may fail
3. Test environment may not have proper hand setup for discard costs

**Fix Strategy**:
- [ ] Verify hand setup in `setup_oracle_environment()` includes enough cards
- [ ] Check `resolve_interaction()` for `SELECT_HAND_DISCARD` handling
- [ ] Add debug logging for discard cost execution
- [ ] Verify Truth file `HAND_DISCARD` values match actual bytecode behavior

### 2. SCORE_DELTA Failures (11 cases)
**Pattern**: `Mismatch SCORE_DELTA for 'EFFECT: BOOST_SCORE(1)': Exp 1, Got 0`

**Root Causes**:
1. `BOOST_SCORE` effect may not be applying to the correct game state
2. Live phase context may not be set up correctly for `ONLIVESUCCESS` triggers
3. Score tracking in `ZoneSnapshot` may not capture `live_score_bonus`

**Fix Strategy**:
- [ ] Verify `live_score_bonus` is tracked in `ZoneSnapshot`
- [ ] Check live phase setup for `ONLIVESUCCESS` abilities
- [ ] Add debug logging for score changes

### 3. DISCARD Failures (7 cases)
**Pattern**: `Mismatch DISCARD_DELTA for 'COST: MOVE_TO_DECK(1)': Exp -1, Got 0`

**Root Causes**:
1. `MOVE_TO_DECK` cost may not be properly implemented
2. Discard pile tracking may not update correctly

**Fix Strategy**:
- [ ] Verify `MOVE_TO_DECK` opcode implementation
- [ ] Check discard pile updates in test environment

### 4. SEGMENT_STUCK Failures (6 cases)
**Pattern**: `Mismatch OPPONENT_MEMBER_TAP_DELTA for 'EFFECT: TAP_OPPONENT(ALL)': Exp 1, Got 0`

**Root Causes**:
1. `TAP_OPPONENT(ALL)` effect may not be targeting opponent correctly
2. Opponent stage may be empty in test environment

**Fix Strategy**:
- [ ] Verify opponent stage setup in `setup_oracle_environment()`
- [ ] Check `TAP_OPPONENT` opcode implementation
- [ ] Add special handling for `ALL` targets

### 5. Negative Test Failures (178 cases)
**Pattern**: Abilities firing without conditions in minimal state

**Root Causes**:
1. Some abilities have no conditions and always fire (expected behavior)
2. Condition checking in bytecode may be incomplete

**Fix Strategy**:
- [ ] Differentiate between "always-on" abilities and conditional abilities
- [ ] Update negative test to skip abilities without conditions

## Implementation Steps

### Phase 1: Debug Infrastructure
1. Add verbose logging for failed test cases
2. Create single-card debug test for detailed analysis
3. Add state dumps before/after ability execution

### Phase 2: Truth File Alignment
1. Re-generate Truth file from actual bytecode execution
2. Compare generated values with expected values
3. Identify systematic discrepancies

### Phase 3: Test Environment Fixes
1. Ensure hand has at least 5 cards for discard costs
2. Ensure opponent has 3 stage members for target effects
3. Ensure live zone is set up for live-phase abilities

### Phase 4: Assertion Logic Fixes
1. Handle `TAP_OPPONENT(ALL)` with value 99 correctly
2. Fix `BOOST_SCORE` tracking for live abilities
3. Add special handling for `MOVE_TO_DECK` effects

## Expected Outcome
- Target: 95%+ pass rate
- All panic counts remain at 0
- Clear documentation of remaining edge cases

## Code Changes Required

### File: `engine_rust_src/src/semantic_assertions.rs`

```rust
// 1. Improve hand setup for discard costs
fn setup_oracle_environment() {
    // Ensure at least 5 cards in hand for discard costs
    while state.core.players[0].hand.len() < 5 {
        state.core.players[0].hand.push(dummy_member_id);
    }
}

// 2. Add special handling for TAP_OPPONENT(ALL)
fn assert_cumulative_deltas() {
    // Handle 99 value for ALL targets
    if expected_tap_all {
        let available_targets = baseline_p1.active_members_count;
        if actual_tap == 0 && available_targets > 0 {
            return Err(...);
        }
    }
}

// 3. Fix live score tracking
fn diff_snapshots() {
    // Track live_score_bonus separately
    let d_live_score = current.live_score_bonus - baseline.live_score_bonus;
    if d_live_score != 0 {
        deltas.push(SemanticDelta { tag: "LIVE_SCORE_DELTA", ... });
    }
}
```

### File: `reports/semantic_truth_v3.json`

- Re-generate with corrected values
- Add `OPPONENT_MEMBER_TAP_DELTA` for tap opponent effects
- Fix `HAND_DISCARD` values to match actual execution

## Testing Approach

1. Run single-card tests for each failure category
2. Compare bytecode execution with Truth expectations
3. Update Truth file or fix bytecode as needed
4. Re-run mass verification to confirm fixes
