//! CPU vs GPU Game Sync Test
//! 
//! This test verifies that CPU and GPU produce the same game states when given
//! the same action sequence. The key insight is that GPU auto-advances through
//! non-interactive phases, so we compare states at "synchronization points" -
//! the interactive phases where both CPU and GPU should be aligned.
//!
//! SYNC STRATEGY:
//! 1. Run game on CPU, recording all actions taken
//! 2. Replay same actions on GPU with forced_action
//! 3. Compare states at each interactive phase

use std::sync::Arc;
use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::core::gpu_state::GpuGameState;

struct ShaderRng {
    x: u32,
    y: u32,
}

impl ShaderRng {
    fn new(seed: u32) -> Self {
        Self { x: seed, y: seed.wrapping_mul(2654435761) }
    }
    fn jump(&mut self) -> u32 {
        self.x ^= self.y << 13;
        self.y ^= self.x >> 7;
        self.x ^= self.y << 17;
        self.x.wrapping_add(self.y)
    }
}

/// Phase constants matching WGSL
const PHASE_TERMINAL: i32 = 9;
const PHASE_MAIN: i32 = 4;
const PHASE_LIVESET: i32 = 5;
const PHASE_RESPONSE: i32 = 10;
const PHASE_MULLIGAN_P1: i32 = -1;
const PHASE_MULLIGAN_P2: i32 = 0;

fn is_interactive_phase(phase: i32) -> bool {
    phase == PHASE_MAIN || phase == PHASE_LIVESET || phase == PHASE_RESPONSE || 
    phase == PHASE_MULLIGAN_P1 || phase == PHASE_MULLIGAN_P2
}

fn main() {
    println!("=== CPU vs GPU Sync Test (Equalized RNG) ===\n");
    
    // Load database
    let json_path = if std::path::Path::new("data/cards_compiled.json").exists() {
        "data/cards_compiled.json"
    } else {
        "../data/cards_compiled.json"
    };
    let json_str = std::fs::read_to_string(json_path).expect("Failed to read cards JSON");
    let db = CardDatabase::from_json(&json_str).expect("Failed to parse JSON");
    let (stats, bytecode) = db.convert_to_gpu();
    
    // Initialize GPU
    let gpu_manager = Arc::new(GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).expect("Failed to init GPU"));
    
    // Build deterministic decks
    let mut all_members: Vec<i32> = db.members.keys().map(|&k| k as i32).collect();
    let mut all_lives: Vec<i32> = db.lives.keys().map(|&k| k as i32).collect();
    
    // Sort for determinism
    all_members.sort();
    all_lives.sort();
    
    // Build decks: 16 members + 4 lives each
    let p0_deck: Vec<i32> = all_members.iter().take(16).cloned()
        .chain(all_lives.iter().take(4).cloned()).collect();
    let p1_deck: Vec<i32> = all_members.iter().skip(16).take(16).cloned()
        .chain(all_lives.iter().skip(4).take(4).cloned()).collect();
    
    // Get energy cards
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();
    
    println!("P0 deck: {} cards", p0_deck.len());
    println!("P1 deck: {} cards", p1_deck.len());
    println!("Energy cards: {}", energy_ids.len());
    
    // Use same seed for both
    let seed = 12345u32;
    
    // Initialize CPU game state
    let mut cpu_state = Box::new(GameState::default());
    cpu_state.initialize_game(
        p0_deck.clone(),
        p1_deck.clone(),
        energy_ids.clone(),
        energy_ids.clone(),
        Vec::new(),
        Vec::new(),
    );
    cpu_state.ui.silent = true;
    
    // IMPORTANT: CPU starts at Rps phase, but GPU auto-advances to first interactive phase.
    // We need to step CPU through the initial phases to match GPU's starting point.
    // GPU auto-advances: Rps -> TurnChoice -> Active -> Energy -> Draw -> Main
    // CPU needs explicit steps for RPS and TurnChoice phases.
    println!("Before step: CPU phase={:?}", cpu_state.phase);
    
    // RPS phase: Both players need to make a choice
    // P0: action 10000-10002 (rock/paper/scissors)
    // P1: action 11000-11002 (rock/paper/scissors)
    let _ = cpu_state.step(&db, 10000); // P0: Rock
    let _ = cpu_state.step(&db, 11001); // P1: Paper (P1 wins)
    println!("After RPS: CPU phase={:?}", cpu_state.phase);
    
    // TurnChoice phase: Winner chooses who goes first
    // ACTION_TURN_CHOICE_FIRST = 5000, ACTION_TURN_CHOICE_SECOND = 5001
    if cpu_state.phase == engine_rust::core::logic::Phase::TurnChoice {
        let _ = cpu_state.step(&db, 5000); // Choose to go first
        println!("After TurnChoice: CPU phase={:?}", cpu_state.phase);
    }
    
    // Now auto_step should advance through Active -> Energy -> Draw -> Main
    cpu_state.auto_step(&db);
    println!("After auto_step: CPU phase={:?}", cpu_state.phase);
    
    // Initialize GPU game state (copy from CPU)
    let mut gpu_state = cpu_state.to_gpu(&db);
    println!("GPU initial phase={}", gpu_state.phase);
    let mut rng = ShaderRng::new(seed);
    gpu_state.rng_state_lo = rng.x;
    gpu_state.rng_state_hi = rng.y;
    
    println!("\nStarting game simulation...\n");
    println!("{:<6} | {:<12} | {:<4} | {:<6} | {:<10} | {:<10}", 
             "Step", "Phase", "Turn", "Action", "CPU Lives", "GPU Lives");
    println!("{}", "-".repeat(70));
    
    let max_steps = 500;
    let mut sync_points = 0;
    let mut mismatches = 0;
    
    for step in 0..max_steps {
        // Check if game ended
        if cpu_state.is_terminal() || gpu_state.phase == PHASE_TERMINAL {
            println!("\nGame ended at step {} (CPU: {}, GPU: {})", 
                     step, cpu_state.is_terminal(), gpu_state.phase == PHASE_TERMINAL);
            break;
        }
        
        // Generate legal actions on CPU
        let current_p = cpu_state.current_player as usize;
        let mut legals = smallvec::SmallVec::<[i32; 32]>::new();
        cpu_state.generate_legal_actions(&db, current_p, &mut legals);
        
        if legals.is_empty() {
            println!("\nNo legal actions at step {}", step);
            break;
        }
        
        // Pick same random action for both
        let action = legals[(rng.jump() as usize) % legals.len()];
        
        // Step CPU
        let _ = cpu_state.step(&db, action);
        
        // Step GPU with forced action
        gpu_state.forced_action = action;
        gpu_state.is_debug = 0; // Enable auto-phase advance to match CPU behavior
        
        let mut gpu_output = vec![GpuGameState::default()];
        gpu_manager.run_single_step(&[gpu_state.clone()], &mut gpu_output);
        gpu_state = gpu_output[0].clone();
        
        // Sync RNG from GPU (GPU may have consumed RNG during auto-phase advance)
        rng.x = gpu_state.rng_state_lo;
        rng.y = gpu_state.rng_state_hi;
        
        // Get current stats
        let cpu_phase = cpu_state.phase as i32;
        let cpu_p0_lives = cpu_state.core.players[0].success_lives.len() as u32;
        let cpu_p1_lives = cpu_state.core.players[1].success_lives.len() as u32;
        let gpu_p0_lives = gpu_state.player0.lives_cleared_count;
        let gpu_p1_lives = gpu_state.player1.lives_cleared_count;
        
        // Compare at interactive phases (sync points)
        if is_interactive_phase(cpu_phase) && is_interactive_phase(gpu_state.phase) {
            sync_points += 1;
            
            let phase_match = cpu_phase == gpu_state.phase;
            let lives_match = cpu_p0_lives == gpu_p0_lives && cpu_p1_lives == gpu_p1_lives;
            let turn_match = cpu_state.turn as u32 == gpu_state.turn;
            
            let status = if phase_match && lives_match && turn_match { "OK" } else { "MISMATCH" };
            
            println!("{:<6} | {:<12} | {:<4} | {:<6} | {:<3}/{:<3}     | {:<3}/{:<3}     | {}", 
                     step, format!("{:?}", cpu_state.phase), cpu_state.turn, action,
                     cpu_p0_lives, cpu_p1_lives, gpu_p0_lives, gpu_p1_lives, status);
            
            if !phase_match || !lives_match || !turn_match {
                mismatches += 1;
                if !phase_match {
                    println!("  Phase: CPU={:?} GPU={}", cpu_state.phase, gpu_state.phase);
                }
                if !lives_match {
                    println!("  Lives: CPU=({},{}) GPU=({},{})", cpu_p0_lives, cpu_p1_lives, gpu_p0_lives, gpu_p1_lives);
                }
                if !turn_match {
                    println!("  Turn: CPU={} GPU={}", cpu_state.turn, gpu_state.turn);
                }
            }
        }
    }
    
    // Final comparison
    println!("\n=== Final State ===");
    let cpu_winner = cpu_state.get_winner();
    let gpu_winner = gpu_state.winner;
    let cpu_p0_lives = cpu_state.core.players[0].success_lives.len() as u32;
    let cpu_p1_lives = cpu_state.core.players[1].success_lives.len() as u32;
    let gpu_p0_lives = gpu_state.player0.lives_cleared_count;
    let gpu_p1_lives = gpu_state.player1.lives_cleared_count;
    
    println!("CPU: Winner={} P0_Lives={} P1_Lives={} Turns={}", 
             cpu_winner, cpu_p0_lives, cpu_p1_lives, cpu_state.turn);
    println!("GPU: Winner={} P0_Lives={} P1_Lives={} Turns={}", 
             gpu_winner, gpu_p0_lives, gpu_p1_lives, gpu_state.turn);
    
    println!("\n=== Summary ===");
    println!("Sync points checked: {}", sync_points);
    println!("Mismatches at sync points: {}", mismatches);
    
    let final_match = cpu_winner == gpu_winner && 
                      cpu_p0_lives == gpu_p0_lives && 
                      cpu_p1_lives == gpu_p1_lives;
    
    if final_match && mismatches == 0 {
        println!("\nSUCCESS: CPU and GPU are in sync!");
    } else if final_match {
        println!("\nPARTIAL: Final results match but intermediate states differed.");
    } else {
        println!("\nFAILURE: CPU and GPU diverged.");
        std::process::exit(1);
    }
}
