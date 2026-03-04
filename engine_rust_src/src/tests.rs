use crate::core::logic::*;
const TEST_CARDS: &str = r#"{
    "member_db": {
        "0": {
            "card_id": 0,
            "card_no": "TEST-001",
            "name": "Test Member",
            "cost": 2,
            "hearts": [1, 0, 0, 0, 0, 0, 0],
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
            "blades": 1,
            "groups": [],
            "units": [],
            "abilities": [],
            "rare": "R",
            "volume_icons": 0,
            "draw_icons": 0
        }
    },
    "live_db": {
        "11000": {
            "card_id": 11000,
            "card_no": "LIVE-001",
            "name": "Test Live",
            "score": 1,
            "required_hearts": [1, 0, 0, 0, 0, 0, 0],
            "abilities": [],
            "groups": [],
            "units": [],
            "volume_icons": 0,
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0]
        }
    }
}"#;

#[test]
fn test_database_load() {
    let db = CardDatabase::from_json(TEST_CARDS).unwrap();
    assert_eq!(db.members.len(), 1);
    assert_eq!(db.lives.len(), 1);
    assert_eq!(db.members[&0].name, "Test Member");
}

#[test]
fn test_game_initialization() {
    let _db = CardDatabase::from_json(TEST_CARDS).unwrap();
    let mut state = GameState {
        core: CoreGameState {
            players: [
                PlayerState {
                    player_id: 0,
                    ..PlayerState::default()
                },
                PlayerState {
                    player_id: 1,
                    ..PlayerState::default()
                },
            ],
            ..CoreGameState::default()
        },
        ..GameState::default()
    };

    state.initialize_game(
        vec![0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 11000], // P0 Main (10 members + 1 live)
        vec![0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 11000], // P1 Main
        vec![0, 0, 0, 0, 0],                       // P0 Energy
        vec![0, 0, 0, 0, 0],                       // P1 Energy
        Vec::new(),
        Vec::new(),
    );

    assert_eq!(state.players[0].hand.len(), 6);
    assert_eq!(state.players[0].energy_zone.len(), 3);
    assert_eq!(state.players[0].live_zone, [-1; 3]);
    assert_eq!(state.players[1].live_zone, [-1; 3]);
    // Lives are shuffled into the main deck (may be drawn into hand)
    assert!(
        state.players[0].deck.contains(&11000) || state.players[0].hand.contains(&11000)
    );
}

#[test]
fn test_play_member() {
    let db = CardDatabase::from_json(TEST_CARDS).unwrap();
    let mut state = GameState {
        core: CoreGameState {
            players: [
                PlayerState {
                    player_id: 0,
                    hand: vec![0].into(),
                    energy_zone: vec![0, 0].into(),
                    tapped_energy_mask: 0,
                    ..PlayerState::default()
                },
                PlayerState {
                    player_id: 1,
                    ..PlayerState::default()
                },
            ],
            phase: Phase::Main,
            ..CoreGameState::default()
        },
        ..GameState::default()
    };

    // Play card 0 (cost 2) to slot 0
    state.play_member(&db, 0, 0).unwrap();

    assert_eq!(state.players[0].stage[0], 0);
    assert_eq!(state.players[0].hand.len(), 0);
    assert_eq!(state.players[0].tapped_energy_mask.count_ones(), 2);
}
