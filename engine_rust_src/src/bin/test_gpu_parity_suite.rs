use engine_rust::core::logic::*;
use engine_rust::core::enums::TriggerType;
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_state::GpuGameState;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::test_helpers::{create_test_state, load_real_db, create_test_db, add_card, Action};

fn main() {
    pollster::block_on(run_suite());
}

async fn run_suite() {
    println!("--- GPU PARITY TEST SUITE (BATCH 1) ---");
    let mut mismatch_count = 0;
    
    // --- PART 1: OPCODE UNIT PARITY (Mirroring CPU Unit Tests) ---
    println!("\n[PART 1] OPCODE UNIT MIRRORING (Synthetic)");
    let mut unit_db = create_test_db();
    
    // S-UNIT-1: O_REVEAL_UNTIL (CPU Mirror: test_opcode_reveal_until_type_live)
    let s1_bc = vec![69, 232, 1, 6, O_RETURN, 0, 0, 0];
    add_card(&mut unit_db, 2001, "REVEAL_LIVE", vec![], vec![(TriggerType::OnPlay, s1_bc, vec![])]);
    
    // S-UNIT-2: O_IMMUNITY (CPU Mirror: test_opcode_immunity)
    let s2_bc = vec![O_IMMUNITY, 1, 0, 0, O_RETURN, 0, 0, 0];
    add_card(&mut unit_db, 2002, "SET_IMMUNITY", vec![], vec![(TriggerType::OnPlay, s2_bc, vec![])]);

    // S-UNIT-3: O_SET_BLADES (CPU Mirror: test_opcode_set_blades)
    let s3_bc = vec![O_SET_BLADES, 5, 0, 4, O_RETURN, 0, 0, 0]; // 4 = SELF (Slot 0 for us)
    add_card(&mut unit_db, 2003, "SET_BLADES_5", vec![], vec![(TriggerType::OnPlay, s3_bc, vec![])]);

    // S-UNIT-4: O_LOOK_AND_CHOOSE
    // v: look=3, pick=1 -> 1 << 8 | 3 = 259
    // a: source=Deck(8) -> 8 << 12 = 32768
    // s: target=Hand(6), rem=Discard(7) -> 6 | (7 << 8) = 1798
    let s4_bc = vec![O_LOOK_AND_CHOOSE, 259, 32768, 1798, O_RETURN, 0, 0, 0];
    add_card(&mut unit_db, 2004, "LOOK_AND_CHOOSE", vec![], vec![(TriggerType::OnPlay, s4_bc, vec![])]);

    // S-UNIT-5: O_MOVE_MEMBER
    // Move from slot 0 to slot 1
    let s5_bc = vec![O_MOVE_MEMBER, 0, 1, 0, O_RETURN, 0, 0, 0];
    add_card(&mut unit_db, 2005, "MOVE_MEMBER", vec![], vec![(TriggerType::OnPlay, s5_bc, vec![])]);
    
    let (unit_stats, unit_bytecode) = unit_db.convert_to_gpu();
    let unit_manager = GpuManager::new(&unit_stats, &unit_bytecode, wgpu::Backends::all()).expect("Failed to init GPU");

    // Run S-UNIT-1
    let mut state = create_test_state();
    state.core.players[0].deck = vec![3001, 3002, 55001, 3003, 3004].into(); 
    state.core.players[0].hand = vec![2001].into(); 
    if !run_parity_check(&unit_manager, &unit_db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U1 Reveal Live") { mismatch_count += 1; }

    // Run S-UNIT-2
    let mut state = create_test_state();
    state.core.players[0].hand = vec![2002].into();
    if !run_parity_check(&unit_manager, &unit_db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U2 Immunity") { mismatch_count += 1; }

    // Run S-UNIT-3
    let mut state = create_test_state();
    state.core.players[0].stage[0] = 3001;
    state.core.players[0].hand = vec![2003].into();
    if !run_parity_check(&unit_manager, &unit_db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U3 Set Blades") { mismatch_count += 1; }

    // Run S-UNIT-4 (O_LOOK_AND_CHOOSE)
    let mut state = create_test_state();
    state.core.players[0].deck = vec![3001, 3002, 3003, 3004].into(); 
    state.core.players[0].hand = vec![2004].into();
    if !run_parity_check(&unit_manager, &unit_db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U4 Look & Choose") { mismatch_count += 1; }

    // Run S-UNIT-5 (O_MOVE_MEMBER)
    let mut state = create_test_state();
    state.core.players[0].stage[0] = 3001;
    state.core.players[0].hand = vec![2005].into(); // Play to slot 1
    // Wait, O_MOVE_MEMBER triggers OnPlay. We play to slot 1, but we want to move from 0 to 1? 
    // It'll play to slot 1, then the effect moves 0 to 1, swapping?
    // Let's just play to slot 2, effect moves 0 to 1.
    if !run_parity_check(&unit_manager, &unit_db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 2 }.id(), "U5 Move Member") { mismatch_count += 1; }


    // --- PART 2: PRODUCTION CARD PARITY (Real Database) ---
    println!("\n[PART 2] PRODUCTION CARD PARITY (Real Data)");
    let mut db = load_real_db();
    
    // Inject missing Live Card 73 for P1
    db.lives.insert(73, engine_rust::core::logic::card_db::LiveCard {
        card_id: 73, card_no: "DUMMY-LIVE".to_string(), name: "Dummy Live".to_string(),
        score: 1, required_hearts: [1,0,0,0,0,0,0], ..Default::default()
    });
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).expect("Failed to init GPU");

    // SCENARIO P1: O_REVEAL_UNTIL (CID 4340)
    println!("\n[SCENARIO P1] CID 4340: O_REVEAL_UNTIL");
    let mut state = create_test_state();
    state.core.players[0].deck = vec![9, 10, 73, 11, 12].into(); // Valid Member/Live IDs
    state.core.players[0].hand = vec![6001, 4340].into(); // 6001 Junk for discard
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into(); // Add 20 energy
    if !run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 1, slot_idx: 0 }.id(), "P1 Real Reveal") { mismatch_count += 1; }

    // SCENARIO P2: O_ADD_BLADES (CID 399)
    println!("\n[SCENARIO P2] CID 399: O_ADD_BLADES");
    let mut state = create_test_state();
    state.core.players[0].hand = vec![399].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into(); // Add 20 energy
    if !run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "P2 Real Blades") { mismatch_count += 1; }

    // --- SCENARIO 3: O_DRAW (CID 4348) ---
    // PL!N-bp1-019-PR: "OnPlay: Draw 1, Discard 1" (Testing Op 10)
    println!("\n[SCENARIO P3] CID 4348: O_DRAW");
    let mut state = create_test_state();
    state.core.players[0].hand = vec![4348].into();
    state.core.players[0].deck = vec![3201].into(); // Card to draw
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into(); // Add 20 energy
    if !run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "P3 Real Draw") { mismatch_count += 1; }

    if mismatch_count > 0 {
        println!("\n--- SUITE FAILED WITH {} MISMATCHES ---", mismatch_count);
        std::process::exit(1);
    } else {
        println!("\n--- ALL PARITY SCENARIOS PASSED ---");
    }
}

fn run_parity_check(manager: &GpuManager, db: &CardDatabase, state: &GameState, action: i32, name: &str) -> bool {
    let mut cpu_state = state.clone();
    cpu_state.step(db, action).expect("CPU step failed");
    
    // Resolve any pending interactions to match GPU's eager execution (assumes choices=0)
    let mut loop_safety = 0;
    while !cpu_state.interaction_stack.is_empty() && loop_safety < 10 {
        cpu_state.step(db, (ACTION_BASE_CHOICE + 0) as i32).expect("CPU choice failed");
        loop_safety += 1;
    }
    
    let mut gpu_initial = state.to_gpu(db);
    gpu_initial.forced_action = action;
    gpu_initial.is_debug = 1;

    let mut results = vec![GpuGameState::default(); 1];
    manager.run_simulations_into(&[gpu_initial], &mut results);
    let gpu_final = &results[0];

    let mut mismatch = false;
    
    // Check Hand Length
    if cpu_state.players[0].hand.len() as u32 != gpu_final.player0.hand_len {
        println!("  [FAIL] {}: Hand length mismatch (CPU: {}, GPU: {})", name, cpu_state.players[0].hand.len(), gpu_final.player0.hand_len);
        mismatch = true;
    }
    // Check Deck Length
    if cpu_state.players[0].deck.len() as u32 != gpu_final.player0.deck_len {
        println!("  [FAIL] {}: Deck length mismatch (CPU: {}, GPU: {})", name, cpu_state.players[0].deck.len(), gpu_final.player0.deck_len);
        mismatch = true;
    }
    // Check Blade Buffs
    if cpu_state.players[0].blade_buffs[0] as u32 != gpu_final.player0.blade_buffs[0] {
        println!("  [FAIL] {}: Blade Buff [0] mismatch (CPU: {}, GPU: {})", name, cpu_state.players[0].blade_buffs[0], gpu_final.player0.blade_buffs[0]);
        mismatch = true;
    }
    // Check Flags (Moved, etc)
    if cpu_state.players[0].flags != gpu_final.player0.flags {
         println!("  [FAIL] {}: Flags mismatch (CPU: {:08x}, GPU: {:08x})", name, cpu_state.players[0].flags, gpu_final.player0.flags);
         mismatch = true;
    }

    if !mismatch {
        println!("  [PASS] {}", name);
    }
    !mismatch
}
