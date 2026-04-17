# Cargo Test Failure Patterns (157 failures)

## 1. Cost Reduction Issues (12 failures)
**Pattern**: Hand-based and baton touch cost reduction not working correctly
- test_card_10_counts_other_hand_cards_not_itself
- test_card_10_cost_reduction_hand_size_variations
- test_card_10_reduce_cost_opcode_per_card_filter
- test_second_copy_of_card_10_keeps_hand_reduction_after_first_is_played
- test_card_10_playability_uses_effective_hand_cost
- test_card_10_baton_cost_does_not_double_count_hand_reduction
- test_card_10_baton_cost_ignores_stage_copy_hand_reduction_leak
- test_q206_baton_touch_cost_reduction
- test_hand_only_structured_cost_reducers_use_authored_conditions
- test_cost_13_blade_aura_requires_structured_stage_gate
- test_id_717_baton_touch_untaps_energy
- test_baton_touch_restriction

**Root Cause**: Parser not generating REDUCE_COST frames with proper card filters (exclude self, count other hand cards)

---

## 2. Live Start Triggers (18 failures)
**Pattern**: Live start triggers not handling energy payments, score bonuses, member selection
- test_repro_card_459_live_start_queues_member_selection
- test_card_4558_ability_0_on_live_start_pay_energy
- test_card_628_live_start_prompts_optional_topdeck_discard
- test_card_47_live_start_second_mode_grants_heart03_only_to_selected_self_member
- test_card_47_live_start_third_mode_grants_heart06_only_to_selected_self_member
- test_card_697_live_start_discards_dollchestra_to_copy_cost_and_gain_heart
- test_card_777_live_start_selected_kasumi_colors_grant_matching_hearts
- test_card_854_live_start_declining_energy_skips_mode_resolution
- test_card_854_live_start_accepting_energy_still_hides_stage_targets_until_mode_choice
- test_card_854_live_start_draw_branch_draws_without_waiting_opponent
- test_card_854_live_start_wait_branch_only_targets_cost_4_or_less
- test_live_583_live_start_active_energy_grants_score_bonus
- test_live_708_live_start_paying_energy_with_same_hasunosora_unit_skips_score_bonus
- test_live_709_live_start_with_three_distinct_names_and_costs_grants_score_bonus
- test_live_260_live_start_declining_energy_skips_score_bonus
- test_live_260_live_start_paying_energy_with_nijigasaki_grants_score_bonus
- test_live_260_live_start_paying_energy_without_nijigasaki_skips_score_bonus
- test_live_459_live_start_six_blade_aqours_target_grants_score_bonus

**Root Cause**: Live start triggers not parsing optional energy payments, score bonus conditions, member selection phases

---

## 3. Multi-Name / Distinct Name Conditions (15 failures)
**Pattern**: Multi-name cards and distinct name/group conditions not working
- test_card_8844_constant_grants_heart_only_with_three_distinct_names
- test_card_761_on_play_distinct_live_groups_only_enables_double_recovery_mode
- test_card_761_on_play_distinct_live_names_only_enables_single_recovery_mode
- test_card_761_on_play_requires_three_distinct_lives_before_any_recovery_mode_is_legal
- test_card_761_on_play_when_both_modes_are_legal_double_recovery_mode_stays_isolated
- test_card_761_on_play_when_both_modes_are_legal_single_recovery_mode_stays_isolated
- test_live_709_live_start_with_three_distinct_names_and_costs_grants_score_bonus
- test_live_459_live_start_six_blade_aqours_target_grants_score_bonus
- test_q204_same_name_condition_counts_multi_name_member
- test_q62_q65_q69_q90_triple_name_card
- test_hs_pr_016_same_unit_discard_requires_matching_partner
- test_q4794_same_group_discard_requires_matching_partner
- test_q203_niji_score_buff_reaches_two_with_energy_and_member_activation
- test_q203_niji_score_buff_requires_energy_activation_before_member_activation
- test_q203_niji_score_buff

**Root Cause**: Multi-name card parsing and distinct name/group condition frames not generated correctly

---

## 4. Multi-Pick / Selection Issues (8 failures)
**Pattern**: Sequential pick operations, choose count, selection modes
- test_repro_card_420_second_pick_can_be_skipped
- test_repro_card_420_cost_sum_limit
- test_repro_card_420_multi_pick_from_discard
- test_look_and_choose_allows_multiple_picks
- test_look_and_choose_uses_real_card_choose_count
- test_hazuki_500_looks_at_five_cards_after_optional_discard
- test_card_4770_discard_then_peek_resolves_one_looked_card
- test_q196_select_member_empty

**Root Cause**: Multi-pick sequence not handling skip options, cost limits, choose count correctly

---

## 5. Frame Sequence / Ordering Issues (6 failures)
**Pattern**: Frame order not matching gameplay text sequence
- test_ruby_423_frame_sequence
- test_ruby_423_requires_self_sacrifice
- test_split_frame_index_entries_follow_their_gameplay_text
- test_card_275_sequential_interaction_resumption
- test_q84_simultaneous_trigger_order
- test_q171_until_live_end_effect_expires_even_without_a_live

**Root Cause**: Frame generation order not preserving gameplay text sequence

---

## 6. Heart Filter / Type Issues (5 failures)
**Pattern**: Heart type filtering, blade-heart type combinations
- test_card_579_ability_1_heart_filter
- test_card_579_ability_0_cost_comparison
- test_card_693_on_play_mills_four_and_gains_blades_when_a_live_is_milled
- test_card_693_on_play_mills_four_without_blade_bonus_when_no_live_is_milled
- test_card_693_reveal_three_blade_heart_types_adds_heart01_only
- test_card_693_reveal_six_blade_heart_types_adds_heart01_and_grants_score

**Root Cause**: Heart type filtering and blade-heart combination conditions not parsed correctly

---

## 7. Activation / Deployment Cost Issues (4 failures)
**Pattern**: Cards should leave stage as activation cost, deployment conditions
- test_card_874_activation_discards_self_before_energy_charge
- test_card_574_self_discards_without_stage_selection
- test_card_707_wait_execution_honors_cost_filter
- test_card_163_optional_live_start_prompt_uses_yes_no_actions_only

**Root Cause**: Activation cost parsing - card should leave stage, wait execution not honored

---

## 8. Baton Touch / Double Baton Issues (4 failures)
**Pattern**: Baton touch interactions, double baton mechanics
- test_repro_card_560_double_baton
- test_card_656_on_play_baton_discard_down_then_draw_three_for_both_players
- test_card_656_on_play_response_hands_off_from_controller_to_opponent_and_back
- test_card_755_on_leaves_cost_fifteen_baton_also_draws
- test_card_755_on_leaves_cost_twelve_baton_untaps_two_without_draw
- test_q193_double_baton_can_land_in_either_source_slot

**Root Cause**: Baton touch mechanics not handling double baton, response phase correctly

---

## 9. On Play / Nested Trigger Issues (12 failures)
**Pattern**: Nested on play triggers, tap restrictions, mode selection
- test_card_558_on_play_declining_self_tap_skips_live_selection
- test_card_558_on_play_tap_branch_only_allows_high_requirement_liella_live
- test_card_672_private_wars_first_mode_activates_waiting_member_and_adds_blade
- test_card_672_private_wars_second_mode_only_targets_opponent_with_three_or_less_blades
- test_card_654_on_play_score_six_success_pile_adds_energy
- test_card_801_on_play_only_high_cost_aqours_choice_is_legal_and_remainders_discard
- test_card_801_on_play_declining_optional_discard_skips_aqours_search
- test_card_861_on_play_only_high_cost_liella_choice_is_legal_and_remainders_discard
- test_card_8844_activate_draw_branch_requires_discard_tracking
- test_card_8844_activate_recover_branch_uses_non_muse_discard
- test_q201_nested_on_play
- test_q202_nested_on_play_optional

**Root Cause**: On play triggers not handling nested conditions, tap restrictions, mode selection

---

## 10. QA Verification Tests (23 failures)
**Pattern**: General QA verification failures across multiple cards
- test_q110_q127_vienna_constant_stacking
- test_q111_q117_vienna_yell_penalty
- test_pl_n_bp5_030_l_resolve_trigger
- test_multi_qa_ll_bp2_001
- test_q189_opponent_chooses_effect
- test_q183_cost_selection_isolation
- test_q160_q161_q162_play_count_trigger
- test_q168_q169_q170_q181_q188_nico_exhaustive
- test_q209_discarded_live_can_be_recovered_as_activation_target
- test_q214_zero_score_live_recovery_costs_zero_energy
- test_q229_response_skips_controller_discard_and_opens_opponent_owned_prompt
- test_q229_player_with_three_or_fewer_hand_still_draws_three
- test_q232_score_icon_does_not_change_live_self_score
- test_q230_setsuna_zero_equality
- test_q237_revealing_nonmatching_variant_does_not_recover_base_name
- test_recursive_multi_card_discard_batch_context
- test_q132_live_success_bonus_applies_for_first_player
- test_q234_kinako_requires_hand_card_for_activation
- test_q239_live_success_places_one_energy_when_under_energy_is_empty
- test_q4791_on_leaves_position_change_prompts_for_destination
- test_q49_oh_love_and_peace_live_success_bonus_applies_on_heart_lead
- test_q96_q97_q103_catchu_exhaustive
- test_rule_bp4_001_group_condition
- test_rule_bp4_001_triggers_on_both_sequential_plays

**Root Cause**: Various condition parsing, trigger order, cost selection, discard tracking issues

---

## 11. Other / Debug Tests (50 failures)
**Pattern**: Debug tests, softlock fixes, specific card repros
- card_617_draws_once_per_six_energy_from_text
- muse_live_recovery_puts_the_discard_live_card_on_top_of_deck_before_draw
- energy_threshold_draw_cards_follow_their_text
- test_repro_bp4_002_p_wait_flow
- test_card_528_movement_fix
- test_repro_pb1_001_r_all_combinations
- test_repro_pb1_001_r_softlock_fix
- test_pay_energy_high_cost_softlock_fix
- test_kanon_557_repro
- test_repro_softlock_full_flow
- test_cost_13_passive_repro
- test_ability_activation_zone_repro
- debug_card_122_hydrated_frames
- test_multi_ability_encoding_slots
- test_prevent_activate_blocks_all
- test_tapped_member_can_activate_non_tapself
- test_area_rotation_mei
- test_selective_retrieval_natsumi
- test_selective_reveal_kanon
- test_meta_rule_yell_mulligan
- test_card_4558_abilities_in_compiled_data
- test_card_4558_ability_exposure_in_game_state
- test_yell_persistence_and_selection
- test_ability_55_kurosawa_ruby_missing_saintsnow_filter
- test_ability_6_ozawa_rurino_simple_draw_behavior
- test_ability_64_kurosawa_dia_flavor_choice
- test_ability_64_option1_aqours_blade
- test_ability_64_option2_saintsnow_position_change
- debug_q203_trace
- test_opcode_tap_opponent_dynamic
- verify_buff_logic
- test_trigger_activated_eli
- test_kimi_no_kokoro_prevention
- (and 20+ more debug/repro tests)

**Root Cause**: Debug tests, softlock fixes, specific card mechanics

---

## Summary by Root Cause

1. **Cost Reduction Parsing** (12): REDUCE_COST frames not generated with proper card filters
2. **Live Start Trigger Parsing** (18): Optional energy payments, score bonuses, member selection not handled
3. **Multi-Name Card Parsing** (15): Distinct name/group conditions not parsed correctly
4. **Multi-Pick Sequence** (8): Skip options, cost limits, choose count issues
5. **Frame Ordering** (6): Frame generation order not preserving gameplay text sequence
6. **Heart Type Filtering** (5): Blade-heart combination conditions not parsed
7. **Activation Cost** (4): Card leave stage, wait execution issues
8. **Baton Touch Mechanics** (4): Double baton, response phase issues
9. **On Play Nested Triggers** (12): Nested conditions, tap restrictions, mode selection
10. **General QA Issues** (23): Condition parsing, trigger order, discard tracking
11. **Debug/Repro Tests** (50): Debug tests, softlock fixes, specific card mechanics

**Total**: 157 failures
