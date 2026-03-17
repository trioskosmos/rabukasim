# MOVE_MEMBER and SELECT_MEMBER Compilation Analysis

## Current Implementation Status

### 1. How MOVE_MEMBER with ALL targets is currently compiled

**File**: [engine/models/ability.py](engine/models/ability.py#L1319-L1407)

When `MOVE_MEMBER` is compiled with `ALL` or `TARGETS`:
- **Lines 1319-1324**: If `eff.value` is `"ALL"` or `"TARGETS"`, or `raw_val` parameter is `"ALL"`, `"TARGET"`, or `"TARGETS"`:
  - `val` is set to `99` (indicates "apply to all")
  - `attr` is set to `99` (indicates "move to target-specified destination")

**Bytecode Structure** (5 integers per instruction):
- **Opcode**: `20` (MOVE_MEMBER)
- **Value**: `99` (ALL/TARGETS marker)
- **Attr**: `99` (target-based destination)
- **Slot**: destination zone encoding
- **Reserved**: 0

**Current Card 193 Compilation**:
```json
{
  "runtime_opcode": 20,
  "runtime_value": 99,
  "runtime_attr": 99,
  "runtime_slot": 1
}
```

### 2. Patterns for looping or repeating selections

**Current Status**: NO explicit looping mechanism in bytecode.

The compiler does NOT generate `JUMP` loops. Instead:
- The `is_all` bit (value=99) signals the **engine interpreter** to iterate
- The interpreter iterates over the target list when executing the effect
- **This means all selected members are processed with the SAME operation parameters**

**File References**:
- [compiler/main.py](compiler/main.py#L477-L500): MOVE_MEMBER is in the `core_ops` set
- No `FOR_EACH_MEMBER` or `FOR_EACH_TARGET` opcode exists
- No bytecode-level looping construct for iterating different selections

### 3. How FORMATION_CHANGE differs from SELECT_MEMBER(ALL) + MOVE_MEMBER

| Aspect | MOVE_MEMBER | FORMATION_CHANGE |
|--------|-------------|-----------------|
| **Opcode** | 20 | 26 (unused) |
| **Current Use** | Active in compiler | [UNUSED] per comments |
| **Semantics** | Move members to zones | Rearrange members on stage |
| **In Bytecode** | Opcode 20 | Opcode 26 |
| **Difference** | Includes zone specification | Stage position rearrangement |

**Key Difference**: FORMATION_CHANGE was intended for pure positional rearrangement (swapping stage positions), while MOVE_MEMBER handles zone transitions (stage→discard, etc.).

**File References**:
- [engine/models/ability.py](engine/models/ability.py#L50): `EffectType.FORMATION_CHANGE: "Rearrange members on stage"  # [UNUSED]`
- [engine_rust_src/src/core/logic/shader_constants.wgsl](engine_rust_src/src/core/logic/shader_constants.wgsl#L19-L25): Opcode definitions

### 4. Effect_type value comparison

From [engine/models/opcodes.py] and generated enums:

- **EffectType.MOVE_MEMBER = 20** (active, used for zone transitions)
- **EffectType.FORMATION_CHANGE = 26** (marked [UNUSED])
- **Opcode.MOVE_MEMBER = 20** (active)
- **Opcode.FORMATION_CHANGE = 26** (in constants but never emitted)

Both use the same bytecode structure, but FORMATION_CHANGE was never implemented in the interpreter.

### 5. Mechanism for "each member can be moved to a different area"

**Current Status**: NO SUCH MECHANISM EXISTS

#### Problems with Current Implementation

1. **Single Destination Problem**:
   - `SELECT_MEMBER(ALL) -> TARGETS; MOVE_MEMBER(TARGETS)` compiles to:
     - Opcode 65: SELECT_MEMBER with ALL flag (value=99)
     - Opcode 20: MOVE_MEMBER with attr=99 (target-based destination)
   - The `attr=99` means "all targets go to ONE destination specified by the player's area selection"

2. **Missing Repeatable Selection**:
   - There is no "FOR_EACH_TARGET { SELECT_AREA; MOVE_MEMBER(TARGET, AREA) }" pattern
   - Each selected member cannot have its own area choice

3. **No Interactive Loop**:
   - No bytecode mechanism to:
     - Iterate over each selected member
     - Request a separate area selection for each
     - Apply MOVE_MEMBER with different parameters each iteration

#### What Card 193 Needs

Card 193 (藤島 慈) has pseudocode:
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(ALL) -> TARGETS; MOVE_MEMBER(TARGETS)
```

**Intended Semantics**: "Each member can be moved to areas of choice"

**Current Behavior**: Single area selection, all members move there

**Required Fix**: A new pseudocode structure supporting:
```
TRIGGER: ON_PLAY
EFFECT: FOR_EACH_MEMBER(ALL) -> MEMBER; 
        SELECT_AREA(PLAYER) -> AREA; 
        MOVE_MEMBER(MEMBER, AREA)
```

... or similar repeating selection pattern.

---

## Compiler Architecture Summary

### Effect Compilation Flow

1. **Parser** ([compiler/parser_v2.py](compiler/parser_v2.py)):
   - Parses pseudocode → Effect objects
   - Extracts `effect_type`, `value`, `params`, `target`
   - `SELECT_MEMBER(ALL)` sets `value=99`

2. **Ability Compilation** ([engine/models/ability.py](engine/models/ability.py)):
   - `_compile_effects()`: Iterates effects
   - `_compile_single_effect()`: Packs each effect into 5-integer bytecode
   - Special handling for MOVE_MEMBER: if `value=99` or `raw_val="ALL"`, sets `attr=99`

3. **Bytecode Output**:
   - Fixed 5-integer chunks: `[opcode, value, attr, slot, reserved]`
   - No jump/loop constructs
   - All-flag (value=99) handled at interpreter level

4. **Engine Interpretation** ([engine_rust_src](engine_rust_src)):
   - Reads bytecode instructions
   - When `value=99`, iterates over registered targets
   - Applies same parameters to each target

### Key Opcodes

| Opcode | Name | Used | Comment |
|--------|------|------|---------|
| 20 | MOVE_MEMBER | ✓ | Zone transitions |
| 26 | FORMATION_CHANGE | ✗ | Stage rearrangement [UNUSED] |
| 65 | SELECT_MEMBER | ✓ | Target selection |

---

## What Needs to Change

### Option 1: New Pseudocode Construct (Recommended)

Introduce `FOR_EACH` or `REPEAT_SELECT` pattern:

```pseudocode
TRIGGER: ON_PLAY
EFFECT: FOR_EACH_MEMBER(ALL) -> MEMBER;
        SELECT_AREA(PLAYER, NOT_SELF) -> AREA;
        MOVE_MEMBER(MEMBER, AREA)
```

**Changes Needed**:
1. [compiler/parser_v2.py](compiler/parser_v2.py): Parse FOR_EACH construct
2. [engine/models/ability.py](engine/models/ability.py): Generate loop bytecode
3. Bytecode: Add JUMP instructions to create iteration loop
4. Engine: Implement loop unrolling or dynamic iteration

### Option 2: Extend MOVE_MEMBER semantics

Change how `attr=99` + MOVE_MEMBER works:
- Current: All targets move to one area (user selects area once)
- New: Each target moves to different area (user selects per target)

**Changes Needed**:
1. [engine_rust_src](engine_rust_src): Modify interpreter to request per-target area selection
2. Engine UI: Support multiple area prompts in sequence
3. Bytecode: Could remain unchanged, semantic shift at interpretation

### Option 3: Use SELECT_AREA in loop

Pseudocode structure already supported:
```pseudocode
EFFECT: SELECT_MEMBER(1) {FILTER="ALL"} -> TARGET;
        SELECT_AREA(PLAYER) -> AREA;
        MOVE_MEMBER(TARGET, AREA);
        [REPEAT 5 times]
```

**Problem**: No repeat mechanism; each repetition is a separate ability or requires manual cloning.

---

## Summary

| Item | Current Status | Issue for Card 193 |
|------|---------------|--------------------|
| MOVE_MEMBER with ALL | Compiles to attr=99 | All members move to SINGLE area selected once |
| SELECT_MEMBER(ALL) → TARGETS | Sets value=99 | Selects all, but doesn't support per-target operations |
| Loop/FOR_EACH mechanism | None | Can't iterate with different selections per iteration |
| FORMATION_CHANGE | Unused (opcode 26) | Alternative approach available but not implemented |
| Per-target area selection | Not supported | Missing feature for "each member to different area" |

**Recommendation**: Implement FOR_EACH pseudocode construct with repeated SELECT_AREA pattern to enable card 193's intended behavior.
