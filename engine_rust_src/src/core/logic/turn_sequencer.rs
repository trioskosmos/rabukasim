use crate::core::logic::{GameState, CardDatabase};
use crate::core::enums::Phase;
use crate::core::{ACTION_BASE_HAND, ACTION_BASE_LIVESET};
use std::time::Instant;
use itertools::Itertools;

pub struct TurnSequencer;

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

        let _p_idx = state.current_player as usize;
        let legal_ids = state.get_legal_action_ids(db);

        for &action in &legal_ids {
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            if sim_state.step(db, action).is_ok() {
                let mut current_seq = vec![action];
                let mut best_seq = vec![action];
                let mut best_val = -1.0;
                let mut best_breakdown = (0.0, 0.0);

                // Continue DFS from this action until turn end
                Self::dfs_turn(&mut sim_state, db, &mut current_seq, &mut best_seq, &mut best_val, &mut best_breakdown, &mut total_nodes);

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
        current_seq: &mut Vec<i32>,
        best_seq: &mut Vec<i32>,
        best_val: &mut f32,
        best_breakdown: &mut (f32, f32),
        total_count: &mut usize,
    ) {
        *total_count += 1;

        // If we are still in Main, we can either play more members OR stop and go to LiveSet
        if state.phase == Phase::Main {
            // Option A: Stop Main and evaluate LiveSet result
            let (board_score, live_ev) = Self::evaluate_state(state, db);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_seq = current_seq.clone();
                *best_breakdown = (board_score, live_ev);
            }

            // Option B: Continue playing members
            if current_seq.len() < 10 { // Depth safety
                let p_idx = state.current_player as usize;
                let hand_len = state.players[p_idx].hand.len();

                for h_idx in 0..hand_len {
                    let s0_empty = state.players[p_idx].stage[0] == -1;
                    let s2_empty = state.players[p_idx].stage[2] == -1;
                    let skip_s2 = s0_empty && s2_empty;

                    for slot in 0..3 {
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
                                    Self::dfs_turn(&mut next_state, db, current_seq, best_seq, best_val, best_breakdown, total_count);
                                    current_seq.pop();
                                }
                            }
                        }
                    }
                }
            }
        } else if state.phase == Phase::LiveSet {
            // In LiveSet, we use a simpler combination search
            let (ls_actions, _, _) = Self::find_best_liveset_selection(state, db);
            let mut final_state = state.clone();
            for &act in &ls_actions {
                let _ = final_state.step(db, act);
            }
            let (board_score, live_ev) = Self::evaluate_state(&final_state, db);
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
            let (board_score, live_ev) = Self::evaluate_state(state, db);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_breakdown = (board_score, live_ev);
                *best_seq = current_seq.clone();
            }
        }
    }

    fn evaluate_members_only(state: &GameState, db: &CardDatabase) -> f32 {
        let p_idx = state.current_player as usize;
        let mut score = 0.0;
        let mut filled_slots = 0;
        for i in 0..3 {
            let cid = state.players[p_idx].stage[i];
            if cid >= 0 {
                filled_slots += 1;
                // Board Presence Bonus: Higher per-slot value to reward fielding
                score += 1.5;

                if let Some(m) = db.get_member(cid) {
                    // Blades (Yell) is still very important for scoring later
                    score += m.blades as f32 * 1.5;
                    // Hearts directly satisfy live requirements — weight raised to match importance
                    score += m.hearts.iter().sum::<u8>() as f32 * 1.0;
                }
            }
        }

        // Super-linear saturation bonus: filling all 3 slots is disproportionately valuable
        // because it maximizes hearts available for live judgement
        if filled_slots == 3 {
            score += 3.0;
        }

        // --- AGGRESSIVE: PENALIZE ENERGY HOARDING ---
        // In a stochastic game, saving energy for "later" is high variance.
        // We want the AI to play its hand NOW if it has valid slots.
        let untapped = state.players[p_idx].energy_zone.len() - state.players[p_idx].tapped_energy_count() as usize;
        score -= untapped as f32 * 0.5; // Strong penalty per untapped energy to force spending.

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

        if hand_lives.is_empty() { return (Vec::new(), 0, 0); }

        let empty_slots = state.players[p_idx].live_zone.iter().filter(|&&cid| cid == -1).count();
        let pick_count = hand_lives.len().min(empty_slots);

        let mut best_actions = Vec::new();
        let mut best_ev = -1.0;

        // Exhaustive combination search for Live Sets and Member Plays
        for combo_size in 0..=pick_count {
            for live_combo in hand_lives.iter().combinations(combo_size) {
                let mut actions = Vec::new();
                let mut sim_state = state.clone();
                sim_state.ui.silent = true;

                let mut combo_indices: Vec<usize> = live_combo.iter().map(|&&i| i).collect();
                combo_indices.sort_by(|a: &usize, b: &usize| b.cmp(a)); // Sort descending for index stability

                for &h_idx in &combo_indices {
                    let action = ACTION_BASE_LIVESET + (h_idx as i32);
                    actions.push(action);
                    let _ = sim_state.step(db, action);
                }

                // Optimization: In vanilla mode, we usually play members AFTER setting lives.
                // We don't need to recursively call find_best_main_sequence deep inside combinations
                // for a full evaluation. Instead, we predict the best possible score from members.
                let ev_score = Self::predict_best_liveset_score(&sim_state, db);
                // Tiny bonus for each live card set to encourage using slots
                let score_with_bonus = ev_score + (live_combo.len() as f32 * 0.01);

                if score_with_bonus > best_ev {
                    best_ev = score_with_bonus;
                    best_actions = actions;
                }
            }
        }

        (best_actions, 0, (best_ev * 1000.0) as u128)
    }

    fn evaluate_state(state: &GameState, db: &CardDatabase) -> (f32, f32) {
        let _p_idx = state.current_player as usize;

        // --- 1. Scoring Potential (The Primary Driver) ---
        // Amplified multiplier: live success is THE way to win.
        let live_score_ev = Self::predict_best_liveset_score(state, db);
        let live_ev = live_score_ev * 15.0;

        // --- 2. Board State (Secondary) ---
        let board_score = Self::evaluate_members_only(state, db);

        (board_score, live_ev)
    }

    /// Quickly estimates the best possible Live result for the current board without a full combo search.
    fn predict_best_liveset_score(state: &GameState, db: &CardDatabase) -> f32 {
        let p_idx = state.current_player as usize;
        let lives_in_hand: Vec<i32> = state.players[p_idx].hand.iter()
            .cloned()
            .filter(|&cid| db.get_live(cid).is_some())
            .collect();

        if lives_in_hand.is_empty() { return 0.0; }

        let mut best_total_ev = 0.0;
        let empty_slots: Vec<usize> = (0..3).filter(|&i| state.players[p_idx].live_zone[i] == -1).collect();

        if empty_slots.is_empty() { return 0.0; }

        // --- PRE-CALC HEURISTICS (Shared across slot evaluations) ---
        use crate::core::heuristics::{calculate_deck_expectations, calculate_live_success_prob};
        let deck_stats = calculate_deck_expectations(&state.players[p_idx].deck, db);
        let yell_count = state.get_total_blades(p_idx, db, 0);
        let board_hearts = state.get_total_hearts(p_idx, db, 0).to_array().map(|v| v as u32);
        let expected_yell_hearts: Vec<f32> = deck_stats.avg_hearts.iter().map(|&h| h * yell_count as f32).collect();
        let heart_reductions = state.players[p_idx].heart_req_reductions.to_array();

        // Greedy estimation: for each empty slot, what is the best card in hand?
        let mut available_lives = lives_in_hand.clone();
        for _slot_idx in &empty_slots {
            let mut best_slot_ev = 0.0;
            let mut best_l_idx = None;

            for (l_idx, &cid) in available_lives.iter().enumerate() {
                if let Some(live) = db.get_live(cid) {
                    let prob = if db.is_vanilla {
                        calculate_live_success_prob(
                            live,
                            &board_hearts,
                            &expected_yell_hearts,
                            heart_reductions,
                        ).min(1.0)
                    } else {
                        // Fallback for non-vanilla: just a rough estimate since we're in a heuristic
                        0.5
                    };

                    // Super-linear: punish uncertainty. prob^1.5 makes 90%→0.86, 50%→0.35
                    // This strongly favors lives the AI can almost certainly pass
                    let ev = prob.powf(1.5) * live.score as f32;
                    if ev > best_slot_ev {
                        best_slot_ev = ev;
                        best_l_idx = Some(l_idx);
                    }
                }
            }

            if let Some(idx) = best_l_idx {
                best_total_ev += best_slot_ev;
                available_lives.remove(idx);
            }
        }

        best_total_ev
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
