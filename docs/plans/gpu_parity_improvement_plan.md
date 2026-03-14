# GPU Parity Improvement Plan

## Current Status (2026-02-24)

### Test Results Summary
- **PASS: 384**
- **FAIL: 551**
- **SKIP: 51**
- **Pass Rate: 41.1%**

### Failure Categories Analysis

Based on the test output, failures are categorized as follows:

| Category | Count | Percentage | Priority |
|----------|-------|------------|----------|
| Hand Delta Mismatch | ~245 | 44.5% | P0 |
| Blade Delta Mismatch | ~108 | 19.7% | P1 |
| Member Tap Not Detected | ~63 | 11.4% | P2 |
| Score Delta Mismatch | ~64 | 11.7% | P2 |
| Discard Delta Mismatch | ~70 | 12.7% | P2 |

### Root Cause Analysis

#### 1. Hand Delta Issues (P0 - Highest Impact)
**Symptoms:**
- `Hand delta mismatch (expected: 1, actual: 0)` - Draw effects not working
- `Hand delta mismatch (expected: -1, actual: 0)` - Discard from hand not working
- `Hand delta mismatch (expected: -2, actual: 0)` - Multiple discards not working

**Root Cause (CONFIRMED):**
The `match_filter()` function in shader_rules.wgsl:27 only supports:
- Group Filter (attr >> 5 & 0x7F)
- Type Filter (attr >> 2 & 0x03)

**COST_GE filter is NOT implemented!** This means conditions like `COUNT_STAGE {MIN=1, FILTER="COST_GE=13"}` always fail because the filter cannot match cards by cost.

**Investigation Findings:**
- `match_filter()` at shader_rules.wgsl:27-44 only checks groups and card type
- COST_GE filter requires comparing card cost, but this is not implemented
- Many abilities have COST_GE conditions that will never be satisfied

**Solution:**
1. **Short-term**: Add COST_GE filter support to `match_filter()` function
2. **Alternative**: Skip tests with unsupported conditions

**Code Fix Required in shader_rules.wgsl:**
```wgsl
fn match_filter(cid: u32, attr: u32) -> bool {
    if (cid == 0u || cid >= arrayLength(&card_stats)) { return false; }
    let s = card_stats[cid];

    // Cost Filter (attr >> 12 & 0xFF) - NEW
    let cost_filter = (attr >> 12u) & 0xFFu;
    if (cost_filter > 0u && s.cost < cost_filter) { return false; }

    // Group Filter (attr >> 5 & 0x7F)
    // ... existing code ...
}
```

**Files to Fix:**
- `engine_rust_src/src/core/shader_rules.wgsl` - Add COST_GE filter support
- `engine_rust_src/src/core/shader_core.wgsl` - Same fix needed
- `engine_rust_src/src/core/combined_shader.wgsl` - Same fix needed

#### 2. Blade Delta Issues (P1 - High Impact)
**Symptoms:**
- `Blade delta mismatch (expected: 1, actual: 0)` - Blade gain not working
- `Blade delta mismatch (expected: 2, actual: 0)` - Multiple blades not working
- `Blade delta mismatch (expected: 3, actual: 0)` - Large blade gains not working

**Root Cause:**
The O_ADD_BLADES opcode (11) updates blade_buffs array but the value may not be persisted correctly or the comparison logic in gpu_semantic_bridge.rs may not be reading the correct field.

**Files to Fix:**
- `engine_rust_src/src/core/shader_rules.wgsl` - O_ADD_BLADES implementation
- `engine_rust_src/src/core/gpu_semantic_bridge.rs` - Blade comparison logic

#### 3. Member Tap Issues (P2)
**Symptoms:**
- `Member tap expected but not detected` - Tap effects not working

**Root Cause:**
The O_TAP_OPPONENT opcode (32) may not be setting the tapped state correctly, or the comparison logic is not checking the correct field.

**Files to Fix:**
- `engine_rust_src/src/core/shader_rules.wgsl` - O_TAP_OPPONENT implementation
- `engine_rust_src/src/core/gpu_semantic_bridge.rs` - Tap detection logic

#### 4. Score Delta Issues (P2)
**Symptoms:**
- `Score delta mismatch (expected: 1, actual: 0)` - Score boost not working
- `Score delta mismatch (expected: 2, actual: 0)` - Multiple score boosts not working

**Root Cause:**
The O_BOOST_SCORE opcode (16) may not be updating player.score correctly.

**Files to Fix:**
- `engine_rust_src/src/core/shader_rules.wgsl` - O_BOOST_SCORE implementation

#### 5. Discard Delta Issues (P2)
**Symptoms:**
- `Discard delta mismatch (expected: 1, actual: 0)` - Move to discard not working
- `Discard delta mismatch (expected: 5, actual: 0)` - Bulk discard not working

**Root Cause:**
The O_MOVE_TO_DISCARD opcode (58) may not be moving cards to the discard pile correctly.

**Files to Fix:**
- `engine_rust_src/src/core/shader_rules.wgsl` - O_MOVE_TO_DISCARD implementation
- `engine_rust_src/src/core/shader_helpers.wgsl` - move_to_discard() function

---

## Improvement Plan

### Phase 1: Fix Ability Triggering (Est. +20% pass rate)

**Problem:** Abilities are not being triggered during GPU execution.

**Investigation Steps:**
1. Check if ability bytecode is being loaded correctly into GPU memory
2. Verify that the trigger type matching logic works correctly
3. Ensure that the ability execution loop is being entered

**Code Changes:**
1. Add debug logging to shader_main.wgsl to trace ability execution
2. Verify ability_offsets and ability_data are correctly populated in GpuManager
3. Check that forced_action codes are being decoded correctly

### Phase 2: Fix O_DRAW Implementation (Est. +15% pass rate)

**Problem:** Draw effects are not updating hand count.

**Investigation Steps:**
1. Verify draw_card() function is being called
2. Check that hand_len is being incremented
3. Ensure deck cards are being moved to hand

**Code Changes:**
```wgsl
// In shader_rules.wgsl, verify O_DRAW case:
case O_DRAW: {
    for (var d = 0; d < v; d = d + 1) {
        draw_card(p_idx);
    }
}

// In shader_helpers.wgsl, verify draw_card():
fn draw_card(p_idx: u32) {
    let player = get_player(p_idx);
    if (player.deck_len > 0u) {
        let card_id = player.deck[player.deck_len - 1u];
        add_to_hand(p_idx, card_id);
        player.deck_len -= 1u;
    }
}
```

### Phase 3: Fix O_ADD_BLADES Implementation (Est. +10% pass rate)

**Problem:** Blade gains are not being applied.

**Investigation Steps:**
1. Verify blade_buffs array is being updated
2. Check that the value persists after shader execution
3. Ensure comparison logic reads blade_buffs[0] correctly

**Code Changes:**
```wgsl
// In shader_rules.wgsl, verify O_ADD_BLADES case:
case O_ADD_BLADES: {
    player.blade_buffs[0] = player.blade_buffs[0] + v;
}
```

### Phase 4: Fix O_TAP_OPPONENT Implementation (Est. +5% pass rate)

**Problem:** Tap effects are not being applied.

**Investigation Steps:**
1. Verify tapped state is being set on opponent members
2. Check that the comparison logic detects tap state changes

**Code Changes:**
```wgsl
// In shader_rules.wgsl, verify O_TAP_OPPONENT case:
case O_TAP_OPPONENT: {
    let target_slot = get_target_slot();
    let opponent = get_player(1u - p_idx);
    opponent.stage_tapped[target_slot] = true;
}
```

### Phase 5: Fix O_BOOST_SCORE Implementation (Est. +5% pass rate)

**Problem:** Score boosts are not being applied.

**Investigation Steps:**
1. Verify player.score is being updated
2. Check that score persists after shader execution

**Code Changes:**
```wgsl
// In shader_rules.wgsl, verify O_BOOST_SCORE case:
case O_BOOST_SCORE: {
    player.score = player.score + v;
}
```

---

## Expected Results After Fixes

| Phase | Pass Rate Target | Cumulative Pass |
|-------|------------------|-----------------|
| Current | 41.1% | 384 |
| Phase 1 | 61.1% | 571 |
| Phase 2 | 76.1% | 711 |
| Phase 3 | 86.1% | 804 |
| Phase 4 | 91.1% | 851 |
| Phase 5 | 96.1% | 898 |

---

## Next Steps

1. **Immediate:** Add debug output to GPU shader to trace ability execution
2. **Short-term:** Fix ability triggering logic (Phase 1)
3. **Medium-term:** Fix individual opcode implementations (Phases 2-5)
4. **Long-term:** Add comprehensive unit tests for each opcode

## Technical Details

### Key Files
- `engine_rust_src/src/core/shader_main.wgsl` - Main compute shader
- `engine_rust_src/src/core/shader_rules.wgsl` - Opcode implementations
- `engine_rust_src/src/core/shader_helpers.wgsl` - Helper functions
- `engine_rust_src/src/core/gpu_semantic_bridge.rs` - Comparison logic
- `engine_rust_src/src/core/gpu_manager.rs` - GPU initialization and execution

### Opcode Reference
| Opcode | Name | Description |
|--------|------|-------------|
| 10 | O_DRAW | Draw cards from deck |
| 11 | O_ADD_BLADES | Add blade points |
| 16 | O_BOOST_SCORE | Increase score |
| 32 | O_TAP_OPPONENT | Tap opponent member |
| 58 | O_MOVE_TO_DISCARD | Move card to discard pile |

### Trigger Type Codes
| Code | Trigger Type |
|------|--------------|
| 1 | ON_PLAY |
| 2 | ON_LIVE_START |
| 3 | ON_LIVE_SUCCESS |
| 7 | ACTIVATED |
| 8 | TURN_START |
| 9 | TURN_END |
