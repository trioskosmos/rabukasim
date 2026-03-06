use rand::rngs::SmallRng;
use rand::SeedableRng;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;
use std::collections::{HashMap, HashSet, VecDeque};

use super::models::*;
use super::player::*;
use crate::core::enums::*;
use crate::core::logic::card_db::CardDatabase;
use crate::core::logic::models::{TurnEvent, AbilityContext};
// use crate::core::logic::constants::*;
// use crate::core::enums::Zone; // Remainder zone is currently int

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
    fn eq(&self, _other: &Self) -> bool {
        true
    }
}
impl Eq for BypassLog {}

impl Serialize for BypassLog {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_unit()
    }
}

impl<'de> Deserialize<'de> for BypassLog {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let _ = serde::de::IgnoredAny::deserialize(deserializer)?;
        Ok(Self::default())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoreGameState {
    pub players: [PlayerState; 2],
    #[serde(default)]
    pub current_player: u8,
    #[serde(default)]
    pub first_player: u8,
    #[serde(default)]
    pub phase: Phase,
    #[serde(default)]
    pub prev_phase: Phase,
    #[serde(default)]
    pub prev_card_id: i32,
    #[serde(default)]
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
    #[serde(default)]
    pub trigger_queue: VecDeque<(i32, u16, AbilityContext, bool, TriggerType)>,
    #[serde(skip, default = "SmallRng::from_os_rng")]
    pub rng: SmallRng,
    #[serde(default)]
    pub rps_choices: [i8; 2],
    #[serde(default)]
    pub score_req_list: Vec<u8>,
    #[serde(default)]
    pub score_req_player: i8,
    #[serde(default)]
    pub turn_history: Option<Vec<TurnEvent>>,
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
            score_req_list: Vec::new(),
            score_req_player: 0,
            turn_history: None,
            obtained_success_live: [false; 2],
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UIState {
    #[serde(default)]
    pub silent: bool,
    #[serde(default)]
    pub rule_log: Option<Vec<String>>,
    #[serde(default)]
    pub performance_results: HashMap<u8, serde_json::Value>,
    #[serde(default)]
    pub last_performance_results: HashMap<u8, serde_json::Value>,
    #[serde(default)]
    pub performance_history: Vec<serde_json::Value>,
    #[serde(default)]
    pub next_execution_id: u32,
    #[serde(default)]
    pub current_execution_id: Option<u32>,
    #[serde(default)]
    pub bytecode_log: Vec<String>,
}

impl Default for UIState {
    fn default() -> Self {
        Self {
            silent: false,
            rule_log: None,
            performance_results: HashMap::new(),
            last_performance_results: HashMap::new(),
            performance_history: Vec::new(),
            next_execution_id: 1,
            current_execution_id: None,
            bytecode_log: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DebugState {
    pub debug_ignore_conditions: bool,
    pub bypassed_conditions: Option<BypassLog>,
    pub debug_mode: bool,
    pub executed_opcodes: Option<HashSet<i32>>,
    #[serde(default)]
    pub trace_log: Vec<String>,
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

impl GameState {
    pub fn is_card_in_zone(&self, ctx_player_id: u8, target_player: u8, cid: i32, mask: u8) -> bool {
        // target_player: 1=Self, 2=Opponent, 3=Both, 0=Any
        let players_to_check: Vec<usize> = match target_player {
            1 => vec![ctx_player_id as usize],
            2 => vec![1 - (ctx_player_id as usize)],
            3 | 0 => vec![0, 1], // Both or Any
            _ => vec![ctx_player_id as usize],
        };

        for p_idx in players_to_check {
            let p = &self.players[p_idx];
            // mask is a Zone enum value (3-bit packed)
            // 4=STAGE, 6=HAND, 7=DISCARD, 3=ENERGY
            match mask {
                4 => {
                    if p.stage.iter().any(|&c| c == cid) { return true; }
                }
                6 => {
                    if p.hand.iter().any(|&c| c == cid) { return true; }
                }
                7 => {
                    if p.discard.iter().any(|&c| c == cid) { return true; }
                }
                3 => {
                    if p.energy_zone.iter().any(|&c| c == cid) { return true; }
                }
                _ => {
                    // fallback or other zones
                }
            }
        }
        false
    }

    pub fn get_card_ids_in_zone(&self, player_idx: u8, mask: u8) -> Vec<i32> {
        let p = &self.players[player_idx as usize];
        match mask {
            4 | 44 => p.stage.iter().filter(|&&c| c != -1).cloned().collect(), // STAGE
            6 | 66 => p.hand.iter().cloned().collect(), // HAND
            7 | 77 => p.discard.iter().cloned().collect(), // DISCARD
            3 | 33 => p.energy_zone.iter().cloned().collect(), // ENERGY
            15 => p.yell_cards.iter().cloned().collect(), // YELL
            _ => Vec::new(),
        }
    }

    pub fn render_debug_board(&self, db: &CardDatabase) -> String {
        let mut out = String::new();
        out.push_str(&format!("\n=== GAME STATE (Turn {}, Phase {:?}, Player {}) ===\n", self.turn, self.phase, self.current_player));
        
        for p_idx in 0..2 {
            let p = &self.players[p_idx];
            out.push_str(&format!("--- PLAYER {} ---\n", p_idx));
            out.push_str(&format!("  HAND:    {:?}\n", p.hand));
            
            out.push_str("  STAGE:   [");
            for (i, &cid) in p.stage.iter().enumerate() {
                if cid == -1 {
                    out.push_str(" EMPTY ");
                } else {
                    let name = db.get_member(cid).map(|c| c.name.as_str()).unwrap_or("Unknown");
                    let tapped = if p.is_tapped(i) { "(T)" } else { "" };
                    out.push_str(&format!(" {}{} ", name, tapped));
                }
                if i < p.stage.len() - 1 { out.push_str("|"); }
            }
            out.push_str("]\n");

            out.push_str("  LIVE:    [");
            for (i, &cid) in p.live_zone.iter().enumerate() {
                if cid == -1 {
                    out.push_str(" EMPTY ");
                } else {
                    let name = db.get_live(cid).map(|c| c.name.as_str()).unwrap_or("Unknown");
                    out.push_str(&format!(" {} ", name));
                }
                if i < p.live_zone.len() - 1 { out.push_str("|"); }
            }
            out.push_str("]\n");

            out.push_str(&format!("  ENERGY:  {} total, {} tapped (Mask: {:b})\n", p.energy_zone.len(), p.tapped_energy_mask.count_ones(), p.tapped_energy_mask));
            out.push_str(&format!("  DISCARD: {} cards\n", p.discard.len()));
            out.push_str(&format!("  SUCCESS: {} cards\n", p.success_lives.len()));
        }
        out.push_str("==========================================\n");
        out
    }
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



