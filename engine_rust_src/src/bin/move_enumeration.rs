use std::fs;
use engine_rust::core::logic::{GameState, CardDatabase};
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
    let content = fs::read_to_string(path).expect("Failed to read deck");
    let mut members = Vec::new();
    let mut lives = Vec::new();

    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        let card_no = line;
        if let Some(id) = db.id_by_no(card_no) {
            if db.lives.contains_key(&id) {
                lives.push(id);
            } else {
                members.push(id);
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

fn main() {
    let db = load_vanilla_db();
    let deck_path = if std::path::Path::new("ai/decks/liella_cup.txt").exists() {
        "ai/decks/liella_cup.txt"
    } else {
        "../ai/decks/liella_cup.txt"
    };

    let (p0_members, p0_lives) = load_deck(deck_path, &db);
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    let mut state = GameState::default();
    state.initialize_game(
        p0_members.clone(),
        p0_members.clone(),
        energy.clone(),
        energy.clone(),
        p0_lives.clone(),
        p0_lives.clone(),
    );
    state.ui.silent = true;

    // Advance to first Main phase
    while state.phase != Phase::Main && !state.is_terminal() {
        state.auto_step(&db);
    }

    println!("\n╔═══════════════════════════════════════════════════╗");
    println!("║  Move Sequence Enumeration & State Explosion   ║");
    println!("╚═══════════════════════════════════════════════════╝\n");

    let legal_root = state.get_legal_action_ids(&db);
    
    println!("Initial State:");
    println!("  Current player: P{}", state.current_player);
    println!("  Phase: {:?}", state.phase);
    println!("  Hand size: {}", state.players[0].hand.len());
    println!("  Stage: {} cards", state.players[0].stage.iter().filter(|&&c| c >= 0).count());
    println!("  Legal actions: {}\n", legal_root.len());

    // Theoretical analysis
    println!("Move Space Analysis:\n");
    println!("Depth | Branching | Est. Tree Size | Est. Compressed (AB)");
    println!("────────────────────────────────────────────────────────");

    let branching = legal_root.len() as f64;
    for depth in 1..=10 {
        let tree_size = branching.powi(depth as i32);
        // Alpha-beta roughly reduces by factor of sqrt(branching)
        let compressed = (branching.sqrt()).powi(depth as i32);
        
        println!(
            "{:>5} | {:>9.1} | {:>14.0} | {:>19.0}",
            depth, branching, tree_size, compressed
        );
    }

    println!("\n╔═══════════════════════════════════════════════════╗");
    println!("║  Key Insight: Equivalent Moves                  ║");
    println!("╚═══════════════════════════════════════════════════╝\n");

    println!("If all 3 stage slots are empty:");
    println!("  Placing card A then B then C");
    println!("  Placing card C then B then A");
    println!("  Placing card B then A then C");
    println!("  → These explore 3! = 6 sequences");
    println!("  → But lead to SAME board state if no abilities trigger\n");

    println!("With abilities that trigger on placement:");
    println!("  Order MATTERS because effects can change what's legal next\n");

    println!("Conclusion:");
    println!("  • Legal branching factor: ~6-8 actions per state (realistic)");
    println!("  • Depth N explores 6^N states without pruning");
    println!("  • Move ordering + pruning: reduces to ~6^(N/3) effective nodes");
    println!("  • Alpha-beta effectiveness depends on ability-triggered order changes\n");
}
