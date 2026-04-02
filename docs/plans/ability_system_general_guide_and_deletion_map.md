# Ability System General Guide And Deletion Map

## Purpose

This document explains how abilities are actually implemented in the current repository, which files participate in that pipeline, which files are authoritative versus derived, and which layers look redundant enough to delete or collapse.

This is a general guide, not a single-card trace. It is meant to answer four practical questions:

1. Where ability logic is authored.
2. How that logic is compiled and loaded.
3. Which runtime files actually execute it.
4. Which artifacts, adapters, and helper layers should be considered redundant.

The main theme is simple: the codebase is mostly moving toward a frame-first model, but it still carries multiple overlapping representations of the same ability.

## Executive Summary

The actual modern path is:

1. Human-readable card text lives in `data/cards.json`.
2. Authored frame logic lives in `data/ability_frame_index.yaml`.
3. Python compile code in `engine/compiler/` builds semantic runtime exports into `data/cards_compiled.json`.
4. Rust loads `cards_compiled.json` and then reattaches authored frame data from `data/consolidated_abilities.json`.
5. Trigger collection in `game_trigger.rs` decides whether an ability should queue.
6. The interpreter in `engine_rust_src/src/core/logic/interpreter/` executes frames.
7. Frontend debug and presentation layers should display the same model using frame or execution terminology, not stale bytecode labels.

That is the path to preserve.

The main redundancy problem is that the same ability may exist at the same time as:

- raw printed text
- authored sparse frames
- derived consolidated frames
- semantic effects, conditions, and costs
- bytecode words or bytecode-shaped compatibility data
- runtime-derived metadata such as choice flags and opcode masks
- user-facing labels that still say "bytecode" even when the UI is showing execution traces or frame-derived summaries

If the project wants big deletions, they should focus on removing entire duplicate representations and compatibility loaders, not on shaving individual condition checks.

## Current Reality Versus Stale Guidance

Some docs and skills still describe `data/ability_frames.json` as the primary authored source. That does not match the active pipeline in this workspace.

The currently active path is centered on:

- `data/ability_frame_index.yaml`
- `data/consolidated_abilities.json`
- `data/cards_compiled.json`

Important drift points:

- the repository previously carried a stale `tools/sync_ability_frame_index.py` path pointing at `data/ability_frames.json`
- that deleted script imported `prepare_frame_index` from `tools/abilities/pipeline.py`
- the current `tools/abilities/pipeline.py` does not define that function
- some skills and older docs still tell readers to inspect `data/ability_frames.json`

That means there is already documentation and tooling drift around the frame source of truth. Any cleanup plan should start by naming the real canonical files and deleting or rewriting the stale guidance.

## Single Source Of Truth Map

### Canonical inputs

These files are the real authored or hand-maintained inputs.

- `data/cards.json`
- `data/ability_frame_index.yaml`
- `data/metadata.json`

What they do:

- `data/cards.json` contains the card database as edited source.
- `data/ability_frame_index.yaml` contains authored frame logic tied to cards and ability indices.
- `data/metadata.json` defines opcode names, trigger names, and layout information consumed by both compiler and runtime.

### Derived but important runtime artifacts

These are not the human-authored source, but they are active derived artifacts used by the runtime.

- `data/consolidated_abilities.json`
- `data/cards_compiled.json`

What they do:

- `data/consolidated_abilities.json` is the runtime-friendly consolidated view of authored frame data.
- `data/cards_compiled.json` is the semantic runtime card export produced by the Python compiler.

### Mirrored runtime copies

These are not canonical. They are mirrors for consumers.

- `engine/data/cards_compiled.json`
- `launcher/static_content/data/cards_compiled.json`

These should be treated as generated live copies, not places to edit.

## End-To-End Ability Pipeline

## Stage 1: Authoring

### `data/cards.json`

This file provides card identity, printed text, score, cost, hearts, and card type. It is the card catalog.

It does not express the full execution plan for nontrivial abilities.

### `data/ability_frame_index.yaml`

This is where authored ability logic actually becomes executable design. The file stores sparse frame-based ability definitions linked to cards.

In practice this is the closest thing to the authored ability logic source.

### `data/metadata.json`

This defines the symbolic meaning of opcodes and layout fields. It is the schema and constant dictionary that lets compiler and runtime agree on frame meaning.

## Stage 2: Python compilation

### `tools/build_cards.py`

This is the user-facing entry point. It exists mainly to call the smaller pipeline module.

### `tools/abilities/pipeline.py`

This is the top-level orchestrator for the simplified runtime build.

Right now it:

- compiles cards unconditionally
- writes `data/cards_compiled.json`
- optionally syncs launcher and runtime mirrors
- does not maintain a separate frame-index build path anymore

That last point matters because some other scripts still behave as if it does.

### `engine/compiler/main.py`

This is the main compiler for cards.

Its active role is:

- read raw card data from `data/cards.json`
- resolve authored ability information through sparse authored sources
- build `Ability` model objects
- populate semantic effects, conditions, and costs
- export compact runtime cards into `data/cards_compiled.json`

The important design decision in this file is that the runtime export keeps semantic ability data and deliberately omits `frame_program` in the runtime profile.

That means Rust is expected to rebuild executable frame programs later.

### `engine/compiler/semantic_processor.py`

This module translates frames into semantic `effects`, `conditions`, and `costs`.

It is the bridge between authored frame logic and the semantic runtime export.

It is also one of the main places where flattening occurs. When the semantic export becomes stricter or simpler than the authored control flow, runtime prechecks can become more restrictive than actual frame execution.

That is why it is a critical file for consolidation.

### `tools/sync_launcher_assets.py`

This is not part of semantic compilation. It is distribution plumbing.

Its job is to mirror `data/cards_compiled.json` into:

- launcher static content
- `engine/data/`

This is operationally useful, but it also means there are several copies of the compiled database in the repo at any given time.

## Stage 3: Rust load and normalization

### `engine_rust_src/src/core/logic/card_db.rs`

This file is one of the most important files in the system and one of the best places to delete code.

Its responsibilities currently include:

- loading the compiled card database
- loading the consolidated authored sparse frame data
- reattaching frame programs to abilities
- deriving top-level conditions from leading frame blocks
- enriching runtime metadata such as opcode masks, trigger masks, and choice flags
- applying a few compatibility policies around legacy ids and sparse data lookup

This file is the place where the system most visibly carries both the semantic export world and the authored frame world at once.

### `engine_rust_src/src/core/logic/models.rs`

This file defines the core runtime types:

- `Ability`
- `FrameProgram`
- `AbilityFrame`
- `Effect`
- `Condition`
- `Cost`

It also contains several compatibility bridges.

The most important one is in `Ability` itself: the struct still stores multiple representations of the same ability.

That representation overlap is not just a documentation problem. It shapes how the runtime falls back between `frame_program`, semantic effects, and bytecode-like conversions.

## Stage 4: Trigger collection and queueing

### `engine_rust_src/src/core/logic/performance.rs`

This is one of the timing entry points for live abilities. It is where performance-phase ability timing begins for things like `OnLiveStart`.

This file does not define ability semantics, but it is part of the ability pipeline because it decides when triggers are emitted.

### `engine_rust_src/src/core/logic/game_trigger.rs`

This file collects eligible triggered abilities from board state and queues them.

Its role is not execution. Its role is pre-execution filtering.

That means it relies heavily on top-level semantic conditions. Any mismatch between frame-authored control flow and compiled semantic condition flattening will show up here first.

## Stage 5: Execution

### `engine_rust_src/src/core/logic/interpreter/mod.rs`

This is the frame interpreter.

It:

- walks frame sequences
- evaluates condition-like frames
- handles branching and jumps
- dispatches non-control frames to handler modules
- still carries a mixture of frame-first logic and bytecode-era compatibility wrappers

This is the core execution engine.

### `engine_rust_src/src/core/logic/interpreter/conditions/`

This directory contains condition evaluation logic.

The important architectural fact is that it contains both normal condition opcode handling and raw semantic param handling such as `raw_cond` payloads.

That is a sign that the runtime is already partly beyond packed bytecode-only conditions.

### `engine_rust_src/src/core/logic/interpreter/handlers/`

These files perform the concrete effect operations for movement, selection, score, hearts, and state updates.

They are real runtime logic, not just helpers.

The fragmentation here is not necessarily wrong, but some of it reflects an older decomposition that grew around compatibility edges.

### `engine_rust_src/src/core/logic/action_gen/`

This directory matters because some ability execution produces response prompts or selectable actions rather than immediate state mutation.

It is downstream of interpreter behavior.

If ability cleanup changes selection or prompt semantics, action generation is one of the first places that will expose regressions.

## Stage 6: Tests and verification

### `engine_rust_src/src/qa_verification_tests.rs`

This is the broad regression and rules verification suite for real-card behavior.

### `engine_rust_src/src/test_helpers.rs`

This file is not just a convenience layer. It also demonstrates how many fallback paths currently exist for locating card databases. That is useful for tests, but it is also another sign of duplicated runtime artifacts.

## What Each Important File Actually Does

## Compiler side

### `engine/compiler/main.py`

Primary responsibilities:

- parse cards
- assign ids
- build `Ability` objects
- export runtime JSON

Should not do:

- author runtime-specific hacks for individual cards
- treat the compiled export as the long-term authored source

### `engine/compiler/semantic_processor.py`

Primary responsibilities:

- derive semantic `effects`
- derive semantic `conditions`
- derive semantic `costs`

Should not do:

- flatten branch-local conditions into unconditional trigger gates unless that is truly intended
- become a second authored logic system independent of frames

## Runtime side

### `card_db.rs`

Primary responsibilities:

- load cards
- join compiled cards with consolidated authored frame data
- compute runtime metadata cheaply enough for play

Should not do:

- invent new ability logic from printed text
- silently patch card-specific semantic bugs that belong in authored or compiled data
- keep multiple obsolete sparse index formats alive forever

### `models.rs`

Primary responsibilities:

- define core models
- provide conversions needed for runtime use

Should not do long-term:

- keep every bytecode-era compatibility layer if the runtime is frame-first
- make `Ability` the owner of several equally authoritative ability representations

### `game_trigger.rs`

Primary responsibilities:

- collect triggers
- precheck gates
- enqueue abilities

Should not do:

- compensate for incorrect compiler flattening through a growing pile of special-case skips

### `interpreter/mod.rs`

Primary responsibilities:

- execute frames
- branch correctly
- suspend and resume interactions

Should not do long-term:

- operate as both a frame interpreter and a bytecode compatibility sandbox forever

## Core Redundancies

## Redundancy 1: Multiple ability representations in `Ability`

The current `Ability` struct carries overlapping representations:

- `bytecode`
- `effects`
- `conditions`
- `costs`
- `frame_program`

This creates several problems:

- every loader has to decide which representation to trust
- every helper must define fallback order
- test failures can come from disagreement between representations rather than actual gameplay logic
- cleanup work becomes harder because removing one layer seems unsafe while the others still exist

What should become authoritative:

- authored execution should be `frame_program`
- semantic summaries should be derived support data, not competing execution sources

What is probably redundant long-term:

- persistent `bytecode` storage as a first-class field
- automatic effect-to-frame round-tripping as a normal runtime behavior

## Redundancy 2: Runtime export plus runtime rehydration

The Python compiler exports semantic runtime cards without `frame_program`.

Then Rust loads `cards_compiled.json` and reattaches frames from `consolidated_abilities.json`.

That means the system currently needs both:

- semantic export for runtime cards
- consolidated frame data for executable logic

This is workable, but it is still dual-source runtime loading.

There are only two clean end states:

1. Export executable frame programs directly and stop runtime rehydration.
2. Keep the semantic export minimal and treat consolidated authored frames as the single execution source by design.

The worst state is the current middle state where both are substantial and both are treated as partially authoritative.

## Redundancy 3: Duplicate compiled card copies

The compiled runtime card database exists in several places:

- `data/cards_compiled.json`
- `engine/data/cards_compiled.json`
- `launcher/static_content/data/cards_compiled.json`

This duplication is understandable for distribution, but it creates drift pressure in:

- tests
- manual scripts
- debugging commands
- archive tools

The real source among those copies should remain the root `data/cards_compiled.json`.

The other two are delivery copies.

## Redundancy 4: Stale frame-index tooling

The runtime loader used to support older frame-index shapes. Part of that has already been cut back.

The repo still contains more stale frame-index signs:

- the deleted `tools/sync_ability_frame_index.py` assumed `data/ability_frames.json`
- it imported `prepare_frame_index` from `tools/abilities/pipeline.py`
- the active pipeline module does not define that function
- `tools/frame_codec.py` still describes frame/index output as derived and secondary

This means part of the repository still points at a frame-index maintenance path that is no longer clearly active.

That is not just confusing. It is deletion bait.

## Redundancy 5: Bytecode compatibility layers

The runtime still contains bytecode-shaped APIs and conversion helpers in several places, including:

- `models.rs`
- interpreter instruction helpers
- state-level bytecode resolution helpers
- logging that still refers to bytecode as a primary description path

A frame-first runtime does not need all of those as permanent public surfaces.

Some should survive for tests or old data import.

Most should stop being central.

## Redundancy 6: Build-time documentation logic inside runtime core

`engine_rust_src/src/core/logic/ability_manifest.rs` is useful, but it is not runtime gameplay logic.

It reads like analysis and manifest-generation code living inside the runtime core namespace.

Likewise, `interpreter/logging.rs` contains a lot of human-readable description logic that is valuable for diagnostics, but not essential to core frame execution.

These modules are not necessarily bad. But they are good candidates to move out of the tight runtime core once the architecture is cleaned up.

## What Should Be Redundant

The list below is intentionally blunt.

### Should be redundant now or very soon

- support for legacy `ability_frame_index.json` loading in the Rust card DB loader
- stale docs claiming `data/ability_frames.json` is the primary authored source
- dead frame-index pipeline entry points that no longer exist in the active build pipeline
- runtime use of mirrored `cards_compiled.json` copies as if they were independent sources
- web UI labels and help text that present execution logs as "bytecode" when they are really trace or frame views

### Should become redundant after the next cleanup phase

- `Ability.bytecode` as a normal first-class representation
- effect-to-frame runtime rebuilding as a normal execution fallback
- card-specific runtime patching in loaders for data issues that should be fixed upstream
- debug manifest generation inside the runtime core tree

### Should only be removed after more source data normalization

- semantic effect and condition support entirely
- raw condition compatibility for placeholder-authored frames
- certain test-only or repro-only bytecode helpers

These last items remain useful until authored frame data is consistently first-class and complete.

## Big Deletion Candidates

## Safe deletions or rewrites first

These are high-value and comparatively safe.

### 1. Delete or rewrite stale frame-source docs and skills

Targets:

- docs that name `data/ability_frames.json` as canonical
- skills or workflow notes that direct people to the wrong file

Reason:

- they actively mislead people about the current ability source of truth

### 2. Delete dead frame-index entry points

Targets:

- the removed `tools/sync_ability_frame_index.py`, which used to point at a stale frame-source path

Reason:

- it referenced `prepare_frame_index`, which is not present in the active pipeline
- it points to an authored source that is not the active one described elsewhere

### 3. Delete duplicate loader support for obsolete sparse index formats

Targets:

- old alternate index-shape support in Rust loaders and related helpers

Reason:

- every extra accepted input shape keeps dead data paths alive

## Medium-risk but high-value deletions

### 4. Remove `Ability.bytecode` from normal runtime flow

Targets:

- fields and helpers that keep bytecode as a peer of frames rather than a conversion edge case

Reason:

- the project is already frame-first in practice
- keeping bytecode first-class forces fallback logic throughout models and interpreter code

Risk:

- tests, tooling, and debug helpers may still assume bytecode access

### 5. Remove runtime effect-to-frame synthesis as a normal fallback

Targets:

- runtime paths that construct executable frames from semantic `effects` automatically

Reason:

- it creates fake execution programs that were not truly authored
- it hides missing or broken authored data

Risk:

- cards with incomplete authored frame data may stop working until upstream data is fixed

### 6. Move manifest and descriptive logging out of core logic

Targets:

- `engine_rust_src/src/core/logic/ability_manifest.rs`
- portions of `engine_rust_src/src/core/logic/interpreter/logging.rs`

Reason:

- these are diagnostics and build-analysis concerns, not core gameplay execution

Risk:

- any tools depending on the current module path will need a new home

## High-risk deletions that need prior cleanup

### 7. Collapse semantic `effects`, `conditions`, and `costs` into a purely derived layer

Reason:

- this would remove the main dual-representation problem

Why not first:

- trigger prechecks and some selection logic still rely on semantic summaries
- some authored frames still degrade into placeholder forms such as unique-name checks represented as `NOP`

### 8. Remove raw condition compatibility payloads

Reason:

- they are a compatibility seam, not ideal authored execution data

Why not first:

- some authored entries still depend on them indirectly because placeholder frames are not yet normalized upstream

## Non-Logic Surfaces To Audit

The plan should include anything that exposes ability data to a person, even if it does not affect gameplay:

- `frontend/web_ui/js/modals/DebugModal.js`
- `frontend/web_ui/js/modals/SettingsModal.js`
- `frontend/web_ui/index.html`
- `frontend/web_ui/js/i18n/locales/en.json`
- `frontend/web_ui/js/i18n/locales/jp.json`
- `frontend/web_ui/js/components/ChoiceView.js`
- workflow docs and skills that tell contributors how to inspect card logic

These surfaces do not own ability rules, but they do shape how users and contributors understand the system. If the runtime is frame-first, these labels should say frame, execution, trace, or log unless they are explicitly showing legacy bytecode data.

## Files That Matter Most For Future Cleanup

If the project wants large, structural deletion work, these files should be the focus order.

### Tier 1

- `engine_rust_src/src/core/logic/card_db.rs`
- `engine_rust_src/src/core/logic/models.rs`
- `engine/compiler/main.py`
- `engine/compiler/semantic_processor.py`

These decide what an ability is and how it moves between authored, compiled, and executable form.

### Tier 2

- `engine_rust_src/src/core/logic/game_trigger.rs`
- `engine_rust_src/src/core/logic/interpreter/mod.rs`
- `engine_rust_src/src/core/logic/interpreter/conditions/`
- `engine_rust_src/src/core/logic/interpreter/handlers/`

These decide how loaded ability data is interpreted and enforced.

### Tier 3

- `tools/sync_launcher_assets.py`
- `engine_rust_src/src/test_helpers.rs`
- `engine_rust_src/src/core/logic/ability_manifest.rs`
- frontend debug and settings panels that still say "bytecode"
- stale docs and skills under `docs/` and `.github/skills/`

These reflect distribution, diagnostics, or drift rather than core logic.

## Recommended Deletion Order

This is the least chaotic order.

### Phase 1: Delete drift and dead tooling

- rewrite stale docs that still point to `data/ability_frames.json`
- keep deleted the stale `tools/sync_ability_frame_index.py` path and do not reintroduce it without a real pipeline owner
- remove dead references to absent frame-index pipeline functions

Outcome:

- documentation and build tooling stop lying about the source of truth

### Phase 2: Tighten runtime inputs

- keep only one accepted sparse authored-frame format in runtime loaders
- stop supporting old index shapes
- reduce test and script reliance on mirror copies of compiled cards

Outcome:

- fewer runtime branches for data loading

### Phase 3: Remove runtime self-healing

- stop deriving executable frame programs from semantic effects
- stop raw-text-driven or card-specific loader fixes
- fix the upstream authored or compiled data instead

Outcome:

- data bugs become visible at the source instead of being masked in runtime

### Phase 4: Collapse representation overlap

- demote or remove bytecode as a first-class runtime representation
- reduce `Ability` to one execution source plus derived summaries

Outcome:

- the engine becomes legible again because each ability has one execution story

### Phase 5: Move diagnostics out of core logic

- move manifest generation and heavy human-readable description helpers into tooling or debug-only modules

Outcome:

- runtime core becomes smaller and easier to reason about

## What Not To Delete Yet

Some things look redundant but still carry real compatibility value.

### Raw condition support

Do not delete it until authored placeholder conditions such as unique-name checks are normalized upstream.

### Semantic condition summaries

Do not delete them until trigger collection has a clean alternative that stays consistent with frame-authored control flow.

### Test database path fallbacks

Do not aggressively delete those until the repository standardizes one test runtime location for compiled card data.

## The Clean Target Architecture

The clean end state should look like this:

1. Author ability logic once in a single authored frame source.
2. Compile one canonical runtime execution artifact.
3. Load that artifact without reinterpreting or repairing it in Rust.
4. Use semantic summaries only as derived metadata, not as competing execution truth.
5. Treat mirrored runtime data and diagnostic manifests as outputs, not peers of authored data.

In practical terms that means:

- one authored logic source
- one execution representation
- one compiled card database source
- zero loader-time card-specific repairs
- zero stale frame-index side paths

## Current Bottom Line

The ability system is not mainly suffering from too many opcode handlers.

It is suffering from too many representations of the same ability and too many layers that still pretend older representations are primary.

If the project wants big deletions, the best deletions are:

1. stale docs and stale frame-source tooling
2. old frame-index compatibility paths
3. runtime self-healing that invents executable programs from semantic summaries
4. bytecode-era first-class runtime surfaces
5. diagnostic manifest code living inside core runtime logic

That is the path that will reduce actual architectural complexity, not just line count.