# Lovecasim Project Documentation

> [!IMPORTANT]
> **Source of Truth Rules**:
> - **Frontend**: Edit `frontend/web_ui/` ONLY.
> - **Server**: Edit `launcher/` (Rust) ONLY. `backend/server.py` is **LEGACY/RETIRED**.
> - **Engine**: Edit `engine_rust_src/` (Rust) ONLY. `engine/` (Python) is **LEGACY/RETIRED**.
> - **Data**: Edit `data/cards.json` ONLY.
- **Tools**: Use `tools/`. Legacy scripts are in `tools/_legacy_scripts/`.

❌ **DO NOT EDIT**: `css/`, `js/`, `engine/data/`, `frontend/css|js` (orphans), `launcher/static_content/` (derived).
❌ **DO NOT EDIT LEGACY**: `engine/` (except `models/ability.py` for compiler), `backend/server.py`.

## 0. Critical Agent Protocol
These are mandatory workflows for any AI agent working on this project.

Always run default.md workflow.

### 🛡️ Skills First Policy
Before starting any significant task, **ALWAYS** check for relevant skills:
1. List `.agent/skills/` to see available capabilities.
2. Read the `SKILL.md` of any relevant skill.
3. Follow the skill's specific workflow.

### 📝 Terminal Output Handling
When running tests, builds, or analysis commands that produce significant output:
- **NEVER** let the output flood the chat.
- **ALWAYS** redirect output to a file (e.g., `reports/last_cmd_output.txt`) or ensure the tool writes to a file.
- **THEN** use `read_file` to inspect the results.

### 🔣 Encoding Safety
- **Python**: ALWAYS use `encoding="utf-8"` in `open()`. Windows defaults to cp1252 and WILL crash on Japanese text.
- **Rust**: Use `std::fs::read_to_string` (implies UTF-8) or `std::str::from_utf8`.

### 🪟 Windows Safety
- **Paths**: Use `os.path.join()` or double backslashes `\\`.
- **Search**: **NEVER** use `grep`. Use the provided `grep_search` tool or `Select-String` (Powershell).

## 1. Unified Architecture (Preventing Mess)
To keep the project organized while supporting multiple platforms (EXE, Web, Rust Server), we follow a **One-Way Data Flow**:

### 🏛️ Tier 1: Source (The Master)
This is where 100% of your work happens.
- **UI**: `frontend/web_ui/` (HTML/JS/CSS)
- **Engine**: `engine_rust_src/` (Rust Logic)
- **Data**: `data/cards.json` (Card Logic)
- **Assets**: `frontend/img/` (The only place you should add new images)

### ⚙️ Tier 2: Processing (The Sync)
Scripts that move/transform source code into delivery formats.
- `tools/sync_launcher_assets.py`: Mirrors `frontend/` -> `launcher/static_content/`.
- `tools/build_web_pwa.py`: Prepares a serverless build for GitHub Pages.

### 🚀 Tier 3: Delivery (The Apps)
These are **read-only** outputs. Never edit files inside these.
- **Local EXE**: Bundled via PyInstaller (`build_dist_optimized.py`).
- **Rust Launcher**: Standalone LAN host.
- **Web/PWA**: Hosted on GitHub Pages or wrapped in Android/iOS.

---

## 2. Project Overview
Lovecasim is a web-based implementation of the "Love Live! School Idol Collection" Trading Card Game (TCG). The project is designed with a client-server architecture where a Python/Flask backend (powered by a hybrid Python/Rust game engine) serves a Vanilla JS/HTML frontend.

## 3. Architecture

### Backend & Engine
- **Server (Primary)**: `launcher/` (Rust) - High-performance standalone server.
- **Server (Legacy)**: `backend/server.py` - Flask server (now secondary).
- **Engine (Primary)**: `engine_rust_src/` (Rust) - Core high-performance logic.
- **Engine (Legacy)**: `engine/` (Python) - Python implementation of game logic (secondary).
- **Serializer**: Rust launcher now handles its own rich serialization for API parity.

### Frontend
- **Location**: `frontend/web_ui/`
- **Assets**: `frontend/img/` (Card images and assets).
- **Core Files**: `frontend/web_ui/index.html`, `frontend/web_ui/js/main.js`, `frontend/web_ui/css/style.css`.
- **Note**: Do not edit files in the root `js/` or `css/` as they are likely orphaned or legacy.

### Data Pipeline
- **Master Data**: `data/cards.json`
- **Compilation**: The engine reads from `cards_compiled.json`.
- **Workflow**:
    1. Edit `data/cards.json`
    2. Run `uv run python -m compiler.main`
    3. Output -> `data/cards_compiled.json` (which is read by the engine).

## 3. Directory Structure
| Directory | Purpose |
|---|---|
| `backend/` | Server logic (`server.py`) and serialization (`rust_serializer.py`). |
| `compiler/` | Utilities (`parser_v2.py`) for processing raw card data options into bytecode/JSON. |
| `data/` | **MASTER DATA**. `cards.json` lives here. `rulesets/` contains experimental rules. |
| `engine/` | Python game logic. `engine/game/` (State), `engine/models/` (Schema). |
| `engine_rust_src/` | Rust source code `src/` and Cargo configuration. |
| `docs/` | Documentation, including opcode maps and developer guides. |
| `reports/` | Generated analysis reports (e.g., translation coverage, benchmarks). |
| `tests/` | Python test suite (Pytest). |
| `tools/` | Utility scripts (e.g., `analyze_translation_coverage.py`). |

## 4. Development Workflows

### Setup
- The project uses `uv` for Python dependency management.
- Rust toolchain (`cargo`) is required for the engine.

### Running the Game (Release)
```bash
# Run the optimized single-file executable
dist\LovecaSim.exe
```

### Running the Server (Dev)
```bash
# Standard Python/Flask server
start_server.bat
```

### Building the Release
Always run this to generate the optimized EXE and Source archive:
```bash
uv run python tools/build_dist_optimized.py
```
Output -> `dist/LovecaSim.exe` (128MB) and `dist/Source_Code.zip`.

### Running Tests
```bash
# Python Tests
uv run pytest

# Rust Tests
cd engine_rust_src
cargo test

# GPU Parity Tests (WIP)
cd engine_rust_src
cargo run --bin test_gpu_parity_suite > ../reports/parity_results.txt
```

### Linting & Formatting
```bash
uv run pre-commit run --all-files
```

## 5. Translation System
- **Master Translator**: `frontend/web_ui/js/ability_translator.js`
- **Pseudocode**: `data/manual_pseudocode.json` maps card abilities to readable strings.
- **Validation**:
    ```bash
    uv run python tools/analyze_translation_coverage.py
    ```
- **Sync**: Use `uv run python tools/sync_metadata.py` to propagate opcode changes from `data/metadata.json` to Rust/JS/Python.

## 6. Known Quirks & Windows Notes
- **Paths**: Use backslashes `\` or functional `os.path.join`.
- **Search**: **NEVER** use `grep` in `run_command`. Use `Select-String` in PowerShell or `findstr` in CMD. Better yet, use the provided `grep_search` tool which handles platform differences automatically.
- **Rust Engine**: The server will try to compile the rust engine if binaries are missing. Ensure `cargo` is in PATH.

## 7. Useful Tools
The `tools/` directory is organized into several categories:

- **Game Runners** (Root):
    - `tools/play_vs_ai.py`: Play a CLI game against the AI.
    - `tools/play_interactive.py`: Interactive debug session.
- **Analysis** (`tools/analysis/`):
    - Scripts for analyzing card data and game logs.
    - `tools/analysis/analyze_translation_coverage.py`: Check translation gaps.
- **Benchmarks** (`tools/benchmarks/`):
    - `tools/benchmarks/benchmark_ai.py`: Measure AI performance.
- **Validation** (`tools/verify/`):
    - `tools/validate_pseudocode.py`: Validate `manual_pseudocode.json`.
    - One-off verification scripts for specific bugs/features.
- **Generators** (`tools/generators/`):
    - Scripts to generate reports, replays, and test data.

- **Deployment**:
    - `tools/hf_upload_staged.py`: Deploy to HuggingFace Spaces.

- **Obsolete & Archive**:
    - `tools/_legacy_scripts/`: Old python scripts.
    - `tools/debug/`: Debugging scripts (moved from root).
    - `archive/`: Old logs and lint results.
## 8. Standardized File Handling (Anti-Circle Rules)
To prevent encoding errors and redundant logic, always follow these standards:

### Python (Foolproof UTF-8)
Always specify `encoding="utf-8"` explicitly. Windows defaults to `cp1252`, which crashes on Japanese text.
```python
# Reading JSON
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Writing JSON
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### Rust (Encoding Safety)
- **Disk**: `std::fs::read_to_string(path)` expects UTF-8 and is the standard for non-embedded files.
- **Embedded**: Use `std::str::from_utf8` on `RustEmbed` data.
```rust
let file = Assets::get("data/cards_compiled.json").expect("Missing asset!");
let json_str = std::str::from_utf8(file.data.as_ref()).expect("Invalid UTF-8");
```

### Critical File: cards_compiled.json
This file is the "Pre-compiled Truth".
- **Generator**: `uv run python -m compiler.main`
- **Location**: `data/cards_compiled.json`
- **Usage**: Both the Python engine (`engine/data/`) and Rust launcher use this for card logic, opcodes, and translations.

### 9. Card Research Standard (Source of Truth)
To avoid confusion between raw data and compiled engine logic, use the following workflow:

> [!WARNING]
> **Special Character Alert**: Card numbers containing `＋` (Full-width Plus) or `-` (half-width) can cause search failures in standard `grep`. Always use `tools/card_finder.py` or regex-based search if exact matches fail.

### Sources
- **`data/cards.json`**: Source of **Content**. Use this for card names, Japanese ability text, and manually written translations/pseudocode.
- **`data/cards_compiled.json`**: Source of **Logic**. Use this for engine IDs, compiled bytecode, and trigger values.
- **`reports/all_unique_abilities.md`**: Source of **Metadata**. Use this for frequency analysis and quick opcode lookups.

### Known ID Truths
- **Rank 5**: `PL!HS-PR-010-PR` -> ID `30030`
- **Rank 19**: `PL!SP-bp1-003-R＋` -> ID `1179`

### Recommended Tool
Use `tools/card_finder.py` to inspect a card across both data sources simultaneously.
```bash
uv run python tools/card_finder.py <CARD_NO_OR_TEXT>
```
*Example*: `uv run python tools/card_finder.py PL!SP-bp1-003-R＋`
