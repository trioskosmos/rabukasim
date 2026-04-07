use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use rand::prelude::{Rng, SeedableRng, StdRng};
use std::time::Instant;

#[derive(Debug, Clone, Copy, PartialEq)]
enum SubPhase {
    Draw,
    HandleLivesetP1,
    Main,
    LiveResult,
    Other,
    StepCall,
}

#[derive(Default)]
struct GranularTimer {
    timers: Vec<(SubPhase, Vec<u64>)>,
}

impl GranularTimer {
    fn new() -> Self {
        Self {
            timers: vec![
                (SubPhase::Draw, Vec::new()),
                (SubPhase::HandleLivesetP1, Vec::new()),
                (SubPhase::Main, Vec::new()),
                (SubPhase::LiveResult, Vec::new()),
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
        println!(
            "{:<15} {:<6} {:<12} {:<10} {:<10}",
            "Phase", "Count", "Total(ns)", "Avg(μs)", "Max(μs)"
        );
        println!("{}", "-".repeat(65));

        for (phase, timings) in &self.timers {
            if timings.is_empty() {
                continue;
            }
            let count = timings.len();
            let total: u64 = timings.iter().sum();
            let avg = total / count as u64;
            let max = timings.iter().max().unwrap();

            let phase_name = match phase {
                SubPhase::Draw => "Draw",
                SubPhase::HandleLivesetP1 => "HandleLivesetP1",
                SubPhase::Main => "Main",
                SubPhase::LiveResult => "LiveResult",
                SubPhase::Other => "Other",
                SubPhase::StepCall => "StepCall",
            };

            println!(
                "{:<15} {:<6} {:<12} {:<10} {:<10}",
                phase_name,
                count,
                total,
                avg / 1000,
                max / 1000
            );
        }
        println!("{}", "-".repeat(65));
        let total: u64 = self.timers.iter().flat_map(|(_, t)| t).sum();
        println!(
            "TOTAL                              {:.2}μs",
            total as f64 / 1000.0
        );
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

fn resolve_deck_path(deck_name: &str) -> String {
    let candidates = [
        format!("ai/decks/{}.txt", deck_name),
        format!("../ai/decks/{}.txt", deck_name),
        format!("../../ai/decks/{}.txt", deck_name),
    ];

    for path in &candidates {
        if std::path::Path::new(path).exists() {
            return path.clone();
        }
    }
    panic!("Deck {} not found", deck_name);
}

fn load_deck(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let content = std::fs::read_to_string(path).expect("Failed to read deck");
    let mut member_ids = Vec::new();
    let mut live_ids = Vec::new();

    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        if let Some(card_no_str) = line.strip_prefix("card_no=") {
            if let Ok(card_no) = card_no_str.parse::<i32>() {
                if let Some(card_id) = db.id_by_no(&card_no.to_string()) {
                    if card_id >= 4000 && card_id < 4100 {
                        live_ids.push(card_id);
                    } else if card_id >= 1000 && card_id < 1200 {
                        member_ids.push(card_id);
                    }
                }
            }
        }
    }

    (member_ids, live_ids)
}

fn run_fast_game_benchmark(
    state: &mut GameState,
    db: &CardDatabase,
    timer: &mut GranularTimer,
    max_turns: usize,
    rng: &mut StdRng,
) -> u64 {
    let start = Instant::now();
    let mut step_count = 0;
    let mut main_turns_played = 0;

    // Skip detailed logging for speed
    while !state.is_terminal() && main_turns_played < (max_turns * 2) && step_count < 5000 {
        step_count += 1;
        let phase_before = state.phase;

        // Get legal actions
        let legal = state.get_legal_action_ids(db);

        // Fast random selection
        let chosen_action = if legal.is_empty() {
            ACTION_BASE_PASS
        } else {
            let random_idx = rng.random_range(0..legal.len());
            legal[random_idx]
        };

        let step_start = Instant::now();
        let _result = state.step(db, chosen_action);
        let elapsed = step_start.elapsed().as_nanos() as u64;

        // Phase attribution
        match (phase_before, state.phase) {
            (Phase::Rps, _) => timer.record(SubPhase::Other, elapsed),
            (Phase::MulliganP1, _) => timer.record(SubPhase::Other, elapsed),
            (Phase::MulliganP2, _) => timer.record(SubPhase::Other, elapsed),
            _ => timer.record(SubPhase::Other, elapsed),
        }

        if state.phase == Phase::Main && phase_before != Phase::Main {
            main_turns_played += 1;
        }
    }

    start.elapsed().as_nanos() as u64
}

fn main() {
    use std::time::Instant;

    let db = load_db();
    let deck_path = resolve_deck_path("muse_cup");
    let p0_deck = load_deck(&deck_path, &db);
    let p1_deck = load_deck(&deck_path, &db);

    const MAX_TURNS: usize = 5;
    let mut timer = GranularTimer::new();
    let mut total_times = Vec::new();

    let benchmark_start = Instant::now();
    let mut games_completed = 0;

    // Use a single RNG for better performance
    let mut rng = StdRng::seed_from_u64(42);

    // Run for 10 seconds
    while benchmark_start.elapsed().as_secs() < 10 {
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

        state.ui.silent = true;

        let total_ns = run_fast_game_benchmark(&mut state, &db, &mut timer, MAX_TURNS, &mut rng);
        total_times.push(total_ns);
        games_completed += 1;
    }

    let total_runtime = benchmark_start.elapsed();

    // Only show final summary
    println!("=== FAST GAME BENCHMARK ===");
    println!("Benchmark duration: {:?}", total_runtime);
    println!("Games completed: {}", games_completed);
    println!(
        "Games per second: {:.1}",
        games_completed as f64 / total_runtime.as_secs_f64()
    );
    timer.print_stats();

    total_times.sort();
    let min = total_times[0];
    let max = total_times[games_completed - 1];
    let avg = total_times.iter().sum::<u64>() / games_completed as u64;

    println!("\n=== Fast Game Performance Summary ===");
    println!("Runs:    {}", games_completed);
    println!("Turns:   {} max per game", MAX_TURNS);
    println!("Min:     {}μs", min / 1000);
    println!("Max:     {}μs", max / 1000);
    println!("Avg:     {}μs", avg / 1000);
    println!("Total:   {}μs", total_times.iter().sum::<u64>() / 1000);

    println!("\n=== Performance Analysis ===");
    println!("This benchmark uses:");
    println!("✓ Random actions (no AI overhead)");
    println!("✓ Actual deck parsing from AI/DECKS");
    println!("✓ Complete game flow (all phases)");
    println!("✓ Pure game speed measurement");
    println!("✓ No UI (headless mode)");
    println!("✓ No file I/O overhead");
    println!("✓ Single RNG instance");
}
