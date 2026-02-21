use pyo3::prelude::*;
use rayon::prelude::*;
use numpy::{PyArray1, PyArray2, PyReadonlyArray1, PyArrayMethods};
use crate::core::logic::{GameState, PlayerState, Phase};
// use crate::core::enums::*;
use crate::core::mcts::SearchHorizon;
use crate::core::heuristics::{EvalMode, HeuristicConfig, OriginalHeuristic, LegacyHeuristic};
use smallvec::SmallVec;
// use crate::core::heuristics::{OriginalHeuristic, SimpleHeuristic};

#[pyclass]
#[derive(Clone)]
pub struct PyPlayerState {
    pub inner: PlayerState,
}

#[pymethods]
impl PyPlayerState {
    #[getter]
    fn player_id(&self) -> u8 { self.inner.player_id }

    #[getter]
    fn score(&self) -> u32 { self.inner.score }
    #[setter(score)]
    fn set_score_prop(&mut self, val: u32) { self.set_score(val); }
    fn set_score(&mut self, val: u32) { self.inner.score = val; }

    #[getter]
    fn success_lives(&self) -> Vec<u32> { self.inner.success_lives.iter().map(|&x| x as u32).collect() }
    #[setter(success_lives)]
    fn set_success_lives_prop(&mut self, val: Vec<u32>) { self.set_success_lives(val); }
    fn set_success_lives(&mut self, val: Vec<u32>) { self.inner.success_lives = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn hand(&self) -> Vec<u32> { self.inner.hand.iter().map(|&x| x as u32).collect() }
    #[setter(hand)]
    fn set_hand_prop(&mut self, val: Vec<u32>) { self.set_hand(val); }
    fn set_hand(&mut self, val: Vec<u32>) { self.inner.hand = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn stage(&self) -> [i32; 3] { [self.inner.stage[0] as i32, self.inner.stage[1] as i32, self.inner.stage[2] as i32] }
    #[setter(stage)]
    fn set_stage_prop(&mut self, val: [i32; 3]) { self.set_stage(val); }
    fn set_stage(&mut self, val: [i32; 3]) { self.inner.stage = [val[0], val[1], val[2]]; }

    #[getter]
    fn discard(&self) -> Vec<u32> { self.inner.discard.iter().map(|&x| x as u32).collect() }
    #[setter(discard)]
    fn set_discard_prop(&mut self, val: Vec<u32>) { self.set_discard(val); }
    fn set_discard(&mut self, val: Vec<u32>) { self.inner.discard = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn exile(&self) -> Vec<u32> { self.inner.exile.iter().map(|&x| x as u32).collect() }

    #[getter]
    fn deck(&self) -> Vec<u32> { self.inner.deck.iter().map(|&x| x as u32).collect() }
    #[setter(deck)]
    fn set_deck_prop(&mut self, val: Vec<u32>) { self.set_deck(val); }
    fn set_deck(&mut self, val: Vec<u32>) { self.inner.deck = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn energy_zone(&self) -> Vec<u32> { self.inner.energy_zone.iter().map(|&x| x as u32).collect() }
    #[setter(energy_zone)]
    fn set_energy_zone_prop(&mut self, val: Vec<u32>) { self.set_energy_zone(val); }
    fn set_energy_zone(&mut self, val: Vec<u32>) { self.inner.energy_zone = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn energy_deck(&self) -> Vec<u32> { self.inner.energy_deck.iter().map(|&x| x as u32).collect() }
    #[setter(energy_deck)]
    fn set_energy_deck_prop(&mut self, val: Vec<u32>) { self.set_energy_deck(val); }
    fn set_energy_deck(&mut self, val: Vec<u32>) { self.inner.energy_deck = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn live_zone(&self) -> [i32; 3] { [self.inner.live_zone[0] as i32, self.inner.live_zone[1] as i32, self.inner.live_zone[2] as i32] }
    #[setter(live_zone)]
    fn set_live_zone_prop(&mut self, val: [i32; 3]) { self.set_live_zone(val); }
    fn set_live_zone(&mut self, val: [i32; 3]) { self.inner.live_zone = [val[0], val[1], val[2]]; }

    #[getter]
    fn live_zone_revealed(&self) -> [bool; 3] { [self.inner.is_revealed(0), self.inner.is_revealed(1), self.inner.is_revealed(2)] }
    #[setter(live_zone_revealed)]
    fn set_live_zone_revealed_prop(&mut self, val: [bool; 3]) { self.set_live_zone_revealed(val); }
    fn set_live_zone_revealed(&mut self, val: [bool; 3]) {
        for (i, &v) in val.iter().enumerate() { self.inner.set_revealed(i, v); }
    }

    #[getter]
    fn tapped_energy(&self) -> Vec<bool> {
        (0..self.inner.energy_zone.len()).map(|i| self.inner.is_energy_tapped(i)).collect()
    }
    #[setter(tapped_energy)]
    fn set_tapped_energy_prop(&mut self, val: Vec<bool>) { self.set_tapped_energy(val); }
    fn set_tapped_energy(&mut self, val: Vec<bool>) {
        self.inner.tapped_energy_mask = 0;
        for (i, &tapped) in val.iter().enumerate() {
            if tapped { self.inner.set_energy_tapped(i, true); }
        }
    }

    #[getter]
    fn tapped_members(&self) -> [bool; 3] { [self.inner.is_tapped(0), self.inner.is_tapped(1), self.inner.is_tapped(2)] }
    #[setter(tapped_members)]
    fn set_tapped_members_prop(&mut self, val: [bool; 3]) { self.set_tapped_members(val); }
    fn set_tapped_members(&mut self, val: [bool; 3]) { for i in 0..3 { self.inner.set_tapped(i, val[i]); } }

    #[setter(moved_members_this_turn)]
    fn set_moved_members_this_turn_prop(&mut self, val: [bool; 3]) { self.set_moved_members_this_turn(val); }
    fn set_moved_members_this_turn(&mut self, val: [bool; 3]) { for i in 0..3 { self.inner.set_moved(i, val[i]); } }

    #[getter]
    fn base_revealed_cards(&self) -> Vec<u32> { self.inner.looked_cards.iter().map(|&x| x as u32).collect() }
    #[setter(base_revealed_cards)]
    fn set_base_revealed_cards_prop(&mut self, val: Vec<u32>) { self.set_base_revealed_cards(val); }
    fn set_base_revealed_cards(&mut self, val: Vec<u32>) { self.inner.looked_cards = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn revealed_cards(&self) -> Vec<u32> { self.inner.looked_cards.iter().map(|&x| x as u32).collect() }
    #[setter(revealed_cards)]
    fn set_revealed_cards_prop(&mut self, val: Vec<u32>) { self.set_revealed_cards(val); }
    fn set_revealed_cards(&mut self, val: Vec<u32>) { self.inner.looked_cards = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn looked_cards(&self) -> Vec<u32> { self.inner.looked_cards.iter().map(|&x| x as u32).collect() }
    fn set_looked_cards(&mut self, val: Vec<u32>) { self.inner.looked_cards = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn deck_count(&self) -> usize { self.inner.deck.len() }
    #[getter]
    fn energy_deck_count(&self) -> usize { self.inner.energy_deck.len() }

    #[getter]
    fn mulligan_selection(&self) -> u64 { self.inner.mulligan_selection }
    #[setter(mulligan_selection)]
    fn set_mulligan_selection_prop(&mut self, val: u64) { self.set_mulligan_selection(val); }
    fn set_mulligan_selection(&mut self, val: u64) { self.inner.mulligan_selection = val; }

    #[getter]
    fn baton_touch_count(&self) -> u32 { self.inner.baton_touch_count as u32 }
    #[setter(baton_touch_count)]
    fn set_baton_touch_count_prop(&mut self, val: u32) { self.set_baton_touch_count(val); }
    fn set_baton_touch_count(&mut self, val: u32) { self.inner.baton_touch_count = val as u8; }

    #[getter]
    fn baton_touch_limit(&self) -> u32 { self.inner.baton_touch_limit as u32 }
    #[setter(baton_touch_limit)]
    fn set_baton_touch_limit_prop(&mut self, val: u32) { self.set_baton_touch_limit(val); }
    fn set_baton_touch_limit(&mut self, val: u32) { self.inner.baton_touch_limit = val as u8; }

    #[getter]
    fn hand_added_turn(&self) -> Vec<u32> { self.inner.hand_added_turn.iter().map(|&x| x as u32).collect() }
    #[setter(hand_added_turn)]
    fn set_hand_added_turn_prop(&mut self, val: Vec<u32>) { self.set_hand_added_turn(val); }
    fn set_hand_added_turn(&mut self, val: Vec<u32>) { self.inner.hand_added_turn = val.into_iter().map(|x| x as i32).collect(); }

    #[getter]
    fn yell_cards(&self) -> Vec<u32> { Vec::new() }
    #[setter(yell_cards)]
    fn set_yell_cards_prop(&mut self, _val: Vec<u32>) {}
    fn set_yell_cards(&mut self, _val: Vec<u32>) {}

    #[getter]
    pub fn heart_buffs(&self) -> Vec<Vec<i32>> {
        self.inner.heart_buffs.iter().map(|h| h.to_array().iter().map(|&x| x as i32).collect()).collect()
    }
    #[setter(heart_buffs)]
    pub fn set_heart_buffs_prop(&mut self, val: Vec<Vec<i32>>) { self.set_heart_buffs(val); }
    pub fn set_heart_buffs(&mut self, val: Vec<Vec<i32>>) {
        for (i, v) in val.iter().enumerate() {
            if i < 3 && v.len() == 7 {
                for (j, &heart) in v.iter().enumerate() {
                    self.inner.heart_buffs[i].set_color_count(j, heart.max(0).min(255) as u8);
                }
            }
        }
    }

    #[getter]
    pub fn blade_buffs(&self) -> Vec<i32> { self.inner.blade_buffs.iter().map(|&x| x as i32).collect() }
    #[setter(blade_buffs)]
    pub fn set_blade_buffs_prop(&mut self, val: Vec<i32>) { self.set_blade_buffs(val); }
    pub fn set_blade_buffs(&mut self, val: Vec<i32>) {
        for (i, &v) in val.iter().enumerate() { if i < 3 { self.inner.blade_buffs[i] = v as i16; } }
    }

}


#[pyclass]
#[derive(Clone)]
pub struct PyCardDatabase {
    pub inner: std::sync::Arc<crate::core::logic::CardDatabase>,
}

#[pymethods]
impl PyCardDatabase {
    #[new]
    fn new(json_str: &str) -> PyResult<Self> {
        let db = crate::core::logic::CardDatabase::from_json(json_str)
            .map_err(|e: serde_json::Error| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(Self { inner: std::sync::Arc::new(db) })
    }

    #[getter]
    fn member_count(&self) -> usize {
        self.inner.members.len()
    }

    #[getter]
    fn live_count(&self) -> usize {
        self.inner.lives.len()
    }

    fn has_member(&self, card_id: u32) -> bool {
        self.inner.members.contains_key(&(card_id as i32))
    }

    fn get_member_ids(&self) -> Vec<u32> {
        self.inner.members.keys().map(|&k| k as u32).collect()
    }

    fn id_by_no(&self, card_no: &str) -> Option<i32> {
        self.inner.id_by_no(card_no)
    }
}


#[pyclass]
pub struct PyGameState {
    pub inner: GameState,
    pub db: PyCardDatabase,
    pub legal_action_buffer: Vec<bool>,
}

#[pymethods]
impl PyGameState {
    #[new]
    fn new(db: PyCardDatabase) -> PyResult<Self> {
        Ok(Self {
            inner: GameState::default(),
            db,
            legal_action_buffer: vec![false; crate::core::logic::ACTION_SPACE],
        })
    }

    pub fn copy(&self) -> Self {
        Self {
            inner: self.inner.clone(),
            db: self.db.clone(),
            legal_action_buffer: vec![false; crate::core::logic::ACTION_SPACE],
        }
    }

    pub fn ping(&self) -> String {
        "pong_v_force_fix_1212".to_string()
    }

    #[getter]
    fn db(&self) -> PyCardDatabase {
        self.db.clone()
    }

    #[getter]
    fn current_player(&self) -> u8 {
        self.inner.current_player
    }

    #[setter]
    fn set_current_player(&mut self, val: u8) {
        self.inner.current_player = val;
    }

    #[getter]
    fn first_player(&self) -> u8 {
        self.inner.first_player
    }

    #[setter]
    fn set_first_player(&mut self, val: u8) {
        self.inner.first_player = val;
    }

    #[getter]
    fn rps_choices(&self) -> [i8; 2] {
        self.inner.rps_choices
    }

    #[getter]
    fn rule_log(&self) -> Vec<String> {
        self.inner.ui.rule_log.clone()
    }

    #[getter]
    fn phase(&self) -> i8 {
        self.inner.phase as i8
    }

    #[getter]
    fn turn(&self) -> u32 {
        self.inner.turn as u32
    }

    #[setter]
    fn set_turn(&mut self, val: u32) {
        self.inner.turn = val as u16;
    }

    #[getter]
    fn silent(&self) -> bool {
        self.inner.ui.silent
    }

    #[setter(silent)]
    fn set_silent(&mut self, val: bool) {
        self.inner.ui.silent = val;
    }

    #[getter]
    fn debug_mode(&self) -> bool {
        self.inner.debug.debug_mode
    }

    #[setter(debug_mode)]
    fn set_debug_mode(&mut self, val: bool) {
        self.inner.debug.debug_mode = val;
    }

    #[getter]
    fn performance_results(&self) -> String {
        serde_json::to_string(&self.inner.ui.performance_results).unwrap_or_default()
    }

    #[getter]
    fn pending_card_id(&self) -> i32 {
        self.inner.interaction_stack.last().map(|p| p.card_id as i32).unwrap_or(-1)
    }

    #[getter]
    fn pending_ab_idx(&self) -> i32 {
        self.inner.interaction_stack.last().map(|p| p.ability_index as i32).unwrap_or(-1)
    }

    #[getter]
    fn pending_effect_opcode(&self) -> i32 {
        self.inner.interaction_stack.last().map(|p| p.effect_opcode as i32).unwrap_or(-1)
    }

    #[getter]
    fn pending_choice_type(&self) -> String {
        self.inner.interaction_stack.last().map(|p| p.choice_type.clone()).unwrap_or_default()
    }

    #[getter]
    fn pending_choice_text(&self) -> String {
        self.inner.interaction_stack.last().map(|p| p.choice_text.clone()).unwrap_or_default()
    }

    #[getter]
    fn yell_cards(&self) -> Vec<u32> {
        // Moved to GameState
        Vec::new()
    }

    #[setter]
    fn set_yell_cards(&mut self, _val: Vec<u32>) {
        // Moved to GameState
    }

    #[getter]
    fn pending_area_idx(&self) -> i32 {
        if let Some(pi) = self.inner.interaction_stack.last() {
            pi.ctx.area_idx as i32
        } else {
            -1
        }
    }

    #[getter]
    fn pending_player_id(&self) -> i32 {
        if let Some(pi) = self.inner.interaction_stack.last() {
            pi.ctx.player_id as i32
        } else {
            -1
        }
    }

    #[getter]
    fn last_performance_results(&self) -> String {
        serde_json::to_string(&self.inner.ui.last_performance_results).unwrap_or_else(|_| "{}".to_string())
    }

    #[getter]
    fn performance_history(&self) -> String {
        serde_json::to_string(&self.inner.ui.performance_history).unwrap_or_else(|_| "[]".to_string())
    }

    #[getter]
    fn pending_choices(&self) -> Vec<(String, String)> {
        use crate::core::enums::O_ORDER_DECK;
        use crate::core::enums::O_LOOK_AND_CHOOSE;
        use crate::core::enums::O_REVEAL_CARDS;
        use crate::core::enums::O_RECOVER_LIVE;
        use crate::core::enums::O_RECOVER_MEMBER;
        use crate::core::enums::O_TAP_OPPONENT;
        use crate::core::enums::O_MOVE_MEMBER;
        use crate::core::enums::O_ACTIVATE_MEMBER;
        use crate::core::enums::O_COLOR_SELECT;
        use crate::core::enums::O_MOVE_TO_DISCARD;
        use crate::core::enums::O_PLAY_MEMBER_FROM_HAND;
        use crate::core::enums::O_SELECT_CARDS;
        use crate::core::enums::O_OPPONENT_CHOOSE;
        use crate::core::enums::O_SELECT_MODE;

        let mut result = Vec::new();
        let op = self.inner.interaction_stack.last().map(|p| p.effect_opcode).unwrap_or(-1);

        let p_idx = if let Some(pi) = self.inner.interaction_stack.last() {
            pi.ctx.player_id as usize
        } else {
            self.inner.current_player as usize
        };

        if op == O_ORDER_DECK || op == O_LOOK_AND_CHOOSE || op == O_REVEAL_CARDS || op == O_RECOVER_LIVE || op == O_RECOVER_MEMBER {
            let looked = &self.inner.players[p_idx].looked_cards;
            let params = serde_json::json!({
                "cards": looked
            });
            let type_str = if op == O_ORDER_DECK { "ORDER_DECK" } else { "SELECT_FROM_LIST" };
            result.push((type_str.to_string(), params.to_string()));
        } else if op == O_TAP_OPPONENT {
            result.push(("TARGET_OPPONENT_MEMBER".to_string(), "{}".to_string()));
        } else if op == O_MOVE_MEMBER {
            result.push(("MOVE_MEMBER".to_string(), "{}".to_string()));
        } else if op == O_ACTIVATE_MEMBER {
            result.push(("TAP_MEMBER".to_string(), "{}".to_string()));
        } else if op == O_COLOR_SELECT {
            result.push(("COLOR_SELECT".to_string(), "{}".to_string()));
        } else if op == O_MOVE_TO_DISCARD {
            result.push(("SELECT_HAND_DISCARD".to_string(), "{}".to_string()));
        } else if op == O_PLAY_MEMBER_FROM_HAND {
            result.push(("SELECT_HAND_PLAY".to_string(), "{}".to_string()));
        } else if op == O_SELECT_CARDS {
            result.push(("SELECT_FROM_LIST".to_string(), "{}".to_string()));
        } else if op == O_OPPONENT_CHOOSE {
            result.push(("OPPONENT_CHOOSE".to_string(), "{}".to_string()));
        } else if op == O_SELECT_MODE {
            // We might need to store the options in the state if we want better labels
            result.push(("SELECT_MODE".to_string(), "{}".to_string()));
        }

        result
    }

    #[getter]
    fn pending_effects(&self) -> Vec<String> {
        Vec::new()
    }



    fn get_player(&self, idx: usize) -> PyResult<PyPlayerState> {
        if idx < 2 {
            Ok(PyPlayerState { inner: self.inner.players[idx].clone() })
        } else {
            Err(pyo3::exceptions::PyIndexError::new_err("Player index out of bounds"))
        }
    }

    fn initialize_game(&mut self, p0_deck: Vec<u32>, p1_deck: Vec<u32>, p0_energy: Vec<u32>, p1_energy: Vec<u32>, p0_lives: Vec<u32>, p1_lives: Vec<u32>) {
        let p0_d: Vec<i32> = p0_deck.into_iter().map(|x| x as i32).collect();
        let p1_d: Vec<i32> = p1_deck.into_iter().map(|x| x as i32).collect();
        let p0_e: Vec<i32> = p0_energy.into_iter().map(|x| x as i32).collect();
        let p1_e: Vec<i32> = p1_energy.into_iter().map(|x| x as i32).collect();
        let p0_l: Vec<i32> = p0_lives.into_iter().map(|x| x as i32).collect();
        let p1_l: Vec<i32> = p1_lives.into_iter().map(|x| x as i32).collect();
        self.inner.initialize_game(p0_d, p1_d, p0_e, p1_e, p0_l, p1_l);
    }

    fn initialize_game_with_seed(&mut self, p0_deck: Vec<u32>, p1_deck: Vec<u32>, p0_energy: Vec<u32>, p1_energy: Vec<u32>, p0_lives: Vec<u32>, p1_lives: Vec<u32>, seed: u64) {
        let p0_d: Vec<i32> = p0_deck.into_iter().map(|x| x as i32).collect();
        let p1_d: Vec<i32> = p1_deck.into_iter().map(|x| x as i32).collect();
        let p0_e: Vec<i32> = p0_energy.into_iter().map(|x| x as i32).collect();
        let p1_e: Vec<i32> = p1_energy.into_iter().map(|x| x as i32).collect();
        let p0_l: Vec<i32> = p0_lives.into_iter().map(|x| x as i32).collect();
        let p1_l: Vec<i32> = p1_lives.into_iter().map(|x| x as i32).collect();
        self.inner.initialize_game_with_seed(p0_d, p1_d, p0_e, p1_e, p0_l, p1_l, Some(seed));
    }

    fn get_legal_actions(&mut self) -> Vec<bool> {
        self.inner.get_legal_actions_into(&self.db.inner, self.inner.current_player as usize, &mut self.legal_action_buffer);
        self.legal_action_buffer.clone()
    }

    fn get_legal_action_ids(&mut self) -> Vec<i32> {
        self.inner.get_legal_action_ids(&self.db.inner)
    }

    fn get_legal_action_ids_for_player(&mut self, p_idx: usize) -> Vec<i32> {
        self.inner.get_legal_action_ids_for_player(&self.db.inner, p_idx)
    }

    fn get_observation(&self) -> Vec<f32> {
        self.inner.get_observation(&self.db.inner)
    }

    fn is_terminal(&self) -> bool {
        self.inner.phase == Phase::Terminal
    }

    fn get_winner(&self) -> i32 {
        self.inner.get_winner()
    }

    fn get_effective_blades(&self, p_idx: usize, slot_idx: usize) -> u32 {
        self.inner.get_effective_blades(p_idx, slot_idx, &self.db.inner, 0)
    }

    fn get_effective_hearts(&self, p_idx: usize, slot_idx: usize) -> [u8; 7] {
        self.inner.get_effective_hearts(p_idx, slot_idx, &self.db.inner, 0).to_array()
    }

    fn get_total_blades(&self, p_idx: usize) -> u32 {
        self.inner.get_total_blades(p_idx, &self.db.inner, 0)
    }

    fn get_total_hearts(&self, p_idx: usize) -> [u32; 7] {
        self.inner.get_total_hearts(p_idx, &self.db.inner, 0).to_array().map(|x| x as u32)
    }

    fn get_member_cost(&self, p_idx: usize, card_id: i32, slot_idx: i32) -> i32 {
        self.inner.get_member_cost(p_idx, card_id, slot_idx as i16, -1, &self.db.inner, 0)
    }

    fn execute_mulligan(&mut self, player_idx: usize, discard_indices: Vec<usize>) {
        self.inner.execute_mulligan(player_idx, discard_indices);
    }

    fn step(&mut self, action: i32) -> PyResult<()> {
        let db = &self.db.inner;
        if self.inner.debug.debug_mode {
            self.inner.dump_diagnostics(db);
        }
        self.inner.step(db, action)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    }

    fn debug_execute_bytecode(&mut self, bytecode: Vec<i32>, player_id: u8, area_idx: i32, source_card_id: i32, target_slot: i32, choice_index: i32, selected_color: i32) {
        let db = &self.db.inner;
        let ctx = crate::core::logic::AbilityContext {
            player_id,
            area_idx: area_idx as i16,
            source_card_id,
            target_slot: target_slot as i16,
            choice_index: choice_index as i16,
            selected_color: selected_color as i16,
            program_counter: 0,
            ability_index: -1,
            v_remaining: -1,
            trigger_type: Default::default(),
        };
        self.inner.resolve_bytecode(db, &bytecode, &ctx);
    }

    fn integrated_step(&mut self, action: i32, opp_mode: u8, mcts_sims: usize, enable_rollout: bool) -> (f32, bool) {
        let db = &self.db.inner;
        self.inner.integrated_step(db, action, opp_mode, mcts_sims, enable_rollout)
    }

    #[pyo3(signature = (p0_sims, p1_sims, p0_heuristic_id, p1_heuristic_id, horizon=SearchHorizon::GameEnd(), p0_rollout=true, p1_rollout=true))]
    fn play_asymmetric_match(&mut self, p0_sims: usize, p1_sims: usize, p0_heuristic_id: i32, p1_heuristic_id: i32, horizon: SearchHorizon, p0_rollout: bool, p1_rollout: bool) -> (i32, u32) {
        let db = &self.db.inner;
        self.inner.play_asymmetric_match(db, p0_sims, p1_sims, p0_heuristic_id, p1_heuristic_id, horizon, p0_rollout, p1_rollout)
    }

    #[pyo3(signature = (p0_sims, p1_sims, p0_heuristic_id, p1_heuristic_id, horizon=SearchHorizon::GameEnd(), enable_rollout=true))]
    fn play_mirror_match(&mut self, p0_sims: usize, p1_sims: usize, p0_heuristic_id: i32, p1_heuristic_id: i32, horizon: SearchHorizon, enable_rollout: bool) -> (i32, u32) {
        let db = &self.db.inner;
        self.inner.play_mirror_match(db, p0_sims, p1_sims, p0_heuristic_id, p1_heuristic_id, horizon, enable_rollout)
    }

    fn step_opponent(&mut self) {
        let db = &self.db.inner;
        self.inner.step_opponent(db);
    }

    #[pyo3(signature = (sims, config=None))]
    fn step_opponent_mcts(&mut self, sims: usize, config: Option<HeuristicConfig>) {
        let db = &self.db.inner;
        let h = OriginalHeuristic { config: config.unwrap_or_default() };
        self.inner.step_opponent_mcts(db, sims, &h);
    }

    #[pyo3(signature = (config=None))]
    fn step_opponent_greedy(&mut self, config: Option<HeuristicConfig>) {
        let db = &self.db.inner;
        let h = OriginalHeuristic { config: config.unwrap_or_default() };
        self.inner.step_opponent_greedy(db, &h);
    }

    #[pyo3(signature = (_db, p_idx, heuristic_id, config=None))]
    fn get_greedy_action(&mut self, _db: &PyCardDatabase, p_idx: usize, heuristic_id: i32, config: Option<HeuristicConfig>) -> i32 {
        let db = &self.db.inner;
        let cfg = config.unwrap_or_default();
        match heuristic_id {
            1 => self.inner.get_greedy_action(db, p_idx, &LegacyHeuristic { config: cfg }),
            2 => self.inner.get_greedy_action(db, p_idx, &LegacyHeuristic { config: cfg }),
            _ => self.inner.get_greedy_action(db, p_idx, &OriginalHeuristic { config: cfg }),
        }
    }

    #[pyo3(signature = (_db, p_idx, heuristic_id, config=None))]
    fn get_greedy_evaluations(&mut self, _db: &PyCardDatabase, p_idx: usize, heuristic_id: i32, config: Option<HeuristicConfig>) -> Vec<(i32, f32)> {
        let db = &self.db.inner;
        let cfg = config.unwrap_or_default();
        match heuristic_id {
            1 => self.inner.get_greedy_evaluations(db, p_idx, &LegacyHeuristic { config: cfg }),
            2 => self.inner.get_greedy_evaluations(db, p_idx, &LegacyHeuristic { config: cfg }),
            _ => self.inner.get_greedy_evaluations(db, p_idx, &OriginalHeuristic { config: cfg }),
        }
    }

    #[pyo3(signature = (heuristic_id, baseline_score0=0, baseline_score1=0, config=None))]
    fn evaluate(&self, heuristic_id: i32, baseline_score0: u32, baseline_score1: u32, config: Option<HeuristicConfig>) -> f32 {
        let db = &self.db.inner;
        let cfg = config.unwrap_or_default();
        match heuristic_id {
            1 => self.inner.evaluate(db, baseline_score0, baseline_score1, EvalMode::Normal, &LegacyHeuristic { config: cfg }),
            2 => self.inner.evaluate(db, baseline_score0, baseline_score1, EvalMode::Normal, &LegacyHeuristic { config: cfg }),
            _ => self.inner.evaluate(db, baseline_score0, baseline_score1, EvalMode::Normal, &OriginalHeuristic { config: cfg }),
        }
    }

    #[pyo3(signature = (sims, timeout_sec=0.0, horizon=SearchHorizon::GameEnd(), eval_mode=EvalMode::Blind))]
    fn get_mcts_suggestions(&mut self, sims: usize, timeout_sec: f32, horizon: SearchHorizon, eval_mode: EvalMode) -> Vec<(i32, f32, u32)> {
        let db = &self.db.inner;
        self.inner.get_mcts_suggestions(db, sims, timeout_sec, horizon, eval_mode)
    }

    #[pyo3(signature = (sims, timeout_sec=0.0, horizon=SearchHorizon::GameEnd(), eval_mode=EvalMode::Blind, config=None))]
    fn get_mcts_suggestions_with_config(&mut self, sims: usize, timeout_sec: f32, horizon: SearchHorizon, eval_mode: EvalMode, config: Option<HeuristicConfig>) -> Vec<(i32, f32, u32)> {
        let db = &self.db.inner;
        let h = OriginalHeuristic { config: config.unwrap_or_default() };
        self.inner.get_mcts_suggestions_ext(db, sims, timeout_sec, horizon, eval_mode, &h)
    }

    #[setter]
    fn set_phase(&mut self, val: i8) {
        self.inner.phase = match val {
            -1 => Phase::MulliganP1,
            0 => Phase::MulliganP2,
            1 => Phase::Active,
            2 => Phase::Energy,
            3 => Phase::Draw,
            4 => Phase::Main,
            5 => Phase::LiveSet,
            6 => Phase::PerformanceP1,
            7 => Phase::PerformanceP2,
            8 => Phase::LiveResult,
            9 => Phase::Terminal,
            10 => Phase::Response,
            _ => Phase::Setup,
        };
    }

    fn set_player(&mut self, idx: usize, player: PyPlayerState) -> PyResult<()> {
        if idx < 2 {
            self.inner.log(format!("set_player {}: Discard len = {}", idx, player.inner.discard.len()));
            self.inner.players[idx] = player.inner;
            Ok(())
        } else {
            Err(pyo3::exceptions::PyIndexError::new_err("Player index out of bounds"))
        }
    }

    fn set_stage_card(&mut self, p_idx: usize, slot_idx: usize, card_id: i32) {
        if p_idx < 2 && slot_idx < 3 {
            self.inner.players[p_idx].stage[slot_idx] = card_id;
        }
    }

    fn set_live_card(&mut self, p_idx: usize, slot_idx: usize, card_id: i32, revealed: bool) {
        if p_idx < 2 && slot_idx < 3 {
            self.inner.players[p_idx].live_zone[slot_idx] = card_id;
            self.inner.players[p_idx].set_revealed(slot_idx, revealed);
        }
    }

    fn set_hand_cards(&mut self, p_idx: usize, cards: Vec<u32>) {
        if p_idx < 2 {
            self.inner.players[p_idx].hand = cards.into_iter().map(|x| x as i32).collect();
            self.inner.players[p_idx].hand_added_turn = SmallVec::from_vec(vec![self.inner.turn as i32; self.inner.players[p_idx].hand.len()]);
        }
    }

    fn set_discard_cards(&mut self, p_idx: usize, cards: Vec<u32>) {
        if p_idx < 2 {
            self.inner.players[p_idx].discard = cards.into_iter().map(|x| x as i32).collect();
        }
    }

    fn set_revealed_cards(&mut self, p_idx: usize, cards: Vec<u32>) {
        if p_idx < 2 {
            // looked_cards is the shared buffer for revealing cards in the engine
            self.inner.players[p_idx].looked_cards = cards.into_iter().map(|x| x as i32).collect();
        }
    }

    fn set_deck_cards(&mut self, p_idx: usize, cards: Vec<u32>) {
        if p_idx < 2 {
            self.inner.players[p_idx].deck = cards.into_iter().map(|x| x as i32).collect();
        }
    }

    fn set_energy_cards(&mut self, p_idx: usize, cards: Vec<u32>) {
        if p_idx < 2 {
            self.inner.players[p_idx].energy_zone = cards.into_iter().map(|x| x as i32).collect();
            // Initialize tapped_energy if needed (reset mask)
            self.inner.players[p_idx].tapped_energy_mask = 0;
        }
    }

    fn set_live_cards(&mut self, p_idx: usize, cards: Vec<u32>) {
        if p_idx < 2 {
            for (i, &cid) in cards.iter().enumerate().take(3) {
                self.inner.players[p_idx].live_zone[i] = cid as i32;
            }
        }
    }

    fn resolve_bytecode(&mut self, bytecode: Vec<i32>, player_id: u8, area_idx: i32) {
        let ctx = crate::core::logic::AbilityContext {
            player_id,
            area_idx: area_idx as i16,
            ..crate::core::logic::AbilityContext::default()
        };
        self.inner.resolve_bytecode(&self.db.inner, &bytecode, &ctx);
    }

    fn trigger_abilities(&mut self, trigger: i32, player_id: u8) {
        let trigger_type = unsafe { std::mem::transmute::<i8, crate::core::enums::TriggerType>(trigger as i8) };
        let ctx = crate::core::logic::AbilityContext {
            player_id,
            ..crate::core::logic::AbilityContext::default()
        };
        self.inner.trigger_abilities(&self.db.inner, trigger_type, &ctx);
    }

    fn trigger_ability_on_card(&mut self, _player_id: u8, _card_id: i32, slot_idx: i32, ab_idx: i32) -> PyResult<()> {
        let db = &self.db.inner;
        self.inner.activate_ability(db, slot_idx as usize, ab_idx as usize)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    }

    fn clear_once_per_turn_flags(&mut self, p_idx: usize) {
        if p_idx < 2 {
            self.inner.players[p_idx].used_abilities.clear();
        }
    }

    fn start_turn(&mut self) {
        self.inner.do_active_phase(&self.db.inner);
    }

    #[pyo3(signature = (num_sims=0, seconds=0.0, heuristic_type="original", horizon=SearchHorizon::GameEnd(), eval_mode=EvalMode::Blind, config=None, _model_path=None))]
    fn search_mcts(&self, num_sims: usize, seconds: f32, heuristic_type: &str, horizon: SearchHorizon, eval_mode: EvalMode, config: Option<HeuristicConfig>, _model_path: Option<&str>) -> Vec<(i32, f32, u32)> {
        let cfg = config.unwrap_or_default();
        if heuristic_type == "resnet" || heuristic_type == "hybrid" {
            // ... (keeping NN logic simplified for now as it's less commonly used in diagnostics)
            #[cfg(not(feature = "nn"))]
            {
                let mcts = crate::core::mcts::MCTS::new();
                let h = OriginalHeuristic { config: cfg };
                return mcts.search_parallel(&self.inner, &self.db.inner, num_sims, seconds, horizon, &h, eval_mode == EvalMode::Blind);
            }
        }

        let mcts = crate::core::mcts::MCTS::new();
        match heuristic_type {
            "legacy" => {
                let h = LegacyHeuristic { config: cfg };
                mcts.search_parallel(&self.inner, &self.db.inner, num_sims, seconds, horizon, &h, eval_mode == EvalMode::Blind)
            },
            _ => {
                let h = OriginalHeuristic { config: cfg };
                mcts.search_parallel(&self.inner, &self.db.inner, num_sims, seconds, horizon, &h, eval_mode == EvalMode::Blind)
            }
        }
    }
}


#[pyclass]
pub struct PyVectorGameState {
    envs: Vec<GameState>,
    db: PyCardDatabase,
    p0_deck: Vec<u32>,
    p1_deck: Vec<u32>,
    p0_lives: Vec<u32>,
    p1_lives: Vec<u32>,
    seeds: Vec<u64>,
    opp_mode: u8,
    mcts_sims: usize,
}

#[pymethods]
impl PyVectorGameState {
    #[new]
    #[pyo3(signature = (num_envs, db, opp_mode=0, mcts_sims=50))]
    fn new(num_envs: usize, db: PyCardDatabase, opp_mode: u8, mcts_sims: usize) -> Self {
        let mut envs = Vec::with_capacity(num_envs);
        for _ in 0..num_envs {
            envs.push(GameState::default());
        }
        Self {
            envs,
            db,
            p0_deck: Vec::new(),
            p1_deck: Vec::new(),
            p0_lives: Vec::new(),
            p1_lives: Vec::new(),
            seeds: vec![0; num_envs],
            opp_mode,
            mcts_sims,
        }
    }

    fn initialize(&mut self, p0_deck: Vec<u32>, p1_deck: Vec<u32>, p0_lives: Vec<u32>, p1_lives: Vec<u32>, seed: u64) {
        self.p0_deck = p0_deck;
        self.p1_deck = p1_deck;
        self.p0_lives = p0_lives;
        self.p1_lives = p1_lives;

        let num_envs = self.envs.len();
        for i in 0..num_envs {
            self.seeds[i] = seed + i as u64;
        }

        self.envs.par_iter_mut().enumerate().for_each(|(i, env)| {
             env.initialize_game_with_seed(
                 self.p0_deck.iter().map(|&x| x as i32).collect(),
                 self.p1_deck.iter().map(|&x| x as i32).collect(),
                 Vec::new(), Vec::new(),
                 self.p0_lives.iter().map(|&x| x as i32).collect(),
                 self.p1_lives.iter().map(|&x| x as i32).collect(),
                 Some(self.seeds[i])
             );
        });
    }

    #[allow(clippy::too_many_arguments)]
    fn step<'py>(
        &mut self,
        _py: Python<'py>,
        actions: PyReadonlyArray1<'py, i32>,
        obs_out: &Bound<'py, PyArray2<f32>>,
        rewards_out: &Bound<'py, PyArray1<f32>>,
        dones_out: &Bound<'py, PyArray1<bool>>,
        term_obs_out: &Bound<'py, PyArray2<f32>>,
    ) -> PyResult<Vec<usize>> {
        let actions = actions.as_slice()?;
        let obs_slice = unsafe { obs_out.as_slice_mut()? };
        let rewards_slice = unsafe { rewards_out.as_slice_mut()? };
        let dones_slice = unsafe { dones_out.as_slice_mut()? };
        let term_obs_slice = unsafe { term_obs_out.as_slice_mut()? };

        let num_envs = self.envs.len();
        let db = &self.db.inner;
        let obs_dim = 320;

        if actions.len() != num_envs {
            return Err(pyo3::exceptions::PyValueError::new_err("Action dim mismatch"));
        }

        // 1. Step
        let opp_mode = self.opp_mode;
        let mcts_sims = self.mcts_sims;
        let results: Vec<(f32, bool)> = self.envs.par_iter_mut().zip(actions.par_iter())
            .map(|(env, &act)| {
                env.integrated_step(db, act, opp_mode, mcts_sims, true)
            }).collect();

        results.par_iter().zip(rewards_slice.par_iter_mut()).zip(dones_slice.par_iter_mut())
            .for_each(|((&(r, d), r_out), d_out)| {
                *r_out = r;
                *d_out = d;
            });

        // 2. Filter Done
        let mut done_indices = Vec::with_capacity(num_envs / 10);
        for (i, &(_, done)) in results.iter().enumerate() {
            if done { done_indices.push(i); }
        }

        // 3. Write Terminal Obs (Before Reset)
        if !done_indices.is_empty() {
            term_obs_slice.par_chunks_mut(obs_dim).zip(done_indices.par_iter())
                .for_each(|(chunk, &env_idx)| {
                    self.envs[env_idx].write_observation(db, chunk);
                });
        }

        // 4. Auto-Reset
        let p0_deck = &self.p0_deck;
        let p1_deck = &self.p1_deck;
        let p0_lives = &self.p0_lives;
        let p1_lives = &self.p1_lives;

        self.envs.par_iter_mut().zip(results.par_iter()).for_each(|(env, &(_, done))| {
             if done {
                  env.initialize_game_with_seed(
                      p0_deck.iter().map(|&x| x as i32).collect(),
                      p1_deck.iter().map(|&x| x as i32).collect(),
                      Vec::new(), Vec::new(),
                      p0_lives.iter().map(|&x| x as i32).collect(),
                      p1_lives.iter().map(|&x| x as i32).collect(),
                      None
                  );
             }
        });

        // 5. Write Final Obs
        obs_slice.par_chunks_mut(obs_dim).zip(self.envs.par_iter())
            .for_each(|(chunk, env)| {
                env.write_observation(db, chunk);
            });

        Ok(done_indices)
    }

    // New: Zero-Copy get_observations
    fn get_observations<'py>(&self, _py: Python<'py>, out: &Bound<'py, PyArray2<f32>>) -> PyResult<()> {
        let db = &self.db.inner;
        let obs_dim = 320;
        let obs_slice = unsafe { out.as_slice_mut()? };

        obs_slice.par_chunks_mut(obs_dim).zip(self.envs.par_iter())
            .for_each(|(chunk, env)| {
                env.write_observation(db, chunk);
            });
        Ok(())
    }

    // New: Zero-Copy get_action_masks
    fn get_action_masks<'py>(&self, _py: Python<'py>, out: &Bound<'py, PyArray2<bool>>) -> PyResult<()> {
        let db = &self.db.inner;
        let action_dim = crate::core::logic::ACTION_SPACE;
        let mask_slice = unsafe { out.as_slice_mut()? };

        mask_slice.par_chunks_mut(action_dim).zip(self.envs.par_iter())
            .for_each(|(chunk, env)| {
                env.get_legal_actions_into(db, env.current_player as usize, chunk);
            });
        Ok(())
    }
}

#[cfg(feature = "nn")]
#[pyclass]
pub struct PyHybridMCTS {
    pub session: std::sync::Arc<std::sync::Mutex<ort::session::Session>>,
    pub neural_weight: f32,
    pub skip_rollout: bool,
}

#[cfg(feature = "nn")]
#[pymethods]
impl PyHybridMCTS {
    #[new]
    #[pyo3(signature = (model_path, neural_weight=0.3, skip_rollout=false))]
    fn new(model_path: &str, neural_weight: f32, skip_rollout: bool) -> PyResult<Self> {
        let session = ort::session::Session::builder()
            .map_err(|e: ort::Error| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .commit_from_file(model_path)
            .map_err(|e: ort::Error| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(Self {
            session: std::sync::Arc::new(std::sync::Mutex::new(session)),
            neural_weight,
            skip_rollout
        })
    }

    #[pyo3(signature = (game, num_sims=0, seconds=0.0))]
    fn get_suggestions(&mut self, game: &mut PyGameState, num_sims: usize, seconds: f32) -> Vec<(i32, f32, u32)> {
        let mut mcts = crate::core::mcts::HybridMCTS::new(
            self.session.clone(),
            self.neural_weight,
            self.skip_rollout
        );
        mcts.get_suggestions(&game.inner, &game.db.inner, num_sims, seconds)
    }
}

pub fn register_python_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyGameState>()?;
    m.add_class::<PyPlayerState>()?;
    m.add_class::<PyCardDatabase>()?;
    m.add_class::<PyVectorGameState>()?;
    #[cfg(feature = "nn")]
    m.add_class::<PyHybridMCTS>()?;
    m.add_class::<SearchHorizon>()?;
    m.add_class::<EvalMode>()?;
    m.add_class::<HeuristicConfig>()?;
    Ok(())
}
