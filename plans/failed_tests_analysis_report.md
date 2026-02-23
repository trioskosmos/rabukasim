# Failed Tests Analysis Report

## Summary

After running all Rust tests unfiltered and unblocked, **5 tests failed** out of 182 total tests. This report analyzes each failure and identifies the root causes.

## Test Results Overview

```
test result: FAILED. 176 passed; 5 failed; 1 ignored; 0 measured; 0 filtered out
```

## Failed Tests Analysis

### 1. test_repro_bp4_002_p_wait_flow

**Location:** `engine_rust_src/src/repro_bp4_002_p.rs`

**Error:**
```
assertion `left == right` failed: Should still be in Response phase for LOOK_AND_CHOOSE
  left: Main
 right: Response
```

**Root Cause:**
The test plays card 558 (PL!SP-bp4-002-P) which has an OPTIONAL TAP_MEMBER (WAIT) ability followed by LOOK_AND_CHOOSE. After choosing YES for the OPTIONAL, the phase transitions to Main instead of staying in Response for the subsequent LOOK_AND_CHOOSE.

**Analysis:**
Looking at [`handlers.rs:347-380`](engine_rust_src/src/core/logic/handlers.rs:347), when `activate_ability_with_choice` is called in Response phase:
1. It pops the interaction from the stack
2. Resolves bytecode with the choice
3. Restores phase to Main if `interaction_stack.is_empty()`

The issue is that when the OPTIONAL choice is resolved, the bytecode execution should continue and trigger the next suspension (LOOK_AND_CHOOSE), but instead the phase is restored to Main prematurely.

**Fix Required:**
The O_TAP_MEMBER handler in [`member_state.rs:22-46`](engine_rust_src/src/core/logic/interpreter/handlers/member_state.rs:22) needs to properly continue bytecode execution after OPTIONAL choice resolution, allowing subsequent opcodes (like LOOK_AND_CHOOSE) to execute and suspend.

---

### 2. test_yell_persistence_and_selection

**Location:** `engine_rust_src/src/repro/yell_persistence_repro.rs`

**Error:**
```
assertion `left == right` failed: Should pause for LOOK_AND_CHOOSE
  left: Main
 right: Response
```

**Root Cause:**
Similar to test #1. After resolving an OPTIONAL discard cost, the phase transitions to Main instead of staying in Response for LOOK_AND_CHOOSE from YELL source (zone 15).

**Analysis:**
The test flow:
1. Live card 111 triggers ON_LIVE_SUCCESS
2. OPTIONAL cost: DISCARD_HAND(1) - player accepts and discards
3. Should trigger LOOK_AND_CHOOSE from yell_cards (zone 15)
4. But phase goes to Main instead

The debug output shows:
```
DEBUG: looked_cards: []
```

This indicates the LOOK_AND_CHOOSE never populated `looked_cards`, meaning the opcode was never executed.

**Fix Required:**
Same as #1 - ensure bytecode execution continues after OPTIONAL resolution.

---

### 3. test_rurino_filter_masking_fix

**Location:** `engine_rust_src/src/repro_card_fixes.rs:160-184`

**Error:**
```
assertion failed: Hand index 0 should be selectable
```

**Root Cause:**
The test creates a `SELECT_HAND_DISCARD` interaction with `filter_attr: 0x6000`. The filter `0x6000` represents zone bits (bits 12-15 encode source zone information), but the card matching logic may be incorrectly filtering out valid hand cards.

**Analysis:**
Looking at [`filter.rs:203-262`](engine_rust_src/src/core/logic/filter.rs:203), the `CardFilter::from_attr` function parses filter attributes:
- `0x6000` = `0110 0000 0000 0000` in binary
- Bit 12 (0x1000) = TAPPED filter
- Bit 13 (0x2000) = HAS_BLADE_HEART filter  
- Bit 14 (0x4000) = NOT_BLADE_HEART filter

The filter `0x6000` sets both HAS_BLADE_HEART and NOT_BLADE_HEART, which is contradictory.

Looking at [`deck_zones.rs:233`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:233):
```rust
let filter_attr = (a as u32 as u64) & 0xFFFFFFFFFFFF0FFF;
```

This masks out bits 12-15 (zone bits) for filter matching. But the test passes `0x6000` directly as `filter_attr`, which includes these zone bits.

**Fix Required:**
The test should use a proper filter value, or the action generation code in [`response.rs`](engine_rust_src/src/core/logic/action_gen/response.rs) should properly mask the filter_attr before checking card matches.

---

### 4. test_archetype_n_pr_005_draw_2_discard_2

**Location:** `engine_rust_src/src/semantic_assertions.rs:714-719`

**Error:**
```
Mismatch HAND_DELTA for 'カードを2枚引き、手札を2枚控え室に置く': Exp 0, Got 2
```

**Root Cause:**
The semantic assertion expects a net hand delta of 0 (draw 2, discard 2), but the engine reports +2.

**Analysis:**
Looking at the bytecode trace:
```
[DEBUG] BC_STEP: ip=0, op=10 (real=10), v=2, a=0, s=1, cond=true  // O_DRAW 2
[DEBUG] BC_STEP: ip=4, op=58 (real=58), v=2, a=24576, s=1, cond=true  // O_MOVE_TO_DISCARD 2
```

The draw happens, but the discard may not be executing properly. The `a=24576 = 0x6000` includes zone bits that may be causing the discard to fail or be skipped.

**Fix Required:**
Same as #3 - the filter/zone attribute handling needs review.

---

### 5. test_archetype_sd1_001_success_live_cond

**Location:** `engine_rust_src/src/semantic_assertions.rs:704`

**Error:**
```
Mismatch HAND_DELTA for '自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える': Exp 1, Got 0
```

**Root Cause:**
The card should add 1 live card from discard to hand when there are 2+ cards in success_lives, but the hand delta is 0.

**Analysis:**
Looking at the bytecode trace:
```
[DEBUG] BC_STEP: ip=0, op=218 (real=218), v=2, a=0, s=0, cond=true  // Condition check
[DEBUG] BC_STEP: ip=4, op=15 (real=15), v=1, a=0, s=6, cond=true  // O_RECOVER_LIVE
```

The O_RECOVER_LIVE (op 15) handler suspends for RECOV_L choice, but when choice 99 is provided (decline/skip), the handler doesn't add the card to hand.

Looking at [`deck_zones.rs:204-208`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:204):
```rust
O_RECOVER_LIVE | O_RECOVER_MEMBER => {
    match handle_recovery(state, db, ctx, v, a, s, instr_ip, op) {
        Some(_) => {},
        None => return HandlerResult::Suspend,
    }
}
```

The `handle_recovery` function needs to properly handle the choice and add the card to hand.

**Fix Required:**
The `handle_recovery` function should properly add the selected card to hand when a valid choice is made.

---

## Common Patterns

### Pattern 1: OPTIONAL Resolution Not Continuing Bytecode

Tests #1 and #2 share the same root cause: after resolving an OPTIONAL choice, the bytecode execution should continue to the next opcode, but instead the phase is restored to Main.

**Key Files:**
- [`handlers.rs:347-380`](engine_rust_src/src/core/logic/handlers.rs:347) - `activate_ability_with_choice`
- [`member_state.rs:22-46`](engine_rust_src/src/core/logic/interpreter/handlers/member_state.rs:22) - O_TAP_MEMBER handler
- [`deck_zones.rs:222-327`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:222) - O_MOVE_TO_DISCARD handler

### Pattern 2: Filter Attribute Confusion

Tests #3 and #4 involve filter attributes that include zone bits (0x6000) being passed to card matching functions that interpret them as filter flags.

**Key Files:**
- [`filter.rs:203-262`](engine_rust_src/src/core/logic/filter.rs:203) - `CardFilter::from_attr`
- [`response.rs:95-232`](engine_rust_src/src/core/logic/action_gen/response.rs:95) - action generation for LOOK_AND_CHOOSE

### Pattern 3: Recovery Handler Not Adding to Hand

Test #5 involves O_RECOVER_LIVE not properly adding the selected card to hand.

**Key Files:**
- [`deck_zones.rs:204-208`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:204) - O_RECOVER_LIVE handler

---

## Recommended Fix Priority

1. **HIGH:** Fix OPTIONAL resolution to continue bytecode execution (affects 2 tests)
2. **HIGH:** Fix filter attribute handling for zone bits (affects 2 tests)
3. **MEDIUM:** Fix O_RECOVER_LIVE handler to add card to hand (affects 1 test)

---

## Next Steps

1. Switch to Code mode to implement fixes
2. Run tests individually to verify fixes
3. Run full test suite to ensure no regressions
