use std::collections::{BTreeMap, HashSet};
use std::env;
use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use rand::prelude::StdRng;
use rand::seq::IndexedRandom;
use rand::SeedableRng;
use smallvec::SmallVec;

fn load_vanilla_db() -> CardDatabase {
    let candidates = [
        "data/cards_vanilla.json",
        "../data/cards_vanilla.json",
        "../../data/cards_vanilla.json",
    ];

    for path in &candidates {
        if !std::path::Path::new(path).exists() {
            continue;
        }
        let json = fs::read_to_string(path).expect("Failed to read DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
        db.is_vanilla = true;
        return db;
    }
    panic!("cards_vanilla.json not found");
}

fn load_deck(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let content = fs::read_to_string(path).expect("Failed to read deck");
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

#[derive(Default)]
struct SequenceStats {
    total_sequences: usize,
    by_card_plays: BTreeMap<usize, usize>,
    unique_end_states: HashSet<String>,
    cut_off_sequences: usize,
    max_card_plays_seen: usize,
}

impl SequenceStats {
    fn record(&mut self, card_plays: usize, state: &GameState, was_cutoff: bool) {
        self.total_sequences += 1;
        *self.by_card_plays.entry(card_plays).or_insert(0) += 1;
        self.max_card_plays_seen = self.max_card_plays_seen.max(card_plays);
        if was_cutoff {
            self.cut_off_sequences += 1;
        }
        self.unique_end_states.insert(format!(
            "turn={} current={} phase={:?} p0_stage={:?} p0_live={:?} p0_hand={} p0_score={} p1_stage={:?} p1_live={:?} p1_hand={} p1_score={}",
            state.turn,
            state.current_player,
            state.phase,
            state.players[0].stage,
            state.players[0].live_zone,
            state.players[0].hand.len(),
            state.players[0].score,
            state.players[1].stage,
            state.players[1].live_zone,
            state.players[1].hand.len(),
            state.players[1].score,
        ));
    }
}

fn advance_to_first_main(state: &mut GameState, db: &CardDatabase, seed: u64) {
    let mut rng = StdRng::seed_from_u64(seed);
    let mut step_count = 0usize;

    while state.phase != Phase::Main && !state.is_terminal() {
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                let legal = state.get_legal_action_ids(db);
                if let Some(&action) = legal.choose(&mut rng) {
                    let _ = state.step(db, action);
                } else {
                    let _ = state.step(db, ACTION_BASE_PASS);
                }
            }
            _ => state.auto_step(db),
        }

        step_count += 1;
        if step_count > 200 {
            panic!("failed to reach Main phase; stuck in {:?}", state.phase);
        }
    }
}

fn enumerate_main_sequences(
    state: &GameState,
    db: &CardDatabase,
    card_plays: usize,
    max_depth: usize,
    stats: &mut SequenceStats,
) {
    if state.phase != Phase::Main {
        stats.record(card_plays, state, false);
        return;
    }

    if card_plays >= max_depth {
        stats.record(card_plays, state, true);
        return;
    }

    let mut actions = SmallVec::<[i32; 64]>::new();
    state.generate_legal_actions(db, state.current_player as usize, &mut actions);

    let mut saw_non_pass = false;
    for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
        saw_non_pass = true;
        let mut next_state = state.clone();
        if next_state.step(db, action).is_ok() {
            enumerate_main_sequences(&next_state, db, card_plays + 1, max_depth, stats);
        }
    }

    // Passing is always an exact end-of-turn sequence when legal from Main.
    let mut stop_state = state.clone();
    if stop_state.step(db, ACTION_BASE_PASS).is_ok() {
        stats.record(card_plays, &stop_state, false);
    } else if !saw_non_pass {
        stats.record(card_plays, state, false);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut seed = 100u64;
    let mut max_depth = 15usize;
    let mut deck_path = "ai/decks/liella_cup.txt".to_string();

    let mut i = 1usize;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" if i + 1 < args.len() => {
                seed = args[i + 1].parse().unwrap_or(seed);
                i += 2;
            }
            "--max-depth" if i + 1 < args.len() => {
                max_depth = args[i + 1].parse().unwrap_or(max_depth);
                i += 2;
            }
            "--deck" if i + 1 < args.len() => {
                deck_path = args[i + 1].clone();
                i += 2;
            }
            _ => i += 1,
        }
    }

    if !std::path::Path::new(&deck_path).exists() {
        deck_path = format!("../{}", deck_path);
    }

    let db = load_vanilla_db();
    let (members, lives) = load_deck(&deck_path, &db);
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    let mut state = GameState::default();
    state.initialize_game(
        members.clone(),
        members,
        energy.clone(),
        energy,
        lives.clone(),
        lives,
    );
    state.ui.silent = true;
    advance_to_first_main(&mut state, &db, seed);

    let mut root_actions = SmallVec::<[i32; 64]>::new();
    state.generate_legal_actions(&db, state.current_player as usize, &mut root_actions);
    let root_non_pass = root_actions.iter().filter(|&&action| action != ACTION_BASE_PASS).count();

    let start = Instant::now();
    let mut stats = SequenceStats::default();
    enumerate_main_sequences(&state, &db, 0, max_depth, &mut stats);

    println!("phase={:?} seed={} max_depth={}", state.phase, seed, max_depth);
    println!("root_actions_total={} root_actions_non_pass={}", root_actions.len(), root_non_pass);
    println!("total_sequences={}", stats.total_sequences);
    println!("unique_end_states={}", stats.unique_end_states.len());
    println!("max_card_plays_seen={}", stats.max_card_plays_seen);
    println!("cut_off_sequences={}", stats.cut_off_sequences);
    println!("elapsed_secs={:.3}", start.elapsed().as_secs_f32());
    println!("sequences_by_card_plays:");
    for (plays, count) in &stats.by_card_plays {
        println!("  plays={} count={}", plays, count);
    }
}
