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
The canonical edit target for ability logic is `data/consolidated_abilities.json` and the canonical card source is `data/cards.json`.
Run the consolidated build entrypoint after editing card or ability data. It now refreshes:

- `data/cards_compiled.json`
- `engine/data/cards_compiled.json`
- `launcher/static_content/data/cards_compiled.json`

- **Command**:
  ```bash
  uv run python tools/build_cards.py --force --sync-launcher-assets
  ```
- **Output**: `data/cards_compiled.json` plus the mirrored live copies used by the engine and launcher.
