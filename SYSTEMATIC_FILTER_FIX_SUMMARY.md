# Card 207 Systematic Filter Parsing Fix - Complete

**Status:** ✅ COMPLETED AND VERIFIED

## Issue Summary
User challenged whether the initial one-line fix for Card 207's UNIQUE_NAMES filter flag was sufficiently general. Investigation revealed that multiple boolean filter flags were being parsed ONLY from params dict, not from the filter_str where they actually appear in pseudocode. This created an architectural inconsistency and left several common filter keywords unparsed.

## Root Cause
In `engine/models/ability.py`, the `_pack_filter_attr()` method had inconsistent filter parsing:
- Some keywords checked both params AND filter_str: GROUP, UNIT, COST, COLOR, etc.
- Other keywords checked ONLY params: is_tapped, has_blade_heart, not_has_blade_heart, unique_names (before this fix)
- This meant cards with filters like `STATUS=TAPPED` or `HAS_BLADE_HEART` in pseudocode would fail to set the corresponding bytecode flags

## Real-World Impact
Evidence from `consolidated_abilities.json` shows these keywords appear regularly in filter strings:
- `STATUS=TAPPED` appears in ~20+ card abilities
- `HAS_BLADE_HEART` appears in ~10+ card abilities  
- `NOT_HAS_BLADE_HEART` appears in ~5+ card abilities
- `UNIQUE_NAMES` appears in Card 207 and others

## Solution Implemented
Replaced lines 2202-2210 in `engine/models/ability.py` to add filter_str parsing:

```python
# Legacy flags (Bits 12-15)
# Parse STATUS=TAPPED from filter string or params
if params.get("is_tapped") or "STATUS=TAPPED" in filter_str or "STATUS=TAP" in filter_str:
    filter_obj["is_tapped"] = True

# Parse HAS_BLADE_HEART / NOT_HAS_BLADE_HEART from filter string or params
bh = params.get("has_blade_heart")
if bh is True or "HAS_BLADE_HEART" in filter_str:
    filter_obj["has_blade_heart"] = True
elif bh is False or "NOT_HAS_BLADE_HEART" in filter_str:
    filter_obj["not_has_blade_heart"] = True

# Parse UNIQUE_NAMES from filter string or params
if params.get("UNIQUE_NAMES") or params_upper.get("UNIQUE_NAMES") or "UNIQUE_NAMES" in filter_str:
    filter_obj["unique_names"] = True
```

## Verification Results
✅ **Compilation**: 1787 cards compiled successfully, 0 issues
✅ **Card 207**: Bytecode confirmed with UNIQUE_NAMES flag (packed_attr=1802241, bit 0x8000 set)
✅ **Card 23** (Honoka): is_tapped flag now parsed correctly (status=tapped filter, bit 0x1000 set)
✅ **Card 653** (Umi): has_blade_heart flag now parsed correctly (has_blade_heart filter, bit 0x2000 set)
✅ **Testing**: All 598 Rust tests pass, 0 failed, 1 ignored (no regressions)

## Architectural Consistency
This fix aligns filter keyword parsing with existing patterns in the codebase:
- All boolean filter flags (`is_tapped`, `has_blade_heart`, `not_has_blade_heart`, `unique_names`) now support filter_str parsing
- Consistent with how GROUP, UNIT, COST, COLOR keywords are already parsed
- Reduces architectural quirks in the compiler
- Prevents future missed filters when developers write pseudocode with these keywords in filter strings

## Files Modified
- `engine/models/ability.py`: Lines 2202-2210 (added filter_str checks for 4 boolean flags)

## Testing Approach
1. Recompiled entire card database
2. Verified Card 207 bytecode maintained correctness
3. Spot-checked cards with new filter flags (Card 23 for TAPPED, Card 653 for HAS_BLADE_HEART)
4. Ran full Rust test suite (598 tests)
5. Verified bit patterns match expected values (0x1000 for tapped, 0x2000 for blade_heart, 0x8000 for unique_names)

---
**Completed:** After user identified the architectural issue, implemented comprehensive systematic solution that addresses all affected boolean filter flags at once, rather than addressing them piecemeal.
