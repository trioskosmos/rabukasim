use crate::core::enums::Phase;
use crate::test_helpers::{create_test_state, load_real_db};

#[test]
fn test_card_874_activation_discards_self_before_energy_charge() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.phase = Phase::Main;
    state.current_player = 0;
    state.ui.silent = true;

    let p_idx = 0usize;
    let card_id = 874;
    let starting_energy = vec![3001, 3002, 3003, 3004, 3005, 3006];
    let energy_deck = vec![9101, 9102, 9103];

    state.players[p_idx].stage = [card_id, -1, -1];
    state.players[p_idx].discard.clear();
    state.players[p_idx].energy_zone = starting_energy.clone().into();
    state.players[p_idx].energy_deck = energy_deck.clone().into();

    state
        .activate_ability(&db, 0, 0)
        .expect("card 874 should activate with 6 energy");

    assert_eq!(
        state.players[p_idx].stage[0],
        -1,
        "card 874 should leave stage as activation cost"
    );
    assert!(
        state.players[p_idx].discard.contains(&card_id),
        "card 874 should be in discard after paying its activation cost"
    );
    assert_eq!(
        state.players[p_idx].energy_zone.len(),
        starting_energy.len() + 1,
        "exactly one energy should be charged"
    );
    assert_eq!(
        state.players[p_idx].energy_deck.len(),
        energy_deck.len() - 1,
        "energy charge should draw exactly one card from the energy deck"
    );
    let last_energy_idx = state.players[p_idx].energy_zone.len() - 1;
    assert!(
        state.players[p_idx].is_energy_tapped(last_energy_idx),
        "charged energy should enter in wait state"
    );
}