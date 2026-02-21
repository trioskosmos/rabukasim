use wasm_bindgen::prelude::*;
use crate::core::models::{GameState, CardDatabase};
use crate::core::mcts::SearchHorizon;
use crate::core::heuristics::EvalMode;


#[wasm_bindgen]
pub struct WasmEngine {
    state: GameState,
    db: CardDatabase,
}

#[wasm_bindgen]
impl WasmEngine {
    #[wasm_bindgen(constructor)]
    pub fn new(card_db_json: &str) -> Result<WasmEngine, JsError> {
        let db = CardDatabase::from_json(card_db_json)
            .map_err(|e| JsError::new(&format!("Failed to parse card DB: {}", e)))?;

        Ok(WasmEngine {
            state: GameState::default(),
            db,
        })
    }

    pub fn init_game(&mut self,
        p0_deck: Vec<u32>,
        p1_deck: Vec<u32>,
        p0_energy: Vec<u32>,
        p1_energy: Vec<u32>,
        p0_lives: Vec<u32>,
        p1_lives: Vec<u32>,
        seed: Option<u64>
    ) {
        self.state.initialize_game_with_seed(
            p0_deck.into_iter().map(|x| x as i32).collect(),
            p1_deck.into_iter().map(|x| x as i32).collect(),
            p0_energy.into_iter().map(|x| x as i32).collect(),
            p1_energy.into_iter().map(|x| x as i32).collect(),
            p0_lives.into_iter().map(|x| x as i32).collect(),
            p1_lives.into_iter().map(|x| x as i32).collect(),
            seed
        );
    }

    pub fn step(&mut self, action_id: i32) -> Result<(), JsError> {
        self.state.step(&self.db, action_id)
            .map_err(|e| JsError::new(&e.to_string()))
    }

    pub fn get_state_json(&self) -> Result<String, JsError> {
        serde_json::to_string(&self.state)
            .map_err(|e| JsError::new(&e.to_string()))
    }

    pub fn get_legal_actions(&mut self) -> Vec<i32> {
        self.state.get_legal_action_ids(&self.db)
    }

    pub fn ai_suggest(&mut self, sims: usize) -> Result<i32, JsError> {
        let suggestions = self.state.get_mcts_suggestions(&self.db, sims, 0.0, SearchHorizon::GameEnd(), EvalMode::Normal);
        if let Some((action, _, _)) = suggestions.first() {
            Ok(*action)
        } else {
            Ok(0)
        }
    }

    pub fn ai_suggest_timed(&mut self, time_ms: f64) -> Result<i32, JsError> {
        let horizon = SearchHorizon::GameEnd();

        // Pass time in seconds
        let suggestions = self.state.get_mcts_suggestions(&self.db, 1000000, time_ms as f32 / 1000.0, horizon, EvalMode::Normal);
        if let Some((action, _, _)) = suggestions.first() {
            Ok(*action)
        } else {
            Ok(0)
        }
    }

    // Direct accessors to key state fields to avoid full JSON serialization
    pub fn get_phase(&self) -> i32 { self.state.phase as i32 }
    pub fn get_turn(&self) -> u32 { self.state.turn as u32 }
    pub fn get_current_player(&self) -> u32 { self.state.current_player as u32 }
    pub fn get_score(&self, p_idx: usize) -> u32 { self.state.core.players[p_idx].score }
    pub fn get_lives(&self, p_idx: usize) -> usize { self.state.core.players[p_idx].success_lives.len() }

    pub fn get_hand(&self, p_idx: usize) -> Vec<i32> { self.state.core.players[p_idx].hand.to_vec() }
    pub fn get_stage(&self, p_idx: usize) -> Vec<i32> { self.state.core.players[p_idx].stage.iter().map(|&x| x as i32).collect() }
    pub fn get_energy(&self, p_idx: usize) -> Vec<i32> { self.state.core.players[p_idx].energy_zone.to_vec() }
    pub fn get_tapped_energy(&self, p_idx: usize) -> Vec<u8> {
        (0..self.state.core.players[p_idx].energy_zone.len())
            .map(|i| if self.state.core.players[p_idx].is_energy_tapped(i) { 1 } else { 0 })
            .collect()
    }

    pub fn get_pending_choice_type(&self) -> String {
        self.state.interaction_stack.last().map(|p| p.choice_type.clone()).unwrap_or_default()
    }

    pub fn get_last_log(&self) -> String {
        self.state.ui.rule_log.last().cloned().unwrap_or_default()
    }
}
