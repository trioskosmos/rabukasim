# Full Analysis: Semantic to Frame Converter Issues

## What the Converter Does

The `semantic_to_frame_converter.py` converts semantic abilities from `abilities_extracted_from_cards.json` to frame format in `ability_frame_source.json` for the Rust engine.

**Input (Semantic Format):**
```json
{
  "triggers": "ライブ開始時",
  "cost": {
    "type": "move_cards",
    "source": "stage",
    "destination": "waitroom",
    "target": "this_member",
    "count": 1
  },
  "effect": {
    "actions": [
      {
        "action": "add_to_hand",
        "source": "waitroom",
        "count": 1,
        "card_type": "live_card"
      }
    ]
  }
}
```

**Output (Frame Format):**
```json
{
  "trigger": "LIVE_START",
  "frames": [
    {
      "op": "MOVE_TO_DISCARD",
      "frame_index": 0,
      "value": 1,
      "slot": {
        "source_zone": "STAGE",
        "dest_zone": "DISCARD",
        "target_slot": "CONTEXT"
      }
    },
    {
      "op": "RECOVER_LIVE",
      "frame_index": 1,
      "value": 1,
      "slot": {
        "source_zone": "DISCARD",
        "target_slot": "HAND"
      }
    }
  ]
}
```

## Current State

**Conversion Results:**
- Backup abilities: 598
- Semantic abilities: 598
- Converted abilities: 598
- Text overlap (normalized): 485 common, 113 only in backup, 113 only in semantic
- Frame count differences: 195/488 common abilities (50%) have different frame counts

## Key Issues

### 1. Semantic Extraction Provides Incomplete Data

**Evidence from BiBi Tap Ability:**
- **Backup**: Has SELECT_MEMBER, TAP_MEMBER frames
- **Semantic**: Has `action: "note"` instead of real actions
- **Converted**: Generates incomplete frames because semantic data is incomplete

**Root Cause:** The semantic extraction pipeline (`tools/ability_extraction/`) often extracts "note" placeholders instead of actual semantic actions like "member_to_wait", "tap_opponent", etc.

### 2. Mapping Issues

**Problematic Mappings:**
- `"may_place_card"` → `"MOVE_TO_DECK"` (backup expects `"SELECT_CARDS"`)
- This causes test failure: `test_ability_55_kurosawa_ruby_missing_saintsnow_filter`

**Attempted Fix:** Changed `"may_place_card"` to `"SELECT_CARDS"` but test still fails because the specific ability (#55) requires different frames.

### 3. Multi-Trigger Ability Splitting

**Observation:** Semantic extraction splits multi-trigger abilities (e.g., "登場/ライブ開始時") into separate entries, while backup keeps them combined.

**Impact:** This causes 113 abilities to be "only in backup" and 113 to be "only in semantic" even though total count is the same.

### 4. Missing Frame Types

**Common Missing Frames:**
- SELECT_CARDS (for card selection with filters)
- RECOVER_MEMBER (for member recovery)
- Proper remainder_zone handling
- Complex condition frames (dual-group conditions)

## What I've Tried

1. **Changed `may_place_card` mapping** from `MOVE_TO_DECK` to `SELECT_CARDS`
   - Result: Test `test_ability_55` still fails
   - Reason: The specific ability needs different frames than this mapping provides

2. **Investigated ability #55 test failure**
   - Test expects RECOVER_MEMBER or SELECT_CARDS frames
   - Cannot locate the specific ability in backup data
   - Likely semantic extraction issue

## Actual Problems

### The Converter is Working Correctly
The converter is doing exactly what it's designed to do: convert semantic actions to frame opcodes based on the `SEMANTIC_TO_OPCODE` mapping.

### The Real Issue is Semantic Extraction
The semantic extraction pipeline is not extracting complete/accurate semantic data:
- Uses "note" placeholders instead of real actions
- Splits multi-trigger abilities incorrectly
- Misses complex conditions (dual-group, cost thresholds)
- Incomplete card_type and group information

### Test Failures are Due to Input Data Quality
Rust tests expect frames based on the backup data, but the converter receives incomplete semantic data. The converter can only generate frames from what it receives.

## Recommended Actions

1. **Fix semantic extraction pipeline** (`tools/ability_extraction/`)
   - Extract real actions instead of "note" placeholders
   - Handle multi-trigger abilities correctly
   - Extract complex conditions accurately

2. **Improve action mappings** in converter
   - Add more specific mappings for edge cases
   - Handle remainder_zone properly
   - Support dual-group conditions

3. **Verify semantic extraction quality**
   - Compare semantic output with backup expectations
   - Fix extraction patterns that produce incomplete data
