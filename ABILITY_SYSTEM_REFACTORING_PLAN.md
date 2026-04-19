# Ability System Refactoring Plan

## Executive Summary

The ability execution system in `engine_rust_src` has significant overengineering. Simple operations (draw card, tap member, add hearts) are represented through multiple layers of abstraction, resulting in ~15,000+ lines of complex code that could be reduced by 50-70%.

## Current Architecture

```
JSON (ability_frame_source.json)
  ↓ [build_cards.py]
Compiled JSON
  ↓ [AbilityManifest]
FrameProgram → AbilityFrame[]
  ↓ [Interpreter]
Handlers (35+ files)
  ↓
GameState
```

## Frame Semantics Question

**Do frames have semantics in them? YES.**

Frames already contain complete semantic information:
- `opcode`: What operation (DRAW, MOVE_MEMBER, BOOST_SCORE, etc.)
- `value`: Operation-specific value (count, amount, etc.)
- `attr`: 64-bit packed filter (target player, card type, group, color, etc.)
- `slot`: Packed slot word (source/dest zones, target slot)
- `is_cost`: Whether this is a cost step
- `params`: JSON with additional semantic data (raw_cond, raw_effect, per_card, etc.)

### Example Frame from ability_frame_source.json:
```json
{
  "op": "DRAW",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

This frame already tells you: "Draw 1 card to the context (hand)".

### The Problem: "Semantic Types"

The code then creates "semantic types" that re-package this same information:
- `SemanticDiscardSpec` (12 fields)
- `SemanticLookAndChooseSpec` (11 fields)
- `SemanticRecoveryBranchSpec`
- `SemanticCountZone`, `SemanticScaleSource`, `SemanticComparisonMode`

These are **unnecessary** - they're just unpacking the frame's existing semantics into Rust structs with named fields, then often re-packing them back.

**This is pure overengineering.** The frames already have the semantics; we don't need a separate "semantic" layer.

## Major Overengineering Issues

### 1. Filter System (filter.rs - 2092 lines)

**Problem**: 64-bit packed attribute with "raw attr juggling" - repeatedly merging/splitting structured and raw representations. The comment explicitly calls this a "known debt item."

Current bit layout:
```
Bits 0-1:   Target Player
Bits 2-3:   Card Type
Bits 5-11:  Group ID
Bits 17-23: Unit ID
Bits 25-29: Value Threshold
Bits 32-38: Color Mask
... (more bits)
Bits 56-63: Compatibility flags (passthrough bits)
```

The code constantly converts:
```rust
CardFilter → to_attr() → u64
u64 → from_raw() → CardFilter
```

**Should be**: Replace packed bits with named struct fields:
```rust
pub struct CardFilter {
    pub target_player: TargetPlayer,
    pub card_type: CardType,
    pub group: Option<u8>,
    pub unit: Option<u8>,
    pub color_mask: u8,
    pub cost_threshold: Option<u8>,
    pub cost_mode: CostMode,
    pub zone_mask: u8,
    // ... other fields as actual fields, not bits
    pub compatibility_flags: CompatibilityFlags, // explicit flags
}
```

### 2. Semantic Types Layer (models.rs)

**Problem**: Multiple semantic wrapper types that add unnecessary abstraction:
- `SemanticDiscardSpec` - 12 fields re-packing frame data
- `SemanticLookAndChooseSpec` - 11 fields re-packing frame data
- `SemanticRecoveryBranchSpec` - re-packing params
- `SemanticCountZone`, `SemanticScaleSource`, `SemanticComparisonMode`

These types are used in pattern matching and condition evaluation, but they're just re-expressing what's already in the frame.

**Should be**: Use the raw `AbilityFrame` directly. Remove the semantic type layer entirely. The frame already has all the information.

### 3. Handler Over-modularization (interpreter/handlers/ - 35+ files)

**Problem**: 35+ files for relatively simple operations. The README claims this is "domain organization" but it's over-granular:

```
state_score_hearts.rs (score/hearts dispatch)
state_score_bonus.rs (score boosting)
state_score_stats.rs (blades, hearts, transforms)
state_score_requirements.rs (heart requirements)
state_score_slots.rs (slot targeting)
state_score_transforms.rs (heart/blade transforms)

state_member.rs (member dispatch)
state_member_tap.rs (tapping, activation)
state_member_position.rs (movement, formation)
state_member_play.rs (playing members)
state_member_play_discard.rs (discard resolution)
state_member_play_discard_place.rs (placement)
state_member_play_discard_select.rs (selection)
state_member_play_hand.rs (play from hand)
state_member_play_resolve.rs (resolution)
state_member_activate.rs (activation)
state_member_formation.rs (formation)
state_member_move.rs (movement)
state_member_position.rs (position)
state_member_tap.rs (tapping - 18KB!)
```

And similar for energy, movement, flow, interaction.

**Should be**: Consolidate into ~5 files:
- `score.rs` - All score/hearts/blades operations (~500 lines)
- `member.rs` - All member operations (~800 lines)
- `energy.rs` - All energy operations (~400 lines)
- `zones.rs` - All deck/discard/movement operations (~600 lines)
- `interactions.rs` - All selection/interaction operations (~700 lines)

### 4. Ability Manifest (ability_manifest.rs - 698 lines)

**Problem**: Complex JSON parsing with multiple fallback paths, metadata lookups, frame normalization, summarization logic generating human-readable descriptions.

Functions like:
- `metadata_lookup()` - Looks up trigger/opcode names from metadata
- `opcode_name()` - Multiple fallback paths to find opcode name
- `normalize_frame()` - Normalizes frame structure
- `describe_frame()` - Generates human-readable descriptions
- `summarize_frames()` - Summarizes entire ability

The summarization generates strings like "May Draw 1 card(s)" - this is only used for debugging/manifests, not runtime.

**Should be**: Keep it simple - just load the JSON into structs. Remove the summarization/description generation unless it's actually needed for runtime. Move manifest generation to a separate tool.

### 5. Ability Patterns (ability_patterns.rs - 525 lines)

**Problem**: Very specific pattern matching functions that detect particular card ability patterns:
- `structured_targeted_live_heart_bonus_signature()` - Detects specific live heart bonus pattern
- `is_distinct_optional_mode_live_ability()` - Detects specific optional mode pattern
- `is_optional_live_start_discard_count_ability()` - Detects specific discard count pattern
- `pending_targeted_live_heart_bonus()` - Matches pending interaction to ability
- `pending_optional_mode_mask()` - Computes optional mode mask

These are hardcoded for specific card types rather than being generic.

**Should be**: Replace with a generic pattern matching system based on frame sequences. For example:
```rust
pub fn matches_pattern(ability: &Ability, pattern: &[OpcodePattern]) -> bool
```

Where `OpcodePattern` can specify:
- Opcode (or opcode class)
- Optional flags
- Value constraints
- Attr constraints

### 6. Interpreter Complexity (interpreter/)

**Problem**: 
- `instruction.rs` (32KB) - Complex frame parsing with multiple fallback paths
- `suspension.rs` (22KB) - State saving/restoration for interactions
- `logging.rs` (24KB) - Logging framework
- `costs.rs` (24KB) - Cost checking and payment

The frame parsing has special cases for:
- Multiple opcode name sources (opcode, op, opcode_name, kind)
- Multiple value sources (value, params.value)
- Multiple attr sources (attr, semantic.attr)
- Multiple slot sources (slot, semantic.slot)

**Should be**: Simplify the frame format so parsing is trivial. Use a consistent structure:
```rust
{
  "opcode": "DRAW",
  "value": 1,
  "attr": { "target_player": "SELF", "card_type": "MEMBER" },
  "slot": { "source_zone": "DECK", "dest_zone": "HAND" },
  "is_cost": false,
  "params": { }
}
```

No fallbacks, no multiple sources. One way to represent each piece of data.

### 7. Condition Derivation (models.rs)

**Problem**: `derive_conditions_from_frame_program()` scans frames for condition opcodes and converts them to `Condition` structs. This is done at load time.

But frames already contain the condition information via opcode ranges (CONDITION_START_1 to CONDITION_END_2) and params.

**Should be**: Don't derive conditions separately. Check conditions directly from frames when needed. The Condition struct is just re-packing frame data.

## Refactoring Plan

### Phase 1: Eliminate Semantic Types (Highest Impact)
1. Remove `SemanticDiscardSpec`, `SemanticLookAndChooseSpec`, `SemanticRecoveryBranchSpec`, etc.
2. Update all code that uses these types to use `AbilityFrame` directly
3. Remove condition derivation - check conditions from frames directly
4. **Expected reduction**: ~500 lines

### Phase 2: Simplify Filter System
1. Replace 64-bit packed `attr` with `CardFilter` struct
2. Remove `to_attr()` / `from_raw()` conversions
3. Update `AbilityFrame` to use `CardFilter` instead of `attr: u64`
4. **Expected reduction**: ~1000 lines

### Phase 3: Consolidate Handlers
1. Merge handler files by domain (score, member, energy, zones, interactions)
2. Remove the intermediate dispatch functions
3. Go direct from opcode to handler
4. **Expected reduction**: ~2000 lines

### Phase 4: Simplify Frame Format
1. Standardize JSON frame structure (no fallbacks)
2. Simplify frame parsing (no special cases)
3. Remove instruction.rs complexity
4. **Expected reduction**: ~1500 lines

### Phase 5: Remove Ability Manifest Complexity
1. Move manifest generation to separate tool
2. Keep only simple JSON loading in runtime
3. Remove summarization/description generation
4. **Expected reduction**: ~500 lines

### Phase 6: Generic Pattern Matching
1. Replace hardcoded pattern functions with generic pattern matcher
2. Define patterns as data, not code
3. **Expected reduction**: ~300 lines

## Total Expected Impact

**Lines of code reduction**: ~5,800 lines (from ~15,000 to ~9,200)
**Complexity reduction**: 50-70%
**Maintainability**: Much simpler data flow, easier to understand
**Performance**: Slightly faster (less conversion/packing)

## Key Insight

The fundamental issue is that the system has **too many layers of abstraction** for simple operations:

```
Current: JSON → Manifest → Semantic Types → Frames → Handlers → GameState
Simpler: JSON → Frames → Handlers → GameState
```

Frames already have all the semantic information needed. The "semantic types", "condition derivation", "manifest summarization", and complex parsing are all unnecessary layers that add complexity without adding value.

## Next Steps

1. Start with Phase 1 (eliminate semantic types) - highest impact, lowest risk
2. Test thoroughly after each phase
3. Keep the JSON frame format stable during refactoring
4. Update documentation as we go
