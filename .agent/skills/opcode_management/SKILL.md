---
name: opcode_management
description: Unified workflow for adding, modifying, and synchronizing opcodes across Rust, Python, and JavaScript.
---

# Opcode Management Skill

Use this skill when you need to add a new game mechanic (opcode), condition, or trigger that must be consistent across the engine (Rust), the compiler (Python), and the user interface (JS).

## 1. The Single Source of Truth
All opcode definitions are stored in:
`data/metadata.json`

This file contains mapping for:
- `opcodes`: Effect opcodes (bytecodes 0-99)
- `triggers`: Card ability trigger types
- `targets`: Bytecode targeting modes (100-199)
- `conditions`: Bytecode condition checks (200-299)
- `action_bases`: Numerical bases for Action IDs (used in legal action generation)
- `phases`: Game phase IDs
- `costs`: Ability cost types

## 2. Adding a New Opcode
1. **Edit JSON**: Add the new key-value pair to the appropriate section in `data/metadata.json`.
   - Keys must be `SCREAMING_SNAKE_CASE`.
   - Values must be unique within their section.

2. **Run Sync**: Execute the synchronization script to propagate changes to all languages.
   ```bash
   uv run python tools/sync_metadata.py
   ```

## 3. Propagation Targets
Running the sync script automatically updates:

| Language | Target File | Purpose |
|---|---|---|
| **Rust** | `engine_rust_src/src/core/enums.rs` | Enums with `serde` support for serializing state. |
| **Rust** | `engine_rust_src/src/core/generated_constants.rs` | `pub const` for high-performance match statements in the interpreter. |
| **JS** | `frontend/web_ui/js/generated_constants.js` | Exports for the UI and ability translator. |
| **Python**| `engine/models/generated_metadata.py` | Metadata dictionaries for the card compiler. |

## 4. Verification
After syncing, verify that everything still compiles and tests pass:

```bash
# Verify Rust Engine
cd engine_rust_src
cargo check

# Verify Python Compiler/Models
uv run pytest

# Verify Frontend
# Open index.html and ensure ability text is still rendered correctly.
```

## 5. Implementation Rules
- **Naming**: Rust variants will be auto-converted to `PascalCase`. (e.g., `DRAW` -> `Draw`, `ADD_HEARTS` -> `AddHearts`).
- **Reserved Words**: `SELF` in JSON is converted to `Self_` in Rust to avoid keyword conflict.
- **Defaults**: All generated Rust enums implement `Default`. `TriggerType` defaults to `None`, `EffectType` defaults to `Nop`.

## 6. Parameter Bit-Packing Standards
To save space in the 4x32-bit bytecode structure, some opcodes use bit-packing for their parameters:

### `v` (Value) Packing
- `LOOK_AND_CHOOSE`: `RevealCount | (PickCount << 8) | (ColorMask << 23)`

### `s` (Slot/Target) Packing
When an opcode needs both a primary target and a secondary destination (like for remainders), use the following 16-bit packed structure:
- **Bits 0-7**: Primary Target Slot (e.g., 6=Hand, 7=Discard, 4=Stage).
- **Bits 8-15**: Remainder/Secondary Destination.
  - `0`: Default (Source)
  - `7`: Discard
  - `8`: Deck Top (Shuffle)
  - `1`: Deck Top (No Shuffle)
  - `2`: Deck Bottom

*Note: The interpreter must explicitly mask `s & 0xFF` to get the target slot.*

