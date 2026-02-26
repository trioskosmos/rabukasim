# PL!SP-bp4-001-P Baton Pass Issue Analysis

## Problem Statement

**Card:** PL!SP-bp4-001-P (Card ID: 557) - 澁谷かのん (Kanon Shibuya)

**Ability Text:**
> [On Play] If all members on your stage are 'Liella!' and you have 7 or more energy, place 1 energy card from your energy deck in a wait state.

**Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: ALL_MEMBERS {FILTER="GROUP_ID=3"}, SUM_ENERGY {MIN=7}
EFFECT: ENERGY_CHARGE(1, MODE="WAIT") -> PLAYER
```

**Issue:** The `ALL_MEMBERS {FILTER="GROUP_ID=3"}` condition doesn't seem to activate correctly when Kanon is played via baton pass from a non-Liella! member.

## Technical Analysis

### Bytecode Structure

The compiled bytecode for card 557's ability is:
```
[209, 4, 3, 0, 0, 213, 7, 0, 0, 0, 23, 1, 1, 0, 4, 1, 0, 0, 0, 0]
```

Decoded:
1. **Condition 1:** `C_GROUP_FILTER` (209) with `val=4`, `attr=3`
   - `val=4` has bit 2 set (0x04), meaning "Check ALL members on stage"
   - `attr=3` is the GROUP_ID for Liella!
   
2. **Condition 2:** `C_COUNT_ENERGY` (213) with `val=7`
   - Checks if energy count >= 7

3. **Effect:** `O_ENERGY_CHARGE` (23) with `val=1`, `target=1`

### Condition Evaluation Flow

The `C_GROUP_FILTER` condition is evaluated in [`conditions.rs:357-371`](engine_rust_src/src/core/logic/interpreter/conditions.rs:357):

```rust
C_GROUP_FILTER => {
    let lower_attr = attr & 0x00000000FFFFFFFF;
    let filter = if (lower_attr & 0x10) == 0 && lower_attr != 0 && lower_attr < 300 { 
        0x10 | (lower_attr << 5) 
    } else if (lower_attr & 0x10) == 0 && val != 0 {
        0x10 | (((val & 0x7F) as u64) << 5)
    } else { lower_attr };

    // Bit 2 of val (0x04) flags "Check ALL members on stage"
    if (val & 0x04) != 0 {
        player.stage.iter().filter(|&&cid| cid >= 0).all(|&cid| state.card_matches_filter(db, cid, filter))
    } else if let Some(cid) = state.get_context_card_id(ctx) {
        state.card_matches_filter(db, cid, filter)
    } else { false }
}
```

### Baton Pass Execution Flow

The baton pass execution in [`handlers.rs:506-536`](engine_rust_src/src/core/logic/handlers.rs:506):

```rust
fn execute_play_member_state(&mut self, db: &CardDatabase, p_idx: usize, hand_idx: usize, card_id: i32, slot_idx: usize, secondary_slot_idx: i16, start_ab_idx: usize, choice: i32) {
    let old_card_id = self.core.players[p_idx].stage[slot_idx];
    if old_card_id >= 0 { self.core.players[p_idx].baton_touch_count += 1; }
    // ... secondary slot handling ...

    self.core.players[p_idx].hand.remove(hand_idx);
    
    if old_card_id >= 0 {
        self.trigger_event(db, TriggerType::OnLeaves, p_idx, old_card_id, slot_idx as i16, 0, -1);
        self.core.players[p_idx].discard.push(old_card_id);  // OLD CARD REMOVED HERE
    }

    self.prev_card_id = old_card_id;
    self.core.players[p_idx].stage[slot_idx] = card_id;  // NEW CARD PLACED HERE
    // ...
    
    self.trigger_event(db, TriggerType::OnPlay, p_idx, card_id, slot_idx as i16, start_ab_idx, choice as i16);
}
```

## Root Cause Analysis

### Scenario: Baton Pass from Non-Liella! to Kanon

1. **Initial State:** Stage slot 0 has a non-Liella! member (e.g., Honoka from Muse, Group 1)
2. **Action:** Play Kanon (Liella!, Group 3) to slot 0 via baton pass
3. **Expected:** After baton pass, only Kanon is on stage, so ALL_MEMBERS condition should pass

### Potential Issues

#### Issue 1: Timing of Stage Update vs Condition Check

The execution order is:
1. Old card triggers `OnLeaves` event
2. Old card is moved to discard
3. **New card is placed on stage**
4. `OnPlay` trigger fires for new card
5. Condition is evaluated

This order appears correct - the old card should be gone when the condition is checked.

#### Issue 2: Filter Attribute Construction

The filter is constructed from `attr=3`:
- `lower_attr = 3`
- Since `(3 & 0x10) == 0` and `3 != 0` and `3 < 300`:
  - `filter = 0x10 | (3 << 5) = 0x10 | 0x60 = 0x70`

This translates to:
- `FILTER_GROUP_ENABLE` (0x10) is set
- Group ID = 3 (Liella!)

This appears correct.

#### Issue 3: Card Filter Matching

The [`card_matches_filter`](engine_rust_src/src/core/logic/game.rs:463) function checks if each card on stage matches the filter:

```rust
pub fn card_matches_filter(&self, db: &CardDatabase, cid: i32, filter_attr: u64) -> bool {
    if cid == -1 { return false; }
    let filter = CardFilter::from_attr(filter_attr);
    // ...
    filter.matches(db, cid, is_tapped)
}
```

The [`CardFilter::matches`](engine_rust_src/src/core/logic/filter.rs:62) function checks group membership:

```rust
// Group Filter
if let Some(group_id) = self.group_id {
    if let Some(m) = db.get_member(cid) {
        if !m.groups.contains(&(group_id as u8)) { return false; }
    } else if let Some(l) = db.get_live(cid) {
        if !l.groups.contains(&(group_id as u8)) { return false; }
    } else {
        return false;
    }
}
```

## Hypothesis

The most likely issue is that **the condition check is happening before the stage is fully updated** during the baton pass sequence, or there's an issue with how the filter attribute is being passed through the bytecode execution.

### Debug Steps Needed

1. **Add logging** to `C_GROUP_FILTER` condition evaluation to see:
   - What cards are on stage when the condition is checked
   - What filter is being applied
   - What each card's groups are

2. **Verify the bytecode execution order** - ensure conditions are evaluated after all state changes

3. **Test with the actual game engine** to reproduce the issue

## Recommended Fix

### Option 1: Add Debug Logging

Add temporary logging to [`conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs:357) in the `C_GROUP_FILTER` branch:

```rust
C_GROUP_FILTER => {
    let lower_attr = attr & 0x00000000FFFFFFFF;
    let filter = if (lower_attr & 0x10) == 0 && lower_attr != 0 && lower_attr < 300 { 
        0x10 | (lower_attr << 5) 
    } else if (lower_attr & 0x10) == 0 && val != 0 {
        0x10 | (((val & 0x7F) as u64) << 5)
    } else { lower_attr };

    if (val & 0x04) != 0 {
        // DEBUG: Log stage state
        if state.debug.debug_mode {
            println!("[C_GROUP_FILTER] Checking ALL members on stage");
            println!("[C_GROUP_FILTER] Filter attr: {:#x}, Group ID: {}", filter, (filter >> 5) & 0x7F);
            for (i, &cid) in player.stage.iter().enumerate() {
                if cid >= 0 {
                    if let Some(m) = db.get_member(cid) {
                        println!("[C_GROUP_FILTER] Slot {}: Card {} ({}) - Groups: {:?}", i, cid, m.name, m.groups);
                    }
                }
            }
        }
        player.stage.iter().filter(|&&cid| cid >= 0).all(|&cid| state.card_matches_filter(db, cid, filter))
    } else if let Some(cid) = state.get_context_card_id(ctx) {
        state.card_matches_filter(db, cid, filter)
    } else { false }
}
```

### Option 2: Verify Bytecode Encoding

The bytecode `[209, 4, 3, 0, 0]` should be interpreted as:
- Opcode: 209 (C_GROUP_FILTER)
- Value: 4 (ALL_MEMBERS flag)
- Attr Low: 3 (GROUP_ID)
- Attr High: 0
- Slot: 0

Verify this matches the expected encoding in the interpreter.

## Test Case

A test case has been created at [`tests/repro_bp4_001_baton_pass.rs`](engine_rust_src/tests/repro_bp4_001_baton_pass.rs) to reproduce the issue:

```rust
#[test]
fn test_card_557_baton_pass_from_non_liella() {
    // Setup: Non-Liella! member on stage
    // Action: Play Kanon (Liella!) via baton pass
    // Expected: ALL_MEMBERS condition should pass
    // Assert: Energy should be charged
}
```

## Next Steps

1. Run the test case to confirm the issue
2. Add debug logging to identify the exact failure point
3. Fix the root cause (likely in condition evaluation timing or filter construction)
4. Verify fix with additional test cases

## Related Files

- [`engine_rust_src/src/core/logic/interpreter/conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs) - Condition evaluation
- [`engine_rust_src/src/core/logic/handlers.rs`](engine_rust_src/src/core/logic/handlers.rs) - Game action handlers
- [`engine_rust_src/src/core/logic/filter.rs`](engine_rust_src/src/core/logic/filter.rs) - Card filter logic
- [`engine_rust_src/tests/repro_bp4_001_baton_pass.rs`](engine_rust_src/tests/repro_bp4_001_baton_pass.rs) - Test case
- [`data/cards_compiled.json`](data/cards_compiled.json) - Card database (card 557)
