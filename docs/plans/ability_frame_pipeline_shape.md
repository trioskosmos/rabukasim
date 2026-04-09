# Ability Frame Pipeline Shape

This note describes the current end-to-end ability pipeline after the collapse to a single normalization pass.

## End-to-end flow

The live path is:

1. `data/ability_frame_source.json` is loaded through `tools/frame_codec.py`.
2. `normalize_authored_ability_index(...)` produces one normalized payload.
3. `tools/abilities/pipeline.py` projects that normalized payload into two views:
   - `data/ability_frame_source.json` as the compact authored view
   - `data/ability_runtime_index.json` as a thin runtime-marked mirror
4. Rust loads `data/cards_compiled.json` as the primary runtime card payload in `engine_rust_src/src/core/logic/card_db.rs`.
5. A compatibility-only sparse index is now derived from the compiled cards instead of reopening the authored sparse source.

The important change is that the pipeline no longer normalizes twice and then strips duplicates. It normalizes once, then clones into view-specific shapes.

## Shape layers

### 1. Authored payload input

`load_authored_payload(...)` accepts either JSON or legacy YAML, and `iter_authored_entries(...)` accepts either:

- a list under `abilities`
- a legacy object map of entries

This is the only place where multiple authoring shapes are still tolerated.

### 2. Normalized ability index

`normalize_authored_ability_index(...)` is the canonical in-memory shape.

Top-level keys:

- `generated_at`
- `source`
- `metadata_source`
- `schema`
- `_comment`
- `summary`
- `opcode_catalog`
- `abilities`

Each ability entry always has:

- `primary_text_jp`
- `primary_text_en`
- `source_ability_texts`
- `trigger_id`
- `trigger`
- `frame_count`
- `opcode_sequence`
- `frames`
- `cards`
- `card_refs`
- `pseudocode`

The older hash fields and generated signature keys are treated as internal generator bookkeeping. They should not be considered part of the human-edited authored contract, and they should not be the first thing someone has to scan when editing the file.

Optional authored metadata is preserved when present:

- `choice_flags`
- `choice_count`
- `is_once_per_turn`
- `requires_selection`

### 3. Compact authored view

`_apply_compact_view(...)` changes the normalized payload into the compact source artifact.

Top-level changes:

- `schema` becomes `ability_frame_source.flat.v2`
- `_comment` becomes `Authored sparse ability source. Edit this file directly.`

Per-entry changes:

- `source_mode` is set to `frame_authored`
- the normalized `frames` list is kept as-is

This means the compact source is not a different model. It is the normalized model with a source-specific schema and marker.

### 4. Runtime view

`_apply_runtime_view(...)` changes the normalized payload into the runtime artifact.

Top-level changes:

- `schema` becomes `ability_runtime_index.flat.v2`
- `_comment` becomes `Generated runtime ability index. Edit data/ability_frame_source.json directly.`

Per-entry changes:

- `frames` are cloned as-is from the normalized source
- no extra engine-visible frame data is added
- the view exists mainly as a separate file shape and schema marker

The runtime view does not change the ability ordering, signatures, counts, or frame payloads. It is now only a thin mirror over the normalized source.

## Frame shape change

The most visible change is inside each frame.

### Compact source frame

```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "AQOURS"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  }
}
```

### Runtime mirror frame

```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "AQOURS"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  }
}
```

So the runtime shape is effectively the compact shape with a different schema/comment wrapper.

## What is no longer happening

The old path did this:

1. normalize authored abilities
2. build a compact source payload
3. normalize again from that compact payload
4. strip duplicate instruction entries

That created extra churn without changing the final data meaning.

The current path is:

1. normalize once
2. clone into compact and runtime views
3. write those views directly

## Why this is simpler

The simplification is structural rather than cosmetic:

- one normalization pass means one source of truth for signatures, counts, and card refs
- view builders are pure projections instead of second-pass transformers
- the runtime file now differs from the source file only by schema/comment wrapping, not by a separate normalization pipeline
- runtime card loading now comes from `cards_compiled.json`, with only a compatibility index derived from the parsed cards

## Current files

- `tools/abilities/pipeline.py`
- `tools/frame_codec.py`
- `data/ability_frame_source.json`
- `data/ability_runtime_index.json`
- `engine_rust_src/src/core/logic/card_db.rs`
