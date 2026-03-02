use crate::test_helpers::{create_test_state, load_real_db};
use crate::core::logic::*;

#[test]
fn test_win_by_lives() {
    let _db = load_real_db();
    let mut state = create_test_state();

    // Player 0 has 3 success lives (START:DASH!! ID 137)
    state.core.players[0].success_lives = vec![137, 137, 137].into();
    state.core.players[1].success_lives = vec![].into();

    state.check_win_condition();

    assert_eq!(state.phase, Phase::Terminal);
    assert_eq!(state.get_winner(), 0);
}

#[test]
fn test_draw_simultaneous_lives() {
    let _db = load_real_db();
    let mut state = create_test_state();

    // Simultaneous reach 3 lives
    state.core.players[0].success_lives = vec![137, 137, 137].into();
    state.core.players[1].success_lives = vec![137, 137, 137].into();

    state.check_win_condition();

    assert_eq!(state.phase, Phase::Terminal);
    assert_eq!(state.get_winner(), 2, "Rule 1.2.1.2: Simultaneous 3+ lives is a Draw (2)");
}

#[test]
fn test_true_draw_lives_and_score_equal() {
    let _db = load_real_db();
    let mut state = create_test_state();

    state.core.players[0].success_lives = vec![137, 137, 137].into();
    state.core.players[1].success_lives = vec![137, 137, 137].into();

    state.core.players[0].score = 25;
    state.core.players[1].score = 25;

    state.check_win_condition();

    assert_eq!(state.get_winner(), 2, "Should be a true draw (2)");
}


#[test]
fn test_deck_out_not_yet_implemented() {
    // Verifying current behavior: Deck out doesn't cause immediate loss yet
    let _db = load_real_db();
    let mut state = create_test_state();
    state.core.players[0].deck = vec![].into();
    state.core.players[0].discard = vec![].into();

    state.draw_cards(0, 1);

    assert_ne!(state.phase, Phase::Terminal, "Deck out logic NOT in game.rs yet");
}
