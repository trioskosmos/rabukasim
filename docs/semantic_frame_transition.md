# Semantic Frame Transition

This note tracks the move from bytecode-first ability handling to semantic frame execution.

The transition is not complete. The engine already understands more semantic metadata, but some paths still fall back to packed runtime fields or bytecode-style assumptions.

## Goal

The goal is for the authored frame data to describe ability intent directly:

- what the ability does
- which targets it uses
- which heart or color it refers to
- which conditions must be true
- which values are execution state versus optional metadata

Bytecode remains a compatibility format, not the primary source of truth.

## Current Direction

The working rule is simple: if a code path can answer from semantic data, it should.

That means prefer:

- `params`
- `frame_program`
- semantic frame variants
- explicit target metadata
- named filters and labels

Only fall back to legacy packed fields when the authored semantic data is genuinely absent.

## What Is Already In Place

### Semantic heart decoding

Heart labels are decoded through the shared helper in:

- `engine_rust_src/src/core/logic/heart_semantics.rs`

That helper is used by the state scoring, rule, performance, and JSON condition paths so heart handling no longer depends on ad hoc bit interpretation.

### Frame reconstruction keeps authored metadata

The frame conversion paths in:

- `engine_rust_src/src/core/logic/models.rs`
- `engine_rust_src/src/core/logic/card_db.rs`

now preserve more semantic detail instead of overwriting it with runtime-only state.

Important constraints:

- semantic frames keep their `params`
- zero is not treated as missing unless the schema says it is
- derived effects are only substituted when they still match the original effect count

### Raw conditions use semantic payloads

The `COUNT_MEMBER` branch in:

- `engine_rust_src/src/core/logic/interpreter/conditions/json_params.rs`

was added to handle named-member and filtered-count conditions correctly.

This matters for cases such as:

- checking for both Kanon and Keke
- counting named members
- matching a semantic filter against a specific group

Related target-player handling for count-style conditions must continue to derive the target from semantic params rather than defaulting to self.

## Known Constraints

These are the guardrails that should not regress while the transition continues:

1. Do not regenerate `data/ability_frames.json` from compiled cards.
1. Preserve authored frame metadata such as `is_once_per_turn` and choice flags through codec paths.
1. Treat `0` as a valid value when the schema allows it.
1. Keep semantic and runtime representations aligned during conversion.
1. Make tests assert meaning, not packed encoding.

The repo memory notes also capture two recurring failure modes:

- count-style conditions must respect `cond.params["target"]` for self versus opponent
- optional cost skip jumps must account for synthetic jumps inserted later in the emission pass

## Where The Remaining Work Lives

The remaining bytecode-era seams are concentrated in:

- `engine_rust_src/src/core/logic/action_gen/response.rs`
- `engine_rust_src/src/core/logic/interpreter/suspension.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/*`
- `engine_rust_src/src/core/logic/interpreter/conditions/*`
- `engine_rust_src/src/core/logic/performance_requirements.rs`
- `engine_rust_src/src/core/logic/rules.rs`

Those are the places where the engine still chooses between semantic frame metadata, packed filter fields, and runtime compatibility fields.

## Transition Checklist

### Conditions

- Parse semantic params first.
- Resolve target player, group, and color semantically.
- Keep the legacy raw-field fallback narrow and explicit.

### Selection

- Read target lists from semantic metadata.
- Prefer semantic filter names over packed masks.
- Only generate packed masks for legacy compatibility.

### Heart logic

- Decode heart type from semantic params first.
- Use color masks only as fallback support.
- Keep any "any color" handling explicit.

### Frame conversion

- Preserve `params` and structured slots.
- Avoid lossy conversion from `Effect` back to frame data.
- Do not rewrite runtime fields unless the semantic form genuinely needs it.

### Tests

- Add one success test and one failure test for each fixed semantic rule.
- Prefer data-driven tests that read compiled card metadata.
- Update bytecode-era assertions to check semantic meaning instead of encoding.

## Current Status

The engine is partially semantic now:

- heart decoding is semantic-first
- `COUNT_MEMBER` is semantic-first
- frame reconstruction preserves more metadata

Still to do:

- remove more packed-mask selection fallbacks
- convert the remaining condition handlers
- reduce raw attr guessing in interaction resolution
- tighten serialization so semantic frames round-trip without loss

## Related Plan

The implementation plan for the execution path is tracked in:

- `docs/plans/semantic_frame_execution_plan.md`

That plan covers the interpreter-side refactor separately from this semantic-transition note.
