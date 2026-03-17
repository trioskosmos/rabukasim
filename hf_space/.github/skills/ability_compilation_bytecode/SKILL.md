---
name: ability_compilation_bytecode
description: Unified framework for ability compilation, bytecode generation, semantic verification, and parity testing across all versions. **Covers ALL ability mapping, card-ability linking, ID resolution, and opcode management.**
keywords: 
  - ability mapping
  - card-ability linking
  - ability compilation
  - bytecode generation
  - card ID resolution
  - ability to card association
  - opcode management
tags:
  - ability-mapping
  - compilation
  - bytecode
---

# Ability Compilation, Mapping & Bytecode Management

This skill provides a complete end-to-end framework for:
- **Linking card IDs to ability definitions** (ability mapping)
- **Developing and compiling card abilities** into bytecode
- **Managing opcodes and semantic metadata**
- **Verifying bytecode parity and correctness**

It consolidates workflow steps previously scattered across `ability_logic`, `opcode_management`, and `pseudocode_guidelines`.

---

## � ABILITY MAPPING OVERVIEW

### What is Ability Mapping?
**Ability mapping** = linking card IDs to their ability definitions. This ensures each card knows what abilities it has and what they do.

### How It Works (Simplified Flow)

```
Card ID (e.g., 410)
    ↓
[cards.json] – Lists card metadata + name
    ↓
[consolidated_abilities.json] – Maps JP text → pseudocode
    ↓
[compiler/main.py] – Matches card names to pseudocode
    ↓
[cards_compiled.json] – Output: Card ID → Bytecode
    ↓
[codegen_abilities.py] – Syncs common abilities to Rust
    ↓
[Rust engine] – Executes ability when card is played
```

### Source of Truth Files for Ability Mapping
| File | Purpose | What It Contains |
|:---|:---|:---|
| `data/cards.json` OR `data/cards_vanilla.json` | Card registry | Card ID → Name, Type, Cost, **JP Text** |
| `data/consolidated_abilities.json` | Ability definitions | JP Text → Pseudocode logic |
| `data/cards_compiled.json` | Compiled output | Card ID → **Bytecode (compiled form)** |
| `engine_rust_src/src/core/hardcoded.rs` | Optimized subset | Frequently used abilities (faster execution) |

### Quick Ability Mapping Checks
- **"Does card ID 410 have an ability?"** → Check `cards.json`, search for ID 410, look for non-empty `text` field
- **"What does the ability text mean?"** → Open `consolidated_abilities.json`, find the JP text, check the `pseudocode` field
- **"Does the mapping work?"** → Run `python tools/inspect_ability.py 410` and verify bytecode matches pseudocode
- **"Is it in the Rust engine?"** → Check `hardcoded.rs` for the ability opcode; if missing, most common abilities need to be added via `codegen_abilities.py`

---

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

### Ability Mapping Issues
- **"Card ID X has no ability showing up"**: 
  1. Verify the card exists in `cards.json` with a non-empty `text` field.
  2. Check that the JP text appears in `consolidated_abilities.json`.
  3. If it does, run `python -m compiler.main` to recompile.
  4. Run `python tools/inspect_ability.py <ID>` to verify bytecode exists.
  5. If the ability is common, run `python tools/codegen_abilities.py` to ensure Rust knows about it.

- **"Card is in compiled JSON but doesn't work in-game"**: The Rust engine may have a hardcoded optimization. Run `tools/codegen_abilities.py` to sync.

### Compilation & Bytecode Issues  
- **"My change isn't working"**: Did you run `tools/codegen_abilities.py`? Most standard abilities are optimized into `hardcoded.rs` and ignore the compiled JSON at runtime.
- **"Unknown Opcode"**: Did you run `tools/sync_metadata.py` after adding it to `metadata.json`?
- **"Desync detected"**: If `inspect_ability.py` shows a desync, it means the compiler logic changed but the card wasn't re-built, or vice versa. Run a full compile.

---

## 🔍 Troubleshooting Ability Mapping

| Symptom | Root Cause | Solution |
|:---|:---|:---|
| Card found, no text | Card has `text: ""` or `text: null` | Update `cards.json` with the JP ability text |
| Text found, no pseudocode | Entry missing from `consolidated_abilities.json` | Add entry to `consolidated_abilities.json` with `"pseudocode": "..."` |
| Pseudocode exists, bytecode missing | Compiler error or old build | Run `python -m compiler.main` |
| Bytecode exists, not in Rust | Ability not hardcoded | Run `python tools/codegen_abilities.py` |
| Mismatch: Compiled vs Readable | Parser or decoder bug | Run `python tools/verify/test_parity_ir_bytecode_readable.py` |

---

## 📖 Related Files

- [metadata.json](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/metadata.json) - Opcode SSOT
- [ability_ir.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/ability_ir.py) - IR & Versioning models
- [bytecode_readable.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/bytecode_readable.py) - Decoder logic
- [parser_v2.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/parser_v2.py) - Pseudocode tokenizer
- [hardcoded.rs](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/core/hardcoded.rs) - Rust optimizations
