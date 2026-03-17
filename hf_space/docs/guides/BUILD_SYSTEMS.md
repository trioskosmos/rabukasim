# LovecaSim Build Systems

This document describes how to build different versions of LovecaSim for local use and distribution.

## 1. Local EXE (Optimized)
This is the standard way to distribute the game as a single-file executable for Windows.

- **Script**: `tools/build_dist_optimized.py`
- **What it does**:
  1. Prunes legacy PNG assets.
  2. Ensures only WebP images are included.
  3. Bundles the Python backend and core logic using PyInstaller.
  4. Optimizes file size (~100MB).
- **Commands**:
  ```bash
  uv run python tools/build_dist_optimized.py
  ```
- **Output**: `dist/LovecaSim.exe`

## 2. Rust Launcher (High Performance)
The Rust launcher is a standalone, compiled server that provides maximum performance for LAN play or high-load hosting.

- **Location**: `launcher/`
- **Prerequisites**: Rust toolchain (`cargo`).
- **Commands**:
  ```bash
  cd launcher
  cargo run --release
  ```
- **Note**: Ensure `launcher/static_content` is synced using `tools/sync_launcher_assets.py` if you modify the frontend.

## 3. WASM Engine (Web/Offline)
Required for the GitHub Pages / PWA version of the game.

- **Prerequisites**: `wasm-pack`.
- **Command**:
  ```bash
  wasm-pack build engine_rust_src --target web --out-dir ../frontend/web_ui/wasm
  ```
- **Cleanup**: After building, the `wasm/` folder inside `frontend/web_ui/` must contain:
  - `engine_rust.js`
  - `engine_rust_bg.wasm`
  - `engine_rust.d.ts` (optional)

## 4. Card Data Compilation
The engine (both Rust and Python) reads from `cards_compiled.json`. Always run this after editing `data/cards.json`.

- **Command**:
  ```bash
  uv run python -m compiler.main
  ```
- **Output**: `data/cards_compiled.json` (Automatically copied to `engine/data/`).
