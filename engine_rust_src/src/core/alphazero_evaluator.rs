use crate::core::logic::{CardDatabase, GameState};
use crate::core::alphazero_encoding::AlphaZeroEncoding;
// removed unused AlphaZeroEncoding
use crate::core::heuristics::{Heuristic, HeuristicConfig};
#[cfg(feature = "extension-module")]
// Removed unused Arc

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
use pyo3::prelude::*;

#[cfg(feature = "extension-module")]
pub struct PyAlphaZeroEvaluator {
    model: PyObject, // A Python object with a `.predict_batch(tensors)` method
}

#[cfg(feature = "extension-module")]
impl PyAlphaZeroEvaluator {
    pub fn new(model: PyObject) -> Self {
        Self { model }
    }
}

#[cfg(feature = "extension-module")]
impl AlphaZeroEvaluator for PyAlphaZeroEvaluator {
    fn evaluate_batch(&self, states: &[GameState], db: &CardDatabase) -> Vec<AlphaZeroOutput> {
        Python::with_gil(|py| {
            // 1. Encode all states to tensors
            let tensors: Vec<Vec<f32>> = states.iter().map(|s| s.to_alphazero_tensor(db)).collect();

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
                        policy: policies[i].clone(),
                        weights: cfg,
                    }
                })
                .collect()
        })
    }
}
