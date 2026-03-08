use std::collections::{HashMap, VecDeque};
use std::sync::{Arc, Mutex};
use serde::Deserialize;
use std::time::SystemTime;
use engine_rust::core::logic::{GameState, CardDatabase};

pub struct Room {
    pub _id: String,
    pub state: GameState,
    pub players: HashMap<String, usize>, // Token -> Player ID (0 or 1)
    pub username_to_token: HashMap<String, String>, // Username -> Token (for recovery)
    pub mode: String, // "pve" or "pvp"
    pub last_update: SystemTime,
    pub created_at: SystemTime,
    pub is_public: bool,
    pub pending_decks: [Option<ParsedDecks>; 2],
    pub is_ai_thinking: bool,
    pub ai_status: String,
    pub history: VecDeque<GameState>,
    pub redo_history: VecDeque<GameState>,
}

pub struct AppState {
    pub rooms: Mutex<HashMap<String, Arc<Mutex<Room>>>>,
    pub card_db: CardDatabase,
    pub server_instance_id: u64,
    pub debug_mode: bool,
    #[cfg(feature = "nn")]
    pub model_session: Option<Arc<Mutex<ort::session::Session>>>,
}

// API Request Structures
#[derive(Deserialize)]
pub struct CreateRoomReq {
    pub mode: Option<String>,
    pub public: Option<bool>,
    pub username: Option<String>,
    pub p0_deck: Option<Vec<String>>,
    pub p1_deck: Option<Vec<String>>,
    pub p0_energy: Option<Vec<String>>,
    pub p1_energy: Option<Vec<String>>,
}

#[derive(Deserialize, Clone)]
pub struct DeckConfig {
    pub main: Vec<String>,
    pub energy: Vec<String>,
    #[serde(default)]
    #[serde(rename = "type")]
    pub _deck_type: String,
}

#[derive(Deserialize)]
pub struct JoinRoomReq {
    pub room_id: String,
    pub username: Option<String>,
    pub deck_id: Option<String>,
    pub deck_list: Option<Vec<String>>,
}

#[derive(Deserialize)]
pub struct ActionReq {
    pub action_id: i32,
}

#[derive(Deserialize)]
pub struct UploadDeckReq {
    pub player: usize,
    pub content: String, // Raw deck file content
}

#[derive(Deserialize)]
pub struct AiSuggestReq {
    pub sims: usize,
}

#[derive(Deserialize)]
#[allow(dead_code)]
pub struct SetDeckReq {
    pub player: usize,
    pub deck: Vec<String>,
    pub energy_deck: Option<Vec<String>>,
}

#[derive(Deserialize)]
pub struct PlayerBoardOverride {
    pub stage: Option<Vec<i32>>,
    pub live_zone: Option<Vec<i32>>,
    pub hand: Option<Vec<i32>>,
    pub energy: Option<Vec<i32>>,
    pub success_lives: Option<Vec<i32>>,
    pub discard: Option<Vec<i32>>,
}

#[derive(Deserialize)]
pub struct BoardOverrideReq {
    pub phase: Option<i8>,
    pub turn: Option<u16>,
    pub players: Vec<PlayerBoardOverride>,
}

#[derive(Clone)]
pub struct ParsedDecks {
    pub members: Vec<i32>,
    pub lives: Vec<i32>,
    pub energy: Vec<i32>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    Pass,
    ToggleMulligan { hand_idx: usize },
    PlayMember { hand_idx: usize, slot_idx: usize },
    ActivateAbility { slot_idx: usize, ab_idx: usize },
    SelectChoice { choice_idx: usize },
    SelectHand { hand_idx: usize },
    SelectResponseSlot { slot_idx: usize },
    SelectResponseColor { color_idx: u8 },
    ActivateAbilityWithChoice { slot_idx: usize, ab_idx: usize, choice_idx: usize },
    PlayMemberWithChoice { hand_idx: usize, slot_idx: usize, choice_idx: usize },
    PlayMemberDouble { hand_idx: usize, slot_idx: usize, other_slot: usize },
    ActivateFromDiscard { discard_idx: usize, ab_idx: usize },
    ActivateFromHand { hand_idx: usize, ab_idx: usize },
    PlaceLive { hand_idx: usize },
    Rps { choice: i8 },
    ChooseTurnOrder { first: bool },
    Formation { src_idx: usize, dst_idx: usize },
    Unknown(i32),
    SelectEnergy { energy_idx: usize },
}

impl Action {
    pub fn from_id(id: i32, phase: engine_rust::core::logic::Phase) -> Self {
        use engine_rust::core::logic::Phase;
        use engine_rust::core::generated_constants::*;
        match phase {
            Phase::Rps => Action::Rps { choice: (id % 10) as i8 },
            Phase::TurnChoice => Action::ChooseTurnOrder { first: id == ACTION_BASE_TURN_ORDER_FIRST },
            Phase::MulliganP1 | Phase::MulliganP2 => {
                if id == ACTION_BASE_PASS { Action::Pass }
                else if id >= ACTION_BASE_MULLIGAN && id < ACTION_BASE_LIVESET { Action::ToggleMulligan { hand_idx: (id - ACTION_BASE_MULLIGAN) as usize } }
                else { Action::Unknown(id) }
            },
            Phase::Main => {
                if id == ACTION_BASE_PASS { Action::Pass }
                else if id >= ACTION_BASE_HAND && id < ACTION_BASE_HAND_CHOICE {
                    let adj = (id - ACTION_BASE_HAND) as usize;
                    let hand_idx = adj / 10;
                    let offset = adj % 10;
                    if offset < 3 {
                        Action::PlayMember { hand_idx, slot_idx: offset }
                    } else if offset >= 3 && offset < 9 {
                        let combo_idx = offset - 3;
                        let slot_idx = (combo_idx / 2) as usize;
                        let is_next = (combo_idx % 2) == 1;
                        let other_slot = if slot_idx == 0 {
                            if is_next { 1 } else { 2 }
                        } else if slot_idx == 1 {
                            if is_next { 2 } else { 0 }
                        } else {
                            if is_next { 0 } else { 1 }
                        };
                        Action::PlayMemberDouble { hand_idx, slot_idx, other_slot }
                    } else {
                        Action::Unknown(id)
                    }
                } else if id >= ACTION_BASE_HAND_ACTIVATE && id < ACTION_BASE_HAND_CHOICE {
                    let adj = id - ACTION_BASE_HAND_ACTIVATE;
                    Action::ActivateFromHand {
                        hand_idx: (adj / 10) as usize,
                        ab_idx: (adj % 10) as usize
                    }
                } else if id >= ACTION_BASE_STAGE_CHOICE && id < ACTION_BASE_DISCARD_ACTIVATE {
                    let adj = id - ACTION_BASE_STAGE_CHOICE;
                    Action::ActivateAbilityWithChoice {
                        slot_idx: (adj / 100) as usize,
                        ab_idx: ((adj % 100) / 10) as usize,
                        choice_idx: (adj % 10) as usize
                    }
                } else if id >= ACTION_BASE_HAND_CHOICE && id < ACTION_BASE_HAND_SELECT {
                    let adj = id - ACTION_BASE_HAND_CHOICE;
                    Action::PlayMemberWithChoice {
                        hand_idx: (adj / 100) as usize,
                        slot_idx: ((adj % 100) / 10) as usize,
                        choice_idx: (adj % 10) as usize
                    }
                } else if id >= ACTION_BASE_DISCARD_ACTIVATE && id < ACTION_BASE_DISCARD_ACTIVATE + 600 {
                    let adj = id - ACTION_BASE_DISCARD_ACTIVATE;
                    Action::ActivateFromDiscard {
                        discard_idx: (adj / 10) as usize,
                        ab_idx: (adj % 10) as usize
                    }
                } else if id >= ACTION_BASE_STAGE && id < ACTION_BASE_STAGE_CHOICE {
                    let adj = id - ACTION_BASE_STAGE;
                    Action::ActivateAbility { slot_idx: (adj / 100) as usize, ab_idx: ((adj % 100) / 10) as usize }
                } else { Action::Unknown(id) }
            },
            Phase::LiveSet => {
                if id == ACTION_BASE_PASS { Action::Pass }
                else if id >= ACTION_BASE_LIVESET && id < ACTION_BASE_COLOR { Action::PlaceLive { hand_idx: (id - ACTION_BASE_LIVESET) as usize } }
                else { Action::Unknown(id) }
            },
            Phase::LiveResult => {
                if id == ACTION_BASE_PASS { Action::Pass }
                else if id >= ACTION_BASE_STAGE_SLOTS && id < ACTION_BASE_STAGE_SLOTS + 3 { Action::SelectChoice { choice_idx: (id - ACTION_BASE_STAGE_SLOTS) as usize } }
                else { Action::Unknown(id) }
            },
            Phase::Response => {
                if id == ACTION_BASE_PASS { Action::Pass }
                else if id >= ACTION_BASE_COLOR && id < ACTION_BASE_COLOR + 10 { Action::SelectResponseColor { color_idx: (id - ACTION_BASE_COLOR) as u8 } }
                else if id >= ACTION_BASE_STAGE_SLOTS && id < ACTION_BASE_STAGE_SLOTS + 20 { Action::SelectResponseSlot { slot_idx: (id - ACTION_BASE_STAGE_SLOTS) as usize } }
                else if id >= ACTION_BASE_HAND_SELECT && id < ACTION_BASE_STAGE { Action::SelectHand { hand_idx: (id - ACTION_BASE_HAND_SELECT) as usize } }
                else if id >= ACTION_BASE_HAND && id < ACTION_BASE_HAND_CHOICE { Action::SelectHand { hand_idx: (id - ACTION_BASE_HAND) as usize } }
                else if id >= ACTION_BASE_ENERGY && id < ACTION_BASE_CHOICE { Action::SelectEnergy { energy_idx: (id - ACTION_BASE_ENERGY) as usize } }
                else if id >= ACTION_BASE_CHOICE { Action::SelectChoice { choice_idx: (id - ACTION_BASE_CHOICE) as usize } }
                else if id >= ACTION_BASE_MODE && id < ACTION_BASE_COLOR { Action::SelectChoice { choice_idx: (id - ACTION_BASE_MODE) as usize } }
                else { Action::Unknown(id) }
            },
            _ => {
                if id == 0 { Action::Pass }
                else if id >= ACTION_BASE_CHOICE { Action::SelectChoice { choice_idx: (id - ACTION_BASE_CHOICE) as usize } }
                else if id >= ACTION_BASE_MODE && id < ACTION_BASE_COLOR { Action::SelectChoice { choice_idx: (id - ACTION_BASE_MODE) as usize } }
                else { Action::Unknown(id) }
            }
        }
    }
}
