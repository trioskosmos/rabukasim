# Engine Refactor Master Plan

## Goal

Make the Rust engine the only authoritative runtime for gameplay while keeping the Python tree available only as compatibility and legacy support.

## Current State

- Rust is the live engine in `engine_rust_src/`.
- Python runtime code in `engine/game/` still exists and is still imported by parts of the repo.
- `engine/deprecated/` exists as the archive/legacy area.
- The largest remaining Rust work is handler decomposition in the interpreter layer.

## Principles

1. Rust owns runtime behavior.
2. Python keeps compatibility only where callers still need it.
3. Do not delete old code until usage has been mapped.
4. Prefer thin shims over disruptive rewrites.
5. Split large files by responsibility, not just by size.

## Target Architecture

### `ability.py`

Keep this module focused on ability definition and light schema-adjacent helpers.

Should stay here:

- ability dataclasses and enums
- stable serialization fields
- minimal accessors that read ability data

Should move out:

- bytecode compilation
- opcode emission
- effect wrapper generation
- condition/cost compilation
- human-readable description generation if it depends on execution details

Suggested destination:

- `compiler/ability_compile.py`
- `compiler/ability_emit.py`
- `compiler/ability_describe.py`
- `engine/models/ability_ir.py` for any stable intermediate representation

### `effect_mixin.py`

Treat this as legacy runtime glue, not the owner of gameplay logic.

Should stay here only if Python compatibility is still required:

- thin orchestration wrappers
- compatibility methods that old callers import
- minimal delegation to helper modules

Should move out:

- cost evaluation
- choice handling
- condition checks
- opcode dispatch
- state mutation logic
- effect resolution branching

Suggested destination:

- Rust handler modules in `engine_rust_src/src/core/logic/interpreter/handlers/`
- temporary Python helper modules only if a behavior has not yet been ported

### `game_state.py`

This should be a thin state container and transition coordinator, not a gameplay rules engine.

Should stay here:

- top-level state structure
- phase bookkeeping
- compatibility entry points used by tooling

Should move out:

- ability resolution internals
- opcode execution
- large action branches
- repeated helper logic that belongs to handlers or services

Suggested destination:

- Rust `GameState` and interpreter modules
- `engine/deprecated/` only for compatibility or reference copies

### `player_state.py`

This should model player-owned state data and small state mutations.

Should stay here:

- storage for zones, counters, and flags
- small invariant-preserving helpers

Should move out:

- cross-cutting game rules
- expensive lookups that depend on global engine state
- ability-specific logic

Suggested destination:

- Rust player-state implementations
- focused helper modules for any Python compatibility layer

### `serializer.py`

This should be a presentation/export layer.

Should stay here:

- serialization of game state for UI, logs, or debug output
- simple formatting helpers that do not affect gameplay

Should move out:

- any logic that mutates state
- any logic that decides outcomes
- any duplicated ability-resolution rules

Suggested destination:

- separate presentation helpers
- Rust-side serializers if the runtime needs them

### `desc_utils.py`

This should be a pure description layer.

Should stay here:

- card and ability text formatting
- readable summaries
- UI-facing translation helpers

Should move out:

- execution logic
- compilation logic
- state mutation

Suggested destination:

- a dedicated formatting/description module
- frontend-facing translation utilities if the text is only used for display

### `state_utils.py`

This should be a small utility module only.

Should stay here:

- UID helpers
- masked lookup helpers
- tiny state-mixin utilities

Should move out:

- business rules
- gameplay resolution
- compiler logic

Suggested destination:

- keep only the truly generic helpers
- migrate any gameplay-specific helpers to Rust or to domain-specific modules

### `fast_logic.py` and `numba_utils.py`

These are compatibility/performance helpers, not the long-term engine architecture.

Should stay here:

- only if they are still used by external tooling or legacy benchmarks

Should move out:

- anything that is now duplicated by Rust
- anything that is still treated as authoritative gameplay logic

Suggested destination:

- `engine/deprecated/` if they are only archival
- Rust equivalents if the behavior is still required in production

### Shared Boundary Types

Move all cross-cutting runtime data into neutral types that do not own behavior.

Examples:

- `Ability`
- `Effect`
- `Condition`
- `Cost`
- runtime context / pending interaction state

These should be data carriers, not the place where the engine lives.

### Rust

- `engine_rust_src/src/core/logic/interpreter/`
  - `mod.rs` remains the entry point.
  - `handlers/` contains focused opcode groups.
  - `flow_helpers.rs` holds shared flow utilities.
  - `state_helpers.rs` holds shared state utilities.
  - Future helper modules should be added only when they reduce coupling.

### Python

- `engine/game/`
  - remains the compatibility import surface for existing tooling.
  - should not receive new gameplay logic.
  - should gradually shrink to wrappers and compatibility helpers.
- `engine/deprecated/`
  - holds archived or quarantined legacy Python code.
  - is the right place for code that must remain available but should not be treated as active.

## Workstreams

### 1. Rust Handler Decomposition

Break interpreter handler files into smaller units.

Priority order:

1. `movement.rs`
2. `state_member.rs`
3. `flow.rs`
4. `state_score_hearts.rs`
5. `interaction_*` modules
6. `state_energy.rs`

Definition of done:

- Each split compiles.
- `mod.rs` re-exports the public handler entry points.
- The original file becomes a thin shim or a small dispatcher.
- No behavior changes beyond bug fixes.

### 2. Rust Shared Helpers

Extract repeated logic into helpers when multiple handlers depend on it.

Candidate helpers:

- effect lookup
- target-slot resolution
- discard / zone transfer utilities
- repeated choice-suspension setup
- common score / heart calculations

Definition of done:

- Helpers have one clear responsibility.
- Helpers are imported by more than one handler.
- No helper module becomes a new monolith.

### 3. Python Compatibility Cleanup

Keep Python importable, but make the role explicit.

Tasks:

- leave `engine/game/` as the public compatibility path
- keep `engine/deprecated/` for archival notes and future quarantine
- add deprecation notes where users are likely to look
- avoid adding new logic to Python runtime files

Definition of done:

- Existing import paths keep working.
- New gameplay features do not land in Python.
- Documentation clearly says Rust is the source of truth.

### 4. Import Surface Audit

Inventory every remaining `engine.game.*` import and classify it.

Categories:

1. must stay for compatibility
2. should be ported to Rust
3. should be moved behind a deprecated boundary
4. can be removed after consumer cleanup

Definition of done:

- every remaining Python import has an owner and a reason
- no unknown runtime dependencies remain

### 5. Test and Validation Strategy

Keep behavior stable while refactoring.

Required checks:

- `cargo check --manifest-path engine_rust_src/Cargo.toml`
- `cargo test --manifest-path engine_rust_src/Cargo.toml --lib --no-run`
- targeted runtime tests when a handler changes
- Python syntax checks if the environment allows the interpreter

Notes:

- Existing QA failures that predate the refactor should be tracked separately.
- A refactor should not be judged by unrelated failing tests unless the new change touches them.

### 6. Deletion Order

Do not delete first. Delete last, after usage is mapped.

Recommended order:

1. Extract logic into focused modules or Rust handlers.
2. Leave compatibility shims in place.
3. Audit consumers.
4. Remove duplicate legacy paths only when no callers remain.
5. Delete archival copies after the compatibility window closes.

## Recommended Execution Order

1. Finish splitting the remaining large Rust handler files.
2. Clean up the shared helper modules.
3. Audit the Python import surface.
4. Keep Python as compatibility only.
5. Move or archive any Python code that no longer needs to be active.
6. Update docs so the repository history matches the actual architecture.

## Files Already Touched

- `engine_rust_src/src/core/logic/interpreter/handlers/state.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/movement.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_effects.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_play.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_position.rs`

## Current Progress

- `movement.rs` is now a thin shim over `movement_draw`, `movement_discard`, `movement_deck_zones`, and `movement_swap_zone`.
- `state_member.rs` now delegates play handling to `state_member_play` and movement/positioning to `state_member_position`.
- `flow.rs` now delegates selection handling to `flow_select` and remote/meta resolution to `flow_effects`.
- The crate still compiles after each extraction.
- Full test runs still report the same pre-existing QA failures, which are tracked separately from the refactor work.
- `engine_rust_src/src/core/logic/interpreter/handlers/state_energy.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_play_live.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_select_cards.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_look_choose.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_recovery.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_helpers.rs`

## Open Questions

- Which remaining Python modules are still required by backend tools?
- Which Python modules are only used by scripts that can be migrated later?
- Should the compatibility shims stay long term or be removed after the import audit?
