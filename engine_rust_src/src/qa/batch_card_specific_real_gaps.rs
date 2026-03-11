use crate::core::enums::ChoiceType;
use crate::core::generated_constants::{ACTION_BASE_CHOICE, ACTION_BASE_HAND, ACTION_BASE_HAND_SELECT, ACTION_BASE_STAGE, ACTION_BASE_STAGE_SLOTS, C_COUNT_STAGE, C_TOTAL_BLADES};
use crate::core::logic::*;
use crate::test_helpers::*;

#[cfg(test)]
mod tests {
    use super::*;

    fn first_member_with_cost<F>(db: &CardDatabase, cost: u32, predicate: F) -> i32
    where
        F: Fn(&MemberCard) -> bool,
    {
        db.members
            .values()
            .find(|card| card.cost == cost && predicate(card))
            .map(|card| card.card_id)
            .expect("expected a parseable member matching the requested cost")
    }

    fn first_member_matching<F>(db: &CardDatabase, predicate: F) -> i32
    where
        F: Fn(&MemberCard) -> bool,
    {
        db.members
            .values()
            .find(|card| predicate(card))
            .map(|card| card.card_id)
            .expect("expected a parseable member matching the requested predicate")
    }

    fn first_live_id(db: &CardDatabase) -> i32 {
        db.lives
            .keys()
            .copied()
            .next()
            .expect("expected a parseable live card in the real DB")
    }

    fn blade_threshold_pair(db: &CardDatabase, threshold: u32) -> (i32, i32, u32, u32) {
        let mut candidates: Vec<&MemberCard> = db.members.values().filter(|card| card.blades > 0).collect();
        candidates.sort_by_key(|card| std::cmp::Reverse(card.blades));

        for active in &candidates {
            if active.blades >= threshold {
                continue;
            }
            for waiting in &candidates {
                if active.card_id == waiting.card_id {
                    continue;
                }
                let total = active.blades.saturating_add(waiting.blades);
                if total >= threshold {
                    return (active.card_id, waiting.card_id, active.blades, waiting.blades);
                }
            }
        }

        panic!("expected two members whose combined blades cross the threshold only when both count");
    }

    fn setup_sumire_double_baton_state(db: &CardDatabase) -> GameState {
        let sumire_id = db
            .id_by_no("PL!SP-bp4-004-R＋")
            .expect("Q193/Q194: expected Sumire double-baton card in DB");
        let kanon_id = db
            .id_by_no("PL!SP-bp4-001-P")
            .expect("Q193/Q194: expected Kanon in DB");
        let keke_id = db
            .id_by_no("PL!SP-bp4-002-P")
            .expect("Q193/Q194: expected Keke in DB");

        let mut state = create_test_state();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.ui.silent = true;
        state.players[0].stage = [kanon_id, keke_id, -1];
        state.players[0].hand = vec![sumire_id].into();
        state.players[0].energy_zone = vec![3001; 22].into();
        state
    }

    #[test]
    fn test_q132_live_success_bonus_applies_for_first_player() {
        let db = load_real_db();
        let live_id = db
            .id_by_no("PL!S-pb1-021-L")
            .expect("Q132: expected Strawberry Trapper in DB");
        let live = db.get_live(live_id).expect("Q132: live card should resolve from DB");
        let ability = live
            .abilities
            .iter()
            .find(|ability| ability.trigger == TriggerType::OnLiveSuccess)
            .expect("Q132: expected a live-success ability on Strawberry Trapper");
        let aqours_candidates: Vec<i32> = db
            .members
            .values()
            .filter(|card| card.groups.contains(&1))
            .take(18)
            .map(|card| card.card_id)
            .collect();

        let mut passing_stage = None;
        'search: for i in 0..aqours_candidates.len() {
            let single = vec![aqours_candidates[i]];
            if {
                let stage_members = single.clone();
                let mut state = create_test_state();
                state.phase = Phase::LiveResult;
                state.current_player = 0;
                state.first_player = 0;
                state.ui.silent = true;
                state.players[0].live_zone[0] = live_id;
                state.players[1].excess_hearts = 0;
                state.obtained_success_live[0] = true;
                for (slot, cid) in stage_members.iter().copied().enumerate() {
                    state.players[0].stage[slot] = cid;
                }
                let ctx = AbilityContext {
                    source_card_id: live_id,
                    player_id: 0,
                    trigger_type: TriggerType::OnLiveSuccess,
                    ..Default::default()
                };
                ability
                    .conditions
                    .iter()
                    .all(|condition| state.check_condition(&db, 0, condition, &ctx, 0))
            } {
                passing_stage = Some(single);
                break;
            }
            for j in (i + 1)..aqours_candidates.len() {
                let pair = vec![aqours_candidates[i], aqours_candidates[j]];
                if {
                    let stage_members = pair.clone();
                    let mut state = create_test_state();
                    state.phase = Phase::LiveResult;
                    state.current_player = 0;
                    state.first_player = 0;
                    state.ui.silent = true;
                    state.players[0].live_zone[0] = live_id;
                    state.players[1].excess_hearts = 0;
                    state.obtained_success_live[0] = true;
                    for (slot, cid) in stage_members.iter().copied().enumerate() {
                        state.players[0].stage[slot] = cid;
                    }
                    let ctx = AbilityContext {
                        source_card_id: live_id,
                        player_id: 0,
                        trigger_type: TriggerType::OnLiveSuccess,
                        ..Default::default()
                    };
                    ability
                        .conditions
                        .iter()
                        .all(|condition| state.check_condition(&db, 0, condition, &ctx, 0))
                } {
                    passing_stage = Some(pair);
                    break 'search;
                }
                for k in (j + 1)..aqours_candidates.len() {
                    let triple = vec![aqours_candidates[i], aqours_candidates[j], aqours_candidates[k]];
                    if {
                        let stage_members = triple.clone();
                        let mut state = create_test_state();
                        state.phase = Phase::LiveResult;
                        state.current_player = 0;
                        state.first_player = 0;
                        state.ui.silent = true;
                        state.players[0].live_zone[0] = live_id;
                        state.players[1].excess_hearts = 0;
                        state.obtained_success_live[0] = true;
                        for (slot, cid) in stage_members.iter().copied().enumerate() {
                            state.players[0].stage[slot] = cid;
                        }
                        let ctx = AbilityContext {
                            source_card_id: live_id,
                            player_id: 0,
                            trigger_type: TriggerType::OnLiveSuccess,
                            ..Default::default()
                        };
                        ability
                            .conditions
                            .iter()
                            .all(|condition| state.check_condition(&db, 0, condition, &ctx, 0))
                    } {
                        passing_stage = Some(triple);
                        break 'search;
                    }
                }
            }
        }

        let stage_members = passing_stage.expect("Q132: expected to find a real Aqours stage combination satisfying the live-success condition");

        let conditions_hold = |first_player: u8, opponent_excess_hearts: u32| {
            let mut state = create_test_state();
            state.phase = Phase::LiveResult;
            state.current_player = 0;
            state.first_player = first_player;
            state.ui.silent = true;
            state.players[0].live_zone[0] = live_id;
            state.players[1].excess_hearts = opponent_excess_hearts;
            state.obtained_success_live[0] = true;

            for (slot, cid) in stage_members.iter().copied().enumerate() {
                state.players[0].stage[slot] = cid;
            }

            let ctx = AbilityContext {
                source_card_id: live_id,
                player_id: 0,
                trigger_type: TriggerType::OnLiveSuccess,
                ..Default::default()
            };
            ability
                .conditions
                .iter()
                .all(|condition| state.check_condition(&db, 0, condition, &ctx, 0))
        };

        assert!(
            conditions_hold(0, 0),
            "Q132: Strawberry Trapper's live-success conditions should evaluate true even when its controller is first player"
        );
        assert!(
            conditions_hold(1, 0),
            "Q132: the same live-success conditions should also evaluate true when the controller is not first player"
        );
        assert!(
            !conditions_hold(0, 1),
            "Q132: the same live-success condition set should fail once the opponent has excess hearts"
        );
    }

    #[test]
    fn test_q144_up_to_two_can_choose_only_one_target() {
        let db = load_real_db();
        let eli_id = db
            .id_by_no("PL!-bp3-002-P")
            .expect("Q144: expected Eli card in DB");
        let victim_id = first_member_matching(&db, |card| card.cost <= 4 && card.card_id != eli_id);
        let expensive_id = first_member_matching(&db, |card| {
            card.cost >= 5 && card.card_id != eli_id && card.card_id != victim_id
        });
        let discard_cost_id = first_member_matching(&db, |card| {
            card.card_id != eli_id && card.card_id != victim_id && card.card_id != expensive_id
        });

        let mut state = create_test_state();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.ui.silent = true;
        state.players[0].stage[0] = eli_id;
        state.players[0].hand = vec![discard_cost_id].into();
        state.players[1].stage[0] = victim_id;
        state.players[1].stage[1] = expensive_id;
        state.players[1].set_tapped(0, false);
        state.players[1].set_tapped(1, false);

        let actx = AbilityContext {
            source_card_id: eli_id,
            player_id: 0,
            area_idx: 0,
            trigger_type: TriggerType::OnPlay,
            ability_index: 0,
            ..Default::default()
        };
        state
            .trigger_queue
            .push_back((eli_id, 0, actx, false, TriggerType::OnPlay));
        state.process_trigger_queue(&db);

        if let Some(interaction) = state.interaction_stack.last() {
            if interaction.choice_type == ChoiceType::Optional {
                state
                    .handle_response(&db, ACTION_BASE_CHOICE + 0)
                    .expect("Q144: accepting the optional cost should succeed");
                state.process_trigger_queue(&db);
            }
        }

        if let Some(interaction) = state.interaction_stack.last() {
            if interaction.choice_type == ChoiceType::SelectHandDiscard {
                let mut receiver = TestActionReceiver::default();
                state.generate_legal_actions(&db, 0, &mut receiver);
                let discard_action = *receiver
                    .actions
                    .iter()
                    .find(|action| **action >= ACTION_BASE_HAND_SELECT)
                    .expect("Q144: discard cost should generate a selectable hand action");
                state
                    .handle_response(&db, discard_action)
                    .expect("Q144: paying the discard cost should succeed");
                state.process_trigger_queue(&db);
            }
        }

        if let Some(interaction) = state.interaction_stack.last() {
            assert_eq!(
                interaction.choice_type,
                ChoiceType::SelectMember,
                "Q144: the effect should pause on filtered opponent-member target selection"
            );

            let mut receiver = TestActionReceiver::default();
            state.generate_legal_actions(&db, 0, &mut receiver);

            state
                .handle_response(&db, ACTION_BASE_STAGE_SLOTS + 0)
                .expect("Q144: selecting the single valid target should succeed");

            let follow_up = state
                .interaction_stack
                .last()
                .expect("Q144: selecting the target should advance into the optional tap prompt");
            assert_eq!(
                follow_up.choice_type,
                ChoiceType::Optional,
                "Q144: after choosing one valid target, the effect should only require confirming the optional tap"
            );

            state
                .handle_response(&db, ACTION_BASE_CHOICE + 0)
                .expect("Q144: confirming the optional tap should succeed");
            state.process_trigger_queue(&db);
        }

        assert!(
            state.players[1].is_tapped(0),
            "Q144: the single valid opponent member should end up tapped"
        );
        assert!(
            !state.players[1].is_tapped(1),
            "Q144: the out-of-range opponent member must remain untouched"
        );
    }

    #[test]
    fn test_q146_on_play_counts_the_member_itself() {
        let db = load_real_db();
        let umi_id = db
            .id_by_no("PL!-bp3-004-R＋")
            .expect("Q146: expected Umi card in DB");

        let mut state = create_test_state();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.ui.silent = true;
        state.players[0].stage[0] = umi_id;

        let ctx = AbilityContext {
            source_card_id: umi_id,
            player_id: 0,
            area_idx: 0,
            trigger_type: TriggerType::OnPlay,
            ..Default::default()
        };

        assert!(
            state.check_condition_opcode(&db, C_COUNT_STAGE, 1, 0, 0, &ctx, 0),
            "Q146: once Umi has entered the stage, the engine should count that source member as the one stage member"
        );
        assert!(
            !state.check_condition_opcode(&db, C_COUNT_STAGE, 2, 0, 0, &ctx, 0),
            "Q146: the same board should not count as two members when only the source member is present"
        );
    }

    #[test]
    fn test_q148_wait_state_member_blades_still_count() {
        let db = load_real_db();
        let live_id = db
            .id_by_no("PL!-bp3-023-L")
            .expect("Q148: expected live card in DB");
        let (active_id, waiting_id, active_blades, waiting_blades) = blade_threshold_pair(&db, 10);

        let condition_passes = |include_waiting_member: bool| {
            let mut state = create_test_state();
            state.phase = Phase::Main;
            state.current_player = 0;
            state.ui.silent = true;
            state.players[0].live_zone[0] = live_id;
            state.players[0].stage[0] = active_id;

            if include_waiting_member {
                state.players[0].stage[1] = waiting_id;
                state.players[0].set_tapped(1, true);
            }

            let ctx = AbilityContext {
                source_card_id: live_id,
                player_id: 0,
                trigger_type: TriggerType::OnLiveStart,
                ..Default::default()
            };
            state.check_condition_opcode(&db, C_TOTAL_BLADES, 10, 0, 0, &ctx, 0)
        };

        let without_condition = condition_passes(false);
        let with_condition = condition_passes(true);

        assert!(
            active_blades < 10,
            "Q148: chosen active member must stay below threshold on its own"
        );
        assert!(
            active_blades.saturating_add(waiting_blades) >= 10,
            "Q148: chosen pair must only cross the threshold when the waiting member is counted"
        );
        assert!(!without_condition, "Q148: the threshold condition should fail before counting the waiting member");
        assert!(with_condition, "Q148: the total-blades threshold should pass once the waiting member is included");
    }

    #[test]
    fn test_q155_success_pile_cost_bonus_does_not_apply_in_hand() {
        let db = load_real_db();
        let member_id = db
            .id_by_no("PL!S-bp3-016-N")
            .expect("Q155: expected Dia card in DB");
        let base_cost = db
            .members
            .get(&member_id)
            .expect("Q155: member should resolve from DB")
            .cost as usize;

        let mut state = create_test_state();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.ui.silent = true;
        state.players[0].hand = vec![member_id].into();
        state.players[0].energy_zone = vec![3001; base_cost].into();
        state.players[0].success_lives = vec![first_live_id(&db)].into();

        let mut actions: Vec<i32> = Vec::new();
        state.generate_legal_actions(&db, 0, &mut actions);

        assert!(
            actions.iter().any(|action| *action >= ACTION_BASE_HAND && *action < ACTION_BASE_STAGE),
            "Q155: the card should still be playable for its printed cost while it is in hand, even with one success live already scored"
        );
    }

    #[test]
    fn test_q184_under_member_energy_does_not_count_for_play_costs() {
        let db = load_real_db();
        let mut state = create_test_state();
        let support_member_id = db
            .id_by_no("PL!N-bp3-001-P")
            .expect("Q184: expected under-member energy card in DB");
        let cost4_member_id = first_member_with_cost(&db, 4, |card| card.abilities.is_empty());

        state.phase = Phase::Main;
        state.current_player = 0;
        state.ui.silent = true;
        state.players[0].stage[0] = support_member_id;
        state.players[0].stage_energy[0] = vec![3101, 3102].into();
        state.players[0].energy_zone = vec![3001, 3002, 3003].into();
        state.players[0].hand = vec![cost4_member_id].into();

        let play_to_empty_slot = ACTION_BASE_HAND + 1;
        let mut actions = Vec::new();
        state.generate_legal_actions(&db, 0, &mut actions);

        assert_eq!(state.players[0].energy_zone.len(), 3, "Q184: energy zone should only count visible energy cards");
        assert_eq!(state.players[0].stage_energy[0].len(), 2, "Q184: under-member energy should be tracked separately");
        assert!(
            !actions.contains(&play_to_empty_slot),
            "Q184: two cards under a member must not let a 3-energy board pay for a cost-4 play"
        );

        state.players[0].energy_zone.push(3004);
        actions.clear();
        state.generate_legal_actions(&db, 0, &mut actions);

        assert!(
            actions.contains(&play_to_empty_slot),
            "Q184: once the fourth actual energy is added, the same play should become legal"
        );
    }

    #[test]
    fn test_q193_double_baton_can_land_in_either_source_slot() {
        let db = load_real_db();
        let state = setup_sumire_double_baton_state(&db);
        let mut actions = Vec::new();
        state.generate_legal_actions(&db, 0, &mut actions);

        let land_in_slot_0 = ACTION_BASE_HAND + 4;
        let land_in_slot_1 = ACTION_BASE_HAND + 5;

        assert!(
            actions.contains(&land_in_slot_0),
            "Q193: double-baton play should allow landing in the first source slot"
        );
        assert!(
            actions.contains(&land_in_slot_1),
            "Q193: double-baton play should allow landing in the second source slot"
        );

        let mut resolve_into_second_slot = setup_sumire_double_baton_state(&db);
        let sumire_id = resolve_into_second_slot.players[0].hand[0];
        resolve_into_second_slot
            .step(&db, land_in_slot_1)
            .expect("Q193: double-baton resolution into the second source slot should succeed");

        assert_eq!(
            resolve_into_second_slot.players[0].stage,
            [-1, sumire_id, -1],
            "Q193: the played member should occupy whichever baton source slot the player selected"
        );
        assert_eq!(
            resolve_into_second_slot.players[0].baton_touch_count,
            2,
            "Q193: resolving the play should consume two baton sources"
        );
    }

    #[test]
    fn test_q194_double_baton_rejects_member_that_entered_this_turn() {
        let db = load_real_db();
        let mut state = setup_sumire_double_baton_state(&db);
        let mut actions = Vec::new();

        state.players[0].set_moved(1, true);
        state.generate_legal_actions(&db, 0, &mut actions);

        assert!(
            actions.contains(&(ACTION_BASE_HAND + 0)),
            "Q194: a normal baton over the eligible older member should still be legal"
        );
        assert!(
            !actions.contains(&(ACTION_BASE_HAND + 1)),
            "Q194: a same-turn member cannot be used as the primary baton slot"
        );
        assert!(
            !actions.contains(&(ACTION_BASE_HAND + 4)) && !actions.contains(&(ACTION_BASE_HAND + 5)),
            "Q194: any double-baton line using the same-turn member must be rejected"
        );
    }

    #[test]
    fn test_q198_cost11_baton_does_not_trigger_lanzhu_stage_entry() {
        let db = load_real_db();
        let mut state = create_test_state();
        let lanzhu_id = db
            .id_by_no("PL!N-pb1-012-P＋")
            .expect("Q198: expected Lanzhu card in DB");
        let cost11_member_id = first_member_with_cost(&db, 11, |card| card.card_id != lanzhu_id);

        state.phase = Phase::Main;
        state.current_player = 0;
        state.ui.silent = true;
        state.players[0].stage[1] = lanzhu_id;
        state.players[0].hand = vec![cost11_member_id].into();
        state.players[0].energy_zone = vec![3001].into();
        state.players[0].set_energy_tapped(0, true);

        let tapped_before = state.players[0].tapped_energy_mask.count_ones();

        state
            .play_member(&db, 0, 1)
            .expect("Q198: cost-11 baton play should succeed");
        state.process_trigger_queue(&db);

        assert_eq!(
            state.players[0].tapped_energy_mask.count_ones(),
            tapped_before,
            "Q198: Lanzhu's stage-entry auto should not activate a waiting energy when she is the member being replaced"
        );
        assert_eq!(
            state.players[0].stage[1],
            cost11_member_id,
            "Q198: the replacement member should still be the card left on stage"
        );
        assert!(
            state.players[0].discard.contains(&lanzhu_id),
            "Q198: Lanzhu should be in discard after being used as the baton source"
        );
    }

    #[test]
    fn test_q171_until_live_end_effect_expires_even_without_a_live() {
        let db = load_real_db();
        let chika_id = db
            .id_by_no("PL!S-bp3-001-P")
            .expect("Q171: expected Chika in DB");
        let target_member_id = first_member_matching(&db, |card| card.card_id != chika_id);

        let mut state = create_test_state();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.first_player = 0;
        state.ui.silent = true;
        state.players[0].stage[0] = target_member_id;
        state.players[0].stage[1] = chika_id;

        state
            .step(&db, ACTION_BASE_STAGE + 100)
            .expect("Q171: activating Chika should succeed");
        state
            .step(&db, ACTION_BASE_STAGE_SLOTS + 0)
            .expect("Q171: selecting the other member as the target should succeed");
        state.process_trigger_queue(&db);

        assert_eq!(
            state.players[0].granted_abilities.len(),
            1,
            "Q171: the until-live-end granted ability should exist immediately after activation"
        );

        state.phase = Phase::LiveResult;
        state.finalize_live_result();
        state.do_active_phase(&db);

        assert!(
            state.players[0].granted_abilities.is_empty(),
            "Q171: the until-live-end granted ability should disappear even if no live was performed"
        );
    }

    #[test]
    fn test_q204_same_name_condition_counts_multi_name_member() {
        let db = load_real_db();
        let live_id = db
            .id_by_no("PL!N-pb1-042-L")
            .expect("Q204: expected Eternalize Love!! in DB");
        let karin_id = db
            .id_by_no("PL!N-pb1-016-R")
            .expect("Q204: expected Karin in DB");
        let multi_name_id = db
            .id_by_no("LL-bp4-001-R＋")
            .expect("Q204: expected the Karin-containing multi-name member in DB");
        let mut positive_state = create_test_state();
        positive_state.phase = Phase::Main;
        positive_state.current_player = 0;
        positive_state.ui.silent = true;
        positive_state.players[0].stage[0] = karin_id;
        positive_state.players[0].stage[1] = multi_name_id;
        positive_state.players[0].live_zone[0] = live_id;

        positive_state.trigger_event(&db, TriggerType::OnLiveStart, 0, -1, -1, 0, -1);
        positive_state.process_trigger_queue(&db);

        assert_eq!(
            positive_state.players[0]
                .heart_req_reductions
                .to_array()
                .into_iter()
                .sum::<u8>(),
            3,
            "Q204: the multi-name member should count as a second Karin for the same-name live-start condition"
        );
    }
}