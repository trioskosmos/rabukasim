
use std::sync::Arc;
use engine_rust::core::logic::{GameState, CardDatabase};
// use engine_rust::core::enums::Phase;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::core::gpu_state::GpuGameState;
use engine_rust::core::gpu_manager::GpuManager;

struct ShaderRng {
    x: u32,
    y: u32,
}

impl ShaderRng {
    fn new(lo: u32, hi: u32) -> Self {
        Self { x: lo, y: hi }
    }

    fn jump(&mut self) -> u32 {
        self.x ^= self.y << 13;
        self.y ^= self.x >> 7;
        self.x ^= self.y << 17;
        self.x.wrapping_add(self.y)
    }
}

fn get_gpu_hand(result: &GpuGameState, p: usize) -> Vec<i32> {
    let mut hand = Vec::new();
    let player = if p == 0 { &result.player0 } else { &result.player1 };
    for i in 0..player.hand_len {
        let card = (player.hand[i as usize / 2] >> ((i % 2) * 16)) & 0xFFFF;
        hand.push(card as i32);
    }
    hand
}

#[allow(dead_code)]
fn get_gpu_stage(result: &GpuGameState, p: usize) -> Vec<i16> {
    let mut stage = Vec::new();
    let player = if p == 0 { &result.player0 } else { &result.player1 };
    for i in 0..3 {
        let card = (player.stage[i / 2] >> ((i % 2) * 16)) & 0xFFFF;
        stage.push(if card == 0 { -1 } else { card as i16 });
    }
    stage
}

fn main() {
    eprintln!("DIAG: main() entered, spawning 8MB thread...");
    // Naga's recursive WGSL compiler needs a massive stack for complex shaders.
    let builder = std::thread::Builder::new()
        .name("gpu-parity-main".into())
        .stack_size(32 * 1024 * 1024);
    let handler = builder.spawn(real_main).expect("Failed to spawn main thread");
    handler.join().expect("Main thread panicked");
}

fn real_main() {
    println!("DEBUG: Main start");
    println!("GpuGameState Size: {}", std::mem::size_of::<GpuGameState>());
    println!("GpuPlayerState Size: {}", std::mem::size_of::<engine_rust::core::gpu_state::GpuPlayerState>());

    // Check offsets
    let base = GpuGameState::default();
    let base_ptr = &base as *const _ as usize;
    let p0_ptr = &base.player0 as *const _ as usize;
    let p1_ptr = &base.player1 as *const _ as usize;
    let phase_ptr = &base.phase as *const _ as usize;

    println!("Offset Player 0: {}", p0_ptr - base_ptr);
    println!("Offset Player 1: {}", p1_ptr - base_ptr);
    println!("Offset Phase: {}", phase_ptr - base_ptr);

    let p0_base = &base.player0 as *const _ as usize;
    println!("P0 DeckLen Offset: {}", (&base.player0.deck_len as *const _ as usize) - p0_base);
    println!("P0 AvgHearts Offset: {}", (&base.player0.avg_hearts as *const _ as usize) - p0_base);

    let json_path = if std::path::Path::new("data/cards_compiled.json").exists() {
        "data/cards_compiled.json"
    } else {
        "../data/cards_compiled.json"
    };

    let json_str = std::fs::read_to_string(json_path).expect("Failed to read cards JSON");
    let db = CardDatabase::from_json(&json_str).expect("Failed to parse JSON");
    let (stats, bytecode) = db.convert_to_gpu();
    let gpu_manager = Arc::new(GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).expect("Failed to init GPU"));

    let p0_main: Vec<i32> = vec![1; 16];
    let p1_main: Vec<i32> = vec![1; 16];
    let p0_energy: Vec<i32> = vec![1; 10];
    let p1_energy: Vec<i32> = vec![1; 10];

    let mut state = Box::new(GameState::default());
    state.initialize_game(
        p0_main,
        p1_main,
        p0_energy,
        p1_energy,
        Vec::new(), Vec::new(),
    );

    // Skip setup
    for act in [10000, 11001, 5000, 0, 0, 0, 0] { let _ = state.step(&db, act); }

    let mut rng = ShaderRng::new(12345, 67890);

    println!("{:<4} | {:3} | {:<12} | {:<4} | {:<5} | {:<7} | {:<7} | F", "Step", "P", "Phase", "Turn", "Act", "Hand", "Energy", );
    println!("--------------------------------------------------------------------------------------------");

    for step in 0..100 {
        if state.is_terminal() { break; }
        let current_p = state.current_player as usize;
        let mut legals = smallvec::SmallVec::<[i32; 32]>::new();
        state.generate_legal_actions(&db, current_p, &mut legals);
        if legals.is_empty() { break; }

        let action = legals[(rng.jump() as usize) % legals.len()];

        // 1. Snapshot for GPU
        let mut gpu_input = state.to_gpu(&db);
        gpu_input.rng_state_lo = rng.x;
        gpu_input.rng_state_hi = rng.y;
        gpu_input.forced_action = action;
        gpu_input.is_debug = 1;  // Mark as debug for single-step semantics

        let mut gpu_output = vec![GpuGameState::default(); 1];
        gpu_manager.run_single_step(&[gpu_input], &mut gpu_output);
        let result = &gpu_output[0];

        // 2. Step CPU
        let _cpu_h_len_before = state.core.players[current_p].hand.len();
        let _cpu_e_len_before = state.core.players[current_p].energy_zone.len();
        let _ = state.step(&db, action);

        let untap_cpu = state.core.players[current_p].energy_zone.len() - state.core.players[current_p].tapped_energy_mask.count_ones() as usize;
        let gpu_player = if current_p == 0 { &result.player0 } else { &result.player1 };
        let untap_gpu = gpu_player.energy_count - gpu_player.tapped_energy_count;

        println!("{:4} | {:3} | {:<12?} | {:<4} | {:<5} | {:<3}/{:<3} | {:<3}/{:<3} | {}:{}",
            step, current_p, state.phase, state.turn, action,
            state.core.players[current_p].hand.len(), gpu_player.hand_len,
            untap_cpu, untap_gpu,
            state.first_player, result.first_player
        );

        let mut mismatch = false;
        let gpu_player = if current_p == 0 { &result.player0 } else { &result.player1 };
        if state.turn as u32 != result.turn { mismatch = true; println!("  [!] Turn mismatch: CPU={}, GPU={}", state.turn, result.turn); }
        if state.phase as i32 != result.phase { mismatch = true; println!("  [!] Phase mismatch: CPU={:?}, GPU={}", state.phase, result.phase); }
        if state.core.players[current_p].hand.len() != gpu_player.hand_len as usize { mismatch = true; println!("  [!] Hand size mismatch: CPU={}, GPU={}", state.core.players[current_p].hand.len(), gpu_player.hand_len); }
        if state.first_player as u32 != result.first_player { mismatch = true; println!("  [!] FirstP mismatch: CPU={}, GPU={}", state.first_player, result.first_player); }
        if (state.core.players[current_p].energy_zone.len() as i32 - gpu_player.energy_count as i32).abs() > 0 {
             mismatch = true;
             println!("  [!] Energy Count mismatch: CPU={}, GPU={}", state.core.players[current_p].energy_zone.len(), gpu_player.energy_count);
        }

        if mismatch {
            let gpu_player = if current_p == 0 { &result.player0 } else { &result.player1 };
            println!("\nFAILURE at step {}. Detailed Breakdown:", step);
            println!("  Action: {}", action);
            println!("  CurrentPlayer: CPU={}, GPU={}", state.current_player, result.current_player);
            println!("  P{} Energy: CPU={}, GPU={} (Tapped: CPU={}, GPU={})", current_p, state.core.players[current_p].energy_zone.len(), gpu_player.energy_count, state.core.players[current_p].tapped_energy_mask.count_ones(), gpu_player.tapped_energy_count);
            println!("  P{} Hand CPU: {:?}", current_p, state.core.players[current_p].hand);
            println!("  P{} Hand GPU: {:?}", current_p, get_gpu_hand(result, current_p));
            println!("  P{} DeckLen: CPU={}, GPU={}", current_p, state.core.players[current_p].deck.len(), gpu_player.deck_len);
            if !state.interaction_stack.is_empty() {
                println!("  CPU Interaction Stack: {:?}", state.interaction_stack);
            }
            std::process::exit(1);
        }
    }
    println!("\nSUCCESS: Parity maintained!");
}
