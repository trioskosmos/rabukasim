use crate::core::heuristics::Heuristic;
use crate::core::logic::{CardDatabase, GameState};
#[cfg(feature = "extension-module")]
use pyo3::prelude::*;
use rand::prelude::*;
use rand::rngs::SmallRng;
use rand::SeedableRng;
// use crate::core::logic::{Phase, ActionReceiver};
#[cfg(feature = "nn")]
use crate::core::enums::*;
#[cfg(feature = "nn")]
use crate::core::logic::ai_encoding::GameStateEncoding;
#[cfg(feature = "nn")]
use ort::session::Session;
#[cfg(feature = "parallel")]
use rayon::prelude::*;
use smallvec::SmallVec;
use std::collections::HashMap;
use std::f32;
#[cfg(feature = "nn")]
use std::sync::{Arc, Mutex};
use std::time::Duration;

#[derive(Default, Clone, Copy)]
pub struct MCTSProfiler {
    pub determinization: Duration,
    pub selection: Duration,
    pub expansion: Duration,
    pub simulation: Duration,
    pub backpropagation: Duration,
}

// DeckStats and EvalMode moved to heuristics.rs

impl MCTSProfiler {
    pub fn merge(&mut self, other: &Self) {
        self.determinization += other.determinization;
        self.selection += other.selection;
        self.expansion += other.expansion;
        self.simulation += other.simulation;
        self.backpropagation += other.backpropagation;
    }

    pub fn print(&self, total: Duration) {
        let total_secs = total.as_secs_f64();
        if total_secs == 0.0 {
            return;
        }
        println!("[MCTS Profile] Breakdown:");
        let items = [
            ("Determinization", self.determinization),
            ("Selection", self.selection),
            ("Expansion", self.expansion),
            ("Simulation", self.simulation),
            ("Backpropagation", self.backpropagation),
        ];

        for (name, dur) in items {
            let secs = dur.as_secs_f64();
            println!(
                "  - {:<16}: {:>8.3}s ({:>6.1}%)",
                name,
                secs,
                (secs / total_secs) * 100.0
            );
        }
    }
}

struct Node {
    visit_count: u32,
    value_sum: f32,
    player_just_moved: u8,
    prior_prob: f32, // AlphaZero Policy P(s,a)
    untried_actions: SmallVec<[i32; 32]>,
    children: SmallVec<[(i32, usize); 16]>, // (Action, NodeIndex in Arena)
    parent: Option<usize>,
    parent_action: i32,
}

pub struct MCTS {
    nodes: Vec<Node>,
    rng: SmallRng,
    unseen_buffer: SmallVec<[i32; 64]>,
    legal_buffer: SmallVec<[i32; 32]>,
    reusable_state: GameState,
    pub evaluator:
        Option<std::sync::Arc<Box<dyn crate::core::alphazero_evaluator::AlphaZeroEvaluator>>>,
    pub cpu_batch_size: usize,
    pub leaf_batch_size: usize,
    pub exploration_weight: f32,
}

#[cfg_attr(feature = "extension-module", pyclass)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SearchHorizon {
    GameEnd(),
    TurnEnd(),
    Limited(u32),
}

// EvalMode moved to heuristics.rs

impl MCTS {
    pub fn new() -> Self {
        Self {
            nodes: Vec::with_capacity(16384),
            rng: SmallRng::from_os_rng(),
            unseen_buffer: SmallVec::with_capacity(64),
            legal_buffer: SmallVec::with_capacity(32),
            reusable_state: GameState::default(),
            evaluator: None,
            cpu_batch_size: 16,
            leaf_batch_size: 512,
            exploration_weight: 1.41,
        }
    }

    pub fn with_evaluator(
        eval: std::sync::Arc<Box<dyn crate::core::alphazero_evaluator::AlphaZeroEvaluator>>,
        batch_size: usize,
    ) -> Self {
        let mut mcts = Self::new();
        mcts.evaluator = Some(eval);
        mcts.cpu_batch_size = batch_size;
        mcts
    }

    pub fn get_tree_size(&self) -> usize {
        self.nodes.len()
    }

    pub fn get_max_depth(&self) -> usize {
        let mut max_d = 0;
        for i in 0..self.nodes.len() {
            let mut d = 0;
            let mut curr = i;
            while let Some(p) = self.nodes[curr].parent {
                d += 1;
                curr = p;
            }
            if d > max_d {
                max_d = d;
            }
        }
        max_d
    }

    pub fn search_parallel(
        &self,
        root_state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
        horizon: SearchHorizon,
        heuristic: &dyn Heuristic,
        shuffle_self: bool,
    ) -> Vec<(i32, f32, u32)> {
        #[cfg(feature = "parallel")]
        let mut _num_threads = rayon::current_num_threads().max(1);
        #[cfg(not(feature = "parallel"))]
        let _num_threads = 1;
        let num_threads = _num_threads;

        let start_overall = std::time::Instant::now();
        let leaf_batch_size = self.leaf_batch_size;
        let sims_per_thread = if num_sims > 0 {
            (num_sims + num_threads - 1) / num_threads
        } else {
            0
        };

        // Collect results
        #[cfg(feature = "parallel")]
        let results: Vec<(Vec<(i32, f32, u32)>, MCTSProfiler)> = {
            let pool = rayon::ThreadPoolBuilder::new()
                .stack_size(16 * 1024 * 1024)
                .num_threads(num_threads)
                .build()
                .unwrap_or_else(|_| {
                    rayon::ThreadPoolBuilder::default()
                        .num_threads(num_threads)
                        .build()
                        .unwrap()
                });

            pool.install(|| {
                (0..num_threads)
                    .into_par_iter()
                    .map(|_| {
                        let mut mcts = MCTS::new();
                        mcts.leaf_batch_size = leaf_batch_size;
                        mcts.search_custom(
                            root_state,
                            db,
                            sims_per_thread,
                            timeout_sec,
                            horizon,
                            heuristic,
                            shuffle_self,
                            true,
                        )
                    })
                    .collect()
            })
        };

        #[cfg(not(feature = "parallel"))]
        let results: Vec<(Vec<(i32, f32, u32)>, MCTSProfiler)> = vec![{
            let mut mcts = MCTS::new();
            mcts.leaf_batch_size = leaf_batch_size;
            mcts.search_custom(
                root_state,
                db,
                num_sims,
                timeout_sec,
                horizon,
                heuristic,
                shuffle_self,
                true,
            )
        }];

        // Merge results
        let mut agg_map: HashMap<i32, (f32, u32)> = HashMap::new();
        let mut total_visits = 0;
        let mut agg_profile = MCTSProfiler::default();

        for (res, profile) in results {
            agg_profile.merge(&profile);
            for (action, score, visits) in res {
                let entry = agg_map.entry(action).or_insert((0.0, 0));
                let total_value = score * visits as f32;
                entry.0 += total_value;
                entry.1 += visits;
                total_visits += visits;
            }
        }

        // Logging Speed
        let duration = start_overall.elapsed();
        let _sims_per_sec = total_visits as f64 / duration.as_secs_f64();
        if total_visits > 100 {
            // println!("[MCTS] Completed {} sims in {:.3}s ({:.0} sims/s)", total_visits, duration.as_secs_f64(), sims_per_sec);
            // agg_profile.print(duration);
        }

        let mut stats: Vec<(i32, f32, u32)> = agg_map
            .into_iter()
            .map(|(action, (sum_val, visits))| {
                if visits > 0 {
                    (action, sum_val / visits as f32, visits)
                } else {
                    (action, 0.0, 0)
                }
            })
            .collect();

        stats.sort_by_key(|&(_, _, v)| std::cmp::Reverse(v));
        stats
    }

    pub fn search_parallel_mode(
        &self,
        root_state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
        horizon: SearchHorizon,
        eval_mode: crate::core::heuristics::EvalMode,
        heuristic: &dyn Heuristic,
    ) -> Vec<(i32, f32, u32)> {
        let start_overall = std::time::Instant::now();

        #[cfg(feature = "parallel")]
        let mut _num_threads = rayon::current_num_threads().max(1);
        #[cfg(not(feature = "parallel"))]
        let mut _num_threads = 1;

        let num_threads = _num_threads;

        let leaf_batch_size = self.leaf_batch_size;
        let sims_per_thread = if num_sims > 0 {
            (num_sims + num_threads - 1) / num_threads
        } else {
            0
        };

        // Collect results
        #[cfg(feature = "parallel")]
        let results: Vec<(Vec<(i32, f32, u32)>, MCTSProfiler)> = (0..num_threads)
            .into_par_iter()
            .map(|_| {
                let mut mcts = MCTS::new();
                mcts.leaf_batch_size = leaf_batch_size;
                mcts.search_mode(
                    root_state,
                    db,
                    sims_per_thread,
                    timeout_sec,
                    horizon,
                    eval_mode,
                    heuristic,
                )
            })
            .collect();

        #[cfg(not(feature = "parallel"))]
        let results: Vec<(Vec<(i32, f32, u32)>, MCTSProfiler)> = vec![{
            let mut mcts = MCTS::new();
            mcts.leaf_batch_size = leaf_batch_size;
            mcts.search_mode(
                root_state,
                db,
                num_sims,
                timeout_sec,
                horizon,
                eval_mode,
                heuristic,
            )
        }];

        // Merge results
        let mut agg_map: HashMap<i32, (f32, u32)> = HashMap::new();
        let mut total_visits = 0;
        let mut agg_profile = MCTSProfiler::default();

        for (res, profile) in results {
            agg_profile.merge(&profile);
            for (action, score, visits) in res {
                let entry = agg_map.entry(action).or_insert((0.0, 0));
                let total_value = score * visits as f32;
                entry.0 += total_value;
                entry.1 += visits;
                total_visits += visits;
            }
        }

        // Logging Speed
        let duration = start_overall.elapsed();
        let _sims_per_sec = total_visits as f64 / duration.as_secs_f64();
        if total_visits > 100 {
            // println!("[MCTS Mode] Completed {} sims in {:.3}s ({:.0} sims/s)", total_visits, duration.as_secs_f64(), sims_per_sec);
            // agg_profile.print(duration);
        }

        let mut stats: Vec<(i32, f32, u32)> = agg_map
            .into_iter()
            .map(|(action, (sum_val, visits))| {
                if visits > 0 {
                    (action, sum_val / visits as f32, visits)
                } else {
                    (action, 0.0, 0)
                }
            })
            .collect();

        stats.sort_by_key(|&(_, _, v)| std::cmp::Reverse(v));
        stats
    }

    pub fn search(
        &mut self,
        root_state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
        horizon: SearchHorizon,
        heuristic: &dyn Heuristic,
    ) -> (Vec<(i32, f32, u32)>, MCTSProfiler) {
        self.search_custom(
            root_state,
            db,
            num_sims,
            timeout_sec,
            horizon,
            heuristic,
            false,
            false,
        )
    }

    pub fn search_custom(
        &mut self,
        root_state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
        horizon: SearchHorizon,
        heuristic: &dyn Heuristic,
        shuffle_self: bool,
        enable_rollout: bool,
    ) -> (Vec<(i32, f32, u32)>, MCTSProfiler) {
        use crate::core::heuristics::calculate_deck_expectations;
        let p0_stats = calculate_deck_expectations(&root_state.players[0].deck, db);

        let mut p1_unseen = root_state.players[1].hand.clone();
        p1_unseen.extend(root_state.players[1].deck.iter().cloned());
        let p1_stats = calculate_deck_expectations(&p1_unseen, db);

        self.run_mcts_config(
            root_state,
            db,
            num_sims,
            timeout_sec,
            horizon,
            shuffle_self,
            enable_rollout,
            |state, _db| {
                if state.is_terminal() {
                    match state.get_winner() {
                        0 => 1.0,
                        1 => 0.0,
                        _ => 0.5,
                    }
                } else {
                    heuristic.evaluate(
                        state,
                        db,
                        root_state.players[0].score,
                        root_state.players[1].score,
                        crate::core::heuristics::EvalMode::Normal,
                        Some(p0_stats),
                        Some(p1_stats),
                    )
                }
            },
        )
    }

    pub fn search_mode(
        &mut self,
        root_state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
        horizon: SearchHorizon,
        eval_mode: crate::core::heuristics::EvalMode,
        heuristic: &dyn Heuristic,
    ) -> (Vec<(i32, f32, u32)>, MCTSProfiler) {
        use crate::core::heuristics::{calculate_deck_expectations, EvalMode};
        // Pre-calculate deck expectations for optimization
        let p0_stats = calculate_deck_expectations(&root_state.players[0].deck, db);

        let mut p1_unseen = root_state.players[1].hand.clone();
        p1_unseen.extend(root_state.players[1].deck.iter().cloned());
        let p1_stats = calculate_deck_expectations(&p1_unseen, db);

        self.run_mcts_config(
            root_state,
            db,
            num_sims,
            timeout_sec,
            horizon,
            eval_mode == EvalMode::Blind,
            true,
            |state, _db| {
                if state.is_terminal() {
                    if eval_mode == EvalMode::Solitaire {
                        match state.get_winner() {
                            0 => 1.0,
                            1 => 0.0,
                            _ => 0.5,
                        }
                    } else {
                        match state.get_winner() {
                            0 => 1.0,
                            1 => 0.0,
                            _ => 0.5,
                        }
                    }
                } else {
                    heuristic.evaluate(
                        state,
                        db,
                        root_state.players[0].score,
                        root_state.players[1].score,
                        eval_mode,
                        Some(p0_stats),
                        Some(p1_stats),
                    )
                }
            },
        )
    }

    pub fn run_mcts_config<F>(
        &mut self,
        root_state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
        horizon: SearchHorizon,
        shuffle_self: bool,
        enable_rollout: bool,
        mut eval_fn: F,
    ) -> (Vec<(i32, f32, u32)>, MCTSProfiler)
    where
        F: FnMut(&GameState, &CardDatabase) -> f32,
    {
        self.nodes.clear();
        let start_time = std::time::Instant::now();
        let timeout = if timeout_sec > 0.0 {
            Some(std::time::Duration::from_secs_f32(timeout_sec))
        } else {
            None
        };
        let root_start_turn = root_state.turn;
        let mut profiler = MCTSProfiler::default();

        // Root Node
        let mut legal_indices: SmallVec<[i32; 32]> = SmallVec::with_capacity(32);
        root_state.generate_legal_actions(
            db,
            root_state.current_player as usize,
            &mut legal_indices,
        );

        if legal_indices.is_empty() {
            return (vec![(0, 0.5, 0)], profiler);
        }
        if legal_indices.len() == 1 {
            return (vec![(legal_indices[0], 0.5, 1)], profiler);
        }

        self.nodes.push(Node {
            visit_count: 0,
            value_sum: 0.0,
            player_just_moved: 1 - root_state.current_player,
            prior_prob: 1.0,
            untried_actions: legal_indices,
            children: SmallVec::new(),
            parent: None,
            parent_action: 0,
        });

        let mut sims_done = 0;
        loop {
            if num_sims > 0 && sims_done >= num_sims {
                break;
            }
            if let Some(to) = timeout {
                if start_time.elapsed() >= to {
                    break;
                }
            }
            if num_sims == 0 && timeout.is_none() {
                break;
            } // Safety

            let is_trace = num_sims == 1;
            let t_setup = std::time::Instant::now();

            // --- BRANCH: AlphaZero Batch or Sequential ---
            if let Some(ref evaluator) = self.evaluator {
                let batch_size = self.cpu_batch_size;
                let mut batch_leaf_indices = Vec::with_capacity(batch_size);
                let mut batch_leaf_states = Vec::with_capacity(batch_size);

                for _ in 0..batch_size {
                    // 1. Setup (Determinization)
                    self.reusable_state.copy_from(&root_state);
                    let state = &mut self.reusable_state;
                    state.ui.silent = true;
                    // (Determinization logic duplicated for now within batch loop)
                    let me = root_state.current_player as usize;
                    let opp = 1 - me;
                    let opp_hand_len = state.core.players[opp].hand.len();
                    self.unseen_buffer.clear();
                    self.unseen_buffer
                        .extend_from_slice(&state.core.players[opp].hand);
                    self.unseen_buffer
                        .extend_from_slice(&state.core.players[opp].deck);
                    self.unseen_buffer.shuffle(&mut self.rng);
                    state.core.players[opp]
                        .hand
                        .copy_from_slice(&self.unseen_buffer[0..opp_hand_len]);
                    state.core.players[opp]
                        .deck
                        .copy_from_slice(&self.unseen_buffer[opp_hand_len..]);

                    // 2. Selection
                    let mut node_idx = 0;
                    while self.nodes[node_idx].untried_actions.is_empty()
                        && !self.nodes[node_idx].children.is_empty()
                    {
                        node_idx = Self::select_child_logic(
                            &self.nodes,
                            node_idx,
                            self.exploration_weight,
                        );
                        let action = self.nodes[node_idx].parent_action;
                        let _ = state.step(db, action);
                    }

                    // 3. Expansion
                    if !self.nodes[node_idx].untried_actions.is_empty() {
                        let idx = self
                            .rng
                            .random_range(0..self.nodes[node_idx].untried_actions.len());
                        let action = self.nodes[node_idx].untried_actions.swap_remove(idx);
                        let actor = state.current_player;
                        let _ = state.step(db, action);
                        state.sync_cost_modifiers(0, db);
                        state.sync_cost_modifiers(1, db);

                        self.legal_buffer.clear();
                        state.generate_legal_actions(
                            db,
                            state.current_player as usize,
                            &mut self.legal_buffer,
                        );
                        let new_legal_indices = self.legal_buffer.clone();
                        let prob = 1.0 / (new_legal_indices.len().max(1) as f32);

                        let new_idx = self.nodes.len();
                        self.nodes.push(Node {
                            visit_count: 0,
                            value_sum: 0.0,
                            player_just_moved: actor,
                            prior_prob: prob,
                            untried_actions: new_legal_indices,
                            children: SmallVec::new(),
                            parent: Some(node_idx),
                            parent_action: action,
                        });
                        self.nodes[node_idx].children.push((action, new_idx));
                        node_idx = new_idx;
                    }

                    batch_leaf_indices.push(node_idx);
                    batch_leaf_states.push(state.clone());
                }

                // 4. Collective Inference
                let outputs = evaluator.evaluate_batch(&batch_leaf_states, db);

                // 5. Apply results & Backprop
                for (i, output) in outputs.into_iter().enumerate() {
                    let leaf_idx = batch_leaf_indices[i];

                    // Update Policy Priors for children (if expanded)
                    if !self.nodes[leaf_idx].children.is_empty() {
                        // Assuming ACTION_SPACE is 8192
                        for j in 0..self.nodes[leaf_idx].children.len() {
                            let (action, child_idx) = self.nodes[leaf_idx].children[j];
                            if (action as usize) < output.policy.len() {
                                self.nodes[child_idx].prior_prob = output.policy[action as usize];
                            }
                        }
                    }

                    // Hybrid Reward: NN Value + Heuristic Weighting
                    let reward_p0 = if batch_leaf_states[i].is_terminal() {
                        match batch_leaf_states[i].get_winner() {
                            0 => 1.0,
                            1 => 0.0,
                            _ => 0.5,
                        }
                    } else {
                        // Meta-Heuristic: Use NN-predicted weights!
                        use crate::core::heuristics::{EvalMode, OriginalHeuristic};
                        let h = OriginalHeuristic {
                            config: output.weights,
                        };
                        let h_val = h.evaluate(
                            &batch_leaf_states[i],
                            db,
                            root_state.players[0].score,
                            root_state.players[1].score,
                            EvalMode::Normal,
                            None,
                            None,
                        );
                        // Blend: 50/50 NN Value and Heuristic Assessment
                        (output.value * 0.5) + (h_val * 0.5)
                    };

                    // Backprop
                    let mut curr = Some(leaf_idx);
                    while let Some(idx) = curr {
                        let node_p_moved = self.nodes[idx].player_just_moved;
                        let node = &mut self.nodes[idx];
                        node.visit_count += 1;
                        if node_p_moved == 0 {
                            node.value_sum += reward_p0;
                        } else {
                            node.value_sum += 1.0 - reward_p0;
                        }
                        curr = node.parent;
                    }
                }
                sims_done += batch_size;
            } else {
                sims_done += 1;
                let mut node_idx = 0;

                // 1. Setup & Determinization (Sequential)
                self.reusable_state.copy_from(&root_state);
                let state = &mut self.reusable_state;
                state.ui.silent = true;

                let me = root_state.current_player as usize;
                let opp = 1 - me;
                let opp_hand_len = state.core.players[opp].hand.len();

                self.unseen_buffer.clear();
                self.unseen_buffer
                    .extend_from_slice(&state.core.players[opp].hand);
                self.unseen_buffer
                    .extend_from_slice(&state.core.players[opp].deck);
                self.unseen_buffer.shuffle(&mut self.rng);

                state.core.players[opp]
                    .hand
                    .copy_from_slice(&self.unseen_buffer[0..opp_hand_len]);
                state.core.players[opp]
                    .deck
                    .copy_from_slice(&self.unseen_buffer[opp_hand_len..]);

                if shuffle_self {
                    let mut my_deck = state.core.players[me].deck.clone();
                    my_deck.shuffle(&mut self.rng);
                    state.core.players[me].deck = my_deck;
                }

                // --- SEQUENTIAL PATH (Original logic) ---
                profiler.determinization += t_setup.elapsed();

                // 2. Selection
                let t_selection = std::time::Instant::now();
                while self.nodes[node_idx].untried_actions.is_empty()
                    && !self.nodes[node_idx].children.is_empty()
                {
                    node_idx =
                        Self::select_child_logic(&self.nodes, node_idx, self.exploration_weight);
                    let action = self.nodes[node_idx].parent_action;
                    if is_trace {
                        println!("[MCTS TRACE] Selection: Action {}", action);
                    }
                    let _ = state.step(db, action);
                }
                profiler.selection += t_selection.elapsed();

                // 3. Expansion
                let t_expansion = std::time::Instant::now();
                if !self.nodes[node_idx].untried_actions.is_empty() {
                    let idx = self
                        .rng
                        .random_range(0..self.nodes[node_idx].untried_actions.len());
                    let action = self.nodes[node_idx].untried_actions.swap_remove(idx);
                    if is_trace {
                        println!("[MCTS TRACE] Expansion: Action {}", action);
                    }

                    let actor = state.current_player;
                    let _ = state.step(db, action);

                    state.sync_cost_modifiers(0, db);
                    state.sync_cost_modifiers(1, db);

                    self.legal_buffer.clear();
                    let mut is_capped = false;
                    if let SearchHorizon::TurnEnd() = horizon {
                        if state.turn > root_start_turn {
                            is_capped = true;
                        }
                    }
                    if !is_capped {
                        state.generate_legal_actions(
                            db,
                            state.current_player as usize,
                            &mut self.legal_buffer,
                        );
                    }

                    let new_legal_indices = self.legal_buffer.clone();
                    let prob = 1.0 / (new_legal_indices.len().max(1) as f32);
                    let new_node = Node {
                        visit_count: 0,
                        value_sum: 0.0,
                        player_just_moved: actor,
                        prior_prob: prob,
                        untried_actions: new_legal_indices,
                        children: SmallVec::new(),
                        parent: Some(node_idx),
                        parent_action: action,
                    };

                    let new_idx = self.nodes.len();
                    self.nodes.push(new_node);
                    self.nodes[node_idx].children.push((action, new_idx));
                    node_idx = new_idx;
                }
                profiler.expansion += t_expansion.elapsed();

                // 4. Simulation
                let t_simulation = std::time::Instant::now();
                let reward_p0 = {
                    // Standard CPU Rollout
                    let mut depth = 0;
                    if enable_rollout {
                        while !state.is_terminal() && depth < 200 {
                            if let SearchHorizon::Limited(max_depth) = horizon {
                                if depth >= max_depth as usize {
                                    break;
                                }
                            }
                            if let SearchHorizon::TurnEnd() = horizon {
                                if state.turn > root_start_turn {
                                    break;
                                }
                            }
                            state.generate_legal_actions(
                                db,
                                state.current_player as usize,
                                &mut self.legal_buffer,
                            );
                            if self.legal_buffer.is_empty() {
                                break;
                            }
                            let chunk_action = *self.legal_buffer.choose(&mut self.rng).unwrap();
                            let _ = state.step(db, chunk_action);
                            depth += 1;
                        }
                    }
                    eval_fn(&state, db)
                };
                profiler.simulation += t_simulation.elapsed();

                // 5. Backpropagation
                let _t_backprop = std::time::Instant::now();
                let mut curr = Some(node_idx);
                let batch_weight = 1.0;
                let batch_visits = 1;

                while let Some(idx) = curr {
                    let node_p_moved = self.nodes[idx].player_just_moved;
                    let node = &mut self.nodes[idx];
                    node.visit_count += batch_visits as u32;
                    if node_p_moved == 0 {
                        node.value_sum += reward_p0 * batch_weight;
                    } else {
                        node.value_sum += (1.0 - reward_p0) * batch_weight;
                    }
                    curr = node.parent;
                }
                sims_done += 1;
            }
        }

        let mut stats: Vec<(i32, f32, u32)> = self.nodes[0]
            .children
            .iter()
            .map(|&(act, idx)| {
                let child = &self.nodes[idx];
                (
                    act,
                    child.value_sum / child.visit_count as f32,
                    child.visit_count,
                )
            })
            .collect();

        stats.sort_by_key(|&(_, _, v)| std::cmp::Reverse(v));
        (stats, profiler)
    }

    fn select_child_logic(nodes: &[Node], node_idx: usize, exploration_weight: f32) -> usize {
        let node = &nodes[node_idx];
        let mut best_score = f32::NEG_INFINITY;
        let mut best_child = 0;

        let total_visits_sqrt = (node.visit_count as f32).sqrt();

        for &(_, child_idx) in &node.children {
            let child = &nodes[child_idx];

            // Average Value (Q). If no visits, evaluate slightly optimistically (0.5)
            let exploit = if child.visit_count > 0 {
                child.value_sum / child.visit_count as f32
            } else {
                0.5
            };

            // PUCT Exploration (AlphaZero)
            let explore = exploration_weight
                * child.prior_prob
                * (total_visits_sqrt / (1.0 + child.visit_count as f32));

            let score = exploit + explore;

            if score > best_score {
                best_score = score;
                best_child = child_idx;
            }
        }
        best_child
    }

    #[allow(dead_code)]
    fn select_child(&self, node_idx: usize) -> usize {
        Self::select_child_logic(&self.nodes, node_idx, self.exploration_weight)
    }

    // Evaluation functions moved to heuristics.rs
}

#[cfg(feature = "nn")]
pub struct HybridMCTS {
    pub session: Arc<Mutex<Session>>,
    pub neural_weight: f32,
    pub skip_rollout: bool,
    pub rng: SmallRng,
}

#[cfg(feature = "nn")]
impl HybridMCTS {
    pub fn new(session: Arc<Mutex<Session>>, neural_weight: f32, skip_rollout: bool) -> Self {
        Self {
            session,
            neural_weight,
            skip_rollout,
            rng: SmallRng::from_os_rng(),
        }
    }

    pub fn get_suggestions(
        &mut self,
        state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
    ) -> Vec<(i32, f32, u32)> {
        let start = std::time::Instant::now();
        let (stats, profile) = self.search(state, db, num_sims, timeout_sec);
        let duration = start.elapsed();
        if num_sims > 10 {
            profile.print(duration);
        }
        stats
    }

    pub fn search(
        &mut self,
        root_state: &GameState,
        db: &CardDatabase,
        num_sims: usize,
        timeout_sec: f32,
    ) -> (Vec<(i32, f32, u32)>, MCTSProfiler) {
        let session_arc = self.session.clone();
        let neural_weight = self.neural_weight;
        let mut mcts = MCTS::new();

        mcts.run_mcts_config(
            root_state,
            db,
            num_sims,
            timeout_sec,
            SearchHorizon::GameEnd(),
            false,
            !self.skip_rollout,
            |state: &GameState, db: &CardDatabase| {
                if state.is_terminal() {
                    return match state.get_winner() {
                        0 => 1.0,
                        1 => 0.0,
                        _ => 0.5,
                    };
                }

                // Normal Heuristic Baseline
                use crate::core::heuristics::{EvalMode, OriginalHeuristic};
                let h = OriginalHeuristic::default();
                let h_val = h.evaluate(
                    state,
                    db,
                    root_state.players[0].score,
                    root_state.players[1].score,
                    EvalMode::Normal,
                    None,
                    None,
                );

                // NN Evaluation
                let input_vec = state.encode_state(db);
                let mut session = session_arc.lock().unwrap();

                let input_shape = [1, input_vec.len()];

                // Try to create input tensor and run using (shape, vec) which is version-agnostic
                if let Ok(input_tensor) = ort::value::Value::from_array((input_shape, input_vec)) {
                    if let Ok(outputs) = session.run(ort::inputs![input_tensor]) {
                        // Try to get value output. AlphaNet has 'output_1' or index 1
                        let val_opt = outputs.get("output_1").or_else(|| outputs.get("value"));

                        if let Some(v_val) = val_opt {
                            if let Ok((_, v_slice)) = v_val.try_extract_tensor::<f32>() {
                                let nn_val = v_slice[0];
                                let nn_norm = (nn_val * 0.5 + 0.5).clamp(0.0, 1.0) as f32;
                                return h_val * (1.0 - neural_weight) + nn_norm * neural_weight;
                            }
                        } else if outputs.len() > 1 {
                            // Fallback to index if names missing
                            if let Ok((_, v_slice)) = outputs[1].try_extract_tensor::<f32>() {
                                let nn_val = v_slice[0];
                                let nn_norm = (nn_val * 0.5 + 0.5).clamp(0.0, 1.0) as f32;
                                return h_val * (1.0 - neural_weight) + nn_norm * neural_weight;
                            }
                        }
                    }
                }

                h_val
            },
        )
    }
}
