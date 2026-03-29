# Action ID System Analysis

Date: 2026-03-29

This document reviews the current action ID system, how it is generated and consumed across the repo, and what would need to change if we want the policy space to be friendlier to neural-network learning.

## Short Version

The current system works as a deterministic game protocol, but it is not a good learning interface.

The main problems are:

- Several action ranges are position-based, not identity-based.
- The policy space is flattened into a large sparse index space.
- The same semantic move can map to different IDs depending on hand order or prompt context.
- The repo already has multiple consumers of these raw IDs, so the fix is not isolated to one Rust file.

The more important nuance is that the system is not "broken" for execution. It is mostly broken as a representation for learning efficiency and generalization.

## What `metadata.json` Actually Controls

`data/metadata.json` is the source of truth for the generated constants. It currently defines:

- `triggers`
- `targets`
- `opcodes`
- `action_bases`
- `phases`
- `conditions`
- `costs`

`tools/sync_metadata.py` turns that metadata into:

- `engine_rust_src/src/core/generated_constants.rs`
- `engine_rust_src/src/core/enums.rs`
- `frontend/web_ui/js/generated_constants.js`
- `engine/models/generated_metadata.py`
- `engine/models/opcodes.py`

There are also tests that enforce this sync:

- `engine_rust_src/src/database_tests.rs`
- `engine_rust_src/src/qa_verification_tests.rs` indirectly depends on the generated action layout through runtime behavior

That means any action-space redesign should treat `metadata.json` as the coordination point, not just a loose config file.

## Where The Current Action Scheme Is Used

### Rust engine

- `engine_rust_src/src/core/logic/action_gen/main_phase.rs`
- `engine_rust_src/src/core/logic/action_gen/response.rs`
- `engine_rust_src/src/core/logic/action_gen/live_set.rs`
- `engine_rust_src/src/core/logic/action_gen/mulligan.rs`
- `engine_rust_src/src/core/logic/action_gen/active_draw.rs`
- `engine_rust_src/src/core/logic/action_factory.rs`
- `engine_rust_src/src/core/logic/execution.rs`
- `engine_rust_src/src/core/logic/game_action_processor.rs`
- `engine_rust_src/src/core/logic/handlers.rs`
- `engine_rust_src/src/core/alphazero_evaluator.rs`
- `engine_rust_src/src/core/logic/constants.rs`
- `engine_rust_src/src/core/logic/game.rs`
- `engine_rust_src/src/py_bindings.rs`

### Launcher / API / UI

- `launcher/src/models.rs`
- `launcher/src/serialization.rs`
- `launcher/src/handlers/api.rs`
- `launcher/src/bin/audit_buttons.rs`
- `frontend/web_ui/js/wasm_adapter.js`
- `frontend/web_ui/js/components/ActionListView.js`
- `frontend/web_ui/js/components/CardRenderer.js`
- `frontend/web_ui/js/components/ChoiceView.js`
- `frontend/web_ui/js/ui_drag_drop.js`
- `frontend/web_ui/js/ui_tooltips.js`
- `frontend/web_ui/js/services/GameService.js`

### Python AI and tooling

- `ai/models/network.py`
- `ai/models/network_torch.py`
- `ai/utils/profile_self_play.py`
- `ai/utils/record_game.py`
- `ai/utils/verify_ai_abilities.py`
- `ai/_legacy_archive/*`

## What Is Actually Weak In The Current Design

### 1. Hand-order dependence

The main issue is in `engine_rust_src/src/core/logic/action_gen/main_phase.rs`.

The play action ID is derived from `hand_idx`, not card identity. That means the policy target changes when the same hand contents appear in a different order. This is bad for learning because:

- the same semantic card appears under many different action IDs over time
- gradients get smeared across position-dependent duplicates
- the model has to learn hand-order invariance indirectly, even though the game semantics are about the card, not the array index

This is the strongest argument for redesigning the representation.

### 2. The action space is larger than the task needs

`engine_rust_src/src/core/logic/constants.rs` defines `ACTION_SPACE = 16384`.

In practice, only a small subset of these IDs is legal at any one moment, and many action intervals are reserved for prompt variants, choice variants, or future growth.

That creates:

- a large softmax head
- a lot of masking
- a lot of learning capacity spent on impossible actions

### 3. Semantics are encoded as arithmetic ranges

`engine_rust_src/src/core/logic/action_factory.rs` and `launcher/src/models.rs` both decode actions by range math.

That works mechanically, but it means the model sees IDs like:

- `1000 + hand_idx * 10 + slot_idx`
- `8300 + slot_idx * 100 + ab_idx * 10`
- `11000 + choice_idx`

Those ranges are human-decodable, but they do not give the network any structural understanding of:

- action category
- source zone
- destination zone
- card identity
- choice type

### 4. Existing state encodings do not fully cancel this problem

The repo does have structured state encodings:

- `engine_rust_src/src/core/ai_encoding.rs`
- `engine_rust_src/src/core/alphazero_encoding.rs`
- `engine_rust_src/src/core/alphazero_encoding_vanilla.rs`

Those encodings include card features in fixed slots, which helps the model see the board in a consistent layout.

But that does not fully solve the action-side issue, because the action labels still depend on array position. The model can learn the mapping, but it is still learning a brittle representation.

## What I Think We Should Be Doing Instead

### Recommended direction: a factored action representation

The best long-term design is not "one giant ID table with nicer arithmetic."

It is a factored action space:

- action type
- source card or template
- source slot or zone
- target slot or target zone
- choice index or mode index

That can still be serialized into a single engine action if needed, but the learning interface should be structured.

### Why this is better

- It preserves semantic stability across hand shuffles.
- It lets the model reuse knowledge across similar cards and actions.
- It reduces wasted policy capacity.
- It matches the way the game actually branches: first choose intent, then source, then target, then mode.

### A practical variant

If we want to preserve the engine protocol for compatibility, the best compromise is:

- keep raw engine IDs for execution and UI compatibility
- add a separate learning-facing action encoding
- map between them with a translation layer

That translation layer should be the only thing the policy model sees.

## What Would Need To Change

### In `data/metadata.json`

We likely need to extend metadata so it can describe more than just flat bases.

Possible additions:

- action category definitions
- action factor dimensions
- stable template or card-group slots
- zone/source/target enums for learning

### In `tools/sync_metadata.py`

This script would need to generate the new action metadata alongside the existing constants.

It currently emits only flat constants and enums. For a factored policy, it should also emit:

- a canonical action schema
- per-category descriptors
- stable action vocabulary IDs for the learning layer

### In Rust action generation

The core generators will need to stop treating the action ID as the primary semantic object.

Files to rework:

- `engine_rust_src/src/core/logic/action_gen/main_phase.rs`
- `engine_rust_src/src/core/logic/action_gen/response.rs`
- `engine_rust_src/src/core/logic/action_factory.rs`

The generator should emit semantic action records first, then encode them into the legacy ID if that path is still required.

### In the launcher and API

These files decode raw IDs for display and interaction:

- `launcher/src/models.rs`
- `launcher/src/serialization.rs`
- `launcher/src/handlers/api.rs`
- `frontend/web_ui/js/wasm_adapter.js`

They will need either:

- a richer decoded action object, or
- a translation from semantic action records back to display labels

### In the AI stack

The policy heads must be updated in both Python and Rust:

- `engine_rust_src/src/core/alphazero_evaluator.rs`
- `ai/models/network.py`
- `ai/models/network_torch.py`
- `engine_rust_src/src/py_bindings.rs`

The current models assume a flat vector policy. A factored action space means:

- multiple heads, or
- a smaller canonical action vocabulary with structured masking

The legacy Python code is especially inconsistent right now:

- one model assumes `action_size = 1000`
- another transformer wrapper emits `action_size = 2000`
- the Rust evaluator still expands into `ACTION_SPACE = 16384`

That mismatch should be resolved as part of the redesign, not after it.

### In tests

Expect a wide test update across:

- `engine_rust_src/src/database_tests.rs`
- `engine_rust_src/src/qa_verification_tests.rs`
- `engine_rust_src/src/core/logic/action_gen/main_phase.rs` tests
- `engine_rust_src/src/core/alphazero_evaluator.rs` tests
- launcher and frontend mapping tests
- AI verification utilities

The current tests encode many assumptions about specific ID ranges.

## What I Would Keep

I would not throw away the current system entirely.

Keep:

- the legacy action IDs as an execution protocol
- the debug labels
- the generated constants sync pipeline
- the legal-action mask machinery

Those are useful for tooling and compatibility.

What should change is the learning-facing representation.

## Recommended Migration Path

### Phase 1

- Add a semantic action schema in metadata.
- Add a translation layer from semantic actions to legacy engine IDs.
- Keep the existing engine protocol intact.

### Phase 2

- Update the AI models to consume the semantic action schema.
- Move training targets away from the flat 16K policy when possible.

### Phase 3

- Reduce reliance on the legacy flat space.
- Keep legacy IDs only for execution, debugging, and compatibility.

## Bottom Line

The current action ID system is suitable as a compact engine protocol and debug surface.

It is not a good neural-network action representation because it bakes in hand order, overuses sparse ranges, and forces the model to learn semantics from arithmetic offsets.

If we want the learning system to improve cleanly, the next move should be to introduce a semantic, factored action layer and treat the current ID system as a compatibility layer rather than the primary model interface.
