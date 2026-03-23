---
name: ability_execution_frames
description: Structured framework for ability execution, AbilityFrame management, and signature-based logic mapping.
---

# Ability Execution Frames Skill

This skill provides a unified reference for the LovecaSim "Ability Frame" system, which has replaced legacy bytecode as the primary execution model for card abilities.

## 🏗️ Core Architecture: Frame-First
The engine now executes logic from **Frame Programs** rather than raw bytecode.

- **Primary Source of Truth**: `data/ability_frames.json`
- **Mapping Key**: `signature` (or `signature_hash`)
- **Runtime Representation**: `AbilityFrame` (Rust Enum)

### 🧩 AbilityFrame Variants
Abilities are sequences of `AbilityFrame` objects. Key variants include:
- `Return`: Terminates execution.
- `Draw { count: i32 }`: Draws cards.
- `Semantic { opcode, value, filter, slot, ... }`: Most complex logic (Effect-based).
- `RecoverLive`, `RecoverMember`, `LookAndChoose`, `SelectMember`, `MoveMember`, `MetaRule`: Specialized high-level frames.
- `Raw`: Compatibility layer for raw opcodes (avoid in new development).

## 🗺️ Mapping & Identification
Cards are linked to their logic via a unique **Signature**.

1. **Find Card Signature**: Use `cf.py "<CARD_NO>" --json` to see the `signature` field.
2. **Lookup Frame Sequence**: Search for that signature in `data/ability_frames.json`.
3. **Inspect Implementation**: Review the `frames` array in the JSON to see exactly what the card does.

### 🔍 Quick Discovery with `cf.py`
The `cf.py` tool automatically resolves frames for you:
```bash
uv run python tools/cf.py "PL!N-bp1-001" --output reports/card_analysis.md
```
Then view the "Ability Frames" section in the generated report.

## 🔄 4-Phase Ability Cycle (Frame-Era)
When working on card abilities, follow this cycle:

1. **Discovery**: Use `cf.py` to check the current Frame sequence and Signature.
2. **Validation**: Cross-reference with `data/ability_frames.json` to ensure the logic matches the card text.
3. **Execution**: Verify in Rust using `FrameProgram::from_bytecode` (for tests) or by building frames directly.
4. **Verification**: Confirm behavior in `qa_verification_tests.rs` using real card IDs.

## 🛡️ Single Source of Truth (SSOT)
- **Logic Definition**: `data/ability_frames.json` (Editable source for new logic).
- **Metadata**: `data/metadata.json` (Defines opcodes, triggers, and UI strings).
- **Engine Models**: `engine_rust_src/src/core/logic/models.rs` (The Rust definition of `AbilityFrame`).

## ⚠️ Common Pitfalls
- **Bytecode Obsession**: DO NOT author tests or documentation against raw `bytecode: vec![...]` unless specifically testing the legacy codec.
- **Signature Desync**: If you change logic, you MUST update the signature to avoid collision with the old version.
- **Raw Frames**: Prefer `Semantic` frames over `Raw` frames for better readability and engine integration.

## Related Files
- [ability_frames.json](file:///c:/Users/trios/../data/ability_frames.json)
- [models.rs (AbilityFrame)](file:///c:/Users/trios/../engine_rust_src/src/core/logic/models.rs)
- [cf.py](file:///c:/Users/trios/../tools/cf.py)
