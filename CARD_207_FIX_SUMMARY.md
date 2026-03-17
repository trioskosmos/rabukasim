# Card 207 (Link to the FUTURE) - Hasunosora Score Bonus Fix

## Issue Summary
**Card**: PL!HS-bp2-020-L "Link to the FUTURE" (Live Card, ID 207)
**Ability**: "For each different-named Hasunosora member on your stage, increase thiscard's score by +2"
**Problem**: The score bonus was not appearing in the performance modal, staying at 0

## Root Cause Analysis

The bytecode compilation for the ON_LIVE_START ability had a missing FILTER flag.

### Pseudocode vs. Compiled Bytecode
```
Pseudocode: EFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="STAGE", FILTER="UNIT_HASU, UNIQUE_NAMES"}

Compiled Bytecode (BEFORE FIX):
[16, 2, 1769473, 268435456, 268487424, 1, 0, 0, 0, 0]
 |  |      |
 |  |      Filter Attribute = 1769473 (0x001B0001)
 |  Score Value = 2
 Opcode 16 = O_BOOST_SCORE

Compiled Bytecode (AFTER FIX):
[16, 2, 1802241, 268435456, 268487424, 1, 0, 0, 0, 0]
           |
   Filter Attribute = 1802241 (0x001B8001) - UNIQUE_NAMES flag added!
```

### The Bug in the Compiler
**File**: `engine/models/ability.py`, line 2193

The filter packing function (`_pack_filter_attr`) was NOT checking if "UNIQUE_NAMES" appeared in the filter string:

```python
# OLD CODE (INCOMPLETE):
if params.get("UNIQUE_NAMES") or params_upper.get("UNIQUE_NAMES"):
    filter_obj["unique_names"] = True
```

When the pseudocode contained `FILTER="UNIT_HASU, UNIQUE_NAMES"`, the "UNIQUE_NAMES" flag was in the filter string parameter, not as a direct key in params. Therefore, it was never set!

## Solution

### Fix Applied
Added check for "UNIQUE_NAMES" in the filter string (line 2193):

```python
# NEW CODE (CORRECT):
if params.get("UNIQUE_NAMES") or params_upper.get("UNIQUE_NAMES") or "UNIQUE_NAMES" in filter_str:
    filter_obj["unique_names"] = True
```

This simple one-line addition now checks all three potential sources for the UNIQUE_NAMES flag:
1. Direct parameter key (`params.get("UNIQUE_NAMES")`)
2. Uppercase parameter key (`params_upper.get("UNIQUE_NAMES")`)
3. **NEW**: Comma-separated filter string (`"UNIQUE_NAMES" in filter_str`)

### Impact
- ✅ Card database recompiled successfully (1787 cards)
- ✅ Card 207's bytecode updated:
  - Old filter_attr: 1769473 (0x001B0001) - BROKEN
  - New filter_attr: 1802241 (0x001B8001) - FIXED (added 0x8000)
- ✅ All 598 Rust engine tests pass
- ✅ No regressions

## Technical Details

### Filter Attribute Bit Layout (64-bit)
For card 207's BOOST_SCORE effect:
```
Bit 15: FILTER_UNIQUE_NAMES = 0x8000 (32768)
  - OLD: NOT SET (0x0)
  - NEW: SET (0x1)

Combined with other flags:
  - OLD: 0x00000000001B0001 (1,769,473)
  - NEW: 0x00000000001B8001 (1,802,241)
  - Difference: 32,768 (0x8000)
```

### How It Works in the Engine
When executing the BOOST_SCORE bytecode during ON_LIVE_START:
1. The engine reads the filter_attr (1802241)
2. Detects FILTER_UNIQUE_NAMES is set
3. Counts stage cards matching "UNIT_HASU" (Hasunosora members)
4. Deduplicates by unique card name
5. Multiplies score bonus by unique count: +2 × unique_count
6. Adds to `live_score_bonus_logs` for performance modal display

Example: 2 different Hasunosora members = +4 score bonus

## Files Modified
- **engine/models/ability.py** (line 2193): Added UNIQUE_NAMES filter string check

## Testing
- Created integration test: `engine_rust_src/tests/repro_card207_hasunosora_score.rs`
- All existing tests pass without modification
- Verified bytecode change: 1769473 → 1802241
- Verified filter_attr packing includes 0x8000 bit

## Result
Card 207 now correctly functions as intended:
- Hasunosora members with different names are counted as unique
- Score bonus of +2 per unique member is applied
- Bonus appears in the performance modal breakdown
- Works with other group members (supports Cerise, Doll, Mirakura via tags)
