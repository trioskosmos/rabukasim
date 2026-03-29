//! Tool to recreate and analyze slow game conditions
//! 
//! Usage: Run this as a binary to load and analyze captured slow events
//! 
//! Example:
//!   cargo run --example analyze_slow_events -- target/slow_events.json

use engine_rust::core::logic::{CardDatabase, GameState};
use std::collections::HashMap;
use std::fs;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SlowEvent {
    operation: String,
    phase: String,
    duration_ns: u64,
    turn: u16,
    action_taken: i32,
    game_state_json: String,
    board_analysis: Option<BoardAnalysis>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct BoardAnalysis {
    p0_stage_cards: Vec<i32>,
    p1_stage_cards: Vec<i32>,
    p0_live_zone: Vec<i32>,
    p1_live_zone: Vec<i32>,
    p0_granted_abilities: usize,
    p1_granted_abilities: usize,
    p0_hand_size: usize,
    p1_hand_size: usize,
    p0_discard_size: usize,
    p1_discard_size: usize,
    p0_yell_cards: usize,
    p1_yell_cards: usize,
    has_constant_abilities: bool,
    has_color_transforms: bool,
    has_cost_modifiers: bool,
}

fn load_db() -> CardDatabase {
    for path in &[
        "data/cards_vanilla.json",
        "../data/cards_vanilla.json",
        "../../data/cards_vanilla.json",
        "engine_rust_src/data/cards_vanilla.json",
    ] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = true;
            return db;
        }
    }
    panic!("DB not found - looked in: data/cards_vanilla.json, ../data/cards_vanilla.json, ../../data/cards_vanilla.json, engine_rust_src/data/cards_vanilla.json");
}

fn analyze_board_patterns(events: &[SlowEvent]) {
    println!("\n=== BOARD STATE PATTERN ANALYSIS ===\n");
    
    // Group by operation type
    use std::collections::HashMap;
    let mut by_op: HashMap<&str, Vec<&SlowEvent>> = HashMap::new();
    for event in events {
        by_op.entry(&event.operation).or_default().push(event);
    }
    
    for (op, op_events) in by_op {
        println!("--- {} ({} events) ---", op, op_events.len());
        
        // Analyze board characteristics
        let with_analysis: Vec<_> = op_events.iter().filter(|e| e.board_analysis.is_some()).collect();
        if with_analysis.is_empty() {
            println!("  No board analysis data available");
            continue;
        }
        
        // Calculate averages
        let avg_duration = op_events.iter().map(|e| e.duration_ns).sum::<u64>() / op_events.len() as u64;
        let max_duration = op_events.iter().map(|e| e.duration_ns).max().unwrap_or(0);
        println!("  Duration: avg={}μs, max={}μs", avg_duration / 1000, max_duration / 1000);
        
        // Board complexity metrics
        let avg_p0_stage = with_analysis.iter().map(|e| e.board_analysis.as_ref().unwrap().p0_stage_cards.len()).sum::<usize>() / with_analysis.len();
        let avg_p1_stage = with_analysis.iter().map(|e| e.board_analysis.as_ref().unwrap().p1_stage_cards.len()).sum::<usize>() / with_analysis.len();
        let avg_p0_live = with_analysis.iter().map(|e| e.board_analysis.as_ref().unwrap().p0_live_zone.len()).sum::<usize>() / with_analysis.len();
        let avg_p1_live = with_analysis.iter().map(|e| e.board_analysis.as_ref().unwrap().p1_live_zone.len()).sum::<usize>() / with_analysis.len();
        
        println!("  Stage cards: P0={}, P1={}", avg_p0_stage, avg_p1_stage);
        println!("  Live zone: P0={}, P1={}", avg_p0_live, avg_p1_live);
        
        // Active effects
        let with_constant = with_analysis.iter().filter(|e| e.board_analysis.as_ref().unwrap().has_constant_abilities).count();
        let with_transforms = with_analysis.iter().filter(|e| e.board_analysis.as_ref().unwrap().has_color_transforms).count();
        let with_cost_mods = with_analysis.iter().filter(|e| e.board_analysis.as_ref().unwrap().has_cost_modifiers).count();
        
        if with_constant > 0 || with_transforms > 0 || with_cost_mods > 0 {
            println!("  Active effects:");
            if with_constant > 0 {
                println!("    - Constant abilities: {} positions ({}%)", with_constant, with_constant * 100 / with_analysis.len());
            }
            if with_transforms > 0 {
                println!("    - Color transforms: {} positions ({}%)", with_transforms, with_transforms * 100 / with_analysis.len());
            }
            if with_cost_mods > 0 {
                println!("    - Cost modifiers: {} positions ({}%)", with_cost_mods, with_cost_mods * 100 / with_analysis.len());
            }
        }
        
        // Find slowest specific position
        let slowest = op_events.iter().max_by_key(|e| e.duration_ns);
        if let Some(s) = slowest {
            if let Some(ref analysis) = s.board_analysis {
                println!("  Slowest position ({}μs):", s.duration_ns / 1000);
                println!("    P0 stage: {:?}, P1 stage: {:?}", analysis.p0_stage_cards, analysis.p1_stage_cards);
                println!("    P0 live: {:?}, P1 live: {:?}", analysis.p0_live_zone, analysis.p1_live_zone);
                println!("    Granted abilities: P0={}, P1={}", analysis.p0_granted_abilities, analysis.p1_granted_abilities);
                println!("    Yell cards: P0={}, P1={}", analysis.p0_yell_cards, analysis.p1_yell_cards);
            }
        }
        println!();
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let file_path = args.get(1).map(|s| s.as_str()).unwrap_or("target/slow_events.json");
    
    let json_str = fs::read_to_string(file_path).expect("Failed to read slow events file");
    let events: Vec<SlowEvent> = serde_json::from_str(&json_str).expect("Failed to parse JSON");
    
    println!("=== Loaded {} slow events from {} ===\n", events.len(), file_path);
    
    // Show aggregate patterns first
    analyze_board_patterns(&events);
    
    let db = load_db();
    
    // Show top 5 slowest individual events for detailed inspection
    let mut sorted_events = events.clone();
    sorted_events.sort_by(|a, b| b.duration_ns.cmp(&a.duration_ns));
    
    println!("\n=== TOP 5 SLOWEST EVENTS (Detailed) ===\n");
    for (i, event) in sorted_events.iter().take(5).enumerate() {
        println!("--- Event {} ---", i + 1);
        println!("  Operation: {}", event.operation);
        println!("  Phase: {}", event.phase);
        println!("  Turn: {}", event.turn);
        println!("  Duration: {} ns ({} μs)", event.duration_ns, event.duration_ns as f64 / 1000.0);
        println!("  Action taken: {}", event.action_taken);
        
        // Recreate the game state
        match serde_json::from_str::<GameState>(&event.game_state_json) {
            Ok(state) => {
                println!("  State recreated successfully");
                println!("    Current player: {}", state.current_player);
                println!("    Phase: {:?}", state.phase);
                println!("    Turn: {}", state.turn);
                
                // Verify the operation is slow by re-running it
                use std::time::Instant;
                
                match event.operation.as_str() {
                    "get_legal_actions" => {
                        let t = Instant::now();
                        let actions = state.get_legal_action_ids(&db);
                        let elapsed = t.elapsed().as_nanos() as u64;
                        println!("  Rerun get_legal_actions: {} actions found in {} ns", actions.len(), elapsed);
                    }
                    "check_win_condition" => {
                        let mut test_state = state.clone();
                        let t = Instant::now();
                        test_state.check_win_condition();
                        let elapsed = t.elapsed().as_nanos() as u64;
                        println!("  Rerun check_win_condition: {} ns", elapsed);
                    }
                    "sync_all_stats" => {
                        let mut test_state = state.clone();
                        let t = Instant::now();
                        test_state.sync_all_stats(&db);
                        let elapsed = t.elapsed().as_nanos() as u64;
                        println!("  Rerun sync_all_stats: {} ns", elapsed);
                    }
                    op if op.ends_with(":step") => {
                        // Handle phase-specific step operations like "LiveSet:step", "Main:step"
                        let mut test_state = state.clone();
                        // Get legal actions and pick first one to simulate a step
                        let actions = test_state.get_legal_action_ids(&db);
                        if !actions.is_empty() {
                            let action = actions[0];
                            let t = Instant::now();
                            let _ = test_state.step(&db, action);
                            let elapsed = t.elapsed().as_nanos() as u64;
                            println!("  Rerun {} with action {}: {} ns", op, action, elapsed);
                        } else {
                            // Try auto_step if no actions available
                            let t = Instant::now();
                            test_state.auto_step(&db);
                            let elapsed = t.elapsed().as_nanos() as u64;
                            println!("  Rerun {} auto_step: {} ns", op, elapsed);
                        }
                    }
                    _ => println!("  Unknown operation, cannot rerun"),
                }
            }
            Err(e) => {
                println!("  ERROR: Failed to recreate state: {}", e);
            }
        }
        println!();
    }
    
    println!("\nAnalysis complete.");
    println!("To dig deeper into a specific event, you can:");
    println!("  1. Extract the game_state_json from the file");
    println!("  2. Write a custom test that deserializes it and profiles specific functions");
}
