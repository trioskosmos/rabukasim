# LovecaSim Bytecode Specification (v2)

This document defines the binary communication format between the Python compiler (Ability System) and the Rust Game Engine.

## instruction Structure
Each instruction is a fixed-size block of 5 `i32` values (20 bytes).

```rust
[OP, V, A_LOW, A_HIGH, S]
```

### 1. OP (Opcode)
The ID of the operation to perform. See `data/metadata.json` for mapping.

### 2. V (Primary Value)
A 32-bit signed integer used for counts, logic IDs, or packed bitfields.

#### Special Packing: LOOK_AND_CHOOSE
- **Bits 0-7**: Look Count (How many cards to reveal/draw)
- **Bits 8-15**: Pick Count (How many cards the player can choose)
- **Bits 23-29**: Color Filter Mask (1=Pink, 2=Red, 4=Yellow, 8=Green, 16=Blue, 32=Purple, 64=Star)
- **Bit 30**: Reveal Flag (1 if chosen cards should be revealed)

### 3. A (Attribute/Filter)
A 64-bit unsigned integer (`A_HIGH << 32 | A_LOW`).
Primarily used for the **Global Card Filter System**.

- **Bits 0-1**: Type Filter (0=Any, 1=Member, 2=Live)
- **Bit 4**: Filter Optional (1 if the effect can be skipped)
- **Bit 5**: Group Enable
- **Bits 6-12**: Group ID
- **Bit 16**: Unit Enable
- **Bits 17-23**: Unit ID
- **Bit 24**: Cost Enable
- **Bits 25-29**: Cost Value
- **Bit 30**: Cost Operator (0=Exact, 1=Less/Equal)
- **Bit 31**: Color Mask Enable
- **Bits 32-38**: Color Mask
- **Bits 48-63**: Character ID Filter

### S-Word (Slot/Source/Flags)
- Bits 0-7: Target Slot Index (0-2: Stage, 3: Success, 4: Context/Area, 6: Hand, 7: Discard, 8: Deck)
- Bit 15: Opponent Flag (Target opponent instead of self)
- Bits 16-23: Source Zone ID (Same mapping as Target Slot)
- Bit 24: `Target Opponent` (Standard flag, often redundant with Bit 15)
- Bit 25: `REVEAL_UNTIL` Live Flag / `PLACE_VAL` capture flag.
- Bit 26: `EMPTY_SLOT_ONLY` flag.
- Bit 27: `WAIT` flag (Energy Charge).
- Bits 28-30: Area index (1=Left, 2=Center, 3=Right).

#### Opcode-Specific Exceptions (S-Word)
- **DYNAMIC Effects** (per_card Multipliers):
  - Bit 16: `DYNAMIC` Flag (1 = Dynamic).
  - Bits 8-15: `count_op` (ConditionType enum) used as the count source.
- **LOOK_AND_CHOOSE**:
  - Bits 8-15: `rem_val` (Destination zone for cards NOT picked).
- **Condition Opcodes** (e.g., `CHECK_STAGE_COUNT`):
  - Bits 4-7: `CompOp` (Comparison Operator: 0=EQ, 1=GT, 2=LT, 3=GE, 4=LE).
  - Bits 0-3: Target Slot.

### V-Word (Value)
- Standard: 32-bit signed integer.

#### Opcode-Specific Exceptions (V-Word)
- **LOOK_AND_CHOOSE**:
  - Bits 0-7: Look Count.
  - Bits 8-15: Pick Count.
  - Bits 16-22: Character ID 1 (Primary).
  - Bits 23-29: Color Mask (7-bit: P,R,Y,G,B,V,S).
  - Bit 30: Reveal Flag.
- **MOVE_TO_DISCARD**:
  - Bit 31: `UNTIL_SIZE` Mode (1 = discard until zone size matches `V & 0x7FFFFFFF`).
- **JUMP / JUMP_IF_FALSE**:
  - `V` is the relative offset in instructions (5-word chunks).

### A-Word (Attribute/Filter)
- Standard: 64-bit filter attribute.

#### Opcode-Specific Exceptions (A-Word)
- **META_RULE**:
  - `A` word is repurposed as the Meta Rule Type ID (0-13).
- **LOOK_AND_CHOOSE** Character IDs:
  - Repurposes Unit ID (bits 17-23) for Char ID 2.
  - Repurposes Cost bits (bits 24-30) for Char ID 3.
- **TOTAL_COST_LIMIT**:
  - Bit 50: Set for cumulative multipliers across multiple selections.
- **OPTIONAL**:
  - Bit 63: Legacy optional flag (often used in cost checking).
