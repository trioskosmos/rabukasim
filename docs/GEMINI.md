# Lovecasim Project Context

> [!IMPORTANT]
> **Source of Truth Rules**:
> - **Frontend**: Edit `frontend/web_ui/` ONLY.
> - **Server**: Edit `backend/server.py` ONLY.
> - **Data**: Edit `data/cards.json` ONLY.
> - **Engine**: Edit `engine/` (Python) or `engine_rust_src/` (Rust).
> - **Tools**: Use `tools/`. Legacy scripts are in `tools/_legacy_scripts/`.
>
> ❌ **DO NOT EDIT**: `css/`, `js/`, `engine/data/`, `frontend/css|js` (orphans).

## ⚡ Update Cheat Sheet

| If you edited... | ...then you MUST run: |
| :--- | :--- |
| **`data/cards.json`** | `uv run python -m compiler.main` |
| **`engine_rust_src/`** | `cd launcher && cargo run` (to verify) |
| **`frontend/web_ui/`** | `python tools/sync_launcher_assets.py` (if using Rust Launcher) |
| **The AI Logic** | `uv run python tools/hf_upload_staged.py` (to redeploy HF) |

**Full Guides**: [Deployment](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/guides/DEPLOYMENT.md) \| [Build Systems](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/guides/BUILD_SYSTEMS.md)

## Overview
This project is a web-based implementation of the "Love Live! School Idol Collection" Trading Card Game (TCG).

## Architecture
The project follows a modular architecture separating the game engine, backend server, and frontend assets.

- **Engine** (`engine/`): Core game logic, state management, and data models.
- **Backend** (`backend/server.py`): Flask server exposing the game via API.
- **Frontend** (`frontend/web_ui/`): Vanilla HTML/JS interface. Served static assets.
- **Compiler** (`compiler/`): Utilities for processing raw card data into `cards_compiled.json`.
- **Tools** (`tools/`): Utility scripts and benchmarks.

## Translation System
The project uses a localized translation system for card abilities.
- **Master Translator**: `frontend/web_ui/js/ability_translator.js`.
- **Process**: Compiles raw Japanese text into "pseudocode" strings in `cards_compiled.json`, which are then translated by the frontend for display (supporting JP and EN).
- **Parity**: Opcode constants in `ability_translator.js` MUST match `engine_rust_src/src/core/logic.rs` and `engine/models/opcodes.py`.
- **Maintenance**: Use `uv run python tools/analyze_translation_coverage.py` to ensure 100% coverage after engine changes.

## Key Directories
| Directory | Purpose |
|O---|---|
| `data/` | **MASTER DATA**. Edit `cards.json` here. |
| `frontend/web_ui/` | **MASTER FRONTEND**. All CSS/JS/HTML lives here. |
| `backend/` | Server logic. |
| `engine/game/` | Game state, logic, and turn orchestration. |
| `engine/models/` | Pydantic models. |
| `engine/tests/` | Comprehensive test suite (Pytest). |
| `tools/_legacy_scripts/` | Archived old scripts. |

## Development Standards

### Static Analysis
We enforce high code quality using pre-commit hooks.
- **Linting & Formatting:** `ruff` (replaces black/isort/flake8).
- **Type Checking:** `mypy` (strict mode compliant).
- **Automation:** `pre-commit` runs these checks on every commit.

**Commands:**
```bash
# Run all checks
uv run pre-commit run --all-files

# Manual checks
uv run ruff check .
uv run mypy .
```

### Testing
Tests are run using **Pytest**.
- **Run all tests:** `uv run pytest`
- **Data Source:** Tests read from `engine/data/`, which is auto-synced from `data/` by the compiler.

## Windows Environment Notes
- **Search**: Use `findstr` or `Select-String` (PowerShell) instead of `grep`.
- **Paths**: Use backslashes `\` or ensure cross-platform compatibility.
- **Tools**: Preference for `uv run python` for script execution.

## Logic Quirks & Learnings
- **Pre-compiled Data:** The engine now relies on `cards_compiled.json`. Always run `uv run python -m compiler.main` after editing `cards.json`.
- **GameState Class Vars:** `member_db` and `live_db` are class-level for memory efficiency; tests must handle this.
- **Conditionals:** `GROUP_FILTER` checks prioritize `context` (e.g., revealed card) over global state.
- **Arrays:** `tapped_energy` is a fixed-size NumPy array.
- **Action IDs:**
    - **Color Select:** 580-585 (Pink, Red, Yellow, Green, Blue, Purple)
    - **Target Opponent:** 600-602 (Stage Slots)
