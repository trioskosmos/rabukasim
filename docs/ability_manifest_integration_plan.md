# Ability Manifest Integration Plan

## Goal

Replace ad hoc ability interpretation with one normalized ability manifest that can be:

- generated from the compiled card database,
- serialized and checked into the repo when desired,
- consumed by tests,
- used by debugging and inspection tools,
- and eventually used by runtime code paths that currently re-derive intent from raw opcodes.

The core idea is simple:

- raw card data remains the source of truth,
- the manifest becomes the canonical normalized view,
- runtime code should stop re-inventing that view in multiple places.

## Current State

The repo already has:

- `data/cards_compiled.json`
- `data/metadata.json`
- `data/ability_frames.json`
- `data/ability_frame_index.json`
- multiple analysis and verification scripts
- a working Rust manifest generator at `src/bin/generate_ability_manifest.rs`
- generated output at:
  - `reports/ability_manifest.json`
  - `reports/ability_manifest.md`

The current manifest is useful, but it is still a report artifact. It is not yet integrated as a first-class pipeline input for tests, serialization, or runtime behavior.

## Target Shape

The final system should look like this:

1. Card DB loads compiled cards.
2. Ability manifest generator normalizes every ability into a stable schema.
3. The manifest is serialized to JSON and optionally Markdown.
4. Tests validate that manifest entries match compiled abilities, opcode sequences, and expected summaries.
5. Runtime code can read the manifest for diagnostics or fallback semantics.
6. Serialization of `Ability`, `FrameProgram`, and `AbilityFrame` remains round-trippable.

## Proposed Schema

### Top Level

```json
{
  "generated_at": "...",
  "source_cards": ".../data/cards_compiled.json",
  "source_metadata": ".../data/metadata.json",
  "schema": "ability_manifest.v1",
  "summary": {
    "card_count": 0,
    "ability_count": 0,
    "trigger_counts": {},
    "flow_counts": {},
    "opcode_counts": {}
  },
  "cards": []
}
```

### Card Entry

Each card entry should contain:

- `card_id`
- `card_no`
- `name`
- `db`
- `ability_count`
- `source_text`
- `source_text_en`
- `abilities`

### Ability Entry

Each normalized ability should contain:

- `ability_index`
- `trigger_id`
- `trigger`
- `flow_pattern`
- `summary`
- `frame_count`
- `opcode_sequence`
- `source_text`
- `source_text_en`
- `frames`
- `choice_flags`
- `choice_count`
- `requires_selection`
- `is_once_per_turn`
- `card_no`
- `card_id`
- `name`
- `db`

### Frame Entry

Each normalized frame should contain:

- `index`
- `opcode_id`
- `opcode`
- `role`
- `summary`
- `optional`
- `negated`
- `value` when present
- `attr` when present
- `slot` when present
- `decoded` when available

## Integration Steps

### 1. Keep the generator as the canonical builder

The Rust bin in:

- `src/bin/generate_ability_manifest.rs`

should remain the central generator. It should be the only place that builds the full manifest from compiled cards and metadata.

### 2. Add explicit schema versioning

The manifest must keep a version string such as:

- `ability_manifest.v1`

If the shape changes, bump the version and preserve compatibility helpers where practical.

### 3. Serialize the manifest deterministically

JSON output should be deterministic:

- stable card ordering
- stable ability ordering
- stable frame ordering
- stable summary ordering

This makes diffing, testing, and review much easier.

### 4. Add round-trip serialization tests

Add tests that verify:

- the manifest serializes without loss for the fields we care about,
- `AbilityFrame` can be serialized and deserialized,
- `FrameProgram` still round-trips,
- `Ability` preserves frame program data and trigger metadata,
- a generated manifest for a known card matches the expected normalized shape.

### 5. Add snapshot-style manifest tests

Add tests for representative cards:

- a simple linear ability,
- an optional branch ability,
- a prompt-driven ability,
- a multi-ability card like `LL-bp1-001-R+`,
- a card with jump/branch control flow,
- a card with a selection prompt and follow-up effect.

The tests should assert:

- trigger name,
- frame count,
- opcode sequence,
- flow pattern,
- normalized summary,
- basic frame role classification.

### 6. Add coverage tests for the manifest generator

The generator should have tests that ensure:

- every ability in `cards_compiled.json` appears in the manifest,
- ability counts match between source and output,
- no ability is silently dropped,
- no frame list is empty unless the source ability is truly empty,
- trigger counts and opcode counts are non-zero for known sample sets.

### 7. Integrate with existing verification tooling

The new manifest should be consumable by existing scripts:

- card verification tools
- semantic audit tools
- opcode coverage reports
- debugging scripts

At minimum, tools should be able to:

- read the JSON manifest,
- look up a card by `card_no` or `card_id`,
- inspect the normalized frame summaries,
- and print a human-friendly ability digest.

### 8. Use the manifest in diagnostics before runtime adoption

Before runtime code depends on it, the manifest should be used for:

- debugging output,
- regression checks,
- semantic review,
- generated documentation.

This lets us prove the representation is stable before changing execution behavior.

### 9. Add runtime fallback wiring only after tests pass

If runtime adoption is needed later:

- prefer fallback reads from the manifest for inspection,
- do not replace execution semantics blindly,
- keep the existing interpreter as the authoritative executor until the manifest has proven equivalent.

## Serialization Plan

### Rust serialization

Keep the existing data structures serializable:

- `Ability`
- `AbilityFrame`
- `FrameProgram`
- `CardDatabase`

The manifest should be emitted with `serde_json`.

### Determinism requirements

Serialization should keep:

- stable field order in generated JSON where possible,
- stable ordering in arrays,
- no hidden nondeterministic iteration over hash maps,
- consistent formatting in Markdown output.

### Suggested file placement

- Generator: `engine_rust_src/src/bin/generate_ability_manifest.rs`
- JSON output: `reports/ability_manifest.json`
- Markdown output: `reports/ability_manifest.md`
- Integration plan: `docs/ability_manifest_integration_plan.md`

## Test Plan

### Serialization tests

Add tests that verify:

- `serde_json::to_value` and `from_value` on manifest entries works,
- `AbilityFrame` round-trips,
- `Ability` round-trips with `frame_program`,
- `FrameProgram` round-trips with the known frame set from compiled cards.

### Manifest generator tests

Add tests that verify:

- generator output includes `LL-bp1-001-R+`,
- its two abilities are present,
- the first ability is recognized as recovery,
- the second ability is recognized as optional cost + reward,
- all cards with abilities appear in the manifest summary.

### Regression tests

Add tests that guard against:

- missing trigger labels,
- missing frame role labels,
- empty summaries on non-empty abilities,
- dropped optional flags,
- corrupted opcode sequences.

### Coverage tests

Add checks for:

- card count coverage,
- ability count coverage,
- frame count coverage,
- representative opcode coverage,
- representative trigger coverage.

## Rollout Phases

### Phase 1

- Keep the generator and reports.
- Add manifest tests.
- Add serialization tests.
- Keep runtime untouched.

### Phase 2

- Update inspection and verification tooling to read the manifest directly.
- Prefer manifest summaries in debug reports.

### Phase 3

- Introduce optional runtime accessors that expose normalized manifest data.
- Keep execution logic separate from manifest lookup.

### Phase 4

- Remove redundant analysis paths once manifest consumers are stable.
- Keep the manifest generator as the canonical normalization step.

## Non-Goals

This plan does not try to:

- rewrite card text,
- change game rules,
- alter opcode execution semantics,
- add card-specific test cheats,
- or replace the interpreter with a completely new engine in one step.

## Acceptance Criteria

The integration is good when all of the following are true:

- every ability in `cards_compiled.json` appears in the manifest,
- the manifest is generated deterministically,
- serialization tests pass,
- representative ability snapshots pass,
- the manifest is readable by tooling,
- and runtime code no longer needs to infer the same ability meaning in multiple places.

