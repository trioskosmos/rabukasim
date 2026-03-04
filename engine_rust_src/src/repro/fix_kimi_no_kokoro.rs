#![allow(unused_imports)]
use crate::core::logic::{ChoiceType, CardDatabase, GameState, Phase};

// use serde_json::json;
#[test]
fn test_kimi_no_kokoro_prevention() {
    let db_path = std::path::Path::new("../data/cards_compiled.json");
    if !db_path.exists() {
        println!("Skipping test: cards_compiled.json not found");
        return;
    }
    let json_str = std::fs::read_to_string(db_path).unwrap();
    let db = CardDatabase::from_json(&json_str).unwrap();

    let kimi_no_kokoro_id = 431;
    // ...
    let mut state = GameState::default();

    state.initialize_game(
        vec![101; 48], // Dummy deck
        vec![101; 48],
        vec![1, 2, 3, 4, 5, 6], // Dummy energy
        vec![1, 2, 3, 4, 5, 6],
        vec![], // No initial success lives
        vec![]
    );
    state.debug.debug_mode = true;

    // Force set live card
    state.core.players[0].live_zone[0] = kimi_no_kokoro_id;

    // Give player some dummy cards in hand for the discard cost
    state.core.players[0].hand.push(1);
    state.core.players[0].hand.push(2);

    // Mock performance results to force success
    // We can manually insert a success result into performance_results
    // OR we can rely on do_live_result calculating it.
    // Let's rely on do_live_result. We need to satisfy hearts.
    // Just give the player infinite hearts of all colors.
    for i in 0..7 {
        state.core.players[0].heart_buffs[0].set_color_count(i, 1);
        state.core.players[0].heart_buffs[1].set_color_count(i, 1);
        state.core.players[0].heart_buffs[2].set_color_count(i, 1);
    }

    // We need to run do_performance_phase to generate the result entry?
    // Or we can just mock the entry.
    // do_live_result checks performance_results first.
    state.ui.performance_results.insert(0, serde_json::json!({
        "success": true,
        "lives": [
            {
                "score": 10,
                // "passed": true // calculated in do_live_result if not present?
                // Actually do_live_result recalculates satisfaction: "Judgment Phase"
            }
        ]
    }));

    // Set phase
    state.phase = Phase::LiveResult;
    state.current_player = 0;

    // Run do_live_result
    state.step(&db, 0).unwrap(); // 0 = Confirm/Proceed

    // Rule 1: Card should be in DISCARD, not SUCCESS_LIVES
    // But wait, OnLiveSuccess triggers first (Step 0 in do_live_result).

    // The OnLiveSuccess ability is: DRAW(2); MOVE_TO_DISCARD(1) -> CARD_HAND
    // This requires a choice. So state should be in Response.

    assert_eq!(state.phase, Phase::Response, "Should pause for Discard choice");
    assert_eq!(state.interaction_stack.last().map(|i| i.choice_type).unwrap_or(ChoiceType::None), ChoiceType::SelectHandDiscard);
    assert_eq!(state.interaction_stack.last().map(|i| i.card_id).unwrap_or(0), kimi_no_kokoro_id);

    // Resume properly through the game engine
    state.step(&db, crate::core::logic::ACTION_BASE_CHOICE as i32).unwrap();

    println!("DEBUG: Phase after resumption: {:?}", state.phase);
    println!("DEBUG: Live slot 0: {}", state.core.players[0].live_zone[0]);
    println!("DEBUG: Hand size: {}", state.core.players[0].hand.len());

    // Initial hand was 8 (6 from start + 2 manually added)
    // Ability draws 2 -> 10
    // Ability discards 1 -> 9
    // Turn Start draw (auto-stepped) -> 10
    assert_eq!(state.core.players[0].hand.len(), 10, "Hand size should be 10 (8+2-1+1)");

    // Rule 1 Verification:
    // The card at slot 0 should be gone (-1)
    assert_eq!(state.core.players[0].live_zone[0], -1, "Live card should be removed from zone");

    // It should be in DISCARD (due to Prevention)
    // discard should contain KIMI_NO_KOKORO_ID
    assert!(state.core.players[0].discard.contains(&(kimi_no_kokoro_id as i32)), "Live card should be in discard");

    // It should NOT be in success_lives
    assert!(!state.core.players[0].success_lives.contains(&(kimi_no_kokoro_id as i32)), "Live card should NOT be in success pile");

}
