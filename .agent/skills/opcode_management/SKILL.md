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

### `a` (Attribute) Packing
The attribute word `a` is used for card filtering. While the Rust engine uses a `u64`, the bytecode word is typically packed as a `u32`. 

> [!WARNING]
> **Sign Extension**: Bytecode words are signed `i32`. When bit 31 (sign bit) is set, it will sign-extend to bits 32-63 in the Rust engine. Use bit 31 only as a flag that is checked before or after masking.

| Bits | Usage | Notes |
| :--- | :--- | :--- |
| **0** | **FREE** | Available for a new flag. |
| **1** | `DYNAMIC_VALUE` | If set, the effect value is dynamic. |
| **2-3** | Card Type | `1`=Member, `2`=Live. |
| **4** | Group Toggle | Enable group filter. |
| **5-11**| Group ID | 7-bit Group ID. |
| **12** | `FILTER_TAPPED` | Filter for tapped cards. |
| **13-14**| Blade Hearts | Flags for blade heart presence. |
| **15** | `UNIQUE_NAMES` | Count unique names instead of instances. |
| **16** | Unit Toggle | Enable unit filter. |
| **17-23**| Unit ID | 7-bit Unit ID. |
| **24** | Cost Toggle | Enable cost filter. |
| **25-29**| Cost Threshold | 5-bit cost (0-31). |
| **30** | Cost Mode | `0`=GE, `1`=LE. |
| **31** | Color Toggle | **SIGN BIT**. Triggers color filtering logic. |

### `s` (Slot/Target) Packing
When an opcode needs both a primary target and a secondary destination (like for remainders), or for condition comparison modes:

#### Effect Target Structure:
- **Bits 0-7**: Primary Target Slot (e.g., 6=Hand, 7=Discard, 4=Stage).
- **Bits 8-15**: Remainder/Secondary Destination.
  - `0`: Default (Source)
  - `7`: Discard
  - `8`: Deck Top (Shuffle)
  - `1`: Deck Top (No Shuffle)
  - `2`: Deck Bottom

#### Condition Target Structure:
- **Bits 0-3**: Target Slot (0-2 Stage, 10=Context Card).
- **Bits 4-7**: Comparison Mode:
  - `0`: GE (>=)
  - `1`: LE (<=)
  - `2`: GT (>)
  - `3`: LT (<)
  - `4`: EQ (==)
- **Bits 8-31**: **FREE** (Available for new condition flags).

*Note: The interpreter must explicitly mask `s & 0x0F` or `s & 0xFF` depending on the instruction type.*

## 7. Maintenance: Performing a Migration
Use this guide when you need to shift bit allocations (e.g., expanding Character ID space) or change ID assignment logic.

### Shifting Bitmasks
1. **Rust Engine**: Update `engine_rust_src/src/core/logic/interpreter/constants.rs` (shifts and masks).
2. **Interpreter Logic**: Update `engine_rust_src/src/core/logic/filter.rs` (ensure `from_attr` and `to_attr` reflect the new layout).
3. **Compiler**: Update `engine/models/ability.py` (specifically `_pack_filter_attr`) to match the Rust bitmask.
4. **Metadata**: Sync `data/metadata.json` if any high-level shifts are defined there.

### Card ID Synchronization
Card IDs are assigned to unique `(Name, Ability Text)` pairs and are relatively stable. However, if code logic changes:
1. **Check Tests**: Perform a global search in `engine_rust_src/src/` for hardcoded logic IDs (e.g., `30030`, `1179`). These will likely need manual updates.
2. **Master Mappings**: If adding new Characters or Groups, you must manually update the following files to maintain sync:
   - **Python**: `engine/models/enums.py` (`CHAR_MAP`, `Group`, `Unit`).
   - **Rust**: `engine_rust_src/src/core/logic/card_db.rs` (`CHARACTER_NAMES`).
   - **JS**: `frontend/web_ui/js/ability_translator.js` (for display names).

### Stability Rules
- **Alpha-Sorting**: The compiler always alpha-sorts card numbers before ID assignment. To maintain ID stability, ensure "Card No" strings never change.
- **Pseudocode**: Use card numbers (e.g., `LL-bp01-001`) in pseudocode parameters rather than logic IDs whenever possible to remain agnostic of ID shifts.

## 8. Opcode Rigor Audit
Unified workflow for assessing the rigor of opcode tests. Dry run tests are good for coverage, but specialized tests ensure correctness.

### Test Rigor Levels
- **Level 1 (Property Check)**: Verifies a value changed.
- **Level 2 (Parity Check)**: Compares outputs between two implementations (Semantic Audit).
- **Level 3 (Functional Behavior)**: Verifies gameplay flow, phase transitions, and interaction stack.

### Recipe: Level 3 "Interaction Cycle" Test
1. **Verify Suspension**: Assert `state.phase == Phase::Response` and `state.interaction_stack.len() > 0`.
2. **Action Generation**: Ensure correct action IDs are available.
3. **Resume**: Call `state.step(db, action_id)` and verify final state.

### One-Shot Ready Principles
- **Unified Dispatch**: Update both modular and legacy handlers.
- **ID Validation**: Use Logic IDs in `3000-3500` range for dummy tests.
- **Visibility**: Use debug prints for Phase and InteractionStack transitions.
