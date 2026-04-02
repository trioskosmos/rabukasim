# Bytecode And Bitpacking Migration Plan

## Purpose

This document explains where metadata-driven bitpacking and bytecode-shaped data are still active in the repository, what the minimum acceptable cleanup looks like, and what the preferred end state should be.

The user goal behind this plan is not just to remove one ugly helper. The real problem is broader:

1. Structured authored frames already exist.
2. Runtime execution is mostly frame-first.
3. But many layers still collapse structured data back into packed integers.
4. That keeps `data/metadata.json` bit layout details alive far beyond the legacy compatibility surface.

This document therefore separates two targets:

## Migration Targets

### Minimum acceptable target

Stop forcing every potentially-needed bit to be reserved in `metadata.json`.

That means:

- new runtime behavior must not require adding new bit positions to `bytecode_layout`
- runtime code must stop depending on generated bit-layout constants outside explicit compatibility modules
- packers and unpackers become legacy adapters, not primary infrastructure

### Preferred target

Remove bitmapped runtime frame storage entirely.

That means:

- authored frames remain structured from authored YAML to runtime execution
- Rust `AbilityFrame` stores typed fields directly instead of packed `value`, `attr`, and `slot`
- raw words remain only for import, audit, and a narrow regression suite

## Executive Summary

The repo is already in a mixed frame-first state.

The good news:

- authored frame data exists in `data/ability_frame_index.yaml`
- compact frame-oriented tooling exists in `tools/frame_codec.py`
- Python compile code already prefers semantic/frame-authored data over active bytecode generation
- Rust runtime execution primarily consumes `FrameProgram.frames`

The bad news:

- `tools/sync_metadata.py` still turns `data/metadata.json` bit layout into generated runtime helpers
- Rust still parses structured frame JSON and repacks it into packed integer fields
- filter, slot, and special value semantics are still threaded through many modules as packed numbers
- the Python fallback runtime still has a raw bytecode execution path
- tests, debug serializers, and ML encoding still assume a packed 5-word or bytecode-shaped representation

So the real work is not deleting one file. It is moving the runtime boundary so that bitpacking becomes a quarantined compatibility layer.

## Authoritative Data Versus Legacy Data

### Authored and modern

- `data/ability_frame_index.yaml`
- `tools/frame_codec.py`
- `engine/compiler/main.py`
- `engine_rust_src/src/core/logic/card_db.rs`
- `engine_rust_src/src/core/logic/interpreter/`

### Legacy and compatibility

- `data/metadata.json` `bytecode_layout`
- `tools/sync_metadata.py` generated packer/layout output
- `engine/models/generated_packer.py`
- `tools/archive/bytecode_codec.py`
- `FrameProgram::from_words()` and `to_words()`
- Python raw-bytecode execution helpers

## Current Use Map

This section lists the active surfaces where bitpacking still matters.

### 1. Metadata-driven layout generation

Current source:

- `data/metadata.json`
- `tools/sync_metadata.py`

Current reality:

- `bytecode_layout` is still read and converted into both Python packers and Rust bit-layout constants.
- extra constants are still derived from bit positions instead of being treated as independent runtime semantics.

Current code:

```python
# tools/sync_metadata.py
packed_layout = metadata.get("packed_layout") or metadata.get("bytecode_layout", {})
layout_fields = packed_layout.get("A", {}).get("standard", {})

shift_mappings = {
    "FILTER_TYPE_SHIFT": "card_type",
    "FILTER_GROUP_SHIFT": "group_id",
    "FILTER_UNIT_SHIFT": "unit_id",
    "FILTER_COST_SHIFT": "value_threshold",
    "FILTER_COLOR_SHIFT": "color_mask",
    "FILTER_SPECIAL_SHIFT": "special_id",
    "FILTER_ZONE_MASK_SHIFT": "zone_mask",
}
```

Current code:

```python
# tools/sync_metadata.py
layout = metadata.get("packed_layout") or metadata.get("bytecode_layout")
if layout:
    py_packer_path = "engine/models/generated_packer.py"
    rust_layout_path = "engine_rust_src/src/core/generated_layout.rs"
```

Why this is a problem:

- runtime semantics and legacy encoding are still coupled
- adding or changing runtime fields still pressures the bit layout
- generated layout constants leak into active runtime code

Target at minimum:

```python
# tools/sync_metadata.py
runtime_metadata = {
    "opcodes": metadata["opcodes"],
    "triggers": metadata["triggers"],
    "conditions": metadata["conditions"],
    "costs": metadata["costs"],
    "choices": metadata["choices"],
    "zones": metadata["zones"],
}

legacy_layout = metadata.get("legacy_bytecode_layout")
if legacy_mode and legacy_layout:
    generate_legacy_packers(legacy_layout)
```

Preferred target:

```python
# tools/sync_metadata.py
generate_runtime_constants_from_enums_only(metadata)

if build_legacy_codec:
    generate_legacy_codec_support(metadata.get("legacy_bytecode_layout", {}))
```

### 2. Generated Python bit packers

Current source:

- `engine/models/generated_packer.py`

Current code:

```python
def pack_v_look_choose(**kwargs) -> int:
    value = 0
    value = _set_bits(value, 0, 0xFF, kwargs.get("count", 0))
    value = _set_bits(value, 8, 0x7F, kwargs.get("char_id_2", 0))
    value = _set_bits(value, 16, 0x7F, kwargs.get("char_id_1", 0))
    value = _set_bits(value, 23, 0x7F, kwargs.get("char_id_3", 0))
    value = _set_bits(value, 30, 0x1, kwargs.get("reveal", 0))
    value = _set_bits(value, 31, 0x1, kwargs.get("dest_discard", 0))
    return value
```

Why this is a problem:

- human-readable authored fields are immediately flattened
- this encoding leaks into tests and archive codec logic
- it makes LOOK_AND_CHOOSE look simpler than it is while hiding field structure in bit ranges

Minimum target:

```python
# legacy only
def pack_v_look_choose_legacy(data: dict[str, int | bool]) -> int:
    ...
```

Preferred target:

```python
@dataclass
class LookAndChooseValue:
    count: int
    choose_count: int = 0
    char_id_1: int = 0
    char_id_2: int = 0
    char_id_3: int = 0
    reveal: bool = False
    dest_discard: bool = False
```

### 3. Rust runtime frame storage still uses packed fields

Current source:

- `engine_rust_src/src/core/logic/models.rs`

Current code:

```rust
pub struct AbilityFrame {
    pub opcode: i32,
    pub value: i32,
    pub attr: u64,
    pub slot: i32,
    pub is_cost: bool,
    pub params: Value,
}
```

Why this is the main architectural bottleneck:

- even structured frames become packed at load time
- every handler has to decode or reinterpret packed pieces
- special cases like LOOK_AND_CHOOSE require repacking during parsing and hydration

Current code path for structured JSON becoming packed runtime fields:

```rust
let packed = crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
    count: lac_count,
    choose_count: lac_choose,
    reveal: lac_reveal,
    dest_discard: lac_dest,
    char_id_1: lac_c1,
    char_id_2: lac_c2,
    char_id_3: lac_c3,
}.to_raw();
Self::with_components(O_LOOK_AND_CHOOSE, packed, filter, slot, is_cost, Value::Null)
```

Minimum target:

```rust
pub struct AbilityFrame {
    pub opcode: i32,
    pub value: i32,
    pub filter: CardFilter,
    pub slot: DecodedSlot,
    pub is_cost: bool,
    pub params: Value,
    pub legacy_attr: Option<u64>,
    pub legacy_slot: Option<i32>,
}
```

Preferred target:

```rust
pub struct AbilityFrame {
    pub opcode: i32,
    pub value: FrameValue,
    pub filter: CardFilter,
    pub slot: DecodedSlot,
    pub is_cost: bool,
    pub params: Value,
}

pub enum FrameValue {
    Scalar(i32),
    LookAndChoose(LookAndChooseValue),
    HeartCounts(HeartCountsValue),
    HeartCost(HeartCostValue),
    ScalarDynamic { base_value: i32, divisor: i32 },
}
```

### 4. Structured frame parsing still repacks on load

Current source:

- `engine_rust_src/src/core/logic/models.rs`

Current code:

```rust
pub(crate) fn from_json_value(frame: &Value) -> Self {
    ...
    let mut filter = CardFilter::from_frame_json(payload, &options, &params);
    let slot = slot_value
        .clone()
        .and_then(|value| serde_json::from_value::<DecodedSlot>(value).ok())
        .unwrap_or_default();
    ...
    Self::with_components(raw_op, value, filter, slot, is_cost, params)
}
```

Current problem:

- parser accepts structured `DecodedSlot`
- parser accepts structured filter information
- parser still funnels everything into `with_components`, which packs them

Minimum target:

```rust
pub(crate) fn from_json_value(frame: &Value) -> Self {
    let filter = CardFilter::from_frame_json(payload, &options, &params);
    let slot = parse_structured_slot(slot_value);

    Self {
        opcode: raw_op,
        value: value,
        filter,
        slot,
        is_cost,
        params,
        legacy_attr: None,
        legacy_slot: None,
    }
}
```

Preferred target:

```rust
pub(crate) fn from_json_value(frame: &Value) -> Self {
    let filter = CardFilter::from_frame_json(payload, &options, &params);
    let slot = parse_structured_slot(slot_value);
    let value = FrameValue::from_frame_json(opcode, payload, &params);

    Self { opcode, value, filter, slot, is_cost, params }
}
```

### 5. Raw word conversion is still treated as normal runtime API

Current source:

- `engine_rust_src/src/core/logic/models.rs`
- `engine_rust_src/src/core/logic/state.rs`

Current code:

```rust
pub fn from_words(words: &[i32]) -> Self {
    let mut frames = Vec::with_capacity(words.len() / WORDS_PER_INSTRUCTION);
    let mut ip = 0;
    while ip < words.len() {
        let instr = BytecodeInstruction::decode(words, ip);
        frames.push(AbilityFrame::from_instruction(&instr));
        ip += WORDS_PER_INSTRUCTION;
    }
    Self { frames, raw_program: Some(serde_json::json!({ "instructions": [], "bytecode": words })) }
}
```

Current code:

```rust
pub fn resolve_frames<B: AsRef<[i32]>>(
    &mut self,
    db: &CardDatabase,
    words: B,
    ctx_in: &AbilityContext,
) {
    let frame_program = FrameProgram::from_words(words.as_ref());
    ...
}
```

Why this is a problem:

- raw words are still presented as a first-class input to active runtime methods
- tests and helpers keep using word arrays instead of structured frames
- deprecation exists in comments but not yet in architecture

Minimum target:

```rust
pub fn resolve_frame_program(
    &mut self,
    db: &CardDatabase,
    program: &FrameProgram,
    ctx_in: &AbilityContext,
) {
    resolve_semantic_frames(self, db, &program.frames, ctx_in)
}

pub fn resolve_legacy_words(
    &mut self,
    db: &CardDatabase,
    words: &[i32],
    ctx_in: &AbilityContext,
) {
    let program = LegacyWordCodec::decode(words);
    self.resolve_frame_program(db, &program, ctx_in);
}
```

Preferred target:

- `resolve_frames` takes `&[AbilityFrame]` or `&FrameProgram`
- all word-based entrypoints move to `legacy_codec` or test helpers

### 6. Filter semantics still depend on attr bit layout

Current sources:

- `engine_rust_src/src/core/logic/filter.rs`
- `engine_rust_src/src/core/logic/filter_attr_compat.rs`
- `engine_rust_src/src/core/logic/constants.rs`

Current code:

```rust
//! BIT LAYOUT (synchronized with Python _pack_filter_attr, Revision 5):
//! Bits 0-1:   Target Player
//! Bits 2-3:   Card Type
//! Bit 4:      Group Enable flag
//! ...
```

Current code:

```rust
pub fn to_attr_computed(&self) -> u64 {
    let mut attr: u64 = 0;
    attr |= self.target_player as u64;
    attr |= (self.card_type as u64) << 2;
    ...
    if self.is_optional { attr |= 1 << 61; }
    if self.keyword_energy { attr |= 1 << 62; }
    if self.keyword_member { attr |= 1 << 63; }
    attr
}
```

Current code:

```rust
pub const FILTER_TARGET_SHIFT: u64 =
    crate::core::generated_layout::A_STANDARD_TARGET_PLAYER_SHIFT as u64;
```

Why this is a problem:

- filter semantics are still described in terms of bits, not fields
- constants layer still exposes layout shifts as if they were runtime API
- many handlers still bounce through `to_attr()` and `from_attr()`

Minimum target:

```rust
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct CardFilter {
    pub target_player: TargetPlayer,
    pub card_type: Option<CardType>,
    pub group: Option<GroupId>,
    pub unit: Option<UnitId>,
    pub value_gate: Option<ValueGate>,
    pub color_mask: ColorMask,
    pub characters: [Option<CharacterId>; 3],
    pub zone_mask: ZoneMask,
    pub special: Option<SpecialFilter>,
    pub flags: FilterFlags,
}
```

Preferred target:

```rust
impl CardFilter {
    pub fn matches(&self, state: &GameState, db: &CardDatabase, cid: i32, ctx: &AbilityContext) -> bool {
        // pure field logic, no attr packing
    }
}

pub mod legacy_attr_codec {
    pub fn encode(filter: &CardFilter) -> u64 { ... }
    pub fn decode(attr: u64) -> CardFilter { ... }
}
```

### 7. Slot semantics still depend on a packed integer

Current source:

- `engine_rust_src/src/core/logic/interpreter/instruction.rs`

Current code:

```rust
pub fn decode(raw_s: i32) -> Self {
    let s = raw_s as u32;
    Self {
        target_slot: ((s >> S_STANDARD_TARGET_SLOT_SHIFT) & S_STANDARD_TARGET_SLOT_MASK as u32) as u8,
        comparison: ((s >> 4) & 0x0F) as u8,
        remainder_zone: ((s >> S_STANDARD_REMAINDER_ZONE_SHIFT)
            & S_STANDARD_REMAINDER_ZONE_MASK as u32) as u8,
        ...
    }
}
```

Current code:

```rust
pub fn to_raw(&self) -> i32 {
    let mut s = 0u32;
    s |= (self.target_slot as u32 & S_STANDARD_TARGET_SLOT_MASK as u32)
        << S_STANDARD_TARGET_SLOT_SHIFT;
    ...
    s as i32
}
```

Minimum target:

- keep `DecodedSlot` as the active runtime type
- move `to_raw()` and `decode()` into a legacy slot codec module

Preferred target:

```rust
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct DecodedSlot {
    pub target_slot: SlotTarget,
    pub comparison: Option<Comparison>,
    pub source_zone: Option<Zone>,
    pub dest_zone: Option<Zone>,
    pub remainder_zone: Option<Zone>,
    pub is_opponent: bool,
    pub is_reveal_until_live: bool,
    pub is_baton_slot: bool,
    pub is_empty_slot: bool,
    pub is_wait: bool,
    pub is_dynamic: bool,
    pub area_idx: Option<u8>,
}
```

### 8. Special packed values still exist for LOOK_AND_CHOOSE, heart counts, heart cost, and scalar dynamic

Current source:

- `engine_rust_src/src/core/logic/interpreter/instruction.rs`

Current code:

```rust
impl DecodedLookAndChoose {
    pub fn decode(v: i32) -> Self {
        let uv = v as u32;
        Self {
            count: ((uv >> V_LOOK_CHOOSE_COUNT_SHIFT) & V_LOOK_CHOOSE_COUNT_MASK) as u8,
            choose_count: 0,
            char_id_1: ((uv >> V_LOOK_CHOOSE_CHAR_ID_1_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_1_MASK) as u8,
            ...
        }
    }

    pub fn to_raw(&self) -> i32 {
        let mut v = 0u32;
        ...
        v as i32
    }
}
```

This is a concrete example of the current mismatch:

- authored data already has named fields
- runtime decode helper still assumes packed integer storage
- `choose_count` is not truly represented in raw bits and therefore needs side-channel handling

Minimum target:

```rust
pub struct LookAndChooseValue {
    pub count: u8,
    pub choose_count: u8,
    pub char_id_1: u8,
    pub char_id_2: u8,
    pub char_id_3: u8,
    pub reveal: bool,
    pub dest_discard: bool,
}

pub mod legacy_look_choose_codec {
    pub fn encode(value: &LookAndChooseValue) -> i32 { ... }
    pub fn decode(raw: i32) -> LookAndChooseValue { ... }
}
```

Preferred target:

- store `LookAndChooseValue` directly in `FrameValue::LookAndChoose`
- do not flatten it during normal runtime load

### 9. Card hydration still mutates frames by repacking fields

Current source:

- `engine_rust_src/src/core/logic/card_db.rs`

Current code:

```rust
if let Some(program) = ability.frame_program.as_mut() {
    if let Some(frame) = program.frames.iter_mut().find(|f| f.opcode == O_LOOK_AND_CHOOSE) {
        let mut lac = frame.look_choose();
        if lac.choose_count == 0 {
            lac.choose_count = choose_count;
            frame.value = lac.to_raw();
        }
    }
}
```

Why this is a problem:

- card loading should not need to encode domain values back into packed integers
- it is compensating for missing fidelity in the runtime frame model

Minimum target:

```rust
if let Some(program) = ability.frame_program.as_mut() {
    if let Some(frame) = program.frames.iter_mut().find(|f| f.opcode == O_LOOK_AND_CHOOSE) {
        if let FrameValue::LookAndChoose(ref mut value) = frame.value {
            if value.choose_count == 0 {
                value.choose_count = choose_count;
            }
        }
    }
}
```

### 10. AlphaZero encoding still projects frames as raw words

Current source:

- `engine_rust_src/src/core/alphazero_encoding.rs`

Current code:

```rust
tensor.push(frame.opcode() as f32 / 255.0);
tensor.push(frame.value() as f32 / 255.0);
let a = frame.attr();
tensor.push((a as u32) as f32 / 255.0);
tensor.push((a >> 32) as u32 as f32 / 255.0);
tensor.push(frame.slot() as f32 / 255.0);
```

Why this matters:

- the ML layer is not bytecode-driven in authoring terms
- but its features still assume the runtime frame projection is a 5-word numeric block

Minimum target:

- keep this as `legacy_frame_projection_v1`
- version the encoding explicitly before changing it

Preferred target:

```rust
tensor.push(frame.opcode() as f32 / 255.0);
tensor.extend(encode_filter_features(&frame.filter));
tensor.extend(encode_slot_features(&frame.slot));
tensor.extend(encode_value_features(&frame.value));
```

### 11. Python compatibility runtime still executes raw segments

Current sources:

- `engine/game/mixins/effect_mixin.py`
- `engine/game/effects/pending_effect_resolution.py`
- `engine/game/effects/effect_opcode_resolution.py`
- `engine/game/effects/choice_resolution.py`

Current code:

```python
# engine/game/effects/pending_effect_resolution.py
if isinstance(resolving_effect, list):
    i = 0
    while i < len(resolving_effect):
        op = resolving_effect[i]
        ...
        self._resolve_effect_opcode(Opcode(base_op), resolving_effect[i : i + 4], context or {})
        i += 4
    return
```

Current code:

```python
# engine/game/effects/choice_resolution.py
bytecodes = params.get("options_bytecode")
if bytecodes and 0 <= opt < len(bytecodes):
    self.pending_effects.insert(0, bytecodes[opt])
    return
```

Why this is a problem:

- this is an independent legacy execution surface
- it keeps bytecode-like behavior alive even if Rust becomes clean
- it is not even aligned to the same word shape as the Rust 5-word layout

Minimum target:

- explicitly freeze this path as legacy-only
- stop feeding new structured functionality into it
- rename bytecode-specific fields to legacy names where needed

Preferred target:

```python
if isinstance(resolving_effect, StructuredResolvingEffect):
    resolve_structured_effect(self, resolving_effect, context)
elif isinstance(resolving_effect, LegacyWordEffect):
    resolve_legacy_word_effect(self, resolving_effect, context)
```

### 12. Archive codec and current tests still preserve the old round-trip contract

Current sources:

- `tools/archive/bytecode_codec.py`
- `backend/tests/test_consolidate_abilities.py`
- `backend/tests/test_frame_codec.py`

Current code:

```python
# backend/tests/test_consolidate_abilities.py
rebuilt = legacy_codec.model_to_bytecode({"frames": entry["instructions"]}, metadata)
```

Current code:

```python
# tools/archive/bytecode_codec.py
def model_to_bytecode(model: dict[str, Any], metadata: dict[str, Any] | None = None) -> list[int]:
    ...
```

Why this matters:

- this codec is still useful for audit and forensic comparison
- but it should stop being treated as an active build contract

Minimum target:

- move all legacy round-trip tests behind a clearly named legacy test group
- keep a small contract suite for archive tooling only

Preferred target:

```python
def model_to_legacy_words(model: dict[str, Any], metadata: dict[str, Any] | None = None) -> list[int]:
    ...
```

That naming makes the compatibility role explicit.

## What Should Be Preserved

The following parts are already close to the desired end state and should become the anchor for cleanup:

### Compact authored frame index

Current code:

```python
# tools/frame_codec.py
def _normalize_frame(frame: Any, idx: int) -> dict[str, Any]:
    if frame == "Return" or frame == {"Return": {}}:
        return {"op": "RETURN", "frame_index": idx}

    op = frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or frame.get("kind") or "NOP"
    normalized = {"op": str(op).upper(), "frame_index": idx}

    if isinstance(frame.get("options"), dict):
        normalized["options"] = frame["options"]

    for key in ("source_words", "value", "filter", "slot", "params", "choice_flags", "choice_count"):
        if key in frame:
            normalized[key] = frame[key]

    return normalized
```

Why this is good:

- opcode is explicit
- frame options remain readable
- authored structure is preserved
- this shape is far better than `value/attr/slot` packing for new work

Desired direction:

- this normalized instruction form should remain readable all the way into runtime load
- only legacy adapters should convert it to old packed forms

## Recommended End-State Runtime Shape

The clean destination is something close to this.

```rust
#[derive(Debug, Clone, PartialEq)]
pub struct FrameProgram {
    pub frames: Vec<AbilityFrame>,
    pub raw_program: Option<Value>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct AbilityFrame {
    pub opcode: i32,
    pub value: FrameValue,
    pub filter: CardFilter,
    pub slot: DecodedSlot,
    pub is_cost: bool,
    pub params: Value,
}

#[derive(Debug, Clone, PartialEq)]
pub enum FrameValue {
    None,
    Scalar(i32),
    LookAndChoose(LookAndChooseValue),
    HeartCounts(HeartCountsValue),
    HeartCost(HeartCostValue),
    ScalarDynamic { base_value: i32, divisor: i32 },
}
```

This shape makes the actual domain visible:

- filter is a filter
- slot is a slot
- look-and-choose is not an integer pretending to be a struct

## Concrete Phases

## Phase 1: Quarantine layout generation

Goal:

- stop runtime code from depending on `generated_layout` for new work

Changes:

1. Move `bytecode_layout` to `legacy_bytecode_layout` or equivalent.
2. Make `tools/sync_metadata.py` generate runtime constants from enum data only.
3. Generate packer and layout code only for explicit legacy mode.
4. Stop adding new runtime semantics by assigning bit positions.

Validation:

- build still succeeds
- archive codec still works when legacy mode is enabled
- no new runtime modules import `generated_layout`

## Phase 2: Change runtime frame storage

Goal:

- remove packed `attr` and `slot` as the authoritative internal representation

Changes:

1. Change `AbilityFrame` to hold `CardFilter` and `DecodedSlot` directly.
2. Keep optional legacy raw fields only if needed for transition.
3. Refactor `AbilityFrame::from_json_value()` so it no longer repacks.
4. Refactor `card_db.rs` hydration fixups to mutate typed values, not packed ints.

Validation:

- existing authored frame programs still load
- no behavior changes in current Rust tests
- a compatibility suite still confirms that structured-to-legacy projection can be produced when requested

## Phase 3: Replace packed special values with typed variants

Goal:

- stop using `i32 value` as a hidden union for unrelated concepts

Changes:

1. Introduce `FrameValue`.
2. Convert LOOK_AND_CHOOSE first.
3. Convert heart counts and heart requirements next.
4. Convert scalar dynamic values after that.

Validation:

- special handlers no longer decode bit ranges from runtime frame values
- LOOK_AND_CHOOSE no longer needs side-channel choose-count repair

## Phase 4: Remove raw-word entrypoints from active runtime API

Goal:

- treat words and bytecode as import formats, not runtime APIs

Changes:

1. Add `resolve_frame_program()` as the main execution entrypoint.
2. Move word decoding to `legacy_codec` or test helper boundaries.
3. Stop constructing most tests via `FrameProgram::from_words()`.

Validation:

- runtime game flow only uses structured frames
- old raw-word tests still pass inside a narrow compat suite

## Phase 5: Clean serializer, debug, and ML surfaces

Goal:

- remove bytecode language from active surfaces once the runtime is structured

Changes:

1. Remove `decoded_bytecode` from debug card serialization.
2. Rename `bytecode_log` to `frame_log` where practical.
3. Version AlphaZero frame encoding before changing its feature projection.
4. Freeze or explicitly legacy-label Python raw-bytecode execution helpers.

Validation:

- frontend still renders game state correctly
- debug tools still have a structured frame view
- existing checkpoints keep a stable encoding path until deliberately migrated

## Recommended Implementation Order

If the goal is the smallest useful change first:

1. Quarantine `bytecode_layout` and `generated_layout`.
2. Stop deriving runtime constants from bit positions.
3. Stop using `generated_layout` outside compatibility modules.

If the goal is the clean architectural finish:

1. Change `AbilityFrame` storage.
2. Refactor structured parsing so it does not repack.
3. Convert LOOK_AND_CHOOSE to a typed runtime value.
4. Move legacy word encode/decode to explicit compat modules.
5. Then clean serializer, tests, and AlphaZero projections.

## Bottom Line

The minimum fix is not "delete `look_choose` from metadata." That would be too shallow.

The real minimum fix is:

- new work must not require new layout bits
- runtime code must stop treating layout shifts and masks as core semantics

The preferred fix is:

- authored frames stay structured from source to execution
- bitpacking survives only as a narrow import/export compatibility layer

That is the difference between merely reducing metadata pain and actually removing the architectural reason the pain keeps coming back.