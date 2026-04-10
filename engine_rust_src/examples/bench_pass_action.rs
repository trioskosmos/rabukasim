use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use smallvec::SmallVec;
use std::mem::size_of;
use std::time::{Duration, Instant};

fn load_db() -> CardDatabase {
    let candidates = [
        "data/cards_compiled.json",
        "../data/cards_compiled.json",
        "../../data/cards_compiled.json",
    ];

    for path in &candidates {
        if !std::path::Path::new(path).exists() {
            continue;
        }
        let json = std::fs::read_to_string(path).expect("Failed to read DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
        db.is_vanilla = false;
        return db;
    }
    panic!("cards_compiled.json not found");
}

fn setup_base_state(db: &CardDatabase) -> GameState {
    let mut base_state = GameState::default();
    base_state.ui.silent = true;
    base_state.ui.headless = true;
    base_state.phase = Phase::Main;
    base_state.current_player = 0;
    base_state.first_player = 0;

    // Use a realistic maximum deck size rather than an artificial oversized heap.
    // Each player deck is at most a few dozen cards in actual gameplay.
    const PER_PLAYER_DECK_CARDS: usize = 72;
    let card_id = db.members.keys().copied().next().unwrap_or(1);
    let mut deck_vec = Vec::with_capacity(PER_PLAYER_DECK_CARDS);
    deck_vec.resize(PER_PLAYER_DECK_CARDS, card_id);
    let deck = SmallVec::from_vec(deck_vec);
    base_state.players[0].deck = deck.clone();
    base_state.players[1].deck = deck;

    base_state
}

fn print_cache_estimate(state: &GameState) {
    let state_stack_bytes = size_of::<GameState>();
    let deck_bytes = state.players[0].deck.capacity() * size_of::<i32>();
    let total_heap_bytes = deck_bytes * 2; // two players
    let total_estimated = state_stack_bytes + total_heap_bytes;
    let l2 = 512 * 1024;
    let l3 = 8 * 1024 * 1024;

    println!("Estimated working set:");
    println!("  GameState struct stack bytes: {}", state_stack_bytes);
    println!("  Player deck heap bytes per player: {}", deck_bytes);
    println!("  Total estimated bytes (stack + both decks): {}", total_estimated);
    println!("  Fits in 512KB L2? {}", total_estimated <= l2);
    println!("  Fits in 8MB L3?  {}", total_estimated <= l3);
    println!("  Note: this is a rough estimate; heap allocations beyond decks are not included.");
}

fn print_type_size_hints() {
    println!("Type sizes:");
    println!("  i32: {}", size_of::<i32>());
    println!("  u32: {}", size_of::<u32>());
    println!("  u16: {}", size_of::<u16>());
    println!("  u8:  {}", size_of::<u8>());
    println!("  u64: {}", size_of::<u64>());
    println!("  usize: {}", size_of::<usize>());
    println!("  (i32, i32, u16): {}", size_of::<(i32, i32, u16)>());
    println!("  SmallVec<[i32; 60]>: {}", size_of::<SmallVec<[i32; 60]>>());
    println!("  SmallVec<[i32; 16]>: {}", size_of::<SmallVec<[i32; 16]>>());
}

struct AutoStepTimes {
    check_win_condition_ns: u128,
    process_trigger_queue_ns: u128,
    do_active_phase_ns: u128,
    do_energy_phase_ns: u128,
    do_draw_phase_ns: u128,
    do_performance_phase_ns: u128,
    do_live_result_ns: u128,
}

impl AutoStepTimes {
    fn new() -> Self {
        Self {
            check_win_condition_ns: 0,
            process_trigger_queue_ns: 0,
            do_active_phase_ns: 0,
            do_energy_phase_ns: 0,
            do_draw_phase_ns: 0,
            do_performance_phase_ns: 0,
            do_live_result_ns: 0,
        }
    }
}

fn measure_auto_step(db: &CardDatabase, state: &mut GameState, times: &mut AutoStepTimes) {
    if state.core.trigger_queue.is_empty()
        && !matches!(state.phase, Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::Energy | Phase::Draw | Phase::Active | Phase::LiveSet)
    {
        return;
    }

    let mut loop_count = 0;
    while loop_count < 40 {
        if state.core.needs_win_check {
            let t = Instant::now();
            state.check_win_condition();
            times.check_win_condition_ns += t.elapsed().as_nanos() as u128;
        }

        if state.phase == Phase::Terminal || state.phase == Phase::Response {
            break;
        }
        if !state.interaction_stack.is_empty() {
            break;
        }

        if !state.core.trigger_queue.is_empty() {
            let t = Instant::now();
            state.process_trigger_queue(db);
            times.process_trigger_queue_ns += t.elapsed().as_nanos() as u128;
            if state.phase == Phase::Response {
                break;
            }
            loop_count += 1;
            continue;
        }

        let old_phase = state.phase;
        match state.phase {
            Phase::Active => {
                let t = Instant::now();
                state.do_active_phase(db);
                times.do_active_phase_ns += t.elapsed().as_nanos() as u128;
            }
            Phase::Energy => {
                let t = Instant::now();
                state.do_energy_phase();
                times.do_energy_phase_ns += t.elapsed().as_nanos() as u128;
            }
            Phase::Draw => {
                let t = Instant::now();
                state.do_draw_phase(db);
                times.do_draw_phase_ns += t.elapsed().as_nanos() as u128;
            }
            Phase::PerformanceP1 | Phase::PerformanceP2 => {
                let t = Instant::now();
                state.do_performance_phase(db);
                times.do_performance_phase_ns += t.elapsed().as_nanos() as u128;
            }
            Phase::LiveResult => {
                if state.live_result_selection_pending {
                    break;
                } else {
                    let t = Instant::now();
                    state.do_live_result(db);
                    times.do_live_result_ns += t.elapsed().as_nanos() as u128;
                }
            }
            _ => {}
        }

        if state.phase == old_phase && state.core.trigger_queue.is_empty() {
            break;
        }
        loop_count += 1;
    }
}

fn main() {
    let db = load_db();
    let base_state = setup_base_state(&db);
    print_cache_estimate(&base_state);
    print_type_size_hints();
    let mut state = GameState::default();

    let time_budget = Duration::from_secs(1);
    let start = Instant::now();
    let mut total_steps = 0usize;
    let mut games = 0usize;
    let mut step_internal_ns = 0u128;
    let mut auto_times = AutoStepTimes::new();

    while start.elapsed() < time_budget {
        state.copy_from(&base_state);
        state.phase = Phase::Main;
        state.current_player = 0;
        state.first_player = 0;

        while state.phase != Phase::Terminal && start.elapsed() < time_budget {
            let t0 = Instant::now();
            state
                .step_internal(&db, ACTION_BASE_PASS)
                .expect("step_internal failed");
            step_internal_ns += t0.elapsed().as_nanos() as u128;

            measure_auto_step(&db, &mut state, &mut auto_times);

            total_steps += 1;
        }

        games += 1;
    }

    let elapsed = start.elapsed();
    println!("Pass-only game benchmark");
    println!("games completed: {}", games);
    println!("total pass steps: {}", total_steps);
    println!("elapsed: {:?}", elapsed);
    if total_steps > 0 {
        let auto_step_ns = auto_times.check_win_condition_ns
            + auto_times.process_trigger_queue_ns
            + auto_times.do_active_phase_ns
            + auto_times.do_energy_phase_ns
            + auto_times.do_draw_phase_ns
            + auto_times.do_performance_phase_ns
            + auto_times.do_live_result_ns;
        let total_step_ns = step_internal_ns + auto_step_ns;
        println!("avg: {:.2} ns per pass", elapsed.as_nanos() as f64 / total_steps as f64);
        println!("throughput: {:.2} million passes/sec",
            total_steps as f64 / elapsed.as_secs_f64() / 1_000_000.0);
        println!("avg step_internal: {:.2} ns", step_internal_ns as f64 / total_steps as f64);
        println!("avg auto_step: {:.2} ns", auto_step_ns as f64 / total_steps as f64);
        println!("  avg check_win_condition: {:.2} ns", auto_times.check_win_condition_ns as f64 / total_steps as f64);
        println!("  avg process_trigger_queue: {:.2} ns", auto_times.process_trigger_queue_ns as f64 / total_steps as f64);
        println!("  avg do_active_phase: {:.2} ns", auto_times.do_active_phase_ns as f64 / total_steps as f64);
        println!("  avg do_energy_phase: {:.2} ns", auto_times.do_energy_phase_ns as f64 / total_steps as f64);
        println!("  avg do_draw_phase: {:.2} ns", auto_times.do_draw_phase_ns as f64 / total_steps as f64);
        println!("  avg do_performance_phase: {:.2} ns", auto_times.do_performance_phase_ns as f64 / total_steps as f64);
        println!("  avg do_live_result: {:.2} ns", auto_times.do_live_result_ns as f64 / total_steps as f64);
        println!("avg breakdown: step_internal {:.1}%, auto_step {:.1}%",
            step_internal_ns as f64 / total_step_ns as f64 * 100.0,
            auto_step_ns as f64 / total_step_ns as f64 * 100.0);
    }
}
