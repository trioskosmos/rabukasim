# Lovecasim Project Structure

> [!IMPORTANT]
> This document defines the **Single Source of Truth** for all file locations.
> Do NOT create duplicate files in other locations.

## 📂 Source of Truth Map

| Component | Canonical Identity | Location | Notes |
|-----------|--------------------|----------|-------|
| **Frontend** | Web UI Assets | `frontend/web_ui/` | **ONLY** edit here. Served by Flask. |
| **Backend** | Flask Server | `backend/server.py` | The only active server file. |
| **Data** | Game Data | `data/` | `cards.json` lives here. Compiler syncs to `engine/data/`. |
| **Engine** | Python Logic | `engine/` | Game state, logic, tests. |
| **Engine (Rust)** | Rust Core | `engine_rust_src/` | Rust source code. |
| **Compiler** | Data Compiler | `compiler/` | `main.py` compiles JSON. |
| **Tools** | Scripts/Utils | `tools/` | All utility scripts. |
| **AI** | RL Agents | `ai/` | Training and inference code. |
| **Reports** | Analysis Outputs | `reports/` | Generated analysis and audit reports. |

---

## 🚫 Forbidden / Legacy Paths

| Path | Status | Action |
|------|--------|--------|
| `css/` | **DELETED** | Use `frontend/web_ui/css/` |
| `js/` | **DELETED** | Use `frontend/web_ui/js/` |
| `scripts/` | **MOVED** | Moved to `tools/_legacy_scripts/` |
| `engine/data/` | **READ-ONLY** | Auto-synced from `data/`. Do not edit manually. |
| `backend/server_old.py` | **DELETED** | Use `backend/server.py` |
| `compiler/parser_legacy.py` | **DELETED** | Use `compiler/parser.py` |

---

## 🛠️ Workflow Rules

1.  **Editing Frontend:**
    *   Always work in `frontend/web_ui/`.
    *   Do NOT create `frontend/css` or `frontend/js` (without web_ui).

2.  **Editing Data:**
    *   Edit `data/cards.json`.
    *   Run `uv run python -m compiler.main` to compile.
    *   This automatically updates `engine/data/cards_compiled.json`.

3.  **Running Scripts:**
    *   Scripts in `tools/` should reference `data/` for input/output where possible.
    *   Legacy scripts in `tools/_legacy_scripts/` may need migration.

4.  **Tests:**
    *   Run `uv run pytest`.
    *   Tests read from `engine/data/` (which is synced from `data/`).

---

## 🌳 Detailed Tree

```text
loveca-copy/
├── ai/                 # AI Agents & Training
├── backend/            # Flask Server
│   └── server.py       # Main Entry Point
├── compiler/           # Card Data Compiler
├── data/               # MASTER Data Directory
│   ├── cards.json      # Edited by Humans
│   └── cards_compiled.json # Generated
├── docs/               # Documentation
├── engine/             # Python Game Engine
│   ├── data/           # Symlinked/Synced from ../data
│   ├── game/           # Game Logic
│   └── tests/          # Pytest Suite
├── engine_rust_src/    # Rust Implementation
├── frontend/           # Web Interface
│   └── web_ui/         # SERVED Directory
│       ├── css/
│       ├── js/
│       └── index.html
├── reports/            # Analysis Reports
└── tools/              # Utilities & Scripts
    └── _legacy_scripts/ # Archived scripts
```
