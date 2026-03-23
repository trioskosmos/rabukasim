// Basic imports
#[cfg(feature = "extension-module")]
use crate::core::alphazero_encoding_vanilla::AlphaZeroVanillaEncoding;
#[cfg(feature = "extension-module")]
use crate::core::generated_constants::{
    ACTION_BASE_HAND, ACTION_BASE_LIVESET, ACTION_BASE_MULLIGAN, ACTION_BASE_PASS, ACTION_BASE_RPS,
    ACTION_BASE_RPS_P2, ACTION_BASE_STAGE_SLOTS, ACTION_BASE_TURN_ORDER_FIRST,
};
use crate::core::heuristics::{Heuristic, HeuristicConfig};
use crate::core::logic::card_db::CardDatabase;
#[cfg(feature = "extension-module")]
use crate::core::logic::constants::ACTION_SPACE;
use crate::core::logic::state::GameState;

/// Combined output from the Transformer for a single state.
#[derive(Debug, Clone)]
pub struct AlphaZeroOutput {
    pub value: f32,               // Predicted win probability (-1 to 1 or 0 to 1)
    pub policy: Vec<f32>,         // Prior probabilities for ACTION_SPACE (16384 elements)
    pub weights: HeuristicConfig, // Meta-Heuristic parameters predicted by the Transformer
}

pub trait AlphaZeroEvaluator: Send + Sync {
    /// Evaluate a batch of states.
    fn evaluate_batch(&self, states: &[GameState], db: &CardDatabase) -> Vec<AlphaZeroOutput>;
}

#[cfg(feature = "extension-module")]
#[derive(Debug, Clone, Copy)]
pub enum PythonTensorEncoding {
    Vanilla,
    Original,
}

/// Baseline evaluator that uses the default heuristic.
/// Useful for bootstrapping or when NN is not available.
pub struct HeuristicBaselineEvaluator;

impl AlphaZeroEvaluator for HeuristicBaselineEvaluator {
    fn evaluate_batch(&self, states: &[GameState], db: &CardDatabase) -> Vec<AlphaZeroOutput> {
        use crate::core::heuristics::{EvalMode, OriginalHeuristic};
        let h = OriginalHeuristic::default();

        states
            .iter()
            .map(|s| {
                let val = h.evaluate(
                    s,
                    db,
                    s.players[0].score,
                    s.players[1].score,
                    EvalMode::Normal,
                    None,
                    None,
                );

                // Uniform policy as fallback
                let policy = vec![1.0 / 16384.0; 16384];

                AlphaZeroOutput {
                    value: val,
                    policy,
                    weights: h.config,
                }
            })
            .collect()
    }
}

#[cfg(feature = "extension-module")]
use crate::core::alphazero_encoding::AlphaZeroEncoding;

#[cfg(feature = "extension-module")]
use pyo3::prelude::*;

#[cfg(feature = "extension-module")]
pub struct PyAlphaZeroEvaluator {
    model: PyObject, // A Python object with a `.predict_batch(tensors)` method
    tensor_encoding: PythonTensorEncoding,
}

#[cfg(feature = "extension-module")]
impl PyAlphaZeroEvaluator {
    pub fn new(model: PyObject, tensor_encoding: PythonTensorEncoding) -> Self {
        Self {
            model,
            tensor_encoding,
        }
    }
}

#[cfg(feature = "extension-module")]
const VANILLA_ACTION_PASS_ID: usize = 0;
#[cfg(feature = "extension-module")]
const VANILLA_ACTION_RPS_OFFSET: usize = 1;
#[cfg(feature = "extension-module")]
const VANILLA_ACTION_TURN_CHOICE_OFFSET: usize = 4;
#[cfg(feature = "extension-module")]
const VANILLA_ACTION_MULLIGAN_OFFSET: usize = 6;
#[cfg(feature = "extension-module")]
const VANILLA_MAIN_PLAY_ACTIONS: usize = 60;
#[cfg(feature = "extension-module")]
const VANILLA_ACTION_LIVESET_OFFSET: usize = VANILLA_ACTION_MULLIGAN_OFFSET + 20;
#[cfg(feature = "extension-module")]
const VANILLA_ACTION_MAIN_PLAY_OFFSET: usize = VANILLA_ACTION_LIVESET_OFFSET + 20;
#[cfg(feature = "extension-module")]
const VANILLA_ACTION_LIVE_RESULT_OFFSET: usize =
    VANILLA_ACTION_MAIN_PLAY_OFFSET + VANILLA_MAIN_PLAY_ACTIONS;

#[cfg(feature = "extension-module")]
fn engine_action_to_vanilla_policy_id(engine_action: i32) -> Option<usize> {
    if engine_action == ACTION_BASE_PASS {
        return Some(VANILLA_ACTION_PASS_ID);
    }
    if (ACTION_BASE_RPS..=ACTION_BASE_RPS + 2).contains(&engine_action) {
        return Some(VANILLA_ACTION_RPS_OFFSET + (engine_action - ACTION_BASE_RPS) as usize);
    }
    if (ACTION_BASE_RPS_P2..=ACTION_BASE_RPS_P2 + 2).contains(&engine_action) {
        return Some(VANILLA_ACTION_RPS_OFFSET + (engine_action - ACTION_BASE_RPS_P2) as usize);
    }
    if (ACTION_BASE_TURN_ORDER_FIRST..=ACTION_BASE_TURN_ORDER_FIRST + 1).contains(&engine_action) {
        return Some(
            VANILLA_ACTION_TURN_CHOICE_OFFSET
                + (engine_action - ACTION_BASE_TURN_ORDER_FIRST) as usize,
        );
    }
    if (ACTION_BASE_MULLIGAN..ACTION_BASE_MULLIGAN + 20).contains(&engine_action) {
        return Some(
            VANILLA_ACTION_MULLIGAN_OFFSET + (engine_action - ACTION_BASE_MULLIGAN) as usize,
        );
    }
    if (ACTION_BASE_LIVESET..ACTION_BASE_LIVESET + 20).contains(&engine_action) {
        return Some(
            VANILLA_ACTION_LIVESET_OFFSET + (engine_action - ACTION_BASE_LIVESET) as usize,
        );
    }
    if (ACTION_BASE_HAND..ACTION_BASE_HAND + 100).contains(&engine_action) {
        let adjusted = (engine_action - ACTION_BASE_HAND) as usize;
        let hand_idx = adjusted / 10;
        let slot_idx = adjusted % 10;
        if hand_idx < 20 && slot_idx < 3 {
            return Some(VANILLA_ACTION_MAIN_PLAY_OFFSET + hand_idx * 3 + slot_idx);
        }
    }
    if (ACTION_BASE_STAGE_SLOTS..=ACTION_BASE_STAGE_SLOTS + 2).contains(&engine_action) {
        return Some(
            VANILLA_ACTION_LIVE_RESULT_OFFSET + (engine_action - ACTION_BASE_STAGE_SLOTS) as usize,
        );
    }
    None
}

#[cfg(feature = "extension-module")]
fn expand_vanilla_policy_to_engine_space(
    compact_policy: &[f32],
    legal_actions: &[i32],
) -> Vec<f32> {
    let mut expanded = vec![0.0; ACTION_SPACE];
    let mut mapped_total = 0.0f32;

    for &action in legal_actions {
        let action_idx = action as usize;
        if action_idx >= expanded.len() {
            continue;
        }
        if let Some(policy_id) = engine_action_to_vanilla_policy_id(action) {
            if policy_id < compact_policy.len() {
                let prob = compact_policy[policy_id].max(0.0);
                expanded[action_idx] = prob;
                mapped_total += prob;
            }
        }
    }

    if mapped_total <= 0.0 {
        let mut supported = 0usize;
        for &action in legal_actions {
            let action_idx = action as usize;
            if action_idx < expanded.len() {
                expanded[action_idx] = 1.0;
                supported += 1;
            }
        }
        if supported > 0 {
            let uniform = 1.0 / supported as f32;
            for &action in legal_actions {
                let action_idx = action as usize;
                if action_idx < expanded.len() {
                    expanded[action_idx] = uniform;
                }
            }
        }
        return expanded;
    }

    for &action in legal_actions {
        let action_idx = action as usize;
        if action_idx < expanded.len() && expanded[action_idx] > 0.0 {
            expanded[action_idx] /= mapped_total;
        }
    }
    expanded
}

#[cfg(feature = "extension-module")]
impl AlphaZeroEvaluator for PyAlphaZeroEvaluator {
    fn evaluate_batch(&self, states: &[GameState], db: &CardDatabase) -> Vec<AlphaZeroOutput> {
        Python::with_gil(|py| {
            // 1. Encode all states to tensors
            let tensors: Vec<Vec<f32>> = states
                .iter()
                .map(|state: &GameState| match self.tensor_encoding {
                    PythonTensorEncoding::Vanilla => state.to_vanilla_tensor(db),
                    PythonTensorEncoding::Original => state.to_alphazero_tensor(db),
                })
                .collect();

            // 2. Wrap in NumPy arrays (or just list of lists) and call Python
            let py_tensors = pyo3::IntoPyObjectExt::into_py_any(tensors, py).unwrap();

            let result = self
                .model
                .call_method1(py, "predict_batch", (py_tensors,))
                .expect(
                    "Python AlphaZero model call failed! Ensure model has predict_batch(tensors).",
                );

            // 3. Parse results from Python
            // Expected format: (values: List[float], policies: List[List[float]], weights: List[List[float]])
            let (values, policies, weights): (Vec<f32>, Vec<Vec<f32>>, Vec<Vec<f32>>) = result.extract(py)
                .expect("Failed to extract results from Python AlphaZero model. Expected (values, policies, weights).");

            values
                .into_iter()
                .enumerate()
                .map(|(i, v)| {
                    let legal_actions = states[i].get_legal_action_ids(db);
                    let policy = match self.tensor_encoding {
                        PythonTensorEncoding::Vanilla => {
                            expand_vanilla_policy_to_engine_space(&policies[i], &legal_actions)
                        }
                        PythonTensorEncoding::Original => policies[i].clone(),
                    };

                    // Map weights back to HeuristicConfig if applicable
                    // (This assumes the Transformer outputs exactly the fields in HeuristicConfig order)
                    let w_vec = &weights[i];
                    let cfg = if w_vec.len() >= 17 {
                        HeuristicConfig {
                            weight_live_score: w_vec[0],
                            weight_success_bonus: w_vec[1],
                            weight_member_cost: w_vec[2],
                            weight_heart: w_vec[3],
                            weight_slot_bonus: w_vec[4],
                            weight_slot_penalty: w_vec[5],
                            weight_blade: w_vec[6],
                            weight_draw_potential: w_vec[7],
                            weight_vol_bonus: w_vec[8],
                            weight_discard_bonus: w_vec[9],
                            weight_stage_ability: w_vec[10],
                            weight_untapped_bonus: w_vec[11],
                            weight_synergy_group: w_vec[12],
                            weight_synergy_center: w_vec[13],
                            weight_mill_bonus: w_vec[14],
                            weight_live_filter: w_vec[15],
                            scaling_factor: w_vec[16],
                        }
                    } else {
                        HeuristicConfig::default()
                    };

                    AlphaZeroOutput {
                        value: v,
                        policy,
                        weights: cfg,
                    }
                })
                .collect()
        })
    }
}
