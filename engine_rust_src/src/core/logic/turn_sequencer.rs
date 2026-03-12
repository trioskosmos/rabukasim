use std::collections::HashMap;
use std::fs;
use std::hash::{Hash, Hasher};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, RwLock};
use std::thread;
use std::time::Duration;
use std::time::Instant;

use once_cell::sync::Lazy;
use rand::seq::IndexedRandom;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

use crate::core::enums::Phase;
use crate::core::logic::constants::*;
use crate::core::logic::{CardDatabase, GameState};
use crate::core::{ACTION_BASE_HAND, ACTION_BASE_LIVESET, ACTION_BASE_PASS};

// MCTS Constants
const MCTS_EXPLORATION_CONST: f32 = 1.414; // sqrt(2) for UCB1

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct WeightsConfig {
    pub board_presence: f32,
    pub blades: f32,
    pub hearts: f32,
    pub saturation_bonus: f32,
    pub energy_penalty: f32,
    pub live_ev_multiplier: f32,
    pub uncertainty_penalty_pow: f32,
    pub liveset_placement_bonus: f32,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct SearchConfig {
    pub max_dfs_depth: usize,
    pub mc_trials: usize,
    pub beam_width: usize,
    pub use_memoization: bool,
    pub beam_search: bool,
    pub use_alpha_beta: bool,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct SequencerConfig {
    pub weights: WeightsConfig,
    pub search: SearchConfig,
}

pub static CONFIG: Lazy<RwLock<SequencerConfig>> = Lazy::new(|| {
    let path = "sequencer_config.json";
    let base = if let Ok(content) = fs::read_to_string(path) {
        serde_json::from_str(&content).unwrap_or_default()
    } else {
        SequencerConfig::default()
    };
    RwLock::new(base)
});

struct SearchTelemetry {
    enabled: bool,
    done: AtomicBool,
    aborted: AtomicBool,
    node_count: AtomicUsize,
    root_done: AtomicUsize,
    root_total: AtomicUsize,
    best_seq_len: AtomicUsize,
    best_val_bits: AtomicU32Compat,
}

struct AtomicU32Compat(std::sync::atomic::AtomicU32);

impl AtomicU32Compat {
    fn new(value: u32) -> Self {
        Self(std::sync::atomic::AtomicU32::new(value))
    }

    fn load(&self, ordering: Ordering) -> u32 {
        self.0.load(ordering)
    }

    fn store(&self, value: u32, ordering: Ordering) {
        self.0.store(value, ordering)
    }
}

impl SearchTelemetry {
    fn disabled() -> Self {
        Self {
            enabled: false,
            done: AtomicBool::new(false),
            aborted: AtomicBool::new(false),
            node_count: AtomicUsize::new(0),
            root_done: AtomicUsize::new(0),
            root_total: AtomicUsize::new(0),
            best_seq_len: AtomicUsize::new(0),
            best_val_bits: AtomicU32Compat::new(f32::NEG_INFINITY.to_bits()),
        }
    }
}

static SEARCH_TELEMETRY: Lazy<RwLock<Option<Arc<SearchTelemetry>>>> = Lazy::new(|| RwLock::new(None));

impl Default for SequencerConfig {
    fn default() -> Self {
        Self {
            weights: WeightsConfig::default(),
            search: SearchConfig::default(),
        }
    }
}

impl Default for WeightsConfig {
    fn default() -> Self {
        Self {
            board_presence: 2.0,
            blades: 1.75,
            hearts: 1.5,
            saturation_bonus: 4.0,
            energy_penalty: 0.2,
            live_ev_multiplier: 18.0,
            uncertainty_penalty_pow: 1.2,
            liveset_placement_bonus: 6.0,
        }
    }
}

struct TranspositionTable {
    entries: HashMap<(u64, usize), (Vec<i32>, f32, (f32, f32))>,
}

impl TranspositionTable {
    fn new() -> Self {
        Self {
            entries: HashMap::new(),
        }
    }

    fn get(&self, state: &GameState, depth: usize) -> Option<(Vec<i32>, f32, (f32, f32))> {
        self.entries.get(&(state_cache_key(state), depth)).cloned()
    }

    fn insert(&mut self, state: &GameState, depth: usize, value: (Vec<i32>, f32, (f32, f32))) {
        self.entries.insert((state_cache_key(state), depth), value);
    }
}

impl Default for SearchConfig {
    fn default() -> Self {
        Self {
            max_dfs_depth: 15,
            mc_trials: 100,
            beam_width: 8,
            use_memoization: true,
            beam_search: false,
            use_alpha_beta: true,
        }
    }
}

fn hash_pending_interaction<H: Hasher>(pending: &crate::core::logic::PendingInteraction, state: &mut H) {
    pending.ctx.hash(state);
    pending.card_id.hash(state);
    pending.ability_index.hash(state);
    pending.effect_opcode.hash(state);
    pending.target_slot.hash(state);
    pending.choice_type.hash(state);
    pending.filter_attr.hash(state);
    pending.choice_text.hash(state);
    pending.v_remaining.hash(state);
    pending.original_phase.hash(state);
    pending.original_current_player.hash(state);
    pending.actions.hash(state);
    pending.execution_id.hash(state);
}

fn state_cache_key(state: &GameState) -> u64 {
    let mut hasher = std::collections::hash_map::DefaultHasher::new();
    state.players.hash(&mut hasher);
    state.current_player.hash(&mut hasher);
    state.first_player.hash(&mut hasher);
    state.phase.hash(&mut hasher);
    state.prev_phase.hash(&mut hasher);
    state.prev_card_id.hash(&mut hasher);
    state.turn.hash(&mut hasher);
    state.trigger_depth.hash(&mut hasher);
    state.live_set_pending_draws.hash(&mut hasher);
    state.live_result_selection_pending.hash(&mut hasher);
    state.live_result_triggers_done.hash(&mut hasher);
    state.live_start_triggers_done.hash(&mut hasher);
    state.live_result_processed_mask.hash(&mut hasher);
    state.live_start_processed_mask.hash(&mut hasher);
    state.live_success_processed_mask.hash(&mut hasher);
    state.performance_reveals_done.hash(&mut hasher);
    state.performance_yell_done.hash(&mut hasher);
    state.rps_choices.hash(&mut hasher);
    state.score_req_list.hash(&mut hasher);
    state.score_req_player.hash(&mut hasher);
    state.obtained_success_live.hash(&mut hasher);

    for pending in &state.interaction_stack {
        hash_pending_interaction(pending, &mut hasher);
    }
    for (card_id, opcode, ctx, mandatory, trigger) in &state.trigger_queue {
        card_id.hash(&mut hasher);
        opcode.hash(&mut hasher);
        ctx.hash(&mut hasher);
        mandatory.hash(&mut hasher);
        trigger.hash(&mut hasher);
    }

    hasher.finish()
}

pub struct TurnSequencer;

/// MCTS Node for Monte Carlo Tree Search
#[derive(Clone)]
struct MctsNode {
    state: GameState,
    action: Option<i32>,
    parent: Option<usize>,
    children: Vec<usize>,
    visits: u32,
    total_score: f32,
    untried_actions: Vec<i32>,
    depth: usize,
}

impl MctsNode {
    fn new(state: GameState, action: Option<i32>, parent: Option<usize>, db: &CardDatabase) -> Self {
        // Get legal actions for this state
        let legal_ids = state.get_legal_action_ids(db);

        Self {
            state,
            action,
            parent,
            children: Vec::new(),
            visits: 0,
            total_score: 0.0,
            untried_actions: legal_ids,
            depth: 0, // Not used for limiting anymore
        }
    }

    fn ucb1(&self, parent_visits: u32) -> f32 {
        if self.visits == 0 {
            f32::INFINITY
        } else {
            let exploitation = self.total_score / self.visits as f32;
            let exploration = MCTS_EXPLORATION_CONST * (parent_visits as f32 / self.visits as f32).sqrt();
            exploitation + exploration
        }
    }

    fn is_fully_expanded(&self) -> bool {
        self.untried_actions.is_empty()
    }

    fn average_score(&self) -> f32 {
        if self.visits == 0 {
            0.0
        } else {
            self.total_score / self.visits as f32
        }
    }
}

/// MCTS Tree structure
struct MctsTree {
    nodes: Vec<MctsNode>,
    db: CardDatabase,
}

impl MctsTree {
    fn new(root_state: GameState, db: CardDatabase) -> Self {
        let mut nodes = Vec::new();

        // Get legal actions for root with actual db
        let legal_ids = root_state.get_legal_action_ids(&db);

        let root = MctsNode {
            state: root_state,
            action: None,
            parent: None,
            children: Vec::new(),
            visits: 0,
            total_score: 0.0,
            untried_actions: legal_ids,
            depth: 0,
        };

        nodes.push(root);

        Self { nodes, db }
    }

    fn root_index(&self) -> usize {
        0
    }

    fn select_child(&self, node_idx: usize) -> Option<usize> {
        let node = &self.nodes[node_idx];
        if node.children.is_empty() {
            return None;
        }

        let parent_visits = node.visits;
        let mut best_idx = None;
        let mut best_ucb = f32::NEG_INFINITY;

        for &child_idx in &node.children {
            let ucb = self.nodes[child_idx].ucb1(parent_visits);
            if ucb > best_ucb {
                best_ucb = ucb;
                best_idx = Some(child_idx);
            }
        }

        best_idx
    }

    fn expand(&mut self, parent_idx: usize) -> Option<usize> {
        let parent = &mut self.nodes[parent_idx];

        if parent.untried_actions.is_empty() {
            return None;
        }

        // Pick a random untried action
        let action_idx = parent.untried_actions.len() - 1;
        let action = parent.untried_actions.remove(action_idx);

        // Apply action to create new state
        let mut new_state = parent.state.clone();
        new_state.ui.silent = true;

        let success = new_state.step(&self.db, action).is_ok();

        if !success {
            // Action failed, create a terminal node with low score
            let new_node = MctsNode {
                state: new_state,
                action: Some(action),
                parent: Some(parent_idx),
                children: Vec::new(),
                visits: 1,
                total_score: -100.0, // Failed action gets negative score
                untried_actions: Vec::new(),
                depth: parent.depth + 1,
            };

            let new_idx = self.nodes.len();
            self.nodes.push(new_node);
            self.nodes[parent_idx].children.push(new_idx);
            return Some(new_idx);
        }

        // Get legal actions for the new state (no depth limit for MCTS)
        let new_legal_ids = new_state.get_legal_action_ids(&self.db);

        let new_node = MctsNode {
            state: new_state,
            action: Some(action),
            parent: Some(parent_idx),
            children: Vec::new(),
            visits: 0,
            total_score: 0.0,
            untried_actions: new_legal_ids,
            depth: parent.depth + 1,
        };

        let new_idx = self.nodes.len();
        self.nodes.push(new_node);
        self.nodes[parent_idx].children.push(new_idx);

        Some(new_idx)
    }

    fn simulate(&self, node_idx: usize) -> f32 {
        let node = &self.nodes[node_idx];

        // Simulate to the end of the turn (Main + LiveSet phases)
        let mut sim_state = node.state.clone();
        sim_state.ui.silent = true;

        // Continue playing until we're past Main phase
        // Use random playout for the rest of the turn
        let mut rng = rand::rng();
        let mut steps = 0;
        let max_steps = 100; // Safety limit for simulation

        while sim_state.phase == Phase::Main && steps < max_steps {
            let legal = sim_state.get_legal_action_ids(&self.db);
            if legal.is_empty() {
                break;
            }
            if let Some(&action) = legal.choose(&mut rng) {
                let _ = sim_state.step(&self.db, action);
            }
            steps += 1;
        }

        // Handle LiveSet phase
        if sim_state.phase == Phase::LiveSet {
            // Use the best liveset selection for simulation
            let weights = TurnSequencer::config_snapshot().weights;
            let (ls_actions, _, _) = TurnSequencer::find_best_liveset_selection_internal(&sim_state, &self.db, &weights);
            for &act in &ls_actions {
                let _ = sim_state.step(&self.db, act);
            }
        }

        // Evaluate final state
        let (board_score, live_ev) = TurnSequencer::evaluate_state_internal(&sim_state, &self.db);
        board_score + live_ev
    }

    fn backpropagate(&mut self, node_idx: usize, score: f32) {
        let mut idx = Some(node_idx);
        while let Some(i) = idx {
            self.nodes[i].visits += 1;
            self.nodes[i].total_score += score;
            idx = self.nodes[i].parent;
        }
    }

    fn get_best_sequence(&self) -> Vec<i32> {
        let root = &self.nodes[self.root_index()];
        if root.children.is_empty() {
            return Vec::new();
        }

        // Find the child with highest average score
        let mut best_child = root.children[0];
        let mut best_avg = f32::NEG_INFINITY;

        for &child_idx in &root.children {
            let avg = self.nodes[child_idx].average_score();
            if avg > best_avg {
                best_avg = avg;
                best_child = child_idx;
            }
        }

        // Build sequence by following best children
        let mut sequence = Vec::new();
        let mut current_idx = best_child;

        while !self.nodes[current_idx].children.is_empty() {
            if let Some(action) = self.nodes[current_idx].action {
                sequence.push(action);
            }

            // Continue with best child
            let mut best_next = self.nodes[current_idx].children[0];
            let mut best_next_avg = f32::NEG_INFINITY;

            for &child_idx in &self.nodes[current_idx].children {
                let avg = self.nodes[child_idx].average_score();
                if avg > best_next_avg {
                    best_next_avg = avg;
                    best_next = child_idx;
                }
            }

            current_idx = best_next;
        }

        // Add final action
        if let Some(action) = self.nodes[current_idx].action {
            sequence.push(action);
        }

        sequence
    }
}

#[derive(Clone)]
pub struct SequenceResult {
    pub actions: Vec<i32>,
    pub expected_value: f32,
    pub success_prob: f32,
}

impl TurnSequencer {
    fn config_snapshot() -> SequencerConfig {
        CONFIG.read().unwrap().clone()
    }

    fn progress_enabled() -> bool {
        matches!(std::env::var("TURNSEQ_PROGRESS").ok().as_deref(), Some("1") | Some("true") | Some("TRUE"))
    }

    fn stall_seconds() -> u64 {
        std::env::var("TURNSEQ_STALL_SECS")
            .ok()
            .and_then(|value| value.parse().ok())
            .unwrap_or(10)
    }

    fn install_telemetry(root_total: usize) -> (Arc<SearchTelemetry>, Option<thread::JoinHandle<()>>) {
        let telemetry = Arc::new(if Self::progress_enabled() {
            SearchTelemetry {
                enabled: true,
                done: AtomicBool::new(false),
                aborted: AtomicBool::new(false),
                node_count: AtomicUsize::new(0),
                root_done: AtomicUsize::new(0),
                root_total: AtomicUsize::new(root_total),
                best_seq_len: AtomicUsize::new(0),
                best_val_bits: AtomicU32Compat::new(f32::NEG_INFINITY.to_bits()),
            }
        } else {
            SearchTelemetry::disabled()
        });

        *SEARCH_TELEMETRY.write().unwrap() = Some(Arc::clone(&telemetry));

        if !telemetry.enabled {
            return (telemetry, None);
        }

        let telemetry_for_thread = Arc::clone(&telemetry);
        let handle = thread::spawn(move || {
            let stall_secs = Self::stall_seconds();
            let start = Instant::now();
            let mut last_nodes = 0usize;
            let mut stagnant_seconds = 0u64;

            loop {
                thread::sleep(Duration::from_secs(1));

                let nodes = telemetry_for_thread.node_count.load(Ordering::Relaxed);
                let elapsed = start.elapsed().as_secs_f32().max(1.0);
                let rate = nodes as f32 / elapsed;
                let roots_done = telemetry_for_thread.root_done.load(Ordering::Relaxed);
                let roots_total = telemetry_for_thread.root_total.load(Ordering::Relaxed);
                let best_len = telemetry_for_thread.best_seq_len.load(Ordering::Relaxed);
                let best_val = f32::from_bits(telemetry_for_thread.best_val_bits.load(Ordering::Relaxed));

                eprintln!(
                    "[search] t={:.0}s nodes={} rate={:.1}/s roots={}/{} best_val={:.3} best_len={}",
                    elapsed,
                    nodes,
                    rate,
                    roots_done,
                    roots_total,
                    best_val,
                    best_len,
                );

                if telemetry_for_thread.done.load(Ordering::Relaxed) {
                    break;
                }

                if nodes == last_nodes {
                    stagnant_seconds += 1;
                    if stagnant_seconds >= stall_secs {
                        telemetry_for_thread.aborted.store(true, Ordering::Relaxed);
                        eprintln!("[search] stalled for {}s without node progress; aborting current search", stall_secs);
                        break;
                    }
                } else {
                    last_nodes = nodes;
                    stagnant_seconds = 0;
                }
            }
        });

        (telemetry, Some(handle))
    }

    fn clear_telemetry(telemetry: &Arc<SearchTelemetry>, handle: Option<thread::JoinHandle<()>>) {
        telemetry.done.store(true, Ordering::Relaxed);
        if let Some(join_handle) = handle {
            let _ = join_handle.join();
        }
        *SEARCH_TELEMETRY.write().unwrap() = None;
    }

    fn telemetry_snapshot() -> Option<Arc<SearchTelemetry>> {
        SEARCH_TELEMETRY.read().unwrap().clone()
    }

    fn exact_turn_threshold() -> usize {
        std::env::var("TURNSEQ_EXACT_THRESHOLD")
            .ok()
            .and_then(|value| value.parse().ok())
            .unwrap_or(10000)
    }

    fn count_main_end_sequences(state: &GameState, db: &CardDatabase, depth: usize) -> usize {
        if state.phase != Phase::Main || depth == 0 {
            return 1;
        }

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        let mut total = 1usize;
        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            let mut next_state = state.clone();
            if next_state.step(db, action).is_ok() {
                total += Self::count_main_end_sequences(&next_state, db, depth.saturating_sub(1));
            }
        }

        total
    }

    fn evaluate_stop_state(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        weights: &WeightsConfig,
    ) -> (f32, (f32, f32)) {
        let mut final_state = state.clone();
        if final_state.phase == Phase::LiveSet {
            let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights);
            for &ls_act in &ls_actions {
                let _ = final_state.step(db, ls_act);
            }
        }
        let brk = Self::evaluate_state_for_player_with_weights(&final_state, db, root_player, weights);
        (brk.0 + brk.1, brk)
    }

    fn exact_small_turn_search(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        weights: &WeightsConfig,
        total_count: &AtomicUsize,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        total_count.fetch_add(1, Ordering::Relaxed);

        if state.phase != Phase::Main || depth == 0 {
            let (val, brk) = Self::evaluate_stop_state(state, db, root_player, weights);
            return (vec![], val, brk);
        }

        let mut best_seq = vec![ACTION_BASE_PASS];
        let mut pass_state = state.clone();
        let _ = pass_state.step(db, ACTION_BASE_PASS);
        let (mut best_val, mut best_brk) = Self::evaluate_stop_state(&pass_state, db, root_player, weights);

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            let mut next_state = state.clone();
            if next_state.step(db, action).is_err() {
                continue;
            }

            let (mut suffix, val, brk) = Self::exact_small_turn_search(
                &next_state,
                db,
                root_player,
                depth.saturating_sub(1),
                weights,
                total_count,
            );

            if val > best_val {
                let mut full = vec![action];
                full.append(&mut suffix);
                best_seq = full;
                best_val = val;
                best_brk = brk;
            }
        }

        (best_seq, best_val, best_brk)
    }

    /// Returns a list of (ActionID, Total, Board, Live) for all legal actions,
    /// the best overall sequence, the total nodes, and the best score breakdown.
    pub fn plan_full_turn(state: &GameState, db: &CardDatabase) -> (Vec<i32>, f32, (f32, f32), usize) {
        let config = Self::config_snapshot();
        let search = config.search.clone();
        let weights = config.weights.clone();
        let p_idx = state.current_player as usize;
        let mut best_overall_seq = Vec::new();
        let mut best_overall_val = f32::NEG_INFINITY;
        let mut best_overall_breakdown = (0.0, 0.0);
        let total_evals = Arc::new(AtomicUsize::new(0));

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, p_idx, &mut actions);
        if actions.is_empty() {
            return (vec![ACTION_BASE_PASS], 0.0, (0.0, 0.0), 1);
        }

        // VANILLA OPTIMIZATION: Skip sequence counting, always use exact planner
        if db.is_vanilla {
            let total_evals = AtomicUsize::new(0);
            let (seq, val, brk) = Self::exact_small_turn_search(
                state,
                db,
                p_idx,
                search.max_dfs_depth,
                &weights,
                &total_evals,
            );
            return (seq, val, brk, total_evals.load(Ordering::Relaxed));
        }

        let exact_sequences = Self::count_main_end_sequences(state, db, search.max_dfs_depth);
        if exact_sequences <= Self::exact_turn_threshold() {
            let total_evals = AtomicUsize::new(0);
            let (seq, val, brk) = Self::exact_small_turn_search(
                state,
                db,
                p_idx,
                search.max_dfs_depth,
                &weights,
                &total_evals,
            );
            return (seq, val, brk, total_evals.load(Ordering::Relaxed));
        }

        let (telemetry, progress_handle) = Self::install_telemetry(actions.len());

        if telemetry.enabled {
            let mut evaluations = Vec::with_capacity(actions.len());
            for &action in &actions {
                if telemetry.aborted.load(Ordering::Relaxed) {
                    break;
                }

                let evals_ref = Arc::clone(&total_evals);
                let mut sim_state = state.clone();
                let evaluation = if sim_state.step(db, action).is_ok() {
                    evals_ref.fetch_add(1, Ordering::Relaxed);
                    if sim_state.phase != Phase::Main {
                        let mut final_state = sim_state.clone();
                        if final_state.phase == Phase::LiveSet {
                            let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, &weights);
                            for &ls_act in &ls_actions {
                                let _ = final_state.step(db, ls_act);
                            }
                        }
                        let (b, l) = Self::evaluate_state_for_player_with_weights(&final_state, db, p_idx, &weights);
                        (b + l, b, l, vec![action])
                    } else {
                        let (suffix, val, breakdown) = if search.beam_search {
                            Self::beam_search_turn(
                                &sim_state,
                                db,
                                p_idx,
                                search.max_dfs_depth.saturating_sub(1),
                                search.beam_width,
                                &weights,
                            )
                        } else {
                            let mut tt = TranspositionTable::new();
                            Self::dfs_turn_memoized(
                                &sim_state,
                                db,
                                p_idx,
                                search.max_dfs_depth.saturating_sub(1),
                                &search,
                                &weights,
                                &mut tt,
                                &evals_ref,
                            )
                        };

                        let mut full_seq = vec![action];
                        full_seq.extend(suffix);
                        (val, breakdown.0, breakdown.1, full_seq)
                    }
                } else {
                    (-1.0, 0.0, 0.0, vec![action])
                };

                telemetry.root_done.fetch_add(1, Ordering::Relaxed);
                evaluations.push(evaluation);
            }

            for (val, b, l, seq) in evaluations {
                if val > best_overall_val {
                    best_overall_val = val;
                    best_overall_seq = seq;
                    best_overall_breakdown = (b, l);
                    telemetry.best_seq_len.store(best_overall_seq.len(), Ordering::Relaxed);
                    telemetry.best_val_bits.store(best_overall_val.to_bits(), Ordering::Relaxed);
                }
            }

            let final_evals = total_evals.load(Ordering::Relaxed);
            Self::clear_telemetry(&telemetry, progress_handle);
            return (best_overall_seq, best_overall_val, best_overall_breakdown, final_evals);
        }

        // Parallelize Root Level Action Evaluation
        let evaluations: Vec<(f32, f32, f32, Vec<i32>)> = actions.par_iter().map(|&action| {
            let evals_ref = Arc::clone(&total_evals);
            let mut sim_state = state.clone();
            if sim_state.step(db, action).is_ok() {
                evals_ref.fetch_add(1, Ordering::Relaxed);
                if sim_state.phase != Phase::Main {
                    let mut final_state = sim_state.clone();
                    if final_state.phase == Phase::LiveSet {
                        let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, &weights);
                        for &ls_act in &ls_actions {
                            let _ = final_state.step(db, ls_act);
                        }
                    }
                    let (b, l) = Self::evaluate_state_for_player_with_weights(&final_state, db, p_idx, &weights);
                    return (b + l, b, l, vec![action]);
                }

                let (suffix, val, breakdown) = if search.beam_search {
                    Self::beam_search_turn(
                        &sim_state,
                        db,
                        p_idx,
                        search.max_dfs_depth.saturating_sub(1),
                        search.beam_width,
                        &weights,
                    )
                } else {
                    let mut tt = TranspositionTable::new();
                    Self::dfs_turn_memoized(
                        &sim_state,
                        db,
                        p_idx,
                        search.max_dfs_depth.saturating_sub(1),
                        &search,
                        &weights,
                        &mut tt,
                        &evals_ref,
                    )
                };

                let mut full_seq = vec![action];
                full_seq.extend(suffix);
                (val, breakdown.0, breakdown.1, full_seq)
            } else {
                (-1.0, 0.0, 0.0, vec![action])
            }
        }).collect();

        for (val, b, l, seq) in evaluations {
            if val > best_overall_val {
                best_overall_val = val;
                best_overall_seq = seq;
                best_overall_breakdown = (b, l);
            }
        }

        let final_evals = total_evals.load(Ordering::Relaxed);
        Self::clear_telemetry(&telemetry, progress_handle);
        (best_overall_seq, best_overall_val, best_overall_breakdown, final_evals)
    }

    /// Compatibility wrapper for the rest of the engine (e.g. MCTS and Heuristics)
    pub fn find_best_main_sequence(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        let (seq, _, _, evals) = Self::plan_full_turn(state, db);
        (seq, 0, evals as u128)
    }

    pub fn plan_full_turn_exact(state: &GameState, db: &CardDatabase) -> (Vec<i32>, f32, (f32, f32), usize) {
        let config = Self::config_snapshot();
        let weights = config.weights;
        let total_evals = AtomicUsize::new(0);
        let p_idx = state.current_player as usize;
        let (seq, val, brk) = Self::exact_small_turn_search(
            state,
            db,
            p_idx,
            config.search.max_dfs_depth,
            &weights,
            &total_evals,
        );
        (seq, val, brk, total_evals.load(Ordering::Relaxed))
    }

    /// Run exhaustive search to find the best sequence of moves for the current turn
    /// This explores ALL legal combinations to the end of the turn (Main + LiveSet phases)
    /// Note: This uses DFS with no depth limit, exploring all possible action sequences
    pub fn plan_full_turn_mcts(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        let mut best_seq = Vec::new();
        let mut best_val = f32::NEG_INFINITY;
        let mut nodes_visited = 0;

        // Get all legal actions for the current state
        let legal_actions = state.get_legal_action_ids(db);
        let total_legal = legal_actions.len();

        for &action in &legal_actions {
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            // Apply the action
            if sim_state.step(db, action).is_ok() {
                let mut current_seq = vec![action];

                // Recursively explore remaining moves in Main phase
                Self::exhaustive_search_main(&mut sim_state, db, &mut current_seq, &mut best_seq, &mut best_val, &mut nodes_visited);
            }
        }

        (best_seq, total_legal, nodes_visited as u128)
    }

    /// Recursively search all combinations in Main phase
    /// Stops when no more legal actions in Main phase
    fn exhaustive_search_main(
        state: &mut GameState,
        db: &CardDatabase,
        current_seq: &mut Vec<i32>,
        best_seq: &mut Vec<i32>,
        best_val: &mut f32,
        nodes_visited: &mut usize,
    ) {
        *nodes_visited += 1;

        // Safety: limit recursion depth to prevent stack overflow
        if *nodes_visited > 100000 {
            return;
        }

        // Check if we're still in Main phase
        if state.phase != Phase::Main {
            // We've exited Main, now handle LiveSet
            Self::exhaustive_search_liveset(state, db, current_seq, best_seq, best_val, nodes_visited);
            return;
        }

        // Get legal actions from current state
        let legal_actions = state.get_legal_action_ids(db);

        // If no more actions in Main, try LiveSet
        if legal_actions.is_empty() {
            Self::exhaustive_search_liveset(state, db, current_seq, best_seq, best_val, nodes_visited);
            return;
        }

        // Try each legal action - but limit to prevent explosion
        // Only explore a reasonable number of paths
        let max_paths = 1000;
        let paths_to_try = legal_actions.len().min(max_paths);

        for i in 0..paths_to_try {
            let action = legal_actions[i];
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            if sim_state.step(db, action).is_ok() {
                current_seq.push(action);
                Self::exhaustive_search_main(&mut sim_state, db, current_seq, best_seq, best_val, nodes_visited);
                current_seq.pop();
            }
        }
    }

    /// Exhaustively search LiveSet combinations and evaluate
    fn exhaustive_search_liveset(
        state: &mut GameState,
        db: &CardDatabase,
        current_seq: &mut Vec<i32>,
        best_seq: &mut Vec<i32>,
        best_val: &mut f32,
        nodes_visited: &mut usize,
    ) {
        *nodes_visited += 1;

        // If we're not in LiveSet phase, just evaluate
        if state.phase != Phase::LiveSet {
            let (board_score, live_ev) = Self::evaluate_state_internal(state, db);
            let total_val = board_score + live_ev;

            if total_val > *best_val {
                *best_val = total_val;
                *best_seq = current_seq.clone();
            }
            return;
        }

        // Get legal LiveSet actions
        let legal_actions = state.get_legal_action_ids(db);

        // If no more LiveSet actions, evaluate
        if legal_actions.is_empty() {
            let (board_score, live_ev) = Self::evaluate_state_internal(state, db);
            let total_val = board_score + live_ev;

            if total_val > *best_val {
                *best_val = total_val;
                *best_seq = current_seq.clone();
            }
            return;
        }

        // Try each LiveSet action
        for &action in &legal_actions {
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            if sim_state.step(db, action).is_ok() {
                current_seq.push(action);
                Self::exhaustive_search_liveset(&mut sim_state, db, current_seq, best_seq, best_val, nodes_visited);
                current_seq.pop();
            }
        }
    }

    pub fn plan_full_turn_with_stats(state: &GameState, db: &CardDatabase) -> (Vec<(i32, f32, f32, f32)>, Vec<i32>, usize, f32, (f32, f32)) {
        let start = Instant::now();
        let (seq, _, breakdown, evals) = Self::plan_full_turn(state, db);
        let duration = start.elapsed().as_secs_f32();
        (vec![], seq, evals, duration, breakdown)
    }
    pub fn find_best_liveset_selection(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        let weights = Self::config_snapshot().weights;
        Self::find_best_liveset_selection_internal(state, db, &weights)
    }

    pub fn beam_search_turn(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        beam_width: usize,
        weights: &WeightsConfig,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        let mut beam: Vec<(GameState, Vec<i32>, f32, (f32, f32))> = vec![(state.clone(), Vec::new(), 0.0, (0.0, 0.0))];
        let mut best_overall_seq = Vec::new();
        let mut best_overall_val = f32::NEG_INFINITY;
        let mut best_overall_breakdown = (0.0, 0.0);

        for _ in 0..depth {
            let mut next_beam = Vec::new();
            let mut any_main = false;

            for (curr_state, seq, _, _) in beam {
                if curr_state.phase != Phase::Main {
                    continue;
                }
                any_main = true;

                let mut legal_actions = SmallVec::<[i32; 64]>::new();
                curr_state.generate_legal_actions(db, curr_state.current_player as usize, &mut legal_actions);
                let mut candidates = Vec::new();

                for action in legal_actions {
                    let mut next_state = curr_state.clone();
                    if next_state.step(db, action).is_ok() {
                        if next_state.phase != Phase::Main {
                            // Evaluate transition to LiveSet
                            let mut final_state = next_state.clone();
                            if final_state.phase == Phase::LiveSet {
                                let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights);
                                for &ls_act in &ls_actions {
                                    let _ = final_state.step(db, ls_act);
                                }
                            }
                            let (b, l) = Self::evaluate_state_for_player_with_weights(&final_state, db, root_player, weights);
                            candidates.push((next_state, action, b + l, (b, l)));
                        } else {
                            // Immediate heuristic for move ordering
                            let (b, l) = Self::evaluate_state_for_player_with_weights(&next_state, db, root_player, weights);
                            candidates.push((next_state, action, b + l, (b, l)));
                        }
                    }
                }

                // Sort and take top beam_width
                candidates.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
                for (ns, act, val, brk) in candidates.into_iter().take(beam_width) {
                    let mut next_seq = seq.clone();
                    next_seq.push(act);
                    next_beam.push((ns, next_seq, val, brk));
                }
            }

            if !any_main { break; }

            next_beam.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
            beam = next_beam.into_iter().take(beam_width).collect();

            if let Some((_, seq, val, brk)) = beam.first() {
                if *val > best_overall_val {
                    best_overall_val = *val;
                    best_overall_seq = seq.clone();
                    best_overall_breakdown = *brk;
                }
            }
        }

        (best_overall_seq, best_overall_val, best_overall_breakdown)
    }

    fn dfs_turn_memoized(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        search: &SearchConfig,
        weights: &WeightsConfig,
        tt: &mut TranspositionTable,
        total_count: &AtomicUsize,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        if search.use_alpha_beta {
            Self::dfs_alpha_beta(
                state, db, root_player, depth, search, weights, tt, total_count,
                f32::NEG_INFINITY, f32::INFINITY,
            )
        } else {
            Self::dfs_negamax(state, db, root_player, depth, search, weights, tt, total_count)
        }
    }

    /// Alpha-beta pruned DFS: dramatically reduces node count while preserving optimal result
    fn dfs_alpha_beta(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        search: &SearchConfig,
        weights: &WeightsConfig,
        tt: &mut TranspositionTable,
        total_count: &AtomicUsize,
        mut alpha: f32,
        beta: f32,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        total_count.fetch_add(1, Ordering::Relaxed);

        if let Some(telemetry) = Self::telemetry_snapshot() {
            telemetry.node_count.fetch_add(1, Ordering::Relaxed);
            if telemetry.aborted.load(Ordering::Relaxed) {
                return (vec![ACTION_BASE_PASS], f32::NEG_INFINITY, (f32::NEG_INFINITY, 0.0));
            }
        }

        if depth == 0 || state.phase != Phase::Main {
            let mut final_state = state.clone();
            if final_state.phase == Phase::LiveSet {
                let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights);
                for &act in &ls_actions {
                    let _ = final_state.step(db, act);
                }
            }
            let brk = Self::evaluate_state_for_player_with_weights(&final_state, db, root_player, weights);
            return (vec![], brk.0 + brk.1, brk);
        }

        if search.use_memoization {
            if let Some(entry) = tt.get(state, depth) {
                return entry;
            }
        }

        let mut best_val = f32::NEG_INFINITY;
        let mut best_seq = Vec::new();
        let mut best_brk = (0.0, 0.0);

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        // Quick heuristic scoring and sorting (ESSENTIAL for AB pruning) - but cheap!
        // Note: depth counts DOWN from max_dfs_depth (15->1), so depth > 10 is SHALLOW (close to root)
        let do_order = depth > 8;  // Only order in first ~7 moves where pruning helps most
        let mut sorted_actions = Vec::with_capacity(actions.len());
        
        if do_order {
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                    // Board-state heuristic for move ordering (good pruning signal)
                    let board_score = Self::move_order_score(&next_state, db, root_player, weights);
                    sorted_actions.push((action, board_score, next_state));
                }
            }
            sorted_actions.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        } else {
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                    sorted_actions.push((action, 0.0, next_state));  // No ordering, random exploration
                }
            }
        }

        for (action, _, next_state) in sorted_actions {
            let (mut suffix, val, brk) = Self::dfs_alpha_beta(
                &next_state,
                db,
                root_player,
                depth.saturating_sub(1),
                search,
                weights,
                tt,
                total_count,
                alpha,
                beta,
            );
            
            if val > best_val {
                best_val = val;
                best_brk = brk;
                let mut full = vec![action];
                full.append(&mut suffix);
                best_seq = full;
                alpha = alpha.max(val);
            }
            
            // Beta cutoff: if we found a move better than beta, parent won't choose this branch
            if alpha >= beta {
                break;
            }
        }

        if best_val == f32::NEG_INFINITY {
            let mut final_state = state.clone();
            if final_state.phase == Phase::LiveSet {
                let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights);
                for &act in &ls_actions {
                    let _ = final_state.step(db, act);
                }
            }
            let brk = Self::evaluate_state_for_player_with_weights(&final_state, db, root_player, weights);
            best_val = brk.0 + brk.1;
            best_brk = brk;
        }

        let result = (best_seq, best_val, best_brk);
        if search.use_memoization {
            tt.insert(state, depth, result.clone());
        }
        result
    }

    /// Original DFS without pruning (for comparison/debugging)
    fn dfs_negamax(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        search: &SearchConfig,
        weights: &WeightsConfig,
        tt: &mut TranspositionTable,
        total_count: &AtomicUsize,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        total_count.fetch_add(1, Ordering::Relaxed);

        if let Some(telemetry) = Self::telemetry_snapshot() {
            telemetry.node_count.fetch_add(1, Ordering::Relaxed);
            if telemetry.aborted.load(Ordering::Relaxed) {
                return (vec![ACTION_BASE_PASS], f32::NEG_INFINITY, (f32::NEG_INFINITY, 0.0));
            }
        }

        if depth == 0 || state.phase != Phase::Main {
            let mut final_state = state.clone();
            if final_state.phase == Phase::LiveSet {
                let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights);
                for &act in &ls_actions {
                    let _ = final_state.step(db, act);
                }
            }
            let brk = Self::evaluate_state_for_player_with_weights(&final_state, db, root_player, weights);
            return (vec![], brk.0 + brk.1, brk);
        }

        if search.use_memoization {
            if let Some(entry) = tt.get(state, depth) {
                return entry;
            }
        }

        let mut best_val = f32::NEG_INFINITY;
        let mut best_seq = Vec::new();
        let mut best_brk = (0.0, 0.0);

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        // Light move ordering only at shallow depths (depth counts DOWN from 15, so depth > 8 is shallow)
        let do_order = depth > 8;  // Order in first ~7 moves for better search quality
        
        if do_order {
            // Light move ordering for shallow searches (ultra-light: count pieces only)
            let mut sorted_actions = Vec::with_capacity(actions.len());
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                    // Board-state heuristic for move ordering (good pruning signal)
                    let board_score = Self::move_order_score(&next_state, db, root_player, weights);
                    sorted_actions.push((action, board_score, next_state));
                }
            }
            sorted_actions.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

            for (action, _, next_state) in sorted_actions {
                let (mut suffix, val, brk) = Self::dfs_negamax(
                    &next_state,
                    db,
                    root_player,
                    depth.saturating_sub(1),
                    search,
                    weights,
                    tt,
                    total_count,
                );
                if val > best_val {
                    best_val = val;
                    best_brk = brk;
                    let mut full = vec![action];
                    full.append(&mut suffix);
                    best_seq = full;
                }
            }
        } else {
            // No move ordering at deep levels - just explore
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                    let (mut suffix, val, brk) = Self::dfs_negamax(
                        &next_state,
                        db,
                        root_player,
                        depth.saturating_sub(1),
                        search,
                        weights,
                        tt,
                        total_count,
                    );
                    if val > best_val {
                        best_val = val;
                        best_brk = brk;
                        let mut full = vec![action];
                        full.append(&mut suffix);
                        best_seq = full;
                    }
                }
            }
        }

        if best_val == f32::NEG_INFINITY {
            let mut final_state = state.clone();
            if final_state.phase == Phase::LiveSet {
                let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights);
                for &act in &ls_actions {
                    let _ = final_state.step(db, act);
                }
            }
            let brk = Self::evaluate_state_for_player_with_weights(&final_state, db, root_player, weights);
            best_val = brk.0 + brk.1;
            best_brk = brk;
        }

        let result = (best_seq, best_val, best_brk);
        if search.use_memoization {
            tt.insert(state, depth, result.clone());
        }
        result
    }

    fn find_best_liveset_selection_with_weights(
        state: &GameState,
        db: &CardDatabase,
        weights: &WeightsConfig,
    ) -> (Vec<i32>, usize, u128) {
        Self::find_best_liveset_selection_internal(state, db, weights)
    }

    fn evaluate_members_only_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> f32 {
        let mut score = 0.0;
        let mut filled_slots = 0;
        for i in 0..3 {
            let cid = state.players[p_idx].stage[i];
            if cid >= 0 {
                filled_slots += 1;
                score += weights.board_presence;

                if let Some(m) = db.get_member(cid) {
                    score += m.blades as f32 * weights.blades;
                    score += m.hearts.iter().sum::<u8>() as f32 * weights.hearts;
                }
            }
        }

        if filled_slots == 3 {
            score += weights.saturation_bonus;
        }

        let untapped = state.players[p_idx].energy_zone.len() - state.players[p_idx].tapped_energy_count() as usize;
        score -= untapped as f32 * weights.energy_penalty;
        score
    }

    /// Ultra-light scoring JUST for move ordering - avoids DB lookups
    #[inline]
    fn quick_move_order_score(
        state: &GameState,
        p_idx: usize,
    ) -> f32 {
        let mut score = 0.0;
        let mut filled_slots = 0;

        // Just count pieces, no DB lookups
        for i in 0..3 {
            if state.players[p_idx].stage[i] >= 0 {
                filled_slots += 1;
                score += 1.0;  // Base unit for piece presence
            }
        }

        if filled_slots == 3 {
            score += 1.0;  // Bonus for full board
        }

        let untapped = state.players[p_idx].energy_zone.len() - state.players[p_idx].tapped_energy_count() as usize;
        score -= untapped as f32 * 0.1;  // Light energy penalty
        score
    }

    // Use board-state eval for move ordering (weights included = good pruning signal)
    #[inline]
    fn move_order_score(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> f32 {
        Self::evaluate_members_only_with_weights(state, db, p_idx, weights)
    }

    fn evaluate_state_for_player_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> (f32, f32) {
        let live_score_ev = Self::predict_best_liveset_score_with_weights(state, db, p_idx, weights);
        let live_ev = live_score_ev * weights.live_ev_multiplier;
        let board_score = Self::evaluate_members_only_with_weights(state, db, p_idx, weights);
        (board_score, live_ev)
    }

    fn evaluate_live_zone_score_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> f32 {
        let Some((board_hearts, expected_yell_hearts, heart_reductions)) =
            Self::build_live_eval_context(state, db, p_idx)
        else {
            return 0.0;
        };

        state.players[p_idx]
            .live_zone
            .iter()
            .filter_map(|&cid| db.get_live(cid))
            .map(|live| {
                Self::live_card_expected_value_with_weights(
                    live,
                    db,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                    weights,
                )
            })
            .sum()
    }

    fn predict_best_liveset_score_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> f32 {
        let Some((board_hearts, expected_yell_hearts, heart_reductions)) =
            Self::build_live_eval_context(state, db, p_idx)
        else {
            return 0.0;
        };

        let mut total = state.players[p_idx]
            .live_zone
            .iter()
            .filter_map(|&cid| db.get_live(cid))
            .map(|live| {
                Self::live_card_expected_value_with_weights(
                    live,
                    db,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                    weights,
                )
            })
            .sum::<f32>();

        let empty_slots = state.players[p_idx].live_zone.iter().filter(|&&cid| cid == -1).count();
        if empty_slots == 0 {
            return total;
        }

        let mut hand_live_values: Vec<f32> = state.players[p_idx]
            .hand
            .iter()
            .filter_map(|&cid| db.get_live(cid))
            .map(|live| {
                Self::live_card_expected_value_with_weights(
                    live,
                    db,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                    weights,
                )
            })
            .collect();

        hand_live_values.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
        total += hand_live_values.into_iter().take(empty_slots).sum::<f32>();
        total
    }

    fn live_card_expected_value_with_weights(
        live: &crate::core::logic::card_db::LiveCard,
        db: &CardDatabase,
        board_hearts: &[u32; 7],
        expected_yell_hearts: &[f32],
        heart_reductions: [u8; 7],
        weights: &WeightsConfig,
    ) -> f32 {
        use crate::core::heuristics::calculate_live_success_prob;

        let prob = if db.is_vanilla {
            calculate_live_success_prob(live, board_hearts, expected_yell_hearts, heart_reductions)
                .min(1.0)
        } else {
            0.5
        };

        prob.powf(weights.uncertainty_penalty_pow) * live.score as f32
    }

    /// Unified DFS that traverses Main and then looks into LiveSet
    fn dfs_turn(
        state: &mut GameState,
        db: &CardDatabase,
        root_player: usize,
        current_seq: &mut Vec<i32>,
        best_seq: &mut Vec<i32>,
        best_val: &mut f32,
        best_breakdown: &mut (f32, f32),
        total_count: &mut usize,
    ) {
        *total_count += 1;

        if state.phase == Phase::Main {
            if current_seq.len() < Self::config_snapshot().search.max_dfs_depth {
                let p_idx = state.current_player as usize;
                let hand_len = state.players[p_idx].hand.len();

                for h_idx in 0..hand_len {
                    let s0_empty = state.players[p_idx].stage[0] == -1;
                    let s2_empty = state.players[p_idx].stage[2] == -1;
                    let skip_s2 = s0_empty && s2_empty;

                    for slot in 0..STAGE_SLOT_COUNT {
                        if slot == 2 && skip_s2 {
                            continue;
                        }
                        let action = ACTION_BASE_HAND + (h_idx as i32) * 10 + (slot as i32);

                        let cid = state.players[p_idx].hand[h_idx];
                        if state.players[p_idx].stage[slot] == -1 && !state.players[p_idx].is_moved(slot) {
                            let cost = state.get_member_cost(p_idx, cid, slot as i16, -1, db, 0);
                            let energy = state.players[p_idx].get_untapped_energy_indices(cost as usize).len();

                            if energy >= cost as usize {
                                let mut next_state = state.clone();
                                if next_state.step(db, action).is_ok() {
                                    current_seq.push(action);
                                    Self::dfs_turn(
                                        &mut next_state,
                                        db,
                                        root_player,
                                        current_seq,
                                        best_seq,
                                        best_val,
                                        best_breakdown,
                                        total_count,
                                    );
                                    current_seq.pop();
                                }
                            }
                        }
                    }
                }
            }

            let mut stop_state = state.clone();
            stop_state.ui.silent = true;
            let _ = stop_state.step(db, ACTION_BASE_PASS);
            let weights = Self::config_snapshot().weights;
            let (board_score, live_ev) =
                Self::evaluate_state_for_player_with_weights(&stop_state, db, root_player, &weights);
            let current_val = board_score + live_ev;

            if current_val > *best_val || (!current_seq.is_empty() && current_val >= *best_val) {
                *best_val = current_val;
                *best_seq = current_seq.clone();
                *best_breakdown = (board_score, live_ev);
            }
        } else if state.phase == Phase::LiveSet {
            let weights = Self::config_snapshot().weights;
            let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(state, db, &weights);
            let mut final_state = state.clone();
            for &act in &ls_actions {
                let _ = final_state.step(db, act);
            }
            let (board_score, live_ev) =
                Self::evaluate_state_for_player_with_weights(&final_state, db, root_player, &weights);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_breakdown = (board_score, live_ev);
                let mut full_seq = current_seq.clone();
                full_seq.extend(ls_actions);
                *best_seq = full_seq;
            }
        } else {
            let weights = Self::config_snapshot().weights;
            let (board_score, live_ev) =
                Self::evaluate_state_for_player_with_weights(state, db, root_player, &weights);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_breakdown = (board_score, live_ev);
                *best_seq = current_seq.clone();
            }
        }
    }

    fn find_best_liveset_selection_internal(
        state: &GameState,
        db: &CardDatabase,
        weights: &WeightsConfig,
    ) -> (Vec<i32>, usize, u128) {
        let p_idx = state.current_player as usize;
        let hand_lives: Vec<usize> = state.players[p_idx].hand.iter()
            .enumerate()
            .filter(|(_, &cid)| db.get_live(cid).is_some())
            .map(|(i, _)| i)
            .collect();

        if hand_lives.is_empty() {
            return (Vec::new(), 0, 0);
        }

        let empty_slots = state.players[p_idx].live_zone.iter().filter(|&&cid| cid == -1).count();
        if empty_slots == 0 {
            return (Vec::new(), 0, 0);
        }

        // In vanilla LiveSet, the order of plays does not affect legality or value.
        // Because live EV is additive across chosen lives, the exact optimum is simply:
        // choose up to `empty_slots` lives with the highest positive (EV + placement bonus).
        let mut scored_actions: Vec<(usize, f32)> = hand_lives
            .into_iter()
            .filter_map(|h_idx| {
                let cid = state.players[p_idx].hand[h_idx];
                let live = db.get_live(cid)?;
                let Some((board_hearts, expected_yell_hearts, heart_reductions)) =
                    Self::build_live_eval_context(state, db, p_idx)
                else {
                    return None;
                };
                let ev = Self::live_card_expected_value_with_weights(
                    live,
                    db,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                    weights,
                );
                Some((h_idx, ev + weights.liveset_placement_bonus))
            })
            .collect();

        scored_actions.sort_by(|a, b| {
            b.1.partial_cmp(&a.1)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| b.0.cmp(&a.0))
        });

        let mut chosen: Vec<(usize, f32)> = scored_actions
            .into_iter()
            .take(empty_slots)
            .filter(|(_, score)| *score > 0.0)
            .collect();

        let total_score = chosen.iter().map(|(_, score)| *score).sum::<f32>();

        // Execute in descending hand-index order so later removals do not invalidate earlier indices.
        chosen.sort_by(|a, b| b.0.cmp(&a.0));
        let best_actions = chosen
            .into_iter()
            .map(|(h_idx, _)| ACTION_BASE_LIVESET + h_idx as i32)
            .collect::<Vec<_>>();

        (best_actions, 0, (total_score.max(0.0) * 1000.0) as u128)
    }

    fn evaluate_state(state: &GameState, db: &CardDatabase) -> (f32, f32) {
        Self::evaluate_state_internal(state, db)
    }

    /// Internal evaluation function (public for MCTS use)
    fn evaluate_state_internal(state: &GameState, db: &CardDatabase) -> (f32, f32) {
        Self::evaluate_state_for_player(state, db, state.current_player as usize)
    }

    fn evaluate_state_for_player(state: &GameState, db: &CardDatabase, p_idx: usize) -> (f32, f32) {
        let weights = Self::config_snapshot().weights;
        Self::evaluate_state_for_player_with_weights(state, db, p_idx, &weights)
    }

    fn evaluate_live_zone_score(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
        let weights = Self::config_snapshot().weights;
        Self::evaluate_live_zone_score_with_weights(state, db, p_idx, &weights)
    }

    fn predict_best_liveset_score(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
        let weights = Self::config_snapshot().weights;
        Self::predict_best_liveset_score_with_weights(state, db, p_idx, &weights)
    }

    fn build_live_eval_context(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
    ) -> Option<([u32; 7], Vec<f32>, [u8; 7])> {
        use crate::core::heuristics::calculate_deck_expectations;

        let deck_stats = calculate_deck_expectations(&state.players[p_idx].deck, db);
        let yell_count = state.get_total_blades(p_idx, db, 0);
        let board_hearts = state.get_total_hearts(p_idx, db, 0).to_array().map(|v| v as u32);
        let expected_yell_hearts: Vec<f32> = deck_stats
            .avg_hearts
            .iter()
            .map(|&h| h * yell_count as f32)
            .collect();
        let heart_reductions = state.players[p_idx].heart_req_reductions.to_array();
        Some((board_hearts, expected_yell_hearts, heart_reductions))
    }

    fn live_card_expected_value(
        live: &crate::core::logic::card_db::LiveCard,
        db: &CardDatabase,
        board_hearts: &[u32; 7],
        expected_yell_hearts: &[f32],
        heart_reductions: [u8; 7],
    ) -> f32 {
        let weights = Self::config_snapshot().weights;
        Self::live_card_expected_value_with_weights(
            live,
            db,
            board_hearts,
            expected_yell_hearts,
            heart_reductions,
            &weights,
        )
    }

    /*
    fn estimate_live_ev(state: &GameState, db: &CardDatabase) -> f32 {
        let p_idx = state.current_player as usize;
        let mut total_ev = 0.0;

        // For each card in the live zone, estimate success
        for i in 0..3 {
            let cid = state.players[p_idx].live_zone[i];
            if cid < 0 { continue; }
            if let Some(live) = db.get_live(cid) {
                let success_prob = Self::monte_carlo_success_prob(state, db, i);
                let score = live.score as f32; // Simplified score
                total_ev += success_prob * score;
            }
        }

        total_ev
    }
    */

    /*
    fn monte_carlo_success_prob(state: &GameState, db: &CardDatabase, slot_idx: usize) -> f32 {
        let p_idx = state.current_player as usize;
        let cid = state.players[p_idx].live_zone[slot_idx];
        let live = db.get_live(cid).unwrap();

        let board_hearts = state.get_total_hearts(p_idx, db, 0);
        let yell_count = state.get_total_blades(p_idx, db, 0);

        if yell_count == 0 {
            return if board_hearts.satisfies(live.hearts_board) { 1.0 } else { 0.0 };
        }

        // --- OPTIMIZATION: Vanilla Mode Statistical Expectation ---
        if db.is_vanilla {
            use crate::core::heuristics::{calculate_deck_expectations, calculate_live_success_prob};
            let stats = calculate_deck_expectations(&state.players[p_idx].deck, db);
            let expected_yell_hearts: Vec<f32> = stats.avg_hearts.iter().map(|&h| h * yell_count as f32).collect();

            // Use the soft probability estimation from heuristics
            return calculate_live_success_prob(
                live,
                &board_hearts.to_array().map(|v| v as u32),
                &expected_yell_hearts,
                state.players[p_idx].heart_req_reductions.to_array(),
            ).min(1.0);
        }

        let mut successes = 0;
        let trials = 100;
        let deck_cards = state.players[p_idx].deck.to_vec();

        let mut rng = rand::rng();

        for _ in 0..trials {
            let mut trial_deck = deck_cards.clone();
            trial_deck.shuffle(&mut rng);
            let mut trial_hearts = board_hearts.clone();
            let to_draw = yell_count.min(trial_deck.len() as u32) as usize;

            for j in 0..to_draw {
                let yid = trial_deck[j];
                if let Some(ym) = db.get_member(yid) {
                    trial_hearts.add(ym.blade_hearts_board);
                }
            }

            if trial_hearts.satisfies(live.hearts_board) {
                successes += 1;
            }
        }

        successes as f32 / trials as f32
    }
    */
}
