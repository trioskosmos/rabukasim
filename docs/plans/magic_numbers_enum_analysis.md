# Hardcoded Magic Numbers Analysis Report

## Overview

This report identifies hardcoded magic numbers in the Loveca card game engine (Rust codebase) that could be converted to enums for better code maintainability and type safety.

## Summary of Findings

The analysis found **numerous hardcoded magic numbers** across multiple files that are candidates for enum conversion. The codebase already has a good foundation with `core/enums.rs` and `core/generated_constants.rs`, but many game-specific constants remain scattered as magic numbers.

---

## Candidate Magic Numbers for Enum Conversion

### 1. Stage Slot Constants

**Current State:** Hardcoded `3` used throughout the codebase for stage slots.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/rules.rs`](engine_rust_src/src/core/logic/rules.rs)
- [`engine_rust_src/src/core/logic/game.rs`](engine_rust_src/src/core/logic/game.rs)
- [`engine_rust_src/src/core/logic/player.rs`](engine_rust_src/src/core/logic/player.rs)
- [`engine_rust_src/src/core/logic/performance.rs`](engine_rust_src/src/core/logic/performance.rs)
- [`engine_rust_src/src/core/logic/interpreter/handlers/state.rs`](engine_rust_src/src/core/logic/interpreter/handlers/state.rs)

**Examples:**
```rust
// Current usage
for slot in 0..3 { ... }
if slot_idx >= 0 && slot_idx < 3 { ... }
stage: [i32; 3],  // In player.rs
```

**Recommended Enum:**
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StageSlot {
    Left = 0,
    Center = 1,
    Right = 2,
}

impl StageSlot {
    pub const COUNT: usize = 3;
    pub fn all() -> impl Iterator<Item = Self> { ... }
}
```

---

### 2. Color Constants (Card Colors)

**Current State:** Colors 0-6 used extensively with magic numbers like `color < 7`, `color == 7` (wildcard).

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/rules.rs`](engine_rust_src/src/core/logic/rules.rs) (lines 251-256, 301-306)
- [`engine_rust_src/src/core/logic/performance.rs`](engine_rust_src/src/core/logic/performance.rs) (lines 85-133)
- [`engine_rust_src/src/core/logic/hearts.rs`](engine_rust_src/src/core/hearts.rs)
- [`engine_rust_src/src/core/logic/interpreter/handlers/state.rs`](engine_rust_src/src/core/logic/interpreter/handlers/state.rs) (lines 976-1025)

**Examples:**
```rust
if color < 7 { ... }
if color == 7 { color = ctx.selected_color as usize; }
// attr 1-7 = colors 0-6. attr 0 = Generic/Any (index 6).
let idx = if attr == 0 || attr == 7 { 6 } else if attr <= 6 { attr - 1 } else { 99 };
```

**Recommended Enum:**
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(u8)]
pub enum Color {
    #[default]
    Smile = 0,     // Red
    Pure = 1,      // Green
    Cool = 2,      // Blue
    Active = 3,
    Natural = 4,
    Elegant = 5,
    All = 6,       // Wildcard/Any color
}

impl Color {
    pub const COUNT: usize = 7;
    pub fn is_valid(idx: usize) -> bool { idx < Self::COUNT }
}
```

---

### 3. Choice Index Constants

**Current State:** Special choice indices like `99` (Done/Cancel) and `999` (All) used throughout.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/constants.rs`](engine_rust_src/src/core/logic/constants.rs) (lines 56-59)
- [`engine_rust_src/src/core/logic/interpreter/handlers/state.rs`](engine_rust_src/src/core/logic/interpreter/handlers/state.rs) (lines 76, 89, 366, 474, etc.)
- [`engine_rust_src/src/core/logic/interpreter/handlers/flow.rs`](engine_rust_src/src/core/logic/interpreter/handlers/flow.rs)

**Examples:**
```rust
pub const CHOICE_DONE: i16 = 99;
pub const CHOICE_ALL: i16 = 999;
// Usage
if ctx.choice_index == 99 { ... }
```

**Recommendation:** These are already defined in `constants.rs` as `CHOICE_DONE` and `CHOICE_ALL`. Consider converting to an enum for stronger typing.

---

### 4. Depth Limits (Recursion Guards)

**Current State:** Magic numbers `5`, `10` used for recursion depth limits.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/rules.rs`](engine_rust_src/src/core/logic/rules.rs) (lines 35, 183, 359)
- [`engine_rust_src/src/core/logic/interpreter/conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs) (line 42)

**Examples:**
```rust
if depth > 5 {
    return 0;
}
if depth > 10 {
    return false;
}
```

**Recommended Enum:**
```rust
#[derive(Debug, Clone, Copy)]
pub enum RecursionDepth {
    BladeCalculation = 5,
    ConditionCheck = 10,
    Interpreter = 8,  // MAX_DEPTH in interpreter/mod.rs
}
```

---

### 5. Action ID Base Ranges

**Current State:** Already partially defined in `generated_constants.rs` but some ranges used directly as magic numbers.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/action_factory.rs`](engine_rust_src/src/core/logic/action_factory.rs)
- [`engine_rust_src/src/core/logic/handlers.rs`](engine_rust_src/src/core/logic/handlers.rs)

**Examples:**
```rust
// Already defined but used directly
ACTION_BASE_HAND + (h_idx as i32) * 10 + (slot as i32)
action >= 600 && action <= 602  // Live slot selection
action >= 100 && action < 200   // Discard index
action >= 200 && action < 300   // Hand index
```

**Recommendation:** The constants in `generated_constants.rs` are good. Ensure all code uses these constants instead of magic numbers.

---

### 6. Interpreter Limits

**Current State:** Magic numbers for interpreter step limits.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/interpreter/mod.rs`](engine_rust_src/src/core/logic/interpreter/mod.rs) (lines 41-42, 95-98)

**Examples:**
```rust
pub const MAX_DEPTH: usize = 8;
pub const MAX_BYTECODE_LOG_SIZE: usize = 500;
if executor.steps >= 1000 {
    println!("[ERROR] Interpreter infinite loop detected (1000 steps)");
}
```

**Recommendation:** Already well-defined. Consider adding `MAX_INTERPRETER_STEPS = 1000` to constants.

---

### 7. Target Slot Encoding

**Current State:** Magic numbers for special slot values like `0`, `4`, `10`, `-1`.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/interpreter/suspension.rs`](engine_rust_src/src/core/logic/interpreter/suspension.rs) (lines 116-131)
- [`engine_rust_src/src/core/logic/rules.rs`](engine_rust_src/src/core/logic/rules.rs) (lines 87-93, 232-238)

**Examples:**
```rust
// From suspension.rs
pub fn resolve_target_slot(target_slot: i32, ctx: &AbilityContext) -> usize {
    if target_slot == 0 && ctx.target_slot >= 0 {
        return ctx.target_slot as usize;
    }
    if target_slot == 4 && ctx.area_idx >= 0 {
        ctx.area_idx as usize
    } else if target_slot == -1 || target_slot == 4 {
        // Fallback to 0
    }
}

// From rules.rs - target area encoding
let target_area = s & 0xFF;
if target_area == 1 { targets_us = true; }
else if (target_area == 4 || target_area == 0) && other_slot == slot_idx { ... }
else if target_area == 10 && slot_idx as i16 == ctx.target_slot { ... }
```

**Recommended Enum:**
```rust
#[derive(Debug, Clone, Copy)]
pub enum TargetSlot {
    ThisSlot = 0,
    AllSlots = 1,
    OpponentSlot = 2,
    AreaIndex = 4,       // Use context.area_idx
    TargetSlot = 10,     // Use context.target_slot
    None = -1,
}
```

---

### 8. Card Type Values

**Current State:** Magic numbers `1` (Member), `2` (Live) used in filter checks.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/filter.rs`](engine_rust_src/src/core/logic/filter.rs) (lines 116-127)

**Examples:**
```rust
if self.card_type == 1 {
    // Member
    if !db.members.contains_key(&cid) { return false; }
} else if self.card_type == 2 {
    // Live
    if !db.lives.contains_key(&cid) { return false; }
}
```

**Recommendation:** These should use the existing `TargetType` enum or create a `CardType` enum.

---

### 9. Zone Values

**Current State:** Magic numbers for zones like `6` (Hand), `7` (Discard), `4` (Stage), etc.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/interpreter/handlers/movement.rs`](engine_rust_src/src/core/logic/interpreter/handlers/movement.rs)
- [`engine_rust_src/src/core/logic/interpreter/conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs)

**Examples:**
```rust
// Zone encoding
source_zone == 6 || source_zone == 7  // Hand or Discard
source_zone == 15  // Yell
if dest_slot == 6 { ... }  // Hand
else if dest_slot == 7 { ... }  // Discard
```

**Recommendation:** The `Zone` enum already exists in `enums.rs`. Ensure all code uses it instead of magic numbers.

---

### 10. RPS (Rock-Paper-Scissors) Values

**Current State:** Magic numbers `0`, `1`, `2` for RPS choices.

**Files with magic numbers:**
- [`engine_rust_src/src/core/logic/handlers.rs`](engine_rust_src/src/core/logic/handlers.rs)
- [`engine_rust_src/src/core/logic/game.rs`](engine_rust_src/src/core/logic/game.rs)

**Examples:**
```rust
let p0_wins = (p0 == 0 && p1 == 2) || (p0 == 1 && p1 == 0) || (p0 == 2 && p1 == 1);
```

**Recommended Enum:**
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum RpsChoice {
    Rock = 0,
    Paper = 1,
    Scissors = 2,
}
```

---

### 11. Special Card ID Values

**Current State:** Magic numbers like `-1` (empty/no card), special card IDs.

**Files with magic numbers:**
- Multiple files

**Examples:**
```rust
if cid == -1 { return false; }
stage[slot] = -1;  // Clear slot
```

**Recommendation:** Define constants for special card IDs:
```rust
pub const NO_CARD_ID: i32 = -1;
pub const INVALID_CARD_ID: i32 = 0;
```

---

## Priority Recommendations

### High Priority (Most Impactful)

1. **StageSlot Enum** - Used in 50+ locations
2. **Color Enum** - Central to game mechanics, heart/blade system
3. **Recursion Depth Constants** - Safety-critical

### Medium Priority

4. **TargetSlot Encoding** - Used in interpreter extensively
5. **Card Type Filter Values** - Used in filtering logic
6. **Zone Constants** - Ensure consistent usage with existing enum

### Low Priority (Nice to Have)

7. **RPS Choice Enum** - Limited usage
8. **Special Choice Indices** - Already partially defined

---

## Implementation Strategy

1. **Create new enum definitions** in `core/enums.rs` or a new `core/logic/game_enums.rs`
2. **Add constants** for special values in `core/logic/constants.rs`
3. **Systematically replace magic numbers** with enum variants or constants
4. **Add tests** to verify behavior matches previous magic number behavior
5. **Update documentation** to reflect the new type-safe constants

---

## Existing Good Patterns

The codebase already has good patterns in place:
- `Phase` enum in [`core/enums.rs`](engine_rust_src/src/core/enums.rs)
- `Zone` enum in [`core/enums.rs`](engine_rust_src/src/core/enums.rs)
- `TriggerType`, `EffectType`, `ConditionType` enums
- `generated_constants.rs` for opcode and action ID bases
- `constants.rs` for interpreter constants

The task is to extend this pattern to the remaining magic numbers found in this analysis.
