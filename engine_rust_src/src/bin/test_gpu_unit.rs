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
    println!("DEBUG: Starting GPU Unit Parity Tests");
    
    // Prepare Database and GPU Manager
    let mut my_db = create_test_db();
    let bc = vec![O_DRAW_UNTIL, 5, 0, 0, O_RETURN, 0, 0, 0];
    let card_id = 1301;
    add_card(&mut my_db, card_id, "TEST-DRAW", vec![1], vec![(TriggerType::OnPlay, bc.clone(), vec![])]);
    
    let (stats, bytecode_raw) = my_db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode_raw, wgpu::Backends::all()).expect("Failed to init GPU");
    
    // ---------------------------------------------------------
    // Scenario 1: O_DRAW_UNTIL Parity
    // ---------------------------------------------------------
    println!("\n[SCENARIO 1] test_opcode_draw_until");
    
    // Setup state
    let mut state = create_test_state();
    state.core.players[0].deck = vec![1, 2, 3, 4, 5].into();
    state.core.players[0].hand = vec![101, 102].into(); // Hand size 2 (will be 3 after adding card_id)
    
    // Prepare CPU state (already in hand)
    state.core.players[0].hand.push(card_id);
    
    // Prepare GPU state
    let mut gpu_initial_rust = state.to_gpu(&my_db);
    gpu_initial_rust.is_debug = 1;
    let hand_idx_to_play = 2; // The card we added
    let slot_idx_to_play = 0;
    let action_id = 1000 + (hand_idx_to_play * 3) + slot_idx_to_play; 
    gpu_initial_rust.forced_action = action_id as i32;

    // Run CPU with the same full-action logic
    let mut cpu_state = state.clone();
    cpu_state.step(&my_db, action_id as i32).expect("CPU step failed");
    
    println!("DEBUG: Formatted Action ID = {}, Playing card at hand index {}", action_id, hand_idx_to_play);
    
    // Run GPU
    let mut results = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_initial_rust], &mut results);
    
    let gpu_final = &results[0];
    
    println!("Initial: HandLen={}, DeckLen=5", state.core.players[0].hand.len());
    println!("CPU: HandLen={}, DeckLen={}", cpu_state.players[0].hand.len(), cpu_state.players[0].deck.len());
    println!("GPU: HandLen={}, DeckLen={}", gpu_final.player0.hand_len, gpu_final.player0.deck_len);
    
    // Parity Check
    assert_eq!(cpu_state.players[0].hand.len() as u32, gpu_final.player0.hand_len, "Hand length mismatch");
    assert_eq!(cpu_state.players[0].deck.len() as u32, gpu_final.player0.deck_len, "Deck length mismatch");
    
    println!("SUCCESS: Scenario 1 Parity Matched!");

    // [SCENARIO 2] test_opcode_add_to_hand (Search)
    println!("\n[SCENARIO 2] test_opcode_add_to_hand");
    let mut state = create_test_state();
    let card_id = 99; // Dummy card to play
    // Opcode: O_ADD_TO_HAND (44), v=0, a=1 (From Deck) -> Draw specific card from deck? 
    // Actually O_ADD_TO_HAND usually takes a specific card ID if "created", 
    // but here we want "Add Top Deck to Hand" which is effectively Draw, 
    // OR "Search Deck". 
    // Let's rely on the shader implementation we just wrote:
    // case O_ADD_TO_HAND: t=1 (Deck) -> moves top card to hand (like draw but specific opcode flow)
    let bc = vec![O_ADD_TO_HAND, 0, 1, 0, O_RETURN, 0, 0, 0];
    add_card(&mut my_db, card_id, "OpAddHand", vec![], vec![(TriggerType::OnPlay, bc.clone(), vec![])]);
    state.core.players[0].hand.push(card_id); // Add trigger card
    
    // Run CPU
    let mut cpu_state = state.clone();
    // cpu_state.step will execute the play (discarding index 0) and then the effect (draw 1 from top deck)
    cpu_state.step(&my_db, 1000).expect("CPU step failed"); 

    // Run GPU
    let mut gpu_state = state.to_gpu(&my_db);
    gpu_state.is_debug = 1;
    gpu_state.forced_action = 1000; // Play hand index 0 (size is 1+5=6)
    
    let mut results = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_state], &mut results);
    let gpu_final = &results[0];

    println!("CPU: HandLen={}, DeckLen={}", cpu_state.players[0].hand.len(), cpu_state.players[0].deck.len());
    println!("GPU: HandLen={}, DeckLen={}", gpu_final.player0.hand_len, gpu_final.player0.deck_len);
    assert_eq!(cpu_state.players[0].hand.len() as u32, gpu_final.player0.hand_len, "S2 Hand len mismatch");
    assert_eq!(cpu_state.players[0].deck.len() as u32, gpu_final.player0.deck_len, "S2 Deck len mismatch");
    println!("SUCCESS: Scenario 2 Parity Matched!");

    // [SCENARIO 3] test_opcode_pay_energy
    println!("\n[SCENARIO 3] test_opcode_pay_energy");
    let mut state = create_test_state();
    // Setup energy
    state.core.players[0].energy_zone = smallvec::smallvec![1, 2, 3];
    state.core.players[0].tapped_energy_mask = 0;
    
    let card_id = 98;
    // Opcode: O_PAY_ENERGY (64), v=2 (Pay 2)
    let bc = vec![O_PAY_ENERGY, 2, 0, 0, O_RETURN, 0, 0, 0];
    add_card(&mut my_db, card_id, "OpPayEnergy", vec![], vec![(TriggerType::OnPlay, bc.clone(), vec![])]);
    state.core.players[0].hand.clear(); // Ensure our card is at index 0
    state.core.players[0].hand.push(card_id);
    
    let mut cpu_state = state.clone();
    cpu_state.step(&my_db, 1000).expect("CPU step failed");

    let mut gpu_state = state.to_gpu(&my_db);
    gpu_state.is_debug = 1;
    gpu_state.forced_action = 1000;

    let mut results = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_state], &mut results);
    let gpu_final = &results[0];

    println!("GPU Debug: {}", gpu_final.is_debug);
    println!("CPU: TappedEnergy={}", cpu_state.players[0].tapped_energy_count());
    println!("GPU: TappedEnergy={}", gpu_final.player0.tapped_energy_count);
    assert_eq!(cpu_state.players[0].tapped_energy_count() as u32, gpu_final.player0.tapped_energy_count, "S3 Tapped Energy mismatch");
    println!("SUCCESS: Scenario 3 Parity Matched!");
}
