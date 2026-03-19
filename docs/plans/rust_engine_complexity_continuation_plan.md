# Rust Engine Complexity Continuation Plan

## Goal

Lower the complexity of the Rust engine while preserving functionality.

This plan assumes the recent work has already completed a first-stage decomposition:

- large handler files were split into smaller modules
- some router files now delegate instead of implementing everything inline
- a few shared helpers now exist for repeated patterns

The next phase should focus on actual simplification, not just further file splitting.

## Current Assessment

The work so far has been helpful, but uneven.

What has helped:

- handler routers such as `flow.rs`, `state_member.rs`, and `movement.rs` are thinner
- duplicated slot-target logic has been centralized in `state_score_slots.rs`
- duplicated zone/card logic has been centralized in `interaction_zone.rs`
- duplicated prompt/suspend logic has started to move into `choice_prompt.rs`

What has not been fully solved:

- several of the largest files still contain the real state-machine complexity
- many handlers still manually implement the same prompt/resume/apply loop
- some files are smaller, but not simpler in their control flow
- the worktree currently contains a lot of unrelated churn, which makes progress harder to judge

## Principle

Do not optimize for "more files".

Optimize for:

- fewer ways to express the same runtime interaction
- smaller state machines
- clearer ownership of state mutation
- fewer ad hoc manipulations of `AbilityContext`
- shared primitives for repeated gameplay flows

## What Stage 1 Accomplished

Stage 1 was decomposition.

That was still worthwhile because it exposed the repeated patterns and created seams we can now simplify against.

Examples of good Stage 1 outcomes:

- `choice_prompt.rs`
- `interaction_zone.rs`
- `state_score_slots.rs`

Those files are important because they reduce duplicated logic across multiple handlers instead of merely relocating code.

## Stage 2 Objective

Stage 2 is consolidation.

The goal is to replace repeated custom control flow with shared runtime primitives.

This is the point where complexity should actually go down at the system level.

## Highest-Value Next Work

### 1. Finish choice-flow consolidation

The engine still has many copies of this pattern:

- derive prompt text
- suspend interaction
- resume via `choice_index`
- update `v_remaining`
- repeat if necessary

This should be expressed through `choice_prompt.rs` wherever possible.

Priority targets still using direct `get_choice_text` / `suspend_interaction` patterns:

- `interaction_select_cards.rs`
- `interaction_look_choose.rs`
- `movement_deck_order.rs`
- `movement_deck_order_reorder.rs`
- `movement_deck_look_cards.rs`
- `movement_discard_prompt.rs`
- `movement_discard_select.rs`
- `state_member_play.rs`
- `state_member_move.rs`
- `state_member_position.rs`
- `state_member_formation.rs`
- `state_energy_place.rs`

Success criterion:

- direct prompt/suspend boilerplate is reduced to a small number of truly special-case sites

### 2. Break the remaining "elephant" files by state-machine phase, not by size

The current largest remaining files are the real complexity hotspots:

- `state_member_play_discard.rs`
- `interaction_look_choose_resolve.rs`
- `state_member_tap_member_logic.rs`
- `movement_discard.rs`
- `movement_discard_select.rs`
- `movement_discard_prompt.rs`

These should be simplified by separating each runtime flow into explicit phases:

- setup / collect candidates
- prompt / suspend
- resume / decode choice
- mutate state
- continue / terminate / repeat

If a file still interleaves all of those phases, it is still too complex even if it has been split before.

Success criterion:

- each major interaction flow is understandable as a small state machine with explicit phases

### 3. Reduce raw `AbilityContext` manipulation

Many handlers still directly mutate:

- `choice_index`
- `v_remaining`
- `target_slot`
- `area_idx`
- `selected_cards`
- `v_accumulated`

That makes the engine hard to reason about because state transitions are implicit and scattered.

Introduce focused helpers or local structs for common flows such as:

- repeated selection
- discard-to-play
- choose-and-move
- optional confirmation
- multi-pick interactions

Success criterion:

- fewer handlers directly manipulate multiple context fields by hand

### 4. Separate mutation primitives from selection logic

Some files still combine "how the user chooses" with "how state changes are applied".

That should be separated.

Examples:

- zone/card removal and placement should be shared primitives
- slot-target application should stay shared
- discard/deck/hand transfers should converge on a smaller set of state mutation helpers

Good direction:

- keep interaction helpers focused on prompting and resume semantics
- keep mutation helpers focused on board/state changes only

Success criterion:

- fewer handlers both collect choices and implement zone mutation inline

### 5. Keep routers as routers

Files like these should continue getting thinner:

- `flow.rs`
- `state_member.rs`
- `movement.rs`
- `mod.rs`

They should dispatch, normalize arguments, and hand off to focused logic.

They should not regain gameplay behavior.

Success criterion:

- router files contain little or no business logic beyond dispatch/normalization

## Recommended Execution Order

### Pass 1: Finish shared choice prompt rollout

Convert the remaining straightforward prompt/suspend call sites to use `choice_prompt.rs`.

This is the safest next pass because:

- it is low-risk
- it removes duplicated plumbing
- it makes the remaining special cases easier to see

### Pass 2: Normalize repeated multi-step interactions

Target the repeated state-machine families:

- look / choose / reorder
- discard selection and discard movement
- select cards from zone
- play from discard
- optional confirm + selection

This pass should create small reusable helpers for each family.

### Pass 3: Simplify the biggest remaining handlers

After the reusable patterns are clearer, revisit:

- `state_member_play_discard.rs`
- `interaction_look_choose_resolve.rs`
- `state_member_tap_member_logic.rs`

These should be simplified with explicit flow phases, not merely split into more sibling files.

### Pass 4: Tighten context boundaries

Reduce raw `AbilityContext` mutation by introducing helper functions or small flow-specific context wrappers.

This pass is where maintainability will improve most for future changes.

## What To Avoid

Avoid:

- creating more `*_utils.rs` junk drawers
- splitting files without changing responsibility boundaries
- adding new gameplay logic to router files
- mixing compiler/data work with interpreter refactor evaluation
- changing behavior while refactoring unless tests clearly show the previous behavior was wrong

## Validation Strategy

After each simplification step:

- run `cargo check --manifest-path engine_rust_src/Cargo.toml`
- run targeted tests for touched interpreter behavior when practical
- prefer characterization tests around public engine behavior before deeper rewrites

Existing smoke tests such as `engine_rust_src/tests/state_member_smoke.rs` should be extended when new behavior seams are stabilized.

## How To Judge Progress

The refactor is helping if:

- repeated prompt/resume patterns disappear from handlers
- large files lose control-flow duplication, not just lines
- routers become more declarative
- fewer handlers manipulate many `AbilityContext` fields directly
- shared primitives are reused by multiple gameplay flows

The refactor is not helping if:

- the same state machine is merely spread across more files
- new helper files are one-off wrappers with no reuse
- the number of unique interaction patterns does not go down

## Immediate Next Tasks

1. Finish converting remaining direct `get_choice_text` / `suspend_interaction` sites to `choice_prompt.rs` where behavior is standard.
2. Consolidate discard / look / choose / reorder flows into clearer shared interaction phases.
3. Refactor `state_member_play_discard.rs` around explicit phases instead of continuing to grow helper fragments around it.
4. Refactor `interaction_look_choose_resolve.rs` into explicit setup/resume/mutate/finalize phases.
5. Refactor `state_member_tap_member_logic.rs` so optional confirmation and tap target selection are represented as separate phases.
