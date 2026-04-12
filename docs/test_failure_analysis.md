# Cargo Test Failure Analysis

## Overall Results
- **Total Tests**: 700
- **Passed**: 646
- **Failed**: 54
- **Ignored**: 0
- **Execution Time**: 3.00s

## Failure Patterns by Module

### 1. core::logic::models::tests (6 failures)
**File**: `src/core/logic/models.rs`
- `discard_cards_can_return_to_the_top_of_the_deck`
- `move_member_frame_preserves_structured_params`
- `muse_live_recovery_puts_the_discard_live_card_on_top_of_deck_before_draw`
- `structured_count_stage_frame_preserves_not_self_filter_bits`
- `structured_reduce_cost_frame_preserves_card10_style_filter_bits`
- `total_cost_budget_helper_accepts_modern_compare_accumulated`

**Pattern**: Structured frame preservation and card movement logic issues

### 2. repro (8 failures)
**Files**:
- `src/repro/repro_bp3_002_p.rs` - `test_repro_bp3_002_p_tap_targeting`
- `src/repro/repro_bp4_002_p.rs` - `test_repro_bp4_002_p_wait_flow`
- `src/repro/repro_card_420.rs` - `test_repro_card_420_cost_sum_limit`, `test_repro_card_420_multi_pick_from_discard`, `test_repro_card_420_second_pick_can_be_skipped`
- `src/repro/repro_hazuki_500.rs` - `test_hazuki_500_looks_at_five_cards_after_optional_discard`
- `src/repro/repro_task.rs` - `test_cost_13_passive_repro`
- `src/repro/repro_softlock_tests.rs` - `test_optional_interaction_actions_real_card`
- `src/repro/special_mechanics_tests.rs` - `test_meta_rule_yell_mulligan`

**Pattern**: Card-specific reproduction tests failing on targeting, flow, and cost mechanics

### 3. test_suite::ability_frame_audit_tests (1 failure)
**File**: `src/test_suite/ability_frame_audit_tests.rs`
- `test_ability_55_kurosawa_ruby_missing_saintsnow_filter`

**Pattern**: Ability frame filter validation

### 4. test_suite::ability_tests (3 failures)
**File**: `src/test_suite/ability_tests.rs`
- `test_ability_64_kurosawa_dia_flavor_choice`
- `test_ability_64_option1_aqours_blade`
- `test_ability_64_option2_saintsnow_position_change`

**Pattern**: Multi-option ability resolution (card 64)

### 5. test_suite::card_interaction_tests (2 failures)
**File**: `src/test_suite/card_interaction_tests.rs`
- `test_card_163_optional_live_start_prompt_uses_yes_no_actions_only`
- `test_card_707_wait_execution_honors_cost_filter`

**Pattern**: Card interaction flow and optional prompts

### 6. test_suite::debug_q203 (1 failure)
**File**: `src/test_suite/debug_q203.rs`
- `debug_q203_trace`

**Pattern**: Q203 card tracing/debug test

### 7. test_suite::meta_rule_card_tests (1 failure)
**File**: `src/test_suite/meta_rule_card_tests.rs`
- `test_meta_rule_pl_sp_bp1_024_l_no_draw_without_both`

**Pattern**: Meta rule card draw conditions

### 8. test_suite::qa::batch_card_specific (26 failures)
**File**: `src/test_suite/qa/batch_card_specific.rs`
- Card-specific tests for cards: 47, 558, 628, 777, 801, 854, 861, 8844, live_260
- Q-series tests: q107, q183, q201, q202, q203, q214, q236

**Pattern**: Card ability resolution, cost selection, nested triggers, score bonuses
**Common Issues**:
- State machine not suspending at expected points (Main vs Response)
- Cost selection isolation failures
- Nested trigger resolution (Q201, Q202)
- Score buff calculations (Q203)
- Live-start energy payment flows

### 9. test_suite::qa_verification_tests (7 failures)
**File**: `src/test_suite/qa_verification_tests.rs`
- `test_cost_13_blade_aura_requires_structured_stage_gate`
- `test_hand_only_structured_cost_reducers_use_authored_conditions`
- `test_position_change_text_frames_include_explicit_destination_metadata`
- `test_q160_q161_q162_play_count_trigger`
- `test_q183_cost_selection_isolation`
- `test_q201_nested_on_play`
- `test_q202_nested_on_play_optional`
- `test_q203_niji_score_buff_reaches_two_with_energy_and_member_activation`
- `test_q203_niji_score_buff_requires_energy_activation_before_member_activation`
- `test_q4794_same_group_discard_requires_matching_partner`

**Pattern**: Verification tests for cost gates, structured params, nested triggers, and score buffs

## Common Error Patterns

### 1. State Machine Suspension Failures
Multiple tests expect the game state to suspend (transition from Main to Response or other states) but it remains in Main:
- Q201 nested on play
- Q202 nested on play optional
- Various card-specific optional prompts

### 2. Cost Selection Issues
Tests expecting cost payment to trigger specific side effects are failing:
- Q183 cost selection isolation
- Card 801 cost payment triggering search
- Cost-13 blade aura conditions

### 3. Score Buff Calculation
Q203 Niji score buff tests failing on expected bonus values:
- Member activation alone: expects 2, gets 1
- Energy + member activation: expects 3, gets 1

### 4. Structured Frame Preservation
Tests for structured parameters (filters, costs) not being preserved correctly during frame operations

### 5. Nested Trigger Resolution
Tests for cards with nested triggers (Q201, Q202) not suspending at expected points in the trigger chain

## Key Files Requiring Attention

1. **src/core/logic/models.rs** - Structured frame logic
2. **src/test_suite/qa/batch_card_specific.rs** - Card-specific QA tests (26 failures)
3. **src/test_suite/qa_verification_tests.rs** - Verification tests (7 failures)
4. **src/repro/** - Multiple repro test files (8 failures total)
5. **src/test_suite/ability_tests.rs** - Multi-option abilities
