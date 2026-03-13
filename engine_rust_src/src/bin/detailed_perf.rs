use std::fs;
use std::time::Instant;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::enums::Phase;

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
    let candidates = [path, &format!("../{}", path), &format!("../../{}", path)];

    for candidate in &candidates {
        let Ok(content) = fs::read_to_string(candidate) else {
            continue;
        };

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
        return (members, lives);
    }

    panic!("Failed to read deck from any candidate path for {}", path);
}

fn main() {
    let db = load_vanilla_db();
    let (p0_members, p0_lives) = load_deck("ai/decks/liella_cup.txt", &db);
    let (p1_members, p1_lives) = load_deck("ai/decks/liella_cup.txt", &db);

    let mut state = GameState::default();
    let energy_vec: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    state.initialize_game(
        p0_members.clone(),
        p1_members.clone(),
        energy_vec.clone(),
        energy_vec,
        p0_lives.clone(),
        p1_lives.clone(),
    );
    state.ui.silent = true;

    // DIAGNOSTIC 1: Time individual operations
    println!("\n=== OPERATION TIMING DIAGNOSTICS ===\n");

    // Measure state clone
    let t = Instant::now();
    for _ in 0..1000 {
        let _ = state.clone();
    }
    println!("[CLONE] 1000 clones: {:.3}ms => {:.3}µs per clone", t.elapsed().as_secs_f32() * 1000.0, t.elapsed().as_secs_f32() * 1_000_000.0 / 1000.0);

    // Measure action generation
    let mut actions: Vec<i32> = Vec::new();
    let t = Instant::now();
    for _ in 0..10000 {
        actions.clear();
        state.generate_legal_actions(&db, state.current_player as usize, &mut actions);
    }
    println!("[ACTIONS] 10000 generations: {:.3}ms => {:.3}µs per gen (found {} actions)", t.elapsed().as_secs_f32() * 1000.0, t.elapsed().as_secs_f32() * 1_000_000.0 / 10000.0, actions.len());

    // Measure state.step()
    let t = Instant::now();
    for _ in 0..1000 {
        let mut temp_state = state.clone();
        let _ = temp_state.step(&db, ACTION_BASE_PASS);
    }
    println!("[STEP] 1000 steps: {:.3}ms => {:.3}µs per step", t.elapsed().as_secs_f32() * 1000.0, t.elapsed().as_secs_f32() * 1_000_000.0 / 1000.0);

    // Measure action generation + clone + step
    let t = Instant::now();
    for _ in 0..1000 {
        let mut acts: Vec<i32> = Vec::new();
        state.generate_legal_actions(&db, state.current_player as usize, &mut acts);
        if !acts.is_empty() {
            let mut temp = state.clone();
            let _ = temp.step(&db, acts[0]);
        }
    }
    println!("[FULL-OP] 1000 (gen + clone + step): {:.3}ms => {:.3}µs per full-op", t.elapsed().as_secs_f32() * 1000.0, t.elapsed().as_secs_f32() * 1_000_000.0 / 1000.0);

    println!("\n=== FULL GAME PROFILE ===\n");

    let mut game_state = GameState::default();
    let energy_vec2: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    game_state.initialize_game(p0_members, p1_members, energy_vec2.clone(), energy_vec2, p0_lives, p1_lives);
    game_state.ui.silent = true;

    let game_start = Instant::now();
    let mut turns_played = 0;
    let mut total_evals = 0;
    const TIMEOUT: u64 = 45;

    // Skip to main phase
    while game_state.phase != Phase::Main && !game_state.is_terminal() {
        game_state.auto_step(&db);
    }

    println!("Turn | Player | Actions | Evals | Time(ms) | Phase");
    println!("-----|--------|---------|-------|----------|------");

    while !game_state.is_terminal() && turns_played < 20 {
        if game_start.elapsed().as_secs() > TIMEOUT {
            println!("TIMEOUT!");
            break;
        }

        match game_state.phase {
            Phase::Main => {
                turns_played += 1;
                
                let mut acts: Vec<i32> = Vec::new();
                game_state.generate_legal_actions(&db, game_state.current_player as usize, &mut acts);
                
                let search_start = Instant::now();
                let (seq, _, _, evals) = TurnSequencer::plan_full_turn(&game_state, &db);
                let search_time = search_start.elapsed();

                total_evals += evals;

                for &action in &seq {
                    if game_state.phase != Phase::Main {
                        break;
                    }
                    let legal = game_state.get_legal_action_ids(&db);
                    if !legal.contains(&action) {
                        break;
                    }
                    let _ = game_state.step(&db, action);
                }

                if game_state.phase == Phase::Main {
                    let _ = game_state.step(&db, ACTION_BASE_PASS);
                }

                println!("{:4} | {:6} | {:7} | {:5} | {:8.2} | Main", 
                    turns_played, game_state.current_player, acts.len(), evals, search_time.as_secs_f32() * 1000.0);
            }
            Phase::LiveSet => {
                let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&game_state, &db);
                for &action in &seq {
                    let _ = game_state.step(&db, action);
                }
                let _ = game_state.step(&db, ACTION_BASE_PASS);
            }
            _ => {
                game_state.auto_step(&db);
            }
        }
    }

    println!("\n=== SUMMARY ===");
    println!("Turns played: {}", turns_played);
    println!("Total evaluations: {}", total_evals);
    println!("Total game time: {:.3}s", game_start.elapsed().as_secs_f32());
    if turns_played > 0 {
        println!("Average time per turn: {:.2}ms", game_start.elapsed().as_secs_f32() * 1000.0 / turns_played as f32);
        println!("Average evals per turn: {:.0}", total_evals as f32 / turns_played as f32);
    }
    println!("Winner: {:?}", game_state.get_winner());
}
