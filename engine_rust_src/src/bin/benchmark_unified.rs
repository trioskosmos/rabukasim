use engine_rust::core::logic::{CardDatabase, GameState, ACTION_SPACE};
use engine_rust::test_helpers::load_real_db;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

fn parse_deck(path: &str, db: &CardDatabase) -> Vec<i32> {
    let content = std::fs::read_to_string(path).unwrap_or_else(|_| String::new());
    if content.is_empty() {
        return vec![];
    }
    let mut ids = Vec::new();
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split('x').map(|s| s.trim()).collect();
        let no = parts[0];
        let count = if parts.len() > 1 {
            parts[1].parse::<usize>().unwrap_or(1)
        } else {
            1
        };
        if let Some(&id) = db.card_no_to_id.get(no) {
            for _ in 0..count {
                ids.push(id);
            }
        }
    }
    ids
}

/// Run a single-threaded benchmark, returns (games, steps)
fn run_single_thread(
    initial_state: &GameState,
    db: &CardDatabase,
    duration: Duration,
    seed: u64,
) -> (u64, u64) {
    let mut total_games: u64 = 0;
    let mut total_steps: u64 = 0;
    let start = Instant::now();
    let mut rng_state = seed;

    // Pre-allocate action mask on stack (avoid heap alloc per step)
    let mut mask = vec![false; ACTION_SPACE];

    while start.elapsed() < duration {
        let mut sim = initial_state.clone();
        let mut steps: u64 = 0;

        while !sim.is_terminal() && steps < 1000 {
            // Reuse pre-allocated mask
            mask.fill(false);
            sim.get_legal_actions_into(db, sim.current_player as usize, &mut mask);

            // Collect valid actions without heap alloc (use SmallVec-like inline)
            let mut valid_count = 0u32;
            let mut first_valid: i32 = -1;
            for (i, &b) in mask.iter().enumerate() {
                if b {
                    if first_valid < 0 {
                        first_valid = i as i32;
                    }
                    valid_count += 1;
                }
            }

            if valid_count == 0 {
                break;
            }

            // Xorshift RNG
            rng_state ^= rng_state << 13;
            rng_state ^= rng_state >> 17;
            rng_state ^= rng_state << 5;
            let target_idx = (rng_state as u32) % valid_count;

            // Find the nth valid action
            let mut count = 0u32;
            let mut chosen_action = first_valid;
            for (i, &b) in mask.iter().enumerate() {
                if b {
                    if count == target_idx {
                        chosen_action = i as i32;
                        break;
                    }
                    count += 1;
                }
            }

            let _ = sim.step(db, chosen_action);
            steps += 1;
        }

        total_games += 1;
        total_steps += steps;
    }
    (total_games, total_steps)
}

fn main() {
    println!("=== Unified Rust CPU Benchmark (10s Challenge) ===");
    let db = load_real_db();

    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() {
        "ai/decks/muse_cup.txt"
    } else {
        "../ai/decks/muse_cup.txt"
    };

    let p_deck = parse_deck(deck_path, &db);
    let p_main = if p_deck.is_empty() {
        println!(
            "Warning: Could not find deck at {}, using fallback.",
            deck_path
        );
        db.members.keys().take(50).cloned().collect()
    } else {
        p_deck
    };

    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    let mut initial_state = GameState::default();
    initial_state.initialize_game(
        p_main.clone(),
        p_main.clone(),
        energy_ids.clone(),
        energy_ids.clone(),
        Vec::new(),
        Vec::new(),
    );
    initial_state.ui.silent = true;
    initial_state.phase = engine_rust::core::logic::Phase::Main;

    let bench_duration = Duration::from_secs(10);
    let num_threads = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4);

    println!("Threads: {}", num_threads);

    // --- Single-threaded benchmark ---
    println!("\n--- Single-Threaded ---");
    let (st_games, st_steps) = run_single_thread(&initial_state, &db, bench_duration, 12345);
    let st_dur = 10.0f64; // approximate
    println!("Games:       {}", st_games);
    println!("Steps:       {}", st_steps);
    println!("Games/sec:   {:.2}", st_games as f64 / st_dur);
    println!("Steps/sec:   {:.2}", st_steps as f64 / st_dur);
    println!(
        "Avg Steps/g: {:.1}",
        st_steps as f64 / st_games.max(1) as f64
    );

    // --- Multi-threaded benchmark ---
    println!("\n--- Multi-Threaded ({} threads) ---", num_threads);
    let total_games = Arc::new(AtomicU64::new(0));
    let total_steps = Arc::new(AtomicU64::new(0));

    let start_time = Instant::now();
    std::thread::scope(|s| {
        for t in 0..num_threads {
            let db_ref = &db;
            let state_ref = &initial_state;
            let games_ref = Arc::clone(&total_games);
            let steps_ref = Arc::clone(&total_steps);

            s.spawn(move || {
                let seed = 12345u64.wrapping_add(t as u64 * 7919);
                let (g, st) = run_single_thread(state_ref, db_ref, bench_duration, seed);
                games_ref.fetch_add(g, Ordering::Relaxed);
                steps_ref.fetch_add(st, Ordering::Relaxed);
            });
        }
    });
    let mt_dur = start_time.elapsed().as_secs_f64();

    let mt_games = total_games.load(Ordering::Relaxed);
    let mt_steps = total_steps.load(Ordering::Relaxed);

    println!("Games:       {}", mt_games);
    println!("Steps:       {}", mt_steps);
    println!("Games/sec:   {:.2}", mt_games as f64 / mt_dur);
    println!("Steps/sec:   {:.2}", mt_steps as f64 / mt_dur);
    println!(
        "Avg Steps/g: {:.1}",
        mt_steps as f64 / mt_games.max(1) as f64
    );
    println!(
        "Speedup:     {:.2}x",
        mt_steps as f64 / st_steps.max(1) as f64
    );

    println!("\n=== Done ===");
}
