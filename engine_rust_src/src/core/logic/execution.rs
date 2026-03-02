use crate::core::logic::{GameState, CardDatabase, Phase, ACTION_SPACE};
use crate::core::mcts::{MCTS, SearchHorizon};
use crate::core::heuristics::{Heuristic, OriginalHeuristic, LegacyHeuristic, SimpleHeuristic, EvalMode};
use rand::prelude::*;
use rand_pcg::Pcg64;
use smallvec::SmallVec;



impl GameState {
    pub fn step_opponent(&mut self, db: &CardDatabase) {
         // Simple Random Opponent Logic
         let mut actions = SmallVec::<[i32; 64]>::new();
         self.generate_legal_actions(db, self.current_player as usize, &mut actions);

         let action = if !actions.is_empty() {
             let mut rng = Pcg64::from_os_rng();
             *actions.choose(&mut rng).unwrap()
         } else { 0 };

         let _ = self.step(db, action);
    }

    pub fn step_opponent_mcts(&mut self, db: &CardDatabase, sims: usize, heuristic: &dyn Heuristic) {
        let mcts = MCTS::new();
        let stats = mcts.search_parallel_mode(self, db, sims, 0.0, SearchHorizon::GameEnd(), EvalMode::Blind, heuristic);

        let action = if !stats.is_empty() {
            stats[0].0
        } else {
            // Fallback for tricky phases like RPS if MCTS returns nothing
            let mut legal: SmallVec<[i32; 32]> = SmallVec::new();
            self.generate_legal_actions(db, self.current_player as usize, &mut legal);
            if !legal.is_empty() {
                 let mut rng = Pcg64::from_os_rng();
                 *legal.choose(&mut rng).unwrap()
            } else {
                0
            }
        };

        if action != 0 {
            let _ = self.step(db, action);
        }
    }

    pub fn step_opponent_greedy(&mut self, db: &CardDatabase, heuristic: &dyn Heuristic) {
        let action = self.get_greedy_action(db, self.current_player as usize, heuristic);
        let _ = self.step(db, action);
    }

    pub fn get_mcts_suggestions(&self, db: &CardDatabase, sims: usize, _timeout_sec: f32, horizon: SearchHorizon, eval_mode: EvalMode) -> Vec<(i32, f32, u32)> {
        self.get_mcts_suggestions_ext(db, sims, _timeout_sec, horizon, eval_mode, &OriginalHeuristic::default())
    }

    pub fn get_mcts_suggestions_ext(&self, db: &CardDatabase, sims: usize, _timeout_sec: f32, horizon: SearchHorizon, eval_mode: EvalMode, heuristic: &dyn Heuristic) -> Vec<(i32, f32, u32)> {
        let mcts = MCTS::new();
        mcts.search_parallel_mode(self, db, sims, 0.0, horizon, eval_mode, heuristic)
    }

    pub fn get_greedy_action(&mut self, db: &CardDatabase, p_idx: usize, heuristic: &dyn Heuristic) -> i32 {
        let evals = self.get_greedy_evaluations(db, p_idx, heuristic);
        let mut best_action = 0;
        let mut best_score = f32::NEG_INFINITY;
        for (action, score) in evals {
            if score > best_score {
                best_score = score;
                best_action = action;
            }
        }
        best_action
    }

    pub fn get_greedy_evaluations(&mut self, db: &CardDatabase, p_idx: usize, heuristic: &dyn Heuristic) -> Vec<(i32, f32)> {
        let legal_indices = self.get_legal_action_ids_for_player(db, p_idx);

        if legal_indices.is_empty() { return vec![(0, 0.0)]; }

        let mut evals = Vec::new();
        let opp = 1 - p_idx;
        let p0_score = self.core.players[0].score;
        let p1_score = self.core.players[1].score;
        for &action in legal_indices.iter() {
            let mut state = self.clone();
            state.ui.silent = true; // Always silent for evaluations

            // Randomize opponent hand/deck for evaluation robustness
            let opp_hand_len = state.core.players[opp].hand.len();
            let mut unseen: Vec<i32> = state.core.players[opp].hand.iter().cloned().collect();
            unseen.extend(state.core.players[opp].deck.iter().cloned());
            let mut rng = Pcg64::from_os_rng();
            unseen.shuffle(&mut rng);
            state.core.players[opp].hand = unseen.drain(0..opp_hand_len).collect();
            state.core.players[opp].deck = SmallVec::from_vec(unseen);

            let _ = state.step(db, action);
            let score = heuristic.evaluate(&state, db, p0_score, p1_score, EvalMode::Normal, None, None);
            let my_utility = if p_idx == 0 { score } else { 1.0 - score };
            evals.push((action, my_utility));
        }
        evals
    }

    pub fn play_asymmetric_match(&mut self, db: &CardDatabase, p0_sims: usize, p1_sims: usize, p0_heuristic_id: i32, p1_heuristic_id: i32, horizon: SearchHorizon, p0_rollout: bool, p1_rollout: bool) -> (i32, u32) {
        let h0: Box<dyn Heuristic> = match p0_heuristic_id {
            1 => Box::new(SimpleHeuristic),
            2 => Box::new(LegacyHeuristic::default()),
            _ => Box::new(OriginalHeuristic::default()),
        };
        let h1: Box<dyn Heuristic> = match p1_heuristic_id {
            1 => Box::new(SimpleHeuristic),
            2 => Box::new(LegacyHeuristic::default()),
            _ => Box::new(OriginalHeuristic::default()),
        };

        let mut loop_count = 0;
        while self.phase != Phase::Terminal && loop_count < 2000 {
            loop_count += 1;

            // Determine who needs to make a decision
            let acting_player = match self.phase {
                Phase::Response => {
                    if let Some(pi) = self.interaction_stack.last() {
                        pi.ctx.player_id as u8
                    } else {
                        self.current_player
                    }
                },
                _ => self.current_player,
            };

            let is_interactive = match self.phase {
                Phase::Main | Phase::LiveSet | Phase::MulliganP1 | Phase::MulliganP2 | Phase::LiveResult | Phase::Energy | Phase::Response => true,
                _ => false,
            };

            if is_interactive {
                let p_idx = acting_player as usize;
                let sims = if p_idx == 0 { p0_sims } else { p1_sims };
                let rollout = if p_idx == 0 { p0_rollout } else { p1_rollout };
                let heuristic = if p_idx == 0 { h0.as_ref() } else { h1.as_ref() };

                let action = if sims > 0 {
                    let mut mcts = MCTS::new();
                    let (stats, _) = mcts.search_custom(self, db, sims, 0.0, horizon, heuristic, false, rollout);
                    if !stats.is_empty() { stats[0].0 } else { 0 }
                } else {
                    self.get_greedy_action(db, p_idx, heuristic)
                };

                let _ = self.step(db, action);
            } else {
                let _ = self.step(db, 0);
            }
        }

        (self.get_winner(), self.turn as u32)
    }

    pub fn play_mirror_match(&mut self, db: &CardDatabase, p0_sims: usize, p1_sims: usize, p0_heuristic_id: i32, p1_heuristic_id: i32, horizon: SearchHorizon, enable_rollout: bool) -> (i32, u32) {
        self.play_asymmetric_match(db, p0_sims, p1_sims, p0_heuristic_id, p1_heuristic_id, horizon, enable_rollout, enable_rollout)
    }

    pub fn get_legal_action_ids(&self, db: &CardDatabase) -> Vec<i32> {
        self.get_legal_action_ids_for_player(db, self.current_player as usize)
    }

    pub fn get_legal_action_ids_for_player(&self, db: &CardDatabase, p_idx: usize) -> Vec<i32> {
        let mut actions = SmallVec::<[i32; 64]>::new();
        self.generate_legal_actions(db, p_idx, &mut actions);
        actions.to_vec()
    }

    pub fn get_legal_actions(&self, db: &CardDatabase) -> Vec<bool> {
        let mut mask = vec![false; ACTION_SPACE];
        self.generate_legal_actions(db, self.current_player as usize, mask.as_mut_slice());
        mask
    }

    pub fn get_legal_actions_into(&self, db: &CardDatabase, p_idx: usize, mask: &mut [bool]) {
         self.generate_legal_actions(db, p_idx, mask);
    }

    pub fn get_winner(&self) -> i32 {
        if self.phase != Phase::Terminal { return -1; }
        let p0_lives = self.core.players[0].success_lives.len();
        let p1_lives = self.core.players[1].success_lives.len();

        if p0_lives >= 3 && p1_lives >= 3 { 2 } // Rule 1.2.1.2: Simultaneous 3+ lives is a Draw
        else if p0_lives > p1_lives { 0 }
        else if p1_lives > p0_lives { 1 }
        else { 2 } // Fallback draw for any other equality
    }
}
