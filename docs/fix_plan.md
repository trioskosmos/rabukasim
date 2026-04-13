# Fix Plan for extract_abilities_to_template.py

## Problem
The script has two `match_dsl_patterns` function definitions, causing a `NameError: name 'dsl_patterns' is not defined` at line 1925.

## Current State
1. **First function** (lines 253-1780): Incomplete
   - Has `dsl_patterns` defined at line 279
   - Contains the full clause-level DSL patterns list
   - Missing function body (no actual matching logic)

2. **Second function** (lines 1861-): Has function body but missing `dsl_patterns`
   - Has `ability_level_patterns = ABILITY_LEVEL_PATTERNS` at line 1863
   - Has complete function body with matching logic
   - Missing `dsl_patterns` definition (causes the error at line 1925)

3. **Module-level patterns** (lines 1783-1858): `ABILITY_LEVEL_PATTERNS`
   - Successfully moved to module level
   - This is correct

## Fix Required
Delete the incomplete first function (lines 253-1780) and add `dsl_patterns` definition to the second function.

### Steps:
1. Delete lines 253-1780 (the incomplete first `match_dsl_patterns` function including its `dsl_patterns` list)
2. In the second function (starting at line 1861), add `dsl_patterns` definition right after line 1863
3. The `dsl_patterns` list needs to be copied from the deleted section (lines 279-1780)

### Alternative Simpler Fix:
Instead of copying the entire 1500-line `dsl_patterns` list, we could:
1. Move `dsl_patterns` to module level (like `ABILITY_LEVEL_PATTERNS`)
2. Add `dsl_patterns = DSL_PATTERNS` inside the function

This would be cleaner and more maintainable.

## Recommended Approach
Move `dsl_patterns` to module level as `DSL_PATTERNS`, then reference it in the function. This mirrors the `ABILITY_LEVEL_PATTERNS` pattern and is more maintainable.
