/// Automated Per-Card Parity Sweep
/// 
/// Iterates over EVERY card in cards_compiled.json that has OnPlay bytecode,
/// plays it on both CPU and GPU engines, and compares the resulting states.
/// Reports opcode coverage and any mismatches.

use engine_rust::core::logic::*;
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_state::GpuGameState;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::test_helpers::{create_test_state, load_real_db};
use std::collections::HashMap;

const ACTION_BASE_CHOICE: u32 = 8000;
const ACTION_BASE_HAND: u32 = 1000;

fn main() {
    // Naga needs a big stack for complex shaders
    let builder = std::thread::Builder::new()
        .name("parity-sweep".into())
        .stack_size(32 * 1024 * 1024);
    let handler = builder.spawn(real_main).expect("Failed to spawn thread");
    handler.join().expect("Thread panicked");
}

fn real_main() {
    println!("=== AUTOMATED PER-CARD PARITY SWEEP ===\n");

    let db = load_real_db();
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::all())
        .expect("Failed to init GPU");

    // Collect all member cards with OnPlay bytecode
    let mut test_cards: Vec<(i32, String)> = Vec::new();
    for (&cid, member) in &db.members {
        for ab in &member.abilities {
            if ab.trigger == TriggerType::OnPlay && !ab.bytecode.is_empty() {
                test_cards.push((cid, member.card_no.clone()));
                break; // One entry per card
            }
        }
    }
    test_cards.sort_by_key(|(cid, _)| *cid);

    println!("Found {} cards with OnPlay bytecode to test.\n", test_cards.len());

    let mut pass_count = 0;
    let mut fail_count = 0;
    let mut skip_count = 0;
    let mut failed_cards: Vec<(i32, String, Vec<String>)> = Vec::new();
    let mut opcode_hits: HashMap<i32, u32> = HashMap::new();

    for (cid, card_no) in &test_cards {
        let cid = *cid;

        // Count opcodes in this card's bytecode
        if let Some(member) = db.get_member(cid) {
            for ab in &member.abilities {
                if ab.trigger == TriggerType::OnPlay {
                    let bc = &ab.bytecode;
                    let mut pc = 0;
                    while pc + 4 < bc.len() {
                        let op = bc[pc];
                        *opcode_hits.entry(op).or_insert(0) += 1;
                        pc += 5; // Each instruction is 5 words
                    }
                }
            }
        }

        // Setup: generous state with plenty of energy, deck cards, hand space
        let mut state = create_test_state();
        state.core.players[0].hand = vec![cid].into();
        state.core.players[0].deck = (51001..51021).collect::<Vec<i32>>().into(); // 20 deck cards
        state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into(); // 20 energy
        state.core.players[0].discard = vec![3001, 3002, 3003].into(); // Some discard targets
        state.core.players[1].deck = (52001..52021).collect::<Vec<i32>>().into();
        state.core.players[1].energy_zone = (30..50).collect::<Vec<i32>>().into();
        state.ui.silent = true;

        // CPU: play the card to slot 0
        let action = (ACTION_BASE_HAND + 0 * 3 + 0) as i32; // Play hand[0] to slot 0
        let mut cpu_state = state.clone();
        if cpu_state.step(&db, action).is_err() {
            skip_count += 1;
            continue;
        }

        // Resolve pending interactions (auto-choose option 0)
        let mut loop_safety = 0;
        while !cpu_state.interaction_stack.is_empty() && loop_safety < 20 {
            let _ = cpu_state.step(&db, (ACTION_BASE_CHOICE + 0) as i32);
            loop_safety += 1;
        }

        // GPU: same action
        let mut gpu_input = state.to_gpu(&db);
        gpu_input.forced_action = action;
        gpu_input.is_debug = 0; // No debug spam

        let mut results = vec![GpuGameState::default(); 1];
        manager.run_simulations_into(&[gpu_input], &mut results);
        let gpu = &results[0];

        // Compare key fields
        let mut mismatches: Vec<String> = Vec::new();
        let cpu_p = &cpu_state.players[0];
        let gpu_p = &gpu.player0;

        if cpu_p.hand.len() as u32 != gpu_p.hand_len {
            mismatches.push(format!("hand_len: CPU={} GPU={}", cpu_p.hand.len(), gpu_p.hand_len));
        }
        if cpu_p.deck.len() as u32 != gpu_p.deck_len {
            mismatches.push(format!("deck_len: CPU={} GPU={}", cpu_p.deck.len(), gpu_p.deck_len));
        }
        if cpu_p.discard.len() as u32 != gpu_p.discard_pile_len {
            mismatches.push(format!("discard_len: CPU={} GPU={}", cpu_p.discard.len(), gpu_p.discard_pile_len));
        }
        if cpu_p.score as u32 != gpu_p.score {
            mismatches.push(format!("score: CPU={} GPU={}", cpu_p.score, gpu_p.score));
        }
        if cpu_p.blade_buffs[0] as u32 != gpu_p.blade_buffs[0] {
            mismatches.push(format!("blade_buffs[0]: CPU={} GPU={}", cpu_p.blade_buffs[0], gpu_p.blade_buffs[0]));
        }
        if cpu_p.energy_zone.len() as u32 != gpu_p.energy_count {
            mismatches.push(format!("energy_count: CPU={} GPU={}", cpu_p.energy_zone.len(), gpu_p.energy_count));
        }
        if cpu_p.flags as u32 != gpu_p.flags {
            mismatches.push(format!("flags: CPU={:08x} GPU={:08x}", cpu_p.flags, gpu_p.flags));
        }

        if mismatches.is_empty() {
            pass_count += 1;
        } else {
            fail_count += 1;
            let card_name = db.get_member(cid).map(|m| m.name.clone()).unwrap_or_else(|| "Unknown".to_string());
            println!("  [FAIL] CID {} ({} - {}): {}", cid, card_no, card_name,
                mismatches.iter().map(|m| m.as_str()).collect::<Vec<_>>().join(", "));
            
            if cid == 9 {
                println!("    [TRACE CID 9]");
                println!("      CPU Flags: {:08x}, HandLen: {}", cpu_p.flags, cpu_p.hand.len());
                println!("      GPU Flags: {:08x}, HandLen: {}", gpu_p.flags, gpu_p.hand_len);
                println!("      CPU Stage: {:?}", cpu_p.stage);
                println!("      GPU Stage: {:?}", gpu.player0.stage);
            }
            failed_cards.push((cid, card_no.clone(), mismatches));
        }
    }

    // === SUMMARY ===
    println!("\n=== RESULTS ===");
    println!("  PASS:  {}", pass_count);
    println!("  FAIL:  {}", fail_count);
    println!("  SKIP:  {}", skip_count);
    println!("  TOTAL: {}", test_cards.len());

    if !failed_cards.is_empty() {
        println!("\n--- FAILED CARDS ---");
        for (cid, no, mismatches) in &failed_cards {
            println!("  CID {}: {} -> {}", cid, no, mismatches.join("; "));
        }
    }

    // === OPCODE COVERAGE ===
    let mut opcodes_sorted: Vec<_> = opcode_hits.iter().collect();
    opcodes_sorted.sort_by_key(|(op, _)| **op);

    println!("\n=== OPCODE COVERAGE (OnPlay bytecode) ===");
    let total_unique = opcodes_sorted.len();
    for (op, count) in &opcodes_sorted {
        println!("  Op {:3}: {} hits", op, count);
    }
    println!("  Total unique opcodes encountered: {}", total_unique);

    println!("\n=== SWEEP COMPLETE ===");

    if fail_count > 0 {
        std::process::exit(1);
    }
}
