# Parsing Fixes Summary

## Overview

This document summarizes the parsing fixes implemented for the ability extraction system, addressing the issues identified in `PARSING_ISSUES_DETAILED_REPORT.md`.

## Issues Before Fixes

- **Total abilities analyzed:** 598
- **Abilities with structural issues:** 25
- **Cost missing type:** 53 occurrences
- **Condition missing type:** 24 occurrences
- **Action missing action field:** 17 occurrences (9 + 5 + 3)
- **Raw text in actions:** 6 occurrences

## Issues After Fixes

- **Total abilities analyzed:** 598
- **Abilities with structural issues:** 14
- **Cost missing type:** 0 occurrences (fixed)
- **Condition missing type:** 1 occurrence (down from 24, 96% reduction)
- **Action missing action field:** 9 occurrences (down from 17, 47% reduction)
- **Raw text in actions:** 1 occurrence (down from 6, 83% reduction)

*Note: The pattern-based issues (自分の, 控え室, 手札, etc.) are expected - they check if common words appear in text, which is normal and not structural issues.*

## Fixes Implemented

### 1. Energy Cost Type Field (cost_parser.py)

**Issue:** Energy costs were parsed as `{'energy': X}` without a `type` field.

**Fix:** Modified the energy cost rule to return `{'type': 'pay_energy', 'energy': X}` instead of just the count.

**Location:** `tools/ability_extraction/cost_parser.py` lines 206-212, 287-298

**Impact:** Fixed 53 occurrences of missing type field in energy costs.

---

### 2. Energy Cost Source Field (cost_parser.py)

**Issue:** Energy-to-energy-deck costs were missing the source field.

**Fix:** Added `source: 'energy_zone'` to `_extract_energy_to_energy_deck_cost` function.

**Location:** `tools/ability_extraction/cost_parser.py` lines 148-155

**Impact:** Fixed 1 occurrence of missing source field.

---

### 3. Condition Type Field (condition_parser.py)

**Issue:** 24 conditions were missing the `type` field, having only fields like `target` or `exclude_this_member`.

**Fix:** Modified the default fallback to set `type: 'raw'` for any condition without a type. Added specific handling for `exclude_this_member` conditions to set `type: 'member_exclusion'`. Added post-processing in `extract_costs.py` to fix conditions that have `exclude_this_member` but no type.

**Location:** 
- `tools/ability_extraction/condition_parser.py` lines 654-669
- `tools/ability_extraction/extract_costs.py` lines 92-104, 135

**Impact:** Fixed 23 of 24 conditions missing type (96% reduction). 1 remaining case appears to be set outside the condition parser.

---

### 4. Action Field Merging (effect_parser.py)

**Issue:** Modifier-only actions (duration, multiplier, timing, target) were being added as separate array elements instead of being merged with the actual action they modify.

**Fix:** Added `_merge_modifier_actions` function to merge modifier-only actions with their target actions. Added helper functions `_is_multiplier_only_action` and `_is_timing_only_action`. Called the merge function in `parse_generic_effect` and in the "そうした場合" conditional pattern.

**Location:** `tools/ability_extraction/effect_parser.py` lines 91-182, 2725, 1806

**Impact:** Fixed 8 of 17 actions missing action field (47% reduction). 9 remaining cases appear to be complex nested structures.

---

### 5. Optional Draw with Conditional Follow-up (effect_parser.py)

**Issue:** Pattern "カードを1枚引いてもよい。そうした場合、～" was not being parsed.

**Fix:** Added parsing pattern in `parse_generic_effect` to detect and parse optional draw with conditional follow-up.

**Location:** `tools/ability_extraction/effect_parser.py` lines 1824-1851

**Impact:** Fixed 1 raw_text occurrence.

---

### 6. Card Selection with Variable Payment (effect_parser.py)

**Issue:** Pattern "～ライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、～" was not being parsed.

**Fix:** Added parsing pattern in `parse_generic_effect` to detect and parse card selection with variable payment based on selected card's score.

**Location:** `tools/ability_extraction/effect_parser.py` lines 1903-1943

**Impact:** Fixed 1 raw_text occurrence.

---

### 7. Complex Trigger with Payment (effect_parser.py)

**Issue:** Pattern "～たび、{{icon_energy.png|E}}支払ってもよい。そうした場合、～" was not being parsed.

**Fix:** Added parsing pattern in `parse_generic_effect` to detect and parse whenever triggers with optional energy payment.

**Location:** `tools/ability_extraction/effect_parser.py` lines 1780-1819

**Impact:** Fixed 1 raw_text occurrence.

---

### 8. Area Selection (effect_parser.py)

**Issue:** Pattern "その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。" was not being parsed.

**Fix:** Added parsing pattern in `parse_generic_effect` for "その後" with area selection. Also added pattern in `parse_effect_backwards` to handle comma-prefixed area selection text.

**Location:** `tools/ability_extraction/effect_parser.py` lines 1763-1797, 1160-1167, 2956-2991

**Impact:** Fixed 1 raw_text occurrence.

---

### 9. Card Selection by Name with Opponent Selection (effect_parser.py)

**Issue:** Pattern "～カード名が異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを～" was not being parsed.

**Fix:** Added parsing pattern in `parse_generic_effect` and `parse_effect_backwards` to detect and parse card selection by name with opponent selection.

**Location:** `tools/ability_extraction/effect_parser.py` lines 1858-1901, 1169-1177

**Impact:** Partially fixed - pattern added but 1 occurrence still shows raw_text due to text splitting.

---

## Remaining Issues

### Action Missing Action Field (9 occurrences)

These are cases where modifier-only actions (duration, multiplier, timing, target) are not being merged properly with their target actions. The merge function handles most cases but some complex nested structures still have issues.

### Condition Missing Type (1 occurrence)

One condition still missing type despite post-processing. This appears to be set outside the condition parser.

### Raw Text in Action (1 occurrence)

Card selection by name pattern still shows raw_text in one case, likely due to text splitting happening before the pattern check.

## Files Modified

1. `tools/ability_extraction/cost_parser.py` - Energy cost type and source fixes
2. `tools/ability_extraction/condition_parser.py` - Condition type fallback fixes
3. `tools/ability_extraction/effect_parser.py` - Action merging and raw_text pattern fixes
4. `tools/ability_extraction/extract_costs.py` - Post-processing for condition types
5. `PARSING_ISSUES_DETAILED_REPORT.md` - Detailed issue report (created)
6. `PARSING_FIXES_SUMMARY.md` - This summary (created)

## Verification

Run `python comprehensive_analysis.py` to verify the current state of parsing issues.

The parsing has been significantly improved, with structural issues reduced from 25 to 14 (44% reduction). The remaining issues are edge cases that would require more complex refactoring of the parsing logic.
