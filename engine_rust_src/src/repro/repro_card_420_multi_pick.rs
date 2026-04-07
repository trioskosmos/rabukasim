use crate::core::enums::Phase;
use crate::core::generated_constants::{
    ACTION_BASE_CHOICE, ACTION_BASE_HAND, ACTION_BASE_STAGE_SLOTS,
};
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::logic::*;
use crate::test_helpers::load_real_db;

/// Regression test for PL!S-bp2-006-P / card 420.
/// The effect should allow at most two discard picks, and members placed by it
/// should enter the stage active unless the card text says otherwise.
#[test]
fn test_repro_card_420_multi_pick_from_discard() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;
    state.debug.debug_mode = false;

    let p_idx = 0usize;
    state.current_player = p_idx as u8;
    state.phase = Phase::Main;

    let card_420_id = 420;
    let card = db
        .get_member(card_420_id)
        .expect("Card 420 not found in DB");
    assert!(!card.abilities.is_empty(), "Card 420 should have abilities");

    let mut discard_members: Vec<i32> = Vec::new();
    for (_card_no, &id) in db.card_no_to_id.iter() {
        if id == card_420_id {
            continue;
        }
        if let Some(m) = db.get_member(id) {
            if m.cost <= 2 && m.abilities.is_empty() {
                discard_members.push(id);
            }
        }
        if discard_members.len() >= 3 {
            break;
        }
    }
    assert!(
        discard_members.len() >= 3,
        "Need at least 3 vanilla low-cost members in DB"
    );

    state.players[p_idx].stage = [-1, -1, -1];
    state.players[p_idx].hand = vec![card_420_id].into();
    state.players[p_idx].discard = discard_members.clone().into();
    state.players[p_idx].deck = vec![9999; 5].into();
    state.players[p_idx].energy_zone = vec![9000; 20].into();
    state.players[p_idx].energy_deck = vec![9000; 20].into();

    state.step(&db, ACTION_BASE_HAND + 0).unwrap();
    state.step(&db, ACTION_BASE_CHOICE + 0).unwrap();

    assert!(
        matches!(
            state.interaction_stack.last().map(|pi| pi.choice_type),
            Some(crate::core::enums::ChoiceType::SelectDiscardPlay)
        ),
        "First discard selection prompt should appear"
    );

    state.step(&db, ACTION_BASE_CHOICE + 0).unwrap();
    let slot_1 = state.players[p_idx]
        .stage
        .iter()
        .position(|&c| c == -1)
        .expect("Need an empty slot for the first discard placement");
    state
        .step(&db, ACTION_BASE_STAGE_SLOTS + slot_1 as i32)
        .unwrap();

    assert!(
        matches!(
            state.interaction_stack.last().map(|pi| pi.choice_type),
            Some(crate::core::enums::ChoiceType::SelectDiscardPlay)
        ),
        "A second discard selection prompt should appear"
    );

    state.step(&db, ACTION_BASE_CHOICE + 0).unwrap();
    let slot_2 = state.players[p_idx]
        .stage
        .iter()
        .position(|&c| c == -1)
        .expect("Need an empty slot for the second discard placement");
    state
        .step(&db, ACTION_BASE_STAGE_SLOTS + slot_2 as i32)
        .unwrap();

    assert!(
        state.interaction_stack.is_empty(),
        "The effect should stop after two discard placements"
    );

    let picked_members: Vec<i32> = state.players[p_idx]
        .stage
        .iter()
        .enumerate()
        .filter_map(|(slot_idx, &cid)| {
            if slot_idx != 0 && discard_members.contains(&cid) {
                Some(cid)
            } else {
                None
            }
        })
        .collect();
    assert_eq!(
        picked_members.len(),
        2,
        "Exactly two discard members should be placed"
    );
    for (slot_idx, &cid) in state.players[p_idx].stage.iter().enumerate() {
        if slot_idx != 0 && discard_members.contains(&cid) {
            assert!(
                !state.players[p_idx].is_tapped(slot_idx),
                "Card 420 should place summoned members active unless the text says wait"
            );
        }
    }
}

#[test]
fn test_repro_card_420_second_pick_can_be_skipped() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;
    state.debug.debug_mode = false;

    let p_idx = 0usize;
    state.current_player = p_idx as u8;
    state.phase = Phase::Main;

    let card_420_id = 420;
    let card = db
        .get_member(card_420_id)
        .expect("Card 420 not found in DB");
    assert!(!card.abilities.is_empty(), "Card 420 should have abilities");

    let mut discard_members: Vec<i32> = Vec::new();
    for (_card_no, &id) in db.card_no_to_id.iter() {
        if id == card_420_id {
            continue;
        }
        if let Some(m) = db.get_member(id) {
            if m.cost == 2 && m.abilities.is_empty() {
                discard_members.push(id);
            }
        }
        if discard_members.len() >= 3 {
            break;
        }
    }
    assert!(
        discard_members.len() >= 3,
        "Need at least 3 vanilla cost-2 members in DB"
    );

    state.players[p_idx].stage = [discard_members[2], -1, -1];
    state.players[p_idx].hand = vec![card_420_id].into();
    state.players[p_idx].discard = discard_members.clone().into();
    state.players[p_idx].deck = vec![9999; 5].into();
    state.players[p_idx].energy_zone = vec![9000; 20].into();
    state.players[p_idx].energy_deck = vec![9000; 20].into();

    state.step(&db, ACTION_BASE_HAND + 0).unwrap();
    state.step(&db, ACTION_BASE_CHOICE + 0).unwrap();

    assert!(
        matches!(
            state.interaction_stack.last().map(|pi| pi.choice_type),
            Some(crate::core::enums::ChoiceType::SelectDiscardPlay)
        ),
        "First discard selection prompt should appear"
    );

    state.step(&db, ACTION_BASE_CHOICE + 0).unwrap();
    assert!(
        matches!(
            state.interaction_stack.last().map(|pi| pi.choice_type),
            Some(crate::core::enums::ChoiceType::SelectStageEmpty)
        ),
        "Discard-play placement should only target empty stage slots"
    );

    let mut actions: Vec<i32> = Vec::new();
    state.generate_legal_actions(&db, p_idx, &mut actions);
    assert!(
        !actions.contains(&ACTION_BASE_STAGE_SLOTS),
        "Occupied stage slot 0 should not be offered"
    );
    assert!(
        actions.contains(&(ACTION_BASE_STAGE_SLOTS + 1)),
        "Empty stage slot 1 should be offered"
    );
    assert!(
        actions.contains(&(ACTION_BASE_STAGE_SLOTS + 2)),
        "Empty stage slot 2 should be offered"
    );

    let slot_1 = state.players[p_idx]
        .stage
        .iter()
        .position(|&c| c == -1)
        .expect("Need an empty slot for the first discard placement");
    state
        .step(&db, ACTION_BASE_STAGE_SLOTS + slot_1 as i32)
        .unwrap();

    assert!(
        matches!(
            state.interaction_stack.last().map(|pi| pi.choice_type),
            Some(crate::core::enums::ChoiceType::SelectDiscardPlay)
        ),
        "A second discard selection prompt should appear"
    );

    state.step(&db, ACTION_BASE_CHOICE + CHOICE_DONE as i32).unwrap();

    assert!(
        state.interaction_stack.is_empty(),
        "Choosing no second card should finish the effect"
    );
    assert!(
        state.players[p_idx].looked_cards.is_empty(),
        "Discard-play cleanup should clear the looked-cards buffer"
    );

    let picked_members: Vec<i32> = state.players[p_idx]
        .stage
        .iter()
        .copied()
        .filter(|cid| discard_members.contains(cid))
        .collect();
    assert_eq!(
        picked_members.len(),
        1,
        "Only one discard member should be placed when the second choice is skipped"
    );
}
