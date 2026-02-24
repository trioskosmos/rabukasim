//! GPU Parity Tests - Ported from comprehensive_tests.rs
//! 
//! This file ports Rust tests from comprehensive_tests.rs to WGSL by running
//! the same tests on both CPU (Rust) and GPU (WGSL) and comparing results.

use engine_rust::core::logic::*;
use engine_rust::core::enums::TriggerType;
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_state::GpuGameState;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::test_helpers::{create_test_db, create_test_state, add_card};

fn main() {
    pollster::block_on(run_tests());
}

async fn run_tests() {
    println!("=== GPU Parity Tests: Triggers (Ported from comprehensive_tests.rs) ===\n");
    
    // Prepare Database and GPU Manager
    let my_db = create_test_db();
    let (stats, bytecode_raw) = my_db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode_raw, wgpu::Backends::all()).expect("Failed to init GPU");
    
    // ---------------------------------------------------------
    // Test 1: OnPlay Trigger - Draw 1 card
    // Uses O_DRAW (10) and O_RETURN (1) - both supported in WGSL
    // ---------------------------------------------------------
    println!("[TEST 1] OnPlay Trigger - Draw 1 card");
    
    let mut db = create_test_db();
    let card_id = 8001;
    let bc = vec![O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0];
    add_card(&mut db, card_id, "TEST_ONPLAY", vec![1], vec![(TriggerType::OnPlay, bc.clone(), vec![])]);
    
    let mut state = create_test_state();
    state.core.players[0].deck = vec![5901, 5902, 5903, 5904, 5905].into();
    state.core.players[0].hand = vec![card_id].into();
    
    // Run CPU
    let mut cpu_state = state.clone();
    cpu_state.step(&db, 1000).expect("CPU step failed");
    println!("CPU: HandLen={}, DeckLen={}", cpu_state.players[0].hand.len(), cpu_state.players[0].deck.len());
    
    // Run GPU
    let mut gpu_state = state.to_gpu(&db);
    gpu_state.is_debug = 1;
    gpu_state.forced_action = 1000;
    
    let mut results = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_state], &mut results);
    let gpu_final = &results[0];
    println!("GPU: HandLen={}, DeckLen={}", gpu_final.player0.hand_len, gpu_final.player0.deck_len);
    
    // Parity Check
    assert_eq!(cpu_state.players[0].hand.len() as u32, gpu_final.player0.hand_len, "TEST 1: Hand length mismatch");
    assert_eq!(cpu_state.players[0].deck.len() as u32, gpu_final.player0.deck_len, "TEST 1: Deck length mismatch");
    println!("SUCCESS: TEST 1 Parity Matched!\n");
    
    // ---------------------------------------------------------
    // Test 2: Add Blades (O_ADD_BLADES = 11) - supported in WGSL
    // ---------------------------------------------------------
    println!("[TEST 2] O_ADD_BLADES - Add 2 blades");
    
    let mut db2 = create_test_db();
    let card_id2 = 8003;
    let bc2 = vec![O_ADD_BLADES, 2, 0, 0, O_RETURN, 0, 0, 0];
    add_card(&mut db2, card_id2, "TEST_BLADES", vec![1], vec![(TriggerType::OnPlay, bc2.clone(), vec![])]);
    
    let mut state2 = create_test_state();
    state2.core.players[0].hand = vec![card_id2].into();
    state2.core.players[0].stage[0] = 3000;
    
    // Run CPU
    let mut cpu_state2 = state2.clone();
    cpu_state2.step(&db2, 1000).expect("CPU step failed");
    println!("CPU: BladeBuff[0]={}", cpu_state2.players[0].blade_buffs[0]);
    
    // Run GPU
    let mut gpu_state2 = state2.to_gpu(&db2);
    gpu_state2.is_debug = 1;
    gpu_state2.forced_action = 1000;
    
    let mut results2 = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_state2], &mut results2);
    let gpu_final2 = &results2[0];
    println!("GPU: BladeBuff[0]={}", gpu_final2.player0.blade_buffs[0]);
    
    // Parity Check
    assert_eq!(cpu_state2.players[0].blade_buffs[0] as u32, gpu_final2.player0.blade_buffs[0], "TEST 2: Blade buff mismatch");
    println!("SUCCESS: TEST 2 Parity Matched!\n");
    
    // ---------------------------------------------------------
    // Test 3: Boost Score (O_BOOST_SCORE = 16) - supported in WGSL
    // ---------------------------------------------------------
    println!("[TEST 3] O_BOOST_SCORE - Add 5 score");
    
    let mut db3 = create_test_db();
    let card_id3 = 8004;
    let bc3 = vec![O_BOOST_SCORE, 5, 0, 0, O_RETURN, 0, 0, 0];
    add_card(&mut db3, card_id3, "TEST_BOOST", vec![1], vec![(TriggerType::OnPlay, bc3.clone(), vec![])]);
    
    let mut state3 = create_test_state();
    state3.core.players[0].hand = vec![card_id3].into();
    state3.core.players[0].score = 100;
    
    // Run CPU
    let mut cpu_state3 = state3.clone();
    cpu_state3.step(&db3, 1000).expect("CPU step failed");
    println!("CPU: Score={}", cpu_state3.players[0].score);
    
    // Run GPU
    let mut gpu_state3 = state3.to_gpu(&db3);
    gpu_state3.is_debug = 1;
    gpu_state3.forced_action = 1000;
    
    let mut results3 = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_state3], &mut results3);
    let gpu_final3 = &results3[0];
    println!("GPU: Score={}", gpu_final3.player0.score);
    
    // Parity Check
    assert_eq!(cpu_state3.players[0].score as u32, gpu_final3.player0.score, "TEST 3: Score mismatch");
    println!("SUCCESS: TEST 3 Parity Matched!\n");
    
    // ---------------------------------------------------------
    // Test 4: Condition C_TURN_1 (200) - supported in WGSL
    // ---------------------------------------------------------
    println!("[TEST 4] C_TURN_1 - Check if turn 1");
    
    let mut db4 = create_test_db();
    let card_id4 = 8005;
    // Condition: turn == 1, then draw 1
    let bc4 = vec![C_TURN_1, 0, 0, 0, O_JUMP_IF_FALSE, 2, 0, 0, O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0];
    add_card(&mut db4, card_id4, "TEST_TURN1", vec![1], vec![(TriggerType::OnPlay, bc4.clone(), vec![])]);
    
    let mut state4 = create_test_state();
    state4.core.players[0].hand = vec![card_id4].into();
    state4.turn = 1; // Turn 1
    
    // Run CPU
    let mut cpu_state4 = state4.clone();
    cpu_state4.step(&db4, 1000).expect("CPU step failed");
    println!("CPU (Turn 1): HandLen={}", cpu_state4.players[0].hand.len());
    
    // Run GPU
    let mut gpu_state4 = state4.to_gpu(&db4);
    gpu_state4.is_debug = 1;
    gpu_state4.forced_action = 1000;
    
    let mut results4 = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_state4], &mut results4);
    let gpu_final4 = &results4[0];
    println!("GPU (Turn 1): HandLen={}", gpu_final4.player0.hand_len);
    
    // Parity Check
    assert_eq!(cpu_state4.players[0].hand.len() as u32, gpu_final4.player0.hand_len, "TEST 4: Hand length mismatch");
    println!("SUCCESS: TEST 4 Parity Matched!\n");
    
    // ---------------------------------------------------------
    // Test 5: Condition C_COUNT_STAGE >= 1 (203) - supported in WGSL
    // ---------------------------------------------------------
    println!("[TEST 5] C_COUNT_STAGE - Check stage count");
    
    let mut db5 = create_test_db();
    let card_id5 = 8006;
    // Condition: stage count >= 1, then draw 1
    let bc5 = vec![C_COUNT_STAGE, 1, 0, 0, O_JUMP_IF_FALSE, 2, 0, 0, O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0];
    add_card(&mut db5, card_id5, "TEST_STAGE_CNT", vec![1], vec![(TriggerType::OnPlay, bc5.clone(), vec![])]);
    
    let mut state5 = create_test_state();
    state5.core.players[0].hand = vec![card_id5].into();
    state5.core.players[0].stage[0] = 3000; // Member on stage
    
    // Run CPU
    let mut cpu_state5 = state5.clone();
    cpu_state5.step(&db5, 1000).expect("CPU step failed");
    println!("CPU (Stage >= 1): HandLen={}", cpu_state5.players[0].hand.len());
    
    // Run GPU
    let mut gpu_state5 = state5.to_gpu(&db5);
    gpu_state5.is_debug = 1;
    gpu_state5.forced_action = 1000;
    
    let mut results5 = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_state5], &mut results5);
    let gpu_final5 = &results5[0];
    println!("GPU (Stage >= 1): HandLen={}", gpu_final5.player0.hand_len);
    
    // Parity Check
    assert_eq!(cpu_state5.players[0].hand.len() as u32, gpu_final5.player0.hand_len, "TEST 5: Hand length mismatch");
    println!("SUCCESS: TEST 5 Parity Matched!\n");
    
    println!("=== All GPU Parity Tests Passed! ===");
}
