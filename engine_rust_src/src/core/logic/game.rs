//! # LovecaSim Game State and Orchestration
//!
//! This module defines the `GameState` struct, which is the heart of the engine.
//! It manages players, zones (Hand, Deck, Stage, Energy, Discard), and the turn cycle.
//!
//! ## Key Roles:
//! - **State Management**: Holds 100% of the data needed to represent a point in time in a game.
//! - **Turn Orchestration**: Manages `Phase` transitions (Main, Live, End) and turn switching.
//! - **Rule Enforcement**: Implements high-level game rules (e.g., Playing a member,
//!   starting a Live performance, checking for Live success).
//! - **Rule 10.5.3 (Cleanup)**: Implements the "State Check" logic
//!   (`process_rule_checks`) which handles automatic energy cleanup and score updates.
//!
//! ## State-Action Integrity:
//! The `GameState` is designed to be highly serializable. It works in tandem with
//! the `interpreter` to resolve complex card effects while maintaining state consistency.

use rand::SeedableRng;
// use rand::rngs::SmallRng;
use rand::seq::SliceRandom;
use rand_pcg::Pcg64;
use smallvec::SmallVec;

// use crate::core::*; // UNUSED
use super::card_db::*;
use super::filter::CardFilter;
use super::models::*;
use super::player::*;
use crate::core::enums::*;
// use super::rules::*;
use crate::core::hearts::*;
use crate::core::heuristics::{EvalMode, Heuristic, OriginalHeuristic};
use crate::core::logic::ai_encoding::GameStateEncoding;
use crate::core::logic::handlers::{
    MainPhaseController, MulliganController, ResponseController, TurnController,
    TurnPhaseController,
};
use crate::core::logic::ActionFactory;
use crate::core::mcts::{SearchHorizon, MCTS};

pub use super::state::*;

impl GameState {
    pub(crate) const ACTION_TURN_CHOICE_FIRST: i32 = 5000;
    pub(crate) const ACTION_TURN_CHOICE_SECOND: i32 = 5001;

    // Helper to calculate other slot index for Double Baton (offset 3-8)
    pub(crate) fn get_combo_other_slot(primary_slot: usize, is_next: bool) -> usize {
        if primary_slot == 0 {
            if is_next {
                1
            } else {
                2
            }
        } else if primary_slot == 1 {
            if is_next {
                2
            } else {
                0
            }
        } else {
            if is_next {
                0
            } else {
                1
            }
        }
    }

    pub fn safe_set_mask(&self, mask: &mut [bool], aid: usize) {
        if aid < mask.len() {
            mask[aid] = true;
        } else {
            panic!(
                "[ACTION_OOB] Action ID {} exceeds mask len {} in phase {:?}",
                aid,
                mask.len(),
                self.phase
            );
        }
    }

    pub fn generate_execution_id(&mut self) -> u32 {
        let id = self.ui.next_execution_id;
        self.ui.next_execution_id = self.ui.next_execution_id.wrapping_add(1);
        self.ui.current_execution_id = Some(id);
        id
    }

    pub fn clear_execution_id(&mut self) {
        self.ui.current_execution_id = None;
    }

    pub fn log(&mut self, msg: String) {
        if self.ui.silent {
            return;
        }

        let (turn_prefix, body) = if msg.starts_with("[Turn") {
            if let Some(idx) = msg.find("] ") {
                (msg[..=idx].to_string(), msg[idx + 2..].to_string())
            } else {
                (format!("[Turn {}]", self.turn), msg)
            }
        } else {
            (format!("[Turn {}]", self.turn), msg)
        };

        let full_msg = if let Some(id) = self.ui.current_execution_id {
            format!("{} [ID: {}] {}", turn_prefix, id, body)
        } else {
            format!("{} {}", turn_prefix, body)
        };

        if self.ui.rule_log.is_none() {
            self.ui.rule_log = Some(Vec::with_capacity(32));
        }
        self.ui.rule_log.as_mut().unwrap().push(full_msg);
    }

    pub fn log_rule(&mut self, rule: &str, msg: &str) {
        // Use unified log_event for RULE events
        self.log_event("RULE", msg, -1, -1, self.current_player, Some(rule), true);
    }

    pub fn log_turn_event(
        &mut self,
        event_type: &str,
        source_cid: i32,
        ability_idx: i16,
        player_id: u8,
        description: &str,
    ) {
        if self.ui.silent {
            return;
        }
        let t = self.turn as u32;
        let ph = self.phase;
        if self.core.turn_history.is_none() {
            self.core.turn_history = Some(Vec::with_capacity(64));
        }
        let history = self.core.turn_history.as_mut().unwrap();
        if history.len() > 2000 {
            return;
        } // Safety cap
        history.push(TurnEvent {
            turn: t,
            phase: ph,
            player_id,
            event_type: event_type.to_string(),
            source_cid,
            ability_idx,
            description: description.to_string(),
        });
    }

    /// Unified event logging function that records to both turn_history and optionally rule_log.
    /// This replaces the pattern of calling both log() and log_turn_event() separately.
    ///
    /// # Arguments
    /// * `event_type` - Type of event (e.g., "PLAY", "ACTIVATE", "TRIGGER", "RULE", "EFFECT")
    /// * `description` - Human-readable description of the event
    /// * `source_cid` - Source card ID (or -1 if not applicable)
    /// * `ability_idx` - Ability index (or -1 if not applicable)
    /// * `player_id` - Player who triggered the event
    /// * `rule_ref` - Optional rule reference (e.g., "Rule 7.7.2.1")
    /// * `log_to_rule_log` - If true, also add to rule_log for text-based viewing
    pub fn trace_internal(&mut self, msg: &str) {
        if self.debug.debug_mode {
            let trace_msg = format!("[TRC] {}", msg);
            self.debug.trace_log.push(trace_msg);
        }
    }

    pub fn log_event(
        &mut self,
        event_type: &str,
        description: &str,
        source_cid: i32,
        ability_idx: i16,
        player_id: u8,
        rule_ref: Option<&str>,
        log_to_rule_log: bool,
    ) {
        // Extract values first to avoid borrow conflicts
        let turn = self.turn as u32;
        let phase = self.phase;
        let silent = self.ui.silent;

        // 1. Always add to turn_history (structured data)
        if !silent {
            if self.core.turn_history.is_none() {
                self.core.turn_history = Some(Vec::with_capacity(64));
            }
            let history = self.core.turn_history.as_mut().unwrap();
            if history.len() < 2000 {
                history.push(TurnEvent {
                    turn,
                    phase,
                    player_id,
                    event_type: event_type.to_string(),
                    source_cid,
                    ability_idx,
                    description: description.to_string(),
                });
            }
        }

        // 2. Optionally add to rule_log (text format)
        if log_to_rule_log && !silent {
            let turn_prefix = format!("[Turn {}]", turn);
            let rule_prefix = rule_ref.map(|r| format!("[{}] ", r)).unwrap_or_default();
            let full_msg = format!("{}{}{}", turn_prefix, rule_prefix, description);
            if self.ui.rule_log.is_none() {
                self.ui.rule_log = Some(Vec::with_capacity(32));
            }
            self.ui.rule_log.as_mut().unwrap().push(full_msg);
        }
    }

    pub fn handle_member_leaves_stage(
        &mut self,
        p_idx: usize,
        slot: usize,
        db: &CardDatabase,
        ctx: &AbilityContext,
    ) -> Option<i32> {
        if slot >= 3 {
            return None;
        }
        let cid = self.core.players[p_idx].stage[slot];
        if cid < 0 {
            return None;
        }

        let mut leave_ctx = ctx.clone();
        leave_ctx.source_card_id = cid;
        leave_ctx.area_idx = slot as i16;

        // Trigger OnLeaves
        self.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);

        // Clear slot data (Buffs are attached to member, Energy stays in slot)
        self.core.players[p_idx].stage[slot] = -1;
        self.core.players[p_idx].blade_buffs[slot] = 0;
        self.core.players[p_idx].blade_overrides[slot] = -1;
        self.core.players[p_idx].heart_buffs[slot] = HeartBoard::default();

        // Clear flags
        self.core.players[p_idx].set_tapped(slot, false);
        self.core.players[p_idx].set_moved(slot, false);

        Some(cid as i32)
    }

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
        // Rule: In LL! OCG, starting deck is 60. 12 lives are in that 60.
        // When drawing 6, if you draw a live, you keep it in hand? 
        // No, actually 12 Lives are logically distinct.
        // Looking at 4.6.1: Live Zone is where you put lives.
        // The common interpretation is that of the 60, you MUST have 48/12.
        
        // Fix: To ensure 6 members in hand and 12 lives in zone, we MUST filter.
        // We've already combined them in the deck forRule awareness, but for the actual setup:
        self.draw_cards(0, 6);
        self.draw_cards(1, 6);

        // Rule 6.2.1.7: 3 cards from Energy Deck to Energy Zone.
        for i in 0..2 {
            for _ in 0..3 {
                if let Some(cid) = self.core.players[i].energy_deck.pop() {
                    self.core.players[i].energy_zone.push(cid);
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

    // Helper for shuffling decks
    fn _fisher_yates_shuffle(&mut self, player_idx: usize) {
        self.core.players[player_idx]
            .deck
            .shuffle(&mut self.core.rng);
    }

    pub fn resolve_deck_refresh(&mut self, player_idx: usize) {
        if !self.core.players[player_idx].discard.is_empty() {
            let mut discard = self.core.players[player_idx]
                .discard
                .drain(..)
                .collect::<Vec<_>>();
            discard.shuffle(&mut self.rng);

            let mut new_deck: SmallVec<[i32; 60]> = SmallVec::from_vec(discard);
            new_deck.extend(self.core.players[player_idx].deck.drain(..));

            // Safety: cap at 60 cards if something went wrong upstream
            if new_deck.len() > 60 {
                if !self.ui.silent {
                    self.log(format!(
                        "WARNING: Impossible deck size {} after refresh. Truncating to 60.",
                        new_deck.len()
                    ));
                }
                new_deck.truncate(60);
            }

            self.core.players[player_idx].deck = new_deck;
            self.core.players[player_idx].set_flag(PlayerState::FLAG_DECK_REFRESHED, true);
        }
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

    pub fn draw_cards(&mut self, player_idx: usize, count: u32) {
        let t = self.turn as i32;
        for _ in 0..count {
            if self.core.players[player_idx].deck.is_empty() {
                self.resolve_deck_refresh(player_idx);
            }
            if let Some(card_id) = self.core.players[player_idx].deck.pop() {
                self.core.players[player_idx].hand.push(card_id);
                self.core.players[player_idx].hand_added_turn.push(t);
            }
        }
    }

    pub fn draw_energy_cards(&mut self, player_idx: usize, count: i32) {
        for _ in 0..count {
            if let Some(cid) = self.core.players[player_idx].energy_deck.pop() {
                let idx = self.core.players[player_idx].energy_zone.len();
                self.core.players[player_idx].energy_zone.push(cid);
                self.core.players[player_idx].set_energy_tapped(idx, false);
            }
        }
    }

    pub fn pay_energy(&mut self, player_idx: usize, count: i32) {
        let mut paid = 0;
        let player = &mut self.core.players[player_idx];
        for i in 0..player.energy_zone.len() {
            if paid >= count {
                break;
            }
            if !player.is_energy_tapped(i) {
                player.set_energy_tapped(i, true);
                paid += 1;
            }
        }
    }

    pub fn activate_energy(&mut self, player_idx: usize, count: i32) {
        let mut activated = 0;
        let player = &mut self.core.players[player_idx];
        for i in 0..player.energy_zone.len() {
            if activated >= count {
                break;
            }
            if player.is_energy_tapped(i) {
                player.set_energy_tapped(i, false);
                activated += 1;
            }
        }
    }

    pub fn set_member_tapped(&mut self, player_idx: usize, slot_idx: usize, tapped: bool) {
        self.core.players[player_idx].set_tapped(slot_idx, tapped);
    }

    // --- Performance Phase Wrappers ---
    pub fn check_win_condition(&mut self) {
        if self.phase == Phase::Terminal {
            return;
        }

        let p0_win = self.core.players[0].success_lives.len() >= 3;
        let p1_win = self.core.players[1].success_lives.len() >= 3;

        if p0_win || p1_win {
            self.phase = Phase::Terminal;
            let msg = match (p0_win, p1_win) {
                (true, false) => "Rule 1.2.1.1: Player 0 wins by 3 successful lives.",
                (false, true) => "Rule 1.2.1.1: Player 1 wins by 3 successful lives.",
                _ => "Rule 1.2.1.2: Draw (Both players reached 3 successful lives).",
            };
            self.log(msg.to_string());
        }
    }

    pub fn is_terminal(&self) -> bool {
        self.phase == Phase::Terminal
    }

    pub fn process_rule_checks(&mut self, db: &CardDatabase) {
        for i in 0..2 {
            // 1. Deck Refresh (Rule 4.4.2)
            if self.core.players[i].deck.is_empty() && !self.core.players[i].discard.is_empty() {
                self.resolve_deck_refresh(i);
            }

            // 2. Energy in empty member area -> Energy Deck (Rule 10.5.3)
            for slot_idx in 0..3 {
                if self.core.players[i].stage[slot_idx] < 0
                    && self.core.players[i].stage_energy_count[slot_idx] > 0
                {
                    if !self.ui.silent {
                        self.log(format!(
                            "Rule 10.5.3: Reclaiming energy from empty slot {} for player {}.",
                            slot_idx, i
                        ));
                    }
                    let reclaimed: Vec<i32> = self.core.players[i].stage_energy[slot_idx]
                        .drain(..)
                        .collect();
                    self.core.players[i].energy_deck.extend(reclaimed);
                    self.core.players[i].stage_energy_count[slot_idx] = 0;

                    // Energy deck is unordered; shuffle to maintain randomness.
                    // OPT 6: Use deterministic seed instead of expensive from_os_rng()
                    use rand::SeedableRng;
                    let mut rng = rand_pcg::Pcg64::seed_from_u64(
                        self.core.turn as u64 * 31 + i as u64 * 7 + slot_idx as u64,
                    );
                    self.core.players[i].energy_deck.shuffle(&mut rng);
                }
            }

            // 3. Eagerly synchronize constant modifiers (Opt V2)
            // OPT 7: Skip during MCTS/silent mode (only needed at expansion/legal action gen)
            if !self.ui.silent {
                self.sync_cost_modifiers(i, db);
            }
        }
        self.check_win_condition();
        self.process_trigger_queue(db);
    }

    pub(crate) fn has_restriction(
        state: &GameState,
        p_idx: usize,
        slot_idx: usize,
        restriction_op: i32,
        db: &CardDatabase,
    ) -> bool {
        crate::core::logic::rules::has_restriction(state, p_idx, slot_idx, restriction_op, db)
    }

    pub fn get_effective_blades(
        &self,
        player_idx: usize,
        slot_idx: usize,
        db: &CardDatabase,
        depth: u32,
    ) -> u32 {
        super::rules::get_effective_blades(self, player_idx, slot_idx, db, depth)
    }

    pub fn get_effective_hearts(
        &self,
        player_idx: usize,
        slot_idx: usize,
        db: &CardDatabase,
        depth: u32,
    ) -> HeartBoard {
        super::rules::get_effective_hearts(self, player_idx, slot_idx, db, depth)
    }

    pub fn get_total_blades(&self, p_idx: usize, db: &CardDatabase, depth: u32) -> u32 {
        super::rules::get_total_blades(self, p_idx, db, depth)
    }

    pub fn get_total_hearts(&self, p_idx: usize, db: &CardDatabase, depth: u32) -> HeartBoard {
        super::rules::get_total_hearts(self, p_idx, db, depth)
    }

    /// Pre-calculates and caches constant cost modifiers for stage slots
    pub fn sync_cost_modifiers(&mut self, p_idx: usize, db: &CardDatabase) {
        let mut new_mods = [0i16; 3];

        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].stage[slot_idx];
            if cid < 0 {
                continue;
            }

            // Wave 1: Global/Area constant reduction abilities
            for other_slot in 0..3 {
                let other_cid = self.core.players[p_idx].stage[other_slot];
                if other_cid < 0 {
                    continue;
                }
                if let Some(other_m) = db.get_member(other_cid) {
                    for ab in &other_m.abilities {
                        if ab.trigger == TriggerType::Constant {
                            // Fast check without DB conditions first if possible, but we must check conditions
                            let ctx = AbilityContext {
                                source_card_id: other_cid,
                                player_id: p_idx as u8,
                                activator_id: p_idx as u8,
                                area_idx: other_slot as i16,
                                target_slot: slot_idx as i16,
                                ..Default::default()
                            };
                            if ab
                                .conditions
                                .iter()
                                .all(|c| self.check_condition(db, p_idx, c, &ctx, 1))
                            {
                                let bc = &ab.bytecode;
                                let mut i = 0;
                                while i + 4 < bc.len() {
                                    if bc[i] == O_REDUCE_COST {
                                        // Some older O_REDUCE_COST might use target slot flags, but standard is global or conditional
                                        new_mods[slot_idx] -= bc[i + 1] as i16;
                                    }
                                    i += 5;
                                }
                            }
                        }
                    }
                }
            }

            // Wave 2: Granted Abilities
            // We need to collect granted abilities first to avoid borrow checker issues with self
            let mut granted = Vec::new();
            for &(target_cid, source_cid, ab_idx) in &self.core.players[p_idx].granted_abilities {
                if target_cid == cid {
                    granted.push((source_cid, ab_idx));
                }
            }

            for (source_cid, ab_idx) in granted {
                if let Some(src_m) = db.get_member(source_cid) {
                    if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                        if ab.trigger == TriggerType::Constant {
                            let ctx = AbilityContext {
                                source_card_id: cid,
                                player_id: p_idx as u8,
                                activator_id: p_idx as u8,
                                area_idx: slot_idx as i16,
                                ..Default::default()
                            };
                            if ab
                                .conditions
                                .iter()
                                .all(|c| self.check_condition(db, p_idx, c, &ctx, 1))
                            {
                                let bc = &ab.bytecode;
                                let mut i = 0;
                                while i + 4 < bc.len() {
                                    if bc[i] == O_REDUCE_COST {
                                        new_mods[slot_idx] -= bc[i + 1] as i16;
                                    }
                                    i += 5;
                                }
                            }
                        }
                    }
                }
            }
        }

        self.core.players[p_idx].slot_cost_modifiers = new_mods;
    }

    pub fn get_member_cost(
        &self,
        p_idx: usize,
        card_id: i32,
        slot_idx: i16,
        secondary_slot_idx: i16,
        db: &CardDatabase,
        depth: u32,
    ) -> i32 {
        super::rules::get_member_cost(
            self,
            p_idx,
            card_id,
            slot_idx,
            secondary_slot_idx,
            db,
            depth,
        )
    }

    pub fn card_matches_filter(&self, db: &CardDatabase, cid: i32, filter_attr: u64) -> bool {
        self.card_matches_filter_with_ctx(db, cid, filter_attr, &crate::core::logic::AbilityContext::default())
    }

    /// Like card_matches_filter but uses a provided AbilityContext (for v_accumulated etc.)
    pub fn card_matches_filter_with_ctx(&self, db: &CardDatabase, cid: i32, filter_attr: u64, ctx: &crate::core::logic::AbilityContext) -> bool {
        self.card_matches_filter_with_ctx_internal(db, cid, filter_attr, ctx, false)
    }

    pub fn card_matches_filter_with_ctx_logs(&self, db: &CardDatabase, cid: i32, filter_attr: u64, ctx: &crate::core::logic::AbilityContext) -> bool {
        self.card_matches_filter_with_ctx_internal(db, cid, filter_attr, ctx, true)
    }

    fn card_matches_filter_with_ctx_internal(&self, db: &CardDatabase, cid: i32, filter_attr: u64, ctx: &crate::core::logic::AbilityContext, debug: bool) -> bool {
        if cid == -1 { return false; }
        if filter_attr == 0 { return true; }

        let filter = CardFilter::from_attr(filter_attr as i64);
        let needs_dynamic_hearts = filter.color_mask != 0;

        for p in 0..2 {
            for s in 0..3 {
                if self.players[p].stage[s] == cid {
                    let s_idx = s as i16;
                    let p_idx = p as u8;
                    
                    let tapped = self.players[p].is_tapped(s);
                    let h_arr = if needs_dynamic_hearts {
                        self.get_effective_hearts(p, s, db, 0).to_array()
                    } else {
                        [0u8; 7]
                    };

                    let res = if debug {
                        filter.matches_with_logs(db, self, cid, ctx, Some((p_idx, s_idx)), tapped, Some(&h_arr))
                    } else {
                        filter.matches(self, db, cid, Some((p_idx, s_idx)), tapped, Some(&h_arr), ctx)
                    };
                    if res {
                        return true;
                    }
                }
            }
        }

        if debug {
            filter.matches_with_logs(db, self, cid, ctx, None, false, None)
        } else {
            filter.matches(self, db, cid, None, false, None, ctx)
        }
    }

    pub fn check_hearts_suitability(&self, have: &[u8; 7], need: &[u8; 7]) -> bool {
        super::performance::check_hearts_suitability(have, need)
    }

    pub fn consume_hearts_from_pool(&self, pool: &mut [u8; 7], need: &[u8; 7]) {
        super::performance::consume_hearts_from_pool(pool, need);
    }

    pub fn get_context_card_id(&self, ctx: &AbilityContext) -> Option<i32> {
        if ctx.source_card_id >= 0 {
            return Some(ctx.source_card_id as i32);
        }
        if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
            let cid = self.core.players[ctx.player_id as usize].stage[ctx.area_idx as usize];
            if cid >= 0 {
                return Some(cid as i32);
            }
        }
        None
    }

    // --- Performance Phase Wrappers ---
    pub fn do_yell(&mut self, db: &CardDatabase, count: u32) -> Vec<i32> {
        super::performance::do_yell(self, db, count)
    }
    pub fn check_live_success(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        live: &LiveCard,
        total_hearts: &[u8; 7],
    ) -> bool {
        super::performance::check_live_success(self, db, p_idx, live, total_hearts)
    }
    pub fn do_performance_phase(&mut self, db: &CardDatabase) {
        super::performance::do_performance_phase(self, db)
    }
    pub fn advance_from_performance(&mut self) {
        super::performance::advance_from_performance(self);
    }

    // --- Phase Methods ---

    pub fn auto_step(&mut self, db: &CardDatabase) {
        let mut loop_count = 0;
        while loop_count < 40 {
            // Increased depth for trigger processing
            // Rule 11.2: Check for win conditions before ANY other processing
            // This ensures Score 3 ends the game immediately even if triggers are pending
            self.check_win_condition();

            if self.phase == Phase::Terminal || self.phase == Phase::Response {
                break;
            }
            if !self.interaction_stack.is_empty() {
                break;
            }

            // NEW: Process any pending triggers before continuing auto-phase
            if !self.core.trigger_queue.is_empty() {
                self.process_trigger_queue(db);
                // If trigger processing caused an interaction (Response phase), stop auto-stepping
                if self.phase == Phase::Response {
                    break;
                }
                continue; // Re-check phase/interaction/triggers after processing
            }

            let old_phase = self.phase;
            if !self.ui.silent && self.debug.debug_mode {
                println!(
                    "[DEBUG] auto_step: Phase={:?}, Player={}",
                    self.phase, self.current_player
                );
            }

            match self.phase {
                Phase::Active => self.do_active_phase(db),
                Phase::Energy => self.do_energy_phase(),
                Phase::Draw => self.do_draw_phase(db),
                Phase::PerformanceP1 | Phase::PerformanceP2 => {
                    self.do_performance_phase(db);
                }
                Phase::LiveResult => {
                    if self.live_result_selection_pending {
                        break;
                    } else {
                        let _ = self.handle_liveresult(db, 0);
                    }
                }
                _ => {
                    // Non-auto phases
                }
            }

            // Loop continues if phase changed OR if we have new triggers to process
            if self.phase == old_phase && self.core.trigger_queue.is_empty() {
                break;
            }
            loop_count += 1;
        }
    }

    pub fn play_member(
        &mut self,
        db: &CardDatabase,
        hand_idx: usize,
        slot_idx: usize,
    ) -> Result<(), String> {
        self.play_member_with_choice(db, hand_idx, slot_idx, -1, -1, 0)
    }

    pub fn end_main_phase(&mut self, db: &CardDatabase) {
        MainPhaseController::end_main_phase(self, db);
    }

    pub fn do_live_result(&mut self, db: &CardDatabase) {
        super::performance::do_live_result(self, db);
    }

    pub fn finalize_live_result(&mut self) {
        super::performance::finalize_live_result(self);
    }

    pub fn activate_ability(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
    ) -> Result<(), String> {
        ResponseController::activate_ability(self, db, slot_idx, ab_idx)
    }

    pub fn activate_ability_with_choice(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
        choice_idx: i32,
        target_slot: i32,
    ) -> Result<(), String> {
        ResponseController::activate_ability_with_choice(
            self,
            db,
            slot_idx,
            ab_idx,
            choice_idx,
            target_slot,
        )
    }

    pub fn execute_mulligan(&mut self, player_idx: usize, discard_indices: Vec<usize>) {
        MulliganController::execute_mulligan(self, player_idx, discard_indices);
    }

    pub fn do_active_phase(&mut self, db: &CardDatabase) {
        TurnPhaseController::do_active_phase(self, db);
    }

    pub fn set_live_cards(&mut self, player_idx: usize, card_ids: Vec<u32>) -> Result<(), String> {
        if card_ids.len() > 3 {
            return Err("Too many lives".to_string());
        }
        // For logging purposes, we'd ideally show card names, but for now just count
        if !self.ui.silent {
            self.log(format!(
                "Rule 8.2.2: Player {} sets {} cards to Live Zone.",
                player_idx,
                card_ids.len()
            ));
        }

        for cid in card_ids {
            let mut placed = false;
            for i in 0..3 {
                if self.core.players[player_idx].live_zone[i] == -1 {
                    self.core.players[player_idx].live_zone[i] = cid as i32;
                    self.core.players[player_idx].set_revealed(i, false);
                    // Rule 8.2.2: Draw same number of cards as placed
                    self.draw_cards(player_idx, 1);
                    placed = true;
                    break;
                }
            }
            if !placed {
                return Err("No empty live slots".to_string());
            }
        }
        Ok(())
    }

    // --- INTERPRETER DELEGATION ---
    pub fn resolve_bytecode(
        &mut self,
        db: &CardDatabase,
        bytecode: std::sync::Arc<Vec<i32>>,
        ctx_in: &AbilityContext,
    ) {
        super::interpreter::resolve_bytecode(self, db, bytecode, ctx_in);
    }

    /// Convenience: Accept Vec (takes ownership)
    #[inline]
    pub fn resolve_bytecode_owned(
        &mut self,
        db: &CardDatabase,
        bytecode: Vec<i32>,
        ctx_in: &AbilityContext,
    ) {
        self.resolve_bytecode(db, std::sync::Arc::new(bytecode), ctx_in);
    }

    /// Convenience: Accept &Vec<i32> (clones internally)
    #[inline]
    pub fn resolve_bytecode_cref(
        &mut self,
        db: &CardDatabase,
        bytecode: &Vec<i32>,
        ctx_in: &AbilityContext,
    ) {
        self.resolve_bytecode(db, std::sync::Arc::new(bytecode.clone()), ctx_in);
    }

    /// Convenience: Accept &[i32] slice (copies internally)
    #[inline]
    pub fn resolve_bytecode_slice(
        &mut self,
        db: &CardDatabase,
        bytecode: &[i32],
        ctx_in: &AbilityContext,
    ) {
        self.resolve_bytecode(db, std::sync::Arc::new(bytecode.to_vec()), ctx_in);
    }

    pub fn check_condition(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        cond: &Condition,
        ctx: &AbilityContext,
        depth: u32,
    ) -> bool {
        super::interpreter::check_condition(self, db, p_idx, cond, ctx, depth)
    }

    pub fn check_condition_opcode(
        &self,
        db: &CardDatabase,
        op: i32,
        val: i32,
        attr: u64,
        slot: i32,
        ctx: &AbilityContext,
        depth: u32,
    ) -> bool {
        super::interpreter::check_condition_opcode(self, db, op, val, attr, slot, ctx, depth)
    }

    pub fn check_cost(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        cost: &Cost,
        ctx: &AbilityContext,
    ) -> bool {
        super::interpreter::check_cost(self, db, p_idx, cost, ctx)
    }

    pub fn pay_cost(
        &mut self,
        db: &CardDatabase,
        p_idx: usize,
        cost: &Cost,
        ctx: &AbilityContext,
    ) -> bool {
        super::interpreter::pay_cost(self, db, p_idx, cost, ctx)
    }

    pub fn process_trigger_queue(&mut self, db: &CardDatabase) {
        super::interpreter::process_trigger_queue(self, db);
    }

    pub fn check_once_per_turn(
        &self,
        p_idx: usize,
        source_type: u8,
        id: u32,
        ab_idx: usize,
    ) -> bool {
        super::interpreter::check_once_per_turn(self, p_idx, source_type, id, ab_idx)
    }

    pub fn consume_once_per_turn(&mut self, p_idx: usize, source_type: u8, id: u32, ab_idx: usize) {
        super::interpreter::consume_once_per_turn(self, p_idx, source_type, id, ab_idx);
    }

    pub fn is_trigger_negated(&self, p_idx: usize, cid: i32, trigger_type: TriggerType) -> bool {
        let player = &self.core.players[p_idx];
        player
            .negated_triggers
            .iter()
            .any(|(t_cid, t_trigger, _)| *t_cid == cid && *t_trigger == trigger_type)
    }

    pub fn trigger_abilities(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        ctx: &AbilityContext,
    ) {
        self.trigger_abilities_from(db, trigger, ctx, 0);
    }

    /// PHASE 3: Queues a specific ability for execution.
    pub fn enqueue_trigger(
        &mut self,
        cid: i32,
        ab_idx: u16,
        ctx: AbilityContext,
        is_live: bool,
        trigger: TriggerType,
    ) {
        self.core
            .trigger_queue
            .push_back((cid, ab_idx, ctx, is_live, trigger));
    }

    /// Unified trigger entry point to reduce boilerplate
    pub fn trigger_event(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        p_idx: usize,
        source_cid: i32,
        slot: i16,
        start_ab_idx: usize,
        choice: i16,
    ) {
        let ctx = AbilityContext {
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            source_card_id: source_cid,
            area_idx: slot,
            trigger_type: trigger,
            choice_index: choice,
            auto_pick: true,
            ..Default::default()
        };
        self.trigger_abilities_from(db, trigger, &ctx, start_ab_idx);
    }

    pub fn trigger_global_event(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        source_cid: i32,
        slot: i16,
        start_ab_idx: usize,
        choice: i16,
    ) {
        self.trigger_depth += 1;
        let cp = self.current_player as usize;
        for i in 0..2 {
            let p_idx = (cp + i) % 2;
            let ctx = AbilityContext {
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                source_card_id: source_cid,
                area_idx: slot,
                trigger_type: trigger,
                choice_index: choice,
                ..Default::default()
            };
            self.trigger_abilities_from_internal(db, trigger, &ctx, start_ab_idx);
        }
        self.trigger_depth -= 1;
        if self.trigger_depth == 0 {
            self.process_trigger_queue(db);
        }
    }

    fn trigger_abilities_from_internal(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
    ) {
        // Collect all potential triggers
        let mut queue = Vec::new();
        let p_idx = ctx.player_id as usize;

        // Stage Members
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].stage[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, false, &mut queue, slot_idx as i16);
        }

        // Performance/Live Cards
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].live_zone[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, true, &mut queue, slot_idx as i16);
        }

        for (cid, _def_cid, ab_idx, mut ab_ctx, is_live) in queue {
            ab_ctx.source_card_id = cid;
            ab_ctx.ability_index = ab_idx as i16;
            self.enqueue_trigger(cid, ab_idx as u16, ab_ctx, is_live, trigger);
        }
    }

    pub fn trigger_abilities_from(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
    ) {
        if self.trigger_depth > 10 {
            if !self.ui.silent {
                println!("[DEBUG] Trigger depth limit reached for {:?}.", trigger);
            }
            return;
        }
        if !self.ui.silent {
            println!("[DEBUG] trigger_abilities_from: {:?} for player {}", trigger, ctx.player_id);
        }
        self.trigger_depth += 1;

        // Collect all potential triggers
        let mut queue = Vec::new();
        let p_idx = ctx.player_id as usize;

        // 1. Stage Members
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].stage[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, false, &mut queue, slot_idx as i16);
        }

        // 2. Performance/Live Cards
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].live_zone[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, true, &mut queue, slot_idx as i16);
        }

        // 3. Source Card (if not on stage/live)
        let source_cid = ctx.source_card_id;
        let on_stage = self.core.players[p_idx]
            .stage
            .iter()
            .any(|&c| c == source_cid);
        let on_live = self.core.players[p_idx]
            .live_zone
            .iter()
            .any(|&c| c == source_cid);
        if !on_stage && !on_live && source_cid >= 0 {
            self.collect_triggers_for_card(
                db,
                source_cid,
                trigger,
                ctx,
                start_ab_idx,
                false,
                &mut queue,
                -1,
            );
            self.collect_triggers_for_card(
                db,
                source_cid,
                trigger,
                ctx,
                start_ab_idx,
                true,
                &mut queue,
                -1,
            );
        }



        if self.debug.debug_mode {
            // println!(
            //     "[DEBUG] trigger_abilities_from: trigger={:?}, queue_len={}",
            //     trigger,
            //     queue.len()
            // );
        }
        for (cid, def_cid, ab_idx, mut ab_ctx, is_live) in queue {
            ab_ctx.source_card_id = cid;
            ab_ctx.ability_index = ab_idx as i16;

            let (_bytecode, conditions, pseudocode) = if is_live {
                let ab = &db.get_live(def_cid).unwrap().abilities[ab_idx as usize];
                (&ab.bytecode, &ab.conditions, &ab.pseudocode)
            } else {
                let ab = &db.get_member(def_cid).unwrap().abilities[ab_idx as usize];
                (&ab.bytecode, &ab.conditions, &ab.pseudocode)
            };

            // Unified logging: TRIGGER events now go to both turn_history and rule_log
            let card_name = if is_live {
                db.get_live(cid).unwrap().name.clone()
            } else {
                db.get_member(cid).unwrap().name.clone()
            };
            let trigger_str = super::interpreter::logging::trigger_as_str(trigger);
            let p_code = if pseudocode.is_empty() {
                ""
            } else {
                &format!(": {}", pseudocode)
            };
            self.log_event(
                "TRIGGER",
                &format!("[{}] Triggered for {}{}", trigger_str, card_name, p_code),
                cid,
                ab_idx as i16,
                p_idx as u8,
                None,
                true, // Also log to rule_log for visibility
            );

            let costs = if is_live {
                &db.get_live(def_cid).unwrap().abilities[ab_idx as usize].costs
            } else {
                &db.get_member(def_cid).unwrap().abilities[ab_idx as usize].costs
            };

            // Check conditions before resolving bytecode
            let mut all_met = true;
            for cond in conditions {
                if !super::interpreter::conditions::check_condition(
                    self, db, p_idx, cond, &ab_ctx, 1,
                ) {
                    all_met = false;
                    break;
                }
            }

            if all_met {
                // Check costs as well before enqueueing
                for cost in costs {
                    if cost.is_optional {
                        continue;
                    } // Skip optional costs for trigger check
                    if !super::interpreter::costs::check_cost(self, db, p_idx, cost, &ab_ctx) {
                        all_met = false;
                        break;
                    }
                }
            }

            if all_met {
                // println!("[DEBUG] Conditions met for card {}. Enqueueing trigger {:?}.", cid, trigger);
                // PHASE 3: Queue instead of immediate resolve to decouple mutations
                self.enqueue_trigger(cid, ab_idx as u16, ab_ctx, is_live, trigger);
            } else {
                if !self.ui.silent {
                    // Log which condition failed
                    for cond in conditions {
                        if !super::interpreter::conditions::check_condition(
                            self, db, p_idx, cond, &ab_ctx, 1,
                        ) {
                            let cond_desc = super::interpreter::logging::describe_condition(
                                cond.condition_type as i32,
                                cond.value,
                                cond.attr,
                            );
                            let card_name = if is_live {
                                db.get_live(cid).unwrap().name.clone()
                            } else {
                                db.get_member(cid).unwrap().name.clone()
                            };
                            self.log(format!("{}'s ability did not activate because target condition was not met: {}.", card_name, cond_desc));
                            break;
                        }
                    }
                }
            }
        }

        self.trigger_depth -= 1;
        if self.trigger_depth == 0 {
            self.process_trigger_queue(db);
        }
    }

    fn collect_triggers_for_card(
        &mut self,
        db: &CardDatabase,
        cid: i32,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
        is_live: bool,
        queue: &mut Vec<(i32, i32, u16, AbilityContext, bool)>,
        slot_idx: i16,
    ) {
        if cid < 0 {
            return;
        }

        let abilities = if is_live {
            db.get_live(cid).map(|l| &l.abilities)
        } else {
            db.get_member(cid).map(|m| &m.abilities)
        };

        let p_idx = ctx.player_id as usize;
        if let Some(abs) = abilities {
            for (ab_idx, ab) in abs.iter().enumerate() {
                if ab.trigger == trigger {
                    // println!("[DEBUG] Found matching trigger for card {}: {:?}", cid, trigger);
                    // Filter OnPlay/OnLeaves to only the specific card being moved
                    // UNLESS it is a monitoring ability (has a GroupFilter/Score/etc condition)
                    if (trigger == TriggerType::OnPlay || trigger == TriggerType::OnLeaves)
                        && cid != ctx.source_card_id
                    {
                        let has_monitor_cond = ab.conditions.iter().any(|c| {
                            c.condition_type == ConditionType::GroupFilter
                                || c.condition_type == ConditionType::ScoreTotalCheck
                        });
                        if !has_monitor_cond {
                            continue;
                        }
                    }

                    if trigger != ctx.trigger_type || ab_idx >= start_ab_idx {
                        // Check and consume negation
                        let mut negated = false;
                        if let Some(n_idx) = self.core.players[p_idx]
                            .negated_triggers
                            .iter()
                            .position(|&(t_cid, t_trig, count)| {
                                t_cid == cid && t_trig == trigger && count > 0
                            })
                        {
                            self.core.players[p_idx].negated_triggers[n_idx].2 -= 1;
                            negated = true;
                        }

                        if negated {
                            if !self.ui.silent {
                                self.log(format!(
                                    "Trigger {:?} for card {} is negated.",
                                    trigger, cid
                                ));
                            }
                            continue;
                        }
                        let mut trigger_ctx = ctx.clone();
                        trigger_ctx.source_card_id = cid;
                        if slot_idx >= 0 && trigger_ctx.area_idx == -1 {
                            trigger_ctx.area_idx = slot_idx;
                        }
                        queue.push((cid, cid, ab_idx as u16, trigger_ctx, is_live));
                    }
                }
            }
        }

        // --- PHASE 3: Granted (Triggered) Abilities Audit Fix ---
        if !is_live {
            // We use a separate loop to avoid borrowing issues if we were mutating,
            // but here we just need to read granted_abilities.
            for i in 0..self.core.players[p_idx].granted_abilities.len() {
                let (target_cid, source_cid, ab_idx) =
                    self.core.players[p_idx].granted_abilities[i];
                if target_cid == cid {
                    if let Some(src_m) = db.get_member(source_cid) {
                        if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                            if ab.trigger == trigger {
                                if (trigger == TriggerType::OnPlay
                                    || trigger == TriggerType::OnLeaves)
                                    && cid != ctx.source_card_id
                                {
                                    continue;
                                }
                                queue.push((cid, source_cid, ab_idx as u16, ctx.clone(), false));
                            }
                        }
                    }
                }
            }
        }
    }

    pub fn step(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        if self.debug.debug_mode {
            self.log(format!(
                "[STEP] Action: {} ({})",
                action,
                ActionFactory::get_action_label(action)
            ));
        }
        self.prev_phase = self.phase;
        self.step_internal(db, action)?;
        self.auto_step(db);
        Ok(())
    }

    fn step_internal(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        match self.phase {
            Phase::Rps => self.handle_rps(action)?,
            Phase::TurnChoice => self.handle_turn_choice(action)?,
            Phase::MulliganP1 | Phase::MulliganP2 => self.handle_mulligan(action)?,
            Phase::Active => self.do_active_phase(db),
            Phase::Energy => self.do_energy_phase(),
            Phase::Draw => self.do_draw_phase(db),
            Phase::Main => self.handle_main(db, action)?,
            Phase::LiveSet => self.handle_liveset(action)?,
            Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::Terminal => {}
            Phase::LiveResult => self.handle_liveresult(db, action)?,
            Phase::Response => self.handle_response(db, action)?,
            _ => {}
        }
        Ok(())
    }

    pub fn get_observation(&self, db: &CardDatabase) -> Vec<f32> {
        self.encode_state(db)
    }

    pub fn write_observation(&self, db: &CardDatabase, out: &mut [f32]) {
        let obs = self.encode_state(db);
        let len = obs.len().min(out.len());
        out[..len].copy_from_slice(&obs[..len]);
    }

    pub fn generate_legal_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        receiver: &mut R,
    ) {
        crate::core::logic::action_gen::ActionGeneratorFactory::generate_actions(
            self, db, p_idx, receiver,
        );
    }

    pub fn calculate_cost_delta(&self, db: &CardDatabase, card_id: i32, p_idx: usize) -> i32 {
        let mut delta = self.core.players[p_idx].cost_reduction as i32;
        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            ..Default::default()
        };
        for (cond, val) in &self.core.players[p_idx].cost_modifiers {
            if self.check_condition(db, p_idx, cond, &ctx, 1) {
                delta += val;
            }
        }
        delta
    }

    pub fn integrated_step(
        &mut self,
        db: &CardDatabase,
        action: i32,
        opp_mode: u8,
        mcts_sims: usize,
        enable_rollout: bool,
    ) -> (f32, bool) {
        let prev_score = self.core.players[0].score as f32;

        // 1. Agent Step (if interactive)
        if self.current_player == 0 && self.phase.is_interactive() {
            let _ = self.step(db, action);
        } else {
            // Auto-progress or illegal call - pass
            let _ = self.step(db, 0);
        }

        // 2. Loop until Agent Turn or Terminal
        while self.phase != Phase::Terminal {
            let is_int = match self.phase {
                Phase::Main
                | Phase::LiveSet
                | Phase::MulliganP1
                | Phase::MulliganP2
                | Phase::Response
                | Phase::LiveResult
                | Phase::Energy => true,
                _ => false,
            };

            if self.current_player == 0 && is_int {
                break; // Agent's turn reached
            }

            if is_int {
                // Interactive turn for opponent (Player 1)
                if opp_mode == 1 {
                    // Default to Original Heuristic for normal integrated step
                    // Default to Original Heuristic for normal integrated step
                    // In-lined to support enable_rollout
                    let sims = if mcts_sims > 0 { mcts_sims } else { 1000 };
                    let mut mcts = MCTS::new();
                    let heuristic = OriginalHeuristic::default();
                    let (stats, _): (Vec<(i32, f32, u32)>, _) = mcts.search_custom(
                        self,
                        db,
                        sims,
                        0.0,
                        SearchHorizon::TurnEnd(),
                        &heuristic,
                        false,
                        enable_rollout,
                    );
                    let best_action = if !stats.is_empty() { stats[0].0 } else { 0 };
                    let _ = self.step(db, best_action);
                } else {
                    // self.step_opponent(db); // MISSING
                    let _ = self.step(db, 0);
                }
            } else {
                // Non-interactive phase (Energy, Draw, LiveResult, etc.)
                let _ = self.step(db, 0);
            }
        }

        let current_score = self.core.players[0].score as f32;
        let reward = current_score - prev_score;

        (reward, self.phase == Phase::Terminal)
    }

    pub fn evaluate<H: Heuristic>(
        &self,
        db: &CardDatabase,
        p0_baseline: u32,
        p1_baseline: u32,
        eval_mode: EvalMode,
        heuristic: &H,
    ) -> f32 {
        heuristic.evaluate(self, db, p0_baseline, p1_baseline, eval_mode, None, None)
    }

    pub fn get_verbose_action_label(&self, action_id: i32, db: &CardDatabase) -> String {
        ActionFactory::get_verbose_action_label(action_id, self, db)
    }
}
