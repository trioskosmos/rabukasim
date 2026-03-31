//! Real Game Granular Benchmark - Uses actual TurnSequencer like frontend

use std::time::Instant;
use std::io::Write;
use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use rand::prelude::{StdRng, IndexedRandom, SeedableRng, Rng};

#[derive(Debug, Clone, Copy, PartialEq)]
enum SubPhase {
    HandleLivesetP1,
    HandleLivesetP2,
    PerformanceP1,
    PerformanceP2,
    LiveResult,
    Main,
    Active,
    Energy,
    Draw,
    Other,
    StepCall,
}

struct GranularTimer {
    timers: Vec<(SubPhase, Vec<u64>)>,
}

impl GranularTimer {
    fn new() -> Self {
        Self {
            timers: vec![
                (SubPhase::HandleLivesetP1, Vec::new()),
                (SubPhase::HandleLivesetP2, Vec::new()),
                (SubPhase::PerformanceP1, Vec::new()),
                (SubPhase::PerformanceP2, Vec::new()),
                (SubPhase::LiveResult, Vec::new()),
                (SubPhase::Main, Vec::new()),
                (SubPhase::Active, Vec::new()),
                (SubPhase::Energy, Vec::new()),
                (SubPhase::Draw, Vec::new()),
                (SubPhase::Other, Vec::new()),
                (SubPhase::StepCall, Vec::new()),
            ],
        }
    }

    fn record(&mut self, phase: SubPhase, nanos: u64) {
        for (p, timings) in &mut self.timers {
            if *p == phase {
                timings.push(nanos);
                break;
            }
        }
    }

    fn print_stats(&self) {
        println!("\n=== Granular Phase Timing ===");
        println!("{:<15} {:<6} {:<12} {:<10} {:<10}", "Phase", "Count", "Total(ns)", "Avg(μs)", "Max(μs)");
        println!("{}", "-".repeat(65));
        
        for (phase, timings) in &self.timers {
            if timings.is_empty() {
                continue;
            }
            let count = timings.len();
            let total: u64 = timings.iter().sum();
            let avg = total / count as u64;
            let max = timings.iter().max().unwrap();
            
            println!("{:<15} {:<6} {:>12} {:>10} {:>10}", 
                format!("{:?}", phase), 
                count, 
                total, 
                avg / 1000, 
                max / 1000);
        }
        println!("{}", "-".repeat(65));
        
        let grand_total: u64 = self.timers.iter().flat_map(|(_, timings)| timings).sum();
        println!("TOTAL                            {:>10.2}μs", grand_total as f64 / 1000.0);
    }
}

fn load_db() -> CardDatabase {
    let candidates = [
        "data/cards_compiled.json",
        "../data/cards_compiled.json",
        "../../data/cards_compiled.json",
    ];

    for path in &candidates {
        if !std::path::Path::new(path).exists() {
            continue;
        }
        let json = std::fs::read_to_string(path).expect("Failed to read DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
        db.is_vanilla = false;
        return db;
    }
    panic!("cards_compiled.json not found");
}

fn load_deck(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let content = std::fs::read_to_string(path).expect("Failed to read deck");
    let mut members = Vec::new();
    let mut lives = Vec::new();

    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.is_empty() {
            continue;
        }

        let card_no = parts[0];
        let count: usize = if parts.len() >= 3 && parts[1] == "x" {
            parts[2].parse().unwrap_or(1)
        } else {
            1
        };

        if let Some(id) = db.id_by_no(card_no) {
            for _ in 0..count {
                if db.lives.contains_key(&id) {
                    lives.push(id);
                } else {
                    members.push(id);
                }
            }
        }
    }

    while members.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            members.push(id);
        } else {
            break;
        }
    }
    while lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            lives.push(id);
        } else {
            break;
        }
    }

    members.truncate(48);
    lives.truncate(12);

    (members, lives)
}

fn resolve_deck_path(spec: &str) -> String {
    let direct = std::path::Path::new(spec);
    if direct.exists() {
        return spec.to_string();
    }

    for base in [std::path::Path::new("ai/decks"), std::path::Path::new("../ai/decks")] {
        let candidate = base.join(format!("{}.txt", spec));
        if candidate.exists() {
            return candidate.to_string_lossy().into_owned();
        }
    }

    spec.to_string()
}

fn run_real_game_benchmark(
    state: &mut GameState,
    db: &CardDatabase,
    timer: &mut GranularTimer,
    max_turns: usize,
    log_file: &mut std::fs::File,
    action_summary: &mut Vec<String>,
) -> u64 {
    let start = Instant::now();
    let mut total_evaluations: usize = 0;
    let mut main_turns_played = 0usize;
    let mut rng = StdRng::seed_from_u64(42);
    let mut step_count = 0;

    writeln!(log_file, "=== GAME START ===").unwrap();
    writeln!(log_file, "Initial Phase: {:?}, Player: {}, Turn: {}", state.phase, state.current_player, state.turn).unwrap();
    
    // Log initial state
    for p in 0..2 {
        let hand = &state.core.players[p].hand;
        let live_in_hand = hand.iter().filter(|&&cid| db.get_live(cid).is_some()).count();
        let member_in_hand = hand.iter().filter(|&&cid| db.get_member(cid).is_some()).count();
        writeln!(log_file, "P{} Hand: {} cards ({} live, {} member) {:?}", 
            p, hand.len(), live_in_hand, member_in_hand, hand).unwrap();
        writeln!(log_file, "P{} Live: {:?}", p, state.core.players[p].live_zone).unwrap();
        writeln!(log_file, "P{} Stage: {:?}", p, state.core.players[p].stage).unwrap();
    }

    // Advance to first Main phase (RPS, Mulligan, etc.)
    while state.phase != Phase::Main && !state.is_terminal() {
        let phase_before = state.phase;
        let t = Instant::now();
        
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                let legal = state.get_legal_action_ids(db);
                if !legal.is_empty() {
                    let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
                    let _ = state.step(db, action);
                } else {
                    let _ = state.step(db, ACTION_BASE_PASS);
                }
            }
            _ => {
                state.auto_step(db);
            }
        }
        
        let elapsed = t.elapsed().as_nanos() as u64;
        timer.record(SubPhase::StepCall, elapsed);
        
        // Phase attribution
        match (phase_before, state.phase) {
            (Phase::Rps, _) => timer.record(SubPhase::Other, elapsed),
            (Phase::MulliganP1, _) => timer.record(SubPhase::Other, elapsed),
            (Phase::MulliganP2, _) => timer.record(SubPhase::Other, elapsed),
            _ => timer.record(SubPhase::Other, elapsed),
        }
    }

    // Main game loop with real gameplay
    let mut consecutive_pass_count = 0;
    let mut last_phase = Phase::Rps;
    
    while !state.is_terminal() && main_turns_played < (max_turns * 2) && step_count < 5000 {
        step_count += 1;
        let phase_before = state.phase;
        let player_before = state.current_player;
        
        writeln!(log_file, "\n=== STEP {} ===", step_count).unwrap();
        writeln!(log_file, "Phase: {:?}, Player: {}", phase_before, player_before).unwrap();
        
        // Get legal actions
        let legal = state.get_legal_action_ids(db);
        writeln!(log_file, "Legal actions: {} available", legal.len()).unwrap();
        
        // ANTI-SOFTLOCK: Detect phase loops
        if phase_before == last_phase && legal.len() == 1 {
            consecutive_pass_count += 1;
            if consecutive_pass_count > 50 {
                writeln!(log_file, "ANTI_SOFTLOCK: Breaking phase loop after {} consecutive PASS actions in phase {:?}", consecutive_pass_count, phase_before).unwrap();
                break;
            }
        } else {
            consecutive_pass_count = 0;
            last_phase = phase_before;
        }
        
        // Log ALL legal actions
        for (i, &action) in legal.iter().enumerate() {
            let action_str = if action == ACTION_BASE_PASS {
                "PASS".to_string()
            } else if (400..=459).contains(&action) {
                format!("LIVESET(hand={})", action - 400)
            } else if (1..=180).contains(&action) {
                let hand_idx = (action - 1) / 3;
                let slot_idx = (action - 1) % 3;
                let areas = ["Left", "Center", "Right"];
                format!("PLAY(hand={}, area={})", hand_idx, areas[slot_idx as usize])
            } else if (300..=359).contains(&action) {
                format!("MULLIGAN(hand={})", action - 300)
            } else if (500..=509).contains(&action) {
                format!("SELECT_HAND(hand={})", action - 500)
            } else if (560..=562).contains(&action) {
                let areas = ["Left", "Center", "Right"];
                format!("SELECT_STAGE(area={})", areas[(action - 560) as usize])
            } else if (580..=585).contains(&action) {
                let colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Pink"];
                format!("COLOR({})", colors[(action - 580) as usize])
            } else if (900..=902).contains(&action) {
                let areas = ["Left", "Center", "Right"];
                format!("PERFORMANCE(area={})", areas[(action - 900) as usize])
            } else {
                format!("ACTION({})", action)
            };
            writeln!(log_file, "  {}: {}", i, action_str).unwrap();
        }
        
        // Show current scores
        writeln!(log_file, "Scores - P0: {} (Success: {}), P1: {} (Success: {})", 
            state.core.players[0].score, state.core.players[0].success_lives.len(),
            state.core.players[1].score, state.core.players[1].success_lives.len()).unwrap();
        
        // Make RANDOM decision (not always first)
        let chosen_action = if legal.is_empty() {
            ACTION_BASE_PASS
        } else {
            let random_idx = rng.gen_range(0..legal.len());
            legal[random_idx]
        };
        
        writeln!(log_file, "RANDOMLY chose action {} (index {})", chosen_action, 
            legal.iter().position(|&x| x == chosen_action).unwrap_or(999)).unwrap();
        
        // Execute the chosen action
        let t = Instant::now();
        let result = state.step(db, chosen_action);
        let elapsed = t.elapsed().as_nanos() as u64;
        timer.record(SubPhase::StepCall, elapsed);
        
        let action_str = if chosen_action == ACTION_BASE_PASS {
            "PASS".to_string()
        } else if (400..=459).contains(&chosen_action) {
            format!("LIVESET(hand={})", chosen_action - 400)
        } else if (1..=180).contains(&chosen_action) {
            let hand_idx = (chosen_action - 1) / 3;
            let slot_idx = (chosen_action - 1) % 3;
            let areas = ["Left", "Center", "Right"];
            format!("PLAY(hand={}, area={})", hand_idx, areas[slot_idx as usize])
        } else if (300..=359).contains(&chosen_action) {
            format!("MULLIGAN(hand={})", chosen_action - 300)
        } else if (500..=509).contains(&chosen_action) {
            format!("SELECT_HAND(hand={})", chosen_action - 500)
        } else if (560..=562).contains(&chosen_action) {
            let areas = ["Left", "Center", "Right"];
            format!("SELECT_STAGE(area={})", areas[(chosen_action - 560) as usize])
        } else if (580..=585).contains(&chosen_action) {
            let colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Pink"];
            format!("COLOR({})", colors[(chosen_action - 580) as usize])
        } else if (900..=902).contains(&chosen_action) {
            let areas = ["Left", "Center", "Right"];
            format!("PERFORMANCE(area={})", areas[(chosen_action - 900) as usize])
        } else {
            format!("ACTION({})", chosen_action)
        };
        writeln!(log_file, "Executed: {} ({}μs) - Result: {:?}", action_str, elapsed / 1000, result).unwrap();
        
        // Add to action summary
        action_summary.push(format!("Step {}: {} - {}μs", step_count, action_str, elapsed / 1000));
        
        // Record phase timing
        match phase_before {
            Phase::Main => timer.record(SubPhase::Main, elapsed),
            Phase::LiveSet => timer.record(SubPhase::HandleLivesetP1, elapsed),
            Phase::PerformanceP1 => timer.record(SubPhase::PerformanceP1, elapsed),
            Phase::PerformanceP2 => timer.record(SubPhase::PerformanceP2, elapsed),
            Phase::LiveResult => timer.record(SubPhase::LiveResult, elapsed),
            Phase::Active => timer.record(SubPhase::Active, elapsed),
            Phase::Draw => timer.record(SubPhase::Draw, elapsed),
            Phase::Energy => timer.record(SubPhase::Energy, elapsed),
            _ => timer.record(SubPhase::Other, elapsed),
        }
        
        // Log state changes
        if phase_before != state.phase {
            writeln!(log_file, "PHASE CHANGE: {:?} -> {:?}", phase_before, state.phase).unwrap();
        }
        if player_before != state.current_player {
            writeln!(log_file, "PLAYER CHANGE: {} -> {}", player_before, state.current_player).unwrap();
        }
        
        // Log state after key phases
        if matches!(phase_before, Phase::LiveSet) || matches!(phase_before, Phase::Main) {
            for p in 0..2 {
                let hand = &state.core.players[p].hand;
                let live_in_hand = hand.iter().filter(|&&cid| db.get_live(cid).is_some()).count();
                let member_in_hand = hand.iter().filter(|&&cid| db.get_member(cid).is_some()).count();
                writeln!(log_file, "P{} Hand: {} cards ({} live, {} member)", 
                    p, hand.len(), live_in_hand, member_in_hand).unwrap();
                writeln!(log_file, "P{} Live: {:?}", p, state.core.players[p].live_zone).unwrap();
                writeln!(log_file, "P{} Stage: {:?}", p, state.core.players[p].stage).unwrap();
            }
        }
    }

    writeln!(log_file, "\n=== GAME END ===").unwrap();
    writeln!(log_file, "Final Phase: {:?}", state.phase).unwrap();
    writeln!(log_file, "Total Steps: {}", step_count).unwrap();
    writeln!(log_file, "Main Turns: {}", main_turns_played).unwrap();
    if step_count >= 5000 {
        writeln!(log_file, "GAME STOPPED: Reached 5000 step limit").unwrap();
    }
    start.elapsed().as_nanos() as u64
}

fn main() {
    use std::time::Instant;
    
    let db = load_db();
    let deck_path = resolve_deck_path("muse_cup");
    let p0_deck = load_deck(&deck_path, &db);
    let p1_deck = load_deck(&deck_path, &db);
    
    const RUNS: usize = 3;
    const MAX_TURNS: usize = 5; // Short games for benchmarking
    let mut timer = GranularTimer::new();
    let mut total_times = Vec::new();
    let mut all_actions = Vec::new();
    
    // Create log file
    let mut log_file = std::fs::File::create("game_log.txt").expect("Failed to create game_log.txt");
    
    let benchmark_start = Instant::now();
    let mut games_completed = 0;
    
    // Run for 10 seconds
    while benchmark_start.elapsed().as_secs() < 10 {
        writeln!(log_file, "\n{}", "=".repeat(60)).unwrap();
        writeln!(log_file, "GAME {}", games_completed + 1).unwrap();
        writeln!(log_file, "{}", "=".repeat(60)).unwrap();
        
        let mut state = GameState::default();
        let energy = vec![49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60];
        state.initialize_game(
            p0_deck.0.clone(),
            p1_deck.0.clone(),
            energy.clone(),
            energy.clone(),
            p0_deck.1.clone(),
            p1_deck.1.clone(),
        );
        
        state.ui.silent = true; // No UI output
        
        let total_ns = run_real_game_benchmark(&mut state, &db, &mut timer, MAX_TURNS, &mut log_file, &mut all_actions);
        total_times.push(total_ns);
        games_completed += 1;
        
        // Silent - no per-run output
    }
    
    log_file.flush().unwrap();
    drop(log_file);
    
    // Calculate actual runtime
    let total_runtime = benchmark_start.elapsed();
    
    // Only show final summary
    println!("=== REAL GAME GRANULAR BENCHMARK ===");
    println!("Benchmark duration: {:?}", total_runtime);
    println!("Games completed: {}", games_completed);
    println!("Game log written to: game_log.txt");
    timer.print_stats();
    
    total_times.sort();
    let min = total_times[0];
    let max = total_times[games_completed - 1];
    let avg = total_times.iter().sum::<u64>() / games_completed as u64;
    
    println!("\n=== Real Game Performance Summary ===");
    println!("Runs:    {}", games_completed);
    println!("Turns:   {} max per game", MAX_TURNS);
    println!("Min:     {}μs", min / 1000);
    println!("Max:     {}μs", max / 1000);
    println!("Avg:     {}μs", avg / 1000);
    println!("Total:   {}μs", total_times.iter().sum::<u64>() / 1000);
    
    println!("\n=== Action Summary ===");
    println!("Total actions executed: {}", all_actions.len());
    println!("Actions per game: {:.1}", all_actions.len() as f64 / games_completed as f64);
    
    // Write performance summary to log file
    let mut summary_file = std::fs::File::create("benchmark_summary.txt").expect("Failed to create benchmark_summary.txt");
    writeln!(summary_file, "=== REAL GAME GRANULAR BENCHMARK SUMMARY ===").unwrap();
    writeln!(summary_file, "Benchmark duration: {:?}", total_runtime).unwrap();
    writeln!(summary_file, "Games completed: {}", games_completed).unwrap();
    writeln!(summary_file, "Actions per game: {:.1}", all_actions.len() as f64 / games_completed as f64).unwrap();
    writeln!(summary_file, "").unwrap();
    writeln!(summary_file, "=== Performance Metrics ===").unwrap();
    writeln!(summary_file, "Min game time: {}μs", min / 1000).unwrap();
    writeln!(summary_file, "Max game time: {}μs", max / 1000).unwrap();
    writeln!(summary_file, "Avg game time: {}μs", avg / 1000).unwrap();
    writeln!(summary_file, "Total game time: {}μs", total_times.iter().sum::<u64>() / 1000).unwrap();
    writeln!(summary_file, "").unwrap();
    writeln!(summary_file, "=== Phase Timing (from print_stats output) ===").unwrap();
    writeln!(summary_file, "See console output for detailed phase timing breakdown").unwrap();
    summary_file.flush().unwrap();
    drop(summary_file);
    println!("Performance summary written to: benchmark_summary.txt");
    
    // Show first 10 and last 10 actions
    if all_actions.len() > 20 {
        println!("First 10 actions:");
        for action in all_actions.iter().take(10) {
            println!("  {}", action);
        }
        println!("...");
        println!("Last 10 actions:");
        for action in all_actions.iter().skip(all_actions.len() - 10) {
            println!("  {}", action);
        }
    } else {
        for action in &all_actions {
            println!("  {}", action);
        }
    }
    
    println!("\n=== Performance Analysis ===");
    println!("This benchmark uses:");
    println!("✓ Random actions (no AI overhead)");
    println!("✓ Actual deck parsing from AI/DECKS");
    println!("✓ Complete game flow (all phases)");
    println!("✓ Pure game speed measurement");
    println!("✓ No UI (headless mode)");
}
