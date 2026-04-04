//! Love Live Card Game Rust Engine

#![allow(unused_crate_dependencies)]
pub mod core;
pub mod export_hydrated_abilities;
#[cfg(feature = "extension-module")]
pub mod py_bindings;
pub mod repro;
pub mod test_helpers;
#[cfg(feature = "wasm")]
pub mod wasm_bindings;

#[cfg(test)]
mod test_suite;
#[cfg(all(test, feature = "extension-module"))]
mod vanilla_encoding_tests;

#[cfg(feature = "extension-module")]
use pyo3::prelude::*;

use serde_json as _;

#[cfg(feature = "extension-module")]
#[pymodule]
fn engine_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    py_bindings::register_python_module(m)
}
