use std::env;
use std::fs;
use std::time::Instant;
use serde::{Serialize, Deserialize};

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use engine_rust::core::{ACTION_BASE_HAND, ACTION_BASE_LIVESET};
use rand::seq::IndexedRandom;
use rand::SeedableRng;
use rand::prelude::StdRng;
use smallvec::SmallVec;

#[derive(Serialize, Deserialize, Debug, Clone)]
struct GameResult {
    game_id: usize,
    seed: u64,
    winner: i32,
    score_p0: u32,
    score_p1: u32,
    turns: u32,
    duration_secs: f32,
    evaluations: usize,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct BatchSummary {
    total_games: usize,
    p0_wins: usize,
    p1_wins: usize,
    draws: usize,
    avg_score_p0: f32,
    avg_score_p1: f32,
    avg_turns: f32,
    total_evaluations: usize,
    results: Vec<GameResult>,
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

fn format_action(action: i32) -> String {
    if action == ACTION_BASE_PASS {
        return "PASS".to_string();
    }
    if action >= ACTION_BASE_HAND {
        let raw = action - ACTION_BASE_HAND;
        return format!("HAND(hand={},slot={})", raw / 10, raw % 10);
    }
    if action >= ACTION_BASE_LIVESET {
        let raw = action - ACTION_BASE_LIVESET;
        return format!("LIVESET(hand={},slot={})", raw / 10, raw % 10);
    }
    format!("ACTION({})", action)
}

fn format_sequence(seq: &[i32]) -> String {
    if seq.is_empty() {
        return "[]".to_string();
    }
    let parts: Vec<String> = seq.iter().map(|&action| format_action(action)).collect();
    format!("[{}]", parts.join(", "))
}

fn count_exact_main_sequences(state: &GameState, db: &CardDatabase, max_depth: usize) -> usize {
    fn recurse(state: &GameState, db: &CardDatabase, depth: usize, max_depth: usize) -> usize {
        if state.phase != Phase::Main {
            return 1;
        }
        if depth >= max_depth {
            return 1;
        }

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        let mut total = 0usize;
        let mut saw_non_pass = false;
        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            saw_non_pass = true;
            let mut next_state = state.clone();
            if next_state.step(db, action).is_ok() {
                total += recurse(&next_state, db, depth + 1, max_depth);
            }
        }

        let mut pass_state = state.clone();
        if pass_state.step(db, ACTION_BASE_PASS).is_ok() {
            total += 1;
        } else if !saw_non_pass {
            total += 1;
        }

        total
    }

    recurse(state, db, 0, max_depth)
}


fn execute_main_sequence(state: &mut GameState, db: &CardDatabase, planned_seq: &[i32]) -> Vec<i32> {
    let mut executed = Vec::new();
    let mut ended_with_pass = false;

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

        executed.push(action);
        if action == ACTION_BASE_PASS {
            ended_with_pass = true;
            break;
        }
    }

    if state.phase == Phase::Main && !ended_with_pass {
        let _ = state.step(db, ACTION_BASE_PASS);
        executed.push(ACTION_BASE_PASS);
    }

    executed
}

fn run_single_game(
    game_id: usize,
    seed: u64,
    db: &CardDatabase,
    p0_deck: &(Vec<i32>, Vec<i32>),
    p1_deck: &(Vec<i32>, Vec<i32>),
    silent: bool,
) -> GameResult {
    let mut state = GameState::default();
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    state.initialize_game(
        p0_deck.0.clone(),
        p1_deck.0.clone(),
        energy.clone(),
        energy.clone(),
        p0_deck.1.clone(),
        p1_deck.1.clone(),
    );
    state.ui.silent = true; // Always silent engine-wise

    let game_start = Instant::now();
    let mut rng = StdRng::seed_from_u64(seed);
    let max_turns = 20usize;
    const TIMEOUT_SECONDS: u64 = 30;

    if !silent {
        println!("\n[GAME {}] Seed: {}", game_id, seed);
    }

    let mut total_evaluations: usize = 0;
    let mut main_turns_played = 0usize;

    // Advance to first Main phase (RPS, Mulligan, etc.)
    while state.phase != Phase::Main && !state.is_terminal() {
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

        if game_start.elapsed().as_secs() > TIMEOUT_SECONDS {
            break;
        }
    }

    while !state.is_terminal() && main_turns_played < max_turns {
        if game_start.elapsed().as_secs() > TIMEOUT_SECONDS {
            break;
        }

        match state.phase {
            Phase::Main => {
                main_turns_played += 1;
                let current_player = state.current_player;
                let search_depth = engine_rust::core::logic::turn_sequencer::CONFIG.read().unwrap().search.max_dfs_depth;
                let exact_threshold = std::env::var("TURNSEQ_EXACT_THRESHOLD")
                    .ok()
                    .and_then(|value| value.parse().ok())
                    .unwrap_or(10000usize);
                let exact_seq_start = Instant::now();
                let exact_sequences = count_exact_main_sequences(&state, db, search_depth);

                if !silent {
                    println!(
                        "[TURN {}] P{} exact_main_sequences={} depth={} counted_in={:.3}s",
                        main_turns_played,
                        current_player,
                        exact_sequences,
                        search_depth,
                        exact_seq_start.elapsed().as_secs_f32(),
                    );
                    std::env::set_var("TURNSEQ_PROGRESS", "1");
                    std::env::set_var("TURNSEQ_STALL_SECS", "5");
                }

                let (best_seq, _, _, evals) = if exact_sequences <= exact_threshold {
                    TurnSequencer::plan_full_turn_exact(&state, db)
                } else {
                    TurnSequencer::plan_full_turn(&state, db)
                };
                total_evaluations += evals;
                let executed_actions = execute_main_sequence(&mut state, db, &best_seq);

                if !silent {
                    println!(
                        "[TURN {}] P{} planned={} evals={} planned_seq={}",
                        main_turns_played,
                        current_player,
                        best_seq.len(),
                        evals,
                        format_sequence(&best_seq),
                    );
                    println!(
                        "[TURN {}] P{} executed={} executed_seq={}",
                        main_turns_played,
                        current_player,
                        executed_actions.len(),
                        format_sequence(&executed_actions),
                    );
                }
            },
            Phase::Active | Phase::Draw | Phase::Energy => {
                state.auto_step(db);
            },
            Phase::LiveSet => {
                let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, db);
                if !silent {
                    println!("[LIVESET] P{} seq={}", state.current_player, format_sequence(&seq));
                }
                for &action in &seq {
                    let _ = state.step(db, action);
                }
                let _ = state.step(db, ACTION_BASE_PASS);
            },
            Phase::PerformanceP1 | Phase::PerformanceP2 => {
                state.auto_step(db);
            },
            Phase::LiveResult => {
                let action = choose_best_live_result_action(&state, db);
                let _ = state.step(db, action);
            },
            Phase::Terminal => break,
            _ => {
                // For RPS/Mulligan if they happen mid-game (unlikely but safe)
                let legal = state.get_legal_action_ids(db);
                if !legal.is_empty() {
                    let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
                    let _ = state.step(db, action);
                } else {
                    state.auto_step(db);
                }
            }
        }
    }

    let result = GameResult {
        game_id,
        seed,
        winner: state.get_winner(),
        score_p0: state.players[0].score,
        score_p1: state.players[1].score,
        turns: state.turn as u32,
        duration_secs: game_start.elapsed().as_secs_f32(),
        evaluations: total_evaluations,
    };

    if !silent {
        println!("  Winner: P{} | Score: {}-{} | Turns: {} | {:.2}s",
            result.winner, result.score_p0, result.score_p1, result.turns, result.duration_secs);
    }

    result
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut count = 1;
    let mut seed_base = 100;
    let mut silent = false;
    let mut json_mode = false;
    let mut deck0_path = "ai/decks/liella_cup.txt".to_string();
    let mut deck1_path = "ai/decks/liella_cup.txt".to_string();

    if !std::path::Path::new(&deck0_path).exists() {
        deck0_path = "../ai/decks/liella_cup.txt".to_string();
    }
    if !std::path::Path::new(&deck1_path).exists() {
        deck1_path = "../ai/decks/liella_cup.txt".to_string();
    }

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--count" => {
                count = args[i+1].parse().unwrap_or(1);
                i += 2;
            }
            "--seed" => {
                seed_base = args[i+1].parse().unwrap_or(100);
                i += 2;
            }
            "--silent" => {
                silent = true;
                i += 1;
            }
            "--deck-p0" => {
                deck0_path = args[i+1].clone();
                i += 2;
            }
            "--deck-p1" => {
                deck1_path = args[i+1].clone();
                i += 2;
            }
            "--weight" => {
                let pair = args[i+1].clone();
                let parts: Vec<&str> = pair.split('=').collect();
                if parts.len() == 2 {
                    let key = parts[0];
                    let val: f32 = parts[1].parse().unwrap_or(0.0);
                    let mut config = engine_rust::core::logic::turn_sequencer::CONFIG.write().unwrap();
                    match key {
                        "board_presence" => config.weights.board_presence = val,
                        "blades" => config.weights.blades = val,
                        "hearts" => config.weights.hearts = val,
                        "saturation_bonus" => config.weights.saturation_bonus = val,
                        "energy_penalty" => config.weights.energy_penalty = val,
                        "live_ev_multiplier" => config.weights.live_ev_multiplier = val,
                        "uncertainty_penalty_pow" => config.weights.uncertainty_penalty_pow = val,
                        "liveset_placement_bonus" => config.weights.liveset_placement_bonus = val,
                        "max_dfs_depth" => config.search.max_dfs_depth = val as usize,
                        "beam_width" => config.search.beam_width = val as usize,
                        _ => println!("[WARN] Unknown weight key: {}", key),
                    }
                }
                i += 2;
            }
            "--beam-search" => {
                engine_rust::core::logic::turn_sequencer::CONFIG.write().unwrap().search.beam_search = true;
                i += 1;
            }
            "--no-memo" => {
                engine_rust::core::logic::turn_sequencer::CONFIG.write().unwrap().search.use_memoization = false;
                i += 1;
            }
            "--no-alpha-beta" => {
                engine_rust::core::logic::turn_sequencer::CONFIG.write().unwrap().search.use_alpha_beta = false;
                i += 1;
            }
            "--json" => {
                json_mode = true;
                silent = true;
                i += 1;
            }
            "--verbose-search" => {
                std::env::set_var("TURNSEQ_PROGRESS", "1");
                silent = false;
                i += 1;
            }
            "--stall-secs" => {
                if i + 1 < args.len() {
                    std::env::set_var("TURNSEQ_STALL_SECS", &args[i + 1]);
                }
                i += 2;
            }
            _ => i += 1,
        }
    }

    let db = load_vanilla_db();
    let p0_deck = load_deck(&deck0_path, &db);
    let p1_deck = load_deck(&deck1_path, &db);

    if !json_mode {
        println!("\n╔═══════════════════════════════════════╗");
        println!("║  Simple Game Runner - Batch Mode    ║");
        println!("╚═══════════════════════════════════════╝");
        println!("[DB] Loaded vanilla data");
        println!("[DECK] P0: {} | P1: {}", deck0_path, deck1_path);
        println!("[BATCH] Running {} games starting with seed {}", count, seed_base);
    }

    let start_all = Instant::now();
    let results: Vec<GameResult> = (0..count)
        .map(|g_idx| run_single_game(g_idx, seed_base + g_idx as u64, &db, &p0_deck, &p1_deck, silent))
        .collect();

    let total_games = results.len();
    let p0_wins = results.iter().filter(|r| r.winner == 0).count();
    let p1_wins = results.iter().filter(|r| r.winner == 1).count();
    let draws = results.iter().filter(|r| r.winner == 2).count();
    let avg_p0 = results.iter().map(|r| r.score_p0 as f32).sum::<f32>() / total_games as f32;
    let avg_p1 = results.iter().map(|r| r.score_p1 as f32).sum::<f32>() / total_games as f32;
    let avg_turns = results.iter().map(|r| r.turns as f32).sum::<f32>() / total_games as f32;
    let total_evaluations_sum = results.iter().map(|r| r.evaluations).sum();

    if json_mode {
        let summary = BatchSummary {
            total_games,
            p0_wins,
            p1_wins,
            draws,
            avg_score_p0: avg_p0,
            avg_score_p1: avg_p1,
            avg_turns,
            total_evaluations: total_evaluations_sum,
            results,
        };
        println!("{}", serde_json::to_string_pretty(&summary).unwrap());
    } else {
        println!("\n╔═══════════════════════════════════════╗");
        println!("║  Batch Complete                     ║");
        println!("╚═══════════════════════════════════════╝");
        println!("Total Time: {:.2}s", start_all.elapsed().as_secs_f32());
        println!("Wins: P0={} ({:.1}%) | P1={} ({:.1}%) | Draws={}",
            p0_wins, (p0_wins as f32 / total_games as f32) * 100.0,
            p1_wins, (p1_wins as f32 / total_games as f32) * 100.0,
            draws);
        println!("Avg Score: P0={:.2} | P1={:.2}", avg_p0, avg_p1);
        println!("Avg Turns: {:.2}", avg_turns);
    }
}
