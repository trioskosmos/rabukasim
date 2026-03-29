//! Performance test for ability-heavy board states

use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::models::Phase;
use engine_rust::core::enums::TriggerType;
use std::time::Instant;

fn load_full_db() -> CardDatabase {
    // Load the full database with abilities
    let json = std::fs::read_to_string("data/cards.json")
        .or_else(|_| std::fs::read_to_string("../data/cards.json"))
        .expect("Card database not found");
    CardDatabase::from_json(&json).expect("Failed to parse database")
}

/// Test performance with 3 stage cards that have constant abilities
#[test]
fn test_performance_with_constant_abilities() {
    let db = load_full_db();
    
    // Find cards with constant abilities
    let cards_with_constants: Vec<i32> = db.members.iter()
        .filter(|(_, m)| m.abilities.iter().any(|a| a.trigger == TriggerType::Constant))
        .map(|(id, _)| *id)
        .take(3)
        .collect();
    
    if cards_with_constants.len() < 3 {
        println!("Not enough cards with constant abilities found");
        return;
    }
    
    let mut state = GameState::default();
    let deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    let lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    
    state.initialize_game(
        deck.clone(), deck.clone(),
        energy.clone(), energy.clone(),
        lives.clone(), lives.clone()
    );
    state.ui.silent = true;
    
    // Place cards with constant abilities on stage
    for (i, &cid) in cards_with_constants.iter().enumerate() {
        state.players[0].stage[i] = cid;
    }
    
    // Add some live cards
    for (i, &cid) in lives.iter().take(3).enumerate() {
        state.players[0].live_zone[i] = cid;
    }
    
    // Time the performance phase
    state.phase = Phase::PerformanceP1;
    state.current_player = 0;
    
    let t = Instant::now();
    state.do_performance_phase(&db);
    let elapsed = t.elapsed().as_micros();
    
    println!("Performance phase with 3 constant abilities: {} μs", elapsed);
    
    // Should complete in reasonable time
    assert!(elapsed < 1000, "Performance phase took too long: {} μs", elapsed);
}

/// Test performance with granted abilities
#[test]
fn test_performance_with_granted_abilities() {
    let db = load_full_db();
    
    let mut state = GameState::default();
    let deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    let lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    
    state.initialize_game(
        deck.clone(), deck.clone(),
        energy.clone(), energy.clone(),
        lives.clone(), lives.clone()
    );
    state.ui.silent = true;
    
    // Get some member cards
    let member_ids: Vec<i32> = db.members.keys().copied().take(3).collect();
    
    // Place cards on stage
    for (i, &cid) in member_ids.iter().enumerate() {
        state.players[0].stage[i] = cid;
    }
    
    // Add granted abilities (simulating ability-granting effects)
    for (i, &target_cid) in member_ids.iter().enumerate() {
        // Grant an ability from one card to another
        if i > 0 {
            state.players[0].granted_abilities.push((target_cid, member_ids[0], 0));
        }
    }
    
    // Add live cards
    for (i, &cid) in lives.iter().take(3).enumerate() {
        state.players[0].live_zone[i] = cid;
    }
    
    state.phase = Phase::PerformanceP1;
    state.current_player = 0;
    
    let t = Instant::now();
    state.do_performance_phase(&db);
    let elapsed = t.elapsed().as_micros();
    
    println!("Performance phase with granted abilities: {} μs", elapsed);
    
    assert!(elapsed < 2000, "Performance phase took too long: {} μs", elapsed);
}

/// Test LiveSet:step with full board
#[test]
fn test_liveset_step_with_full_board() {
    let db = load_full_db();
    
    let mut state = GameState::default();
    let deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    let lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    
    state.initialize_game(
        deck.clone(), deck.clone(),
        energy.clone(), energy.clone(),
        lives.clone(), lives.clone()
    );
    state.ui.silent = true;
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    
    // Place cards on stage with abilities
    let cards_with_abilities: Vec<i32> = db.members.iter()
        .filter(|(_, m)| !m.abilities.is_empty())
        .map(|(id, _)| *id)
        .take(3)
        .collect();
    
    for (i, &cid) in cards_with_abilities.iter().enumerate() {
        state.players[0].stage[i] = cid;
    }
    
    // Set up live zone
    for (i, &cid) in lives.iter().take(2).enumerate() {
        state.players[0].live_zone[i] = cid;
    }
    
    // Sync stats to populate caches
    state.sync_all_stats(&db, 0);
    
    // Time the LiveSet:step (action 0 ends the phase)
    let t = Instant::now();
    let _ = state.step(&db, 0);
    let elapsed = t.elapsed().as_micros();
    
    println!("LiveSet:step with full board: {} μs", elapsed);
    
    assert!(elapsed < 5000, "LiveSet:step took too long: {} μs", elapsed);
}
