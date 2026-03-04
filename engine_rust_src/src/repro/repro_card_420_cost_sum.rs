use crate::core::generated_constants::*;
use crate::core::logic::{ChoiceType, GameState, Phase};
use crate::test_helpers::*;

#[test]
fn test_repro_card_420_cost_sum_limit() {
    let db = load_real_db();
    let card_420_id = 420; // 津島善子, Card No: PL!S-bp2-006-P

    let mut cost_4_id = -1;
    let mut cost_2_ids = Vec::new();

    for (_no, &id) in &db.card_no_to_id {
        if let Some(m) = db.get_member(id) {
            if m.abilities.is_empty() {
                if m.cost == 4 && cost_4_id == -1 {
                    cost_4_id = id;
                } else if m.cost == 2 && cost_2_ids.len() < 2 {
                    cost_2_ids.push(id);
                }
            }
        }
        if cost_4_id != -1 && cost_2_ids.len() >= 2 {
            break;
        }
    }
    assert!(
        cost_4_id != -1 && cost_2_ids.len() >= 2,
        "Need vanilla members with cost 2 and 4 in DB"
    );

    let p0_deck = vec![cost_4_id; 60];
    let p1_deck = vec![cost_4_id; 60];
    let mut state = GameState::default();
    state.initialize_game(
        p0_deck,
        p1_deck,
        vec![999; 12],
        vec![999; 12],
        vec![12001; 3],
        vec![12001; 3],
    );
    state.debug.debug_mode = true;

    let p_idx = 0;

    // Ensure enough energy
    state.core.players[p_idx].energy_zone = smallvec::smallvec![999; 20];
    state.core.players[p_idx].tapped_energy_mask = 0;

    // Scenario 1: Pick Cost 4 -> Should NOT allow 2nd card
    {
        let mut state = state.clone();
        state.core.players[p_idx].discard = vec![cost_4_id, cost_2_ids[0]].into();
        state.core.players[p_idx].hand = vec![card_420_id].into();
        state.current_player = p_idx as u8;
        state.phase = Phase::Main;

        // 1. Play Card 420 from hand to slot 0 (Action includes target slot)
        state.step(&db, ACTION_BASE_HAND + 0).unwrap(); // Play hand[0] to slot 0

        // Now it triggers OnPlay.
        // It should suspend for PAY_ENERGY (Optional).
        assert_eq!(
            state.interaction_stack.last().unwrap().choice_type,
            ChoiceType::Optional
        );
        state.step(&db, ACTION_BASE_CHOICE + 0).unwrap(); // Pay Energy (Yes)

        // Now it should suspend for SELECT_DISCARD_PLAY
        assert_eq!(
            state.interaction_stack.last().unwrap().choice_type,
            ChoiceType::SelectDiscardPlay
        );
        let looked_cards = state.core.players[p_idx].looked_cards.clone();
        let idx = looked_cards
            .iter()
            .position(|&cid| cid == cost_4_id)
            .expect("Cost 4 card not in looked_cards");

        state.step(&db, ACTION_BASE_CHOICE + idx as i32).unwrap(); // Select Card
        state.step(&db, ACTION_BASE_CHOICE + 1).unwrap(); // Select Slot 1 (since Slot 0 has Yoshiko)

        // After placing cost 4 card, v_accumulated should be 0.
        // The engine should see no more cards (since cost 2 > 0) and finish.
        assert_eq!(state.core.players[p_idx].stage[1], cost_4_id);
        assert!(
            state.interaction_stack.is_empty(),
            "Should be empty after limit reached"
        );
    }

    // Scenario 2: Pick Cost 2 -> Should allow another Cost 2 but NOT Cost 4
    {
        let mut state = state.clone();
        state.core.players[p_idx].discard = vec![cost_4_id, cost_2_ids[0], cost_2_ids[1]].into();
        state.core.players[p_idx].hand = vec![card_420_id].into();
        state.current_player = p_idx as u8;
        state.phase = Phase::Main;

        state.step(&db, ACTION_BASE_HAND + 0).unwrap();
        state.step(&db, ACTION_BASE_CHOICE + 0).unwrap(); // Pay Energy (Yes)

        // Pick 1st Cost 2 card
        {
            assert_eq!(
                state.interaction_stack.last().unwrap().choice_type,
                ChoiceType::SelectDiscardPlay
            );
            let looked_cards = state.core.players[p_idx].looked_cards.clone();
            let idx = looked_cards
                .iter()
                .position(|&cid| cid == cost_2_ids[0])
                .expect("Cost 2 card not in looked_cards");
            state.step(&db, ACTION_BASE_CHOICE + idx as i32).unwrap(); // Select Card
            state.step(&db, ACTION_BASE_CHOICE + 1).unwrap(); // Select Slot 1
        }

        // Now it should suspend for 2nd SELECT_DISCARD_PLAY
        // But only cost 2 card should be in looked_cards (cost 4 > 2 remaining)
        {
            assert_eq!(
                state.interaction_stack.last().unwrap().choice_type,
                ChoiceType::SelectDiscardPlay
            );
            let looked_cards = state.core.players[p_idx].looked_cards.clone();
            assert!(
                looked_cards.contains(&cost_2_ids[1]),
                "Should contain 2nd cost 2 card"
            );
            assert!(
                !looked_cards.contains(&cost_4_id),
                "Should NOT contain cost 4 card (4 > 2)"
            );

            let idx = looked_cards
                .iter()
                .position(|&cid| cid == cost_2_ids[1])
                .unwrap();
            state.step(&db, ACTION_BASE_CHOICE + idx as i32).unwrap(); // Select Card
            state.step(&db, ACTION_BASE_CHOICE + 2).unwrap(); // Select Slot 2
        }

        assert_eq!(state.core.players[p_idx].stage[1], cost_2_ids[0]);
        assert_eq!(state.core.players[p_idx].stage[2], cost_2_ids[1]);
        assert!(state.interaction_stack.is_empty(), "Should be finished");
    }
}
