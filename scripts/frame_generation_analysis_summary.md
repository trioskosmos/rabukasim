# Frame Generation Analysis Summary

## Objective
Examine failing tests to identify frame generation bugs (as opposed to semantic extraction bugs or Rust interpreter bugs).

## Methodology
For each failing test:
1. Read the test code to understand expected behavior
2. Read the card data (original text, semantic data, compiled frames)
3. Compare generated frames against ability text
4. Identify root cause: semantic extraction bug, frame generation bug, or Rust interpreter bug

## Findings

### Frame Generation Bugs Fixed

#### Card 47 (PL!-bp5-005-AR)
- **Issue**: SELECT_MODE with choose_heart + select_member had incorrect heart_type mapping and wrong JUMP routing
- **Fix**: 
  - Fixed heart_type mapping fallback to use heart index instead of 0
  - Fixed JUMP routing for SELECT_MODE branches to jump to correct branch start indices
- **Result**: Reduced failures from 95 to 94

#### Card 654 (PL!SP-bp5-009-AR)
- **Issue**: place_card action for energy cards was generating incorrect opcode (MOVE_TO_DISCARD instead of DRAW_ENERGY) and wrong zone mapping
- **Fix**: 
  - Inferred source/destination for energy_card when not specified
  - Added specific opcode case for drawing energy card from energy_deck to energy_zone
- **Result**: Frame generation corrected, but test still fails (potential Rust interpreter issue with DRAW_ENERGY execution)

### Semantic Extraction Bugs Identified (Not Frame Generation)

The following cards were examined and found to have semantic extraction bugs - the frame generation is correctly converting the (incomplete/wrong) semantic data:

#### Card 709
- **Issue**: Missing unique costs condition in semantic data
- **Root Cause**: Semantic extraction tool not parsing "コストが異なる" (different costs) pattern

#### Card 10
- **Issue**: Cost reduction PER_CARD multiplier not applied by Rust interpreter
- **Root Cause**: Rust interpreter bug (not frame generation)

#### Card 777
- **Issue**: Completely wrong frames - missing LIVE_START trigger and effect details
- **Root Cause**: Semantic extraction tool not parsing complex ability correctly

#### Card 697
- **Issue**: Completely wrong frames - missing complex actions (cost copy, conditional heart gain)
- **Root Cause**: Semantic extraction tool not parsing complex ability correctly

#### Card 693
- **Issue**: Completely wrong frames - missing mill action
- **Root Cause**: Semantic extraction tool not parsing mill action correctly

#### Card 801
- **Issue**: Missing cost constraint in semantic data for select_from_looked_at_cards action
- **Root Cause**: Semantic extraction tool not parsing cost constraint correctly

#### Card 558
- **Issue**: LOOK_AND_CHOOSE missing heart total and group filters
- **Root Cause**: Semantic extraction tool not parsing heart total and group filters

#### Card 656
- **Issue**: Missing discard frames despite ability text describing discard action
- **Root Cause**: Semantic extraction tool not parsing discard-to-3 action

#### Card 628 (PL!SP-bp5-009-AR)
- **Issue**: Completely wrong frames - only SET_TAPPED and RETURN
- **Root Cause**: Semantic extraction tool not parsing complex ability with optional discard, conditional blade gain, and repeatable action

#### Card 854 (PL!SP-bp5-001-AR)
- **Issue**: DRAW frame missing source_zone (semantic data missing "source" field)
- **Root Cause**: Semantic extraction tool not extracting source for draw_cards action

#### Card 755 (PL!N-bp5-005-AR)
- **Issue**: Completely wrong frames - missing baton condition, cost filtering, blade heart filtering, conditional draw
- **Root Cause**: Semantic extraction tool not parsing complex ability with baton touch condition and cost-based conditions

#### Card 761 (PL!N-bp5-011-AR)
- **Issue**: Wrong frames - top-level condition should be per-branch conditions, missing second branch
- **Root Cause**: Semantic extraction tool not correctly structuring choice abilities with per-branch conditions

## Conclusion

**Summary**: Out of all cards examined, only Card 47 had a successful frame generation fix that reduced test failures (95 → 94). Card 654 had a frame generation fix applied but the test still fails, suggesting a potential Rust interpreter issue.

**Key Finding**: The vast majority of failing tests are due to semantic extraction bugs, not frame generation bugs. The semantic extraction tool needs to be improved to correctly parse:
- Complex ability structures with multiple conditions and actions
- Cost-based conditions and filters
- Blade heart filtering
- Choice abilities with per-branch conditions
- Optional and repeatable actions
- Baton touch conditions
- Source/destination information for draw/discard actions

## Additional Frame Generation Improvements Made

While examining Card 854, the following frame generation improvements were made (though they didn't fix the test due to semantic extraction issues):
- Added cost_limit filtering to member_to_wait action when target is "opponent"
- Fixed SELECT_MODE JUMP routing for choice actions to correctly calculate branch start indices
- Added source_zone to DRAW frame when source is specified in semantic data

These improvements are correct and will help with future cards that have proper semantic data.
