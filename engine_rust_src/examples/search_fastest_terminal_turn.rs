//! Search for the fastest terminal game by turn count.
//!
//! The starting deck order is fixed by a deck shuffle seed, while each game
//! uses a derived action seed so the harness can explore many possible play
//! paths reproducibly.

use engine_rust::core::logic::{CardDatabase, GameState};
use rand::prelude::IndexedRandom;
use rand::prelude::*;
use rayon::prelude::*;
use std::fs;
use std::thread;
use std::time::Instant;

const DEFAULT_GAMES: usize = 10_000;
const DEFAULT_WARMUP_GAMES: usize = 5;
const DEFAULT_MAX_STEPS: usize = 10_000;

#[derive(Debug, Clone, Copy)]
struct Config {
    games: usize,
    warmup_games: usize,
    workers: usize,
    max_steps: usize,
    deck_seed: u64,
    action_seed: u64,
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
            deck_seed: env_u64("BENCH_DECK_SEED", 0),
            action_seed: env_u64("BENCH_ACTION_SEED", 0),
        }
    }
}

#[derive(Debug, Clone)]
struct GameOutcome {
    index: usize,
    action_seed: u64,
    turns: Option<u32>,
    steps: u32,
    elapsed_ns: u64,
    winner: i32,
    p0_success: usize,
    p1_success: usize,
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

fn run_game(
    db: &CardDatabase,
    deck: &[i32],
    lives: &[i32],
    energy: &[i32],
    deck_seed: u64,
    action_seed: u64,
    game_index: usize,
    max_steps: usize,
) -> GameOutcome {
    let mut state = GameState::default();
    state.initialize_game_with_seed(
        deck.to_vec(),
        deck.to_vec(),
        energy.to_vec(),
        energy.to_vec(),
        lives.to_vec(),
        lives.to_vec(),
        Some(deck_seed),
    );

    state.ui.silent = true;
    state.debug.debug_mode = false;

    let mut rng = StdRng::seed_from_u64(action_seed);
    let mut total_steps = 0u32;
    let start = Instant::now();

    while !state.is_terminal() && (total_steps as usize) < max_steps {
        let legal = state.get_legal_action_ids(db);
        if legal.is_empty() {
            state.auto_step(db);
        } else {
            let action = *legal.choose(&mut rng).unwrap_or(&0);
            let _ = state.step(db, action);
        }
        total_steps += 1;
    }

    let elapsed_ns = start.elapsed().as_nanos() as u64;
    let terminal = state.is_terminal();
    let winner = if terminal { state.get_winner() } else { -1 };

    GameOutcome {
        index: game_index,
        action_seed,
        turns: terminal.then_some(state.turn as u32),
        steps: total_steps,
        elapsed_ns,
        winner,
        p0_success: state.players[0].success_lives.len(),
        p1_success: state.players[1].success_lives.len(),
    }
}

fn main() {
    let config = Config::from_env();
    println!("=== Fastest Terminal Turn Search ===\n");
    println!(
        "games={} warmup_games={} workers={} max_steps={} deck_seed={} action_seed={}",
        config.games,
        config.warmup_games,
        config.workers,
        config.max_steps,
        config.deck_seed,
        config.action_seed,
    );

    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);

    println!("Warming up...");
    for offset in 0..config.warmup_games {
        let _ = run_game(
            &db,
            &deck,
            &lives,
            &energy,
            config.deck_seed,
            config.action_seed.wrapping_add(offset as u64),
            offset,
            config.max_steps,
        );
    }

    println!("Running {} games...", config.games);
    let bench_start = Instant::now();

    let run_game_for_index = |index: usize| {
        let action_seed = config.action_seed.wrapping_add(index as u64);
        run_game(
            &db,
            &deck,
            &lives,
            &energy,
            config.deck_seed,
            action_seed,
            index,
            config.max_steps,
        )
    };

    let mut results: Vec<GameOutcome> = Vec::with_capacity(config.games);
    if config.workers <= 1 {
        results.extend((0..config.games).map(run_game_for_index));
    } else {
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(config.workers)
            .build()
            .expect("build benchmark thread pool");

        pool.install(|| {
            let mut parallel_results: Vec<GameOutcome> = (0..config.games)
                .into_par_iter()
                .map(run_game_for_index)
                .collect();
            results.append(&mut parallel_results);
        });
    }

    results.sort_by_key(|result| result.index);

    let mut total_steps = 0u64;
    let mut total_ns = 0u64;
    let mut min_ns = u64::MAX;
    let mut max_ns = 0u64;
    let mut terminal_games = 0usize;
    let mut p0_wins = 0usize;
    let mut p1_wins = 0usize;
    let mut draws = 0usize;
    let mut capped_games = 0usize;
    let mut best_turns = u32::MAX;
    let mut record_breaks = 0usize;

    for result in &results {
        total_steps += result.steps as u64;
        total_ns += result.elapsed_ns;
        min_ns = min_ns.min(result.elapsed_ns);
        max_ns = max_ns.max(result.elapsed_ns);

        if let Some(turns) = result.turns {
            terminal_games += 1;
            match result.winner {
                0 => p0_wins += 1,
                1 => p1_wins += 1,
                2 => draws += 1,
                _ => {}
            }

            if turns < best_turns {
                best_turns = turns;
                record_breaks += 1;
                println!(
                    "[record {}] game={} action_seed={} turns={} steps={} winner={} p0_success={} p1_success={} elapsed={}μs",
                    record_breaks,
                    result.index,
                    result.action_seed,
                    turns,
                    result.steps,
                    result.winner,
                    result.p0_success,
                    result.p1_success,
                    result.elapsed_ns / 1000,
                );
            }
        } else {
            capped_games += 1;
        }
    }

    let bench_ns = bench_start.elapsed().as_nanos() as u64;
    let avg_ns_per_game = total_ns / config.games.max(1) as u64;
    let avg_steps_per_game = total_steps / config.games.max(1) as u64;
    let ns_per_step = if total_steps == 0 { 0 } else { total_ns / total_steps };
    let wall_games_per_sec = config.games as f64 / bench_ns as f64 * 1_000_000_000.0;
    let wall_steps_per_sec = total_steps as f64 / bench_ns as f64 * 1_000_000_000.0;

    println!("\n=== Results ===");
    println!("Games:        {}", config.games);
    println!(
        "Terminal:     {} (P0={} P1={} Draw={})",
        terminal_games, p0_wins, p1_wins, draws
    );
    println!("Capped:       {}", capped_games);
    println!("Record breaks: {}", record_breaks);
    if best_turns != u32::MAX {
        println!("Fastest terminal turns: {}", best_turns);
    }
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