
use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::core::logic::*;
// use std::collections::HashMap;

fn create_mini_db_with_bytecode(bc: Vec<i32>) -> CardDatabase {
    let mut db = CardDatabase::default();
    let mut m = MemberCard {
        card_id: 101,
        card_no: "MINI-101".to_string(),
        name: "Mini Card".to_string(),
        cost: 2,
        ..Default::default()
    };
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        bytecode: bc,
        ..Default::default()
    });
    db.members.insert(101, m.clone());
    db.members_vec[(101 as usize) & LOGIC_ID_MASK as usize] = Some(m);
    db
}

fn create_mini_state() -> GameState {
    let mut state = GameState::default();
    state.core.players[0].player_id = 0;
    state.core.players[1].player_id = 1;
    state.phase = Phase::Main;
    state.ui.silent = false;
    // Place the card on stage so activate_ability_with_choice can find it
    state.core.players[0].stage[0] = 101;
    state
}

#[test]
fn mini_test_o_pay_energy_resumption() {
    // Bytecode: PAY_ENERGY(1), DRAW(1), RETURN
    let bc = vec![64, 1, 0, 0, 10, 1, 0, 1, 1, 0, 0, 0];
    let db = create_mini_db_with_bytecode(bc);
    let mut state = create_mini_state();

    // Setup energy (2 untapped, need 1 -> should suspend for choice)
    state.core.players[0].tapped_energy_mask = 0;

    // Populate deck so DRAW works
    state.core.players[0].deck.extend(vec![1, 2, 3, 4, 5]);

    // Activate the ability at slot 0, ability 0
    state.activate_ability_with_choice(&db, 0, 0, -1, 0).unwrap();

    assert_eq!(state.phase, Phase::Response, "Should suspend for PAY_ENERGY selection");
    assert_eq!(state.interaction_stack.last().map(|i| i.effect_opcode).unwrap_or(0), 64, "Pending opcode should be O_PAY_ENERGY");

    // Resume with SelectResponseSlot action
    state.step(&db, Action::SelectResponseSlot { slot_idx: 0 }.id() as i32).unwrap();

    assert!(state.core.players[0].is_energy_tapped(0), "Energy should be tapped");
    assert_eq!(state.core.players[0].hand.len(), 1, "Should have resumed and drawn a card");
    assert_eq!(state.phase, Phase::Main, "Should return to Main phase");
}

#[test]
fn mini_test_o_select_mode_resumption() {
    // Bytecode: SELECT_MODE(2 choices), jump targets, Option 1: DRAW(1)+RETURN, Option 2: DRAW(2)+RETURN
    let bc = vec![
        30, 2, 12, 20, // SELECT_MODE, v=2, Jmp0=12, Jmp1=20
        3, 0, 0, 0,  // Option 1 -> instruction 3 (*4 = IP 12)
        5, 0, 0, 0,  // Option 2 -> instruction 5 (*4 = IP 20)
        10, 1, 0, 1, // IP 12: DRAW(1)
        1, 0, 0, 0,  // IP 16: RETURN
        10, 2, 0, 1, // IP 20: DRAW(2)
        1, 0, 0, 0   // IP 24: RETURN
    ];
    let db = create_mini_db_with_bytecode(bc);
    let mut state = create_mini_state();

    // Populate deck so DRAW works
    state.core.players[0].deck.extend(vec![1, 2, 3, 4, 5]);

    // Activate the ability at slot 0, ability 0
    state.activate_ability_with_choice(&db, 0, 0, -1, 0).unwrap();

    assert_eq!(state.phase, Phase::Response, "Should suspend for SELECT_MODE");
    assert_eq!(state.interaction_stack.last().map(|i| i.effect_opcode).unwrap_or(0), 30, "Pending opcode should be O_SELECT_MODE");

    // Pick Option 2 (choice_idx=1)
    state.step(&db, Action::SelectChoice { choice_idx: 1 }.id() as i32).unwrap();

    assert_eq!(state.core.players[0].hand.len(), 2, "Should have picked Option 2 and drawn 2 cards");
    assert_eq!(state.phase, Phase::Main, "Should return to Main phase");
}
