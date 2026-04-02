# Bit-Packed Enum Migration: Phase 1 Complete

## Summary

Successfully isolated all legacy bit-packing code into a quarantined `legacy_codec` module. The migration from packed integer attributes to structured JSON representations has begun.

## What Was Done

### 1. Created `legacy_codec.rs` Module
- **Location**: `src/core/logic/legacy_codec.rs`
- **Purpose**: Quarantine all packed integer encoding/decoding functions
- **Contents**:
  - `DecodedSlot` pack/unpack functions
  - `DecodedHeartCounts` pack/unpack functions  
  - `DecodedLookAndChoose` pack/unpack functions
  - `DecodedHeartRequirements` pack/unpack functions
  - `CardFilter` pack/unpack functions (`to_attr_computed`, bit masking)

### 2. Renamed `from_attr` → `from_attr_legacy`
- **File**: `src/core/logic/filter.rs`
- **Change**: `CardFilter::from_attr(a: i64)` renamed to `from_attr_legacy`
- **Purpose**: Make legacy dependency explicit at all call sites

### 3. Updated All Call Sites
Changed 15+ files to use `from_attr_legacy`:
- `src/core/logic/models.rs`
- `src/core/logic/interpreter/logging.rs`
- `src/core/logic/filter_attr_compat.rs`
- `src/core/logic/interpreter/conditions/counts.rs`
- `src/core/logic/interpreter/conditions/opcodes.rs`
- `src/core/logic/action_gen/response.rs`
- `src/core/logic/game_rules_ext.rs`
- `src/core/logic/interpreter/handlers/interaction_select_cards.rs`
- `src/core/logic/interpreter/handlers/interaction_recovery.rs`
- `src/core/logic/interpreter/handlers/movement_discard.rs`
- `src/core/logic/interpreter/handlers/flow_select.rs`
- `src/perf_tests.rs`

### 4. Removed Legacy Variants from Deserialization Enums
- **File**: `src/core/logic/interpreter/instruction.rs`
- **Changed**: `DecodedSlotRaw`, `DecodedHeartCountsRaw`, `DecodedLookAndChooseRaw`, `DecodedFilterAttrRaw`
- **Before**: Dual variants `Legacy(i64)` and `Structured(DecodedXStructuredRaw)`
- **After**: Only `Structured` variant remains
- **Effect**: Forces exclusive use of structured JSON for deserialization

### 5. Updated `from_frame_json()` to Structured-Only
- **File**: `src/core/logic/filter.rs`
- **Change**: Removed packed attribute path, now only deserializes structured `CardFilter` from JSON

## Current State

### Test Results
```
cargo test --lib
test result: ok. 527 passed; 0 failed; 3 ignored; 0 measured; 0 filtered out
```

All tests pass. The refactoring successfully:
- Maintains backward compatibility through `from_attr_legacy`
- Forces new code to use structured representations
- Creates a clear boundary between legacy and modern code paths

### Code Location
- **Branch**: `ability-rewrite`
- **Commit**: `b2c2e7e`
- **Files Changed**: 23 files, +1478/-1221 lines

## Architecture After Migration

### Before (Hybrid)
```rust
// Could receive either packed integer OR structured JSON
enum DecodedSlotRaw {
    Legacy(i32),                    // Packed: 0x00010002
    Structured(DecodedSlotStructuredRaw),  // JSON: {"source_zone": "DECK", ...}
}

// Runtime had to handle both
let slot = if is_packed(slot_raw) {
    decode_packed(slot_raw)
} else {
    deserialize_structured(slot_json)
};
```

### After (Structured-Only)
```rust
// Only accepts structured JSON
enum DecodedSlotRaw {
    Structured(DecodedSlotStructuredRaw),  // JSON: {"source_zone": "DECK", ...}
}

// Legacy code path explicitly marked
let filter = CardFilter::from_attr_legacy(packed_u64);
```

## Next Steps to Complete Migration

### Phase 2: Audit Remaining Dependencies
Find all uses of `from_attr_legacy` to identify migration candidates:

```bash
grep -r "from_attr_legacy" src/ --include="*.rs"
```

Each occurrence represents a code path still dependent on packed integers.

### Phase 3: Update Test Data
Convert test JSON with packed `attr` values to structured `CardFilter` objects:

```json
// Before (packed)
{
  "attr": 4294967297,  // 0x0000000100000001
  "opcode": "SELECT"
}

// After (structured)
{
  "attr": {
    "target_player": 1,
    "card_type": 0,
    "group_enabled": false,
    "group_id": 1
  },
  "opcode": "SELECT"
}
```

### Phase 4: Update Production Data
Check `data/ability_runtime_entrypoints.json` for packed integer attributes and convert to structured format.

### Phase 5: Eventually Remove `legacy_codec.rs`
Once no callers remain:
1. Delete `legacy_codec.rs`
2. Remove `from_attr_legacy` from `CardFilter`
3. Delete `to_attr()` encoding functions
4. Remove all bit-shift/mask constants from `constants.rs`

## Migration Strategy

### For Each `from_attr_legacy` Call Site:

1. **Identify the source** of the packed integer
   - Test data JSON?
   - Production data JSON?
   - Runtime calculation?

2. **Convert source to structured JSON**
   - If test data: update test JSON files
   - If production data: update data generation pipeline
   - If runtime: refactor to build `CardFilter` struct directly

3. **Update call site**
   - Change `CardFilter::from_attr_legacy(x)` to direct struct construction or `serde_json::from_value()`

4. **Verify**
   - Run tests to ensure behavior unchanged

## Benefits of Complete Migration

1. **Readability**: No more `0xFF` masks and magic bit shifts
2. **Type Safety**: Structured types checked at compile time
3. **Debugging**: Human-readable JSON in logs and traces
4. **Maintainability**: No dual-path logic (packed vs structured)
5. **Performance**: Potential optimization once packing overhead removed

## Files Requiring Attention

### High Priority (Core Runtime)
- `src/core/logic/interpreter/conditions/counts.rs` - Heavy use of `from_attr_legacy` in count resolution
- `src/core/logic/interpreter/conditions/opcodes.rs` - Opcode handlers with packed attrs
- `src/core/logic/models.rs` - `AbilityFrame::from_effect()` uses packed attrs

### Medium Priority (Handlers)
- `src/core/logic/interpreter/handlers/flow_select.rs`
- `src/core/logic/interpreter/handlers/interaction_select_cards.rs`
- `src/core/logic/interpreter/handlers/interaction_recovery.rs`
- `src/core/logic/interpreter/handlers/movement_discard.rs`

### Low Priority (Utilities)
- `src/core/logic/filter_attr_compat.rs` - Compatibility layer (delete when migration complete)
- `src/perf_tests.rs` - Performance tests using packed format

## Conclusion

Phase 1 successfully isolated legacy bit-packing code. The `legacy_codec` module acts as a quarantine zone - all packed integer operations are now explicitly marked and contained. 

The path forward is clear: systematically replace each `from_attr_legacy` call with structured JSON handling, then delete the legacy module once empty.

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-03  
**Related**: `bytecode_bitpacking_migration_plan.md`
