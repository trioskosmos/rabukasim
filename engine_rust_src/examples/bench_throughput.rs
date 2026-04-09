//! Raw throughput benchmark - headless, silent, maximum speed

use engine_rust::core::logic::{CardDatabase, GameState};
use rand::prelude::IndexedRandom;
use rand::prelude::*;
use rayon::prelude::*;
use smallvec::SmallVec;
use std::fs;
use std::thread;
use std::time::Instant;

const DEFAULT_GAMES: usize = 1000;
const DEFAULT_WARMUP_GAMES: usize = 5;
const DEFAULT_MAX_STEPS: usize = 10_000;
const DEFAULT_TRACE_STEP_LIMIT: usize = 32;

#[derive(Debug, Clone, Copy)]
struct Config {
    games: usize,
    warmup_games: usize,
    workers: usize,
    max_steps: usize,
    seed: u64,
    trace_first_game: bool,
    trace_step_limit: usize,
    debug_mode: bool,
}

impl Config {
    fn from_env() -> Self {
        let default_workers = thread::available_parallelism()
            .map(|count| count.get().min(8))
            .unwrap_or(8)
            .max(1);
        Self {
            games: env_usize("BENCH_GAMES", DEFAULT_GAMES),
            warmup_games: env_usize("BENCH_WARMUP_GAMES", DEFAULT_WARMUP_GAMES),
            workers: env_usize("BENCH_WORKERS", default_workers).max(1),
            max_steps: env_usize("BENCH_MAX_STEPS", DEFAULT_MAX_STEPS),
            seed: env_u64("BENCH_SEED", 0),
            trace_first_game: env_bool("BENCH_TRACE_FIRST_GAME", false),
            trace_step_limit: env_usize("BENCH_TRACE_STEP_LIMIT", DEFAULT_TRACE_STEP_LIMIT),
            debug_mode: env_bool("BENCH_DEBUG_MODE", false),
        }
    }
}

fn env_u64(key: &str, default: u64) -> u64 {
    std::env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn env_usize(key: &str, default: usize) -> usize {
    std::env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn env_bool(key: &str, default: bool) -> bool {
    std::env::var(key)
        .ok()
        .and_then(|value| match value.to_ascii_lowercase().as_str() {
            "1" | "true" | "yes" | "on" => Some(true),
            "0" | "false" | "no" | "off" => Some(false),
            _ => None,
        })
        .unwrap_or(default)
}

fn load_db() -> CardDatabase {
    for path in &["data/cards_compiled.json", "../data/cards_compiled.json"] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = true;
            return db;
        }
    }
    panic!("DB not found");
}

fn build_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut deck: Vec<i32> = db.members.keys().copied().collect();
    let mut lives: Vec<i32> = db.lives.keys().copied().collect();
    let mut energy: Vec<i32> = db.energy_db.keys().copied().collect();

    deck.sort_unstable();
    lives.sort_unstable();
    energy.sort_unstable();

    deck.truncate(48);
    lives.truncate(12);
    energy.truncate(12);

    while deck.len() < 48 {
        if let Some(&card_id) = deck.first() {
            deck.push(card_id);
        } else {
            break;
        }
    }
    while lives.len() < 12 {
        if let Some(&card_id) = lives.first() {
            lives.push(card_id);
        } else {
            break;
        }
    }
    while energy.len() < 12 {
        if let Some(&card_id) = energy.first() {
            energy.push(card_id);
        } else {
            break;
        }
    }

    (deck, lives, energy)
}

fn run_headless_game(
    db: &CardDatabase,
    deck: &[i32],
    lives: &[i32],
    energy: &[i32],
    seed: u64,
    game_index: usize,
    max_steps: usize,
    trace_first_game: bool,
    trace_step_limit: usize,
    debug_mode: bool,
) -> (u32, u64, bool, i32) {
    let mut state = GameState::default();
    state.initialize_game(
        deck.to_vec(),
        deck.to_vec(),
        energy.to_vec(),
        energy.to_vec(),
        lives.to_vec(),
        lives.to_vec(),
    );

    // HEADLESS MODE - disable all UI/logging
    state.ui.silent = true;
    state.debug.debug_mode = debug_mode;

    let mut rng = StdRng::seed_from_u64(seed);
    let mut total_steps = 0u32;
    let mut legal: SmallVec<[i32; 64]> = SmallVec::new();
    let trace = trace_first_game && game_index == 0;

    let start = Instant::now();

    if trace {
        println!(
            "[game {}] start phase={:?} turn={} p={}",
            game_index, state.phase, state.turn, state.current_player
        );
    }

    while !state.is_terminal() && (total_steps as usize) < max_steps {
        let phase_before = state.phase;
        legal.clear();
        state.generate_legal_actions(db, state.current_player as usize, &mut legal);
        if legal.len() > 1 {
            legal.sort_unstable();
            legal.dedup();
        }
        if legal.is_empty() {
            if trace && (total_steps as usize) < trace_step_limit {
                println!(
                    "[game {}] step={} phase={:?} action=auto_step",
                    game_index, total_steps, phase_before
                );
            }
            state.auto_step(db);
        } else {
            let action = *legal.choose(&mut rng).unwrap_or(&0);
            if trace && (total_steps as usize) < trace_step_limit {
                println!(
                    "[game {}] step={} phase={:?} legal={} action={}",
                    game_index,
                    total_steps,
                    phase_before,
                    legal.len(),
                    action,
                );
            }
            let _ = state.step(db, action);
        }
        total_steps += 1;
    }

    let elapsed_ns = start.elapsed().as_nanos() as u64;
    let reached_terminal = state.is_terminal();
    let winner = if reached_terminal {
        state.get_winner()
    } else {
        -1
    };

    if trace {
        println!(
            "[game {}] end terminal={} winner={} steps={} p0_success={} p1_success={}",
            game_index,
            reached_terminal,
            winner,
            total_steps,
            state.players[0].success_lives.len(),
            state.players[1].success_lives.len(),
        );
    }

    (total_steps, elapsed_ns, reached_terminal, winner)
}

fn main() {
    let config = Config::from_env();
    println!("=== Raw Throughput Benchmark (Headless/Silent) ===\n");
    println!(
        "games={} warmup_games={} workers={} max_steps={} seed={} trace_first_game={} debug_mode={}",
        config.games,
        config.warmup_games,
        config.workers,
        config.max_steps,
        config.seed,
        config.trace_first_game,
        config.debug_mode,
    );

    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);

    // Warmup
    println!("Warming up...");
    for _ in 0..config.warmup_games {
        let _ = run_headless_game(
            &db,
            &deck,
            &lives,
            &energy,
            42,
            0,
            config.max_steps,
            false,
            0,
            false,
        );
    }

    println!("Running {} games...", config.games);
    let bench_start = Instant::now();

    let run_game = |index: usize| {
        let seed = config.seed.wrapping_add(index as u64);
        run_headless_game(
            &db,
            &deck,
            &lives,
            &energy,
            seed,
            index,
            config.max_steps,
            config.trace_first_game,
            config.trace_step_limit,
            config.debug_mode,
        )
    };

    let mut results: Vec<(u32, u64, bool, i32)> = Vec::with_capacity(config.games);
    if config.trace_first_game && config.games > 0 {
        results.push(run_game(0));
    }

    if config.workers <= 1 {
        let start_index = if config.trace_first_game { 1 } else { 0 };
        results.extend((start_index..config.games).map(run_game));
    } else {
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(config.workers)
            .build()
            .expect("build benchmark thread pool");

        pool.install(|| {
            let start_index = if config.trace_first_game { 1 } else { 0 };
            let mut parallel_results: Vec<(u32, u64, bool, i32)> = (start_index..config.games)
                .into_par_iter()
                .map(run_game)
                .collect();
            results.append(&mut parallel_results);
        });
    }

    let mut total_steps = 0u64;
    let mut total_ns = 0u64;
    let mut min_ns = u64::MAX;
    let mut max_ns = 0u64;
    let mut terminal_games = 0usize;
    let mut p0_wins = 0usize;
    let mut p1_wins = 0usize;
    let mut draws = 0usize;

    for (steps, ns, reached_terminal, winner) in results.iter().copied() {
        total_steps += steps as u64;
        total_ns += ns;
        min_ns = min_ns.min(ns);
        max_ns = max_ns.max(ns);
        if reached_terminal {
            terminal_games += 1;
            match winner {
                0 => p0_wins += 1,
                1 => p1_wins += 1,
                2 => draws += 1,
                _ => {}
            }
        }
    }

    let bench_ns = bench_start.elapsed().as_nanos() as u64;

    // Stats
    let avg_ns_per_game = total_ns / config.games.max(1) as u64;
    let avg_steps_per_game = total_steps / config.games.max(1) as u64;
    let ns_per_step = total_ns / total_steps;

    let wall_games_per_sec = config.games as f64 / bench_ns as f64 * 1_000_000_000.0;
    let wall_steps_per_sec = total_steps as f64 / bench_ns as f64 * 1_000_000_000.0;

    println!("\n=== Results ===");
    println!("Games:        {}", config.games);
    println!(
        "Terminal:     {} (P0={} P1={} Draw={})",
        terminal_games, p0_wins, p1_wins, draws
    );
    println!(
        "Capped:       {}",
        config.games.saturating_sub(terminal_games)
    );
    println!("Total steps:  {}", total_steps);
    println!("Avg steps/game: {}", avg_steps_per_game);
    println!(
        "\nTime per game: {}μs (min: {}μs, max: {}μs)",
        avg_ns_per_game / 1000,
        min_ns / 1000,
        max_ns / 1000
    );
    println!("Time per step: {}ns", ns_per_step);
    println!("\nThroughput:");
    println!("  Wall-clock games/sec: {:.0}", wall_games_per_sec);
    println!("  Wall-clock steps/sec: {:.0}", wall_steps_per_sec);
    println!("\nTotal benchmark time: {}ms", bench_ns / 1_000_000);
}
