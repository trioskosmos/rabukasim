# Cargo Test Failure Analysis - Root Cause Analysis

## Overall Results
- **Total Tests**: 700
- **Passed**: 646
- **Failed**: 54
- **Execution Time**: 3.00s

## Root Cause Analysis from Debug Logs

### Pattern 1: Phase Transition Failures (State Machine Bug)

**Debug Evidence:**
```
[SUSP_DBG] choice_type=SelectStage actions=[] final_actions=[600, 601, 602] has_only_pass=false phase=Main cp=0
```

**Analysis:** The suspension debug logs show that when optional costs and nested triggers should suspend in the `Response` phase, the system is remaining in `Main` phase. This is a fundamental state machine bug.

**Affected Tests:**
- `test_q201_nested_on_play`: Expected `Response`, got `Main`
- `test_q202_nested_on_play_optional`: Expected `Response`, got `Main`  
- `test_card_628_live_start_prompts_optional_topdeck_discard`: Expected `Response`, got `PerformanceP1`
- `test_card_558_on_play_declining_self_tap_skips_live_selection`: Expected `Optional`, got `LookAndChoose`
- `test_card_260_live_start_declining_energy_skips_score_bonus`: Expected `Some(Optional)`, got `None`

**Root Cause:** The phase transition logic in the interpreter is not correctly moving from `Main` to `Response` when encountering optional costs or nested triggers. The `SUSP_DBG` logs consistently show `phase=Main` even when the test expects the game to be in `Response` phase.

### Pattern 2: Choice Type Generation Bug

**Debug Evidence:**
```
[SUSP_DBG] choice_type=LookAndChoose actions=[] final_actions=[11000, 11001, 11002] has_only_pass=false phase=Response cp=0
```

**Assertion Failures:**
- Expected `SelectHandDiscard`, got `LookAndChoose` (card 801, card 861)
- Expected `Optional`, got `LookAndChoose` (card 558)
- Expected `SelectMode`, got `TapO` (card 854)
- Expected `SelectDiscardPlay`, got `Optional` (repro_hazuki_500)

**Analysis:** The choice type generation logic is producing incorrect choice types. The `final_actions` array contains action IDs (11000, 11001, 11002) that correspond to `LookAndChoose` actions when the test expects different choice types like `SelectHandDiscard` or `Optional`.

**Root Cause:** The action generation code in the interpreter is not correctly mapping the intended choice type to the actual action IDs being generated. This suggests a bug in the action-to-choice-type mapping or the conditional logic that determines which choice type to present.

### Pattern 3: Score Buff Calculation Bug (Q203)

**Debug Evidence:**
```
assertion `left == right` failed: Q203: member activation alone currently resolves to +2 in the loaded runtime data
  left: 1
 right: 2

assertion `left == right` failed: Q203: energy plus member activation currently resolves to +3 in the loaded runtime data
  left: 1
 right: 3
```

**Analysis:** The Q203 Niji score buff is not stacking correctly. The expected behavior is:
- Member activation alone: +2
- Energy + member activation: +3
- Actual behavior: Always +1 regardless of activation type

**Affected Tests:**
- `test_q203_niji_score_buff`: Expected 3, got 1
- `test_q203_niji_score_buff_requires_energy_activation_before_member_activation`: Expected 2, got 1
- `test_q203_niji_score_buff_reaches_two_with_energy_and_member_activation`: Expected 3, got 1
- `debug_q203_trace`: Expected 3, got 1

**Root Cause:** The score buff calculation logic is not correctly tracking or accumulating the bonus from different activation types. The buff is being reset to 1 instead of accumulating. This could be due to:
- Incorrect buff state tracking
- Buff not being persisted across activation types
- Buff calculation logic not considering both energy and member activation

### Pattern 4: Cost Selection Isolation Bug

**Debug Evidence:**
```
assertion `left == right` failed: At least one slot should be tapped if cost was accepted
```

**Analysis:** Tests for cost selection (Q183, card 801, card 861) are failing because costs are being accepted without the corresponding side effects (tapping slots, triggering searches, etc.).

**Affected Tests:**
- `test_q183_cost_selection_isolation`: Cost accepted but no slot tapped
- `test_card_801_on_play_only_high_cost_aqours_choice_is_legal_and_remainders_discard`: Expected 5 cards looked at, got 0
- `test_card_801_on_declining_optional_discard_skips_aqours_search`: Expected `SelectHandDiscard`, got `LookAndChoose`

**Root Cause:** The cost payment logic is not correctly linking the cost acceptance to the required side effects. When a cost is paid, the subsequent effects (searching, drawing, tapping) are not being triggered or are being triggered in the wrong order.

### Pattern 5: Structured Frame Preservation Bug

**Debug Evidence:**
```
assertion `left == right` failed: Kinako should not reduce in hand without a moved Liella member
  left: 7
 right: 9

assertion `left == right` failed: The cost-13 blade aura should not apply without a cost 13+ member on either stage
  left: 2
 right: 0
```

**Analysis:** Structured parameters (filters, costs, conditions) are not being preserved correctly during frame operations. The filter bits and cost gates are being lost or incorrectly applied.

**Affected Tests:**
- `structured_count_stage_frame_preserves_not_self_filter_bits`
- `structured_reduce_cost_frame_preserves_card10_style_filter_bits`
- `total_cost_budget_helper_accepts_modern_compare_accumulated`
- `test_hand_only_structured_cost_reducers_use_authored_conditions`
- `test_cost_13_blade_aura_requires_structured_stage_gate`

**Root Cause:** The structured frame serialization/deserialization logic is corrupting or losing filter attributes and cost gate conditions. This is happening in the frame preservation code in `src/core/logic/models.rs`.

### Pattern 6: Card Count/Value Calculation Bug

**Debug Evidence:**
```
assertion `left == right` failed: 558: accepting the self-tap should look at the top four live cards
  left: 0
 right: 4

assertion `left == right` failed: 854: the draw branch should add exactly one card to hand
  left: 0
 right: 1

assertion `left == right` failed: 8844: three different names on stage should grant exactly one additional heart
  left: 0
 right: 1
```

**Analysis:** Card effects that should count or modify values (cards looked at, cards drawn, hearts granted) are returning 0 instead of the expected values.

**Affected Tests:**
- `test_card_558_on_play_tap_branch_only_allows_high_requirement_liella_live`: Expected 4 cards looked at, got 0
- `test_card_854_live_start_draw_branch_draws_without_waiting_opponent`: Expected 1 card drawn, got 0
- `test_card_8844_constant_grants_heart_only_with_three_distinct_names`: Expected 1 heart, got 0
- `test_live_260_live_start_paying_energy_with_nijigasaki_grants_score_bonus`: Expected 1 score, got 0

**Root Cause:** The effect resolution logic is not correctly executing the count/draw/modify operations. This could be due to:
- Effects being skipped or not triggered
- Count logic returning 0 when it should return the actual count
- Effect parameters not being passed correctly to the resolution handlers

### Pattern 7: Position Change Frame Metadata Bug

**Debug Evidence:**
```
Expected position-change ability to expose explicit destination/source frame params: {{toujyou.png|登場}}【左サイド】カードを2枚引き...
```

**Analysis:** Position change abilities are not exposing the expected destination/source metadata in their frame parameters.

**Affected Tests:**
- `test_position_change_text_frames_include_explicit_destination_metadata`

**Root Cause:** The position change frame generation logic is not correctly adding the destination/source parameters to the frame metadata. This is a serialization bug in the frame construction code.

## Summary of Root Causes

1. **State Machine Bug**: Phase transitions from Main to Response are not happening correctly for optional costs and nested triggers
2. **Choice Type Generation Bug**: Action IDs are being mapped to wrong choice types
3. **Score Buff State Bug**: Q203 score buff not accumulating correctly across activation types
4. **Cost-Effect Linkage Bug**: Cost payments not triggering expected side effects
5. **Structured Frame Serialization Bug**: Filter attributes and cost gates being lost during frame operations
6. **Effect Resolution Bug**: Count/draw/modify operations returning 0 instead of expected values
7. **Frame Metadata Bug**: Position change frames missing destination/source parameters

## Key Files to Investigate

1. **State Machine**: `src/core/logic/interpreter/mod.rs` - Phase transition logic
2. **Action Generation**: `src/core/logic/interpreter/handlers/` - Choice type mapping
3. **Score Buff**: `src/core/logic/score.rs` or related buff tracking code
4. **Cost Logic**: `src/core/logic/cost.rs` - Cost-to-effect linkage
5. **Frame Serialization**: `src/core/logic/models.rs` - Structured frame preservation
6. **Effect Resolution**: `src/core/logic/interpreter/handlers/` - Effect execution logic
