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

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use rand::seq::SliceRandom;
use rand_pcg::Pcg64;
use rand::SeedableRng;
use rand::rngs::SmallRng;
use smallvec::SmallVec;

// use crate::core::*; // UNUSED
use crate::core::enums::*;
use crate::core::generated_constants::{
    FILTER_CHARACTER_ENABLE, FILTER_SETSUNA, FILTER_COLOR_SHIFT, FILTER_TYPE_SHIFT,
    FILTER_GROUP_ENABLE, FILTER_GROUP_SHIFT, FILTER_UNIT_ENABLE, FILTER_UNIT_SHIFT,
    FILTER_TAPPED, FILTER_HAS_BLADE_HEART, FILTER_NOT_BLADE_HEART, FILTER_SPECIAL_SHIFT,
    FILTER_COST_ENABLE, FILTER_COST_SHIFT, FILTER_COST_LE,
};
use super::models::*;
use super::card_db::*;
use super::player::*;
use super::rules::*;
use crate::core::hearts::*;
use crate::core::mcts::{MCTS, SearchHorizon};
use crate::core::heuristics::{Heuristic, OriginalHeuristic, EvalMode};

#[derive(Debug, Default)]
pub struct BypassLog(pub std::sync::Mutex<Vec<String>>);

impl Clone for BypassLog {
    fn clone(&self) -> Self {
        if let Ok(l) = self.0.lock() {
            Self(std::sync::Mutex::new(l.clone()))
        } else {
            Self::default()
        }
    }
}

impl PartialEq for BypassLog {
    fn eq(&self, _other: &Self) -> bool { true }
}
impl Eq for BypassLog {}

impl Serialize for BypassLog {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: serde::Serializer {
        serializer.serialize_unit()
    }
}

impl<'de> Deserialize<'de> for BypassLog {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where D: serde::Deserializer<'de> {
        let _ = serde::de::IgnoredAny::deserialize(deserializer)?;
        Ok(Self::default())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoreGameState {
    pub players: [PlayerState; 2],
    pub current_player: u8,
    pub first_player: u8,
    pub phase: Phase,
    #[serde(default)]
    pub prev_phase: Phase,
    pub prev_card_id: i32,
    pub turn: u16,
    #[serde(default)]
    pub trigger_depth: u16,
    #[serde(default)]
    pub live_set_pending_draws: [u8; 2],
    #[serde(default)]
    pub interaction_stack: Vec<PendingInteraction>,
    #[serde(default)]
    pub live_result_selection_pending: bool,
    #[serde(default)]
    pub live_result_triggers_done: bool,
    #[serde(default)]
    pub live_start_triggers_done: bool,
    #[serde(default)]
    pub live_result_processed_mask: [u8; 2],
    #[serde(default)]
    pub live_start_processed_mask: [u8; 2],
    #[serde(default)]
    pub live_success_processed_mask: [u8; 2],
    #[serde(default)]
    pub performance_reveals_done: [bool; 2],
    #[serde(default)]
    pub performance_yell_done: [bool; 2],
    #[serde(skip)]
    pub trigger_queue: VecDeque<(i32, u16, AbilityContext, bool, TriggerType)>,
    #[serde(skip, default = "SmallRng::from_os_rng")]
    pub rng: SmallRng,
    #[serde(default)]
    pub rps_choices: [i8; 2],
    #[serde(default)]
    pub turn_history: Vec<TurnEvent>,
    #[serde(default)]
    pub obtained_success_live: [bool; 2],
}

impl Default for CoreGameState {
    fn default() -> Self {
        Self {
            players: [PlayerState::default(), PlayerState::default()],
            current_player: 0,
            first_player: 0,
            phase: Phase::Setup,
            prev_phase: Phase::Setup,
            prev_card_id: -1,
            turn: 1,
            trigger_depth: 0,
            live_set_pending_draws: [0, 0],
            interaction_stack: Vec::new(),
            live_result_selection_pending: false,
            live_result_triggers_done: false,
            live_start_triggers_done: false,
            live_result_processed_mask: [0, 0],
            live_start_processed_mask: [0, 0],
            live_success_processed_mask: [0, 0],
            performance_reveals_done: [false, false],
            performance_yell_done: [false, false],
            trigger_queue: VecDeque::new(),
            rng: SmallRng::from_os_rng(),
            rps_choices: [-1; 2],
            turn_history: Vec::new(),
            obtained_success_live: [false; 2],
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UIState {
    #[serde(default)]
    pub silent: bool,
    #[serde(default)]
    pub rule_log: Vec<String>,
    #[serde(default)]
    pub performance_results: HashMap<u8, serde_json::Value>,
    #[serde(default)]
    pub last_performance_results: HashMap<u8, serde_json::Value>,
    #[serde(default)]
    pub performance_history: Vec<serde_json::Value>,
}

impl Default for UIState {
    fn default() -> Self {
        Self {
            silent: false,
            rule_log: Vec::new(),
            performance_results: HashMap::new(),
            last_performance_results: HashMap::new(),
            performance_history: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DebugState {
    pub debug_ignore_conditions: bool,
    pub bypassed_conditions: BypassLog,
    pub debug_mode: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct GameState {
    #[serde(flatten)]
    pub core: CoreGameState,
    #[serde(flatten)]
    pub ui: UIState,
    #[serde(skip)]
    pub debug: DebugState,
}

impl std::ops::Deref for GameState {
    type Target = CoreGameState;
    fn deref(&self) -> &Self::Target {
        &self.core
    }
}

impl std::ops::DerefMut for GameState {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.core
    }
}

impl GameState {
    const ACTION_TURN_CHOICE_FIRST: i32 = 5000;
    const ACTION_TURN_CHOICE_SECOND: i32 = 5001;

    // Helper to calculate other slot index for Double Baton (offset 3-8)
    fn get_combo_other_slot(primary_slot: usize, is_next: bool) -> usize {
        if primary_slot == 0 {
            if is_next { 1 } else { 2 }
        } else if primary_slot == 1 {
            if is_next { 2 } else { 0 }
        } else {
            if is_next { 0 } else { 1 }
        }
    }

    pub fn safe_set_mask(&self, mask: &mut [bool], aid: usize) {
        if aid < mask.len() {
            mask[aid] = true;
        } else {
            panic!("[ACTION_OOB] Action ID {} exceeds mask len {} in phase {:?}", aid, mask.len(), self.phase);
        }
    }

    pub fn log(&mut self, msg: String) {
        if self.ui.silent { return; }
        let full_msg = if msg.starts_with("[Turn") {
            msg
        } else {
            format!("[Turn {}] {}", self.turn, msg)
        };
        self.ui.rule_log.push(full_msg);
    }

    pub fn log_rule(&mut self, rule: &str, msg: &str) {
        if self.ui.silent { return; }
        let p_idx = self.current_player;
        self.log(format!("[{}] {}", rule, msg));
        self.log_turn_event("RULE", -1, -1, p_idx, msg);
    }

    pub fn log_turn_event(&mut self, event_type: &str, source_cid: i32, ability_idx: i16, player_id: u8, description: &str) {
        if self.turn_history.len() > 2000 { return; } // Safety cap
        let t = self.turn as u32;
        let ph = self.phase;
        self.turn_history.push(TurnEvent {
            turn: t,
            phase: ph,
            player_id,
            event_type: event_type.to_string(),
            source_cid,
            ability_idx,
            description: description.to_string(),
        });
    }

    pub fn handle_member_leaves_stage(&mut self, p_idx: usize, slot: usize, db: &CardDatabase, ctx: &AbilityContext) -> Option<i32> {
        if slot >= 3 { return None; }
        let cid = self.core.players[p_idx].stage[slot];
        if cid < 0 { return None; }

        let mut leave_ctx = ctx.clone();
        leave_ctx.source_card_id = cid;
        leave_ctx.area_idx = slot as i16;
        
        // Trigger OnLeaves
        self.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);

        // Clear slot data (Buffs are attached to member, Energy stays in slot)
        self.core.players[p_idx].stage[slot] = -1;
        self.core.players[p_idx].blade_buffs[slot] = 0;
        self.core.players[p_idx].heart_buffs[slot] = HeartBoard::default();
        
        // Clear flags (Tapped: bit 3-5, Moved: bit 6-8)
        self.core.players[p_idx].flags &= !(1 << (3 + slot)); 
        self.core.players[p_idx].flags &= !(1 << (6 + slot)); 
        
        Some(cid as i32)
    }

    pub fn setup_turn_log(&mut self) {
        if self.ui.silent { return; }
        let p_idx = self.current_player;
        self.log(format!("=== Player {}'s Turn ===", p_idx));
    }

    pub fn initialize_game(&mut self, p0_deck: Vec<i32>, p1_deck: Vec<i32>, p0_energy: Vec<i32>, p1_energy: Vec<i32>, p0_lives: Vec<i32>, p1_lives: Vec<i32>) {
        eprintln!("RUST: initialize_game START");
        self.initialize_game_with_seed(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives, None);
        eprintln!("RUST: initialize_game END");
    }

    pub fn copy_from(&mut self, other: &GameState) {
        self.core.players[0].copy_from(&other.players[0]);
        self.core.players[1].copy_from(&other.players[1]);
        self.current_player = other.current_player;
        self.first_player = other.first_player;
        self.phase = other.phase;
        self.prev_card_id = other.prev_card_id;
        self.turn = other.turn;
        self.ui.silent = other.ui.silent;
        // self.ui.rule_log.clear(); // We purposely do not copy rule log to avoid overhead
        self.trigger_depth = other.trigger_depth;
        self.live_set_pending_draws = other.live_set_pending_draws;
        self.live_result_processed_mask = other.live_result_processed_mask;
        self.interaction_stack = other.interaction_stack.clone();
        self.debug.debug_ignore_conditions = other.debug.debug_ignore_conditions;
        self.debug.bypassed_conditions = other.debug.bypassed_conditions.clone();
        self.debug.debug_mode = other.debug.debug_mode;
    }

    pub fn initialize_game_with_seed(&mut self, p0_deck: Vec<i32>, p1_deck: Vec<i32>, p0_energy: Vec<i32>, p1_energy: Vec<i32>, p0_lives: Vec<i32>, p1_lives: Vec<i32>, seed: Option<u64>) {
        // Rule 6.1.1.1: Main Deck contains 48 member cards and 12 live cards (total 60)
        let mut d0 = p0_deck;
        d0.extend(p0_lives.clone());
        let mut d1 = p1_deck;
        d1.extend(p1_lives.clone());
        self.core.players[0].deck = SmallVec::from_vec(d0);
        self.core.players[1].deck = SmallVec::from_vec(d1);

        self.core.players[0].energy_deck = SmallVec::from_vec(p0_energy);
        self.core.players[1].energy_deck = SmallVec::from_vec(p1_energy);

        // Reset state
        for i in 0..2 {
            self.core.players[i].hand.clear();
            self.core.players[i].energy_zone.clear();
            self.core.players[i].tapped_energy_mask = 0;
            self.core.players[i].stage = [-1; 3];
            // Clear tapped_members and moved_members flags
            self.core.players[i].set_flag(PlayerState::OFFSET_TAPPED, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_TAPPED + 1, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_TAPPED + 2, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_MOVED, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_MOVED + 1, false);
            self.core.players[i].set_flag(PlayerState::OFFSET_MOVED + 2, false);
            self.core.players[i].discard.clear();
            self.core.players[i].success_lives.clear();
            if i == 0 {
                self.core.players[0].success_lives.extend(p0_lives.iter().map(|&x| x));
            } else {
                self.core.players[1].success_lives.extend(p1_lives.iter().map(|&x| x));
            }
            self.core.players[i].mulligan_selection = 0;
            self.core.players[i].hand_added_turn.clear();
            self.core.players[i].live_deck.clear(); // Obsolete, but clearing for safety
        }

        let mut rng = match seed {
            Some(s) => Pcg64::seed_from_u64(s),
            None => Pcg64::from_os_rng(),
        };
        self.core.players[0].deck.shuffle(&mut rng);
        self.core.players[1].deck.shuffle(&mut rng);
        self.core.players[0].energy_deck.shuffle(&mut rng);
        self.core.players[1].energy_deck.shuffle(&mut rng);

        // Initial Hands (6 cards)
        self.log("Rule 6.2.1.5: Both players draw 6 cards as starting hand.".to_string());
        self.draw_cards(0, 6);
        self.draw_cards(1, 6);

        // Initial Energy (3 cards)
        self.log("Rule 6.2.1.7: Both players place 3 cards from Energy Deck to Energy Zone.".to_string());
        for i in 0..2 {
            for _ in 0..3 {
                if let Some(cid) = self.core.players[i].energy_deck.pop() {
                    self.core.players[i].energy_zone.push(cid);
                    // tapped_energy_mask is already 0 from default() or reset
                }
            }
        }

        // Setup Lives
        self.core.players[0].live_zone = [-1; 3];
        self.core.players[1].live_zone = [-1; 3];
        for i in 0..3 {
            self.core.players[0].set_revealed(i, false);
            self.core.players[1].set_revealed(i, false);
        }

        // Setup first player
        self.phase = Phase::Rps;
        self.current_player = 0; 
        self.rps_choices = [-1; 2];
        self.turn = 1;
        self.ui.rule_log.clear();
        self.ui.performance_results.clear();
        self.ui.last_performance_results.clear();
        self.ui.performance_history.clear();
        self.live_set_pending_draws = [0, 0];
        self.live_result_processed_mask = [0, 0];
        self.setup_turn_log();
    }

    // Helper for shuffling decks
    fn _fisher_yates_shuffle(&mut self, player_idx: usize) {
        self.core.players[player_idx].deck.shuffle(&mut self.core.rng);
    }

    pub fn resolve_deck_refresh(&mut self, player_idx: usize) {
        if !self.core.players[player_idx].discard.is_empty() {
            let mut discard = self.core.players[player_idx].discard.drain(..).collect::<Vec<_>>();
            discard.shuffle(&mut self.rng);
            
            let mut new_deck: SmallVec<[i32; 60]> = SmallVec::from_vec(discard);
            new_deck.extend(self.core.players[player_idx].deck.drain(..));
            
            // Safety: cap at 60 cards if something went wrong upstream
            if new_deck.len() > 60 {
                if !self.ui.silent { self.log(format!("WARNING: Impossible deck size {} after refresh. Truncating to 60.", new_deck.len())); }
                new_deck.truncate(60);
            }
            
            self.core.players[player_idx].deck = new_deck;
            self.core.players[player_idx].set_flag(PlayerState::FLAG_DECK_REFRESHED, true);
        }
    }

    pub fn register_played_member(&mut self, p_idx: usize, card_id: i32, db: &CardDatabase) {
        if let Some(m) = db.get_member(card_id as i32) {
            for &gid in &m.groups {
                if gid > 0 && gid < 32 {
                    self.core.players[p_idx].played_group_mask |= 1 << gid;
                }
            }
        }
    }

    pub fn draw_cards(&mut self, player_idx: usize, count: u32) {
        let t = self.turn as i32;
        for _ in 0..count {
            if self.core.players[player_idx].deck.is_empty() { self.resolve_deck_refresh(player_idx); }
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
            if paid >= count { break; }
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
            if activated >= count { break; }
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
        if self.phase == Phase::Terminal { return; }

        let p0_success = self.core.players[0].success_lives.len();
        let p1_success = self.core.players[1].success_lives.len();

        if p0_success >= 3 || p1_success >= 3 {
            self.phase = Phase::Terminal;
            if p0_success >= 3 && p1_success < 3 {
                self.log("Rule 1.2.1.1: Player 0 wins by 3 successful lives.".to_string());
            } else if p1_success >= 3 && p0_success < 3 {
                self.log("Rule 1.2.1.1: Player 1 wins by 3 successful lives.".to_string());
            } else {
                self.log("Rule 1.2.1.2: Draw (Both players reached 3 successful lives).".to_string());
            }
        }
    }

    pub fn is_terminal(&self) -> bool {
        self.phase == Phase::Terminal
    }

    // --- AI Encoding ---
    pub fn encode_state(&self, db: &CardDatabase) -> Vec<f32> {
        const TOTAL_SIZE: usize = 1200;
        let mut feats = Vec::with_capacity(TOTAL_SIZE);

        feats.push(self.turn as f32 / 50.0);
        feats.push(self.phase as i32 as f32 / 10.0);
        feats.push(self.current_player as f32);
        feats.push(self.core.players[0].score as f32 / 10.0);
        feats.push(self.core.players[1].score as f32 / 10.0);
        feats.push(self.core.players[0].success_lives.len() as f32 / 3.0);
        feats.push(self.core.players[1].success_lives.len() as f32 / 3.0);
        feats.push(self.core.players[0].hand.len() as f32 / 10.0);
        feats.push(self.core.players[1].hand.len() as f32 / 10.0);
        feats.push(self.core.players[0].energy_zone.len() as f32 / 10.0);
        feats.push(self.core.players[1].energy_zone.len() as f32 / 10.0);
        feats.push(self.core.players[0].deck.len() as f32 / 50.0);
        feats.push(self.core.players[1].deck.len() as f32 / 50.0);
        let p0_tapped = (0..self.core.players[0].energy_zone.len()).filter(|&i| self.core.players[0].is_energy_tapped(i)).count();
        let p1_tapped = (0..self.core.players[1].energy_zone.len()).filter(|&i| self.core.players[1].is_energy_tapped(i)).count();
        feats.push(p0_tapped as f32 / 10.0);
        feats.push(p1_tapped as f32 / 10.0);
        feats.push(self.core.players[0].baton_touch_count as f32 / 3.0);
        feats.push(self.core.players[1].baton_touch_count as f32 / 3.0);
        while feats.len() < 20 { feats.push(0.0); }

        for i in 0..3 { self.encode_member_slot(&mut feats, 0, i, db); }
        for i in 0..3 { self.encode_member_slot(&mut feats, 1, i, db); }
        for i in 0..3 { self.encode_live_slot(&mut feats, 0, i, db, true); }
        for i in 0..3 {
            let revealed = self.core.players[1].is_revealed(i);
            self.encode_live_slot(&mut feats, 1, i, db, revealed);
        }

        const CARD_FEAT_SIZE: usize = 48;
        for slot in 0..10 {
            if slot < self.core.players[0].hand.len() {
                let cid = self.core.players[0].hand[slot];
                self.encode_card_features(&mut feats, cid, db);
            } else {
                for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
            }
        }
        feats.push(self.core.players[1].hand.len() as f32 / 10.0);

        let mut p0_power = 0i32;
        let mut p1_power = 0i32;
        for i in 0..3 {
            p0_power += self.get_effective_blades(0, i, db, 0) as i32;
            p1_power += self.get_effective_blades(1, i, db, 0) as i32;
        }
        feats.push(p0_power as f32 / 30.0);
        feats.push(p1_power as f32 / 30.0);
        feats.push((p0_power - p1_power) as f32 / 30.0);

        let mut p0_stage_hearts = [0u32; 7];
        for i in 0..3 {
            let h = self.get_effective_hearts(0, i, db, 0);
            let h_arr = h.to_array();
            for c in 0..7 { p0_stage_hearts[c] += h_arr[c] as u32; }
        }

        let mut suitability = 0.0f32;
        if self.core.players[0].live_zone[0] >= 0 {
            if let Some(l) = db.get_live(self.core.players[0].live_zone[0]) {
                let mut total_req = 0u32;
                let mut total_sat = 0u32;
                for c in 0..7 {
                    let req = l.required_hearts[c] as u32;
                    let have = p0_stage_hearts[c].min(req);
                    total_req += req;
                    total_sat += have;
                }
                let remaining = total_req.saturating_sub(total_sat);
                let any_color = p0_stage_hearts[6];
                total_sat += remaining.min(any_color);
                if total_req > 0 { suitability = total_sat as f32 / total_req as f32; }
            }
        }
        feats.push(suitability);
        feats.push((3 - self.core.players[0].success_lives.len()) as f32 / 3.0);
        feats.push((3 - self.core.players[1].success_lives.len()) as f32 / 3.0);
        feats.push(self.core.players[0].current_turn_volume as f32 / 20.0);
        feats.push(self.core.players[1].current_turn_volume as f32 / 20.0);

        while feats.len() < TOTAL_SIZE - 10 { feats.push(0.0); }
        while feats.len() < TOTAL_SIZE { feats.push(0.0); }
        if feats.len() > TOTAL_SIZE { feats.truncate(TOTAL_SIZE); }
        feats
    }

    fn encode_member_slot(&self, feats: &mut Vec<f32>, p_idx: usize, slot: usize, db: &CardDatabase) {
        const CARD_FEAT_SIZE: usize = 48;
        let cid = self.core.players[p_idx].stage[slot];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                feats.push(1.0); feats.push(1.0); feats.push(0.0); feats.push(0.0);
                feats.push(m.cost as f32 / 10.0);
                feats.push(self.get_effective_blades(p_idx, slot, db, 0) as f32 / 10.0);
                let hearts = self.get_effective_hearts(p_idx, slot, db, 0);
                for h in hearts.to_array() { feats.push(h as f32 / 5.0); }
                for _ in 0..7 { feats.push(0.0); }
                for &bh in &m.blade_hearts { feats.push(bh as f32 / 5.0); }
                feats.push(m.volume_icons as f32 / 5.0);
                feats.push(if (m.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
                feats.push(if (m.semantic_flags & 0x04) != 0 { 1.0 } else { 0.0 });
                feats.push(if (m.semantic_flags & 0x02) != 0 { 1.0 } else { 0.0 });
                feats.push(if self.core.players[p_idx].is_tapped(slot) { 1.0 } else { 0.0 });
                while (feats.len() % 48) != 0 { feats.push(0.0); }
                return;
            }
        }
        for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
    }

    fn encode_live_slot(&self, feats: &mut Vec<f32>, p_idx: usize, slot: usize, db: &CardDatabase, visible: bool) {
        const CARD_FEAT_SIZE: usize = 48;
        let cid = self.core.players[p_idx].live_zone[slot];
        if cid >= 0 && visible {
            if let Some(l) = db.get_live(cid) {
                feats.push(1.0); feats.push(0.0); feats.push(1.0); feats.push(0.0);
                feats.push(0.0); feats.push(l.score as f32 / 10.0);
                for _ in 0..7 { feats.push(0.0); }
                for &h in &l.required_hearts { feats.push(h as f32 / 5.0); }
                for &bh in &l.blade_hearts { feats.push(bh as f32 / 5.0); }
                feats.push(l.volume_icons as f32 / 5.0);
                feats.push(if (l.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
                feats.push(0.0); feats.push(0.0);
                while (feats.len() % 48) != 0 { feats.push(0.0); }
                return;
            }
        }
        for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
    }

    fn encode_card_features(&self, feats: &mut Vec<f32>, cid: i32, db: &CardDatabase) {
        const CARD_FEAT_SIZE: usize = 48;
        if let Some(m) = db.get_member(cid) {
            feats.push(1.0); feats.push(1.0); feats.push(0.0); feats.push(0.0);
            feats.push(m.cost as f32 / 10.0); feats.push(0.0);
            for &h in &m.hearts { feats.push(h as f32 / 5.0); }
            for _ in 0..7 { feats.push(0.0); }
            for &bh in &m.blade_hearts { feats.push(bh as f32 / 5.0); }
            for _ in 0..7 { feats.push(0.0); } // Padding for blade hearts if 7 colors
            feats.push(m.volume_icons as f32 / 5.0);
            feats.push(if (m.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
            feats.push(if (m.semantic_flags & 0x04) != 0 { 1.0 } else { 0.0 });
            feats.push(if (m.semantic_flags & 0x02) != 0 { 1.0 } else { 0.0 });
            feats.push(0.0);
            while (feats.len() % 48) != 0 { feats.push(0.0); }
        } else if let Some(l) = db.get_live(cid) {
            feats.push(1.0); feats.push(0.0); feats.push(1.0); feats.push(0.0);
            feats.push(0.0); feats.push(l.score as f32 / 10.0);
            for _ in 0..7 { feats.push(0.0); }
            for &h in &l.required_hearts { feats.push(h as f32 / 5.0); }
            for &bh in &l.blade_hearts { feats.push(bh as f32 / 5.0); }
            feats.push(l.volume_icons as f32 / 5.0);
            feats.push(if (l.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
            feats.push(0.0); feats.push(0.0); feats.push(0.0);
            while (feats.len() % 48) != 0 { feats.push(0.0); }
        } else {
            for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
        }
    }

    pub fn process_rule_checks(&mut self) {
        for i in 0..2 {
            if self.core.players[i].deck.is_empty() && !self.core.players[i].discard.is_empty() {
                self.resolve_deck_refresh(i);
            }

            // Rule 10.5.3: Energy in empty member area -> Energy Deck
            for slot_idx in 0..3 {
                if self.core.players[i].stage[slot_idx] < 0 {
                    if !self.core.players[i].stage_energy[slot_idx].is_empty() {
                        if !self.ui.silent { self.log(format!("Rule 10.5.3: Reclaiming energy from empty slot {} for player {}.", slot_idx, i)); }
                        let reclaimed: Vec<i32> = self.core.players[i].stage_energy[slot_idx].drain(..).collect();
                        self.core.players[i].energy_deck.extend(reclaimed);
                        self.core.players[i].stage_energy_count[slot_idx] = 0;

                        // Shuffle energy deck after returning cards? Rules say "put in energy deck".
                        // Usually implies random position or shuffle if non-ordered.
                        // Energy deck is unordered (Rule 4.9.2), but typically we push back.
                        // Let's shuffle to be safe since it's "deck".
                        let mut rng = Pcg64::from_os_rng();
                        self.core.players[i].energy_deck.shuffle(&mut rng);
                    }
                }
            }
        }
        for p in 0..2 {
            for i in 0..3 {
                if self.core.players[p].stage[i] < 0 && self.core.players[p].stage_energy_count[i] > 0 {
                    self.core.players[p].stage_energy_count[i] = 0;
                }
            }
        }
        self.check_win_condition();
    }

    pub fn get_effective_blades(&self, player_idx: usize, slot_idx: usize, db: &CardDatabase, depth: u32) -> u32 {
        super::rules::get_effective_blades(self, player_idx, slot_idx, db, depth)
    }

    pub fn get_effective_hearts(&self, player_idx: usize, slot_idx: usize, db: &CardDatabase, depth: u32) -> HeartBoard {
        super::rules::get_effective_hearts(self, player_idx, slot_idx, db, depth)
    }

    pub fn get_total_blades(&self, p_idx: usize, db: &CardDatabase, depth: u32) -> u32 {
        super::rules::get_total_blades(self, p_idx, db, depth)
    }

    pub fn get_total_hearts(&self, p_idx: usize, db: &CardDatabase, depth: u32) -> HeartBoard {
        super::rules::get_total_hearts(self, p_idx, db, depth)
    }

    pub fn get_member_cost(&self, p_idx: usize, card_id: i32, slot_idx: i16, secondary_slot_idx: i16, db: &CardDatabase, depth: u32) -> i32 {
        super::rules::get_member_cost(self, p_idx, card_id, slot_idx, secondary_slot_idx, db, depth)
    }



    pub fn card_matches_filter(&self, db: &CardDatabase, cid: i32, filter_attr: u64) -> bool {
        if cid == -1 { return false; } // Handle tombstone placeholders
        
        // Bit 42: Character Filter Enable (Multi-mode)
        if (filter_attr & FILTER_CHARACTER_ENABLE) != 0 {
             let id1 = ((filter_attr >> 31) & 0x7F) as u8;
             let id2 = ((filter_attr >> 17) & 0x7F) as u8;
             let id3 = ((filter_attr >> 24) & 0x7F) as u8;
             
             let name = if let Some(m) = db.get_member(cid) { &m.name }
                        else if let Some(l) = db.get_live(cid) { &l.name }
                        else { "" };
             
             let mut match_found = false;
             if id1 > 0 && name.contains(crate::core::logic::card_db::get_character_name(id1)) { match_found = true; }
             if !match_found && id2 > 0 && name.contains(crate::core::logic::card_db::get_character_name(id2)) { match_found = true; }
             if !match_found && id3 > 0 && name.contains(crate::core::logic::card_db::get_character_name(id3)) { match_found = true; }
             
             if !match_found {
                 if self.debug.debug_mode { println!("[DEBUG] REJECT cid={}: Character filter mismatch. Name '{}' not found in IDs ({}, {}, {})", cid, name, id1, id2, id3); }
                 return false;
             }
        }

        // Bit 7: Specialized 'Setsuna' filter (優木せつ菜)
        if (filter_attr & FILTER_SETSUNA) != 0 {
             let name = if let Some(m) = db.get_member(cid) { &m.name }
                        else if let Some(l) = db.get_live(cid) { &l.name }
                        else { "" };
             if !name.contains("優木せつ菜") {
                 if self.debug.debug_mode { println!("[DEBUG] REJECT cid={}: Name '{}' does not contain '優木せつ菜'", cid, name); }
                 return false; 
             }
        }
        
        // Bits 32-38: Color Filter (SMILE, PURE, COOL, RED, YELLOW, BLUE, PURPLE)
        let color_mask = (filter_attr >> FILTER_COLOR_SHIFT) & 0x7F;
        if color_mask != 0 {
            if let Some(m) = db.get_member(cid) {
                let mut has_match = false;
                for i in 0..7 {
                    if (color_mask & (1 << i)) != 0 && m.hearts[i] > 0 {
                        has_match = true;
                        break;
                    }
                }
                if !has_match { return false; }
            } else if let Some(l) = db.get_live(cid) {
                let mut has_match = false;
                for i in 0..7 {
                    if (color_mask & (1 << i)) != 0 && l.required_hearts[i] > 0 {
                        has_match = true;
                        break;
                    }
                }
                if !has_match { return false; }
            } else {
                return false;
            }
        }

        // Bit 2-3: Type Filter (0=None, 1=Member, 2=Live)
        let type_filter = (filter_attr >> FILTER_TYPE_SHIFT) & 0x03;
        if type_filter == 1 && db.get_member(cid).is_none() { return false; }
        if type_filter == 2 && db.get_live(cid).is_none() { return false; }

        // Bit 4: Group Filter Enable
        if (filter_attr & FILTER_GROUP_ENABLE) != 0 {
            let group_id = (filter_attr >> FILTER_GROUP_SHIFT) & 0x7F;
            if let Some(m) = db.get_member(cid) {
                if !m.groups.contains(&(group_id as u8)) { return false; }
            } else if let Some(l) = db.get_live(cid) {
                let res = l.groups.contains(&(group_id as u8));
                if !res { return false; }
            } else {
                return false;
            }
        }

        // Bit 16: Unit Filter Enable
        if (filter_attr & FILTER_UNIT_ENABLE) != 0 {
            let unit_id = (filter_attr >> FILTER_UNIT_SHIFT) & 0x7F;
            if let Some(m) = db.get_member(cid) {
                if !m.units.contains(&(unit_id as u8)) { return false; }
            } else if let Some(l) = db.get_live(cid) {
                if !l.units.contains(&(unit_id as u8)) { return false; }
            } else {
                return false;
            }
        }
        // Bit 12: Tapped Filter
        if (filter_attr & FILTER_TAPPED) != 0 {
             // Tapped check requires knowledge of which player's card it is and which slot.
             // This is tricky for Hand/Discard. For Stage, we should ideally pass more context.
             // For now, let's assume it's used for Stage counting where we CAN check the state.
             let mut is_tapped = false;
             for p in 0..2 {
                 for s in 0..3 {
                     if self.core.players[p].stage[s] == cid && self.core.players[p].is_tapped(s) {
                         is_tapped = true;
                     }
                 }
             }
             if !is_tapped { return false; }
        }

        // Bit 13: Has Blade Heart
        if (filter_attr & FILTER_HAS_BLADE_HEART) != 0 {
            if let Some(m) = db.get_member(cid) {
                if m.blade_hearts.iter().all(|&h| h == 0) { return false; }
            } else if let Some(l) = db.get_live(cid) {
                if l.blade_hearts.iter().all(|&h| h == 0) { return false; }
            } else { return false; }
        }

        // Bit 14: Not Has Blade Heart
        if (filter_attr & FILTER_NOT_BLADE_HEART) != 0 {
            if let Some(m) = db.get_member(cid) {
                if m.blade_hearts.iter().any(|&h| h > 0) { return false; }
            } else if let Some(l) = db.get_live(cid) {
                if l.blade_hearts.iter().any(|&h| h > 0) { return false; }
            }
        }

        // Bit 15: UNIQUE_NAMES is handled by the caller (counting loop)

        // Bits 48-50: Special Filter IDs (Moved from 8-10 to avoid Group ID collision)
        let special_id = (filter_attr >> FILTER_SPECIAL_SHIFT) & 0x07;
        if special_id != 0 {
            let card_name = if let Some(m) = db.get_member(cid) { &m.name }
                           else if let Some(l) = db.get_live(cid) { &l.name }
                           else { "" };
            match special_id {
                1 => { // NAME_IN=['澁谷かのん', 'ウィーン·マルガレーテ', '鬼塚冬毬']
                    if !["澁谷かのん", "ウィーン·マルガレーテ", "鬼塚冬毬"].contains(&card_name) { return false; }
                },
                2 => { // NOT_NAME=MY舞☆TONIGHT
                    if card_name == "MY舞☆TONIGHT" { return false; }
                },
                _ => {}
            }
        }

        // Bit 24: Cost/Hearts Filter Enable
        if (filter_attr & FILTER_COST_ENABLE) != 0 {
            let threshold = ((filter_attr >> FILTER_COST_SHIFT) & 0x1F) as i32;
            let is_le = (filter_attr & FILTER_COST_LE) != 0;
            let card_value = if let Some(m) = db.get_member(cid) {
                m.cost as i32
            } else if let Some(l) = db.get_live(cid) {
                // Sum all hearts (0-6)
                l.required_hearts.iter().map(|&h| h as i32).sum::<i32>()
            } else {
                return false;
            };
            if is_le {
                if card_value > threshold { return false; }
            } else {
                if card_value < threshold {
                    println!("REJECT: cid={} val={} thresh={}", cid, card_value, threshold);
                    return false;
                }
            }
        }
        true
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

    /// Get Japanese trigger label for logging
    pub fn get_trigger_label(trigger: TriggerType) -> &'static str {
        match trigger {
            TriggerType::OnPlay => "【登場】",
            TriggerType::OnLiveStart => "【開始】",
            TriggerType::OnLiveSuccess => "【成功】",
            TriggerType::TurnStart => "【ターン開始】",
            TriggerType::TurnEnd => "【ターン終了】",
            TriggerType::Constant => "【常時】",
            TriggerType::Activated => "【起動】",
            TriggerType::OnLeaves => "【退場】",
            TriggerType::OnReveal => "【公開】",
            TriggerType::OnPositionChange => "【移動】",
            TriggerType::None => "",
        }
    }

    // --- Performance Phase Wrappers ---
    pub fn do_yell(&mut self, db: &CardDatabase, count: u32) -> Vec<i32> {
        super::performance::do_yell(self, db, count)
    }
    pub fn check_live_success(&self, p_idx: usize, live: &LiveCard, total_hearts: &[u8; 7]) -> bool {
        super::performance::check_live_success(self, p_idx, live, total_hearts)
    }
    pub fn do_performance_phase(&mut self, db: &CardDatabase) {
        super::performance::do_performance_phase(self, db)
    }
    pub fn advance_from_performance(&mut self) {
        super::performance::advance_from_performance(self);
    }
    pub fn do_live_result(&mut self, db: &CardDatabase) {
        super::performance::do_live_result(self, db);
    }
    pub fn finalize_live_result(&mut self) {
        super::performance::finalize_live_result(self);
    }

    // --- Phase Methods ---
    pub fn do_active_phase(&mut self, db: &CardDatabase) {
        if self.phase != Phase::Active { return; }
        let p_idx = self.current_player as usize;
        self.setup_turn_log();
        if !self.ui.silent { self.log(format!("Rule 7.4.1: [Active Phase] Untapping all cards for Player {}.", p_idx)); }
        self.core.players[p_idx].untap_all();
        let ctx = AbilityContext { source_card_id: -1, player_id: p_idx as u8, area_idx: -1, ..Default::default() };
        self.trigger_abilities(db, TriggerType::TurnStart, &ctx);
        if self.phase == Phase::Active {
            self.phase = Phase::Energy;
        }
    }

    pub fn auto_step(&mut self, db: &CardDatabase) {
        let mut loop_count = 0;
        while loop_count < 10 {
            if self.phase == Phase::Terminal || self.phase == Phase::Response { break; }
            if !self.interaction_stack.is_empty() { break; }

            let old_phase = self.phase;
            match self.phase {
                Phase::Active => self.do_active_phase(db),
                Phase::Energy => self.do_energy_phase(),
                Phase::Draw => self.do_draw_phase(db),
                Phase::PerformanceP1 | Phase::PerformanceP2 => {
                    self.do_performance_phase(db);
                }
                Phase::LiveResult => {
                    if self.live_result_selection_pending {
                        // Waiting for player to select a success live card (600-602)
                        break;
                    } else {
                        // Run the full live result logic (score calc, success zone assignment, etc.)
                        self.do_live_result(db);
                    }
                }
                _ => {
                    if self.phase == old_phase { break; }
                }
            }
            if self.phase == old_phase && self.interaction_stack.is_empty() {
                 loop_count += 1;
            } else {
                 loop_count = 0; // Reset loop count if we are making progress
            }
            if loop_count >= 10 { break; }
        }
    }

    pub fn do_energy_phase(&mut self) {
        if self.phase != Phase::Energy { return; }
        let p_idx = self.current_player as usize;
        if let Some(card_id) = self.core.players[p_idx].energy_deck.pop() {
            if !self.ui.silent { self.log(format!("Rule 7.5.2: Player {} placed Energy from Energy Deck", p_idx)); }
            let idx = self.core.players[p_idx].energy_zone.len();
            self.core.players[p_idx].energy_zone.push(card_id);
            self.core.players[p_idx].set_energy_tapped(idx, false);
        }
        self.phase = Phase::Draw;
    }

    pub fn do_draw_phase(&mut self, db: &CardDatabase) {
        let p_idx = self.current_player as usize;

        let ctx = AbilityContext { source_card_id: -1, player_id: p_idx as u8, area_idx: -1, ..Default::default() };
        self.trigger_abilities(db, TriggerType::TurnStart, &ctx);

        if self.phase != Phase::Draw { return; }
        if !self.ui.silent { self.log(format!("Rule 7.6.2: Player {} draws a card.", p_idx)); }
        self.draw_cards(p_idx, 1);
        self.phase = Phase::Main;
    }

    pub fn set_live_cards(&mut self, player_idx: usize, card_ids: Vec<u32>) -> Result<(), String> {
        if card_ids.len() > 3 { return Err("Too many lives".to_string()); }
        // For logging purposes, we'd ideally show card names, but for now just count
        if !self.ui.silent { self.log(format!("Rule 8.2.2: Player {} sets {} cards to Live Zone.", player_idx, card_ids.len())); }

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
            if !placed { return Err("No empty live slots".to_string()); }
        }
        Ok(())
    }

    pub fn end_main_phase(&mut self, db: &CardDatabase) {
        if !self.ui.silent { self.log(format!("Rule 7.7.3: Player {} ends Main Phase.", self.current_player)); }

        // Dispatch TurnEnd trigger
        let ctx = AbilityContext { source_card_id: -1, player_id: self.current_player, area_idx: -1, ..Default::default() };
        self.trigger_abilities(db, TriggerType::TurnEnd, &ctx);

        if self.current_player == self.first_player {
            self.current_player = 1 - self.first_player;
            self.phase = Phase::Active;
        } else {
            self.phase = Phase::LiveSet;
            self.current_player = self.first_player;
        }
    }

    // --- INTERPRETER DELEGATION ---
    pub fn resolve_bytecode(&mut self, db: &CardDatabase, bytecode: &[i32], ctx_in: &AbilityContext) {
        super::interpreter::resolve_bytecode(self, db, bytecode, ctx_in);
    }

    pub fn check_condition(&self, db: &CardDatabase, p_idx: usize, cond: &Condition, ctx: &AbilityContext, depth: u32) -> bool {
        super::interpreter::check_condition(self, db, p_idx, cond, ctx, depth)
    }

    pub fn check_condition_opcode(&self, db: &CardDatabase, op: i32, val: i32, attr: u64, slot: i32, ctx: &AbilityContext, depth: u32) -> bool {
        super::interpreter::check_condition_opcode(self, db, op, val, attr, slot, ctx, depth)
    }

    pub fn check_cost(&self, db: &CardDatabase, p_idx: usize, cost: &Cost, ctx: &AbilityContext) -> bool {
        super::interpreter::check_cost(self, db, p_idx, cost, ctx)
    }

    pub fn pay_cost(&mut self, db: &CardDatabase, p_idx: usize, cost: &Cost, ctx: &AbilityContext) -> bool {
        super::interpreter::pay_cost(self, db, p_idx, cost, ctx)
    }

    pub fn process_trigger_queue(&mut self, db: &CardDatabase) {
        super::interpreter::process_trigger_queue(self, db);
    }

    pub fn check_once_per_turn(&self, p_idx: usize, source_type: u8, id: u32, ab_idx: usize) -> bool {
        super::interpreter::check_once_per_turn(self, p_idx, source_type, id, ab_idx)
    }

    pub fn consume_once_per_turn(&mut self, p_idx: usize, source_type: u8, id: u32, ab_idx: usize) {
        super::interpreter::consume_once_per_turn(self, p_idx, source_type, id, ab_idx);
    }

    pub fn execute_mulligan(&mut self, player_idx: usize, discard_indices: Vec<usize>) {
        self.log(format!("Rule 6.2.1.6: Player {} finished mulligan ({} cards)", player_idx, discard_indices.len()));
        let mut count = 0;
        let mut discards = Vec::new();
        let mut new_hand = SmallVec::new();
        for (i, &cid) in self.core.players[player_idx].hand.iter().enumerate() {
            if discard_indices.contains(&i) { discards.push(cid); count += 1; }
            else { new_hand.push(cid); }
        }
        self.core.players[player_idx].hand = new_hand;
        let t = self.turn as i32;
        for _ in 0..count {
            if self.core.players[player_idx].deck.is_empty() { self.resolve_deck_refresh(player_idx); }
            if let Some(card_id) = self.core.players[player_idx].deck.pop() {
                self.core.players[player_idx].hand.push(card_id);
                self.core.players[player_idx].hand_added_turn.push(t);
            }
        }
        // If deck still empty and discard has cards, we already refreshed above or it's empty
        self.core.players[player_idx].deck.extend(discards);
        let mut rng = Pcg64::from_os_rng();
        self.core.players[player_idx].deck.shuffle(&mut rng);
        self.resolve_deck_refresh(player_idx);
        if self.phase == Phase::MulliganP1 { self.current_player = 1 - self.first_player; self.phase = Phase::MulliganP2; }
        else if self.phase == Phase::MulliganP2 { self.current_player = self.first_player; self.phase = Phase::Active; }
    }

    pub fn play_member(&mut self, db: &CardDatabase, hand_idx: usize, slot_idx: usize) -> Result<(), String> {
        self.play_member_with_choice(db, hand_idx, slot_idx, -1, -1, 0)
    }

    pub fn play_member_with_choice(&mut self, db: &CardDatabase, hand_idx: usize, slot_idx: usize, secondary_slot_idx: i16, choice_idx: i32, start_ab_idx: usize) -> Result<(), String> {
        let p_idx = self.current_player as usize;

        // 1. Resumption Case (Response Phase)
        if self.phase == Phase::Response {
            return self.resume_play_member(db, choice_idx, start_ab_idx);
        }

        // 2. Fresh Play Case
        if hand_idx >= self.core.players[p_idx].hand.len() { return Err("Invalid hand index".to_string()); }
        if slot_idx >= 3 { return Err("Invalid slot index".to_string()); }

        let card_id = self.core.players[p_idx].hand[hand_idx];
        let card = db.get_member(card_id).ok_or("Card not found")?;
        
        // Check legality
        self.check_play_legality(db, p_idx, card_id, slot_idx, secondary_slot_idx)?;

        // Calculate and Pay Cost
        let mut cost = self.get_member_cost(p_idx, card_id, slot_idx as i16, secondary_slot_idx, db, 0);
        cost = cost.max(0);
        let untap_energy_indices = self.core.players[p_idx].get_untapped_energy_indices(cost as usize);
        
        if !self.debug.debug_ignore_conditions {
            if untap_energy_indices.len() < cost as usize {
                return Err("Not enough energy".to_string());
            }
            for i in untap_energy_indices {
                 self.core.players[p_idx].set_energy_tapped(i, true);
            }
        }

        if !self.ui.silent { 
            self.log(format!("Rule 7.7.2.2: Player {} plays {} to Slot {}", p_idx, card.name, slot_idx)); 
            self.log_turn_event("PLAY", card_id, -1, p_idx as u8, &format!("Plays {} to Slot {}", card.name, slot_idx + 1));
        }

        // Execute state changes
        self.execute_play_member_state(db, p_idx, hand_idx, card_id, slot_idx, secondary_slot_idx, start_ab_idx);
        
        Ok(())
    }

    fn resume_play_member(&mut self, db: &CardDatabase, choice_idx: i32, start_ab_idx: usize) -> Result<(), String> {
        let (card_id, ctx, orig_phase) = if let Some(pi) = self.interaction_stack.last() {
            let mut c = pi.ctx.clone();
            c.choice_index = choice_idx as i16;
            (pi.card_id, c, pi.original_phase)
        } else {
            return Err("No pending interaction found in Response phase".to_string());
        };

        let card = db.get_member(card_id as i32).ok_or("Card not found")?;
        if !self.ui.silent { self.log_rule("Rule 11.3", &format!("Resuming [登場] (On Play) abilities for {} from idx {}.", card.name, start_ab_idx)); }

        self.phase = orig_phase;
        if self.phase == Phase::Response || self.phase == Phase::Setup {
            self.phase = Phase::Main; 
        }
        self.interaction_stack.pop();

        self.trigger_abilities_from(db, TriggerType::OnPlay, &ctx, start_ab_idx);
        self.process_rule_checks();
        Ok(())
    }

    fn check_play_legality(&self, db: &CardDatabase, p_idx: usize, _card_id: i32, slot_idx: usize, secondary_slot_idx: i16) -> Result<(), String> {
        if self.debug.debug_ignore_conditions { return Ok(()); }
        
        let player = &self.core.players[p_idx];
        if (player.prevent_play_to_slot_mask & (1 << slot_idx)) != 0 {
            return Err("Cannot play to this slot due to restriction".to_string());
        }
        if player.is_moved(slot_idx) {
            return Err("Already played/moved to this slot this turn".to_string());
        }

        let old_card_id = player.stage[slot_idx];
        if old_card_id >= 0 {
            if player.baton_touch_count >= player.baton_touch_limit {
                return Err("Baton touch limit reached".to_string());
            }
            if player.prevent_baton_touch > 0 {
                return Err("Baton Touch is restricted".to_string());
            }
            if has_restriction(self, p_idx, slot_idx, O_PREVENT_BATON_TOUCH, db) {
                return Err("Baton Touch is not allowed for this member".to_string());
            }
        }

        if secondary_slot_idx >= 0 {
            let s_idx = secondary_slot_idx as usize;
            if s_idx >= 3 || player.stage[s_idx] < 0 || player.is_moved(s_idx) {
                return Err("Invalid secondary baton touch target".to_string());
            }
        }
        
        Ok(())
    }

    fn execute_play_member_state(&mut self, db: &CardDatabase, p_idx: usize, hand_idx: usize, card_id: i32, slot_idx: usize, secondary_slot_idx: i16, start_ab_idx: usize) {
        let old_card_id = self.core.players[p_idx].stage[slot_idx];
        
        // 1. Baton Touch Counts
        if old_card_id >= 0 { self.core.players[p_idx].baton_touch_count += 1; }
        if secondary_slot_idx >= 0 {
            self.core.players[p_idx].baton_touch_count += 1;
            let s_idx = secondary_slot_idx as usize;
            if let Some(old) = self.handle_member_leaves_stage(p_idx, s_idx, db, &AbilityContext { player_id: p_idx as u8, area_idx: s_idx as i16, ..Default::default() }) {
                self.core.players[p_idx].discard.push(old);
            }
            self.core.players[p_idx].set_moved(s_idx, true);
        }

        // 2. Movement
        self.core.players[p_idx].hand.remove(hand_idx);
        if hand_idx < self.core.players[p_idx].hand_added_turn.len() {
            self.core.players[p_idx].hand_added_turn.remove(hand_idx);
        }

        if old_card_id >= 0 {
            let leave_ctx = AbilityContext { player_id: p_idx as u8, source_card_id: old_card_id, area_idx: slot_idx as i16, ..Default::default() };
            self.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);
            self.core.players[p_idx].discard.push(old_card_id);
        }

        self.prev_card_id = old_card_id;
        self.core.players[p_idx].stage[slot_idx] = card_id;
        self.core.players[p_idx].set_tapped(slot_idx, false);
        self.core.players[p_idx].set_moved(slot_idx, true);

        // 3. Trigger OnPlay
        let card = db.get_member(card_id).unwrap();
        for &gid in &card.groups {
            self.core.players[p_idx].played_group_mask |= 1 << gid;
        }

        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            area_idx: slot_idx as i16,
            ..Default::default()
        };

        if !self.ui.silent && card.abilities.iter().any(|ab| ab.trigger == TriggerType::OnPlay) {
            self.log_rule("Rule 11.3", &format!("Triggering [登場] (On Play) abilities for {}.", card.name));
        }
        self.trigger_abilities_from(db, TriggerType::OnPlay, &ctx, start_ab_idx);
        self.process_rule_checks();
    }

    pub fn is_trigger_negated(&self, p_idx: usize, cid: i32, trigger_type: TriggerType) -> bool {
        let player = &self.core.players[p_idx];
        player.negated_triggers.iter().any(|(t_cid, t_trigger, _)| {
            *t_cid == cid && *t_trigger == trigger_type
        })
    }

    pub fn trigger_abilities(&mut self, db: &CardDatabase, trigger: TriggerType, ctx: &AbilityContext) {
        self.trigger_abilities_from(db, trigger, ctx, 0);
    }

    pub fn trigger_abilities_from(&mut self, db: &CardDatabase, trigger: TriggerType, ctx: &AbilityContext, start_ab_idx: usize) {
        if self.trigger_depth > 10 {
            if !self.ui.silent { self.log(format!("Trigger depth limit reached for {:?}.", trigger)); }
            return;
        }
        self.trigger_depth += 1;

        // Collect all potential triggers
        let mut queue = Vec::new();
        let p_idx = ctx.player_id as usize;
        
        // 1. Stage Members
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].stage[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, false, &mut queue);
        }

        // 2. Performance/Live Cards
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].live_zone[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, true, &mut queue);
        }

        // 3. Source Card (if not on stage/live)
        let source_cid = ctx.source_card_id;
        let on_stage = self.core.players[p_idx].stage.iter().any(|&c| c == source_cid);
        let on_live = self.core.players[p_idx].live_zone.iter().any(|&c| c == source_cid);
        if !on_stage && !on_live && source_cid >= 0 {
            self.collect_triggers_for_card(db, source_cid, trigger, ctx, start_ab_idx, false, &mut queue);
            self.collect_triggers_for_card(db, source_cid, trigger, ctx, start_ab_idx, true, &mut queue);
        }

        for (cid, ab_idx, mut ab_ctx, is_live) in queue {
            ab_ctx.source_card_id = cid;
            ab_ctx.ability_index = ab_idx as i16;
            
            if !self.ui.silent {
                let card_name = if is_live { db.get_live(cid).unwrap().name.clone() } else { db.get_member(cid).unwrap().name.clone() };
                self.log_turn_event("TRIGGER", cid, ab_idx as i16, p_idx as u8, &format!("Triggering {}", card_name));
            }
            
            let (bytecode, conditions) = if is_live {
                let ab = &db.get_live(cid).unwrap().abilities[ab_idx as usize];
                (&ab.bytecode, &ab.conditions)
            } else {
                let ab = &db.get_member(cid).unwrap().abilities[ab_idx as usize];
                (&ab.bytecode, &ab.conditions)
            };

            // Check conditions before resolving bytecode
            let mut all_met = true;
            for cond in conditions {
                if !self.check_condition_opcode(db, cond.condition_type as i32, cond.value, cond.attr, cond.target_slot as i32, &ab_ctx, 1) {
                    all_met = false;
                    break;
                }
            }

            if all_met {
                self.resolve_bytecode(db, bytecode, &ab_ctx);
            } else {
                if !self.ui.silent { self.log(format!("Triggered ability of {} (Index {}) skipped due to unmet conditions.", cid, ab_idx)); }
            }
        }

        self.trigger_depth -= 1;
    }

    pub fn activate_ability(&mut self, db: &CardDatabase, slot_idx: usize, ab_idx: usize) -> Result<(), String> {
        self.activate_ability_with_choice(db, slot_idx, ab_idx, -1, 0)
    }

    pub fn activate_ability_with_choice(&mut self, db: &CardDatabase, slot_idx: usize, ab_idx: usize, choice_idx: i32, target_slot: i32) -> Result<(), String> {
        let p_idx = self.current_player as usize;


        if self.phase == Phase::Response {
            // RESUMPTION: Skip costs and OncePerTurn tracking. Handles both Member and Live cards.
             let (cid, ctx_base, orig_phase, orig_cp) = if let Some(pi) = self.interaction_stack.last() {
                (pi.card_id, pi.ctx.clone(), pi.original_phase, pi.original_current_player)
            } else {
                return Err("No pending interaction found in Response phase".to_string());
            };

            let virtual_bc;
            let (card_name, bytecode) = if cid == -1 {
                // System interaction (e.g. manually pushed or generic cost payment)
                // v_remaining is used as 'v' to continue the count if applicable
                // We provide a dummy bytecode [op, v, a, s, RETURN, 0, 0, 0]
                let pi = self.interaction_stack.last().ok_or("No interaction pending")?;
                virtual_bc = vec![pi.effect_opcode, pi.ctx.v_remaining as i32, 0, 0, O_RETURN, 0, 0, 0];
                ("System".to_string(), &virtual_bc[..])
            } else if let Some(mem) = db.get_member(cid) {
                 let ab = mem.abilities.get(ab_idx).ok_or("Ability not found on member")?;
                 (mem.name.clone(), &ab.bytecode[..])
            } else if let Some(live) = db.get_live(cid) {
                 let ab = live.abilities.get(ab_idx).ok_or("Ability not found on live card")?;
                 (live.name.clone(), &ab.bytecode[..])
            } else {
                 return Err("Card not found in database for resumption".to_string());
            };

            let mut ctx = ctx_base;

            // Update choice
            ctx.choice_index = choice_idx as i16;
            if !self.ui.silent { 
                self.log(format!("Rule 7.7.2.1: Resuming ability of {} (Slot {}, Choice {})", card_name, slot_idx, choice_idx)); 
                self.log_turn_event("ACTIVATE", cid, ab_idx as i16, p_idx as u8, &format!("Resuming {} (Choice {})", card_name, choice_idx));
            }

            // Standardize resumption: Restore correct phase BEFORE execution.
            self.phase = orig_phase;
            self.current_player = orig_cp; // CRITICAL: Restore original current player
            if self.phase == Phase::Response || self.phase == Phase::Setup {
                self.phase = Phase::Main;
            }
            self.interaction_stack.pop();

            self.resolve_bytecode(db, bytecode, &ctx);
            self.process_rule_checks();

            // Safety: if Response phase with empty stack, restore to correct phase
            if self.phase == Phase::Response && self.interaction_stack.is_empty() {
                self.phase = orig_phase;
                if self.phase == Phase::Response || self.phase == Phase::Setup { self.phase = Phase::Main; }
            }
            return Ok(());
        }

        let cid = if slot_idx < 3 {
            let scid = self.core.players[p_idx].stage[slot_idx];
            if scid >= 0 { scid } else { self.core.players[p_idx].live_zone[slot_idx] }
        } else if slot_idx >= 100 && slot_idx < 200 {
            let d_idx = slot_idx - 100;
            if d_idx < self.core.players[p_idx].discard.len() {
                self.core.players[p_idx].discard[d_idx]
            } else { -1 }
        } else { -1 };

        let card = db.get_member(cid).ok_or_else(|| format!("Card not found: {}", cid))?;
        let ab = if self.debug.debug_ignore_conditions {
             // Archetype tests might use ab_idx that doesn't exist on the card if mapping is loose
             match card.abilities.get(ab_idx) {
                 Some(a) => a,
                 None => {
                     if !self.ui.silent { self.log(format!("BYPASS: Ability index {} not found on {}. Skipping activation.", ab_idx, card.name)); }
                     return Ok(());
                 }
             }
        } else {
             card.abilities.get(ab_idx).ok_or_else(|| format!("Ability index {} not found on {}", ab_idx, card.name))?
        };

        if !self.debug.debug_ignore_conditions && ab.trigger != TriggerType::Activated && self.phase != Phase::Response && !self.ui.silent {
             return Err("Not an activated ability".to_string());
        }

        if !self.debug.debug_ignore_conditions && self.core.players[p_idx].prevent_activate > 0 {
            return Err("Cannot activate abilities due to restriction".to_string());
        }

        if !self.ui.silent { 
            self.log(format!("Rule 7.7.2.1: Player {} activates ability of {} (Slot {}, Choice {})", p_idx, card.name, slot_idx, choice_idx)); 
            self.log_turn_event("ACTIVATE", cid, ab_idx as i16, p_idx as u8, &format!("Activates {} (Choice {})", card.name, choice_idx));
        }

        let ctx = AbilityContext {
            source_card_id: cid,
            player_id: p_idx as u8,
            area_idx: slot_idx as i16,
            choice_index: choice_idx as i16,
            target_slot: target_slot as i16,
            ability_index: ab_idx as i16,
            ..Default::default()
        };

        // Check costs
        if !self.debug.debug_ignore_conditions {
            for cost in &ab.costs {
                if !self.check_cost(db, p_idx, cost, &ctx) { return Err("Cannot afford cost".to_string()); }
            }
            // Check conditions
            for cond in &ab.conditions {
                if !self.check_condition(db, p_idx, cond, &ctx, 0) { return Err("Conditions not met".to_string()); }
            }
        }

        // Track Once Per Turn
        if ab.is_once_per_turn {
            let (st, uid_id) = if slot_idx >= 100 { (2, cid as u32) } else { (1, slot_idx as u32) };
            if !self.debug.debug_ignore_conditions && !self.check_once_per_turn(p_idx, st, uid_id, ab_idx) {
                return Err(format!("Ability already used this turn (ST={}, ID={}, AB={})", st, uid_id, ab_idx));
            }
            self.consume_once_per_turn(p_idx, st, uid_id, ab_idx);
        }

        // Pay Costs
        // Removed: Bytecode now handles all cost payments natively (via O_PAY_ENERGY, etc.)
        // to prevent double-charging. Metadata costs are strictly for validation (check_cost).

        // Run
        self.resolve_bytecode(db, &ab.bytecode, &ctx);
        self.process_rule_checks();

        // If we are in Response phase (paused for input), return immediately
        if self.phase == Phase::Response {
            return Ok(());
        }

        // Phase restoration is handled by resumption logic.
        Ok(())
    }

    pub fn handle_rps(&mut self, action: i32) -> Result<(), String> {
        let (p_idx, choice) = if action >= 11000 {
            (1, action - 11000)
        } else if action >= 10000 {
            (0, action - 10000)
        } else {
             return Ok(());
        };

        if choice < 0 || choice > 2 { return Err("Invalid RPS choice".to_string()); }

        if self.rps_choices[p_idx] != -1 {
            if self.rps_choices[p_idx] == choice as i8 {
                return Ok(()); // Idempotent
            }
            return Err(format!("Player {} already chose a different move ({})", p_idx, self.rps_choices[p_idx]));
        }

        self.rps_choices[p_idx] = choice as i8;

        // Toggle current_player if only one has chosen, to help engine-external loops (like Python server) know who should act next
        if self.rps_choices[0] != -1 && self.rps_choices[1] == -1 {
            self.current_player = 1;
        } else if self.rps_choices[1] != -1 && self.rps_choices[0] == -1 {
            self.current_player = 0;
        }

        let names = ["Rock", "Paper", "Scissors"];

        if !self.ui.silent {
            if self.rps_choices[0] != -1 && self.rps_choices[1] != -1 {
                // Resolution will log the actual choices
            } else {
                self.log(format!("Player {} has made a decision.", p_idx));
            }
        }

        if self.rps_choices[0] != -1 && self.rps_choices[1] != -1 {
            let c0 = self.rps_choices[0];
            let c1 = self.rps_choices[1];

            if c0 == c1 {
                self.log(format!("Draw! (Both chose {}). Playing RPS again.", names[c0 as usize]));
                self.rps_choices = [-1; 2];
            } else {
                let p0_wins = (c0 == 0 && c1 == 2) || (c0 == 1 && c1 == 0) || (c0 == 2 && c1 == 1);
                let winner = if p0_wins { 0 } else { 1 };
                self.log(format!("Player {} wins RPS and must choose turn order.", winner));
                self.current_player = winner;
                self.phase = Phase::TurnChoice;
            }
        }
        Ok(())
    }

    fn collect_triggers_for_card(
        &mut self,
        db: &CardDatabase,
        cid: i32,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
        is_live: bool,
        queue: &mut Vec<(i32, u16, AbilityContext, bool)>,
    ) {
        if cid < 0 { return; }
        
        let abilities = if is_live {
            db.get_live(cid).map(|l| &l.abilities)
        } else {
            db.get_member(cid).map(|m| &m.abilities)
        };

        if let Some(abs) = abilities {
            let p_idx = ctx.player_id as usize;
            for (ab_idx, ab) in abs.iter().enumerate() {
                if ab.trigger == trigger {
                    // Filter OnPlay/OnLeaves to only the specific card being moved
                    if (trigger == TriggerType::OnPlay || trigger == TriggerType::OnLeaves) && cid != ctx.source_card_id {
                        continue;
                    }

                    if trigger != ctx.trigger_type || ab_idx >= start_ab_idx {
                        // Check and consume negation
                        let mut negated = false;
                        if let Some(n_idx) = self.core.players[p_idx].negated_triggers.iter().position(|&(t_cid, t_trig, count)| t_cid == cid && t_trig == trigger && count > 0) {
                            self.core.players[p_idx].negated_triggers[n_idx].2 -= 1;
                            negated = true;
                        }

                        if negated {
                            if !self.ui.silent { self.log(format!("Trigger {:?} for card {} is negated.", trigger, cid)); }
                            continue;
                        }
                        queue.push((cid, ab_idx as u16, ctx.clone(), is_live));
                    }
                }
            }
        }
    }

    pub fn step(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        self.prev_phase = self.phase;
        self.step_internal(db, action)?;
        self.auto_step(db);
        Ok(())
    }

    fn step_internal(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        // eprintln!("TRACE: step phase={:?} action={}", self.phase, action);
        match self.phase {
            Phase::Rps => self.handle_rps(action)?,
            Phase::TurnChoice => {
                if action == Self::ACTION_TURN_CHOICE_FIRST {
                    let winner = self.current_player;
                    self.first_player = winner;
                    self.log(format!("Player {} chose to go first!", winner));
                    self.phase = Phase::MulliganP1;
                    self.current_player = winner;
                } else if action == Self::ACTION_TURN_CHOICE_SECOND {
                    let winner = self.current_player;
                    self.first_player = 1 - winner;
                    self.log(format!("Player {} chose to go second!", winner));
                    self.phase = Phase::MulliganP1;
                    self.current_player = 1 - winner;
                }
            },
            Phase::MulliganP1 | Phase::MulliganP2 => {
                let p_idx = self.current_player as usize;
                if action == 0 {
                    let mut discards = Vec::new();
                    for i in 0..60 {
                        if (self.core.players[p_idx].mulligan_selection >> i) & 1 == 1 {
                            discards.push(i as usize);
                        }
                    }
                    self.execute_mulligan(p_idx, discards);
                } else if action >= ACTION_BASE_MULLIGAN && action <= ACTION_BASE_MULLIGAN + 59 {
                    let card_idx = (action - ACTION_BASE_MULLIGAN) as u16;
                    if (card_idx as usize) < self.core.players[p_idx].hand.len() {
                        self.core.players[p_idx].mulligan_selection ^= 1u64 << card_idx;
                    }
                }
            },
            Phase::Active => { self.do_active_phase(db); },
            Phase::Energy => { self.do_energy_phase(); },
            Phase::Draw => { self.do_draw_phase(db); },
            Phase::Main => {
                if action == 0 { 
                    self.end_main_phase(db); 
                } else if action >= ACTION_BASE_HAND && action < ACTION_BASE_HAND_CHOICE {
                    let adj = (action - ACTION_BASE_HAND) as usize;
                    let hand_idx = adj / 10;
                    let offset = adj % 10;
                    if offset < 3 {
                        let slot_idx = offset;
                        self.play_member_with_choice(db, hand_idx, slot_idx, -1, -1, 0)?;
                    } else if offset >= 3 && offset < 9 {
                        let combo_idx = (offset - 3) as usize;
                        let slot_idx = (combo_idx / 2) as usize;
                        let is_next = (combo_idx % 2) == 1;
                        let other_slot = Self::get_combo_other_slot(slot_idx, is_next);
                        self.play_member_with_choice(db, hand_idx, slot_idx, other_slot as i16, -1, 0)?;
                    }
                } else if action >= ACTION_BASE_HAND_CHOICE && action < ACTION_BASE_HAND_SELECT {
                    let adj = (action - ACTION_BASE_HAND_CHOICE) as usize;
                    let hand_idx = adj / 100;
                    let rem = adj % 100;
                    let slot_idx = rem / 10;
                    let choice_idx = (rem % 10) as i32;
                    self.play_member_with_choice(db, hand_idx, slot_idx, -1, choice_idx, 0)?;
                } else if action >= ACTION_BASE_STAGE && action < ACTION_BASE_STAGE_CHOICE {
                    let adj = action - ACTION_BASE_STAGE;
                    let slot_idx = (adj / 100) as usize;
                    let ab_idx = ((adj % 100) / 10) as usize;
                    self.activate_ability(db, slot_idx, ab_idx)?;
                } else if action >= ACTION_BASE_STAGE_CHOICE && action < ACTION_BASE_DISCARD_ACTIVATE {
                    let adj = action - ACTION_BASE_STAGE_CHOICE;
                    let slot_idx = (adj / 100) as usize;
                    let ab_idx = ((adj % 100) / 10) as usize;
                    let choice_idx = (adj % 10) as i32;
                    self.activate_ability_with_choice(db, slot_idx, ab_idx, choice_idx, 0)?;
                } else if action >= ACTION_BASE_DISCARD_ACTIVATE && action < ACTION_BASE_DISCARD_ACTIVATE + 600 {
                    let adj = action - ACTION_BASE_DISCARD_ACTIVATE;
                    let discard_idx = (adj / 10) as usize;
                    let ab_idx = (adj % 10) as usize;
                    self.activate_ability_with_choice(db, 100 + discard_idx, ab_idx, -1, -1)?;
                }
            },
            Phase::LiveSet => {
                let p_idx = self.current_player as usize;
                if action == 0 {
                    let draws = self.live_set_pending_draws[p_idx];
                    if draws > 0 {
                        if !self.ui.silent { self.log(format!("Rule 8.2.2: Live Set End: Player {} draws {} cards.", p_idx, draws)); }
                        self.draw_cards(p_idx, draws as u32);
                        self.live_set_pending_draws[p_idx] = 0;
                    }

                    if self.current_player == self.first_player {
                        self.current_player = 1 - self.first_player;
                    } else {
                        self.phase = Phase::PerformanceP1;
                        self.current_player = self.first_player;
                    }
                } else if action >= ACTION_BASE_LIVESET && action < ACTION_BASE_LIVESET + 100 {
                    let hand_idx = (action - ACTION_BASE_LIVESET) as usize;
                    if hand_idx < self.core.players[p_idx].hand.len() {
                        let cid = self.core.players[p_idx].hand[hand_idx];
                        self.core.players[p_idx].hand.remove(hand_idx);
                        for i in 0..3 {
                             if self.core.players[p_idx].live_zone[i] == -1 {
                                 self.core.players[p_idx].live_zone[i] = cid;
                                 self.core.players[p_idx].set_revealed(i, false);
                                 self.live_set_pending_draws[p_idx] += 1;
                                 if !self.ui.silent { self.log(format!("Rule 8.2.2: Player {} sets live card. Draw pending (+1).", p_idx)); }
                                 break;
                             }
                        }
                    }
                }
            },
            Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::Terminal => {},
            Phase::LiveResult => {
                if action == 0 {
                    self.do_live_result(db);
                } else if action >= 600 && action <= 602 {
                    let p_idx = self.current_player as usize;
                    let slot_idx = (action - 600) as usize;
                    let cid = self.core.players[p_idx].live_zone[slot_idx];
                    if cid >= 0 {
                        // Check for prevention (O_PREVENT_SET_TO_SUCCESS_PILE = 80)
                        let is_prevented = if let Some(card) = db.get_live(cid) {
                    card.abilities.iter().any(|a| a.effects.iter().any(|e| e.effect_type == EffectType::PreventSetToSuccessPile))
                } else { false };

                        self.core.players[p_idx].live_zone[slot_idx] = -1;

                        if is_prevented {
                            if !self.ui.silent { self.log(format!("Player {} SELECTED Success Live prevented by effect. Moving to discard: Card ID {}", p_idx, cid)); }
                             self.core.players[p_idx].discard.push(cid);
                        } else {
                            self.core.players[p_idx].success_lives.push(cid);
                            self.obtained_success_live[p_idx] = true;
                            if !self.ui.silent { self.log(format!("Player {} SELECTED Success Live: Card ID {}", p_idx, cid)); }
                        }
                        self.do_live_result(db);
                    }
                }
            },
            Phase::Response => {
                let pi = if let Some(p) = self.interaction_stack.last() { p } else { return Ok(()); };
                let _ctx = &pi.ctx;
                let _opcode = pi.effect_opcode;
                let _ab_idx = pi.ability_index;
                let _filter_attr = pi.filter_attr;

                // Unified choice index extraction from action using standardized ranges
                let choice_idx = if action == 0 {
                    99 // "Done/Discard Rest/Skip" signal
                }
                else if action >= ACTION_BASE_MODE && action < ACTION_BASE_MODE + 100 {
                    action - ACTION_BASE_MODE
                }
                else if action >= ACTION_BASE_HAND && action < ACTION_BASE_HAND + 100 {
                    action - ACTION_BASE_HAND
                }
                else if action >= ACTION_BASE_HAND_SELECT && action < ACTION_BASE_HAND_SELECT + 1000 {
                    action - ACTION_BASE_HAND_SELECT
                }
                else if action >= ACTION_BASE_COLOR && action < ACTION_BASE_COLOR + 10 {
                    action - ACTION_BASE_COLOR
                }
                else if action >= ACTION_BASE_ENERGY && action < ACTION_BASE_ENERGY + 100 {
                    action - ACTION_BASE_ENERGY
                }
                else if action >= ACTION_BASE_CHOICE && action < ACTION_BASE_CHOICE + 2000 {
                    action - ACTION_BASE_CHOICE
                }
                else if action >= ACTION_BASE_STAGE_SLOTS && action < ACTION_BASE_STAGE_SLOTS + 20 {
                    action - ACTION_BASE_STAGE_SLOTS
                }
                else {
                    -1
                };

                // Resume ability with choice
                let ctx_res = pi.ctx.clone();
                let slot_idx = ctx_res.area_idx as usize;
                let ab_idx_call = if ctx_res.ability_index < 0 { 0 } else { ctx_res.ability_index as usize };
                let target_slot = ctx_res.target_slot as i32;

                self.activate_ability_with_choice(db, slot_idx, ab_idx_call, choice_idx, target_slot)?;
            },
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



    pub fn generate_legal_actions<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, receiver: &mut R) {
        receiver.reset();

        if self.phase == Phase::Rps {
            if self.rps_choices[p_idx] == -1 {
                let offset = if p_idx == 0 { 10000 } else { 11000 };
                receiver.add_action(offset + 0); // Rock
                receiver.add_action(offset + 1); // Paper
                receiver.add_action(offset + 2); // Scissors
            }
            return;
        }

        if self.phase == Phase::TurnChoice {
            if p_idx == self.current_player as usize {
                receiver.add_action(Self::ACTION_TURN_CHOICE_FIRST as usize);
                receiver.add_action(Self::ACTION_TURN_CHOICE_SECOND as usize);
            }
            return;
        }

        let player = &self.core.players[p_idx];

        match self.phase {
            Phase::Main => self.generate_main_actions(db, p_idx, receiver, player),
            Phase::LiveSet => self.generate_live_set_actions(p_idx, receiver, player),
            Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::Terminal => {
                receiver.add_action(0);
            }
            Phase::MulliganP1 | Phase::MulliganP2 => self.generate_mulligan_actions(p_idx, receiver, player),
            Phase::Active | Phase::Draw | Phase::LiveResult => self.generate_active_draw_live_result_actions(p_idx, receiver, player),
            Phase::Energy => {
                receiver.add_action(0); // Auto-draw from energy deck (Rule 7.5.2)
            }
            Phase::Response => {
                self.generate_response_actions(db, p_idx, receiver);
            }
            _ => { receiver.add_action(0); }
        }
    }

    /// Generate actions for Main phase: play members, activate abilities
    fn generate_main_actions<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, receiver: &mut R, player: &PlayerState) {
        receiver.add_action(0);

        // Optimization 3: Loop Hoisting
        let available_energy = (0..player.energy_zone.len()).filter(|&i| !player.is_energy_tapped(i)).count() as i32;

        // Pre-calculate stage slot costs
        let mut slot_costs = [0; 3];
        for s in 0..3 {
            if player.stage[s] >= 0 {
                 if let Some(prev) = db.get_member(player.stage[s]) {
                     slot_costs[s] = prev.cost as i32;
                 }
            }
        }

        // 1. Play Member from Hand
        for (hand_idx, &cid) in player.hand.iter().enumerate().take(60) {
            if let Some(card) = db.get_member(cid) {
                let base_cost = (card.cost as i32 - player.cost_reduction as i32).max(0);

                for slot_idx in 0..3 {
                    if player.is_moved(slot_idx) { continue; }

                    // Check play restriction
                    if (player.prevent_play_to_slot_mask & (1 << slot_idx)) != 0 { continue; }

                    let mut cost = base_cost;
                    if player.stage[slot_idx] >= 0 {
                        cost = (cost - slot_costs[slot_idx]).max(0);
                        // Check global baton touch prevention
                        if player.prevent_baton_touch > 0 { continue; }
                        // Check card-specific restriction (if implemented via O_META)
                        if has_restriction(self, p_idx, slot_idx, O_PREVENT_BATON_TOUCH, db) { continue; }
                    }

                    if cost <= available_energy {
                        // Check for OnPlay choices (Limit to first 10 cards to stay within Action ID space)
                        let mut has_choice_on_play = false;
                        if hand_idx < 10 {
                            for ab in &card.abilities {
                                if ab.trigger == TriggerType::OnPlay {
                                    // OPTIMIZATION: Use pre-computed flags
                                    let _has_look_choose = (ab.choice_flags & CHOICE_FLAG_LOOK) != 0;
                                    let has_select_mode = (ab.choice_flags & CHOICE_FLAG_MODE) != 0;
                                    let has_color_select = (ab.choice_flags & CHOICE_FLAG_COLOR) != 0;
                                    let _has_order_deck = (ab.choice_flags & CHOICE_FLAG_ORDER) != 0;

                                    if has_color_select {
                                        has_choice_on_play = true;
                                        for c in 0..6 {
                                            let choice_aid = ACTION_BASE_HAND_CHOICE + (hand_idx as i32 * 100) + (slot_idx as i32 * 10) + (c as i32);
                                            receiver.add_action(choice_aid as usize);
                                        }
                                    } else if has_select_mode {
                                        has_choice_on_play = true;
                                        let count = ab.choice_count as i32;
                                        for c in 0..count {
                                            let choice_aid = ACTION_BASE_HAND_CHOICE + (hand_idx as i32 * 100) + (slot_idx as i32 * 10) + (c as i32);
                                            receiver.add_action(choice_aid as usize);
                                        }
                                    }
                                }
                            }
                        }

                        if !has_choice_on_play {
                             let aid = ACTION_BASE_HAND + (hand_idx as i32 * 10) + slot_idx as i32;
                            receiver.add_action(aid as usize);
                        }

                        // Double Baton Touch (Card 560 etc.)
                        let multi_limit = crate::core::logic::rules::has_multi_baton(card);
                        if multi_limit >= 2 && hand_idx < 10 {
                            for other_slot in 0..3 {
                                if other_slot == slot_idx { continue; }
                                if player.stage[other_slot] < 0 { continue; }
                                if player.is_moved(other_slot) { continue; }

                                let combined_cost = (base_cost - slot_costs[slot_idx] - slot_costs[other_slot]).max(0);
                                if combined_cost <= available_energy {
                                    let is_next = other_slot == (slot_idx + 1) % 3;
                                    let combo_idx = slot_idx * 2 + (if is_next { 1 } else { 0 });
                                    let aid = ACTION_BASE_HAND + (hand_idx as i32 * 10) + 3 + combo_idx as i32;
                                    receiver.add_action(aid as usize);
                                }
                            }
                        }
                    }
                }
            }
        }

        // 2. Activate Stage Ability
        if player.prevent_activate == 0 {
            for slot_idx in 0..3 {
                if let Some(cid_val) = player.stage.get(slot_idx) {
                    let cid = *cid_val;
                    if cid >= 0 {
                        if let Some(card) = db.get_member(cid) {
                            for (ab_idx, ab) in card.abilities.iter().enumerate() {
                                if ab.trigger == TriggerType::Activated {
                                    let ctx = AbilityContext {
                                        player_id: self.current_player,
                                        area_idx: slot_idx as i16,
                                        source_card_id: cid,
                                        ..Default::default()
                                    };

                                    let cond_ok = ab.conditions.iter().all(|c| self.check_condition(db, p_idx, c, &ctx, 0));
                                    let cost_ok = ab.costs.iter().all(|c| self.check_cost(db, p_idx, c, &ctx));

                                    if cond_ok && cost_ok && self.check_once_per_turn(p_idx, 1, slot_idx as u32, ab_idx) {
                                        let ab_aid = ACTION_BASE_STAGE + (slot_idx as i32 * 100) + (ab_idx as i32 * 10);
                                        receiver.add_action(ab_aid as usize);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // 3. Activate Discard Ability
        if player.prevent_activate == 0 {
            for discard_idx in 0..self.core.players[p_idx].discard.len().min(60) {
                let cid = self.core.players[p_idx].discard[discard_idx];
                if let Some(card) = db.get_member(cid) {
                    for (ab_idx, ab) in card.abilities.iter().enumerate() {
                        if ab.trigger == TriggerType::Activated {
                            let ctx = AbilityContext {
                                player_id: self.current_player,
                                source_card_id: cid,
                                area_idx: -1,
                                ..Default::default()
                            };

                             // Validating if ability is allowed in discard
                             let allowed_in_discard = ab.conditions.iter().any(|c| c.condition_type == ConditionType::IsInDiscard);
                             if !allowed_in_discard {
                                 continue;
                             }

                            let cond_ok = ab.conditions.iter().all(|c| self.check_condition(db, p_idx, c, &ctx, 0));
                            let cost_ok = ab.costs.iter().all(|c| self.check_cost(db, p_idx, c, &ctx));

                            if cond_ok && cost_ok {
                                if self.check_once_per_turn(p_idx, 2, cid as u32, ab_idx) {
                                    // Discard activations use 6000 + idx * 10 + ab_idx
                                    let ab_aid = ACTION_BASE_DISCARD_ACTIVATE + (discard_idx as i32 * 10) + ab_idx as i32;
                                    receiver.add_action(ab_aid as usize);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    /// Generate actions for LiveSet phase
    fn generate_live_set_actions<R: ActionReceiver + ?Sized>(&self, _p_idx: usize, receiver: &mut R, player: &PlayerState) {
        receiver.add_action(0);
        if player.live_zone.iter().any(|&cid| cid == -1) {
            for i in 0..player.hand.len().min(60) {
                // Rule 8.2.2: Any card can be placed in the live zone.
                receiver.add_action((ACTION_BASE_LIVESET + i as i32) as usize);
            }
        }
    }

    /// Generate actions for Mulligan phase
    fn generate_mulligan_actions<R: ActionReceiver + ?Sized>(&self, _p_idx: usize, receiver: &mut R, player: &PlayerState) {
        // Action 0: Confirm
        receiver.add_action(0);
        // Actions 300-359: Toggle (One-way for AI to avoid loops)
        let hand_len = player.hand.len().min(60);
        for i in 0..hand_len {
            // Only legal if NOT already selected
            if (player.mulligan_selection >> i) & 1 == 0 {
                receiver.add_action((ACTION_BASE_MULLIGAN + i as i32) as usize);
            }
        }
    }

    /// Generate actions for Active/Draw/LiveResult phases
    fn generate_active_draw_live_result_actions<R: ActionReceiver + ?Sized>(&self, _p_idx: usize, receiver: &mut R, player: &PlayerState) {
        if self.phase == Phase::LiveResult && self.live_result_selection_pending {
            // Hide Action 0 if mandatory choice is active
        } else {
            receiver.add_action(0);
        }
        if self.phase == Phase::LiveResult {
            // Selection choices (600-602)
            for i in 0..3 {
                if player.live_zone[i] >= 0 {
                    receiver.add_action(600 + i);
                }
            }
        }
    }

    pub fn calculate_cost_delta(&self, db: &CardDatabase, card_id: i32, p_idx: usize) -> i32 {
        let mut delta = self.core.players[p_idx].cost_reduction as i32;
        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            ..Default::default()
        };
        for (cond, val) in &self.core.players[p_idx].cost_modifiers {
             if self.check_condition(db, p_idx, cond, &ctx, 1) {
                 delta += val;
             }
        }
        delta
    }

    pub fn integrated_step(&mut self, db: &CardDatabase, action: i32, opp_mode: u8, mcts_sims: usize, enable_rollout: bool) -> (f32, bool) {
         let prev_score = self.core.players[0].score as f32;

         // 1. Agent Step (if interactive)
         let is_interactive = match self.phase {
             Phase::Main | Phase::LiveSet | Phase::MulliganP1 | Phase::MulliganP2 | Phase::Response | Phase::LiveResult | Phase::Energy => true,
             _ => false,
         };

         if self.current_player == 0 && is_interactive {
             let _ = self.step(db, action);
         } else {
             // Auto-progress or illegal call - pass
             let _ = self.step(db, 0);
         }

         // 2. Loop until Agent Turn or Terminal
         while self.phase != Phase::Terminal {
             let is_int = match self.phase {
                 Phase::Main | Phase::LiveSet | Phase::MulliganP1 | Phase::MulliganP2 | Phase::Response | Phase::LiveResult | Phase::Energy => true,
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
                    let (stats, _) = mcts.search_custom(self, db, sims, 0.0, SearchHorizon::TurnEnd(), &heuristic, false, enable_rollout);
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

    pub fn evaluate<H: Heuristic>(&self, db: &CardDatabase, p0_baseline: u32, p1_baseline: u32, eval_mode: EvalMode, heuristic: &H) -> f32 {
        heuristic.evaluate(self, db, p0_baseline, p1_baseline, eval_mode, None, None)
    }

    fn generate_response_actions<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, receiver: &mut R) {
        let pi = if let Some(p) = self.interaction_stack.last() { p } else { return; };
        let ctx = &pi.ctx;
        let opcode = pi.effect_opcode;
        let choice_type = &pi.choice_type;
        let source_card_id = pi.ctx.source_card_id;

        if ctx.player_id as usize != p_idx {
            return;
        }

        let player = &self.core.players[p_idx];
        
        // 1. Determine action 0 (fallback)
        let mut allow_action_0 = true;
        if choice_type == "REVEAL_HAND" || choice_type == "SELECT_SWAP_SOURCE" || choice_type == "SELECT_SWAP_TARGET" || choice_type == "PAY_ENERGY" {
            allow_action_0 = false;
        }
        if allow_action_0 {
            receiver.add_action(0);
        }
        
        let member = db.get_member(source_card_id as i32);
        let live = db.get_live(source_card_id as i32);
        let abilities = if let Some(m) = member { Some(&m.abilities) } else { live.map(|l| &l.abilities) };

        match choice_type.as_str() {
            "OPTIONAL" => {
                receiver.add_action((ACTION_BASE_CHOICE + 0) as usize);
                return;
            }
            "PAY_ENERGY" => {
                for i in 0..player.energy_zone.len().min(16) {
                    if !player.is_energy_tapped(i) {
                        receiver.add_action((ACTION_BASE_ENERGY + i as i32) as usize);
                    }
                }
                return;
            }
            "REVEAL_HAND" => {
                for i in 0..player.hand.len() {
                    receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                return;
            }
            "SELECT_DISCARD" => {
                for i in 0..player.discard.len() {
                    receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                }
                return;
            }
            "SELECT_SWAP_SOURCE" => {
                for i in 0..player.success_lives.len() {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                }
                return;
            }
            "SELECT_SWAP_TARGET" => {
                for i in 0..player.hand.len() {
                    receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                return;
            }
            _ => {}
        }

        match opcode {
            O_TAP_MEMBER | O_TAP_OPPONENT => {
                for c in 0..3 {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + c as i32) as usize);
                }
                return;
            }
            O_ORDER_DECK => {
                let count = player.looked_cards.len();
                for c in 0..count {
                    if player.looked_cards[c] != -1 {
                        receiver.add_action((ACTION_BASE_CHOICE + c as i32) as usize);
                    }
                }
                return;
            }
            O_COLOR_SELECT => {
                for c in 0..6 {
                    receiver.add_action((ACTION_BASE_COLOR + c as i32) as usize);
                }
                return;
            }
            O_LOOK_AND_CHOOSE => {
                self.generate_look_and_choose_actions(db, p_idx, receiver, pi, abilities);
                return;
            }
            O_MOVE_TO_DISCARD => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if self.card_matches_filter(db, cid, pi.filter_attr) {
                        receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
                return;
            }
            O_RECOVER_MEMBER | O_RECOVER_LIVE => {
                let count = player.looked_cards.len();
                for i in 0..count {
                    let cid = player.looked_cards[i];
                    if cid != -1 && self.card_matches_filter(db, cid, (pi.filter_attr as u32) as u64) {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                receiver.add_action(0);
                return;
            }
            O_PLAY_MEMBER_FROM_HAND => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if self.card_matches_filter(db, cid, pi.filter_attr) {
                        receiver.add_action((ACTION_BASE_HAND + i as i32) as usize);
                    }
                }
                receiver.add_action(0);
                return;
            }
            O_SELECT_MEMBER => {
                self.generate_select_member_actions(db, p_idx, receiver, pi, pi.filter_attr);
                return;
            }
            O_SELECT_LIVE => {
                for i in 0..player.live_zone.len().min(10) {
                    if player.live_zone[i] >= 0 {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
                receiver.add_action(0);
                return;
            }
            O_SELECT_PLAYER => {
                receiver.add_action(0);
                receiver.add_action(1);
                return;
            }
            O_SELECT_MODE => {
                self.generate_select_mode_actions(db, p_idx, receiver, pi, abilities);
                return;
            }
            O_SELECT_CARDS => {
                for i in 0..player.hand.len() {
                    receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                if receiver.is_empty() { receiver.add_action(0); }
                return;
            }
            _ => {
                if choice_type == "SELECT_MEMBER" {
                    self.generate_select_member_actions(db, p_idx, receiver, pi, pi.filter_attr);
                    return;
                }
                if choice_type == "SELECT_STAGE" {
                    for i in 0..3 { receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize); }
                    return;
                }
                if choice_type == "SELECT_LIVE_SLOT" {
                    for i in 0..player.live_zone.len().min(10) {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                    return;
                }
            }
        }

        if receiver.is_empty() {
            receiver.add_action(0);
        }
    }

    fn generate_look_and_choose_actions<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, receiver: &mut R, pi: &PendingInteraction, abilities: Option<&Vec<Ability>>) {
        let player = &self.core.players[p_idx];
        let mut final_filter_attr = pi.filter_attr;
        if final_filter_attr == 0 {
            if let Some(abs) = abilities {
                let ab_idx_real = if pi.ability_index == -1 {
                    abs.iter().position(|ab| (ab.choice_flags & (CHOICE_FLAG_LOOK | CHOICE_FLAG_MODE | CHOICE_FLAG_COLOR | CHOICE_FLAG_ORDER)) != 0).unwrap_or(0)
                } else { pi.ability_index as usize };

                if let Some(ab) = abs.get(ab_idx_real) {
                    if let Some(chunk) = ab.bytecode.chunks(4).find(|ch| ch[0] == O_LOOK_AND_CHOOSE) {
                        final_filter_attr = (chunk[2] as u32) as u64;
                    }
                }
            }
        }

        match pi.choice_type.as_str() {
            "SELECT_HAND_DISCARD" => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if self.card_matches_filter(db, cid, final_filter_attr) {
                        receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
            }
            "SELECT_DISCARD_PLAY" => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if self.card_matches_filter(db, cid, final_filter_attr) {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            }
            "SELECT_STAGE" => {
                for i in 0..3 { receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize); }
            }
            "SELECT_LIVE_SLOT" => {
                for i in 0..player.live_zone.len().min(10) {
                    if player.live_zone[i] >= 0 { receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize); }
                }
            }
            "PAY_ENERGY" => {
                for i in 0..player.energy_zone.len().min(10) {
                    if !player.is_energy_tapped(i) {
                        receiver.add_action((ACTION_BASE_ENERGY + i as i32) as usize);
                    }
                }
            }
            _ => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    let filter_only = final_filter_attr & 0xFFFFFFFFFFFF0FFF;
                    if self.card_matches_filter(db, cid, filter_only) {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            }
        }
    }

    fn generate_select_member_actions<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, receiver: &mut R, pi: &PendingInteraction, filter_attr: u64) {
        let player = &self.core.players[p_idx];
        let packed_zone = (filter_attr >> 12) & 0x0F;
        let target_slot = if packed_zone > 0 { packed_zone as usize } else { 
            if pi.effect_opcode == O_SELECT_MEMBER || (pi.choice_type == "SELECT_MEMBER" && pi.effect_opcode == 0) {
                pi.target_slot as usize
            } else {
                crate::core::logic::interpreter::resolve_target_slot(pi.effect_opcode, &pi.ctx) 
            }
        };

        match target_slot {
            6 => { // Hand
                for i in 0..player.hand.len() {
                    let cid = player.hand[i];
                    if self.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
            },
            7 => { // Discard
                for i in 0..player.discard.len() {
                    let cid = player.discard[i];
                    if self.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            },
            _ => { // Stage (0-2) or Default
                for i in 0..3 {
                    let cid = player.stage[i];
                    if cid >= 0 && self.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
            }
        }
        receiver.add_action(0);
    }

    fn generate_select_mode_actions<R: ActionReceiver + ?Sized>(&self, _db: &CardDatabase, p_idx: usize, receiver: &mut R, pi: &PendingInteraction, abilities: Option<&Vec<Ability>>) {
        let count = if pi.v_remaining > 0 { pi.v_remaining as i32 } else { 4 };
        for i in 0..count {
            let mut option_valid = true;
            if let Some(abs) = abilities {
                let ab_idx_real = if pi.ability_index == -1 {
                    abs.iter().position(|ab| (ab.choice_flags & CHOICE_FLAG_MODE) != 0).unwrap_or(0)
                } else { pi.ability_index as usize };

                if ab_idx_real < abs.len() {
                    let ab = &abs[ab_idx_real];
                    let bc = &ab.bytecode;
                    
                    let mut ip = 0;
                    if let Some(pos) = bc.chunks(4).position(|chunk| chunk[0] == O_SELECT_MODE) {
                        ip = pos * 4;
                    }
                    
                    let target_ip = if i < 2 {
                        let offset = ip + 2 + i as usize;
                        if offset < bc.len() { bc[offset] as usize } else { 0 }
                    } else {
                        let offset = ip + 4 + (i as usize - 2);
                        if offset < bc.len() { bc[offset] as usize } else { 0 }
                    };
                    
                    if target_ip > 0 && target_ip < bc.len() {
                        let target_op = bc[target_ip];
                        if target_op == O_PAY_ENERGY || target_op == O_MOVE_TO_DISCARD || target_op == O_MOVE_TO_DECK {
                            let v = if target_ip + 1 < bc.len() { bc[target_ip + 1] } else { 0 };
                            let s = if target_ip + 3 < bc.len() { bc[target_ip + 3] } else { 0 };
                            
                            if target_op == O_PAY_ENERGY {
                                let available = (0..self.core.players[p_idx].energy_zone.len()).filter(|&idx| !self.core.players[p_idx].is_energy_tapped(idx)).count() as i32;
                                if available < v { option_valid = false; }
                            } else if target_op == O_MOVE_TO_DISCARD {
                                if s == 6 || s == 0 { // TargetType.CARD_HAND or Generic
                                    if (self.core.players[p_idx].hand.len() as i32) < v { option_valid = false; }
                                }
                            }
                        }
                    }
                }
            }
            
            if option_valid {
                receiver.add_action((ACTION_BASE_MODE + i as i32) as usize);
            }
        }
    }
}


// =======================================================================================
// Action Receiver Trait (Sparse Generation)
// =======================================================================================

pub trait ActionReceiver {
    fn add_action(&mut self, action_id: usize);
    fn reset(&mut self);
    fn is_empty(&self) -> bool;
}

impl ActionReceiver for [bool] {
    fn add_action(&mut self, action_id: usize) {
        if action_id < self.len() {
            self[action_id] = true;
        }
    }
    fn reset(&mut self) {
        self.fill(false);
    }
    fn is_empty(&self) -> bool {
        self.iter().all(|&b| !b)
    }
}

impl ActionReceiver for Vec<usize> {
    fn add_action(&mut self, action_id: usize) {
        if !self.contains(&action_id) {
            self.push(action_id);
        }
    }
    fn reset(&mut self) {
        self.clear();
    }
    fn is_empty(&self) -> bool {
        self.is_empty()
    }
}

impl ActionReceiver for Vec<i32> {
    fn add_action(&mut self, action_id: usize) {
        let aid = action_id as i32;
        if !self.contains(&aid) {
            self.push(aid);
        }
    }
    fn reset(&mut self) {
        self.clear();
    }
    fn is_empty(&self) -> bool {
        self.is_empty()
    }
}

impl<const N: usize> ActionReceiver for SmallVec<[i32; N]> {
    fn add_action(&mut self, action_id: usize) {
        let aid = action_id as i32;
        if !self.contains(&aid) {
            self.push(aid);
        }
    }
    fn reset(&mut self) {
        self.clear();
    }
    fn is_empty(&self) -> bool {
        self.is_empty()
    }
}

impl<const N: usize> ActionReceiver for SmallVec<[usize; N]> {
    fn add_action(&mut self, action_id: usize) {
        if !self.contains(&action_id) {
            self.push(action_id);
        }
    }
    fn reset(&mut self) {
        self.clear();
    }
    fn is_empty(&self) -> bool {
        self.is_empty()
    }
}

