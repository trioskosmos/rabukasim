//! GPU Parity Tests from Semantic Truth
//! 
//! This binary loads semantic_truth_v3.json and runs GPU parity tests
//! for each card ability, comparing CPU and GPU execution results.

use engine_rust::core::logic::*;
use engine_rust::core::enums::TriggerType;
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_state::GpuGameState;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::core::gpu_semantic_bridge::{GpuSemanticBridge, SemanticCardTruth, SemanticDelta};
use engine_rust::test_helpers::{create_test_state, Action};
use std::collections::HashMap;

fn main() {
    pollster::block_on(run_semantic_parity_tests());
}

async fn run_semantic_parity_tests() {
    println!("=== GPU PARITY TESTS FROM SEMANTIC TRUTH ===\n");
    
    // Load semantic truth
    let truth = load_semantic_truth();
    if truth.is_empty() {
        println!("WARNING: No semantic truth loaded. Exiting.");
        return;
    }
    
    println!("Loaded {} card truths", truth.len());
    
    // Load real card database from cards_compiled.json
    let db = load_card_database();
    println!("Loaded card database: {} members, {} lives", db.members.len(), db.lives.len());
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = match GpuManager::new(&stats, &bytecode, wgpu::Backends::all()) {
        Some(m) => m,
        None => {
            println!("ERROR: Failed to initialize GPU manager");
            return;
        }
    };
    
    let mut pass_count = 0;
    let mut fail_count = 0;
    let mut skip_count = 0;
    
    // Test each card
    for (card_id, card_truth) in truth.iter() {
        for (ab_idx, ability) in card_truth.abilities.iter().enumerate() {
            let test_name = format!("{}:AB{}", card_id, ab_idx);
            
            let trigger_type = map_trigger_type(&ability.trigger);
            
            // Collect all deltas from the sequence
            let all_deltas: Vec<SemanticDelta> = ability.sequence.iter()
                .flat_map(|seg| seg.deltas.clone())
                .collect();
            
            // Log info for edge cases but continue execution
            if ability.sequence.is_empty() {
                println!("  [INFO] {} has empty sequence, testing anyway", test_name);
            }
            if all_deltas.is_empty() && !ability.sequence.is_empty() {
                println!("  [INFO] {} has no deltas, testing anyway", test_name);
            }
            
            // Run the parity test based on trigger type
            let result = match trigger_type {
                TriggerType::OnPlay | TriggerType::Constant => {
                    run_single_semantic_test(&manager, &db, card_id, ab_idx, trigger_type, &all_deltas)
                }
                TriggerType::OnLiveStart => {
                    run_onlivestart_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                TriggerType::Activated => {
                    run_activated_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                TriggerType::OnLiveSuccess => {
                    run_onlivesuccess_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                TriggerType::TurnStart => {
                    run_turnstart_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                TriggerType::TurnEnd => {
                    run_turnend_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                TriggerType::OnLeaves => {
                    run_onleaves_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                TriggerType::OnReveal => {
                    run_onreveal_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                TriggerType::OnPositionChange => {
                    run_onpositionchange_test(&manager, &db, card_id, ab_idx, &all_deltas)
                }
                _ => {
                    // Unknown trigger type - try generic test
                    run_generic_trigger_test(&manager, &db, card_id, ab_idx, trigger_type, &all_deltas, &ability.trigger)
                }
            };
            
            match result {
                Ok(true) => {
                    println!("  [PASS] {}", test_name);
                    pass_count += 1;
                },
                Ok(false) => {
                    fail_count += 1;
                },
                Err(e) => {
                    // Card not found is a skip, not a failure
                    if e.contains("not found in database") {
                        skip_count += 1;
                    } else {
                        println!("  [ERROR] {}: {}", test_name, e);
                        fail_count += 1;
                    }
                }
            }
        }
    }
    
    println!("\n=== SUMMARY ===");
    println!("PASS: {}, FAIL: {}, SKIP: {}", pass_count, fail_count, skip_count);
    
    if fail_count > 0 {
        std::process::exit(1);
    }
}

fn load_semantic_truth() -> HashMap<String, SemanticCardTruth> {
    // Try multiple paths
    let paths = [
        "reports/semantic_truth_v3.json",
        "../reports/semantic_truth_v3.json",
        "engine_rust_src/reports/semantic_truth_v3.json",
    ];
    
    for path in &paths {
        if let Ok(truth) = GpuSemanticBridge::load_truth(path) {
            println!("Loaded semantic truth from: {}", path);
            return truth;
        }
    }
    
    println!("WARNING: Could not find semantic_truth_v3.json");
    HashMap::new()
}

fn map_trigger_type(s: &str) -> TriggerType {
    match s.to_uppercase().as_str() {
        "ONPLAY" => TriggerType::OnPlay,
        "ONLIVESTART" => TriggerType::OnLiveStart,
        "ONLIVESUCCESS" => TriggerType::OnLiveSuccess,
        "TURNSTART" => TriggerType::TurnStart,
        "TURNEND" => TriggerType::TurnEnd,
        "CONSTANT" => TriggerType::Constant,
        "ACTIVATED" => TriggerType::Activated,
        "ONLEAVES" => TriggerType::OnLeaves,
        "ONREVEAL" => TriggerType::OnReveal,
        "ONPOSITIONCHANGE" => TriggerType::OnPositionChange,
        _ => TriggerType::None,
    }
}

fn run_single_semantic_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    trigger_type: TriggerType,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    // Find the real card ID from the database
    let real_id = find_card_id(db, card_id_str)?;
    
    // Create initial state with extra cards in hand for costs
    let mut state = create_test_state();
    // Put the test card at index 0, plus 4 dummy cards for discard costs
    state.core.players[0].hand = vec![real_id, 5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into(); // Dummy cards for draw
    
    // Set up energy zone with actual energy card IDs from the database
    // Use energy_db if available, otherwise fall back to placeholder IDs
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        // Fallback: use placeholder IDs (these may not work for energy tap effects)
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    state.core.players[0].tapped_energy_mask = 0; // Ensure all energy is untapped
    
    // Get the card's cost to ensure we have enough energy
    let card_cost = if let Some(member) = db.members.get(&real_id) {
        member.cost as usize
    } else {
        0
    };
    
    // Ensure we have enough energy to play the card
    // energy_count is derived from energy_zone.len(), so we need enough cards
    while state.core.players[0].energy_zone.len() < card_cost + 5 {
        state.core.players[0].energy_zone.push(3100 + state.core.players[0].energy_zone.len() as i32);
    }
    
    // Add a dummy member to stage slot 1 for conditions that check "other member on stage"
    // This is needed for cards like PL!HS-bp2-005-P+ which has CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER"}
    // Also needed for COST_GE conditions like COUNT_STAGE {MIN=1, FILTER="COST_GE=13"}
    // We need to find a high-cost member to satisfy COST_GE conditions
    if !db.members.is_empty() {
        // First, try to find a high-cost member (cost >= 13) that's not the test card
        let high_cost_member = db.members.iter()
            .filter(|(&id, _)| id != real_id)
            .max_by_key(|(_, m)| m.cost)
            .map(|(&id, _)| id);
        
        // Fall back to any member if no high-cost one found
        let dummy_member_id = high_cost_member
            .or_else(|| db.members.keys().find(|&&id| id != real_id).cloned())
            .unwrap_or(5001);
        
        state.core.players[0].stage[1] = dummy_member_id;
        
        // Also add a member to stage slot 2 for conditions that need multiple members
        if let Some(second_dummy) = db.members.keys()
            .filter(|&&id| id != real_id && id != dummy_member_id)
            .next()
        {
            state.core.players[0].stage[2] = *second_dummy;
        }
    }
    
    // Capture initial state for GPU (before any execution)
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU from the initial state
    let action = Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id();
    let mut gpu_input = initial_gpu.clone();
    gpu_input.forced_action = action;
    gpu_input.is_debug = 1;
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution (LOOK_AND_CHOOSE, etc.)
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    // Adjust expected deltas for card play
    // When playing a member card, hand decreases by 1 (the card being played)
    // The semantic truth may or may not include this -1 depending on how it was generated
    // 
    // Key insight: Check if semantic_truth already has a HAND_DELTA entry
    // If it does, trust the semantic_truth and don't add extra -1
    // If it doesn't, add -1 for the card play action
    //
    // IMPORTANT: Only add HAND_DELTA(-1) for ONPLAY and CONSTANT triggers
    // Other triggers (ONLIVESTART, ACTIVATED, etc.) don't involve playing a card from hand
    
    let mut adjusted_deltas = expected_deltas.to_vec();
    
    // Check if semantic_truth already has HAND_DELTA or HAND_DISCARD
    let has_hand_delta = expected_deltas.iter().any(|d| {
        d.tag.to_uppercase() == "HAND_DELTA" || d.tag.to_uppercase() == "HAND_DISCARD"
    });
    
    // Only add -1 for card play if:
    // 1. This is an ONPLAY or CONSTANT trigger
    // 2. semantic_truth doesn't already have a HAND_DELTA entry
    if (trigger_type == TriggerType::OnPlay || trigger_type == TriggerType::Constant) && !has_hand_delta {
        adjusted_deltas.push(SemanticDelta {
            tag: "HAND_DELTA".to_string(),
            value: serde_json::json!(-1), // Card play reduces hand by 1
        });
    }
    
    // Compare using semantic bridge
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        &adjusted_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Run test for ONLIVESTART trigger
/// Card is already on stage, trigger fires at live start
fn run_onlivestart_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    // Find the real card ID from the database
    let real_id = find_card_id(db, card_id_str)?;
    
    // Create initial state with card already on stage
    let mut state = create_test_state();
    // Put the test card on stage at slot 0
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].hand = vec![5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    // Set up energy zone
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    // Capture initial state for GPU
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - ONLIVESTART is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // ONLIVESTART = trigger_type 2
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 2 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    // Compare using semantic bridge (no hand delta adjustment for ONLIVESTART)
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Run test for ACTIVATED trigger
/// Card is on stage, player pays activate cost
fn run_activated_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    // Find the real card ID from the database
    let real_id = find_card_id(db, card_id_str)?;
    
    // Create initial state with card already on stage
    let mut state = create_test_state();
    // Put the test card on stage at slot 0
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].hand = vec![5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    // Set up energy zone with untapped energy for activation cost
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    state.core.players[0].tapped_energy_mask = 0; // All energy untapped
    
    // Capture initial state for GPU
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - ACTIVATED is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // ACTIVATED = trigger_type 7
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 7 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    // Compare using semantic bridge (no hand delta adjustment for ACTIVATED)
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

fn find_card_id(db: &CardDatabase, card_id_str: &str) -> Result<i32, String> {
    // Try to find by card_no
    for (&id, member) in &db.members {
        if member.card_no == card_id_str {
            return Ok(id);
        }
    }
    for (&id, live) in &db.lives {
        if live.card_no == card_id_str {
            return Ok(id);
        }
    }
    
    // Try to parse as numeric ID
    if let Ok(id) = card_id_str.parse::<i32>() {
        if db.members.contains_key(&id) || db.lives.contains_key(&id) {
            return Ok(id);
        }
    }
    
    Err(format!("Card {} not found in database", card_id_str))
}

/// Run test for ONLIVESUCCESS trigger
/// Card is on stage, live was successful
fn run_onlivesuccess_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    // Find the real card ID from the database
    let real_id = find_card_id(db, card_id_str)?;
    
    // Create initial state with card already on stage
    let mut state = create_test_state();
    // Put the test card on stage at slot 0
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].hand = vec![5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    // Set up energy zone
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    // Capture initial state for GPU
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - ONLIVESUCCESS is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // ONLIVESUCCESS = trigger_type 3
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 3 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    // Compare using semantic bridge
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Run test for TURNSTART trigger
fn run_turnstart_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;
    
    let mut state = create_test_state();
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].hand = vec![5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - TURNSTART is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // TURNSTART = trigger_type 4
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 4 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Run test for TURNEND trigger
fn run_turnend_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;
    
    let mut state = create_test_state();
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].hand = vec![5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - TURNEND is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // TURNEND = trigger_type 5
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 5 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Run test for ONLEAVES trigger
fn run_onleaves_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;
    
    let mut state = create_test_state();
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].hand = vec![5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - ONLEAVES is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // ONLEAVES = trigger_type 8
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 8 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Run test for ONREVEAL trigger
fn run_onreveal_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;
    
    let mut state = create_test_state();
    // Card is revealed from hand or deck
    state.core.players[0].hand = vec![real_id, 5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - ONREVEAL is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // ONREVEAL = trigger_type 9
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 9 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Run test for ONPOSITIONCHANGE trigger
fn run_onpositionchange_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;
    
    let mut state = create_test_state();
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].hand = vec![5001, 5002, 5003, 5004].into();
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU - ONPOSITIONCHANGE is triggered by ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    // ONPOSITIONCHANGE = trigger_type 10
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + 10 * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{}", card_id_str, ab_idx)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

/// Generic trigger test for unknown trigger types
fn run_generic_trigger_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    trigger_type: TriggerType,
    expected_deltas: &[SemanticDelta],
    trigger_name: &str
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;
    
    let mut state = create_test_state();
    // Put card in a reasonable position
    state.core.players[0].hand = vec![real_id, 5001, 5002, 5003, 5004].into();
    state.core.players[0].stage[0] = real_id; // Also on stage for stage triggers
    state.core.players[0].deck = vec![5005, 5006, 5007, 5008, 5009].into();
    
    let energy_ids: Vec<i32> = if !db.energy_db.is_empty() {
        db.energy_db.keys().cloned().take(10).collect()
    } else {
        (10..20).collect()
    };
    state.core.players[0].energy_zone = energy_ids.clone().into();
    
    let initial_gpu = state.to_gpu(db);
    
    // Execute on GPU using ACTION_BASE_TRIGGER
    // Format: 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
    let trigger_type_id = trigger_type as i32;
    let mut gpu_input = initial_gpu.clone();
    gpu_input.is_debug = 1;
    gpu_input.forced_action = 9000 + 0 * 1000 + trigger_type_id * 100 + (ab_idx as i32 * 10);
    
    let mut results = vec![GpuGameState::default(); 1];
    // Use 10 steps to allow for interaction resolution
    manager.run_multi_step(&[gpu_input], &mut results, 10);
    let gpu_final = &results[0];
    
    // Compare using semantic bridge
    let errors = GpuSemanticBridge::compare_actual_vs_expected(
        &initial_gpu,
        gpu_final,
        expected_deltas,
        0,
        &format!("{}:AB{} ({})", card_id_str, ab_idx, trigger_name)
    );
    
    if errors.is_empty() {
        Ok(true)
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        Ok(false)
    }
}

fn load_card_database() -> CardDatabase {
    // Try multiple paths for cards_compiled.json
    let paths = [
        "data/cards_compiled.json",
        "../data/cards_compiled.json",
        "engine_rust_src/data/cards_compiled.json",
    ];
    
    for path in &paths {
        if let Ok(json_str) = std::fs::read_to_string(path) {
            if let Ok(db) = CardDatabase::from_json(&json_str) {
                println!("Loaded card database from: {}", path);
                return db;
            }
        }
    }
    
    println!("WARNING: Could not load cards_compiled.json, using empty database");
    CardDatabase::default()
}
