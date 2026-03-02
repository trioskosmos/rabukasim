use crate::core::logic::{GameState, CardDatabase};
use crate::core::mcts::MCTS;
use crate::core::alphazero_evaluator::HeuristicBaselineEvaluator;
use crate::core::alphazero_encoding::AlphaZeroEncoding;
use crate::core::heuristics::Heuristic;
use std::sync::Arc;

#[test]
fn test_alphazero_baseline_smoke() {
    let mut db = CardDatabase::default();
    // Load minimal cards or use empty for smoke test
    if let Ok(json) = std::fs::read_to_string("../data/cards_compiled.json") {
       if let Ok(loaded_db) = CardDatabase::from_json(&json) {
           db = loaded_db;
       }
    }

    let mut state = GameState::default();
    // Setup a basic valid state
    if !db.members.is_empty() {
        let first_id = *db.members.keys().next().unwrap();
        state.core.players[0].hand.push(first_id); 
    }
    
    // 1. Verify Tensor Encoding
    let tensor = state.to_alphazero_tensor(&db);
    assert!(tensor.len() > 3000, "Tensor size should be ~3400, got {}", tensor.len());
    // Check for NaN or Inf
    for &v in &tensor {
        assert!(v.is_finite(), "Tensor contains non-finite value: {}", v);
    }

    // 2. Verify MCTS with AlphaZero Evaluator
    let evaluator = Arc::new(Box::new(HeuristicBaselineEvaluator) as Box<dyn crate::core::alphazero_evaluator::AlphaZeroEvaluator>);
    let mut mcts = MCTS::with_evaluator(evaluator, 8); // Batch size 8
    
    // Run a few simulations
    // Note: search_parallel usually takes SearchHorizon and Heuristic, 
    // but run_mcts_config is where the evaluator is actually used.
    // We can test get_suggestions or search which usually call run_mcts_config.
    
    // We need a dummy heuristic for the trait, but if evaluator is present, 
    // AlphaZero path is taken in run_mcts_config.
    use crate::core::heuristics::OriginalHeuristic;
    let h = OriginalHeuristic::default();
    
    let (stats, _): (Vec<(i32, f32, u32)>, _) = mcts.run_mcts_config(
        &state, 
        &db, 
        64,     // sims
        0.0,    // timeout
        crate::core::mcts::SearchHorizon::GameEnd(), 
        false,  // shuffle
        true,   // rollout
        |s, d| h.evaluate(s, d, 0, 0, crate::core::heuristics::EvalMode::Normal, None, None)
    );

    assert!(!stats.is_empty(), "MCTS should return at least one suggestion");
    println!("AlphaZero Baseline Suggestion: {:?}", stats[0]);
    
    // Verify visit counts sum up (sims_done in batch mode is sims_done += batch_size)
    let total_visits: u32 = stats.iter().map(|(_, _, v)| v).sum();
    assert!(total_visits > 0, "Total visits should be > 0");
}

#[test]
fn test_alphazero_volatile_flags() {
    let db = CardDatabase::default();
    let mut state = GameState::default();
    
    // 1. Manually set volatile flags
    state.core.players[0].baton_touch_count = 1;
    state.core.players[0].baton_touch_limit = 2;
    state.core.players[0].hand_increased_this_turn = 3;
    state.core.performance_yell_done[0] = true;
    
    let tensor = state.to_alphazero_tensor(&db);
    
    // Verify offsets (assuming me=0)
    assert_eq!(tensor[12], 1.0, "Baton touch count (me)");
    assert_eq!(tensor[13], 2.0, "Baton touch limit (me)");
    assert_eq!(tensor[16], 3.0 / 5.0, "Hand increased (me)");
    assert_eq!(tensor[18], 1.0, "Performance yell done (me)");
    
    // 2. Verify Spent Ability Bit
    // Add a card with a once-per-turn ability
    let mut db = CardDatabase::default();
    let mut state = GameState::default();
    
    let member = crate::core::logic::CardDatabase::default().members.get(&103).cloned().unwrap_or_else(|| {
        let mut m = crate::core::logic::MemberCard::default();
        m.card_id = 103;
        m.char_id = 103; // Correctly set char_id for identity check
        m.abilities.push(crate::core::logic::Ability {
            trigger: crate::core::enums::TriggerType::OnPlay,
            is_once_per_turn: true,
            bytecode: vec![1, 2, 3],
            ..Default::default()
        });
        m
    });
    db.members.insert(103, member.clone());
    
    state.core.players[0].stage[0] = 103;
    
    // Test NOT SPENT
    let tensor_not_spent = state.to_alphazero_tensor(&db);
    // Entity 0 (Stage Slot 0):
    // Global(25) + Meta(16) + Identity(16) + Stats(10) = 67 offset to Bytecode.
    // Ability Header: [Trigger, IsOnce, Len, IsSpent] -> IsSpent is at 67 + 3 = 70.
    assert_eq!(tensor_not_spent[70], 0.0, "Ability should not be spent");
    
    // 3. Verify Identity Metadata
    // Meta block is 16 floats. Type starts at 25 + 16 = 41.
    assert_eq!(tensor_not_spent[41], 1.0, "Type should be Member (1.0)");
    assert_eq!(tensor_not_spent[42], 103.0, "CharID should be 103");
    
    // 4. Test SPENT
    let uid = crate::core::logic::interpreter::get_ability_uid(0, 103, 0);
    state.core.players[0].used_abilities.push(uid);
    
    let tensor_spent = state.to_alphazero_tensor(&db);
    assert_eq!(tensor_spent[70], 1.0, "Ability should be spent");
}
