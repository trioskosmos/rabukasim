# Sunny Day Song Runtime Trace And Consolidation Notes

## Scope

This document traces what actually happens for `SUNNY DAY SONG` (`PL!-bp5-021-L`, live card id `669`) from authored data through compilation, runtime loading, trigger dispatch, frame execution, and QA coverage. The goal is not just to list files, but to separate:

- the files that are genuinely on the card's execution path,
- the duplicated artifacts that exist to support old and new representations at the same time,
- the compatibility shims and emergency fallbacks that still surround modern frame-driven abilities.

The card text is:

> On live start, if you have at least 1 member on stage, both players draw 1 and discard 1.
> If you have at least 2 members on stage, one `Muse` member on each side gets a heart bonus.
> If you have at least 3 members and all names are different, this live gets `+1` score.

## Short Answer

Sunny Day Song mostly runs through the generic modern path, but the engine still carries a large amount of compatibility baggage around that path.

The clean path is:

1. authored card text in `data/cards.json`
2. authored frame entry in `data/ability_frame_index.yaml`
3. compile semantic `effects` / `conditions` / `costs` into `data/cards_compiled.json`
4. Rust reloads authored sparse frame data at DB load time and reattaches executable frames
5. `OnLiveStart` trigger dispatch queues the ability
6. the interpreter walks the frame sequence and dispatches to generic handlers

The noisy part is that the runtime still supports several parallel representations of the same ability:

- raw card text
- compiled semantic `effects` / `conditions` / `costs`
- sparse authored frames from YAML or JSON-derived indexes
- bytecode words
- runtime-synthesized frames rebuilt from effects when the sparse entry is missing or incomplete

Sunny Day Song exposes one especially important weakness in that stack: the authored frame sequence still encodes its distinct-name clause as `CHECK_UNIQUE_NAMES_COUNT?`, which survives into derived artifacts as a `NOP` placeholder instead of a first-class condition opcode.

## Card-Specific Data Flow

### 1. Raw card definition

The base card lives in these source snapshots:

- `data/cards.json`
- `data/cards_vanilla.json`

Those files provide the canonical printed card text, basic score/hearts metadata, rarity, and card number. For Sunny Day Song, the raw source already contains the full three-branch ability text, including the `different names` clause.

### 2. Authored frame source

The real authored logic for the ability lives in:

- `data/ability_frame_index.yaml`

This is the important logic source for this card. The entry for `PL!-bp5-021-L` defines the frame sequence that the Rust engine is supposed to execute. The key points in that sequence are:

- `COUNT_STAGE >= 1`
- `JUMP_IF_FALSE +6`
- `SET_TARGET_SELF`
- `DRAW 1`
- `MOVE_TO_DISCARD 1`
- `SET_TARGET_OPPONENT`
- `DRAW 1`
- `MOVE_TO_DISCARD 1`
- `COUNT_STAGE >= 2`
- `JUMP_IF_FALSE +6`
- `SET_TARGET_SELF`
- `SELECT_MEMBER` filtered to `Muse`
- `SET_TARGET_OPPONENT`
- `SELECT_MEMBER` filtered to `Muse`
- `SET_TARGET_SELF`
- `ADD_HEARTS 1`
- `COUNT_STAGE >= 3`
- `CHECK_UNIQUE_NAMES_COUNT?`
- `JUMP_IF_FALSE +1`
- `BOOST_SCORE 1`
- `RETURN`

That `CHECK_UNIQUE_NAMES_COUNT?` entry is the first major sign that the authored frame story is not yet fully normalized.

### 3. Derived semantic view

The YAML entry is then materialized into a human-readable derived view in:

- `data/consolidated_abilities.json`

For Sunny Day Song, this derived view confirms the same branch structure. It also reveals that the distinct-name frame is currently represented as:

- opcode name: `NOP`
- decoded summary: `CHECK_UNIQUE_NAMES_COUNT?`

That means the derived semantic artifact knows the author intended a unique-name check, but the frame is not represented as a stable executable condition opcode.

### 4. Compiled runtime card export

The compiler outputs the runtime card record to:

- `data/cards_compiled.json`

For Sunny Day Song, the compiled live card entry contains:

- trigger `2` (`ON_LIVE_START`)
- semantic `effects`
- semantic `conditions`
- no runtime `frame_program` in the export

This is intentional. The current compiler strategy is to ship semantic data and let Rust rehydrate executable frames later.

### 5. Mirrored runtime copies

That compiled JSON is then copied to at least one more live mirror:

- `engine/data/cards_compiled.json`

And when asset syncing runs, it is also copied into launcher static data. This means the same card payload can exist in multiple runtime-facing locations.

## Files On The Actual Happy Path

These are the files that genuinely participate in making Sunny Day Song work today.

### Authoring and compile inputs

- `data/cards.json`
- `data/ability_frame_index.yaml`
- `data/metadata.json`

`data/metadata.json` matters because it defines opcode and filter bit meanings, including `FILTER_UNIQUE_NAMES`.

### Build pipeline

- `tools/build_cards.py`
- `tools/abilities/pipeline.py`
- `engine/compiler/main.py`
- `engine/compiler/semantic_processor.py`
- `tools/sync_launcher_assets.py`

What each one does:

- `tools/build_cards.py` is the user-facing entry point.
- `tools/abilities/pipeline.py` orchestrates runtime preparation.
- `engine/compiler/main.py` loads `cards.json`, resolves sparse authored frame entries from `ability_frame_index.yaml`, builds `Ability` objects, and exports `cards_compiled.json`.
- `engine/compiler/semantic_processor.py` converts frame instructions into semantic `effects`, `conditions`, and `costs`.
- `tools/sync_launcher_assets.py` mirrors the compiled output into `engine/data` and launcher static data.

### Runtime data load

- `engine_rust_src/src/core/logic/card_db.rs`
- `engine_rust_src/src/core/logic/models.rs`

This is where the modern path becomes noisy.

`card_db.rs` loads `cards_compiled.json`, then reattaches frame data from the sparse ability index during `attach_sparse_ability_index()`. `models.rs` defines the shared runtime structures for `Ability`, `FrameProgram`, `AbilityFrame`, `Effect`, and `Condition`.

### Trigger entry

- `engine_rust_src/src/core/logic/performance.rs`
- `engine_rust_src/src/core/logic/game_trigger.rs`

`performance.rs` is the entry point for `OnLiveStart` timing during live resolution. It cleans the live zone, enforces `cannot live` state, then emits the `OnLiveStart` trigger through `state.trigger_abilities()`.

`game_trigger.rs` scans stage cards and live cards, collects matching abilities, prechecks top-level conditions and costs, and queues the ability for execution.

### Interpreter and execution

- `engine_rust_src/src/core/logic/interpreter/mod.rs`
- `engine_rust_src/src/core/logic/interpreter/conditions/common.rs`
- `engine_rust_src/src/core/logic/interpreter/conditions/counts.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/execution.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/movement.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/state.rs`

These files are the real execution core.

For Sunny Day Song specifically:

- `COUNT_STAGE` is evaluated through condition helpers in `conditions/counts.rs`
- `JUMP_IF_FALSE` is processed in the main sequential interpreter in `interpreter/mod.rs`
- `DRAW` is dispatched from `handlers/execution.rs` into movement handlers
- `MOVE_TO_DISCARD` is dispatched into deck / discard movement handlers
- `SELECT_MEMBER` is dispatched into `handlers/flow_select.rs`
- `ADD_HEARTS` and `BOOST_SCORE` are dispatched into `handlers/state.rs` and then score / heart logic

## Exact Runtime Story For Sunny Day Song

### Step 1. Compiler resolves the ability from authored sparse frames

In `engine/compiler/main.py`, `SparseSourceManager` loads `data/ability_frame_index.yaml` and maps card refs like `(PL!-bp5-021-L, 0)` to a sparse ability payload.

When the compiler parses Sunny Day Song:

1. it finds the sparse entry for ability index `0`
2. it builds an `Ability` object from that entry
3. it stores the frame data in `frame_program`
4. it runs `populate_semantic_from_frames()` to derive semantic `effects`, `conditions`, and `costs`
5. for runtime export, it strips the `frame_program` and keeps the semantic fields

This is already a dual-representation design.

### Step 2. Rust reloads frames at database load time

At runtime, `card_db.rs` parses `cards_compiled.json`. Each live card arrives with semantic effects and conditions, but not with exported `frame_program` instructions.

`attach_sparse_ability_index()` then does the following:

1. look up `PL!-bp5-021-L#0` in the sparse index loaded from JSON sources
2. if found, convert that sparse entry back into a `FrameProgram`
3. if the sparse entry is missing or empty, synthesize a fallback frame entry from semantic effects
4. if even that fails, install a synthetic `RETURN`

So the Rust runtime does not trust the compiled export to be execution-ready by itself. It reconstructs executable frame data during load.

### Step 3. Performance phase emits `OnLiveStart`

When the live starts, `performance.rs` handles timing. Before the trigger fires, it does rule cleanup such as discarding non-live cards from the live zone. Then it broadcasts `TriggerType::OnLiveStart`.

### Step 4. Trigger collection finds the live ability

`game_trigger.rs` walks:

- stage members
- live zone cards
- source card if it is outside those zones

For Sunny Day Song, the live card in the live zone is discovered in the live-card scan and its `OnLiveStart` ability is queued.

### Step 5. Top-level conditions are prechecked before queueing

This matters because the engine currently has two layers of condition logic:

- top-level `ability.conditions` prechecks in `game_trigger.rs`
- inline frame conditions in the sequential interpreter

Sunny Day Song still enters the generic path here. The engine does not use a Sunny-specific trigger shim.

### Step 6. Sequential frame interpretation

`interpreter/mod.rs` drives the frame list.

The important part of the model is:

- condition-like frames set the current branch truth value
- `JUMP_IF_FALSE` skips branch bodies
- non-control frames are dispatched to typed handlers

For Sunny Day Song, the runtime behavior is intended to be:

1. if stage count is at least 1, both players draw 1 and discard 1
2. if stage count is at least 2, select `Muse` targets and apply the heart bonus
3. if stage count is at least 3 and names are distinct, apply `BOOST_SCORE 1`

### Step 7. Concrete opcode handler endpoints

The dispatcher in `handlers/execution.rs` sends Sunny's opcodes to these modules:

- `DRAW` -> movement handlers
- `MOVE_TO_DISCARD` -> deck / discard movement handlers
- `SELECT_MEMBER` -> `handlers/flow_select.rs`
- `ADD_HEARTS` and `BOOST_SCORE` -> state / score / hearts handlers

That is the good part of the architecture: after frame resolution, the card is mostly generic.

## Where The Compatibility Layers Start

Sunny Day Song itself is not especially bespoke. The complexity comes from all the formats and rescue paths around it.

### A. Multiple logic artifacts for one card

For this single ability, the repository currently maintains or derives all of the following:

- raw card text in `data/cards.json`
- authored sparse frame entry in `data/ability_frame_index.yaml`
- derived human-readable frame summary in `data/consolidated_abilities.json`
- compiled semantic runtime export in `data/cards_compiled.json`
- mirrored runtime copy in `engine/data/cards_compiled.json`
- launcher-facing mirrored copy during asset sync
- rehydrated `FrameProgram` inside Rust at DB load time

Some of that duplication is reasonable. The problem is that the runtime still depends on several of them simultaneously.

### B. Rust loader fallback chain

`card_db.rs` has a very broad sparse-index load order:

- `data/ability_frame_index.json`
- `../data/ability_frame_index.json`
- `data/consolidated_abilities.json`
- `../data/consolidated_abilities.json`
- embedded consolidated JSON
- embedded legacy frame index JSON

That means the runtime is still willing to accept multiple serialized shapes for the same conceptual thing.

This is a compatibility layer, not a clean runtime contract.

### C. Effect-to-frame synthesis fallback

If sparse frame data is missing or empty, `attach_sparse_ability_index()` synthesizes frames from semantic effects using `AbilityFrame::from_effect()`.

That is useful as a rescue path, but it also means the engine supports:

- authored frames
- compiled effects
- runtime-synthesized frames derived from effects

again, three versions of the same logic.

### D. Bytecode compatibility is still alive

`models.rs` still supports:

- `FrameProgram::from_bytecode()`
- raw bytecode serialization in `to_words()` / `to_bytecode()`
- `Ability.bytecode`
- old instruction decoding through `BytecodeProgram`

Even though Sunny Day Song is frame-era content, the shared runtime model still carries bytecode-era conversion and compatibility APIs.

### E. Legacy normalization shims in card DB load

`card_db.rs` contains explicit normalization functions such as:

- `normalize_legacy_tap_member_ability()`

This kind of load-time mutation is strong evidence that the runtime is still fixing old exports on the fly.

Sunny Day Song does not use that tap-member shim, but it is loaded through the same compatibility-heavy DB layer.

### F. Inline trigger-precheck heuristics for live abilities

`game_trigger.rs` imports `should_skip_inline_live_precheck()` from `ability_patterns.rs`.

That function exists to avoid dropping certain live abilities whose branch logic is encoded inline rather than in clean top-level `ability.conditions`.

Sunny Day Song does not appear to need that skip on its happy path, but the fact that the trigger system needs a pattern-based escape hatch is another sign that authored frames, semantic conditions, and trigger prechecks are not fully aligned.

### G. Card-specific emergency fixes adjacent to the generic interpreter

`interpreter/mod.rs` still contains card-specific gates and direct-effect workarounds for other cards, including:

- `PL!SP-bp1-024-L`
- card `579`
- card `4849`
- card `8844`
- card `358`

Sunny Day Song does not currently hit one of those emergency branches, which is good. But the fact that they live directly inside the shared resolver shows how much compatibility debt is still sitting in the core execution path.

## Sunny Day Song's Distinct-Name Clause Is Not Cleanly Authored Yet

This is the most important Sunny-specific finding.

### What we have now

In `data/ability_frame_index.yaml`, Sunny Day Song's third branch uses:

- `COUNT_STAGE >= 3`
- `CHECK_UNIQUE_NAMES_COUNT?`
- `JUMP_IF_FALSE +1`
- `BOOST_SCORE 1`

In `data/consolidated_abilities.json`, that second frame becomes:

- opcode `NOP`
- summary `CHECK_UNIQUE_NAMES_COUNT?`

### Why that matters

The engine already has a generic unique-name counting mechanism.

`conditions/counts.rs` supports `FILTER_UNIQUE_NAMES`, and `metadata.json` declares the `FILTER_UNIQUE_NAMES` bit. There are also tests proving unique-name counting behavior in `engine_rust_src/src/count_group_tests.rs`.

So the engine has a reusable concept for unique-name counting.

But Sunny Day Song's authored frame is not encoded in that reusable form. Instead, the authored data keeps a placeholder semantic marker that degrades into `NOP` in derived artifacts.

That creates a bad split:

- the engine knows how to count unique names,
- the metadata knows how to encode unique-name filters,
- the Sunny frame entry does not use that mechanism directly.

### Practical consequence

This card is exactly the sort of example that shows where consolidation should start:

- the authored frame source should express a real executable unique-name condition
- the semantic export should preserve that condition faithfully
- the Rust loader should not need to infer intent from a placeholder string

## QA And Verification Status

Relevant QA data exists in:

- `data/qa_data.json`

Sunny Day Song is directly referenced by at least:

- `Q210`
- `Q211`

Those rulings are about multi-name cards and how they count for this live's conditions and targeting.

There is also a QA registry mention in:

- `engine_rust_src/src/qa/mod.rs`

That file advertises `test_q211_sunny_day_song` in the module-level documentation. However, a repository search for `test_q211_sunny_day_song` did not find a matching test implementation in the current Rust test files.

That suggests one of two things:

- the test was planned and documented but never implemented,
- or the implementation was renamed and the QA index comment drifted.

Either way, the card-specific verification story looks weaker than the module commentary implies.

## Canonical Vs Compatibility Matrix

### Likely canonical or should-be-canonical

- `data/cards.json`: printed card source and card metadata
- `data/ability_frame_index.yaml`: authored frame logic
- `engine/compiler/main.py`: compiler entry that joins card data with authored frames
- `engine/compiler/semantic_processor.py`: deterministic semantic derivation layer

### Derived but reasonable

- `data/consolidated_abilities.json`: human-readable inspection output
- `data/cards_compiled.json`: runtime export for cards
- `data/cards_vanilla.json`: snapshot / baseline data set

### Compatibility / shim / fallback layers

- `engine/data/cards_compiled.json`: mirrored runtime copy
- launcher static copy created by `tools/sync_launcher_assets.py`
- sparse-index loader fallback chain in `card_db.rs`
- embedded consolidated JSON and embedded legacy frame index JSON
- `AbilityFrame::from_effect()` rescue path
- `FrameProgram::from_bytecode()` and bytecode compatibility APIs
- load-time normalizers like `normalize_legacy_tap_member_ability()`
- trigger precheck escape hatches in `ability_patterns.rs`
- card-specific emergency checks in `interpreter/mod.rs`

## Consolidation Opportunities

### 1. Make the authored frame source fully executable

This is the highest-value cleanup.

Sunny Day Song should not need a `CHECK_UNIQUE_NAMES_COUNT?` placeholder. The authored YAML should use a real condition representation that survives compilation and runtime intact.

Good outcomes would be:

- encode it as a condition opcode that maps cleanly to `ConditionType::UNIQUE_NAMES_COUNT`
- or encode it as a count frame with `FILTER_UNIQUE_NAMES`

The main point is to stop carrying placeholder intent strings into runtime-facing data.

### 2. Reduce runtime rehydration pressure

Today the compiler intentionally omits `frame_program` from the runtime export, then Rust reconstructs executable frames from sparse data or semantic effects.

That design works, but it creates avoidable duplication.

There are two plausible consolidation directions:

- ship execution-ready structured frames in `cards_compiled.json` and let Rust load one artifact
- or keep the current semantic export, but make Rust depend on exactly one authored sparse artifact instead of several fallback formats

Either direction is cleaner than the current hybrid.

### 3. Collapse the sparse-index loader contract to one format

`card_db.rs` should not need to try:

- ability frame index JSON
- consolidated abilities JSON
- embedded consolidated JSON
- embedded legacy frame index JSON

Pick one runtime sparse format and make the loader strict.

### 4. Remove effect-to-frame synthesis as the normal safety net

`AbilityFrame::from_effect()` is useful for temporary migration support, but it should not be a routine substitute for authored frame presence.

If a card is frame-authored, missing or empty sparse frames should be treated as build-time defects, not runtime reconstruction work.

### 5. Push compatibility fixes out of the interpreter core

The card-specific workarounds in `interpreter/mod.rs` should eventually move into one of these buckets:

- fixed authored frame data
- fixed compiler output
- an explicit compatibility registry outside the generic interpreter

The generic resolver should not keep accumulating emergency branches.

### 6. Reconcile trigger prechecks with inline frame conditions

`game_trigger.rs` currently prechecks top-level semantic conditions, while `interpreter/mod.rs` also evaluates inline condition frames sequentially.

That dual system is exactly why `should_skip_inline_live_precheck()` exists.

Long term, one of these should win:

- top-level conditions become a pure summary and never gate queueing independently
- or inline condition frames become purely executable and the trigger layer stops trying to partially understand them

Right now the engine is doing both.

### 7. Remove mirror proliferation where possible

`tools/sync_launcher_assets.py` copies `data/cards_compiled.json` into:

- launcher static data
- `engine/data/cards_compiled.json`

That may be necessary operationally, but it also creates drift risk. If those mirrors remain necessary, they should be treated as deployment artifacts, not as alternate sources.

## Practical Recommendation Order

If the goal is to consolidate without destabilizing the engine, this is the order I would use.

1. Fix authored placeholder frames first.
2. Make the compiler preserve those conditions cleanly in semantic exports.
3. Tighten the Rust sparse-index load contract to one preferred format.
4. Treat effect-to-frame synthesis as a migration-only fallback.
5. Move card-specific emergency logic out of `interpreter/mod.rs`.
6. Revisit whether `cards_compiled.json` should already contain execution-ready structured frames.

## Bottom Line

Sunny Day Song is a good example of the current engine state because the card itself is not exotic. Its behavior is fundamentally generic:

- count stage members
- draw and discard
- select valid members
- add a heart
- add score

The complexity around it comes from the engine carrying multiple generations of ability representation at once.

The single most useful concrete cleanup this card points to is this:

> stop expressing distinct-name checks as placeholder pseudo-frames and encode them as real executable conditions in the authored source.

Once that class of placeholder is gone, a large part of the compatibility stack becomes easier to shrink, because the engine no longer needs to guess whether authored logic is structural data, semantic summary, or legacy fallback intent.