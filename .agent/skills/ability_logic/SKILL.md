# Ability Logic Skill

This skill provides a unified framework for card ability implementation, verification, and standard guidelines.

## 🎯 Core Objectives
1. **100% Semantic Fidelity**: Every card must behave exactly as its Japanese text describes.
2. **Bytecode Integrity**: 100% of compiled abilities must be valid and roundtrip-verified.
3. **No-Hassle Debugging**: Unified tools for inspecting card logic from text to execution.

## 🛠️ Core Capabilities

### 1. Semantic Audit Pipeline
The primary mechanism for verifying engine logic against textual meaning.
- **Workflow**:
    1. **Baseline**: `cargo test generate_v3_truth` (Synchronized capture).
    2. **Audit**: `cargo test test_semantic_mass_verification -- --nocapture`.
- **Reporting**: [COMPREHENSIVE_SEMANTIC_AUDIT.md](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/reports/COMPREHENSIVE_SEMANTIC_AUDIT.md).

### 2. Semantic Testing Methodology (Triangulation)
Every test must validate parity between:
- **Intent (JP Text)**: What the card *should* do (decoded by the Oracle).
- **Instruction (Bytecode)**: What the engine *tries* to do (compiled logic).
- **Inertia (State Delta)**: What the engine *actually* did (state changes).

### 3. Parser & Bytecode Tools
- **Roundtrip Verification**: `uv run python .agent/skills/ability_logic/scripts/verify_roundtrip.py`.
- **Bytecode Decoder**: `uv run python tools/verify/bytecode_decoder.py <bytecode_array>`.
- **Decompile Bytecode**: `uv run python tools/decompile_bytecode.py '<bytecode_json_array>'` (Human-readable logic).
- **Area Debugger**: `uv run python tools/debug_bytecode_area.py <CARD_NO>` (Extracts slot-specific bits).
- **Logic Audit**: `cargo test logic_audit -- --nocapture` (Deep desync check).
- **Pseudocode Auditor**: `uv run python tools/audit_pseudocode.py` (Checks for semantic/group mismatches).

## 📋 Guidelines & Standards

### Pseudocode Mappings
| Pseudocode | Delta Tag | Logic |
|------------|-----------|-------|
| `DRAW(n)` | `HAND_DELTA` | `after.hand - before.hand == n` |
| `DISCARD_HAND(n)` | `HAND_DISCARD` | `before.hand - after.hand >= n` |
| `ADD_BLADES(n)` | `BLADE_DELTA` | `after.blades - before.blades == n` |

### Interaction Cycle (Level 3 Testing)
A high-rigor test verifies the game's complex systems:
1. **Setup**: Hydrate `GameState` and `CardDatabase`.
2. **Execute**: Call `state.resolve_bytecode` or `state.activate_ability`.
3. **Verify Suspension**: Assert `state.phase == Phase::Response` and `stack.len() > 0`.
4. **Resumption**: Call `state.step(db, action_id)` and verify final state.

### Important Rules
- **Hardcoded Bypass**: Simple abilities are optimized in `hardcoded.rs`. ALWAYS run `uv run python tools/codegen_abilities.py` after modifying `cards.json`.
- **Empty Deck Refresh**: The engine shuffles discard into deck if deck is empty. Always populate dummy cards if discard stability is required.

## 🚀 Speed Verification
- **Crash Triage**: `cargo test crash_triage -- --nocapture` (Runs 287+ unique signatures in one pass).
- **Fault Isolation**: Categorize failures into systemic root causes (Condition Not Met, Score Delta Zero, etc.).
