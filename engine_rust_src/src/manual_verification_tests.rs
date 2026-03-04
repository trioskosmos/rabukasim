use crate::core::logic::*;
use crate::core::enums::*;
use crate::test_helpers::Action;

fn load_test_db() -> CardDatabase {
    let paths = ["data/cards_compiled.json", "../data/cards_compiled.json"];
    for path in paths {
        if let Ok(json_str) = std::fs::read_to_string(path) {
            return CardDatabase::from_json(&json_str).expect("Failed to parse CardDatabase");
        }
    }
    panic!("Could not find cards_compiled.json in any of the expected locations");
}

#[test]
fn test_strict_condition_logic_no_bypass() {
    let mut state = GameState::default();
    state.phase = Phase::Main;

    let db = load_test_db();

    // Reset bypass mode to ensure strictness
    state.debug.debug_ignore_conditions = false;

    let p0 = 0;
    // Give enough energy to play any card
    for _ in 0..10 { state.players[p0].energy_zone.push(40000); }
    state.players[p0].tapped_energy_mask = 0;

    // Put card 278 in hand (PL!HS-PR-019-PR)
    state.players[p0].hand.push(4135);

    // SETUP FAILURE: Put non-heart 04 cards on top of deck
    state.players[p0].deck.clear();
    state.players[p0].deck.push(1);
    state.players[p0].deck.push(11);
    state.players[p0].deck.push(12);

    // Play card 278 (Action ID for hand 0, slot 0 is 1)
    let res = state.step(&db, (ACTION_BASE_HAND + 0) as i32);
    assert!(res.is_ok(), "Play should succeed with enough energy, res: {:?}", res);

    // Check state: 3 cards should be in discard from the deck
    assert_eq!(state.players[p0].discard.len(), 3);

    // Buff should NOT be applied because cards were not heart 04 members
    assert_eq!(state.players[p0].heart_buffs[0].get_color_count(4), 0, "Buff should not be applied if condition fails");

    // SETUP SUCCESS
    let mut state = GameState::default();
    state.phase = Phase::Main;
    state.players[p0].energy_zone = vec![40000; 10].into();
    state.players[p0].tapped_energy_mask = 0;
    state.players[p0].hand.push(4135);
    state.players[p0].deck.push(4135);
    state.players[p0].deck.push(4135);
    state.players[p0].deck.push(4135);

    let res = state.step(&db, (ACTION_BASE_HAND + 0) as i32);
    assert!(res.is_ok());

    // Buff SHOULD be applied
    assert_eq!(state.players[p0].heart_buffs[0].get_color_count(4), 1);
}

#[test]
fn test_effect_dissipation_manual() {
    let mut state = GameState::default();
    state.phase = Phase::Main;
    let p0 = 0;

    // Manually add a buff
    state.players[p0].blade_buffs[0] = 5;
    assert_eq!(state.players[p0].blade_buffs[0], 5);

    // Simulate Turn Start (which calls untap_all in Active Phase)
    state.phase = Phase::Active;
    let db = load_test_db();

    state.do_active_phase(&db);

    // Buff should be cleared
    assert_eq!(state.players[p0].blade_buffs[0], 0, "Buff should be cleared during Active Phase");
}
