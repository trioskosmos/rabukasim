use rand::SeedableRng;
use rand::seq::SliceRandom;
use rand_pcg::Pcg64;
use smallvec::SmallVec;

use crate::core::enums::*;
use super::card_db::*;
use super::player::*;
use super::state::*;

impl GameState {
    pub fn setup_turn_log(&mut self) {
        if self.ui.silent {
            return;
        }
        let p_idx = self.current_player;
        self.log(format!("=== Player {}'s Turn ===", p_idx));
    }

    pub fn initialize_game(
        &mut self,
        p0_deck: Vec<i32>,
        p1_deck: Vec<i32>,
        p0_energy: Vec<i32>,
        p1_energy: Vec<i32>,
        p0_lives: Vec<i32>,
        p1_lives: Vec<i32>,
    ) {
        self.initialize_game_with_seed(
            p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives, None,
        );
    }

    pub fn copy_from(&mut self, other: &GameState) {
        self.core.players[0].copy_from(&other.core.players[0]);
        self.core.players[1].copy_from(&other.core.players[1]);
        self.core.current_player = other.core.current_player;
        self.core.first_player = other.core.first_player;
        self.core.phase = other.core.phase;
        self.core.prev_phase = other.core.prev_phase;
        self.core.prev_card_id = other.core.prev_card_id;
        self.core.turn = other.core.turn;
        self.core.trigger_depth = other.core.trigger_depth;
        self.core.live_set_pending_draws = other.core.live_set_pending_draws;

        // Interaction stack and trigger queue are expensive but necessary
        if other.core.interaction_stack.is_empty() {
            self.core.interaction_stack.clear();
        } else {
            self.core.interaction_stack.clear();
            self.core
                .interaction_stack
                .extend_from_slice(&other.core.interaction_stack);
        }

        if other.core.trigger_queue.is_empty() {
            self.core.trigger_queue.clear();
        } else {
            self.core.trigger_queue.clear();
            self.core
                .trigger_queue
                .extend(other.core.trigger_queue.iter().cloned());
        }

        self.core.live_result_selection_pending = other.core.live_result_selection_pending;
        self.core.live_result_triggers_done = other.core.live_result_triggers_done;
        self.core.live_start_triggers_done = other.core.live_start_triggers_done;
        self.core.live_result_processed_mask = other.core.live_result_processed_mask;
        self.core.live_start_processed_mask = other.core.live_start_processed_mask;
        self.core.live_success_processed_mask = other.core.live_success_processed_mask;
        self.core.performance_reveals_done = other.core.performance_reveals_done;
        self.core.performance_yell_done = other.core.performance_yell_done;
        self.core.rps_choices = other.core.rps_choices;
        self.core.obtained_success_live = other.core.obtained_success_live;

        // UI state - only clone if not silent or if specifically needed
        self.ui.silent = other.ui.silent;
        if !self.ui.silent {
            self.ui.rule_log = other.ui.rule_log.clone();
            self.core.turn_history = other.core.turn_history.clone();
        } else {
            self.ui.rule_log = None;
            self.core.turn_history = None;
        }

        // Debug state - only clone if debug mode is active
        self.debug.debug_mode = other.debug.debug_mode;
        self.debug.debug_ignore_conditions = other.debug.debug_ignore_conditions;
        if self.debug.debug_mode {
            self.debug.executed_opcodes = other.debug.executed_opcodes.clone();
            self.debug.bypassed_conditions = other.debug.bypassed_conditions.clone();
        } else {
            self.debug.executed_opcodes = None;
            self.debug.bypassed_conditions = None;
        }
    }

    pub fn initialize_game_with_seed(
        &mut self,
        p0_deck: Vec<i32>,
        p1_deck: Vec<i32>,
        p0_energy: Vec<i32>,
        p1_energy: Vec<i32>,
        p0_lives: Vec<i32>,
        p1_lives: Vec<i32>,
        seed: Option<u64>,
    ) {
        // Rule 6.1.1.1: Main Deck contains 48 member cards and 12 live cards (total 60)
        // Rule 6.2.1.2: Place main deck and shuffle.
        let mut d0 = Vec::with_capacity(60);
        d0.extend(p0_deck);
        d0.extend(p0_lives.clone());

        let mut d1 = Vec::with_capacity(60);
        d1.extend(p1_deck);
        d1.extend(p1_lives.clone());

        let mut rng = match seed {
            Some(s) => Pcg64::seed_from_u64(s),
            None => Pcg64::from_os_rng(),
        };

        self.core.players[0].initial_deck = SmallVec::from_vec(d0.clone());
        self.core.players[1].initial_deck = SmallVec::from_vec(d1.clone());

        d0.shuffle(&mut rng);
        d1.shuffle(&mut rng);

        self.core.players[0].deck = SmallVec::from_vec(d0);
        self.core.players[1].deck = SmallVec::from_vec(d1);

        // Rule 6.2.1.3: Place energy deck.
        self.core.players[0].energy_deck = SmallVec::from_vec(p0_energy);
        self.core.players[1].energy_deck = SmallVec::from_vec(p1_energy);
        self.core.players[0].energy_deck.shuffle(&mut rng);
        self.core.players[1].energy_deck.shuffle(&mut rng);

        // Reset state
        for i in 0..2 {
            self.core.players[i].hand.clear();
            self.core.players[i].energy_zone.clear();
            self.core.players[i].tapped_energy_mask = 0;
            self.core.players[i].stage = [-1; 3];
            self.core.players[i].set_flag(PlayerState::OFFSET_TAPPED, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_TAPPED + 1, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_TAPPED + 2, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_MOVED, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_MOVED + 1, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_MOVED + 2, false);
            self.core.players[i].discard.clear();
            self.core.players[i].success_lives.clear();
            self.core.players[i].mulligan_selection = 0;
            self.core.players[i].hand_added_turn.clear();
            self.core.players[i].live_zone = [-1; 3];
            for j in 0..3 {
                self.core.players[i].set_revealed(j, false);
            }
        }

        // Rule 6.2.1.5: Both players draw 6 cards.
        self.draw_cards(0, 6);
        self.draw_cards(1, 6);

        // Rule 6.2.1.7: 3 cards from Energy Deck to Energy Zone.
        for i in 0..2 {
            for _ in 0..3 {
                if let Some(cid) = self.core.players[i].energy_deck.pop() {
                        self.core.players[i].push_energy_card(cid, false);
                }
            }
        }

        self.phase = Phase::Rps;
        self.current_player = 0;
        self.rps_choices = [-1; 2];
        self.turn = 1;
        self.ui.rule_log = None;
        self.turn_history = None;
        self.debug.executed_opcodes = None;
        self.debug.bypassed_conditions = None;
        self.debug.trace_log.clear();
        self.ui.performance_results.clear();
        self.ui.last_performance_results.clear();
        self.ui.performance_history.clear();
        self.live_set_pending_draws = [0, 0];
        self.live_result_processed_mask = [0, 0];
        self.setup_turn_log();
    }

    pub fn register_played_member(&mut self, p_idx: usize, card_id: i32, db: &CardDatabase) {
        if let Some(m) = db.get_member(card_id as i32) {
            for &gid in &m.groups {
                if gid > 0 && gid <= 32 {
                    self.core.players[p_idx].played_group_mask |= 1 << (gid - 1);
                }
            }
        }
        self.core.players[p_idx].play_count_this_turn += 1;
    }

    fn _fisher_yates_shuffle(&mut self, player_idx: usize) {
        self.core.players[player_idx]
            .deck
            .shuffle(&mut self.core.rng);
    }
}
