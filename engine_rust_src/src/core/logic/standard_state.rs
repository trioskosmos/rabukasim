use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use super::state::GameState;
use crate::core::alphazero_encoding::AlphaZeroEncoding;
use crate::core::logic::CardDatabase;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandardizedState {
    pub version: String,
    pub timestamp: u64,
    pub room_info: HashMap<String, String>,
    pub current_state: GameState,
    pub tensor: Option<Vec<f32>>,
    pub history: Option<Vec<GameState>>,
}

impl StandardizedState {
    pub fn new(
        gs: GameState,
        db: &CardDatabase,
        room_info: HashMap<String, String>,
        include_tensor: bool,
        history: Option<Vec<GameState>>,
    ) -> Self {
        let tensor = if include_tensor {
            Some(gs.to_alphazero_tensor(db))
        } else {
            None
        };

        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        Self {
            version: "1.1".to_string(),
            timestamp,
            room_info,
            current_state: gs,
            tensor,
            history,
        }
    }
}
