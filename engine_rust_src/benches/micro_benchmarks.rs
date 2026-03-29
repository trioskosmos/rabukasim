use criterion::{black_box, criterion_group, criterion_main, Criterion};
use engine_rust::core::models::Phase;
use engine_rust::core::logic::{CardDatabase, GameState};
use rand::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::sync::OnceLock;
use std::time::{Duration, Instant};

fn load_full_db() -> CardDatabase {
    for path in &["data/cards.json", "../data/cards.json", "../../data/cards.json"] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = false;
            return db;
        }
    }
    panic!("DB not found");
}

fn build_real_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    while deck.len() < 48 { if let Some(&id) = db.members.keys().next() { deck.push(id); } else { break; } }
    let mut lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    while lives.len() < 12 { if let Some(&id) = db.lives.keys().next() { lives.push(id); } else { break; } }
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    (deck, lives, energy)
}

fn select_smart_action(actions: &[i32], rng: &mut StdRng) -> i32 {
    // Prioritize playing members (lower action IDs typically)
    // Action 0 is pass/end phase - avoid if we have plays available
    if actions.len() == 1 {
        return actions[0];
    }
    
    // Try to find a member play action (non-zero, non-pass actions)
    let play_actions: Vec<&i32> = actions.iter().filter(|&&a| a != 0).collect();
    
    if !play_actions.is_empty() {
        // 80% chance to play a card, 20% to pass
        if rng.random_bool(0.8) {
            return *play_actions[rng.gen_range(0..play_actions.len())];
        }
    }
    
    // Default to random selection
    actions[rng.gen_range(0..actions.len())]
}

#[derive(Debug, Default)]
struct TimingStats {
    count: u64, total_ns: u64, min_ns: u64, max_ns: u64, slow_count: u64,
}

impl TimingStats {
    fn record(&mut self, duration_ns: u64, slow_threshold_ns: u64) {
        self.count += 1; self.total_ns += duration_ns;
        if self.min_ns == 0 || duration_ns < self.min_ns { self.min_ns = duration_ns; }
        if duration_ns > self.max_ns { self.max_ns = duration_ns; }
        if duration_ns > slow_threshold_ns { self.slow_count += 1; }
    }
    fn avg_ns(&self) -> u64 { if self.count == 0 { 0 } else { self.total_ns / self.count } }
}

#[derive(Debug, Clone, serde::Serialize)]
struct SlowEvent {
    operation: String,
    phase: String,
    duration_ns: u64,
    turn: u16,
    action_taken: i32,
    game_state_json: String,
    // Board state analysis - what makes this position slow
    board_analysis: BoardAnalysis,
}

#[derive(Debug, Clone, serde::Serialize, Default)]
struct BoardAnalysis {
    // Stage composition
    p0_stage_cards: Vec<i32>,
    p1_stage_cards: Vec<i32>,
    p0_live_zone: Vec<i32>,
    p1_live_zone: Vec<i32>,
    // Complexity metrics
    p0_granted_abilities: usize,
    p1_granted_abilities: usize,
    p0_hand_size: usize,
    p1_hand_size: usize,
    p0_discard_size: usize,
    p1_discard_size: usize,
    // Active effects
    p0_yell_cards: usize,
    p1_yell_cards: usize,
    // Performance flags
    has_constant_abilities: bool,
    has_color_transforms: bool,
    has_cost_modifiers: bool,
}

fn analyze_board_state(state: &GameState, db: &CardDatabase) -> BoardAnalysis {
    use engine_rust::core::enums::TriggerType;

    let mut analysis = BoardAnalysis::default();
    
    // Stage composition
    analysis.p0_stage_cards = state.players[0].stage.iter().copied().filter(|&c| c >= 0).collect();
    analysis.p1_stage_cards = state.players[1].stage.iter().copied().filter(|&c| c >= 0).collect();
    analysis.p0_live_zone = state.players[0].live_zone.iter().copied().filter(|&c| c >= 0).collect();
    analysis.p1_live_zone = state.players[1].live_zone.iter().copied().filter(|&c| c >= 0).collect();
    
    // Complexity metrics
    analysis.p0_granted_abilities = state.players[0].granted_abilities.len();
    analysis.p1_granted_abilities = state.players[1].granted_abilities.len();
    analysis.p0_hand_size = state.players[0].hand.len();
    analysis.p1_hand_size = state.players[1].hand.len();
    analysis.p0_discard_size = state.players[0].discard.len();
    analysis.p1_discard_size = state.players[1].discard.len();
    
    // Active effects
    analysis.p0_yell_cards = state.players[0].yell_cards.len();
    analysis.p1_yell_cards = state.players[1].yell_cards.len();
    
    // Check for constant abilities on stage
    for &cid in &analysis.p0_stage_cards {
        if let Some(m) = db.get_member(cid) {
            if m.abilities.iter().any(|a| a.trigger == TriggerType::Constant) {
                analysis.has_constant_abilities = true;
                break;
            }
        }
    }
    if !analysis.has_constant_abilities {
        for &cid in &analysis.p1_stage_cards {
            if let Some(m) = db.get_member(cid) {
                if m.abilities.iter().any(|a| a.trigger == TriggerType::Constant) {
                    analysis.has_constant_abilities = true;
                    break;
                }
            }
        }
    }
    
    // Check for color transforms and cost modifiers
    analysis.has_color_transforms = !state.players[0].color_transforms.is_empty() 
        || !state.players[1].color_transforms.is_empty();
    analysis.has_cost_modifiers = !state.players[0].cost_modifiers.is_empty()
        || !state.players[1].cost_modifiers.is_empty();
    
    analysis
}

fn run_game_with_slow_capture(
    db: &CardDatabase,
    deck: &[i32],
    lives: &[i32],
    energy: &[i32],
    slow_threshold_ns: u64,
    rng: &mut StdRng,
    slow_events: &mut Vec<SlowEvent>,
) -> (i32, HashMap<String, TimingStats>) {
    let mut stats: HashMap<String, TimingStats> = HashMap::new();
    let mut state = GameState::default();
    state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
    state.ui.silent = true;
    
    // Skip RPS and turn choice - start directly at mulligan
    state.phase = Phase::MulliganP1;
    state.current_player = 0;
    state.first_player = 0;

    let mut auto_steps = 0;

    while state.phase != Phase::Terminal {
        if auto_steps > 100000 { break; }
        let phase = state.phase;

        if state.phase.is_interactive() {
            let t1 = Instant::now();
            let actions = state.get_legal_action_ids(db);
            let get_actions_ns = t1.elapsed().as_nanos() as u64;
            stats.entry(format!("{:?}:get_actions", phase)).or_default().record(get_actions_ns, slow_threshold_ns);

            if get_actions_ns > slow_threshold_ns {
                let analysis = analyze_board_state(&state, db);
                slow_events.push(SlowEvent {
                    operation: format!("{:?}:get_actions", phase),
                    phase: format!("{:?}", state.phase),
                    duration_ns: get_actions_ns,
                    turn: state.turn,
                    action_taken: -1,
                    game_state_json: serde_json::to_string(&state).unwrap_or_default(),
                    board_analysis: analysis,
                });
            }

            if !actions.is_empty() {
                let action = select_smart_action(&actions, rng);
                let t2 = Instant::now();
                let _ = state.step(db, action);
                let step_ns = t2.elapsed().as_nanos() as u64;
                stats.entry(format!("{:?}:step", phase)).or_default().record(step_ns, slow_threshold_ns);

                if step_ns > slow_threshold_ns {
                    let analysis = analyze_board_state(&state, db);
                    slow_events.push(SlowEvent {
                        operation: format!("{:?}:step", phase),
                        phase: format!("{:?}", state.phase),
                        duration_ns: step_ns,
                        turn: state.turn,
                        action_taken: action,
                        game_state_json: serde_json::to_string(&state).unwrap_or_default(),
                        board_analysis: analysis,
                    });
                }
            }
        } else {
            auto_steps += 1;
            let t = Instant::now();
            state.auto_step(db);
            let auto_ns = t.elapsed().as_nanos() as u64;
            stats.entry(format!("{:?}:auto", phase)).or_default().record(auto_ns, slow_threshold_ns);
        }
    }
    (state.get_winner(), stats)
}

fn benchmark_slow_action_detector(c: &mut Criterion) {
    let db = load_full_db();
    let (deck, lives, energy) = build_real_decks(&db);
    let mut group = c.benchmark_group("slow_action_detector");
    group.sample_size(10);
    group.measurement_time(Duration::from_secs(1));
    let slow_threshold_ns = 1_000; // 1 microsecond

    group.bench_function("real_games_with_abilities", |b| {
        b.iter(|| {
            let mut all_stats: HashMap<String, TimingStats> = HashMap::new();
            let mut slow_events: Vec<SlowEvent> = Vec::new();
            let mut rng = StdRng::seed_from_u64(42);
            let mut completed_games = 0;
            let mut total_games = 0;

            // Run fixed number of games per iteration (let Criterion handle timing)
            for _ in 0..1 {
                total_games += 1;
                let (winner, game_stats) = run_game_with_slow_capture(&db, &deck, &lives, &energy, slow_threshold_ns, &mut rng, &mut slow_events);
                if winner >= 0 {
                    completed_games += 1;
                }
                for (key, stats) in game_stats {
                    let entry = all_stats.entry(key).or_default();
                    entry.count += stats.count;
                    entry.total_ns += stats.total_ns;
                    if entry.min_ns == 0 || stats.min_ns < entry.min_ns { entry.min_ns = stats.min_ns; }
                    if stats.max_ns > entry.max_ns { entry.max_ns = stats.max_ns; }
                    entry.slow_count += stats.slow_count;
                }
            }

            // Save slow events to file for analysis
            if !slow_events.is_empty() {
                let slow_data = serde_json::to_string_pretty(&slow_events).unwrap_or_default();
                let _ = fs::write("target/slow_events.json", slow_data);
                eprintln!("\n=== CAPTURED {} SLOW EVENTS ===", slow_events.len());
                eprintln!("Saved to: target/slow_events.json");
                
                // Group by operation type
                let mut by_op: HashMap<&str, Vec<&SlowEvent>> = HashMap::new();
                for event in &slow_events {
                    by_op.entry(&event.operation).or_default().push(event);
                }
                for (op, events) in by_op {
                    eprintln!("  {}: {} events (max: {} us)", op, events.len(), 
                        events.iter().map(|e| e.duration_ns).max().unwrap_or(0) / 1000);
                }
            }

            eprintln!("\n=== RESULTS (Real Games with Abilities) ===");
            eprintln!("Completed games: {} / {} ({}%)", completed_games, total_games, 
                (completed_games * 100) / total_games.max(1));
            
            let mut sorted: Vec<_> = all_stats.iter().collect();
            sorted.sort_by(|a, b| b.1.max_ns.cmp(&a.1.max_ns));
            eprintln!("\nTop operations by max time:");
            for (op, stats) in sorted.iter().take(10) {
                eprintln!("{:35} | cnt: {:8} | avg: {:6} ns | max: {:8} ns | slow: {}", 
                    op, stats.count, stats.avg_ns(), stats.max_ns, stats.slow_count);
            }

            black_box(all_stats);
        });
    });
    group.finish();
}

criterion_group!(benches, benchmark_slow_action_detector);
criterion_main!(benches);
