# Structured Runtime Migration Plan

Goal: simplify the Python to Rust ability pipeline without breaking current behavior.

This plan is intentionally staged. We keep the current bytecode path working until each
new boundary has parity tests and a rollback point.

## Guiding rule

Do not remove an old path until the new path:

1. Produces the same behavior on a targeted test set.
2. Has a clear Rust-side consumer.
3. Has a rollback path that is one commit away.

## Phase 1: Introduce structured data as the source of truth

Scope:

- `engine/models/ability.py`
- `engine/models/structured_instruction_ir.py`
- `compiler/parser_v2.py`
- `compiler/main.py`

Work:

1. Keep `Ability.compile()` behavior unchanged for now.
2. Make sure every `Effect`, `Condition`, and `Cost` carries the runtime fields we need later:
   - `runtime_opcode`
   - `runtime_value`
   - `runtime_attr`
   - `runtime_slot`
   - `is_optional`
   - `target`
   - `params`
3. Treat the structured IR export as the new contract for inspection and debugging.
4. Add tests that snapshot the structured representation for a few representative abilities.

Pass criteria:

- Existing card compilation still works.
- Structured output is stable and human-readable.
- No runtime behavior changes yet.

Rollback:

- Remove the new structured export usage and keep the old compile path only.

## Phase 2: Move one runtime behavior at a time

Scope:

- `engine_rust_src/src/core/logic/interpreter/handlers/flow.rs`
- `engine_rust_src/src/core/logic/interpreter/mod.rs`
- `engine_rust_src/src/core/logic/models.rs`

Work:

1. Start with `ALL_PLAYERS` handling.
2. Let Rust interpret the target semantics directly for one opcode family.
3. Keep Python emitting the legacy expansion until Rust parity is proven.
4. Add regression tests for:
   - self/opponent alternation
   - multiple consecutive `ALL_PLAYERS` effects
   - target reset behavior after mixed target sequences

Pass criteria:

- Rust can execute the structured target behavior without relying on Python expansion.
- Legacy compiled bytecode still passes old tests.

Rollback:

- Re-enable the Python expansion path only.

## Phase 3: Move optional flow control into Rust

Scope:

- `engine/models/ability.py`
- `engine_rust_src/src/core/logic/interpreter/mod.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/flow.rs`

Work:

1. Keep Python jump generation in place until Rust handles optional flow correctly.
2. Add a Rust-side optional execution path that can:
   - ask for player choice
   - skip an instruction cleanly when declined
   - continue execution at the next instruction
3. Test:
   - optional cost accepted
   - optional cost declined
   - nested optional blocks

Pass criteria:

- Optional behavior matches current output.
- No `JUMP_IF_FALSE` dependency is needed for the new path.

Rollback:

- Restore the Python jump emission and keep Rust as a passive executor.

## Phase 4: Remove the semantic shim

Scope:

- `engine/models/ability_ir.py`
- `engine/models/ability.py`
- `compiler/parser_v2.py`

Work:

1. Replace intermediate semantic representations with direct `Effect` / `Condition` / `Cost` construction.
2. Keep any compatibility wrappers needed by tests or exporters.
3. Remove only the parts that no longer have consumers.

Pass criteria:

- Parser output feeds the final dataclasses directly.
- No hidden mapping layer remains in the hot path.

Rollback:

- Reintroduce the shim as a thin adapter if needed.

## Phase 5: Replace packed runtime_attr with named params

Scope:

- `engine/models/generated_packer.py`
- `engine/models/ability.py`
- `engine_rust_src/src/core/logic/models.rs`
- `engine_rust_src/src/core/logic/interpreter/handlers/*`

Work:

1. Add named param access on the Rust side.
2. Keep packed fields available until every consumer has moved.
3. Remove bit-packing only after the last Rust caller stops using it.

Pass criteria:

- Rust reads named params directly.
- Bit-packing is no longer required for runtime correctness.

Rollback:

- Restore packed-field reads from the existing compatibility fields.

## Recommended first commit

If we want the safest possible start, the first commit should only do this:

1. Add or tighten structured IR export coverage.
2. Add golden tests for:
   - optional costs
   - `ALL_PLAYERS`
   - constant-trigger condition handling
3. Leave `Ability.compile()` behavior unchanged.

That gives us a foundation we can trust before we touch control flow or target expansion.
