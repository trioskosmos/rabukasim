use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};

fn main() {
    println!("\n=== LOVECA ABILITIES-ON GAME ===\n");

    let start_total = Instant::now();

    let db = load_abilities_on_db();
    println!("[init] db.is_vanilla = {}", db.is_vanilla);
    println!("[init] db.detect_abilityless() = {}", db.detect_abilityless());

    println!("[init] db.members = {}, db.lives = {}, db.energy = {}", db.members.len(), db.lives.len(), db.energy_db.len());
    let (deck, lives, energy) = build_decks_from_db(&db);
    println!("[init] deck size = {}, lives = {}, energy = {}", deck.len(), lives.len(), energy.len());

    let mut state = GameState::default();
    state.initialize_game_with_seed(
        deck.clone(),
        deck.clone(),
        energy.clone(),
        energy.clone(),
        lives.clone(),
        lives.clone(),
        Some(42),
    );

    println!("[init] starting phase = {:?}", state.phase);

    let mut interactive_steps = 0usize;
    let max_interactive_steps = 20usize;

    while state.phase != Phase::Terminal && interactive_steps < max_interactive_steps {
        while state.phase != Phase::Terminal && !state.phase.is_interactive() {
            state.auto_step(&db);
        }

        if state.phase == Phase::Terminal {
            break;
        }

        interactive_steps += 1;
        let current_player = state.current_player as usize;
        println!(
            "[step {}] phase={:?} current_player=P{} turn={} scores=P0:{} P1:{}",
            interactive_steps,
            state.phase,
            current_player,
            state.turn,
            state.players[0].score,
            state.players[1].score,
        );

        let legal_actions = state.get_legal_action_ids(&db);
        println!("  legal actions: {}", legal_actions.len());

        let mut ability_actions = Vec::new();
        for action_id in legal_actions.iter().copied() {
            let label = state.get_verbose_action_label(action_id, &db);
            if label.to_ascii_lowercase().contains("ability")
                || label.to_ascii_lowercase().contains("activate")
                || label.to_ascii_lowercase().contains("turn")
            {
                ability_actions.push((action_id, label.clone()));
            }
        }

        for (index, action_id) in legal_actions.iter().copied().take(12).enumerate() {
            let label = state.get_verbose_action_label(action_id, &db);
            println!("    {:>2}. {:>6}  {}", index + 1, action_id, label);
        }

        if !ability_actions.is_empty() {
            println!("  ability-like actions visible: {}", ability_actions.len());
            for (action_id, label) in ability_actions.iter().take(8) {
                println!("    -> {:>6}  {}", action_id, label);
            }
        }

        let chosen_action = choose_action(&state, &db, &legal_actions);
        println!("  chosen action: {}  {}", chosen_action, state.get_verbose_action_label(chosen_action, &db));

        if state.step(&db, chosen_action).is_err() {
            println!("  step rejected, falling back to pass");
            let _ = state.step(&db, ACTION_BASE_PASS);
        }

        state.auto_step(&db);
        println!("  -> phase after step: {:?}\n", state.phase);
    }

    println!("=== FINAL STATE ===");
    println!("winner = {}", state.get_winner());
    println!("scores = P0:{} P1:{}", state.players[0].score, state.players[1].score);
    println!("turns processed = {}", interactive_steps);
    println!("elapsed = {:.2}s", start_total.elapsed().as_secs_f32());
}

fn load_abilities_on_db() -> &'static CardDatabase {
    engine_rust::test_helpers::load_real_db()
}

fn build_decks_from_db(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    while deck.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            deck.push(id);
        } else {
            break;
        }
    }

    let mut lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    while lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            lives.push(id);
        } else {
            break;
        }
    }

    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    (deck, lives, energy)
}

fn choose_action(state: &GameState, db: &CardDatabase, legal_actions: &[i32]) -> i32 {
    if legal_actions.is_empty() {
        return ACTION_BASE_PASS;
    }

    if matches!(state.phase, Phase::Main) {
        for action_id in legal_actions.iter().copied() {
            let label = state.get_verbose_action_label(action_id, db).to_ascii_lowercase();
            if label.contains("ability") || label.contains("activate") {
                return action_id;
            }
        }
    }

    legal_actions[0]
}
