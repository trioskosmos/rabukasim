# GPU Parity Test Failure Analysis and Fix Plan

## Executive Summary

The `test_gpu_parity_semantic.exe` test suite shows **535 passes and 391 failures** (57.8% pass rate). This document analyzes the failure patterns and provides a comprehensive fix plan.

## Test Output Summary

```
PASS: 535, FAIL: 391, SKIP: 0
```

## Failure Pattern Categories

Based on analysis of `reports/test_output.txt`, failures fall into these categories:

### 1. Hand Delta Mismatch (Most Common)

**Examples:**
- `PL!SP-bp4-002-P:AB0: Hand delta mismatch (expected: -1, actual: 0)`
- `PL!SP-bp1-008-R:AB0: Hand delta mismatch (expected: 0, actual: 1)`
- `PL!SP-bp2-014-N:AB0: Hand delta mismatch (expected: -2, actual: -1)`

**Root Cause Analysis:**
- GPU shader not correctly applying draw/discard effects
- Semantic truth may have incorrect delta values for card play actions
- The `-1` hand delta for card play may not be applied correctly in all trigger types

**Likely Fix:**
- Review `run_single_semantic_test()` in `test_gpu_parity_semantic.rs` - the HAND_DELTA adjustment logic
- Check WGSL shader DRAW/DISCARD opcode implementations

### 2. Discard Delta Mismatch (Second Most Common)

**Examples:**
- `PL!SP-bp1-007-SEC:AB0: Discard delta mismatch (expected: -1, actual: 0)`
- `PL!N-bp4-011-P+:AB0: Discard delta mismatch (expected: 2, actual: 1)`
- `PL!N-sd1-004-SD:AB0: Discard delta mismatch (expected: 2, actual: 1)`

**Root Cause Analysis:**
- Discard opcodes not executing properly on GPU
- Cost payment flow may not be moving cards to discard pile
- Semantic truth may expect discard from effects that don't trigger

**Likely Fix:**
- Check DISCARD opcode in WGSL shader
- Verify cost payment flow in shader_rules.wgsl

### 3. Energy Tap Delta Mismatch

**Examples:**
- `PL!SP-bp1-009-R:AB0: Energy tap delta mismatch (expected: 1, actual: 0)`
- `PL!HS-bp1-002-R:AB0: Energy tap delta mismatch (expected: 2, actual: 0)`
- `PL!N-pb1-015-R:AB0: Energy tap delta mismatch (expected: 2, actual: 15)` (extreme case)

**Root Cause Analysis:**
- Energy payment not happening or wrong amount being tapped
- Test state may not have enough energy set up
- Energy zone initialization may be incorrect

**Likely Fix:**
- Check PAY_ENERGY opcode implementation
- Verify energy zone setup in test helpers
- Check `tapped_energy_count` tracking in GPU state

### 4. Member Tap Not Detected

**Examples:**
- `PL!-bp3-001-R:AB0: Member tap expected but not detected`
- `PL!N-bp3-008-P+:AB0: Member tap expected but not detected`

**Root Cause Analysis:**
- TAP_MEMBER opcode not implemented or not working
- `moved_flags` not being set correctly for tap actions
- Targeting logic may be wrong

**Likely Fix:**
- Check TAP_MEMBER opcode in WGSL
- Verify `moved_flags` tracking in gpu_state.rs

### 5. Deck Delta Mismatch

**Examples:**
- Less common but present in some failures

## Common Failure Patterns

### Pattern A: Off-by-one errors

Many failures show expected vs actual differing by exactly 1:
- Expected: -1, Actual: 0
- Expected: 2, Actual: 1
- Expected: -2, Actual: -1

This suggests systematic issues with:
1. Card play action not being accounted for
2. One less card being drawn/discarded than expected
3. Initial state setup differences

### Pattern B: Zero vs Expected

Many failures show actual: 0 when expected is non-zero:
- Expected: 2, Actual: 0
- Expected: -1, Actual: 0

This suggests:
1. Effects not executing at all on GPU
2. Trigger conditions not being met
3. Opcode handlers not being called

### Pattern C: Extreme Values

Some failures show extreme differences:
- `PL!N-pb1-015-R:AB0: Energy tap delta mismatch (expected: 2, actual: 15)`
- `PL!-bp3-004-SEC:AB0: Hand delta mismatch (expected: 51, actual: 4)`

These indicate:
1. Semantic truth has incorrect values
2. GPU state corruption
3. Wrong ability being executed

## Root Cause Categories

### Category 1: Semantic Truth Issues

The `semantic_truth_v3.json` may have:
- Incorrect delta values
- Missing conditions
- Wrong trigger type mappings

### Category 2: GPU Shader Implementation

The WGSL shader may have:
- Missing opcode implementations
- Incorrect state transitions
- Wrong targeting logic

### Category 3: Test Infrastructure

The test code may have:
- Incorrect initial state setup
- Wrong action encoding
- Missing trigger type handlers

## Fix Plan

### Phase 1: Create Analysis Tools

1. **Create `tools/analyze_parity_failures.py`**
   - Parse test output and categorize failures
   - Generate statistics and reports
   - Identify high-priority cards

2. **Create `tools/compare_single_card.py`**
   - Run single card through both CPU and GPU
   - Compare state transitions step-by-step
   - Debug output for investigation

### Phase 2: Fix High-Impact Issues

1. **Fix Hand Delta Logic**
   - Review `run_single_semantic_test()` adjustment logic
   - Ensure card play delta is applied correctly for all trigger types
   - Verify HAND_DISCARD conversion in `compare_actual_vs_expected()`

2. **Fix Energy Tap Tracking**
   - Verify `tapped_energy_count` is updated in shader
   - Check energy zone initialization in tests
   - Ensure PAY_ENERGY opcode works correctly

3. **Fix Member Tap Detection**
   - Implement proper tap tracking in GPU state
   - Use correct field for tap indication (not `moved_flags`)

### Phase 3: Semantic Truth Validation

1. **Audit semantic_truth_v3.json**
   - Validate delta values against actual card effects
   - Check for cards with extreme/unusual values
   - Verify trigger type mappings

2. **Fix Oracle Generation**
   - Update `pseudocode_oracle.py` to generate correct deltas
   - Add validation for generated truth values

### Phase 4: Regression Prevention

1. **Add Unit Tests**
   - Test each delta type independently
   - Add edge case tests for off-by-one scenarios

2. **Improve Error Messages**
   - Include more context in failure messages
   - Show initial and final state values

## Recommended Tool Implementation

### Tool: `tools/analyze_parity_failures.py`

```python
# Key features:
# 1. Parse test output and categorize failures
# 2. Compute statistics (avg diff, common patterns)
# 3. Identify cards with multiple error types
# 4. Generate actionable report
```

### Tool: `tools/debug_single_parity_test.py`

```python
# Key features:
# 1. Run single card ability through GPU
# 2. Show step-by-step state changes
# 3. Compare against expected deltas
# 4. Highlight where mismatch occurs
```

## Next Steps

1. Switch to Code mode to create the analysis tools
2. Run analysis to get precise failure statistics
3. Prioritize fixes based on impact
4. Implement fixes incrementally with verification

## Files to Modify

| File | Changes |
|------|---------|
| `engine_rust_src/src/bin/test_gpu_parity_semantic.rs` | Fix hand delta adjustment logic |
| `engine_rust_src/src/core/gpu_semantic_bridge.rs` | Improve delta comparison, add more delta types |
| `engine_rust_src/src/core/shader_rules.wgsl` | Fix opcode implementations |
| `reports/semantic_truth_v3.json` | Validate and fix incorrect values |
| `tools/analyze_parity_failures.py` | NEW: Failure analysis tool |
| `tools/debug_single_parity_test.py` | NEW: Single card debug tool |
