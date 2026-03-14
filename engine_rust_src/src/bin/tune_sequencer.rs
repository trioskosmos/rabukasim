use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::{SearchConfig, SequencerConfig, TurnSequencer, WeightsConfig, CONFIG};
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use rand::prelude::StdRng;
use rand::seq::IndexedRandom;
use rand::SeedableRng;
use serde::Serialize;

#[derive(Clone)]
struct Candidate {
    name: &'static str,
    config: SequencerConfig,
}

#[derive(Serialize)]
struct FaceoffResult {
    candidate: String,
    games: usize,
    p0_wins: usize,
    p1_wins: usize,
    draws: usize,
    avg_turns: f32,
    avg_duration_secs: f32,
    avg_evaluations: f32,
}

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

fn choose_best_live_result_action(state: &GameState, db: &CardDatabase) -> i32 {
    let p_idx = state.current_player as usize;
    let legal = state.get_legal_action_ids(db);
    let mut best_action = ACTION_BASE_PASS;
    let mut best_score = i32::MIN;

    for action in legal {
        if (600..=602).contains(&action) {
            let slot_idx = (action - 600) as usize;
            let cid = state.players[p_idx].live_zone[slot_idx];
            let live_score = db.get_live(cid).map(|live| live.score as i32).unwrap_or(-1);
            if live_score > best_score {
                best_score = live_score;
                best_action = action;
            }
        }
    }

    best_action
}

fn execute_main_sequence(state: &mut GameState, db: &CardDatabase, planned_seq: &[i32]) -> usize {
    let mut executed = 0usize;

    for &action in planned_seq {
        if state.phase != Phase::Main {
            break;
        }

        let legal = state.get_legal_action_ids(db);
        if !legal.contains(&action) {
            break;
        }

        if state.step(db, action).is_err() {
            break;
        }

        executed += 1;
    }

    if state.phase == Phase::Main {
        let _ = state.step(db, ACTION_BASE_PASS);
    }

    executed
}

fn set_config(cfg: &SequencerConfig) {
    *engine_rust::core::logic::turn_sequencer::get_config().write().unwrap() = cfg.clone();
}

fn run_single_game(
    db: &CardDatabase,
    p0_deck: &(Vec<i32>, Vec<i32>),
    p1_deck: &(Vec<i32>, Vec<i32>),
    p0_config: &SequencerConfig,
    p1_config: &SequencerConfig,
    seed: u64,
) -> (i32, u32, f32, usize) {
    let mut state = GameState::default();
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    state.initialize_game(
        p0_deck.0.clone(),
        p1_deck.0.clone(),
        energy.clone(),
        energy,
        p0_deck.1.clone(),
        p1_deck.1.clone(),
    );
    state.ui.silent = true;

    let start = Instant::now();
    let mut rng = StdRng::seed_from_u64(seed);
    let mut total_evals = 0usize;
    let mut main_turns_played = 0usize;
    const TIMEOUT_SECONDS: u64 = 45;

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

        if start.elapsed().as_secs() > TIMEOUT_SECONDS {
            break;
        }
    }

    while !state.is_terminal() && main_turns_played < 20 {
        if start.elapsed().as_secs() > TIMEOUT_SECONDS {
            break;
        }

        let active_cfg = if state.current_player == 0 { p0_config } else { p1_config };

        match state.phase {
            Phase::Main => {
                main_turns_played += 1;
                set_config(active_cfg);
                let (best_seq, _, _, evals) = TurnSequencer::plan_full_turn(&state, db);
                total_evals += evals;
                let _executed_actions = execute_main_sequence(&mut state, db, &best_seq);
            }
            Phase::LiveSet => {
                set_config(active_cfg);
                let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, db);
                for &action in &seq {
                    let _ = state.step(db, action);
                }
                let _ = state.step(db, ACTION_BASE_PASS);
            }
            Phase::Active | Phase::Draw | Phase::Energy | Phase::PerformanceP1 | Phase::PerformanceP2 => {
                state.auto_step(db);
            }
            Phase::LiveResult => {
                let action = choose_best_live_result_action(&state, db);
                let _ = state.step(db, action);
            }
            Phase::Terminal => break,
            _ => {
                let legal = state.get_legal_action_ids(db);
                if let Some(&action) = legal.choose(&mut rng) {
                    let _ = state.step(db, action);
                } else {
                    state.auto_step(db);
                }
            }
        }
    }

    (state.get_winner(), state.turn as u32, start.elapsed().as_secs_f32(), total_evals)
}

fn make_candidates(base: &SequencerConfig) -> Vec<Candidate> {
    let mut out = Vec::new();

    out.push(Candidate {
        name: "baseline",
        config: base.clone(),
    });

    let mut depth12 = base.clone();
    depth12.search.max_dfs_depth = base.search.max_dfs_depth.max(12);
    out.push(Candidate {
        name: "depth12",
        config: depth12,
    });

    let mut depth12_live = base.clone();
    depth12_live.search.max_dfs_depth = base.search.max_dfs_depth.max(12);
    depth12_live.weights.live_ev_multiplier += 3.0;
    depth12_live.weights.liveset_placement_bonus = depth12_live.weights.liveset_placement_bonus.max(2.0);
    out.push(Candidate {
        name: "depth12_live_focus",
        config: depth12_live,
    });

    let mut depth12_board = base.clone();
    depth12_board.search.max_dfs_depth = base.search.max_dfs_depth.max(12);
    depth12_board.weights.board_presence += 0.75;
    depth12_board.weights.saturation_bonus += 1.0;
    depth12_board.weights.energy_penalty = (depth12_board.weights.energy_penalty - 0.15).max(0.0);
    out.push(Candidate {
        name: "depth12_tempo",
        config: depth12_board,
    });

    let defaults = SequencerConfig {
        weights: WeightsConfig::default(),
        search: SearchConfig::default(),
    };
    out.push(Candidate {
        name: "library_defaults",
        config: defaults,
    });

    out
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mut games_per_candidate = 4usize;
    let mut seed_base = 100u64;
    let mut deck0_path = "ai/decks/liella_cup.txt".to_string();
    let mut deck1_path = "ai/decks/liella_cup.txt".to_string();

    let mut i = 1usize;
    while i < args.len() {
        match args[i].as_str() {
            "--count" if i + 1 < args.len() => {
                games_per_candidate = args[i + 1].parse().unwrap_or(games_per_candidate);
                i += 2;
            }
            "--seed" if i + 1 < args.len() => {
                seed_base = args[i + 1].parse().unwrap_or(seed_base);
                i += 2;
            }
            "--deck-p0" if i + 1 < args.len() => {
                deck0_path = args[i + 1].clone();
                i += 2;
            }
            "--deck-p1" if i + 1 < args.len() => {
                deck1_path = args[i + 1].clone();
                i += 2;
            }
            _ => i += 1,
        }
    }

    if !std::path::Path::new(&deck0_path).exists() {
        deck0_path = format!("../{}", deck0_path);
    }
    if !std::path::Path::new(&deck1_path).exists() {
        deck1_path = format!("../{}", deck1_path);
    }

    let db = load_vanilla_db();
    let p0_deck = load_deck(&deck0_path, &db);
    let p1_deck = load_deck(&deck1_path, &db);
    let baseline = engine_rust::core::logic::turn_sequencer::get_config().read().unwrap().clone();
    let candidates = make_candidates(&baseline);

    let mut results = Vec::new();
    let mut best_name = "baseline".to_string();
    let mut best_margin = isize::MIN;
    let mut best_config = baseline.clone();

    for candidate in candidates {
        let mut p0_wins = 0usize;
        let mut p1_wins = 0usize;
        let mut draws = 0usize;
        let mut total_turns = 0u32;
        let mut total_duration = 0.0f32;
        let mut total_evals = 0usize;

        for game_idx in 0..games_per_candidate {
            let (winner, turns, duration, evals) = run_single_game(
                &db,
                &p0_deck,
                &p1_deck,
                &candidate.config,
                &baseline,
                seed_base + game_idx as u64,
            );
            match winner {
                0 => p0_wins += 1,
                1 => p1_wins += 1,
                _ => draws += 1,
            }
            total_turns += turns;
            total_duration += duration;
            total_evals += evals;
        }

        let margin = p0_wins as isize - p1_wins as isize;
        if candidate.name != "baseline" && margin > best_margin {
            best_margin = margin;
            best_name = candidate.name.to_string();
            best_config = candidate.config.clone();
        }

        results.push(FaceoffResult {
            candidate: candidate.name.to_string(),
            games: games_per_candidate,
            p0_wins,
            p1_wins,
            draws,
            avg_turns: total_turns as f32 / games_per_candidate as f32,
            avg_duration_secs: total_duration / games_per_candidate as f32,
            avg_evaluations: total_evals as f32 / games_per_candidate as f32,
        });
    }

    println!("{}", serde_json::to_string_pretty(&results).unwrap());

    if best_margin > 0 {
        fs::write(
            "sequencer_config.json",
            serde_json::to_string_pretty(&best_config).unwrap(),
        )
        .expect("failed to write sequencer_config.json");
        eprintln!("best_candidate={} margin={} -> sequencer_config.json updated", best_name, best_margin);
    } else {
        eprintln!("no candidate beat baseline; sequencer_config.json unchanged");
    }
}