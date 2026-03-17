# WASM Maintenance & Robustness Guide

This document answers the question: *"What do I change as I continue developing, and will this continue to work no matter what?"*

## Executive Summary

**No, this will NOT continue to work "no matter what."**

The WASM distribution relies on a specific set of constraints and parallel implementations. Breaking these constraints will cause the offline mode to fail to compile or behave incorrectly, even if the Python backend works fine.

## Key Architectures to Maintain

### 1. Dual Bindings (`py_bindings.rs` vs `wasm_bindings.rs`)
The Rust engine now has **two separate entry points**:
*   `src/py_bindings.rs`: Uses `pyo3` to expose classes to Python.
*   `src/wasm_bindings.rs`: Uses `wasm-bindgen` to expose classes to JavaScript.

**What to do:**
*   If you add a new method to `GameState` (e.g., `undo_turn()`) and want it available in the offline game, you must expose it in **BOTH** files.
*   `py_bindings` returns Python objects; `wasm_bindings` must return Serde-serializable structs or primitives that JS can understand.

### 2. Dependency Management (`Cargo.toml`)
WebAssembly runs in a sandboxed browser environment. It generally **cannot** use:
*   C-linked libraries (unless compiled to WASM, which is hard).
*   File System I/O (`std::fs`, `std::io` related to files).
*   Networking (`std::net`, `reqwest` usually need WASM-specific feature flags).
*   Multi-threading (Standard `std::thread` is not supported; `rayon` is included but generally falls back to serial on WASM unless configured with Web Workers).

**Critical Rules:**
*   **Gate Python Dependencies:** `pyo3` and `numpy` must ALWAYS be optional and gated behind the `extension-module` feature.
    ```toml
    # Good
    pyo3 = { version = "...", optional = true }
    ```
*   **Gate System Dependencies:** If you need to read a file in Rust, gate it so it doesn't compile for WASM.
    ```rust
    #[cfg(not(target_arch = "wasm32"))]
    fn read_config() { ... }
    ```

### 3. The "Mock" Adapter (`wasm_adapter.js`)
The `wasm_adapter.js` file manually mimics the behavior of your Python Flask server (`server.py`).

**What to do:**
*   If you change the format of the JSON returned by `/api/state` in Python, you **MUST** update `wasm_adapter.js` to match.
*   If you add a new endpoint (e.g., `/api/play_sound`), the offline mode will throw errors unless you implement a handler for it in `wasm_adapter.js` (or `main.js` checks for offline mode).

### 4. Data Format (`cards_compiled.json`)
The WASM engine loads the card database from a JSON file fetched via HTTP (`fetch('/data/cards_compiled.json')`).

**Robustness:**
*   If `CardDatabase::from_json` in Rust changes its expected schema, the `cards_compiled.json` file must be regenerated.
*   Since WASM cannot scan a directory of images or JSONs, this "compiled" single file is the Single Source of Truth for the offline engine.

## Checklist for New Features

When implementing a new feature (e.g., "Mulligan Phase"):

1.  [ ] **Core Logic**: Implement in `src/core/logic.rs`. (Safe for both)
2.  [ ] **Python API**: Expose in `src/py_bindings.rs`.
3.  [ ] **WASM API**: Expose in `src/wasm_bindings.rs`.
4.  [ ] **Verification**: Run `cargo build --target wasm32-unknown-unknown --release --no-default-features` to ensure you didn't break the WASM build.
5.  [ ] **Frontend**: Update `main.js` / `wasm_adapter.js` if the API signature changed.

## Troubleshooting

*   **"Crate `pyo3` not found"**: You are trying to compile WASM with default features. Use `--no-default-features`.
*   **"Random number generator error"**: Ensure `getrandom` is set to `features = ["wasm_js"]` (or `js` for v0.2) in `Cargo.toml`.
*   **"Undefined symbol"**: You likely used a C library or system call not available in the browser.
