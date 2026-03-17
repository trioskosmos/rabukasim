# Rust Test Analysis: test_card_557_logic_repro Failure

## Test Failure Summary
- **Test**: `test_card_557_logic_repro` in `engine_rust_src/tests/repro_bp4_001.rs`
- **Expected**: Energy zone length = 8 (charge 1 energy)
- **Actual**: Energy zone length = 7 (no energy charged)
- **Card**: PL!SP-bp4-001-P (Card ID 557 - Kanon)

## Root Cause Analysis

### Card 557 Pseudocode
```
TRIGGER: ON_PLAY
CONDITION: ALL_MEMBERS {FILTER="GROUP_ID=3"}, ENERGY_COUNT {MIN=7}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
```

### Current Bytecode
```
[209, 4, 3, 0, 48, 33, 1, 0, 0, 4, 1, 0, 0, 0, 0]

Decoded:
  00: CHECK_GROUP_FILTER   | v(Val):4, a(Attr):3, s(Comp):GE (>=), s(Slot):Left Slot
  05: PLACE_UNDER          | v=1, a=0, s=4
  10: RETURN               | v=0, a=0, s=0
```

### Issues Identified

1. **Missing ENERGY_COUNT Condition**: The bytecode only contains C_GROUP_FILTER but is missing the `ENERGY_COUNT {MIN=7}` condition from the pseudocode.

2. **Wrong Opcode for Energy Charging**: The pseudocode says `PLACE_ENERGY_WAIT(1) -> PLAYER` which means "charge 1 energy from deck to player's energy zone with wait state". This should use `O_ENERGY_CHARGE` (opcode 23), not `O_PLACE_UNDER` (opcode 33).

3. **Compiler Bug**: In `compiler/parser_v2.py` line 101:
   ```python
   "PLACE_ENERGY_WAIT": ("PLACE_UNDER", {"type": "energy", "wait": True}),
   ```
   This incorrectly maps PLACE_ENERGY_WAIT to PLACE_UNDER instead of ENERGY_CHARGE.

4. **Handler Mismatch**: The O_PLACE_UNDER handler in `engine_rust_src/src/core/logic/interpreter/handlers/member_state.rs` only handles:
   - `a == 0`: Move from hand to stage_energy
   - `a == 1`: Move from energy_zone to stage_energy

   It does NOT handle charging from energy_deck to energy_zone.

## Fix Required

### Option 1: Fix the Compiler (Recommended)
Change `compiler/parser_v2.py` to map PLACE_ENERGY_WAIT to ENERGY_CHARGE:
```python
"PLACE_ENERGY_WAIT": ("ENERGY_CHARGE", {"wait": True}),
```

And update the main.py to properly compile ENERGY_CHARGE with wait state flag.

### Option 2: Fix the Handler
Add logic to O_PLACE_UNDER handler to detect "type: energy" parameter and use O_ENERGY_CHARGE behavior.

### Option 3: Fix the Test
If PLACE_ENERGY_WAIT is intentionally different from ENERGY_CHARGE, update the test to match the actual expected behavior.

## Notes
- The test `test_card_557_logic_fail_if_not_only_liella` passes because it expects no energy charging (energy_zone stays at 7), which matches the current buggy behavior.
- After fixing the bytecode, the test will need to include proper ENERGY_COUNT condition check.
