//for use with cards_vanilla.json

use crate::core::logic::{GameState, CardDatabase};
use crate::core::enums::Phase;
use crate::core::{ACTION_BASE_HAND, ACTION_BASE_LIVESET};
use crate::core::logic::constants::*;
use std::time::Instant;
use itertools::Itertools;
use serde::{Deserialize, Serialize};
use once_cell::sync::Lazy;
use std::fs;
use rand::seq::IndexedRandom;

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
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct SequencerConfig {
    pub weights: WeightsConfig,
    pub search: SearchConfig,
}

pub static CONFIG: Lazy<SequencerConfig> = Lazy::new(|| {
    let path = "sequencer_config.json";
    if let Ok(content) = fs::read_to_string(path) {
        if let Ok(config) = serde_json::from_str(&content) {
            return config;
        }
    }
    // Default fallback if file missing or invalid
    SequencerConfig {
        weights: WeightsConfig {
            board_presence: 2.0,
            blades: 1.75,
            hearts: 1.5,
            saturation_bonus: 4.0,
            energy_penalty: 0.2,
            live_ev_multiplier: 18.0,
            uncertainty_penalty_pow: 1.2,
            liveset_placement_bonus: 6.0,
        },
        search: SearchConfig {
            max_dfs_depth: 10,
            mc_trials: 100,
        },
    }
});

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
            let (ls_actions, _, _) = TurnSequencer::find_best_liveset_selection_internal(&sim_state, &self.db);
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
    /// Returns a list of (ActionID, Total, Board, Live) for all legal actions,
    /// the best overall sequence, the total nodes, and the best score breakdown.
    pub fn plan_full_turn(state: &GameState, db: &CardDatabase) -> (Vec<(i32, f32, f32, f32)>, Vec<i32>, usize, (f32, f32)) {
        let mut evaluations = Vec::new();
        let mut best_overall_seq = Vec::new();
        let mut best_overall_val = -1.0;
        let mut best_overall_breakdown = (0.0, 0.0);
        let mut total_nodes = 0;

        let p_idx = state.current_player as usize;
        let legal_ids = state.get_legal_action_ids(db);

        // Filter out PASS action (0) - we want to find sequences that play cards, not pass immediately
        let play_actions: Vec<i32> = legal_ids.iter().copied().filter(|&a| a != ACTION_BASE_PASS).collect();

        // Also consider the option of passing (ending main phase immediately)
        let mut pass_state = state.clone();
        pass_state.ui.silent = true;
        if pass_state.step(db, ACTION_BASE_PASS).is_ok() {
            let (board_score, live_ev) = Self::evaluate_state_for_player(&pass_state, db, p_idx);
            let pass_val = board_score + live_ev;
            evaluations.push((ACTION_BASE_PASS, pass_val, board_score, live_ev));

            if pass_val > best_overall_val {
                best_overall_val = pass_val;
                best_overall_seq = vec![ACTION_BASE_PASS];
                best_overall_breakdown = (board_score, live_ev);
            }
        }

        for &action in &play_actions {
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            if sim_state.step(db, action).is_ok() {
                let mut current_seq = vec![action];
                let mut best_seq = vec![action];
                let mut best_val = -1.0;
                let mut best_breakdown = (0.0, 0.0);

                // Continue DFS from this action until turn end
                Self::dfs_turn(
                    &mut sim_state,
                    db,
                    p_idx,
                    &mut current_seq,
                    &mut best_seq,
                    &mut best_val,
                    &mut best_breakdown,
                    &mut total_nodes,
                );

                evaluations.push((action, best_val, best_breakdown.0, best_breakdown.1));

                if best_val > best_overall_val {
                    best_overall_val = best_val;
                    best_overall_seq = best_seq;
                    best_overall_breakdown = best_breakdown;
                }
            } else {
                evaluations.push((action, -1.0, 0.0, 0.0));
            }
        }

        (evaluations, best_overall_seq, total_nodes, best_overall_breakdown)
    }

    /// Compatibility wrapper for the rest of the engine (e.g. MCTS and Heuristics)
    pub fn find_best_main_sequence(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        let (evals, seq, nodes, _) = Self::plan_full_turn(state, db);
        (seq, evals.len(), nodes as u128)
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
        let (evals, seq, nodes, breakdown) = Self::plan_full_turn(state, db);
        let duration = start.elapsed().as_secs_f32();
        (evals, seq, nodes, duration, breakdown)
    }
    pub fn find_best_liveset_selection(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        Self::find_best_liveset_selection_internal(state, db)
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

        // If we are still in Main, we can either play more members OR stop and go to LiveSet
        if state.phase == Phase::Main {
            // Option B: Continue playing members FIRST (before evaluating)
            // This ensures we explore card plays before deciding to pass
            if current_seq.len() < CONFIG.search.max_dfs_depth { // User-defined depth
                let p_idx = state.current_player as usize;
                let hand_len = state.players[p_idx].hand.len();

                for h_idx in 0..hand_len {
                    let s0_empty = state.players[p_idx].stage[0] == -1;
                    let s2_empty = state.players[p_idx].stage[2] == -1;
                    let skip_s2 = s0_empty && s2_empty;

                    for slot in 0..STAGE_SLOT_COUNT {
                        if slot == 2 && skip_s2 { continue; }
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

            // Option A: Stop Main and score the resulting post-main state for the original player.
            let mut stop_state = state.clone();
            stop_state.ui.silent = true;
            let _ = stop_state.step(db, ACTION_BASE_PASS);
            let (board_score, live_ev) = Self::evaluate_state_for_player(&stop_state, db, root_player);
            let current_val = board_score + live_ev;

            // Only update best_seq if we have actions or if this is a better score
            if current_val > *best_val || (!current_seq.is_empty() && current_val >= *best_val) {
                *best_val = current_val;
                *best_seq = current_seq.clone();
                *best_breakdown = (board_score, live_ev);
            }
        } else if state.phase == Phase::LiveSet {
            // In LiveSet, we use a simpler combination search
            let (ls_actions, _, _) = Self::find_best_liveset_selection(state, db);
            let mut final_state = state.clone();
            for &act in &ls_actions {
                let _ = final_state.step(db, act);
            }
            let (board_score, live_ev) = Self::evaluate_state_for_player(&final_state, db, root_player);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_breakdown = (board_score, live_ev);
                let mut full_seq = current_seq.clone();
                full_seq.extend(ls_actions);
                *best_seq = full_seq;
            }
        } else {
            // Other phases: just evaluate
            let (board_score, live_ev) = Self::evaluate_state_for_player(state, db, root_player);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_breakdown = (board_score, live_ev);
                *best_seq = current_seq.clone();
            }
        }
    }

    fn evaluate_members_only(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
        let mut score = 0.0;
        let mut filled_slots = 0;
        for i in 0..3 {
            let cid = state.players[p_idx].stage[i];
            if cid >= 0 {
                filled_slots += 1;
                // Board Presence Bonus: Higher per-slot value to reward fielding
                score += CONFIG.weights.board_presence;

                if let Some(m) = db.get_member(cid) {
                    // Blades (Yell) is still very important for scoring later
                    score += m.blades as f32 * CONFIG.weights.blades;
                    // Hearts directly satisfy live requirements
                    score += m.hearts.iter().sum::<u8>() as f32 * CONFIG.weights.hearts;
                }
            }
        }

        // Super-linear saturation bonus
        if filled_slots == 3 {
            score += CONFIG.weights.saturation_bonus;
        }

        // --- PENALIZE ENERGY HOARDING ---
        let untapped = state.players[p_idx].energy_zone.len() - state.players[p_idx].tapped_energy_count() as usize;
        score -= untapped as f32 * CONFIG.weights.energy_penalty;

        score
    }

    /// Selects the optimal Live Set cards using Monte Carlo success probability.
    fn find_best_liveset_selection_internal(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
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

        let pick_count = hand_lives.len().min(empty_slots);

        let mut best_actions = Vec::new();
        let mut best_ev = -1.0;

        // Exhaustive combination search for Live Sets and Member Plays
        for combo_size in 0..=pick_count {
            for live_combo in hand_lives.iter().combinations(combo_size) {
                let mut actions = Vec::new();
                let mut sim_state = state.clone();
                sim_state.ui.silent = true;

                let mut combo_indices: Vec<usize> = live_combo.iter().map(|&i| *i).collect();
                combo_indices.sort_by(|a: &usize, b: &usize| b.cmp(a)); // Sort descending for index stability

                for &h_idx in &combo_indices {
                    let action = ACTION_BASE_LIVESET + (h_idx as i32);
                    actions.push(action);
                    let _ = sim_state.step(db, action);
                }

                let ev_score = Self::evaluate_live_zone_score(&sim_state, db, p_idx);
                let score_with_bonus = ev_score + (live_combo.len() as f32 * CONFIG.weights.liveset_placement_bonus);

                if score_with_bonus > best_ev {
                    best_ev = score_with_bonus;
                    best_actions = actions;
                }
            }
        }

        (best_actions, 0, (best_ev * 1000.0) as u128)
    }

    fn evaluate_state(state: &GameState, db: &CardDatabase) -> (f32, f32) {
        Self::evaluate_state_internal(state, db)
    }

    /// Internal evaluation function (public for MCTS use)
    fn evaluate_state_internal(state: &GameState, db: &CardDatabase) -> (f32, f32) {
        Self::evaluate_state_for_player(state, db, state.current_player as usize)
    }

    fn evaluate_state_for_player(state: &GameState, db: &CardDatabase, p_idx: usize) -> (f32, f32) {
        let live_score_ev = Self::predict_best_liveset_score(state, db, p_idx);
        let live_ev = live_score_ev * CONFIG.weights.live_ev_multiplier;

        let board_score = Self::evaluate_members_only(state, db, p_idx);

        (board_score, live_ev)
    }

    fn evaluate_live_zone_score(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
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
                Self::live_card_expected_value(
                    live,
                    db,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                )
            })
            .sum()
    }

    fn predict_best_liveset_score(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
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
                Self::live_card_expected_value(
                    live,
                    db,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
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
                Self::live_card_expected_value(
                    live,
                    db,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                )
            })
            .collect();

        hand_live_values.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
        total += hand_live_values.into_iter().take(empty_slots).sum::<f32>();
        total
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
        use crate::core::heuristics::calculate_live_success_prob;

        let prob = if db.is_vanilla {
            calculate_live_success_prob(live, board_hearts, expected_yell_hearts, heart_reductions)
                .min(1.0)
        } else {
            0.5
        };

        prob.powf(CONFIG.weights.uncertainty_penalty_pow) * live.score as f32
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
