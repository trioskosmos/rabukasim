use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::card_db::{CardDatabase, MemberCard};
use engine_rust::core::logic::GameState;
use std::fs;
use std::time::Duration;

fn load_vanilla_db() -> CardDatabase {
    for path in &[
        "data/cards_vanilla.json",
        "../data/cards_vanilla.json",
        "../../data/cards_vanilla.json",
    ] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = true;
            return db;
        }
    }
    panic!("DB not found - run from engine_rust_src/ directory");
}

fn build_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
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

fn setup_game_with_phase(db: &CardDatabase, deck: &[i32], lives: &[i32], energy: &[i32]) -> GameState {
    let mut state = GameState::default();
    state.initialize_game(
        deck.to_vec(),
        deck.to_vec(),
        energy.to_vec(),
        energy.to_vec(),
        lives.to_vec(),
        lives.to_vec(),
    );
    state
}

fn benchmark_main_sequence(c: &mut Criterion) {
    let db = load_vanilla_db();
    let (deck, lives, energy) = build_decks(&db);

    let mut group = c.benchmark_group("turn_sequencer_main");
    group.measurement_time(Duration::from_secs(10));
    group.sample_size(20);

    let mut state = setup_game_with_phase(&db, &deck, &lives, &energy);

    for _ in 0..50 {
        state.auto_step(&db);
        if state.phase == engine_rust::core::enums::Phase::Main {
            break;
        }
    }

    if state.phase == engine_rust::core::enums::Phase::Main {
        group.bench_function("find_best_main_sequence", |b| {
            b.iter(|| {
                let result = TurnSequencer::find_best_main_sequence(&state, &db);
                black_box(result);
            });
        });
    }

    group.finish();
}

fn benchmark_liveset_sequence(c: &mut Criterion) {
    let db = load_vanilla_db();
    let (deck, lives, energy) = build_decks(&db);

    let mut group = c.benchmark_group("turn_sequencer_liveset");
    group.measurement_time(Duration::from_secs(10));
    group.sample_size(20);

    let mut state = setup_game_with_phase(&db, &deck, &lives, &energy);

    for _ in 0..100 {
        state.auto_step(&db);
        if state.phase == engine_rust::core::enums::Phase::LiveSet {
            break;
        }
    }

    if state.phase == engine_rust::core::enums::Phase::LiveSet {
        group.bench_function("find_best_liveset_selection", |b| {
            b.iter(|| {
                let result = TurnSequencer::find_best_liveset_selection(&state, &db);
                black_box(result);
            });
        });
    }

    group.finish();
}

fn benchmark_sequencer_scaling(c: &mut Criterion) {
    let db = load_vanilla_db();
    let (deck, lives, energy) = build_decks(&db);

    let mut group = c.benchmark_group("sequencer_scaling");
    group.measurement_time(Duration::from_secs(15));
    group.sample_size(10);

    let mut state = setup_game_with_phase(&db, &deck, &lives, &energy);

    let mut step_counts = vec![];
    for target_steps in [10, 25, 50, 100].iter() {
        let mut test_state = state.clone();
        let mut steps = 0;
        for _ in 0..*target_steps {
            test_state.auto_step(&db);
            steps += 1;
            if test_state.phase == engine_rust::core::enums::Phase::Terminal {
                break;
            }
        }
        step_counts.push((steps, test_state.clone()));
    }

    for (steps, test_state) in step_counts {
        if test_state.phase == engine_rust::core::enums::Phase::Main {
            group.bench_with_input(
                BenchmarkId::new("main_sequence", steps),
                &test_state,
                |b, s| {
                    b.iter(|| {
                        let result = TurnSequencer::find_best_main_sequence(s, &db);
                        black_box(result);
                    });
                },
            );
        }
    }

    group.finish();
}

criterion_group!(
    benches,
    benchmark_main_sequence,
    benchmark_liveset_sequence,
    benchmark_sequencer_scaling
);
criterion_main!(benches);
