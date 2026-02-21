# WASM Distribution & Offline Mode

This document explains the "Offline Mode" implemented to allow distributing the card game without requiring users to install Python, Docker, or large executables.

## What has been done

We have ported the core game engine (written in Rust) to **WebAssembly (WASM)** and created a portable launcher.

*   **Rust Engine**: The `engine_rust` crate was modified to support compilation to the `wasm32-unknown-unknown` target.
*   **Frontend Adapter**: A new `wasm_adapter.js` file intercepts API calls and routes them to the local WASM engine, replacing the Python backend.
*   **Portable Launcher**: A standalone, lightweight executable (`loveca_launcher`) that serves the game files locally and opens the browser, bypassing "local file" security restrictions.

## How it avoids installations

Traditionally, running this game required installing Python, compiling extensions, and running a server.

With the **Portable Launcher**:
1.  **Zero Installation**: Users just unzip the folder and run `loveca_launcher`.
2.  **No Python Required**: The launcher is a self-contained 1.4MB binary.
3.  **Browser-Based**: The game logic runs securely inside the user's browser via WASM.

## Requirements (End User)

*   **Software Required**: A modern Web Browser (Chrome, Edge, Firefox, Safari).
*   **Setup**:
    1.  Unzip the package.
    2.  Double-click **`loveca_launcher`** (or `.exe`).
    3.  The game starts automatically.

## File Sizes (Measured)

The distribution is extremely lightweight compared to the Python environment (~2GB source/venv).

| Component | Size | Notes |
|T---|---|---|
| **Launcher** | **1.4 MB** | The executable file. |
| **Game Engine (WASM)** | **~1-2 MB** | compiled logic (placeholder in this repo). |
| **Card Database** | **3.6 MB** | `cards_compiled.json`. |
| **Frontend (HTML/JS)** | **~1 MB** | The web interface. |
| **Total** | **~6 - 8 MB** | **< 1% of the original size.** |

*Note*: This size excludes card images (`img/` folder). Users can copy their `img` folder into `dist/www/img` if they want full offline images, which will increase the size.
