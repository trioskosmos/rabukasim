pub mod core;
#[cfg(feature = "extension-module")]
pub mod py_bindings;
pub mod wasm_bindings;
pub mod test_helpers;
pub mod repro;

#[cfg(test)]
mod tests;
#[cfg(test)]
mod mechanics_tests;
#[cfg(test)]
mod baton_pass_tests;
#[cfg(test)]
mod structural_tests;
#[cfg(test)]
mod verification_tests;
#[cfg(test)]
mod deck_refresh_tests;
#[cfg(test)]
mod ability_tests;
#[cfg(test)]
mod opcode_tests;
#[cfg(test)]
mod trigger_tests;
#[cfg(test)]
mod size_test;
#[cfg(test)]
// mod tie_breaker_tests;
#[cfg(test)]
mod meta_rule_tests;
#[cfg(test)]
// mod archetype_tests;
#[cfg(test)]
mod comprehensive_tests;
#[cfg(test)]
mod regression_tests;
#[cfg(test)]
mod rule_parity_regression_tests;
#[cfg(test)]
mod wave2_tests;
#[cfg(test)]
mod stabilized_tests;
#[cfg(test)]
mod database_tests;
#[cfg(test)]
mod card_interaction_tests;
#[cfg(test)]
mod response_flow_tests;
#[cfg(test)]
mod coverage_gap_tests;
#[cfg(test)]
mod wave6_tests;
#[cfg(test)]
mod phase_transition_tests;
#[cfg(test)]
mod game_flow_tests;
#[cfg(test)]
mod game_end_tests;
#[cfg(test)]
mod opcode_missing_tests;
#[cfg(test)]
mod opcode_coverage_gap_2;
#[cfg(test)]
#[cfg(test)]
// mod archetype_runner;
mod repro_task;
#[cfg(test)]
mod repro_card_fixes;
#[cfg(test)]
mod semantic_assertions;
#[cfg(test)]
mod enforcement_tests;
#[cfg(test)]
mod filter_audit_tests;
#[cfg(test)]
mod rule_alignment_tests;
#[cfg(test)]
mod qa_verification_tests;


#[cfg(test)]
mod repro_softlock;
#[cfg(test)]
mod repro_color_filter;

// pub mod repro_pl_bp3_004; // Deleted

#[cfg(feature = "extension-module")]
use pyo3::prelude::*;

#[cfg(feature = "extension-module")]
#[pymodule]
fn engine_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    py_bindings::register_python_module(m)
}
