# Test Failure Analysis - 23 Remaining Failures

## Summary
- **Total Tests**: 521
- **Passed**: 497
- **Failed**: 23
- **Ignored**: 1

## Failing Tests by Category

### 1. Filter/Condition Tests (3 tests)

#### filter_audit_tests::tests::test_tapped_filter
**Issue**: Tapped filter condition not working correctly
**Likely Cause**: Filter matching logic for `is_tapped` flag
**Fix Needed**: Check `filter.is_tapped` handling in `filter.rs` matches function

#### opcode_tests::test_card_matches_filter_live_hearts
**Issue**: Heart filter matching for Live cards
**Likely Cause**: Live cards don't have hearts the same way members do
**Fix Needed**: Ensure heart filter logic handles Live cards correctly

#### opcode_tests::test_opcode_look_and_choose_filter_cost_ge
**Issue**: Look and choose with cost >= filter
**Likely Cause**: Cost comparison filter not working
**Fix Needed**: Check `is_cost_type` and value filter logic

### 2. Card 8844 Tests (2 tests)

#### qa::batch_card_specific::tests::test_card_8844_activate_draw_branch_requires_discard_tracking
#### qa::batch_card_specific::tests::test_card_8844_activate_recover_branch_uses_non_muse_discard
**Issue**: Card 8844 (Pl!-bp5-003-P) ability branches not working
**Likely Cause**: SelectMode or branch conditions not properly evaluated
**Fix Needed**: Check frame program for card 8844 - likely needs condition fix

### 3. Yell/Batch Tests (1 test)

#### qa::batch_card_specific::tests::test_q107_recheer_only_counts_current_yell_batch
**Issue**: Yell card batch counting
**Likely Cause**: Batch tracking or yell persistence issue
**Fix Needed**: Check yell card condition logic

### 4. Vienna Constant Tests (2 tests - duplicate)

#### qa::batch_card_specific::tests::test_q110_q127_vienna_constant_stacking
#### qa_verification_tests::tests::test_q110_q127_vienna_constant_stacking
**Issue**: Vienna constant ability stacking
**Likely Cause**: Score buff stacking logic
**Fix Needed**: Check O_BOOST_SCORE or similar opcode handling

### 5. Cost Selection Tests (2 tests - duplicate)

#### qa::batch_card_specific::tests::test_q183_cost_selection_isolation
#### qa_verification_tests::tests::test_q183_cost_selection_isolation
**Issue**: Cost selection not isolated between abilities
**Likely Cause**: Cost state leaking between ability resolutions
**Fix Needed**: Reset cost-related context between abilities

### 6. Niji Score Buff Tests (2 tests - duplicate)

#### qa::batch_card_specific::tests::test_q203_niji_score_buff
#### qa_verification_tests::tests::test_q203_niji_score_buff
**Issue**: Nijigasaki score buff not applying
**Likely Cause**: Group filter or score buff opcode
**Fix Needed**: Check group_id=2 (Niji) filter and O_BOOST_SCORE

### 7. Live Recovery Tests (2 tests)

#### qa::batch_card_specific::tests::test_q209_discarded_live_can_be_recovered_as_activation_target
#### qa::batch_card_specific::tests::test_q214_zero_score_live_recovery_costs_zero_energy
**Issue**: Live card recovery from discard
**Likely Cause**: O_RECOVER_LIVE or discard tracking
**Fix Needed**: Check recover live opcode and discard zone logic

### 8. Setsuna Zero Tests (2 tests - duplicate)

#### qa::batch_card_specific::tests::test_q230_setsuna_zero_equality
#### qa_verification_tests::tests::test_q230_setsuna_zero_equality
**Issue**: Setsuna zero cost/equality check
**Likely Cause**: Zero cost comparison logic
**Fix Needed**: Check value comparison for zero costs

### 9. Kinako Deck Cost Tests (2 tests - duplicate)

#### qa::batch_card_specific::tests::test_q234_kinako_deck_cost
#### qa_verification_tests::tests::test_q234_kinako_deck_cost
**Issue**: Kinako deck cost calculation
**Likely Cause**: Deck-based cost calculation
**Fix Needed**: Check cost calculation with deck state

### 10. Kinako Variant Tests (1 test)

#### qa::batch_card_specific::tests::test_q237_revealing_nonmatching_variant_does_not_recover_base_name
**Issue**: Card variant name matching
**Likely Cause**: Card name matching for variants
**Fix Needed**: Check name comparison logic for card variants

### 11. Baton Touch Tests (1 test)

#### qa_verification_tests::tests::test_id_717_baton_touch_untaps_energy
**Issue**: Baton touch not untapping energy
**Likely Cause**: O_BATON_TOUCH_MOD or energy untap logic
**Fix Needed**: Check baton touch handler for energy untap

### 12. Catchu Exhaustive Tests (1 test)

#### qa_verification_tests::tests::test_q96_q97_q103_catchu_exhaustive
**Issue**: CYaRon!/AZALEA/Guilty Kiss group handling
**Likely Cause**: Group filter for subunits
**Fix Needed**: Check group filter with subunit IDs

### 13. Sequential Play Tests (1 test)

#### qa_verification_tests::tests::test_rule_bp4_001_triggers_on_both_sequential_plays
**Issue**: Trigger not firing on sequential plays
**Likely Cause**: Trigger condition or sequential play tracking
**Fix Needed**: Check OnPlay trigger handling

### 14. Card 579 Heart Filter (1 test)

#### repro::card_579_verification::test_card_579_ability_1_heart_filter
**Issue**: Heart filter not matching with sufficient hearts
**Root Cause**: `compare_accumulated` flag not set in test filter
**Fix Status**: Already fixed in test - needs rebuild

## Root Cause Categories

### Filter/Condition Issues (8 tests)
- test_tapped_filter
- test_card_matches_filter_live_hearts
- test_opcode_look_and_choose_filter_cost_ge
- test_q203_niji_score_buff (×2)
- test_q230_setsuna_zero_equality (×2)
- test_q234_kinako_deck_cost (×2)
- test_q96_q97_q103_catchu_exhaustive
- test_card_579_ability_1_heart_filter (FIXED)

### Card-Specific Logic (5 tests)
- test_card_8844_activate_draw_branch_requires_discard_tracking
- test_card_8844_activate_recover_branch_uses_non_muse_discard
- test_q107_recheer_only_counts_current_yell_batch
- test_q110_q127_vienna_constant_stacking (×2)
- test_q237_revealing_nonmatching_variant_does_not_recover_base_name

### Cost/Payment Issues (5 tests)
- test_q183_cost_selection_isolation (×2)
- test_q209_discarded_live_can_be_recovered_as_activation_target
- test_q214_zero_score_live_recovery_costs_zero_energy
- test_id_717_baton_touch_untaps_energy

### Trigger/Timing Issues (2 tests)
- test_q209_discarded_live_can_be_recovered_as_activation_target
- test_rule_bp4_001_triggers_on_both_sequential_plays

## Priority Fix Order

### High Priority (Fix 8 tests)
1. **CardFilter matches logic** - Fixes test_tapped_filter, test_card_matches_filter_live_hearts
2. **Value comparison with compare_accumulated** - Fixes test_q203, test_q230, test_q234
3. **Cost filter handling** - Fixes test_opcode_look_and_choose_filter_cost_ge

### Medium Priority (Fix 7 tests)
4. **Card 8844 frame program** - Fix 2 tests
5. **Yell batch tracking** - Fix 1 test
6. **Live recovery opcode** - Fix 2 tests
7. **Baton touch energy untap** - Fix 1 test

### Lower Priority (Fix 8 tests)
8. **Vienna constant stacking** - Already likely working, test may need adjustment
9. **Cost selection isolation** - Context management fix
10. **Name variant matching** - String comparison fix
11. **Sequential play triggers** - Trigger system fix
12. **Catchu group handling** - Group filter enhancement

## Implementation Plan

### Phase 1: Core Filter Fixes (Est. +8 tests)
- [ ] Fix `is_tapped` filter matching in filter.rs
- [ ] Fix heart filter for Live cards
- [ ] Fix cost filter (is_cost_type + value_threshold)
- [ ] Fix compare_accumulated flag handling

### Phase 2: Opcode Fixes (Est. +7 tests)
- [ ] Fix O_RECOVER_LIVE discard zone logic
- [ ] Fix O_BATON_TOUCH_MOD energy untap
- [ ] Fix score buff stacking (O_BOOST_SCORE)

### Phase 3: Card-Specific Fixes (Est. +5 tests)
- [ ] Fix card 8844 frame program/conditions
- [ ] Fix yell batch tracking
- [ ] Fix name variant matching
- [ ] Fix sequential play triggers

### Phase 4: Context/State Fixes (Est. +3 tests)
- [ ] Fix cost selection isolation
- [ ] Fix Catchu group filter

## Files Likely Needing Changes

1. `src/core/logic/filter.rs` - Filter matching logic
2. `src/core/logic/interpreter/handlers/unified.rs` - Opcode handlers
3. `src/core/logic/interpreter/handlers/movement.rs` - Deck/discard operations
4. `src/core/logic/interpreter/handlers/state.rs` - State modifications
5. `src/core/logic/interpreter/mod.rs` - Context management
6. `src/core/logic/models.rs` - Frame/Ability handling
7. `src/core/logic/handlers.rs` - Game action handlers

## Expected Final Result
After all fixes: **520 passed, 0 failed, 1 ignored**
