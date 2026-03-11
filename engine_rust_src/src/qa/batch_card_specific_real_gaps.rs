use crate::core::generated_constants::{ACTION_BASE_HAND, ACTION_BASE_STAGE, ACTION_BASE_STAGE_SLOTS};
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
        let unrelated_id = first_member_matching(&db, |card| {
            card.card_id != karin_id && card.card_id != multi_name_id && !card.name.contains("朝香果林")
        });

        let mut negative_state = create_test_state();
        negative_state.phase = Phase::Main;
        negative_state.current_player = 0;
        negative_state.ui.silent = true;
        negative_state.players[0].stage[0] = karin_id;
        negative_state.players[0].stage[1] = unrelated_id;
        negative_state.players[0].live_zone[0] = live_id;

        negative_state.trigger_event(&db, TriggerType::OnLiveStart, 0, -1, -1, 0, -1);
        negative_state.process_trigger_queue(&db);

        assert_eq!(
            negative_state.players[0]
                .heart_req_reductions
                .to_array()
                .into_iter()
                .sum::<u8>(),
            0,
            "Q204: a single Karin without a second same-name reference should not reduce the live requirement"
        );

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