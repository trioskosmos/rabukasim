# Fix: Energy Count Condition Should Count ALL Energy in Zone

## Current Behavior (Bug)
The `C_COUNT_ENERGY` condition currently counts only **untapped (available) energy**:
```rust
// conditions.rs line 192
C_COUNT_ENERGY => (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32,
```

This subtracts tapped energy from total, resulting in only available energy being counted.

## Expected Behavior
The condition should count **ALL energy in the zone** (tapped + untapped), regardless of tap state.

## Required Changes

### 1. New Interpreter (conditions.rs)
**File**: `engine_rust_src/src/core/logic/interpreter/conditions.rs`

**Line ~192**: Change from:
```rust
C_COUNT_ENERGY => (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32,
```

To:
```rust
C_COUNT_ENERGY => player.energy_zone.len() as i32,
```

### 2. Legacy Interpreter (interpreter_legacy.rs)
**File**: `engine_rust_src/src/core/logic/interpreter_legacy.rs`

**Line ~380**: Change from:
```rust
C_COUNT_ENERGY => player.energy_zone.len() as i32 >= val,
```

This is already correct (counts all energy).

### 3. Fix Error Message (logging.rs)
**File**: `engine_rust_src/src/core/logic/interpreter/logging.rs`

**Line ~133**: The error message shows "Need 0 Energy" but should show the required value (7). This suggests the value is not being passed correctly. However, this may be a separate display bug.

## Summary
Change **one line** in `conditions.rs` to count all energy instead of just untapped energy:
```rust
// Before (current):
C_COUNT_ENERGY => (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32,

// After (fix):
C_COUNT_ENERGY => player.energy_zone.len() as i32,
```
