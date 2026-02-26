use crate::core::logic::*;
use crate::core::enums::TriggerType;
use crate::core::gpu_manager::GpuManager;
use crate::core::gpu_state::GpuGameState;
use crate::core::gpu_conversions::GpuConverter;
use crate::test_helpers::{create_test_state, create_test_db, add_card, Action};

// --- Test Helper Functions derived from parity suite ---

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
    manager.run_single_step(&[gpu_initial], &mut results);
    let gpu_final = &results[0];

    let errors = compare_states(&cpu_state, gpu_final, name);
    
    if errors.is_empty() {
        true
    } else {
        for err in &errors {
            println!("  [FAIL] {}", err);
        }
        false
    }
}

fn compare_states(cpu: &GameState, gpu: &GpuGameState, name: &str) -> Vec<String> {
    let mut errors = Vec::new();
    
    if cpu.players[0].hand.len() as u32 != gpu.player0.hand_len {
        errors.push(format!("{}: Hand length mismatch (CPU: {}, GPU: {})", name, cpu.players[0].hand.len(), gpu.player0.hand_len));
    }
    if cpu.players[0].deck.len() as u32 != gpu.player0.deck_len {
        errors.push(format!("{}: Deck length mismatch (CPU: {}, GPU: {})", name, cpu.players[0].deck.len(), gpu.player0.deck_len));
    }
    if cpu.players[0].discard.len() as u32 != gpu.player0.discard_pile_len {
        errors.push(format!("{}: Discard length mismatch (CPU: {}, GPU: {})", name, cpu.players[0].discard.len(), gpu.player0.discard_pile_len));
    }
    if cpu.players[0].score != gpu.player0.score {
        errors.push(format!("{}: Score mismatch (CPU: {}, GPU: {})", name, cpu.players[0].score, gpu.player0.score));
    }
    for i in 0..3 {
        if cpu.players[0].blade_buffs[i] as i32 != gpu.player0.blade_buffs[i] as i32 {
            errors.push(format!("{}: Blade Buff [{}] mismatch (CPU: {}, GPU: {})", name, i, cpu.players[0].blade_buffs[i], gpu.player0.blade_buffs[i]));
        }
    }
    let cpu_additions: u64 = cpu.players[0].heart_req_additions.0;
    let gpu_additions: u64 = (gpu.player0.heart_req_additions[0] as u64) | ((gpu.player0.heart_req_additions[1] as u64) << 32);
    if cpu_additions != gpu_additions {
        errors.push(format!("{}: Heart Req Additions mismatch (CPU: {:016x}, GPU: {:016x})", name, cpu_additions, gpu_additions));
    }
    let cpu_reductions: u64 = cpu.players[0].heart_req_reductions.0;
    let gpu_reductions: u64 = (gpu.player0.heart_req_reductions[0] as u64) | ((gpu.player0.heart_req_reductions[1] as u64) << 32);
    if cpu_reductions != gpu_reductions {
        errors.push(format!("{}: Heart Req Reductions mismatch (CPU: {:016x}, GPU: {:016x})", name, cpu_reductions, gpu_reductions));
    }
    if cpu.players[0].cost_reduction as i32 != gpu.player0.cost_reduction {
        errors.push(format!("{}: Cost Reduction mismatch (CPU: {}, GPU: {})", name, cpu.players[0].cost_reduction, gpu.player0.cost_reduction));
    }
    if cpu.players[0].energy_zone.len() as u32 != gpu.player0.energy_count {
        errors.push(format!("{}: Energy count mismatch (CPU: {}, GPU: {})", name, cpu.players[0].energy_zone.len(), gpu.player0.energy_count));
    }
    if cpu.players[0].flags != gpu.player0.flags {
        errors.push(format!("{}: Flags mismatch (CPU: {:08x}, GPU: {:08x})", name, cpu.players[0].flags, gpu.player0.flags));
    }
    errors
}

// ---------------------------------------------------------
// UNIT PARITY TESTS
// ---------------------------------------------------------

#[test]
fn parity_o_reveal_until() {
    let mut db = create_test_db();
    let bc = vec![69, 232, 1, 0, 6, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2001, "REVEAL_LIVE", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].deck = vec![3001, 3002, 55001, 3003, 3004].into(); 
    state.core.players[0].hand = vec![2001].into(); 
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U1 Reveal Live"));
}

#[test]
fn parity_o_immunity() {
    let mut db = create_test_db();
    let bc = vec![O_IMMUNITY, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2002, "SET_IMMUNITY", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2002].into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U2 Immunity"));
}

#[test]
fn parity_o_set_blades() {
    let mut db = create_test_db();
    let bc = vec![O_SET_BLADES, 5, 0, 0, 4, O_RETURN, 0, 0, 0, 0]; // 4 = SELF (Slot 0 for us)
    add_card(&mut db, 2003, "SET_BLADES_5", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].stage[0] = 3001;
    state.core.players[0].hand = vec![2003].into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U3 Set Blades"));
}

#[test]
fn parity_o_look_and_choose() {
    let mut db = create_test_db();
    let bc = vec![O_LOOK_AND_CHOOSE, 259, 32768, 0, 1798, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2004, "LOOK_AND_CHOOSE", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].deck = vec![3001, 3002, 3003, 3004].into(); 
    state.core.players[0].hand = vec![2004].into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U4 Look & Choose"));
}

#[test]
fn parity_o_move_member() {
    let mut db = create_test_db();
    let bc = vec![O_MOVE_MEMBER, 0, 1, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2005, "MOVE_MEMBER", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].stage[0] = 3001;
    state.core.players[0].hand = vec![2005].into(); // Play to slot 2, effect moves 0 to 1
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 2 }.id(), "U5 Move Member"));
}

#[test]
fn parity_o_set_heart_cost() {
    let mut db = create_test_db();
    let bc = vec![O_SET_HEART_COST, 3, 0, 0, 2, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2007, "SET_HEART_COST", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2007].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U7 Set Heart Cost"));
}

#[test]
fn parity_o_increase_heart_cost() {
    let mut db = create_test_db();
    let bc = vec![O_INCREASE_HEART_COST, 2, 0, 0, 1, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2008, "INC_HEART_COST", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2008].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U8 Increase Heart Cost"));
}

#[test]
fn parity_o_reduce_heart_req() {
    let mut db = create_test_db();
    let bc = vec![O_REDUCE_HEART_REQ, 2, 0, 0, 3, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2009, "REDUCE_HEART_REQ", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2009].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U9 Reduce Heart Req"));
}

#[test]
fn parity_o_draw() {
    let mut db = create_test_db();
    let bc = vec![O_DRAW, 2, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2010, "DRAW_2", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2010].into();
    state.core.players[0].deck = vec![3001, 3002, 3003, 3004].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U10 Draw 2"));
}

#[test]
fn parity_o_boost_score() {
    let mut db = create_test_db();
    let bc = vec![O_BOOST_SCORE, 5, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2011, "BOOST_SCORE", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2011].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U11 Boost Score"));
}

#[test]
fn parity_o_reduce_cost() {
    let mut db = create_test_db();
    let bc = vec![O_REDUCE_COST, 3, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2012, "REDUCE_COST", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2012].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U12 Reduce Cost"));
}

#[test]
fn parity_o_add_blades() {
    let mut db = create_test_db();
    let bc = vec![O_ADD_BLADES, 2, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2013, "ADD_BLADES", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2013].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U13 Add Blades"));
}

#[test]
fn parity_o_add_hearts() {
    let mut db = create_test_db();
    let bc = vec![O_ADD_HEARTS, 3, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2014, "ADD_HEARTS", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2014].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U14 Add Hearts"));
}

#[test]
fn parity_o_set_score() {
    let mut db = create_test_db();
    let bc = vec![O_SET_SCORE, 100, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    add_card(&mut db, 2015, "SET_SCORE", vec![], vec![(TriggerType::OnPlay, bc, vec![])]);
    
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).unwrap();

    let mut state = create_test_state();
    state.core.players[0].hand = vec![2015].into();
    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();
    assert!(run_parity_check(&manager, &db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "U15 Set Score"));
}
