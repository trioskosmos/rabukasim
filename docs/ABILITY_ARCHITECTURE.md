# Ability System Architecture & Pipeline

> **Document Purpose**: Single source of truth for the card ability execution pipeline.
> This file documents the ACTUAL state of the system, including over-engineered components
> that need simplification.

> **Canonical ability source file**: `data/consolidated_abilities.json`
> The runtime loader reads this file; engine code should not write back to it.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER (JSON)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  consolidated_abilities.json  →  Main card database (1MB+)                   │
│  metadata.json                →  Opcode/trigger name mappings               │
│  cards_compiled.json          →  Compiled card cache (redundant versions)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER (card_db.rs)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  CardDatabase::from_json()                                                   │
│    ├── inject_missing_ability_conditions()  [HARDCODED PATCHES - REMOVE]     │
│    ├── enrich_member_runtime_metadata()     [RUNTIME DERIVATION - PRECOMPUTE]│
│    └── derive_conditions_from_frame_program()                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERPRETER LAYER (interpreter/)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  interpreter/mod.rs           →  resolve_ability(), resolve_semantic_frames()│
│  interpreter/handlers/        →  20+ handler files (FRAGMENTED)              │
│  interpreter/costs.rs         →  Cost resolution                             │
│  interpreter/logging.rs       →  Frame description (DEBUG ONLY - MOVE)       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTION GENERATION (action_gen/)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  response.rs, main_phase.rs, etc. → Generate valid player actions          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Dependencies (What Each File Reads/Writes)

### Data Files (JSON) - SINGLE SOURCE OF TRUTH

| File | Type | Written By | Read By | Notes |
|------|------|------------|---------|-------|
| `data/consolidated_abilities.json` | **SOURCE** | External data pipeline (Python tools) | `card_db.rs`, `ability_manifest.rs` | Contains card definitions + frame_programs. **NEVER written by Rust code** |
| `data/metadata.json` | **SOURCE** | External tools | `card_db.rs`, `ability_manifest.rs`, `logging.rs` | Opcode/trigger name mappings |
| `data/cards_compiled.json` | CACHE | `card_db.rs` (binary serialization) | None | Redundant cache - can be removed |
| `data/ability_frame_index.json` | GENERATED | Unknown external tool | Unknown | Questionable purpose |

### Rust Source Files - HAND-WRITTEN (Never write to JSON)

| File | Lines | Reads From | Writes To | Purpose |
|------|-------|------------|-----------|---------|
| `src/core/logic/card_db.rs` | ~2200 | `consolidated_abilities.json`, `metadata.json` | `cards_compiled.json` (cache) | **SHOULD ONLY READ** - Loads card data, patches it at runtime (BAD) |
| `src/core/logic/models.rs` | ~1800 | Nothing (data structures) | Nothing | Defines `Ability`, `AbilityFrame`, etc. |
| `src/core/logic/interpreter/mod.rs` | ~760 | `models.rs`, `handlers/` | Nothing | Executes abilities - pure logic |
| `src/core/logic/interpreter/handlers/*.rs` | ~2000 | `models.rs`, `constants.rs` | Nothing | Opcode handlers - pure logic |
| `src/core/logic/interpreter/costs.rs` | ~150 | `models.rs`, `filter.rs` | Nothing | Cost resolution logic |
| `src/core/logic/interpreter/conditions/*.rs` | ~400 | `models.rs` | Nothing | Condition checking logic |
| `src/core/logic/interpreter/logging.rs` | ~580 | `models.rs`, `metadata.json` | Nothing | **DEBUG ONLY** - Human-readable descriptions |
| `src/core/logic/ability_manifest.rs` | ~744 | `consolidated_abilities.json`, `metadata.json` | Nothing | **BUILD TIME** - Generates human-readable docs |
| `src/core/logic/ability_patterns.rs` | ~227 | `models.rs` | Nothing | Pattern matching for abilities |
| `src/core/logic/handlers.rs` | ~1648 | `models.rs`, `interpreter/` | Nothing | Game phase handlers |
| `src/core/logic/filter.rs` | ~800 | `models.rs` | Nothing | CardFilter logic |
| `src/core/logic/effects.rs` | ~26 | Nothing | Nothing | **STUBBED** - was 762 lines |
| `src/core/logic/constants.rs` | ~142 | `generated_constants.rs` | Nothing | Re-exports and adds logic-specific constants |

### Generated Files

| File | Lines | Generated By | Purpose |
|------|-------|------------|---------|
| `src/core/generated_constants.rs` | ~558 | `tools/sync_metadata.py` | Opcode/condition/cost constants from metadata |
| `src/core/generated_layout.rs` | ~200 | `tools/sync_metadata.py` | Bitfield layout constants |

---

## Key Rule: **JSON Files Are Source Of Truth**

**NEVER** should Rust code write to:
- `data/consolidated_abilities.json`
- `data/metadata.json`

**ONLY** external Python tools should write to JSON files.

**Rust engine should:**
1. Load JSON at startup
2. Execute abilities using frame_program bytecode
3. Never modify card data at runtime

---

### 6. COMPILATION FAILURES (Python Pipeline - Mar 2026)

**Status**: Python ability compiler fails on certain semantic patterns

**Problem**: The external Python pipeline that generates `consolidated_abilities.json` has compilation failures for certain ability patterns:

| Card | Pattern | Japanese Text | Expected | Actual |
|------|---------|---------------|----------|--------|
| PL!HS-bp1-019-L | Per-score modifier | エールで出たスコア1つにつき... | `BOOST_SCORE` | `RETURN` only |
| PL!N-bp5-006-AR | Conditional wait | このメンバーは...アクティブにしない。いる場合...ウェイトにする | `PREVENT_ACTIVATE`, `SET_TAPPED` | `RETURN` only |
| PL!HS-bp5-018-L | Conditional score | メンバーが3人以上いる場合...スコアを+１する | `COUNT_STAGE`, `JUMP_IF_FALSE`, `BOOST_SCORE` | `RETURN` only |
| PL!SP-bp1-001-P | Restriction | ステージにほかのメンバーがいない場合...ライブできない | `COUNT_STAGE`, `JUMP_IF_FALSE`, `RESTRICTION` | `RETURN` only |
| PL!SP-bp1-003-P | Sum condition | 公開したカードのコストの合計が10...の場合...スコアを+１する | `SUM_VALUE`, `JUMP_IF_FALSE`, `BOOST_SCORE` | `RETURN` only |
| PL!N-bp3-026-L | Score check | スコアが１か５のカードがある場合...スコアを+１する | `SCORE_COMPARE`, `JUMP_IF_FALSE`, `BOOST_SCORE` | `RETURN` only |
| PL!N-bp3-006-P | State change | このメンバーをウェイトにする | `SET_TAPPED` | `RETURN` only |

**Root Cause**: The Python compiler fails on:
1. `につき` (per/for each) score modifiers
2. Multi-part conditional abilities with state changes
3. Complex constant abilities with embedded restrictions

**Impact**: These 7 abilities (1.4% of total) will not function in-game. The Rust engine's `inject_missing_ability_conditions()` has been patching some of these, but this is marked as wrong.

**Solution**: Fix the Python compiler to generate proper semantic frames, then remove runtime patches.

---

## Current Data Flow (WRONG - Needs Fix)

```
External Tools → consolidated_abilities.json → card_db.rs → [PATCHES DATA AT RUNTIME] → Game State
```

## Correct Data Flow (Target)

```
External Tools → [PRECOMPUTE ALL FIELDS] → consolidated_abilities.json → card_db.rs [LOAD ONLY] → Game State
```

---

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `src/core/logic/card_db.rs` | ~2200 | Card database loading & enrichment | **TOO LONG** - Needs split |
| `src/core/logic/models.rs` | ~1800 | Core data structures (Ability, AbilityFrame) | OK |
| `src/core/logic/interpreter/mod.rs` | ~760 | Main interpreter loop | OK |
| `src/core/logic/interpreter/handlers/*.rs` | ~2000 | 20+ handler modules | **FRAGMENTED** - Consolidate |
| `src/core/logic/interpreter/costs.rs` | ~150 | Cost resolution | OK |
| `src/core/logic/interpreter/conditions/*.rs` | ~400 | Condition checking | OK |
| `src/core/logic/interpreter/logging.rs` | ~580 | Frame descriptions | **DEBUG ONLY** - Move to tool |
| `src/core/logic/ability_manifest.rs` | ~744 | Human-readable manifest generation | **BUILD TIME** - Move to tool |
| `src/core/logic/ability_patterns.rs` | ~227 | Pattern matching for abilities | OK |
| `src/core/logic/handlers.rs` | ~1648 | Game phase handlers | OK |
| `src/core/logic/filter.rs` | ~800 | CardFilter logic | OK |
| `src/core/logic/effects.rs` | ~26 | **SIMPLIFIED** - Was 762 lines | ✅ DONE |
| `src/core/logic/action_gen/*.rs` | ~1000 | Action generation | OK |

### Data Files (JSON)

| File | Size | Purpose | Status |
|------|------|---------|--------|
| `data/consolidated_abilities.json` | 1MB+ | Main card database | **TOO LARGE** - Contains computed fields |
| `data/metadata.json` | Small | Opcode/trigger mappings | OK |
| `data/cards_compiled.json` | Medium | Compiled cache | **REDUNDANT** - Multiple versions |
| `data/ability_frame_index.json` | Small | Frame index | **QUESTIONABLE** - Should be generated |

## Critical Issues

### 1. PARALLEL REPRESENTATIONS (Major Problem)

The `Ability` struct has **FOUR** ways to represent the same thing:

```rust
pub struct Ability {
    // BYTECODE (Source of Truth)
    pub frame_program: Option<FrameProgram>,  // Actual executable bytecode
    
    // SEMANTIC (Largely Unused - SHOULD REMOVE)
    pub effects: Vec<Effect>,           // Was 70+ variants, now stubbed
    pub conditions: Vec<Condition>,   // Partially used
    pub costs: Vec<Cost>,               // Barely used
    
    // COMPUTED AT RUNTIME (Should be in JSON)
    pub choice_flags: u8,              // Derived from frame_program
    pub choice_count: u8,              // Derived from frame_program  
    pub requires_selection: bool,      // Derived from frame_program
    pub ability_flags: u64,            // Derived from frame_program
}
```

**Recommendation**: 
- Remove `effects` field completely
- Precompute `choice_flags`, `choice_count`, `ability_flags` into JSON
- Keep only `frame_program` as single source of truth

### 2. RUNTIME PATCHING (card_db.rs:1740-1800)

Hardcoded workarounds for specific cards:

```rust
fn inject_missing_ability_conditions() {
    // Patch for "Tiny Stars" live card
    // Injects Kanon + Keke requirements
    
    // Patch for "Strawberry Trapper"
    // Injects NotHasExcessHeart condition
    
    // Patch for "PL!-N-bp1-006-P"
    // Clears conditions and replaces with CostCompare
    
    // Patch for "PL!-bp5-003-P"
    // Injects UNIQUE_NAMES_COUNT condition
}
```

**Problem**: Engine knows about specific cards. Data should be fixed in JSON.

**Recommendation**: Fix `consolidated_abilities.json` and remove these patches.

### 3. RUNTIME DERIVATION (card_db.rs:1200-1400)

```rust
fn enrich_member_runtime_metadata(card: &mut MemberCard) {
    // Scans frame_program to derive:
    // - choice_flags
    // - choice_count  
    // - requires_selection
    // - ability_flags
    // - ability_opcodes_mask
}
```

**Problem**: ~400 lines of scanning bytecode at load time. Should be precomputed.

**Recommendation**: Add these fields to `consolidated_abilities.json` during data pipeline.

### 4. FRAGMENTED HANDLERS (interpreter/handlers/)

20+ files for opcode handlers, many <50 lines:

```
handlers/
├── mod.rs              (registry)
├── flow.rs             (control flow)
├── flow_helpers.rs     (utilities)
├── flow_context.rs     (context ops)
├── flow_effects.rs     (effect ops)
├── select_mode.rs      (modal selection)
├── state_energy.rs
├── state_energy_charge.rs
├── state_member.rs
├── state_score_hearts.rs
├── movement_draw.rs
├── movement_discard.rs
├── movement_deck.rs
├── movement_swap_zone.rs
├── choice_prompt.rs
└── ... (more)
```

**Recommendation**: Consolidate into:
- `control.rs` (flow + context)
- `state.rs` (all state ops)
- `movement.rs` (all movement ops)
- `selection.rs` (prompts + choices)

### 5. DEBUG CODE IN RUNTIME (interpreter/logging.rs:580 lines)

Human-readable opcode descriptions:

```rust
fn describe_frame(metadata: &Value, frame: &Value) -> String {
    match op.as_str() {
        "DRAW" => format!("Draw {} card(s).", value),
        "RECOVER_MEMBER" => format!("Recover {} member(s)...", value),
        // ... 50+ more opcodes
    }
}
```

**Problem**: 580 lines of debug-only code in runtime path.

**Recommendation**: Move to separate `ability_debug_tool` or `ability_manifest` crate.

## Simplification Roadmap

### Phase 1: Data Cleanup (High Priority)

1. **Fix `consolidated_abilities.json`**
   - Add precomputed `choice_flags`, `choice_count`, `requires_selection`, `ability_flags`
   - Fix card data so no hardcoded patches needed
   - Remove unused `effects` arrays

2. **Simplify `card_db.rs`**
   - Remove `inject_missing_ability_conditions()` (~300 lines)
   - Remove `enrich_member_runtime_metadata()` derivation (~400 lines)
   - Just load JSON directly without runtime computation

### Phase 2: Code Consolidation (Medium Priority)

1. **Consolidate handlers**
   - Merge 20+ files into 4-5 logical modules
   - Target: ~500 lines total instead of ~2000

2. **Move debug code**
   - Move `logging.rs` to separate debug tool
   - Move `ability_manifest.rs` to build-time tool

### Phase 3: Remove Dead Code (Medium Priority)

1. **Remove unused fields from `Ability`**
   - `effects: Vec<Effect>` - Already stubbed, remove field entirely
   - `conditions: Vec<Condition>` - Verify usage, possibly remove
   - `costs: Vec<Cost>` - Verify usage, possibly remove

2. **Clean up JSON**
   - Remove multiple versions of `cards_compiled*.json`
   - Keep only `consolidated_abilities.json` as source

## Data Flow Correct Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE (Pre-compute)                   │
│  Input: Raw card definitions + ability text                       │
│  Output: consolidated_abilities.json with ALL computed fields     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ENGINE (Load & Execute)                       │
│  1. Load JSON directly into CardDatabase (no derivation)         │
│  2. Execute abilities via frame_program bytecode                 │
│  3. Use precomputed flags for quick checks                     │
└─────────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Single Source of Truth**: Only `frame_program` should contain ability logic
2. **Precompute, Don't Derive**: All metadata should be in JSON, not computed at load
3. **Data Fixes, Not Code Patches**: Fix broken cards in JSON, not in code
4. **Debug Tools Separate**: Logging/manifest generation should be separate from runtime
5. **Minimal Runtime**: Engine should load and execute, not analyze bytecode

## Files to Modify (Priority Order)

1. **`data/consolidated_abilities.json`** - Add precomputed fields
2. **`src/core/logic/card_db.rs`** - Remove patches and derivation
3. **`src/core/logic/models.rs`** - Remove unused `effects` field
4. **`src/core/logic/interpreter/handlers/`** - Consolidate modules
5. **`src/core/logic/interpreter/logging.rs`** - Move to debug tool
6. **`src/core/logic/ability_manifest.rs`** - Move to build tool

## Current Status (As of Last Simplification)

- ✅ Removed `Effect` enum (762 → 26 lines)
- ✅ Removed `direct_executor.rs` wrapper (52 → 5 lines)
- ✅ Removed `raw_*` wrapper methods from `AbilityFrame`
- ✅ Removed `derive_choice_metadata_from_semantic` dead code
- ✅ Removed `effect_type_to_opcode` / `cost_type_to_opcode` dead code
- ⏳ Need to remove hardcoded card patches
- ⏳ Need to precompute metadata in JSON
- ⏳ Need to consolidate handler modules
- ⏳ Need to move debug code to separate tools
