
use crate::core::logic::*;

const TEST_CARDS: &str = r#"{
    "member_db": {
        "0": {
            "card_id": 0,
            "card_no": "TEST-001",
            "name": "Test Member",
            "cost": 0,
            "hearts": [0, 0, 0, 0, 0, 0, 0],
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
            "blades": 0,
            "groups": [],
            "units": [],
            "abilities": [],
            "rare": "R",
            "volume_icons": 0,
            "draw_icons": 0
        }
    },
    "live_db": {}
}"#;

#[test]
fn test_baton_pass_restriction() {
    let db = CardDatabase::from_json(TEST_CARDS).unwrap();
    let mut state = GameState { core: CoreGameState { players: [
            PlayerState {
                player_id: 0,
                hand: vec![0, 0].into(), // Two test members
                deck: vec![0].into(),    // Non-empty deck to avoid Terminal
                ..PlayerState::default()
            },
            PlayerState {
                player_id: 1,
                deck: vec![0].into(),    // Non-empty deck to avoid Terminal
                ..PlayerState::default()
            },
        ],
        phase: Phase::Main,
        ..CoreGameState::default() }, ..GameState::default() };

    // 1. First play to slot 0 should succeed
    state.play_member(&db, 0, 0).expect("First play should succeed");
    assert_eq!(state.core.players[0].stage[0], 0);
    assert!(state.core.players[0].is_moved(0));

    // 2. Second play (Baton Pass) to the SAME slot in the SAME turn should fail (Rule 9.6.2.1.2.1)
    let result = state.play_member(&db, 0, 0);
    assert!(result.is_err(), "Second play to same slot should fail this turn");
    assert_eq!(result.unwrap_err(), "Already played/moved to this slot this turn");

    // 3. get_legal_actions_into should also mask out slot 0
    let mut mask = vec![false; 2000];
    state.get_legal_actions_into(&db, 0, &mut mask);

    // Action ID for hand_idx 0, slot 0
    let aid_0 = (ACTION_BASE_HAND + 0 * 3 + 0) as usize;
    assert!(!mask[aid_0], "Play to slot 0 should be masked out in legal actions");

    // Action ID for hand_idx 0, slot 1
    let aid_1 = (ACTION_BASE_HAND + 0 * 3 + 1) as usize;
    assert!(mask[aid_1], "Play to slot 1 should still be legal");

    // 4. End turn and start new turn
    state.end_main_phase(&db); // This advances to next player's Active phase (if first player)

    // Fast forward back to Player 0's Main Phase
    state.current_player = 0;
    state.phase = Phase::Main;
    state.core.players[0].untap_all(); // This should reset moved_members_this_turn

    assert!(!state.core.players[0].is_moved(0));

    // 5. Now Baton Pass to slot 0 should be legal
    state.get_legal_actions_into(&db, 0, &mut mask);
    assert!(mask[aid_0], "Play to slot 0 should be legal in the next turn");

    state.play_member(&db, 0, 0).expect("Baton pass in next turn should succeed");
    assert_eq!(state.core.players[0].baton_touch_count, 1);
}
