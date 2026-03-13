---
name: ability_compilation_bytecode
description: Unified framework for ability compilation, bytecode generation, semantic verification, and parity testing across all versions.
---

# Ability Compilation & Bytecode Management

This skill provides a complete end-to-end framework for developing, compiling, and verifying card abilities. It consolidates workflow steps previously scattered across `ability_logic`, `opcode_management`, and `pseudocode_guidelines`.

---

## 🚀 Unified Development Workflow (`/ability_dev`)

Follow this 4-phase cycle for ALL ability work. **Do not reinvent scripts.**

### Phase 1: Research & Triage
1. **Analyze Card**: `uv run python tools/card_finder.py "<ID_OR_NO>"`
   *   *Purpose*: View current JP text, pseudocode, and decoded bytecode side-by-side.
2. **Check Rules**: Search `data/qa_data.json` for related rulings.
3. **Verify Existing Logic**: `uv run python tools/test_pseudocode.py --card "<ID>"`
   *   *Purpose*: Fast localized check of the current consolidated pseudocode.

### Phase 2: Logic Implementation
1. **Edit Source**: Update `data/consolidated_abilities.json`.
   *   *Standard*: Find the JP text key and update its `pseudocode` field.
2. **Compile**: `uv run python -m compiler.main`
   *   *Note*: This updates `data/cards_compiled.json`.
3. **Inspect Result**: `uv run python tools/inspect_ability.py <PACKED_ID>`
   *   *Purpose*: Verify that the re-compiled bytecode matches your expectations.

### Phase 3: Engine Verification
1. **Sync Optimizations**: `uv run python tools/codegen_abilities.py`
   *   > [!IMPORTANT]
   *   > **CRITICAL**: The Rust engine uses a hardcoded path for common abilities. If you skip this, your changes may not appear in-game.
2. **Repro Test**: Add/run a test in `engine_rust_src/src/repro/`.
   *   Run: `cargo test <test_name> --nocapture`.
3. **Trace**: Add `state.debug.debug_mode = true` in Rust to see the execution stack.

### Phase 4: Quality Audit
1. **Parity Check**: `uv run python tools/verify/test_parity_ir_bytecode_readable.py`
   *   *Purpose*: Ensure IR, Bytecode, and Decoder remain in sync.
2. **Semantic Audit**: `cargo test test_semantic_mass_verification -- --nocapture`
   *   *Purpose*: Mass verification against "truth" baselines.
3. **Roundtrip**: `uv run python tools/verify_parser_roundtrip.py`

---

## 🛠️ Tool Discovery Matrix

| Tool | Command | Primary Use Case |
| :--- | :--- | :--- |
| **Finder** | `python tools/card_finder.py "<QUERY>"` | Start here. ID/Name lookup + logic view. |
| **Inspector** | `python tools/inspect_ability.py <ID>` | Deep dive into bytecode vs semantic form. |
| **Tester** | `python tools/test_pseudocode.py "<TEXT>"` | Rapid iterative prototyping of syntax. |
| **Compiler** | `python -m compiler.main` | Official build of `cards_compiled.json`. |
| **CodeGen** | `python tools/codegen_abilities.py` | Sync Python logic to Rust `hardcoded.rs`. |
| **Metadata** | `python tools/sync_metadata.py` | Propagate `metadata.json` to Python/Rust/JS. |
| **Matrix** | `python tools/gen_full_matrix.py` | Update [QA Matrix](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/.agent/skills/qa_rule_verification/qa_test_matrix.md). |

---

## 🔗 Single Source of Truth (SSOT)

Documentation and code flow through the system in this order:

1.  **Definitions**: `data/metadata.json` (Opcodes, Targets, Conditions).
2.  **Propagation**: `tools/sync_metadata.py` updates:
    -   `engine_rust_src/src/core/enums.rs` (Rust)
    -   `engine/models/generated_metadata.py` (Python)
    -   `frontend/web_ui/js/generated_constants.js` (JS)
3.  **Logic**: `data/consolidated_abilities.json` (Pseudocode).
4.  **Compilation**: `compiler/main.py` generates `data/cards_compiled.json`.
5.  **Optimization**: `tools/codegen_abilities.py` generates `engine_rust_src/src/core/hardcoded.rs`.

---

## 📊 Bytecode Layout & Versioning

### Layout v1 (Fixed 5-word × 32-bit)
```
Word 0: [1000? + Opcode] (1000+ indicates negation/NOT)
Word 1: [Value / Parameter]
Word 2: [Attribute Low Bits]
Word 3: [Attribute High Bits]
Word 4: [Slot / Zone Encoding]
```

### Version Gating
Use `engine.models.ability_ir.VersionGate` to handle layout changes without breaking legacy cards.
- **Default**: `BYTECODE_LAYOUT_VERSION = 1`
- **Compiler Flag**: `python -m compiler.main --bytecode-version 2`

---

## ⚠️ Common Pitfalls

- **"My change isn't working"**: Did you run `tools/codegen_abilities.py`? Most standard abilities are optimized into `hardcoded.rs` and ignore the compiled JSON at runtime.
- **"Unknown Opcode"**: Did you run `tools/sync_metadata.py` after adding it to `metadata.json`?
- **"Desync detected"**: If `inspect_ability.py` shows a desync, it means the compiler logic changed but the card wasn't re-built, or vice versa. Run a full compile.

---

## 📖 Related Files

- [metadata.json](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/metadata.json) - Opcode SSOT
- [ability_ir.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/ability_ir.py) - IR & Versioning models
- [bytecode_readable.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/bytecode_readable.py) - Decoder logic
- [parser_v2.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/parser_v2.py) - Pseudocode tokenizer
- [hardcoded.rs](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/core/hardcoded.rs) - Rust optimizations
