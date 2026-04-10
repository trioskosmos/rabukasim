use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use rand::prelude::{IndexedRandom, SeedableRng, StdRng};
use std::env;
use std::fs;
use std::time::Instant;

fn env_usize(key: &str, default: usize) -> usize {
    env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn env_u64(key: &str, default: u64) -> u64 {
    env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn env_bool(key: &str, default: bool) -> bool {
    env::var(key)
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
            let json = fs::read_to_string(path).expect("Failed to read DB");
            let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
            db.is_vanilla = env_bool("BENCH_VANILLA_MODE", false);
            return db;
        }
    }
    panic!("cards_compiled.json not found");
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
        if let Some(&cid) = deck.first() {
            deck.push(cid);
        } else {
            break;
        }
    }
    while lives.len() < 12 {
        if let Some(&cid) = lives.first() {
            lives.push(cid);
        } else {
            break;
        }
    }
    while energy.len() < 12 {
        if let Some(&cid) = energy.first() {
            energy.push(cid);
        } else {
            break;
        }
    }
    (deck, lives, energy)
}

fn trace_game(
    db: &CardDatabase,
    deck: &[i32],
    lives: &[i32],
    energy: &[i32],
    seed: u64,
    max_steps: usize,
    trace_steps: usize,
) {
    let mut state = GameState::default();
    state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
    state.ui.silent = true;
    state.debug.debug_mode = true;

    let mut rng = StdRng::seed_from_u64(seed);
    let mut legal: Vec<i32> = Vec::with_capacity(64);
    let mut steps = 0;
    let start = Instant::now();

    println!("=== Trace Game ===");
    println!("start phase={:?} turn={} p={}", state.phase, state.turn, state.current_player);

    while !state.is_terminal() && steps < max_steps {
        let phase = state.phase;
        legal.clear();
        state.generate_legal_actions(db, state.current_player as usize, &mut legal);
        if legal.len() > 1 {
            legal.sort_unstable();
            legal.dedup();
        }
        let action = if legal.is_empty() {
            ACTION_BASE_PASS
        } else {
            *legal.choose(&mut rng).unwrap_or(&0)
        };
        if steps < trace_steps {
            println!("step={} phase={:?} legal={} action={}", steps, phase, legal.len(), action);
        }
        let _ = state.step(db, action);
        steps += 1;
    }

    let elapsed = Instant::now().duration_since(start);
    println!("end terminal={} winner={:?} steps={} elapsed={:?}", state.is_terminal(), state.get_winner(), steps, elapsed);
}

fn main() {
    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);
    let games = env_usize("BENCH_GAMES", 1);
    let warmup_games = env_usize("BENCH_WARMUP_GAMES", 0);
    let max_steps = env_usize("BENCH_MAX_STEPS", 10000);
    let workers = env_usize("BENCH_WORKERS", 1);
    let seed = env_u64("BENCH_SEED", 0);
    let trace_steps = env_usize("BENCH_TRACE_STEP_LIMIT", 32);
    let profile_label = env_bool("BENCH_PROFILE_LEGAL_ACTIONS", true);

    println!("bench_profile_legal_actions: games={} warmup={} workers={} max_steps={} seed={} trace_steps={} profile={}", games, warmup_games, workers, max_steps, seed, trace_steps, profile_label);
    println!("Set BENCH_PROFILE_LEGAL_ACTIONS=1 and BENCH_PROFILE_STEP_THRESHOLD_US=50 to enable internal profiler output.");

    for _ in 0..warmup_games {
        let mut state = GameState::default();
        state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
        state.ui.silent = true;
        let mut legal: Vec<i32> = Vec::with_capacity(64);
        let mut rng = StdRng::seed_from_u64(seed);
        while !state.is_terminal() {
            legal.clear();
            state.generate_legal_actions(&db, state.current_player as usize, &mut legal);
            let action = legal.choose(&mut rng).copied().unwrap_or(0);
            let _ = state.step(&db, action);
        }
    }

    trace_game(&db, &deck, &lives, &energy, seed, max_steps, trace_steps);
    println!("Finished profiling harness.");
}
