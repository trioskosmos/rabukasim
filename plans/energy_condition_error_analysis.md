# Error Analysis: 澁谷かのん Ability Activation Failure (Updated)

## Error Message
```
[Turn 5] 澁谷かのん's ability did not activate because target condition was not met: Need 0 Energy.
```

## User Clarification
The user has **8 energy** but the ability still fails to activate. This is a critical clue!

## Card Ability Details
From [`reports/aaaa.md`](reports/aaaa.md):
- **Trigger**: ON_PLAY
- **Conditions**: 
  1. `ALL_MEMBERS {FILTER="GROUP_ID=3"}` - All members on stage must be from group ID 3 (Liella!)
  2. `ENERGY_COUNT {MIN=7}` - Player must have at least 7 energy
- **Effect**: Place 1 energy card in wait state

## Root Cause Analysis

### Finding 1: Two Different Interpreters
The Rust engine has **two** condition-checking systems:

1. **Legacy Interpreter** ([`engine_rust_src/src/core/logic/interpreter_legacy.rs:380`](engine_rust_src/src/core/logic/interpreter_legacy.rs)):
   ```rust
   C_COUNT_ENERGY => player.energy_zone.len() as i32 >= val,
   ```
   Counts **ALL energy** (including tapped/used)

2. **New Interpreter** ([`engine_rust_src/src/core/logic/interpreter/conditions.rs:192`](engine_rust_src/src/core/logic/interpreter/conditions.rs)):
   ```rust
   C_COUNT_ENERGY => (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32,
   ```
   Counts **ONLY UNTAPPED energy** (available to use)

### Finding 2: Energy Count Mismatch
The new interpreter correctly counts **untapped energy only**. If the player has:
- 8 total energy
- But only 0-6 are **untapped** (available)

Then the check would fail with "Need 7 Energy" (since only 0-6 are available).

But the error shows "Need 0 Energy" which means **NO untappd energy** is available!

### Most Likely Cause
**The player has 8 energy TOTAL, but ALL 8 are TAPPED (used).**

This means:
- Total energy: 8
- Untapped (available): 0
- The condition `ENERGY_COUNT {MIN=7}` checks for **available/untapped energy**
- Result: 0 < 7 → Condition fails

The game displays "8 energy" but the condition checks for "available energy" (untapped).

### Why "Need 0 Energy" is Misleading
The error message in [`logging.rs:133`](engine_rust_src/src/core/logic/interpreter/logging.rs):
```rust
C_COUNT_ENERGY => format!("Need {} Energy", val),
```

This shows `val` (the required amount: 7), but the **actual bug** is that:
1. The system is showing the actual count (0) instead of the required count (7)
2. OR the condition value is incorrectly stored as 0 instead of 7

Looking at the bytecode: `CHECK_COUNT_ENERGY | v(Val):7` - the value IS 7 in bytecode. So the display bug is likely that it's showing the actual count (0) instead of required count.

## Verification Needed
To confirm this hypothesis, check:
1. Are all 8 of the player's energy cards **tapped**?
2. Does the UI show "8 energy" but only count "0 available"?

## Solution
1. **Fix the error message** to show both required and actual: "Need 7 Energy (have 0 available)"
2. **Clarify in UI** the difference between total energy and available (untapped) energy
