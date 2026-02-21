# Pseudocode Specification

This document defines the standard pseudocode format used to represent card abilities in the `Love Live! School Idol Collection` engine. This format is designed to be human-readable while maintaining strict bi-directional compatibility with the game engine's `Ability` model and bytecode compiler.

## Structure

An `Ability` is represented as a block of text containing the following sections, in order. Only `TRIGGER` is strictly required; other sections are optional if not applicable.

```text
TRIGGER: [TriggerType]
(Once per turn)  <-- Optional flag
COST: [CostType]([Value]) {PARAMS...}
CONDITION: [NOT] [ConditionType] {PARAMS...}
EFFECT: [EffectType]([Value]) -> [TargetType] {PARAMS...}
```

## Parsing Rules

### 1. Triggers
- Format: `TRIGGER: [TriggerName]`
- Valid values are defined in `TriggerType` IntEnum (e.g., `ON_PLAY`, `ON_LIVE_START`).
- The flag `(Once per turn)` can appear on the same line or the line immediately following.

### 2. Costs, Conditions, Effects
- **Costs**: Comma-separated list.
  - Format: `NAME(VALUE) {KEY=VAL, ...} (Optional)`
- **Conditions**: Comma-separated list.
  - Format: `[NOT] NAME {KEY=VAL, ...}`
- **Effects**: Semicolon-separated list.
  - Format: `NAME(VALUE) -> TARGET {KEY=VAL, ...} (Optional)`
- **Parameters**: Enclosed in curly braces `{}`.
  - Standard format: `KEY=VALUE`.
  - Values can be integers, strings (case-insensitive enum names), or JSON arrays.
  - **Standard Keys**:
    - `COST_MAX`, `COST_MIN` (integers)
    - `GROUP`, `UNIT` (strings)
    - `FROM`, `TO` (zone names)
    - `MIN`, `MAX` (integers)

### 3. Modal Effects (SELECT_MODE)
For effects that offer a choice (e.g., `SELECT_MODE`), the options are listed in an indented block immediately following the effect line.

```text
EFFECT: SELECT_MODE(1) -> SELF {{"options_text": ["Option A", "Option B"]}}
    Options:
      1: DRAW(1)->SELF
      2: RECOVER_LIVE(1)->SELF
```

- Typically `SELECT_MODE` value is 1 (choose 1).
- `options_text` param contains the UI text for buttons.
- The `Options:` block must follow the specific indentation and numbering format `N: Effect...`.

## Verification
Reliability is enforced via `tools/verify_pseudocode.py`, which performs a round-trip check:
1. `Compiled Ability` -> `Generate Pseudocode` -> `Parse Pseudocode` -> `Re-Compile`
2. Bytescodes of the original and re-compiled ability MUST match exactly.

- **Multipliers**: `{MULTIPLIER=MEMBER|ENERGY}` indicates the value scales with these factors.

## Canonical Effect Names

To ensure consistency, use the following standard names:
- **`ADD_TO_HAND`** (not `ADD_HAND`, `MOVE_TO_HAND`)
- **`TAP_MEMBER`** (not `TAP_PLAYER`, `TAP_SELF`)
- **`ENERGY_CHARGE`** (not `CHARGE_ENERGY`)
- **`MOVE_TO_DISCARD`** (not `MOVE_DISCARD`, `REMOVE_SELF`)
- **`SWAP_ZONE`** (not `SWAP_SELF`)
- **`REDUCE_LIVE_SET_LIMIT`** (not `SELECT_LIMIT`)
- **`BUFF_POWER`** (not `POWER_UP`)
- **`MOVE_TO_DECK`** (not `MOVE_DECK`)
- **`OPPONENT_CHOOSE`** (not `OPPONENT_CHOICE`)
- **`ADD_HEARTS`** (not `GRANT_HEART`)
