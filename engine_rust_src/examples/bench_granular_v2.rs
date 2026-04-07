//! Consolidated granular benchmark for real-rule engine execution.
//!
//! This replaces the older split between "real game", "detect slow", and
//! follow-up analysis helpers. The benchmark now:
//! - initializes games through the normal engine path
//! - skips RPS by forcing a starting player, but keeps the rest of setup intact
//! - runs in silent mode to avoid rule-log overhead
//! - plays many games inside a fixed wall-clock budget
//! - uses random decks, random shuffles, and random starting players
//! - follows the front-end style path for Main/LiveSet via TurnSequencer
//! - captures and aggregates slow board states directly
//!
//! This tool is meant to guide optimization work. During large refactors the
//! absolute numbers may move around, so the slow-state fingerprints are often
//! more useful than any single headline timing.

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use rand::rngs::SmallRng;
use rand::seq::{IndexedRandom, SliceRandom};
use rand::{Rng, SeedableRng};
use std::collections::HashMap;
use std::fs;
use std::time::Instant;

const DEFAULT_BENCH_SECS: u64 = 10;
const DEFAULT_MAX_MAIN_TURNS: usize = 10;
const DEFAULT_MAX_TOTAL_STEPS: usize = 2000;
const DEFAULT_SLOW_US: u64 = 2_000;
const TOP_SLOW_MOMENTS: usize = 20;
const TOP_PATTERNS: usize = 12;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum Operation {
    Setup,
    MainPlan,
    MainExec,
    LiveSetPlan,
    LiveSetExec,
    AutoStep,
    LiveResult,
    FallbackStep,
}

#[derive(Debug, Default, Clone)]
struct OperationStats {
    calls: u64,
    total_ns: u64,
    max_ns: u64,
}

#[derive(Debug, Clone)]
struct BoardSnapshot {
    phase: Phase,
    turn: u16,
    player: u8,
    p0_stage: Vec<i32>,
    p1_stage: Vec<i32>,
    p0_live: Vec<i32>,
    p1_live: Vec<i32>,
    p0_hand: usize,
    p1_hand: usize,
    p0_score: u32,
    p1_score: u32,
    p0_success: usize,
    p1_success: usize,
    p0_granted: usize,
    p1_granted: usize,
    trigger_queue: usize,
    interaction_stack: usize,
}

impl BoardSnapshot {
    fn capture(state: &GameState) -> Self {
        Self {
            phase: state.phase,
            turn: state.turn,
            player: state.current_player,
            p0_stage: state.players[0].stage.to_vec(),
            p1_stage: state.players[1].stage.to_vec(),
            p0_live: state.players[0].live_zone.iter().copied().collect(),
            p1_live: state.players[1].live_zone.iter().copied().collect(),
            p0_hand: state.players[0].hand.len(),
            p1_hand: state.players[1].hand.len(),
            p0_score: state.players[0].score,
            p1_score: state.players[1].score,
            p0_success: state.players[0].success_lives.len(),
            p1_success: state.players[1].success_lives.len(),
            p0_granted: state.players[0].granted_abilities.len(),
            p1_granted: state.players[1].granted_abilities.len(),
            trigger_queue: state.core.trigger_queue.len(),
            interaction_stack: state.interaction_stack.len(),
        }
    }

    fn fingerprint(&self) -> String {
        let p0_stage_count = self.p0_stage.iter().filter(|&&cid| cid >= 0).count();
        let p1_stage_count = self.p1_stage.iter().filter(|&&cid| cid >= 0).count();
        let p0_live_count = self.p0_live.iter().filter(|&&cid| cid >= 0).count();
        let p1_live_count = self.p1_live.iter().filter(|&&cid| cid >= 0).count();
        format!(
            "phase={:?}|stage={}-{}|live={}-{}|hand={}-{}|success={}-{}|granted={}-{}|tq={}|stack={}",
            self.phase,
            p0_stage_count,
            p1_stage_count,
            p0_live_count,
            p1_live_count,
            self.p0_hand,
            self.p1_hand,
            self.p0_success,
            self.p1_success,
            self.p0_granted,
            self.p1_granted,
            self.trigger_queue,
            self.interaction_stack,
        )
    }
}

#[derive(Debug, Clone)]
struct SlowMoment {
    op: Operation,
    duration_us: u64,
    detail: String,
    snapshot: BoardSnapshot,
}

#[derive(Debug, Default, Clone)]
struct PatternStats {
    count: u64,
    total_us: u64,
    max_us: u64,
    sample: Option<BoardSnapshot>,
}

#[derive(Debug, Default)]
struct BenchmarkTimer {
    by_op: HashMap<Operation, OperationStats>,
}

impl BenchmarkTimer {
    fn record(&mut self, op: Operation, ns: u64) {
        let entry = self.by_op.entry(op).or_default();
        entry.calls += 1;
        entry.total_ns += ns;
        entry.max_ns = entry.max_ns.max(ns);
    }

    fn total_ns(&self) -> u64 {
        self.by_op.values().map(|stats| stats.total_ns).sum()
    }

    fn print(&self) {
        let total_ns = self.total_ns();
        println!("\n=== Operation Timing ===");
        println!(
            "{:<12} {:>8} {:>11} {:>10} {:>10} {:>7}",
            "Operation", "Calls", "Total(ms)", "Avg(μs)", "Max(μs)", "%time"
        );
        println!("{}", "-".repeat(70));

        let mut rows: Vec<_> = self.by_op.iter().collect();
        rows.sort_by(|a, b| b.1.total_ns.cmp(&a.1.total_ns));
        for (op, stats) in rows {
            let pct = if total_ns == 0 {
                0.0
            } else {
                stats.total_ns as f64 / total_ns as f64 * 100.0
            };
            println!(
                "{:<12?} {:>8} {:>11.2} {:>10.1} {:>10.1} {:>6.1}%",
                op,
                stats.calls,
                stats.total_ns as f64 / 1_000_000.0,
                stats.total_ns as f64 / stats.calls.max(1) as f64 / 1000.0,
                stats.max_ns as f64 / 1000.0,
                pct,
            );
        }
        println!("{}", "-".repeat(70));
        println!(
            "{:<12} {:>8} {:>11.2}ms",
            "TOTAL",
            "",
            total_ns as f64 / 1_000_000.0
        );
    }
}

#[derive(Debug, Default)]
struct GameResult {
    duration_ns: u64,
    total_steps: usize,
    main_turns: usize,
    reached_terminal: bool,
}

#[derive(Debug, Clone, Copy)]
struct Config {
    bench_secs: u64,
    max_main_turns: usize,
    max_total_steps: usize,
    slow_us: u64,
}

impl Config {
    fn from_env() -> Self {
        Self {
            bench_secs: env_u64("BENCH_SECS", DEFAULT_BENCH_SECS),
            max_main_turns: env_usize("BENCH_MAX_MAIN_TURNS", DEFAULT_MAX_MAIN_TURNS),
            max_total_steps: env_usize("BENCH_MAX_TOTAL_STEPS", DEFAULT_MAX_TOTAL_STEPS),
            slow_us: env_u64("BENCH_SLOW_US", DEFAULT_SLOW_US),
        }
    }
}

fn env_u64(key: &str, default: u64) -> u64 {
    std::env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn env_usize(key: &str, default: usize) -> usize {
    std::env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn load_db() -> CardDatabase {
    for path in [
        "data/cards_compiled.json",
        "../data/cards_compiled.json",
        "../../data/cards_compiled.json",
    ] {
        if !std::path::Path::new(path).exists() {
            continue;
        }

        let json = fs::read_to_string(path).expect("read cards_compiled.json");
        let mut db = CardDatabase::from_json(&json).expect("parse cards_compiled.json");
        db.is_vanilla = false;
        return db;
    }

    panic!("cards_compiled.json not found");
}

fn build_random_deck(db: &CardDatabase, rng: &mut SmallRng) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut members: Vec<i32> = db.members.keys().copied().collect();
    let mut lives: Vec<i32> = db.lives.keys().copied().collect();
    let mut energy: Vec<i32> = db.energy_db.keys().copied().collect();

    members.shuffle(rng);
    lives.shuffle(rng);
    energy.shuffle(rng);

    members.truncate(48);
    lives.truncate(12);
    energy.truncate(12);

    while members.len() < 48 {
        if let Some(&cid) = members.first() {
            members.push(cid);
        } else {
            break;
        }
    }
    while lives.len() < 12 {
        if let Some(&cid) = lives.first() {
            lives.push(cid);
        } else {
            break;
        }
    }
    while energy.len() < 12 {
        if let Some(&cid) = energy.first() {
            energy.push(cid);
        } else {
            break;
        }
    }

    (members, lives, energy)
}

fn force_starting_player(state: &mut GameState, first_player: u8) {
    state.first_player = first_player;
    state.current_player = first_player;
    state.phase = Phase::MulliganP1;
    state.rps_choices = [first_player as i8, (1 - first_player) as i8];
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
            let score = db.get_live(cid).map(|live| live.score as i32).unwrap_or(-1);
            if score > best_score {
                best_score = score;
                best_action = action;
            }
        }
    }

    best_action
}

fn record_slow(
    slow_moments: &mut Vec<SlowMoment>,
    patterns: &mut HashMap<String, PatternStats>,
    state: &GameState,
    op: Operation,
    duration_ns: u64,
    threshold_us: u64,
    detail: impl Into<String>,
) {
    let duration_us = duration_ns / 1000;
    if duration_us < threshold_us {
        return;
    }

    let snapshot = BoardSnapshot::capture(state);
    slow_moments.push(SlowMoment {
        op,
        duration_us,
        detail: detail.into(),
        snapshot: snapshot.clone(),
    });

    let fingerprint = snapshot.fingerprint();
    let entry = patterns.entry(fingerprint).or_default();
    entry.count += 1;
    entry.total_us += duration_us;
    entry.max_us = entry.max_us.max(duration_us);
    if entry.sample.is_none() {
        entry.sample = Some(snapshot);
    }
}

fn advance_to_main(
    state: &mut GameState,
    db: &CardDatabase,
    rng: &mut SmallRng,
    timer: &mut BenchmarkTimer,
    slow_moments: &mut Vec<SlowMoment>,
    patterns: &mut HashMap<String, PatternStats>,
    config: Config,
) {
    let mut setup_steps = 0usize;
    while !matches!(state.phase, Phase::Main | Phase::Terminal) && setup_steps < 64 {
        setup_steps += 1;
        let t0 = Instant::now();
        match state.phase {
            Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                let legal = state.get_legal_action_ids(db);
                let action = legal.choose(rng).copied().unwrap_or(ACTION_BASE_PASS);
                let _ = state.step(db, action);
            }
            Phase::Rps => {
                let _ = state.step(db, ACTION_BASE_PASS);
            }
            _ => {
                state.auto_step(db);
            }
        }
        let elapsed_ns = t0.elapsed().as_nanos() as u64;
        timer.record(Operation::Setup, elapsed_ns);
        record_slow(
            slow_moments,
            patterns,
            state,
            Operation::Setup,
            elapsed_ns,
            config.slow_us,
            format!("phase={:?}", state.phase),
        );
    }
}

fn execute_planned_sequence(
    state: &mut GameState,
    db: &CardDatabase,
    actions: &[i32],
    op: Operation,
    timer: &mut BenchmarkTimer,
    slow_moments: &mut Vec<SlowMoment>,
    patterns: &mut HashMap<String, PatternStats>,
    config: Config,
) -> usize {
    let initial_player = state.current_player;
    let phase = state.phase;
    let mut executed = 0usize;

    for &action in actions {
        if state.is_terminal() || state.phase != phase || state.current_player != initial_player {
            break;
        }

        let legal = state.get_legal_action_ids(db);
        if !legal.contains(&action) {
            break;
        }

        let t0 = Instant::now();
        let _ = state.step(db, action);
        let elapsed_ns = t0.elapsed().as_nanos() as u64;
        timer.record(op, elapsed_ns);
        record_slow(
            slow_moments,
            patterns,
            state,
            op,
            elapsed_ns,
            config.slow_us,
            format!("action={action}|legal={}", legal.len()),
        );
        executed += 1;
    }

    if state.phase == phase && state.current_player == initial_player {
        let t0 = Instant::now();
        let _ = state.step(db, ACTION_BASE_PASS);
        let elapsed_ns = t0.elapsed().as_nanos() as u64;
        timer.record(op, elapsed_ns);
        record_slow(
            slow_moments,
            patterns,
            state,
            op,
            elapsed_ns,
            config.slow_us,
            "action=PASS",
        );
        executed += 1;
    }

    executed
}

fn run_one_game(
    db: &CardDatabase,
    rng: &mut SmallRng,
    timer: &mut BenchmarkTimer,
    slow_moments: &mut Vec<SlowMoment>,
    patterns: &mut HashMap<String, PatternStats>,
    config: Config,
) -> GameResult {
    let game_start = Instant::now();
    let (p0_members, p0_lives, p0_energy) = build_random_deck(db, rng);
    let (p1_members, p1_lives, p1_energy) = build_random_deck(db, rng);

    let mut state = GameState::default();
    state.initialize_game(
        p0_members, p1_members, p0_energy, p1_energy, p0_lives, p1_lives,
    );
    state.ui.silent = true;
    force_starting_player(&mut state, rng.random_range(0..=1));

    let mut setup_rng = SmallRng::seed_from_u64(rng.random());
    advance_to_main(
        &mut state,
        db,
        &mut setup_rng,
        timer,
        slow_moments,
        patterns,
        config,
    );

    let mut total_steps = 0usize;
    let mut main_turns = 0usize;
    while !state.is_terminal()
        && total_steps < config.max_total_steps
        && main_turns < (config.max_main_turns * 2)
    {
        match state.phase {
            Phase::Main => {
                main_turns += 1;
                let t0 = Instant::now();
                let (sequence, _, _, evals) = TurnSequencer::plan_full_turn(&state, db);
                let elapsed_ns = t0.elapsed().as_nanos() as u64;
                timer.record(Operation::MainPlan, elapsed_ns);
                record_slow(
                    slow_moments,
                    patterns,
                    &state,
                    Operation::MainPlan,
                    elapsed_ns,
                    config.slow_us,
                    format!("seq_len={}|evals={evals}", sequence.len()),
                );
                total_steps += execute_planned_sequence(
                    &mut state,
                    db,
                    &sequence,
                    Operation::MainExec,
                    timer,
                    slow_moments,
                    patterns,
                    config,
                );
            }
            Phase::LiveSet => {
                let t0 = Instant::now();
                let (sequence, nodes, live_ev) =
                    TurnSequencer::find_best_liveset_selection(&state, db);
                let elapsed_ns = t0.elapsed().as_nanos() as u64;
                timer.record(Operation::LiveSetPlan, elapsed_ns);
                record_slow(
                    slow_moments,
                    patterns,
                    &state,
                    Operation::LiveSetPlan,
                    elapsed_ns,
                    config.slow_us,
                    format!("seq_len={}|nodes={nodes}|live_ev={live_ev}", sequence.len()),
                );
                total_steps += execute_planned_sequence(
                    &mut state,
                    db,
                    &sequence,
                    Operation::LiveSetExec,
                    timer,
                    slow_moments,
                    patterns,
                    config,
                );
            }
            Phase::LiveResult => {
                let legal = state.get_legal_action_ids(db);
                let action = choose_best_live_result_action(&state, db);
                let t0 = Instant::now();
                let _ = state.step(db, action);
                let elapsed_ns = t0.elapsed().as_nanos() as u64;
                timer.record(Operation::LiveResult, elapsed_ns);
                record_slow(
                    slow_moments,
                    patterns,
                    &state,
                    Operation::LiveResult,
                    elapsed_ns,
                    config.slow_us,
                    format!("action={action}|legal={}", legal.len()),
                );
                total_steps += 1;
            }
            Phase::Active
            | Phase::Draw
            | Phase::Energy
            | Phase::PerformanceP1
            | Phase::PerformanceP2 => {
                let t0 = Instant::now();
                state.auto_step(db);
                let elapsed_ns = t0.elapsed().as_nanos() as u64;
                timer.record(Operation::AutoStep, elapsed_ns);
                record_slow(
                    slow_moments,
                    patterns,
                    &state,
                    Operation::AutoStep,
                    elapsed_ns,
                    config.slow_us,
                    format!("phase={:?}", state.phase),
                );
                total_steps += 1;
            }
            Phase::Terminal => break,
            _ => {
                let legal = state.get_legal_action_ids(db);
                let action = legal.choose(rng).copied().unwrap_or(ACTION_BASE_PASS);
                let t0 = Instant::now();
                let _ = state.step(db, action);
                let elapsed_ns = t0.elapsed().as_nanos() as u64;
                timer.record(Operation::FallbackStep, elapsed_ns);
                record_slow(
                    slow_moments,
                    patterns,
                    &state,
                    Operation::FallbackStep,
                    elapsed_ns,
                    config.slow_us,
                    format!(
                        "phase={:?}|action={action}|legal={}",
                        state.phase,
                        legal.len()
                    ),
                );
                total_steps += 1;
            }
        }
    }

    GameResult {
        duration_ns: game_start.elapsed().as_nanos() as u64,
        total_steps,
        main_turns,
        reached_terminal: state.is_terminal(),
    }
}

fn print_slow_moments(slow_moments: &[SlowMoment], threshold_us: u64) {
    println!("\n=== Slowest Moments (>={}μs) ===", threshold_us);
    if slow_moments.is_empty() {
        println!("No slow moments crossed the threshold.");
        return;
    }

    println!(
        "{:<12} {:>8} {:>5} {:>4} {:>14} {:>14} {:>7} {:>7} {:>4}",
        "Operation", "Time(μs)", "Turn", "P", "P0 Stage", "P1 Stage", "Grants", "Hand", "TQ"
    );
    println!("{}", "-".repeat(104));

    for moment in slow_moments.iter().take(TOP_SLOW_MOMENTS) {
        let grants = format!(
            "{}:{}",
            moment.snapshot.p0_granted, moment.snapshot.p1_granted
        );
        let hand = format!("{}:{}", moment.snapshot.p0_hand, moment.snapshot.p1_hand);
        println!(
            "{:<12?} {:>8} {:>5} {:>4} {:>14?} {:>14?} {:>7} {:>7} {:>4}",
            moment.op,
            moment.duration_us,
            moment.snapshot.turn,
            moment.snapshot.player,
            moment.snapshot.p0_stage,
            moment.snapshot.p1_stage,
            grants,
            hand,
            moment.snapshot.trigger_queue,
        );
        println!("  {}", moment.detail);
    }
}

fn print_patterns(patterns: &HashMap<String, PatternStats>) {
    println!("\n=== Frequent Slow-State Fingerprints ===");
    if patterns.is_empty() {
        println!("No repeated slow-state patterns were captured.");
        return;
    }

    let mut rows: Vec<_> = patterns.iter().collect();
    rows.sort_by(|a, b| {
        b.1.max_us
            .cmp(&a.1.max_us)
            .then_with(|| b.1.count.cmp(&a.1.count))
    });

    for (fingerprint, stats) in rows.into_iter().take(TOP_PATTERNS) {
        println!(
            "count={} avg={}μs max={}μs | {}",
            stats.count,
            stats.total_us / stats.count.max(1),
            stats.max_us,
            fingerprint,
        );
        if let Some(sample) = &stats.sample {
            println!(
                "  sample: score={}{} vs {}{}, live={:?} vs {:?}",
                sample.p0_score,
                if sample.p0_success > 0 {
                    format!("/{}S", sample.p0_success)
                } else {
                    String::new()
                },
                sample.p1_score,
                if sample.p1_success > 0 {
                    format!("/{}S", sample.p1_success)
                } else {
                    String::new()
                },
                sample.p0_live,
                sample.p1_live,
            );
        }
    }
}

fn main() {
    let config = Config::from_env();
    println!("=== bench_granular_v2 ===");
    println!(
        "time_budget={}s max_main_turns={} max_total_steps={} slow_threshold={}μs",
        config.bench_secs, config.max_main_turns, config.max_total_steps, config.slow_us,
    );

    let db = load_db();
    println!(
        "loaded db: members={} lives={} energy={} (real rules, silent mode)",
        db.members.len(),
        db.lives.len(),
        db.energy_db.len(),
    );

    let wall_start = Instant::now();
    let mut rng = SmallRng::seed_from_u64(0xBEEF_CAFE_1234_5678);
    let mut timer = BenchmarkTimer::default();
    let mut slow_moments = Vec::new();
    let mut patterns: HashMap<String, PatternStats> = HashMap::new();
    let mut game_results = Vec::new();

    while wall_start.elapsed().as_secs() < config.bench_secs {
        let result = run_one_game(
            &db,
            &mut rng,
            &mut timer,
            &mut slow_moments,
            &mut patterns,
            config,
        );
        game_results.push(result);

        if game_results.len() % 5 == 0 {
            println!(
                "  [{:>5.1}s] games={} slow_moments={}",
                wall_start.elapsed().as_secs_f32(),
                game_results.len(),
                slow_moments.len(),
            );
        }
    }

    if game_results.is_empty() {
        println!("No games completed inside the time budget.");
        return;
    }

    let total_steps: usize = game_results.iter().map(|result| result.total_steps).sum();
    let total_main_turns: usize = game_results.iter().map(|result| result.main_turns).sum();
    let terminal_games = game_results
        .iter()
        .filter(|result| result.reached_terminal)
        .count();

    let mut game_times: Vec<u64> = game_results
        .iter()
        .map(|result| result.duration_ns)
        .collect();
    game_times.sort_unstable();
    let n = game_times.len();
    let avg_game_us = game_times.iter().sum::<u64>() / n as u64 / 1000;
    let min_game_us = game_times[0] / 1000;
    let median_game_us = game_times[n / 2] / 1000;
    let p95_game_us = game_times[(n * 95 / 100).min(n - 1)] / 1000;
    let max_game_us = game_times[n - 1] / 1000;

    println!("\n=== Game Summary ===");
    println!(
        "games={} terminal={} capped={}",
        game_results.len(),
        terminal_games,
        game_results.len() - terminal_games
    );
    println!(
        "steps={} avg_steps_per_game={:.1} main_turns={} avg_main_turns_per_game={:.1}",
        total_steps,
        total_steps as f64 / game_results.len() as f64,
        total_main_turns,
        total_main_turns as f64 / game_results.len() as f64,
    );
    println!(
        "per_game_us: min={} median={} avg={} p95={} max={}",
        min_game_us, median_game_us, avg_game_us, p95_game_us, max_game_us,
    );
    println!(
        "wall_clock={:.2}s throughput={:.2} games/s",
        wall_start.elapsed().as_secs_f64(),
        game_results.len() as f64 / wall_start.elapsed().as_secs_f64().max(0.001),
    );

    timer.print();
    slow_moments.sort_by(|a, b| b.duration_us.cmp(&a.duration_us));
    print_slow_moments(&slow_moments, config.slow_us);
    print_patterns(&patterns);
}
