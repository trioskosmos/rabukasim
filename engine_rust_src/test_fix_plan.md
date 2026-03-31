# Test Failure Analysis and Fix Plan

## Failing Tests Summary

Based on test output, there are **23 failing tests** across these categories:

### Category 1: Vienna Constant Stacking (2 tests)
- `qa::batch_card_specific::tests::test_q110_q127_vienna_constant_stacking`
- `qa_verification_tests::tests::test_q110_q127_vienna_constant_stacking`

**Issue**: Vienna constant stacking not properly applying bonus based on activated group tracking.

### Category 2: look_and_choose (3 tests)
- `deck_refresh_tests::test_refresh_on_look_and_choose`
- `opcode_tests::test_look_and_choose_source_zone_fix`
- `opcode_tests::test_opcode_look_and_choose_filter_cost_ge`

**Issue**: Source zone handling or deck refresh during look_and_choose operations.

### Category 3: card_8844 Discard Tracking (2 tests)
- `qa::batch_card_specific::tests::test_card_8844_activate_draw_branch_requires_discard_tracking`
- `qa::batch_card_specific::tests::test_card_8844_activate_recover_branch_uses_non_muse_discard`

**Issue**: Discard tracking for specific card 8844 abilities.

### Category 4: Cost Selection & Baton (4 tests)
- `qa::batch_card_specific::tests::test_q183_cost_selection_isolation`
- `qa::batch_card_specific::tests::test_q206_baton_touch_cost_reduction`
- `qa_verification_tests::tests::test_q183_cost_selection_isolation`
- `qa_verification_tests::tests::test_q206_baton_touch_cost_reduction`

**Issue**: Baton cost math and cost selection during responses.

### Category 5: Heart Filter (1 test)
- `repro::card_579_verification::test_card_579_ability_1_heart_filter`

**Issue**: Card 579 heart filter condition not matching properly.

### Category 6: Card-Specific Issues (11 tests)
- `qa::batch_card_specific::tests::test_q107_recheer_only_counts_current_yell_batch`
- `qa::batch_card_specific::tests::test_q203_niji_score_buff`
- `qa::batch_card_specific::tests::test_q209_discarded_live_can_be_recovered_as_activation_target`
- `qa::batch_card_specific::tests::test_q214_zero_score_live_recovery_costs_zero_energy`
- `qa::batch_card_specific::tests::test_q230_setsuna_zero_equality`
- `qa::batch_card_specific::tests::test_q234_kinako_deck_cost`
- `qa::batch_card_specific::tests::test_q237_revealing_nonmatching_variant_does_not_recover_base_name`
- `qa_verification_tests::tests::test_q203_niji_score_buff`
- `qa_verification_tests::tests::test_q230_setsuna_zero_equality`
- `qa_verification_tests::tests::test_q234_kinako_deck_cost`
- `qa_verification_tests::tests::test_rule_bp4_001_triggers_on_both_sequential_plays`

## Root Cause Analysis

1. **Unified helper function change**: The `current_effect()` function consolidation in `flow_helpers.rs` may have changed behavior subtly.

2. **AbilityFrameComponents changes**: The `heart_counts()`, `heart_requirements()`, `look_choose()` methods now use decoder functions which may behave differently than manual bit extraction.

3. **Dispatch simplification**: The dispatch function now uses simplified handlers which may not preserve all original behavior.

## Fix Strategy

### Phase 1: Verify current_effect() behavior
- Check that the unified `current_effect()` function matches original behavior
- May need to add back frame_idx-based lookup for certain handlers

### Phase 2: Fix heart count extraction
- Verify `DecodedHeartCounts::decode()` produces same results as manual extraction
- If not, fix the decoder or revert to manual extraction

### Phase 3: Restore look_and_choose source zone
- Check if source zone handling in look_and_choose was broken by recent changes

### Phase 4: Test-specific fixes
- Address each category of failures systematically

## Files to Modify

1. `src/core/logic/interpreter/handlers/flow_helpers.rs` - May need to restore frame_idx lookup
2. `src/core/logic/models.rs` - May need to fix decoder usage
3. `src/core/logic/interpreter/handlers/interaction_look_choose.rs` - Fix source zone handling
4. Various handler files for specific fixes
