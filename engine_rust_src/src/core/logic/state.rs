use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use rand::SeedableRng;
use rand::rngs::SmallRng;
use smallvec::SmallVec;

use crate::core::enums::*;
use super::models::*;
use super::player::*;

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
