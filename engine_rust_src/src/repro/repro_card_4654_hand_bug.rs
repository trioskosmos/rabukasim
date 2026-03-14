use engine_rust::core::enums::*;
use engine_rust::core::logic::*;
use engine_rust::test_helpers::{load_real_db, TestUtils};

#[test]
fn test_repro_card_4654_hand_clearing() {
    let mut state = GameState::default();
    let mut db = load_real_db().clone();

    // Create a mock live card that meets the filter: Type:Live, Group:3 (Liella), Hearts >= 8
    let mut mock_live = LiveCard::default();
    mock_live.card_id = 51001;
    mock_live.groups = vec![3];
    mock_live.hearts_board.set_color_count(1, 8); // 8 red hearts
    db.lives.insert(51001, mock_live.clone());
    db.lives_vec[51001 as usize % LOGIC_ID_MASK as usize] = Some(mock_live);

    state.players[0].player_id = 0;
    state.players[1].player_id = 1;
    state.phase = Phase::Main;

    // Hand: 5 cards
    state.set_hand(0, &[3001, 3002, 3003, 3004, 3005]);
    // Deck: 4 cards. Use the mock live card we just created!
    state.set_deck(0, &[51001, 51001, 51001, 51001]);

    let card_4654_id = 4654; // Card No: PL!N-pb1-028-L
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_4654_id,
        ..AbilityContext::default()
    };

    // Tang Keke Bytecode: [41, 4, 121, 6, 1, 0, 0, 0]
    // 41 = LOOK_AND_CHOOSE
    // 4 = v (look 4)
    // 121 = a (attr/filter)
    // 6 = s (target slot = Hand = 6)
    let bytecode = vec![
        O_LOOK_AND_CHOOSE as i32,
        4,
        121,
        6,
        O_RETURN as i32,
        0,
        0,
        0,
    ];

    println!("DEBUG: Initial hand: {:?}", state.players[0].hand);
    assert_eq!(state.players[0].hand.len(), 5);

    // Execute bytecode
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // The engine should now have suspended for interaction if logic proceeds correctly to look at deck.
    // BUT! Due to the bug, it likely emptied the hand already into looked_cards.

    println!(
        "DEBUG: Hand after resolution: {:?}",
        state.players[0].hand
    );
    println!(
        "DEBUG: Looked cards: {:?}",
        state.players[0].looked_cards
    );

    // BUG CONFIRMATION:
    // If hand is empty and looked_cards contains [3001, 3002, 3003, 3004, 3005], the bug is confirmed.
    assert_eq!(
        state.players[0].hand.len(),
        5,
        "Hand was EMPTIED! Looked cards took them? {:?}, Hand: {:?}",
        state.players[0].looked_cards,
        state.players[0].hand
    );
    assert_eq!(
        state.players[0].looked_cards.len(),
        4,
        "Should have looked at 4 cards from DECK, not: {:?}",
        state.players[0].looked_cards
    );
}
