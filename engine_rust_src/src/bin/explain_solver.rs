use engine_rust::core::analysis::performance_solver::{
    AbilityAdjustments, PerformanceProbabilitySolver,
};
use engine_rust::core::logic::CardDatabase;
use engine_rust::core::logic::GameState;
use engine_rust::test_helpers::load_real_db;

fn parse_deck(path: &str, db: &CardDatabase) -> Vec<i32> {
    let content = std::fs::read_to_string(path).expect("Failed to read deck file");
    let mut ids = Vec::new();
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        // Format: NO x COUNT or just NO
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
        } else {
            println!("[WARN] Card not found in DB: {}", no);
        }
    }
    ids
}

fn main() {
    println!("Loading Card Database...");
    let db = load_real_db();
    println!("DB Loaded successfully.");

    let p_idx = 0;
    let mut state = GameState::default();

    // Load Real AI Deck
    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() {
        "ai/decks/muse_cup.txt"
    } else {
        "../ai/decks/muse_cup.txt"
    };
    println!("Loading AI Deck from: {}", deck_path);
    let master_deck = parse_deck(deck_path, &db);

    // Split into main and energy (if applicable, but muse_cup is mostly main)
    let member_ids: Vec<i32> = master_deck
        .iter()
        .filter(|&&id| db.get_member(id).is_some())
        .cloned()
        .collect();
    let live_ids: Vec<i32> = master_deck
        .iter()
        .filter(|&&id| db.get_live(id).is_some())
        .cloned()
        .collect();

    // Base Yells: 10
    state.players[p_idx].cheer_mod_count = 10;

    // Initial Deck for Scenario 1/2
    state.players[p_idx].deck = member_ids.clone().into();

    // Stage: 1 member to provide a base
    if !member_ids.is_empty() {
        state.players[p_idx].stage[0] = member_ids[0];
    }

    // SCENARIO 1: LOW STAGE (1 Weak Member, 5 Yells)
    println!("\n=======================================================");
    println!("           SCENARIO 1: LOW STAGE, LOW YELLS            ");
    println!("     (1 Basic Member, 0 Blades, 5 Yells / Deck: 10)    ");
    println!("=======================================================\n");

    for &live_id in &live_ids {
        let live_card = db.get_live(live_id).unwrap();
        println!(
            ">>> Evaluating Live Card: {} (Base Score: {}, Hearts Required: {:?})",
            live_card.name, live_card.score, live_card.required_hearts
        );

        let mut state = GameState::default();
        let p_idx = 0;

        // Stage has 1 member
        state.players[p_idx].stage[0] = member_ids[0]; // Eli
                                                            // Deck
        state.players[p_idx]
            .deck
            .extend_from_slice(&member_ids);

        let chance =
            PerformanceProbabilitySolver::calculate_win_chance(&state, &db, p_idx, live_id);

        println!(
            "  - Expected Hearts across {} Yells: {:.2?}",
            chance.k_yells, chance.expected_hearts
        );
        println!("  - Expected Score: {:.2}", chance.expected_score);
        println!(
            "  - Win Probability: {:.2}%",
            chance.success_probability * 100.0
        );
        println!("-------------------------------------------------------");
    }

    // SCENARIO 2: HIGH STAGE (3 Strong Members, 20 Yells, 3 Blades)
    println!("\n=======================================================");
    println!("           SCENARIO 2: HIGH STAGE, HIGH YELLS           ");
    println!("    (3 Strong Members, 3 Blades, 15 Yells / Deck: 10)   ");
    println!("=======================================================\n");

    for &live_id in &live_ids {
        let live_card = db.get_live(live_id).unwrap();
        println!(
            ">>> Evaluating Live Card: {} (Base Score: {}, Hearts Required: {:?})",
            live_card.name, live_card.score, live_card.required_hearts
        );

        let mut state = GameState::default();
        let p_idx = 0;

        // Stage has 3 members
        if member_ids.len() >= 3 {
            state.players[p_idx].stage[0] = member_ids[1];
            state.players[p_idx].stage[1] = member_ids[2];
            state.players[p_idx].stage[2] = member_ids[3];
        }

        // Let's add blades to these members (simulating +1 blade per member)
        state.players[p_idx].blade_buffs[0] += 1;
        state.players[p_idx].blade_buffs[1] += 1;
        state.players[p_idx].blade_buffs[2] += 1;

        // 15 Yells
        state.players[p_idx].cheer_mod_count = 15;
        // Deck
        state.players[p_idx]
            .deck
            .extend_from_slice(&member_ids);

        let chance =
            PerformanceProbabilitySolver::calculate_win_chance(&state, &db, p_idx, live_id);

        println!(
            "  - Expected Hearts across {} Yells: {:.2?}",
            chance.k_yells, chance.expected_hearts
        );
        println!(
            "  - Expected Score: {:.2} (Note: Volume Icons give bonus!)",
            chance.expected_score
        );
        println!(
            "  - Win Probability: {:.2}%",
            chance.success_probability * 100.0
        );
        println!("-------------------------------------------------------");
    }

    // SCENARIO 3: HAND EVALUATION (Ability Awareness)
    println!("\n=======================================================");
    println!("           SCENARIO 3: HAND EVALUATION                 ");
    println!("    (Comparing cards in hand to boost a Live)          ");
    println!("=======================================================\n");

    let live_id = live_ids[0]; // SENTIMENTAL StepS (Score 2)
    let live_card = db.get_live(live_id).unwrap();
    println!(
        ">>> Target Live: {} (Requires: {:?})",
        live_card.name, live_card.required_hearts
    );

    let mut state = GameState::default();
    state.current_player = 0;
    let p_idx = 0;
    // state.players[p_idx].energy = 10; // DEPRECATED
    // Instead, add 10 dummy energy cards
    for _ in 0..10 {
        state.players[p_idx].energy_zone.push(1);
    }
    // Base Yells: 10
    state.players[p_idx].cheer_mod_count = 10;
    state.players[p_idx]
        .deck
        .extend_from_slice(&member_ids);
    // Stage: 1 member to provide a base
    state.players[p_idx].stage[0] = member_ids[0];

    // Hand setup for Scenario 3:
    // 1. PL!-sd1-002-SD (Eri - Activated, no immediate play boost)
    // 2. PL!HS-PR-019-PR (Ginko - Adds 2 Pink Hearts on play)
    // 3. PL!HS-bp2-008-P (Kosuzu - Adds 2 Blades on play)
    // 4. PL!-pb1-004-R (Umi - Boosts score on play)
    let hand_nos = vec![
        "PL!-sd1-002-SD",
        "PL!HS-PR-019-PR",
        "PL!HS-bp2-008-P",
        "PL!SP-pb1-004-R",
    ];
    let mut hand_ids = Vec::new();
    for no in hand_nos {
        if let Some(&id) = db.card_no_to_id.get(no) {
            hand_ids.push(id);
        }
    }

    state.players[p_idx].hand = hand_ids.clone().into();
    // Add multiple members to success pile/deck to ensure variety and satisfy conditions
    state.players[p_idx]
        .success_lives
        .extend_from_slice(&member_ids);

    // Ensure deck has enough variety to meet live requirements, but keep it readable (unique-ish)
    // We'll take all unique members from the DB to form a truly diverse deck
    let mut diverse_deck: Vec<i32> = db.members.keys().cloned().collect();
    // Shuffle or sort? Let's just use the first 40 unique cards for stability
    diverse_deck.sort();
    diverse_deck.truncate(40);
    state.players[p_idx].deck = diverse_deck.into();

    let evaluations = PerformanceProbabilitySolver::evaluate_hand_contributions(
        &state,
        &db,
        &state.players[p_idx].hand,
        live_card,
    );

    println!(">>> Evaluations Found: {}", evaluations.len());

    for (cid, chance) in evaluations {
        let card = db.get_member(cid).unwrap();
        // Predict specifically for the Center slot (slot 1) for this demonstration
        let _adj = PerformanceProbabilitySolver::predict_adjustments(&state, &db, card, 1);
        println!(
            ">>> Resulting Win Probability: {:.2}%",
            chance.success_probability * 100.0
        );
        println!("  - Expected Score: {:.2}", chance.expected_score);
        println!("-------------------------------------------------------");
    }

    // SCENARIO 4: BATCH LIVE EVALUATION (Success Heatmap)
    println!("\n=======================================================");
    println!("        SCENARIO 4: BATCH LIVE EVALUATION              ");
    println!("    (Win Chance for ALL unique lives in Database)      ");
    println!("=======================================================\n");

    let mut live_map = std::collections::BTreeMap::new();
    let all_live_ids: Vec<i32> = db.lives.keys().cloned().collect();

    for &lid in &all_live_ids {
        let l_card = db.get_live(lid).unwrap();
        let chance = PerformanceProbabilitySolver::calculate_performance_chance(
            &state,
            &db,
            l_card,
            &AbilityAdjustments::default(),
        );

        // Group by name - keep the maximum probability found for this name
        let entry = live_map.entry(l_card.name.clone()).or_insert(0.0f32);
        if chance.success_probability > *entry {
            *entry = chance.success_probability;
        }
    }

    let mut live_results: Vec<_> = live_map.into_iter().collect();

    // Sort by success probability descending
    live_results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    println!("{:<40} | {:<10}", "Live Card Name", "Win Chance");
    println!("------------------------------------------------------------------");
    for (name, prob) in live_results {
        if prob > 0.0 {
            println!("{:<40} | {:>9.2}%", name, prob * 100.0);
        }
    }
}
