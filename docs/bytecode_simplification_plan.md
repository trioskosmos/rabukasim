# Bytecode Simplification Plan

## Goal

Keep the useful part of bytecode, a deterministic execution stream, but remove the bitpacking and remove the extra semantic layers we built on top of it.

## Principles

- One instruction model.
- One execution path.
- One choice metadata source.
- No parallel runtime-plan stack.
- No bitfield archaeology for authors or debuggers.

## Target Shape

1. Pseudocode remains the authoring input.
2. The compiler lowers pseudocode into one explicit instruction IR.
3. That IR uses named enums and explicit fields instead of packed bit positions.
4. Rust executes that IR directly.
5. Packed bytecode exists only as a compatibility export or import format, not as the thing we think in.

## What To Remove

- Separate `runtime_plan` as a second semantic representation.
- Duplicate `choice_flags` and `choice_count` derivation paths.
- Launcher and Rust heuristics that infer interaction state from legacy packed values.
- Any code that needs both the old and new models to understand a single ability.

## What To Keep

- The actual opcode sequence ordering.
- The existing Rust handler family that already knows how to resolve effects.
- The parser that turns text into structured ability objects.
- Compatibility conversion for old data until migration is complete.

## Implementation Steps

1. Revert to the bytecode-only baseline and keep the tree stable.
2. Define a single explicit instruction IR with enum-backed fields.
3. Make the compiler emit that IR directly.
4. Add one serializer that can still emit packed bytecode if needed.
5. Make Rust consume the explicit IR first.
6. Keep bytecode only as a fallback boundary, not as a parallel architecture.
7. Add regression tests for choice-heavy cards before removing compatibility code.
8. Delete duplicated semantic or runtime-plan plumbing once parity is proven.

## Success Criteria

- A card can be inspected in one place and understood without bit math.
- Pending interactions render from one prompt contract.
- The Rust engine has one normal path for execution.
- Bytecode is an implementation detail again, not a second architecture.

## Practical Rule

If a new layer does not remove an old layer, it should not survive long-term.
The next simplification should collapse structure, not add another translation pass.
