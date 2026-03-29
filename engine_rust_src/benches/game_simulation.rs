use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use rand::prelude::StdRng;
use rand::SeedableRng;
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

fn benchmark_full_game(c: &mut Criterion) {
    let db = load_vanilla_db();
    let (deck, lives, energy) = build_decks(&db);

    let mut group = c.benchmark_group("full_game_simulation");
    group.measurement_time(Duration::from_secs(10));
    group.sample_size(10);

    group.bench_function("vanilla_ai_vs_ai", |b| {
        b.iter(|| {
            let mut state = GameState::default();
            state.initialize_game(
                deck.clone(),
                deck.clone(),
                energy.clone(),
                energy.clone(),
                lives.clone(),
                lives.clone(),
            );

            let mut turn = 0;
            let mut auto_steps = 0;
            let max_auto_steps = 10000;

            while state.phase != Phase::Terminal && turn < 200 {
                if auto_steps > max_auto_steps {
                    break;
                }

                if state.phase.is_interactive() {
                    turn += 1;
                    match state.phase {
                        Phase::Main => {
                            let (seq, _, _) = TurnSequencer::find_best_main_sequence(&state, &db);
                            for a in seq {
                                let _ = state.step(&db, a);
                            }
                            if state.phase == Phase::Main {
                                let _ = state.step(&db, ACTION_BASE_PASS);
                            }
                        }
                        Phase::LiveSet => {
                            let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
                            for a in seq {
                                let _ = state.step(&db, a);
                            }
                            let _ = state.step(&db, ACTION_BASE_PASS);
                        }
                        _ => {
                            let actions = state.get_legal_action_ids(&db);
                            if !actions.is_empty() {
                                let _ = state.step(&db, actions[0]);
                            }
                        }
                    }
                } else {
                    auto_steps += 1;
                    let actions = state.get_legal_action_ids(&db);
                    if !actions.is_empty() {
                        let _ = state.step(&db, actions[0]);
                    } else {
                        state.auto_step(&db);
                    }
                }
            }

            black_box(state.get_winner());
        });
    });

    group.finish();
}

fn benchmark_game_phases(c: &mut Criterion) {
    let db = load_vanilla_db();
    let (deck, lives, energy) = build_decks(&db);

    let mut group = c.benchmark_group("game_phases");
    group.measurement_time(Duration::from_secs(5));
    group.sample_size(20);

    group.bench_function("game_initialization", |b| {
        b.iter(|| {
            let mut state = GameState::default();
            state.initialize_game(
                black_box(deck.clone()),
                black_box(deck.clone()),
                black_box(energy.clone()),
                black_box(energy.clone()),
                black_box(lives.clone()),
                black_box(lives.clone()),
            );
        });
    });

    group.bench_function("auto_step_through_mulligan", |b| {
        let mut state = GameState::default();
        state.initialize_game(
            deck.clone(),
            deck.clone(),
            energy.clone(),
            energy.clone(),
            lives.clone(),
            lives.clone(),
        );

        b.iter(|| {
            let mut test_state = state.clone();
            let mut steps = 0;
            while test_state.phase != Phase::Main && steps < 100 {
                test_state.auto_step(&db);
                steps += 1;
            }
            black_box(steps);
        });
    });

    group.finish();
}

fn benchmark_batch_games(c: &mut Criterion) {
    let db = load_vanilla_db();
    let (deck, lives, energy) = build_decks(&db);

    let mut group = c.benchmark_group("batch_simulation");
    group.measurement_time(Duration::from_secs(30));
    group.sample_size(10);

    for game_count in [5, 10, 25].iter() {
        group.bench_with_input(
            BenchmarkId::new("games", game_count),
            game_count,
            |b, &count| {
                b.iter(|| {
                    for i in 0..count {
                        let mut state = GameState::default();
                        state.initialize_game(
                            deck.clone(),
                            deck.clone(),
                            energy.clone(),
                            energy.clone(),
                            lives.clone(),
                            lives.clone(),
                        );

                        let mut turn = 0;
                        let mut auto_steps = 0;
                        let max_auto_steps = 10000;

                        while state.phase != Phase::Terminal && turn < 200 {
                            if auto_steps > max_auto_steps {
                                break;
                            }

                            if state.phase.is_interactive() {
                                turn += 1;
                                match state.phase {
                                    Phase::Main => {
                                        let (seq, _, _) = TurnSequencer::find_best_main_sequence(&state, &db);
                                        for a in seq {
                                            let _ = state.step(&db, a);
                                        }
                                        if state.phase == Phase::Main {
                                            let _ = state.step(&db, ACTION_BASE_PASS);
                                        }
                                    }
                                    Phase::LiveSet => {
                                        let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
                                        for a in seq {
                                            let _ = state.step(&db, a);
                                        }
                                        let _ = state.step(&db, ACTION_BASE_PASS);
                                    }
                                    _ => {
                                        let actions = state.get_legal_action_ids(&db);
                                        if !actions.is_empty() {
                                            let _ = state.step(&db, actions[0]);
                                        }
                                    }
                                }
                            } else {
                                auto_steps += 1;
                                let actions = state.get_legal_action_ids(&db);
                                if !actions.is_empty() {
                                    let _ = state.step(&db, actions[0]);
                                } else {
                                    state.auto_step(&db);
                                }
                            }
                        }
                        black_box(state.get_winner());
                    }
                });
            },
        );
    }

    group.finish();
}

criterion_group!(benches, benchmark_full_game, benchmark_game_phases, benchmark_batch_games);
criterion_main!(benches);
