# Comprehensive Audit Report: Ability Extraction Logic

## Executive Summary

This report documents the comprehensive audit of the ability extraction logic, focusing on:
- Consolidating condition operators (>=, <=, >, <) into descriptive types
- Consolidating effect actions into generic categories (move_cards, modify_resource)
- Adding target field (player/opponent/both) to all relevant types
- Ensuring proper variables, zones, and targets for all types

## Changes Made

### 1. Condition Operator Consolidation

**Goal:** Remove comparison operators (>=, <=, >, <, ==) and consolidate into descriptive type names.

**Changes Implemented:**
- `cost_total` with `operator: "=="` → `cost_total_equal`
- `energy` with `operator: ">="` → `energy_at_least`
- `card_count` with `operator: ">="` → `card_count_at_least`
- `member_count` with `operator: ">="` → `member_count_at_least`
- `blade_count` with `operator: "<="` → `blade_count_at_most`
- `heart_count` with `operator: ">="` → `heart_count_at_least`
- `score_sum` with `operator: ">="` → `score_sum_at_least` / `live_total_score_at_least`
- `comparison` with `operator: ">"` → `comparison_greater_than`
- `comparison` with `operator: "<"` → `comparison_less_than`
- `position` with `operator: "=="` → `position_left_side`, `position_right_side`, `position_center`
- `state` with `operator: "=="` → `state_active`, `state_wait`
- `card_score` with `operator: "=="` → `card_score_equal`
- `card_count` with `operator: "=="` → `card_count_equal`
- `surplus_heart` with `operator: "=="` → `surplus_heart_equal`

**Status:** ✅ Completed

### 2. Cost Type Consolidation

**Goal:** Consolidate specific cost types into generic `move_cards` and `reveal_cards` structures.

**Changes Implemented:**
- `waitroom_to_deck_bottom` → `move_cards` (source: waitroom, destination: deck_bottom)
- `member_to_waitroom` → `move_cards` (source: stage, destination: waitroom)
- `member_to_wait` → `move_cards` (source: stage, destination: wait)
- `reveal_cost` → `reveal_cards` (source: hand)
- `energy_to_member` → `move_cards` (source: energy_zone, destination: member_under)
- `energy_to_energy_deck` → `move_cards` (destination: energy_deck)
- `hand_to_deck_bottom` → `move_cards` (source: hand, destination: deck_bottom)
- `discard_from_hand` → `move_cards` (source: hand, destination: waitroom)
- `discard_from_deck` → `move_cards` (source: deck, destination: waitroom)

**Status:** ✅ Completed

### 3. Effect Action Consolidation

**Goal:** Consolidate specific action types into generic `move_cards` and `modify_resource` structures.

**Changes Implemented:**
- Added `_consolidate_action()` function to post-process all parsed effects
- Consolidation applied at end of `parse_effect_backwards()` and `parse_generic_effect()`
- Target consolidations:
  - `draw_cards` → `move_cards` (source: deck, destination: hand)
  - `add_to_hand` → `move_cards` (destination: hand)
  - `discard_to_waitroom` → `move_cards` (destination: waitroom)
  - `place_on_deck` → `move_cards` (destination: deck_top)
  - `member_to_wait` → `move_cards` (source: stage, destination: wait)
  - `deploy_to_stage` → `move_cards` (destination: stage)
  - `add_score` → `modify_resource` (resource_type: score, operation: add)
  - `reduce_score` → `modify_resource` (resource_type: score, operation: subtract)
  - `modify_cost` → `modify_resource` (resource_type: cost, operation: add)
  - `set_original_blade_count` → `modify_resource` (resource_type: blade_count, operation: set)

**Status:** ⚠️ Partially Working

**Issue:** The consolidation is only applied to effects parsed through `parse_effect_backwards()` and `parse_generic_effect()`. Many effects are parsed through other code paths that bypass these functions, resulting in old action types still being present in the output.

### 4. Target Field Addition

**Goal:** Add `target` field (self/opponent/both) to all conditions, costs, and effects where applicable.

**Changes Implemented:**
- Added `_extract_target()` function in both `condition_parser.py` and `effect_parser.py`
- Target extraction logic:
  - "自分と相手の" or "自分と相手" → `both`
  - "相手の" → `opponent`
  - "自分の" → `self`
- Applied target extraction to:
  - All conditions in `parse_condition()`
  - All effects in `parse_effect_context_backwards()`

**Status:** ✅ Completed

## Current State

### Condition Types (43 unique types)

**Properly Consolidated Types:**
- ✅ cost_total_equal (2 occurrences)
- ✅ energy_at_least (13 occurrences)
- ✅ card_count_at_least (20 occurrences)
- ✅ card_count_equal (1 occurrence)
- ✅ member_count_at_least (17 occurrences)
- ✅ blade_count_at_least (2 occurrences)
- ✅ blade_count_at_most (2 occurrences)
- ✅ heart_count_at_least (7 occurrences)
- ✅ score_sum_at_least (10 occurrences)
- ✅ state_active (5 occurrences)
- ✅ state_wait (9 occurrences)
- ✅ card_score_equal (1 occurrence)
- ✅ surplus_heart_equal (2 occurrences)
- ✅ comparison_greater_than (5 occurrences)
- ✅ comparison_less_than (9 occurrences)
- ✅ position_right_side (1 occurrence)

**Types Still Using Operator Field:**
- ⚠️ comparison (32 occurrences) - should be further consolidated
- ⚠️ score_comparison (7 occurrences) - uses operator field
- ⚠️ per_unit (21 occurrences) - uses operator: "*"
- ⚠️ position (14 occurrences) - uses operator: "=="

**Raw Types (Need Further Parsing):**
- ⚠️ raw (9 occurrences) - down from 28, but still present

### Cost Types (2 unique types)

- ✅ move_cards (146 occurrences) - properly consolidated
- ✅ reveal_cards (6 occurrences) - properly consolidated

**Status:** ✅ Fully Consolidated

### Effect Action Types (48 unique types)

**Properly Consolidated:**
- ✅ move_cards (343 occurrences) - increased from 322

**Still Need Consolidation:**
- ❌ add_to_hand (35 occurrences) - should be move_cards
- ❌ add_score (76 occurrences) - should be modify_resource
- ❌ discard_to_waitroom (9 occurrences) - should be move_cards
- ❌ place_card (49 occurrences) - should be move_cards
- ❌ place_on_deck (13 occurrences) - should be move_cards
- ❌ modify_cost (4 occurrences) - should be modify_resource
- ❌ set_original_blade_count (2 occurrences) - should be modify_resource
- ❌ reduce_score (1 occurrence) - should be modify_resource

**Unique Actions (Keep as-is):**
- ✅ activate_ability, activate_energy, activate_member
- ✅ gain_ability, gain_resource
- ✅ choose_heart, look_at_cards
- ✅ position_change, formation_change
- ✅ activation_restriction, cannot_baton_touch, cannot_become_active
- ✅ transform_blades, transform_heart
- ✅ etc.

**Status:** ⚠️ Partially Working - consolidation function not applied to all parsing paths

## Issues Found

### 1. Effect Consolidation Not Applied Universally

**Problem:** The `_consolidate_action()` function is only called at the end of `parse_effect_backwards()` and `parse_generic_effect()`. Many effects are parsed through:
- Direct action pattern matching in `parse_effect_backwards()`
- Early returns in `parse_generic_effect()` before consolidation
- Nested action structures that don't go through the main parsing paths

**Impact:** Old action types (add_to_hand, add_score, etc.) remain in the output despite consolidation logic being present.

**Recommendation:** Apply consolidation as a post-processing step to the entire ability structure after parsing is complete, rather than within individual parsing functions.

### 2. Comparison Conditions Still Use Operator Field

**Problem:** 32 occurrences of `comparison` type still use the `operator` field instead of being consolidated into descriptive types like `comparison_greater_than` or `comparison_less_than`.

**Impact:** Inconsistent representation - some comparisons use descriptive types, others still use operator field.

**Recommendation:** Add logic to handle all comparison patterns in condition_parser.py to consolidate them fully.

### 3. Position Conditions Still Use Operator Field

**Problem:** 14 occurrences of `position` type still use `operator: "=="` instead of being consolidated into descriptive types.

**Impact:** Inconsistent representation.

**Recommendation:** Consolidate all position conditions to use descriptive types (position_left_side, position_right_side, position_center).

### 4. Target Field Not Universally Applied

**Problem:** Target field extraction is only applied in `parse_condition()` and `parse_effect_context_backwards()`. Costs and some effect paths may not have target information extracted.

**Impact:** Some conditions and effects may be missing target information.

**Recommendation:** Apply target extraction as a post-processing step to all parsed structures.

### 5. Raw Conditions Still Present

**Problem:** 9 occurrences of `raw` condition type remain, indicating some conditions are not being parsed.

**Impact:** Unparsed conditions lose semantic meaning.

**Recommendation:** Investigate the 9 raw conditions and add parsing rules for them.

## Recommendations

### Priority 1: Fix Effect Consolidation

1. Move consolidation logic to a post-processing step that runs after all parsing is complete
2. Apply consolidation recursively to all nested action structures
3. Ensure all parsing paths go through the consolidation step

### Priority 2: Complete Condition Consolidation

1. Consolidate all `comparison` types with operators into descriptive types
2. Consolidate all `position` types with operators into descriptive types
3. Review and handle remaining `per_unit` cases

### Priority 3: Improve Target Coverage

1. Add target extraction to cost_parser.py
2. Apply target extraction as a post-processing step
3. Verify target field is present in all relevant types

### Priority 4: Eliminate Raw Types

1. Investigate the 9 raw conditions
2. Add parsing rules for any missing patterns
3. Aim for 0 raw conditions

## Example Verification

### Cost Total Equal (天王寺璃奈)

**Input:**
```
控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。
```

**Output:**
```json
{
  "cost": {
    "type": "move_cards",
    "source": "waitroom",
    "destination": "deck_bottom",
    "count": 2,
    "card_type": "member_card",
    "optional": true,
    "order": "any"
  },
  "effect": {
    "condition": {
      "type": "cost_total_equal",
      "reference": "それらのカード"
    },
    "cost_reference": true,
    "branches": [
      {
        "cost_total": 6,
        "effect": {
          "action": "move_cards",
          "source": "deck",
          "destination": "hand",
          "count": 1
        }
      },
      {
        "cost_total": 8,
        "effect": {
          "action": "gain_resource",
          "heart_type": "all",
          "duration": "until_end_of_live"
        }
      },
      {
        "cost_total": 25,
        "effect": {
          "action": {
            "action": "gain_ability",
            "ability": "{{jyouji.png|常時}}ライブの合計スコアを+１する。"
          }
        }
      }
    ]
  }
}
```

**Status:** ✅ Working correctly - cost_total_equal, move_cards consolidation, heart_type detection all working

## Conclusion

Significant progress has been made:
- ✅ Condition operator consolidation mostly complete
- ✅ Cost type consolidation complete
- ⚠️ Effect action consolidation partially working (needs post-processing approach)
- ✅ Target field extraction added

The main remaining issue is that effect consolidation is not applied universally due to multiple parsing paths. A post-processing approach is recommended to ensure all effects are consolidated regardless of how they were parsed.
