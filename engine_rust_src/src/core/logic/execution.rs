use crate::core::heuristics::{
    EvalMode, Heuristic, OriginalHeuristic, SimpleHeuristic,
};
use crate::core::logic::{CardDatabase, GameState, Phase, ACTION_SPACE};
use crate::core::mcts::{SearchHorizon, MCTS};
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
        } else {
            0
        };

        let _ = self.step(db, action);
    }

    pub fn step_opponent_mcts(
        &mut self,
        db: &CardDatabase,
        sims: usize,
        heuristic: &dyn Heuristic,
    ) {
        let mcts = MCTS::new();
        let stats = mcts.search_parallel_mode(
            self,
            db,
            sims,
            0.0,
            SearchHorizon::GameEnd(),
            EvalMode::Blind,
            heuristic,
        );

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

    fn choose_phase_aware_action(&self, db: &CardDatabase) -> i32 {
        let legal = self.get_legal_action_ids(db);
        if legal.is_empty() {
            return 0;
        }

        match self.phase {
            Phase::Response => {
                if legal.contains(&0) {
                    0
                } else {
                    legal[0]
                }
            }
            Phase::MulliganP1 | Phase::MulliganP2 => 0,
            Phase::Energy | Phase::LiveResult => legal[0],
            Phase::Rps => {
                // Determine RPS choice randomly to ensure fairness and avoid predictability.
                let mut rng = Pcg64::from_os_rng();
                *legal.choose(&mut rng).unwrap_or(&0)
            }
            Phase::TurnChoice => legal[0],
            _ => legal[0],
        }
    }

    /// Execute opponent's full turn using TurnSequencer planner (vanilla mode AI).
    /// This uses the success-count-first heuristic optimized for lower turn counts without the turn limit.
    pub fn step_opponent_turnseq(&mut self, db: &CardDatabase) {
        use crate::core::logic::turn_sequencer::TurnSequencer;

        match self.phase {
            Phase::Main => {
                let initial_player = self.current_player;
                let (action_seq, _, _, _) = TurnSequencer::plan_full_turn(self, db);

                let legal_actions = self.get_legal_action_ids(db);
                for &action in &action_seq {
                    if self.is_terminal()
                        || self.phase != Phase::Main
                        || self.current_player != initial_player
                    {
                        break;
                    }
                    if !legal_actions.contains(&action) {
                        break;
                    }
                    if self.step(db, action).is_err() {
                        break;
                    }
                }

                // Only pass if we are still the same player — avoid accidentally
                // consuming the human player's main phase when auto_step has already
                // advanced the game past the AI's pass.
                if self.phase == Phase::Main && self.current_player == initial_player {
                    let _ = self.step(db, 0);
                }
            }
            Phase::Rps => {
                // RPS is meant to allow draws. Do not filter out the opponent's
                // previous choice here, or the AI can never mirror the human and
                // the "second shot" rematch loop can never happen.
                let legal = self.get_legal_action_ids(db);
                let action = if legal.is_empty() {
                    self.choose_phase_aware_action(db)
                } else {
                    let mut rng = Pcg64::from_os_rng();
                    *legal.choose(&mut rng).unwrap()
                };

                let _ = self.step(db, action);
            }
            Phase::LiveSet => {
                let initial_player = self.current_player;
                let (action_seq, _, _) = TurnSequencer::find_best_liveset_selection(self, db);

                let legal_actions = self.get_legal_action_ids(db);
                for &action in &action_seq {
                    if self.is_terminal()
                        || self.phase != Phase::LiveSet
                        || self.current_player != initial_player
                    {
                        break;
                    }
                    if !legal_actions.contains(&action) {
                        break;
                    }
                    if self.step(db, action).is_err() {
                        break;
                    }
                }

                if self.phase == Phase::LiveSet && self.current_player == initial_player {
                    let _ = self.step(db, 0);
                }
            }
            _ => {
                let action = self.choose_phase_aware_action(db);
                let _ = self.step(db, action);
            }
        }
    }

    pub fn get_mcts_suggestions(
        &self,
        db: &CardDatabase,
        sims: usize,
        _timeout_sec: f32,
        horizon: SearchHorizon,
        eval_mode: EvalMode,
    ) -> Vec<(i32, f32, u32)> {
        self.get_mcts_suggestions_ext(
            db,
            sims,
            _timeout_sec,
            horizon,
            eval_mode,
            &OriginalHeuristic::default(),
        )
    }

    pub fn get_mcts_suggestions_ext(
        &self,
        db: &CardDatabase,
        sims: usize,
        _timeout_sec: f32,
        horizon: SearchHorizon,
        eval_mode: EvalMode,
        heuristic: &dyn Heuristic,
    ) -> Vec<(i32, f32, u32)> {
        let mcts = MCTS::new();
        mcts.search_parallel_mode(self, db, sims, 0.0, horizon, eval_mode, heuristic)
    }

    pub fn get_greedy_action(
        &mut self,
        db: &CardDatabase,
        p_idx: usize,
        heuristic: &dyn Heuristic,
    ) -> i32 {
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

    pub fn get_greedy_evaluations(
        &mut self,
        db: &CardDatabase,
        p_idx: usize,
        heuristic: &dyn Heuristic,
    ) -> Vec<(i32, f32)> {
        let legal_indices = self.get_legal_action_ids_for_player(db, p_idx);

        if legal_indices.is_empty() {
            return vec![(0, 0.0)];
        }

        let mut evals = Vec::new();
        let opp = 1 - p_idx;
        let p0_score = self.core.players[0].score;
        let p1_score = self.core.players[1].score;
        let mut base_state = self.clone();
        base_state.ui.silent = true; // Always silent for evaluations
        let mut state = base_state.clone();
        for &action in legal_indices.iter() {
            state.copy_from(&base_state);
            // State already silented

            // Randomize opponent hand/deck for evaluation robustness
            let opp_hand_len = state.players[opp].hand.len();
            let mut unseen: Vec<i32> = state.players[opp].hand.iter().cloned().collect();
            unseen.extend(state.players[opp].deck.iter().cloned());
            let mut rng = Pcg64::from_os_rng();
            unseen.shuffle(&mut rng);
            state.players[opp].hand = unseen.drain(0..opp_hand_len).collect();
            state.players[opp].deck = SmallVec::from_vec(unseen);

            let _ = state.step(db, action);
            let score =
                heuristic.evaluate(&state, db, p0_score, p1_score, EvalMode::Normal, None, None);
            let my_utility = if p_idx == 0 { score } else { 1.0 - score };
            evals.push((action, my_utility));
        }
        evals
    }

    pub fn play_asymmetric_match(
        &mut self,
        db: &CardDatabase,
        p0_sims: usize,
        p1_sims: usize,
        p0_heuristic_id: i32,
        p1_heuristic_id: i32,
        horizon: SearchHorizon,
        p0_rollout: bool,
        p1_rollout: bool,
    ) -> (i32, u32) {
        let h0: Box<dyn Heuristic> = match p0_heuristic_id {
            1 => Box::new(SimpleHeuristic),
            _ => Box::new(OriginalHeuristic::default()),
        };
        let h1: Box<dyn Heuristic> = match p1_heuristic_id {
            1 => Box::new(SimpleHeuristic),
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
                }
                _ => self.current_player,
            };

            let is_interactive = match self.phase {
                Phase::Main
                | Phase::LiveSet
                | Phase::MulliganP1
                | Phase::MulliganP2
                | Phase::LiveResult
                | Phase::Energy
                | Phase::Response => true,
                _ => false,
            };

            if is_interactive {
                let p_idx = acting_player as usize;
                let sims = if p_idx == 0 { p0_sims } else { p1_sims };
                let rollout = if p_idx == 0 { p0_rollout } else { p1_rollout };
                let heuristic = if p_idx == 0 { h0.as_ref() } else { h1.as_ref() };

                let action = if sims > 0 {
                    let mut mcts = MCTS::new();
                    let (stats, _) =
                        mcts.search_custom(self, db, sims, 0.0, horizon, heuristic, false, rollout);
                    if !stats.is_empty() {
                        stats[0].0
                    } else {
                        0
                    }
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

    pub fn play_mirror_match(
        &mut self,
        db: &CardDatabase,
        p0_sims: usize,
        p1_sims: usize,
        p0_heuristic_id: i32,
        p1_heuristic_id: i32,
        horizon: SearchHorizon,
        enable_rollout: bool,
    ) -> (i32, u32) {
        self.play_asymmetric_match(
            db,
            p0_sims,
            p1_sims,
            p0_heuristic_id,
            p1_heuristic_id,
            horizon,
            enable_rollout,
            enable_rollout,
        )
    }

    pub fn get_legal_action_ids(&self, db: &CardDatabase) -> Vec<i32> {
        self.get_legal_action_ids_for_player(db, self.current_player as usize)
    }

    pub fn get_legal_action_ids_for_player(&self, db: &CardDatabase, p_idx: usize) -> Vec<i32> {
        let mut actions = SmallVec::<[i32; 64]>::new();
        self.generate_legal_actions(db, p_idx, &mut actions);
        actions.sort_unstable();
        actions.dedup();
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
        if self.phase != Phase::Terminal {
            return -1;
        }
        let p0_lives = self.core.players[0].success_lives.len();
        let p1_lives = self.core.players[1].success_lives.len();

        if p0_lives >= 3 && p1_lives >= 3 {
            2
        }
        // Rule 1.2.1.2: Simultaneous 3+ lives is a Draw
        else if p0_lives > p1_lives {
            0
        } else if p1_lives > p0_lives {
            1
        } else {
            2
        } // Fallback draw for any other equality
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_helpers::create_test_db;

    #[test]
    fn turnseq_ai_handles_rps_with_single_choice() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.phase = Phase::Rps;
        state.current_player = 1;
        state.rps_choices = [1, -1];

        state.step_opponent_turnseq(&db);

        // The AI must take a legal RPS action. That may either resolve the phase
        // immediately or produce a valid draw reset if both players matched.
        let resolved_rps = state.phase == Phase::TurnChoice;
        let drew_rps = state.phase == Phase::Rps && state.rps_choices == [-1, -1];

        assert!(
            resolved_rps || drew_rps,
            "AI should either resolve RPS or trigger a legal draw reset; phase={:?}, choices={:?}",
            state.phase,
            state.rps_choices
        );
    }

    #[test]
    fn turnseq_ai_advances_turn_choice_into_mulligan() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.phase = Phase::TurnChoice;
        state.current_player = 1;

        state.step_opponent_turnseq(&db);

        assert_eq!(state.phase, Phase::MulliganP1);
        assert_eq!(state.first_player, 1);
        assert_eq!(state.current_player, 1);

        state.step_opponent_turnseq(&db);

        assert_eq!(state.phase, Phase::MulliganP2);
        assert_eq!(state.current_player, 0);
    }

    #[test]
    fn turnseq_ai_exits_liveset_phase() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.phase = Phase::LiveSet;
        state.first_player = 0;
        state.current_player = 1;
        state.players[1].hand = vec![3000].into();
        state.players[1].live_zone = [-1, -1, -1];

        state.step_opponent_turnseq(&db);

        assert_ne!(state.phase, Phase::LiveSet);
    }

    #[test]
    fn rps_pure_randomness_test() {
        let db = create_test_db();
        let mut choices = std::collections::HashSet::new();

        for _ in 0..100 {
            let mut state = GameState::default();
            state.phase = Phase::Rps;
            state.current_player = 1;
            state.rps_choices = [1, -1]; // Player 0 chose Paper

            let action = state.choose_phase_aware_action(&db);
            let choice = action - crate::core::generated_constants::ACTION_BASE_RPS_P2;
            choices.insert(choice);
        }

        // With 100 trials, the AI should have picked all 3 options (0, 1, 2) eventually.
        assert!(choices.contains(&0), "AI should pick Rock");
        assert!(choices.contains(&1), "AI should pick Paper (Draw)");
        assert!(choices.contains(&2), "AI should pick Scissors");
        assert_eq!(choices.len(), 3, "AI should pick all RPS options randomly");
    }
}
