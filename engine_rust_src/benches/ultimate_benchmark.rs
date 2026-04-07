use engine_rust::core::enums::Phase;
use engine_rust::core::logic::action_factory::DecodedAction;
use engine_rust::core::logic::{CardDatabase, GameState, PendingInteraction};
use rand::rngs::SmallRng;
use rand::seq::{IndexedRandom, SliceRandom};
use rand::{Rng, SeedableRng};
use std::collections::hash_map::DefaultHasher;
use std::collections::HashMap;
use std::fs;
use std::hash::{Hash, Hasher};
use std::time::Instant;

const DEFAULT_BENCH_SECS: u64 = 10;
const DEFAULT_WARMUP_GAMES: usize = 4;
const DEFAULT_MAX_STEPS: usize = 6000;
const DEFAULT_SLOW_US: u64 = 2_000;
const DEFAULT_REPEAT_LIMIT: u32 = 24;
const DEFAULT_SAME_STATE_LIMIT: u32 = 10;
const TOP_SLOW_EVENTS: usize = 20;
const TOP_STEP_ERRORS: usize = 20;
const TOP_STALLS: usize = 12;
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum TimedOp {
    LegalActionsMain,
    LegalActionsLiveSet,
    LegalActionsResponse,
    LegalActionsOther,
    StepInternalMain,
    StepInternalLiveSet,
    StepInternalResponse,
    StepInternalLiveResult,
    StepInternalOther,
    AutoStepAfterMain,
    AutoStepAfterLiveSet,
    AutoStepAfterResponse,
    AutoStepAfterLiveResult,
    AutoStepAfterOther,
    SyncStatsAfterStep,
    StepResidualMain,
    StepResidualLiveSet,
    StepResidualResponse,
    StepResidualLiveResult,
    StepResidualOther,
    StepMain,
    StepLiveSet,
    StepResponse,
    StepLiveResult,
    StepActive,
    StepDraw,
    StepRps,
    StepTurnChoice,
    StepEnergy,
    StepPerformance,
    StepTerminal,
    StepOther,
    AutoStepFallbackMain,
    AutoStepFallbackLiveSet,
    AutoStepFallbackResponse,
    AutoStepFallbackOther,
}

#[derive(Debug, Default, Clone)]
struct OpStats {
    calls: u64,
    total_ns: u64,
    total_sq_ns: f64,
    max_ns: u64,
}

#[derive(Debug, Clone)]
struct Snapshot {
    phase: Phase,
    turn: u16,
    current_player: u8,
    p0_state_hash: u64,
    p1_state_hash: u64,
    trigger_queue_hash: u64,
    interaction_stack_hash: u64,
    p0_stage: [i32; 3],
    p1_stage: [i32; 3],
    p0_live: [i32; 3],
    p1_live: [i32; 3],
    p0_hand: usize,
    p1_hand: usize,
    p0_deck: usize,
    p1_deck: usize,
    p0_discard: usize,
    p1_discard: usize,
    p0_energy: usize,
    p1_energy: usize,
    p0_score: u32,
    p1_score: u32,
    trigger_queue: usize,
    interaction_stack: usize,
    pending_card_id: i32,
    pending_ability_index: i16,
    pending_effect_opcode: i32,
    pending_choice_type: i32,
}

#[derive(Debug, Clone)]
struct SlowEvent {
    op: TimedOp,
    phase: Phase,
    end_phase: Phase,
    duration_us: u64,
    action: Option<i32>,
    legal_count: usize,
    snapshot: Snapshot,
}

#[derive(Debug, Clone)]
struct StateCostRecord {
    count: u64,
    total_ns: u64,
    max_ns: u64,
    sample: Snapshot,
}

#[derive(Debug, Clone)]
struct StepErrorRecord {
    count: u64,
    phase: Phase,
    action: i32,
    message: String,
    snapshot: Snapshot,
}

#[derive(Debug, Default, Clone)]
struct StallRecord {
    count: u64,
    max_repeat: u32,
    sample: Option<Snapshot>,
}

#[derive(Debug, Default)]
struct Telemetry {
    by_op: HashMap<TimedOp, OpStats>,
    state_costs: HashMap<(TimedOp, u64), StateCostRecord>,
    slow_events: Vec<SlowEvent>,
    stalls: HashMap<u64, StallRecord>,
    benign_pass_loops: u64,
    real_no_progress_events: u64,
    step_errors: u64,
    step_error_records: HashMap<String, StepErrorRecord>,
}

fn stable_hash<T: Hash>(value: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

fn interaction_stack_hash(interactions: &[PendingInteraction]) -> u64 {
    let mut hasher = DefaultHasher::new();
    interactions.len().hash(&mut hasher);
    for interaction in interactions {
        interaction.ctx.hash(&mut hasher);
        interaction.card_id.hash(&mut hasher);
        interaction.ability_card_id.hash(&mut hasher);
        interaction.ability_index.hash(&mut hasher);
        interaction.effect_opcode.hash(&mut hasher);
        interaction.target_slot.hash(&mut hasher);
        (interaction.choice_type as i32).hash(&mut hasher);
        interaction.filter_attr.hash(&mut hasher);
        interaction.choice_text.hash(&mut hasher);
        interaction.v_remaining.hash(&mut hasher);
        interaction.original_phase.hash(&mut hasher);
        interaction.original_current_player.hash(&mut hasher);
        interaction.actions.hash(&mut hasher);
        interaction.options.len().hash(&mut hasher);
        interaction.execution_id.hash(&mut hasher);
    }
    hasher.finish()
}

impl Snapshot {
    fn capture(state: &GameState) -> Self {
        let pending = state.interaction_stack.last();
        Self {
            phase: state.phase,
            turn: state.turn,
            current_player: state.current_player,
            p0_state_hash: stable_hash(&state.players[0]),
            p1_state_hash: stable_hash(&state.players[1]),
            trigger_queue_hash: stable_hash(&state.core.trigger_queue),
            interaction_stack_hash: interaction_stack_hash(&state.interaction_stack),
            p0_stage: state.players[0].stage,
            p1_stage: state.players[1].stage,
            p0_live: state.players[0].live_zone,
            p1_live: state.players[1].live_zone,
            p0_hand: state.players[0].hand.len(),
            p1_hand: state.players[1].hand.len(),
            p0_deck: state.players[0].deck.len(),
            p1_deck: state.players[1].deck.len(),
            p0_discard: state.players[0].discard.len(),
            p1_discard: state.players[1].discard.len(),
            p0_energy: state.players[0].energy_zone.len(),
            p1_energy: state.players[1].energy_zone.len(),
            p0_score: state.players[0].score,
            p1_score: state.players[1].score,
            trigger_queue: state.core.trigger_queue.len(),
            interaction_stack: state.interaction_stack.len(),
            pending_card_id: pending.map(|pi| pi.card_id).unwrap_or(-1),
            pending_ability_index: pending.map(|pi| pi.ability_index).unwrap_or(-1),
            pending_effect_opcode: pending.map(|pi| pi.effect_opcode).unwrap_or(-1),
            pending_choice_type: pending.map(|pi| pi.choice_type as i32).unwrap_or(-1),
        }
    }

    fn fingerprint(&self) -> u64 {
        let mut hasher = DefaultHasher::new();
        self.phase.hash(&mut hasher);
        self.turn.hash(&mut hasher);
        self.current_player.hash(&mut hasher);
        self.p0_state_hash.hash(&mut hasher);
        self.p1_state_hash.hash(&mut hasher);
        self.trigger_queue_hash.hash(&mut hasher);
        self.interaction_stack_hash.hash(&mut hasher);
        self.p0_stage.hash(&mut hasher);
        self.p1_stage.hash(&mut hasher);
        self.p0_live.hash(&mut hasher);
        self.p1_live.hash(&mut hasher);
        self.p0_hand.hash(&mut hasher);
        self.p1_hand.hash(&mut hasher);
        self.p0_deck.hash(&mut hasher);
        self.p1_deck.hash(&mut hasher);
        self.p0_discard.hash(&mut hasher);
        self.p1_discard.hash(&mut hasher);
        self.p0_energy.hash(&mut hasher);
        self.p1_energy.hash(&mut hasher);
        self.p0_score.hash(&mut hasher);
        self.p1_score.hash(&mut hasher);
        self.trigger_queue.hash(&mut hasher);
        self.interaction_stack.hash(&mut hasher);
        self.pending_card_id.hash(&mut hasher);
        self.pending_ability_index.hash(&mut hasher);
        self.pending_effect_opcode.hash(&mut hasher);
        self.pending_choice_type.hash(&mut hasher);
        hasher.finish()
    }

    fn short_label(&self) -> String {
        format!(
            "phase={:?} turn={} p={} hand={}:{} deck={}:{} disc={}:{} energy={}:{} tq={} stack={} pending={}/{}/{}/{} state={:016x}/{:016x}",
            self.phase,
            self.turn,
            self.current_player,
            self.p0_hand,
            self.p1_hand,
            self.p0_deck,
            self.p1_deck,
            self.p0_discard,
            self.p1_discard,
            self.p0_energy,
            self.p1_energy,
            self.trigger_queue,
            self.interaction_stack,
            self.pending_card_id,
            self.pending_ability_index,
            self.pending_effect_opcode,
            self.pending_choice_type,
            self.p0_state_hash,
            self.p1_state_hash,
        )
    }

    fn detailed_zones(&self, db: &CardDatabase) -> String {
        format!(
            "stage0={} | stage1={} | live0={} | live1={}",
            format_card_list(db, &self.p0_stage),
            format_card_list(db, &self.p1_stage),
            format_card_list(db, &self.p0_live),
            format_card_list(db, &self.p1_live),
        )
    }
}

fn card_label(db: &CardDatabase, cid: i32) -> String {
    if cid < 0 {
        return "-".to_string();
    }

    if let Some(card) = db.get_member(cid) {
        return format!("{}:{}", cid, card.name);
    }

    if let Some(card) = db.get_live(cid) {
        return format!("{}:{}", cid, card.name);
    }

    cid.to_string()
}

fn format_card_list<const N: usize>(db: &CardDatabase, cards: &[i32; N]) -> String {
    let labels: Vec<_> = cards.iter().map(|&cid| card_label(db, cid)).collect();
    format!("[{}]", labels.join(", "))
}

fn describe_action(snapshot: &Snapshot, action: Option<i32>, db: &CardDatabase) -> String {
    let Some(action) = action else {
        return "action=<none>".to_string();
    };

    let decoded = DecodedAction::decode(action);
    let actor = match decoded {
        DecodedAction::ActivateMember { slot_idx, .. } => {
            let cid = if snapshot.current_player == 0 {
                snapshot.p0_stage.get(slot_idx).copied().unwrap_or(-1)
            } else {
                snapshot.p1_stage.get(slot_idx).copied().unwrap_or(-1)
            };
            format!(" source={}", card_label(db, cid))
        }
        DecodedAction::SelectStageSlot { slot_idx } => {
            format!(" slot={}", slot_idx)
        }
        DecodedAction::SelectMode { mode_idx } => {
            format!(" mode={}", mode_idx)
        }
        _ => String::new(),
    };

    format!("action={:?}{}", decoded, actor)
}

impl Telemetry {
    fn record_timing(
        &mut self,
        op: TimedOp,
        phase: Phase,
        end_phase: Phase,
        elapsed_ns: u64,
        action: Option<i32>,
        legal_count: usize,
        snapshot: &Snapshot,
        slow_us: u64,
    ) {
        let entry = self.by_op.entry(op).or_default();
        entry.calls += 1;
        entry.total_ns += elapsed_ns;
        entry.total_sq_ns += (elapsed_ns as f64) * (elapsed_ns as f64);
        entry.max_ns = entry.max_ns.max(elapsed_ns);

        let state_key = (op, snapshot.fingerprint());
        let state_entry = self.state_costs.entry(state_key).or_insert_with(|| StateCostRecord {
            count: 0,
            total_ns: 0,
            max_ns: 0,
            sample: snapshot.clone(),
        });
        state_entry.count += 1;
        state_entry.total_ns += elapsed_ns;
        state_entry.max_ns = state_entry.max_ns.max(elapsed_ns);

        let elapsed_us = elapsed_ns / 1000;
        if elapsed_us >= slow_us || self.slow_events.len() < TOP_SLOW_EVENTS {
            self.slow_events.push(SlowEvent {
                op,
                phase,
                end_phase,
                duration_us: elapsed_us,
                action,
                legal_count,
                snapshot: snapshot.clone(),
            });
            self.slow_events
                .sort_by(|a, b| b.duration_us.cmp(&a.duration_us));
            self.slow_events.truncate(TOP_SLOW_EVENTS);
        } else if let Some(current_min) = self.slow_events.last().map(|event| event.duration_us) {
            if elapsed_us > current_min {
                self.slow_events.push(SlowEvent {
                    op,
                    phase,
                    end_phase,
                    duration_us: elapsed_us,
                    action,
                    legal_count,
                    snapshot: snapshot.clone(),
                });
                self.slow_events
                    .sort_by(|a, b| b.duration_us.cmp(&a.duration_us));
                self.slow_events.truncate(TOP_SLOW_EVENTS);
            }
        }
    }

    fn record_stall(&mut self, fingerprint: u64, repeat_count: u32, snapshot: &Snapshot) {
        let entry = self.stalls.entry(fingerprint).or_default();
        entry.count += 1;
        entry.max_repeat = entry.max_repeat.max(repeat_count);
        if entry.sample.is_none() {
            entry.sample = Some(snapshot.clone());
        }
    }

    fn record_step_error(
        &mut self,
        phase: Phase,
        action: i32,
        message: &str,
        snapshot: &Snapshot,
    ) {
        self.step_errors += 1;
        let key = format!("{:?}|{}|{}", phase, action, message);
        let entry = self.step_error_records.entry(key).or_insert_with(|| StepErrorRecord {
            count: 0,
            phase,
            action,
            message: message.to_string(),
            snapshot: snapshot.clone(),
        });
        entry.count += 1;
    }
}

#[derive(Debug, Clone, Copy)]
struct Config {
    bench_secs: u64,
    warmup_games: usize,
    max_steps: usize,
    slow_us: u64,
    repeat_limit: u32,
    same_state_limit: u32,
    seed: u64,
}

impl Config {
    fn from_env() -> Self {
        Self {
            bench_secs: env_u64("BENCH_SECS", DEFAULT_BENCH_SECS),
            warmup_games: env_usize("BENCH_WARMUP_GAMES", DEFAULT_WARMUP_GAMES),
            max_steps: env_usize("BENCH_MAX_STEPS", DEFAULT_MAX_STEPS),
            slow_us: env_u64("BENCH_SLOW_US", DEFAULT_SLOW_US),
            repeat_limit: env_u32("BENCH_REPEAT_LIMIT", DEFAULT_REPEAT_LIMIT),
            same_state_limit: env_u32("BENCH_SAME_STATE_LIMIT", DEFAULT_SAME_STATE_LIMIT),
            seed: env_u64("BENCH_SEED", 0xD15E_A5E5_CAFE_BABE),
        }
    }
}

#[derive(Debug, Default, Clone)]
struct GameOutcome {
    duration_ns: u64,
    steps: usize,
    terminal: bool,
    stalled: bool,
    capped: bool,
}

fn env_u64(key: &str, default: u64) -> u64 {
    std::env::var(key)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn env_u32(key: &str, default: u32) -> u32 {
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

fn timed_op_for_legal(phase: Phase) -> TimedOp {
    match phase {
        Phase::Main => TimedOp::LegalActionsMain,
        Phase::LiveSet => TimedOp::LegalActionsLiveSet,
        Phase::Response => TimedOp::LegalActionsResponse,
        _ => TimedOp::LegalActionsOther,
    }
}

fn timed_op_for_step(phase: Phase) -> TimedOp {
    match phase {
        Phase::Main => TimedOp::StepMain,
        Phase::LiveSet => TimedOp::StepLiveSet,
        Phase::Response => TimedOp::StepResponse,
        Phase::LiveResult => TimedOp::StepLiveResult,
        Phase::Active => TimedOp::StepActive,
        Phase::Draw => TimedOp::StepDraw,
        Phase::Rps => TimedOp::StepRps,
        Phase::TurnChoice => TimedOp::StepTurnChoice,
        Phase::Energy => TimedOp::StepEnergy,
        Phase::PerformanceP1 | Phase::PerformanceP2 => TimedOp::StepPerformance,
        Phase::Terminal => TimedOp::StepTerminal,
        _ => TimedOp::StepOther,
    }
}

fn timed_op_for_step_internal(phase: Phase) -> TimedOp {
    match phase {
        Phase::Main => TimedOp::StepInternalMain,
        Phase::LiveSet => TimedOp::StepInternalLiveSet,
        Phase::Response => TimedOp::StepInternalResponse,
        Phase::LiveResult => TimedOp::StepInternalLiveResult,
        _ => TimedOp::StepInternalOther,
    }
}

fn timed_op_for_post_autostep(phase: Phase) -> TimedOp {
    match phase {
        Phase::Main => TimedOp::AutoStepAfterMain,
        Phase::LiveSet => TimedOp::AutoStepAfterLiveSet,
        Phase::Response => TimedOp::AutoStepAfterResponse,
        Phase::LiveResult => TimedOp::AutoStepAfterLiveResult,
        _ => TimedOp::AutoStepAfterOther,
    }
}

fn timed_op_for_step_residual(phase: Phase) -> TimedOp {
    match phase {
        Phase::Main => TimedOp::StepResidualMain,
        Phase::LiveSet => TimedOp::StepResidualLiveSet,
        Phase::Response => TimedOp::StepResidualResponse,
        Phase::LiveResult => TimedOp::StepResidualLiveResult,
        _ => TimedOp::StepResidualOther,
    }
}

fn timed_op_for_autostep(phase: Phase) -> TimedOp {
    match phase {
        Phase::Main => TimedOp::AutoStepFallbackMain,
        Phase::LiveSet => TimedOp::AutoStepFallbackLiveSet,
        Phase::Response => TimedOp::AutoStepFallbackResponse,
        _ => TimedOp::AutoStepFallbackOther,
    }
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
        if let Some(&card_id) = members.first() {
            members.push(card_id);
        } else {
            break;
        }
    }
    while lives.len() < 12 {
        if let Some(&card_id) = lives.first() {
            lives.push(card_id);
        } else {
            break;
        }
    }
    while energy.len() < 12 {
        if let Some(&card_id) = energy.first() {
            energy.push(card_id);
        } else {
            break;
        }
    }

    (members, lives, energy)
}

fn choose_random_action(state: &GameState, db: &CardDatabase, telemetry: &mut Telemetry, config: Config) -> Vec<i32> {
    let snapshot = Snapshot::capture(state);
    let t0 = Instant::now();
    let legal = state.get_legal_action_ids(db);
    let elapsed_ns = t0.elapsed().as_nanos() as u64;
    telemetry.record_timing(
        timed_op_for_legal(state.phase),
        state.phase,
        state.phase,
        elapsed_ns,
        None,
        legal.len(),
        &snapshot,
        config.slow_us,
    );
    legal
}

fn run_one_game(db: &CardDatabase, rng: &mut SmallRng, telemetry: &mut Telemetry, config: Config) -> GameOutcome {
    let game_start = Instant::now();
    let (p0_members, p0_lives, p0_energy) = build_random_deck(db, rng);
    let (p1_members, p1_lives, p1_energy) = build_random_deck(db, rng);

    let mut state = GameState::default();
    state.ui.silent = true;
    state.ui.headless = true;
    state.debug.debug_mode = false;
    state.initialize_game_with_seed(
        p0_members,
        p1_members,
        p0_energy,
        p1_energy,
        p0_lives,
        p1_lives,
        Some(rng.random()),
    );

    let mut steps = 0usize;
    let mut seen: HashMap<u64, u32> = HashMap::new();
    let mut previous_key = Snapshot::capture(&state).fingerprint();
    let mut same_state_count = 0u32;

    while !state.is_terminal() && steps < config.max_steps {
        let legal = choose_random_action(&state, db, telemetry, config);
        let before = Snapshot::capture(&state);
        let before_key = previous_key;
        let mut chosen_action = None;
        let mut step_error = false;

        if legal.is_empty() {
            let t0 = Instant::now();
            state.auto_step(db);
            let elapsed_ns = t0.elapsed().as_nanos() as u64;
            telemetry.record_timing(
                timed_op_for_autostep(before.phase),
                before.phase,
                state.phase,
                elapsed_ns,
                None,
                0,
                &before,
                config.slow_us,
            );
        } else {
            let action = *legal.choose(rng).expect("non-empty legal list should have a random action");
            chosen_action = Some(action);
            let total_start = Instant::now();
            let internal_start = Instant::now();
            let mut auto_elapsed_ns = 0u64;
            let mut sync_elapsed_ns = 0u64;
            let internal_result = state.step_internal(db, action);
            let internal_elapsed_ns = internal_start.elapsed().as_nanos() as u64;
            let after_internal_phase = state.phase;
            telemetry.record_timing(
                timed_op_for_step_internal(before.phase),
                before.phase,
                after_internal_phase,
                internal_elapsed_ns,
                Some(action),
                legal.len(),
                &before,
                config.slow_us,
            );

            if let Err(err) = internal_result {
                telemetry.record_step_error(before.phase, action, &err, &before);
                step_error = true;
            } else {
                let auto_start = Instant::now();
                state.auto_step(db);
                auto_elapsed_ns = auto_start.elapsed().as_nanos() as u64;
                let after_auto_phase = state.phase;
                telemetry.record_timing(
                    timed_op_for_post_autostep(before.phase),
                    before.phase,
                    after_auto_phase,
                    auto_elapsed_ns,
                    Some(action),
                    legal.len(),
                    &before,
                    config.slow_us,
                );

                if !matches!(state.phase, Phase::LiveSet) {
                    let sync_start = Instant::now();
                    state.sync_all_stats(db);
                    sync_elapsed_ns = sync_start.elapsed().as_nanos() as u64;
                    telemetry.record_timing(
                        TimedOp::SyncStatsAfterStep,
                        before.phase,
                        state.phase,
                        sync_elapsed_ns,
                        Some(action),
                        legal.len(),
                        &before,
                        config.slow_us,
                    );
                }
            }
            let elapsed_ns = total_start.elapsed().as_nanos() as u64;
            let explained_ns = internal_elapsed_ns
                .saturating_add(auto_elapsed_ns)
                .saturating_add(sync_elapsed_ns);
            let residual_ns = elapsed_ns.saturating_sub(explained_ns);
            if residual_ns > 0 {
                telemetry.record_timing(
                    timed_op_for_step_residual(before.phase),
                    before.phase,
                    state.phase,
                    residual_ns,
                    Some(action),
                    legal.len(),
                    &before,
                    config.slow_us,
                );
            }
            telemetry.record_timing(
                timed_op_for_step(before.phase),
                before.phase,
                state.phase,
                elapsed_ns,
                Some(action),
                legal.len(),
                &before,
                config.slow_us,
            );
        }

        steps += 1;
        let after = Snapshot::capture(&state);
        let key = after.fingerprint();
        let benign_pass_loop = matches!(chosen_action, Some(0)) && !step_error && key == before_key;

        if benign_pass_loop {
            telemetry.benign_pass_loops += 1;
            continue;
        }

        if step_error && key == before_key {
            telemetry.real_no_progress_events += 1;
        }

        let visit_count = seen.entry(key).or_insert(0);
        *visit_count += 1;

        if key == previous_key {
            same_state_count += 1;
        } else {
            same_state_count = 0;
            previous_key = key;
        }

        if *visit_count >= config.repeat_limit || same_state_count >= config.same_state_limit {
            telemetry.record_stall(key, (*visit_count).max(same_state_count), &after);
            return GameOutcome {
                duration_ns: game_start.elapsed().as_nanos() as u64,
                steps,
                terminal: false,
                stalled: true,
                capped: false,
            };
        }
    }

    GameOutcome {
        duration_ns: game_start.elapsed().as_nanos() as u64,
        steps,
        terminal: state.is_terminal(),
        stalled: false,
        capped: !state.is_terminal(),
    }
}

fn print_op_stats(telemetry: &Telemetry) {
    println!("\n=== Timing By Operation ===");
    println!(
        "{:<22} {:>10} {:>12} {:>12} {:>12} {:>12}",
        "Operation",
        "Calls",
        "Total_ms",
        "Avg_us",
        "StdDev_us",
        "Max_us"
    );
    println!("{}", "-".repeat(88));

    let mut rows: Vec<_> = telemetry.by_op.iter().collect();
    rows.sort_by(|a, b| b.1.total_ns.cmp(&a.1.total_ns));
    for (op, stats) in rows {
        let avg_us = if stats.calls == 0 {
            0.0
        } else {
            stats.total_ns as f64 / stats.calls as f64 / 1000.0
        };
        let stddev_us = if stats.calls <= 1 {
            0.0
        } else {
            let mean_ns = stats.total_ns as f64 / stats.calls as f64;
            let variance_ns = (stats.total_sq_ns / stats.calls as f64) - (mean_ns * mean_ns);
            variance_ns.max(0.0).sqrt() / 1000.0
        };
        println!(
            "{:<22?} {:>10} {:>12.2} {:>12.1} {:>12.1} {:>12.1}",
            op,
            stats.calls,
            stats.total_ns as f64 / 1_000_000.0,
            avg_us,
            stddev_us,
            stats.max_ns as f64 / 1000.0,
        );
    }
}

fn print_state_costs(telemetry: &Telemetry, db: &CardDatabase) {
    println!("\n=== Slow Board States ===");
    if telemetry.state_costs.is_empty() {
        println!("No board-state timing samples were recorded.");
        return;
    }

    let mut rows: Vec<_> = telemetry.state_costs.iter().collect();
    rows.sort_by(|a, b| {
        b.1.total_ns
            .cmp(&a.1.total_ns)
            .then_with(|| b.1.max_ns.cmp(&a.1.max_ns))
    });

    for ((op, fingerprint), record) in rows.into_iter().take(TOP_SLOW_EVENTS) {
        let avg_us = record.total_ns as f64 / record.count as f64 / 1000.0;
        println!(
            "op={:<18?} fingerprint={:016x} calls={} total_ms={:.2} avg_us={:.1} max_us={:.1} {}",
            op,
            fingerprint,
            record.count,
            record.total_ns as f64 / 1_000_000.0,
            avg_us,
            record.max_ns as f64 / 1000.0,
            record.sample.short_label(),
        );
        println!("  zones={}", record.sample.detailed_zones(db));
    }
}

fn print_top_games(outcomes: &[GameOutcome]) {
    println!("\n=== Longest Games By Steps ===");
    if outcomes.is_empty() {
        println!("No games were recorded.");
        return;
    }

    let mut rows: Vec<(usize, &GameOutcome)> = outcomes.iter().enumerate().collect();
    rows.sort_by(|a, b| {
        b.1.steps
            .cmp(&a.1.steps)
            .then_with(|| b.1.duration_ns.cmp(&a.1.duration_ns))
    });

    for (game_id, outcome) in rows.into_iter().take(TOP_STALLS) {
        println!(
            "game={} steps={} duration_ms={:.2} terminal={} stalled={} capped={}",
            game_id,
            outcome.steps,
            outcome.duration_ns as f64 / 1_000_000.0,
            outcome.terminal,
            outcome.stalled,
            outcome.capped,
        );
    }
}

fn print_slow_events(telemetry: &mut Telemetry, slow_us: u64, db: &CardDatabase) {
    telemetry
        .slow_events
        .sort_by(|a, b| b.duration_us.cmp(&a.duration_us));

    println!("\n=== Slow Events (>={}us) ===", slow_us);
    if telemetry.slow_events.is_empty() {
        println!("No slow events crossed the threshold.");
        return;
    }

    for event in telemetry.slow_events.iter().take(TOP_SLOW_EVENTS) {
        println!(
            "{:>8}us {:<22?} phase={:?}->{:?} action={:?} legal={} {}",
            event.duration_us,
            event.op,
            event.phase,
            event.end_phase,
            event.action,
            event.legal_count,
            event.snapshot.short_label(),
        );
        println!(
            "  {} | zones={}",
            describe_action(&event.snapshot, event.action, db),
            event.snapshot.detailed_zones(db),
        );
    }
}

fn print_step_errors(telemetry: &Telemetry) {
    println!("\n=== Step Errors ===");
    if telemetry.step_error_records.is_empty() {
        println!("No step() errors were recorded in this run.");
        return;
    }

    let mut rows: Vec<_> = telemetry.step_error_records.values().collect();
    rows.sort_by(|a, b| b.count.cmp(&a.count));

    for record in rows.into_iter().take(TOP_STEP_ERRORS) {
        println!(
            "count={} phase={:?} action={} error={} {}",
            record.count,
            record.phase,
            record.action,
            record.message,
            record.snapshot.short_label(),
        );
    }
}

fn print_stalls(telemetry: &Telemetry) {
    println!("\n=== Repeated-State Stall Fingerprints ===");
    if telemetry.stalls.is_empty() {
        println!("No repeated-state stalls were detected in this run.");
        return;
    }

    let mut rows: Vec<_> = telemetry.stalls.iter().collect();
    rows.sort_by(|a, b| {
        b.1.max_repeat
            .cmp(&a.1.max_repeat)
            .then_with(|| b.1.count.cmp(&a.1.count))
    });

    for (fingerprint, record) in rows.into_iter().take(TOP_STALLS) {
        let label = record
            .sample
            .as_ref()
            .map(|snapshot| snapshot.short_label())
            .unwrap_or_else(|| "<missing sample>".to_string());
        println!(
            "fingerprint={:016x} hits={} max_repeat={} {}",
            fingerprint,
            record.count,
            record.max_repeat,
            label,
        );
    }
}

fn main() {
    let config = Config::from_env();
    println!("=== LOVECA Ultimate Benchmark ===");
    println!(
        "abilities=on random_legal_actions=yes silent=yes headless=yes bench_secs={} max_steps={} slow_us={} repeat_limit={} same_state_limit={} seed={}",
        config.bench_secs,
        config.max_steps,
        config.slow_us,
        config.repeat_limit,
        config.same_state_limit,
        config.seed,
    );
    println!("timings: game_summary=ms op_and_state_tables=us raw_storage=ns");

    let db = load_db();
    println!(
        "loaded compiled db: members={} lives={} energy={}",
        db.members.len(),
        db.lives.len(),
        db.energy_db.len(),
    );

    let mut rng = SmallRng::seed_from_u64(config.seed);
    let mut telemetry = Telemetry::default();

    if config.warmup_games > 0 {
        println!("warming up {} games...", config.warmup_games);
        for _ in 0..config.warmup_games {
            let _ = run_one_game(&db, &mut rng, &mut telemetry, config);
        }
        telemetry = Telemetry::default();
    }

    let wall_start = Instant::now();
    let mut outcomes = Vec::new();

    while wall_start.elapsed().as_secs() < config.bench_secs {
        outcomes.push(run_one_game(&db, &mut rng, &mut telemetry, config));
        if outcomes.len() % 10 == 0 {
            let stalled = outcomes.iter().filter(|outcome| outcome.stalled).count();
            println!(
                "  [{:>5.1}s] games={} stalled={}",
                wall_start.elapsed().as_secs_f32(),
                outcomes.len(),
                stalled,
            );
        }
    }

    if outcomes.is_empty() {
        println!("no games completed inside the benchmark window");
        return;
    }

    let total_steps: usize = outcomes.iter().map(|outcome| outcome.steps).sum();
    let terminal_games = outcomes.iter().filter(|outcome| outcome.terminal).count();
    let stalled_games = outcomes.iter().filter(|outcome| outcome.stalled).count();
    let capped_games = outcomes.iter().filter(|outcome| outcome.capped).count();

    let mut durations: Vec<u64> = outcomes.iter().map(|outcome| outcome.duration_ns).collect();
    durations.sort_unstable();
    let len = durations.len();
    let avg_game_ms = durations.iter().sum::<u64>() / len as u64 / 1_000_000;
    let median_game_ms = durations[len / 2] / 1_000_000;
    let p95_game_ms = durations[(len * 95 / 100).min(len - 1)] / 1_000_000;
    let max_game_ms = durations[len - 1] / 1_000_000;

    println!("\n=== Game Summary ===");
    println!(
        "games={} terminal={} stalled={} capped={}",
        outcomes.len(),
        terminal_games,
        stalled_games,
        capped_games,
    );
    println!(
        "steps={} avg_steps_per_game={:.1}",
        total_steps,
        total_steps as f64 / outcomes.len() as f64,
    );
    println!(
        "per_game_ms median={} avg={} p95={} max={}",
        median_game_ms,
        avg_game_ms,
        p95_game_ms,
        max_game_ms,
    );
    println!(
        "throughput {:.2} games/s {:.2} actions/s",
        outcomes.len() as f64 / wall_start.elapsed().as_secs_f64().max(0.001),
        total_steps as f64 / wall_start.elapsed().as_secs_f64().max(0.001),
    );
    println!("benign_pass_loops={}", telemetry.benign_pass_loops);
    println!("real_no_progress_events={}", telemetry.real_no_progress_events);
    println!("step_errors={}", telemetry.step_errors);

    print_top_games(&outcomes);
    print_op_stats(&telemetry);
    print_state_costs(&telemetry, &db);
    print_slow_events(&mut telemetry, config.slow_us, &db);
    print_step_errors(&telemetry);
    print_stalls(&telemetry);
}
