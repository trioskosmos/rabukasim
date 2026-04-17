# Remaining Test Failures Analysis

## Summary
- Total failures: 114 (down from 166 after card_id_mapping.json fix)
- Improvement: 52 fewer failures

## Failure Categories

### 1. Card-Specific QA Tests (qa::batch_card_specific::tests)
- test_card_693_on_play_mills_four_without_blade_bonus_when_no_live_is_milled
- test_card_693_reveal_six_blade_heart_types_adds_heart01_and_grants_score
- test_card_693_reveal_three_blade_heart_types_adds_heart01_only
- test_card_697_live_start_discards_dollchestra_to_copy_cost_and_gain_heart
- test_card_755_on_leaves_cost_fifteen_baton_also_draws
- test_card_755_on_leaves_cost_twelve_baton_untaps_two_without_draw
- test_card_761_on_play_distinct_live_groups_only_enables_double_recovery_mode
- test_card_761_on_play_distinct_live_names_only_enables_single_recovery_mode
- test_card_761_on_play_requires_three_distinct_lives_before_any_recovery_mode_is_legal
- test_card_761_on_play_when_both_modes_are_legal_double_recovery_mode_stays_isolated
- test_card_761_on_play_when_both_modes_are_legal_single_recovery_mode_stays_isolated
- test_card_777_live_start_selected_kasumi_colors_grant_matching_hearts
- test_card_801_on_play_only_high_cost_aqours_choice_is_legal_and_remainders_discard
- test_card_854_live_start_draw_branch_draws_without_waiting_opponent
- test_card_854_live_start_wait_branch_only_targets_cost_4_or_less
- test_card_861_on_play_only_high_cost_liella_choice_is_legal_and_remainders_discard
- test_card_8844_activate_draw_branch_requires_discard_tracking
- test_card_8844_activate_recover_branch_uses_non_muse_discard
- test_card_8844_constant_grants_heart_only_with_three_distinct_names
- test_live_260_live_start_paying_energy_with_nijigasaki_grants_score_bonus
- test_live_459_live_start_six_blade_aqours_target_grants_score_bonus
- test_live_583_live_start_active_energy_grants_score_bonus
- test_live_709_live_start_with_three_distinct_names_and_costs_grants_score_bonus
- test_multi_qa_ll_bp2_001
- test_pl_n_bp5_030_l_resolve_trigger
- test_q110_q127_vienna_constant_stacking
- test_q111_q117_vienna_yell_penalty
- test_q160_q161_q162_play_count_trigger
- test_q168_q169_q170_q181_q188_nico_exhaustive
- test_q183_cost_selection_isolation
- test_q196_select_member_empty
- test_q203_niji_score_buff
- test_q206_baton_touch_cost_reduction
- test_q229_response_skips_controller_discard_and_opens_opponent_owned_prompt
- test_q230_setsuna_zero_equality
- test_q232_score_icon_does_not_change_live_self_score
- test_q237_revealing_nonmatching_variant_does_not_recover_base_name
- test_recursive_multi_card_discard_batch_context

### 2. QA Verification Tests (qa_verification_tests::tests)
- test_cost_13_blade_aura_requires_structured_stage_gate
- test_hand_only_structured_cost_reducers_use_authored_conditions
- test_hs_pr_016_same_unit_discard_requires_matching_partner
- test_id_717_baton_touch_untaps_energy
- test_multi_qa_ll_bp2_001
- test_q110_q127_vienna_constant_stacking
- test_q111_q117_vienna_yell_penalty
- test_q160_q161_q162_play_count_trigger
- test_q168_q169_q170_q181_q188_nico_exhaustive
- test_q183_cost_selection_isolation
- test_q196_select_member_empty
- test_q203_niji_score_buff_reaches_two_with_energy_and_member_activation
- test_q203_niji_score_buff_requires_energy_activation_before_member_activation
- test_q206_baton_touch_cost_reduction
- test_q230_setsuna_zero_equality
- test_q239_live_success_places_one_energy_when_under_energy_is_empty
- test_q4791_on_leaves_position_change_prompts_for_destination
- test_q4794_same_group_discard_requires_matching_partner
- test_q49_oh_love_and_peace_live_success_bonus_applies_on_heart_lead
- test_q96_q97_q103_catchu_exhaustive
- test_rule_bp4_001_group_condition
- test_rule_bp4_001_triggers_on_both_sequential_plays
- test_split_frame_index_entries_follow_their_gameplay_text

### 3. Other Tests
- response_flow_tests::test_real_card_646_color_select_uses_color_mask
- stabilized_tests::verify_buff_logic
- wave6_tests::tests::test_baton_touch_restriction

## Notable Observations

1. **test_q203_niji_score_buff**: Expects score buff of 2 but got 0
   - Error: "Q203: member activation alone currently resolves to +2 in the loaded runtime data"
   - left: 0, right: 2
   - This suggests the ability wasn't parsed correctly from semantic extraction

2. **test_q160_q161_q162_play_count_trigger**: Previously investigated for draw issue
   - Still failing after card ID fix
   - Indicates this is a semantic extraction issue, not an ID issue

3. **test_rule_bp4_001_group_condition**: Previously investigated for charged energy
   - Still failing after card ID fix
   - Indicates this is a semantic extraction issue

4. **stabilized_tests::verify_buff_logic**: Previously failed for Card 120 (Ayase Eli)
   - Still failing after card ID fix
   - Indicates this is a semantic extraction issue

## Pattern Analysis

Most failures appear to be related to:
1. Semantic extraction not parsing abilities correctly
2. Missing or incorrect frame generation from semantic data
3. Complex ability logic (multi-branch, conditional effects) not being extracted

These are not card ID issues - they're semantic extraction/parser issues.

## Specific Investigation: test_q203_niji_score_buff

**Card:** PL!N-pb1-037-L - Cara Tesoro (card_id 358, live card)

**Ability Text:**
"ライブ開始時このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを+１する。さらに、自分の『虹ヶ咲』のカードの効果によって自分のステージにいるウェイト状態のメンバーもアクティブにしていた場合、代わりにスコアを+２する。"

**Translation:**
"LIVE_START: If this turn you activated your energy from wait by a 'Nijigasaki' card effect, this card's score +1. Furthermore, if you also activated a member from wait on your stage by a 'Nijigasaki' card effect, instead score +2."

**Extracted Frames:**
- BOOST_SCORE value=0
- BOOST_SCORE value=0
- RETURN

**Issue:**
The ability text clearly says "+1" or "+2" score, but the extracted frames have value=0. The semantic extraction is not parsing the score values correctly. It extracts BOOST_SCORE frames but with value=0 instead of value=1 or value=2.

**Root Cause:**
Semantic extraction parser fails to extract numeric values from ability text for score buffs. This is a parser bug in the semantic extraction pipeline.
