# Structured Operand IR Plan

## Problem

The current pipeline treats bytecode layout as the source of truth:

- every instruction is flattened into `op, v, a_low, a_high, s`
- meaning depends on opcode-specific bit packing
- readability comes from reverse-engineering packed fields
- adding a new operand shape means inventing another packing convention

This is compact enough for a VM, but it is a poor authoring and debugging format.

## Better direction

Make a **structured instruction IR** the primary representation, and treat packed words as one backend encoding.

Target shape:

```json
{
  "role": "effect",
  "opcode_name": "LOOK_AND_CHOOSE",
  "operands": [
    { "name": "look_count", "kind": "int", "value": 3 },
    { "name": "pick_count", "kind": "int", "value": 1 },
    { "name": "filter", "kind": "filter", "value": { "zone": "DECK", "group": 3 } },
    { "name": "reveal", "kind": "bool", "value": true },
    { "name": "destination", "kind": "enum", "value": "HAND" }
  ]
}
```

That gives us:

- readability: fields have names instead of bit offsets
- extensibility: opcodes can carry exactly the operands they need
- compatibility: the VM can still lower structured operands into compact storage
- traceability: logs can print named operands directly

## Proposed layers

1. Source IR

- lives close to pseudocode/parser output
- uses named operands
- no bit packing
- should be easy to diff in JSON

2. Lowered VM IR

- canonical `BytecodeInstruction { op, v, a, raw_s }`
- still useful as the interpreter-facing compatibility layer
- should be derived from source IR, not authored directly

3. Storage layout

- `fixed5x32-v1` for compatibility
- `compact-v2` for sparse word omission
- `tagged-v3` for optional operands
- future layouts can encode only the operands present

## Readability rule

If an operand needs explanation like "bits 8-11 mean X unless opcode Y", it belongs in source IR, not in the author-facing format.

## Recommended migration

1. Keep current parser output, but generate `StructuredAbilityIR` alongside bytecode.
2. Add named operand schemas per opcode family.
3. Lower `StructuredAbilityIR` into current VM bytecode for compatibility.
4. Update tracing/debug tools to prefer structured operands over packed integers.
5. Only then switch compiled snapshots to a new on-disk layout.

## Initial implementation

An initial structured IR helper now exists in:

- `engine/models/structured_instruction_ir.py`

It is intentionally simple:

- builds readable instructions from `Ability.instructions`, `conditions`, `costs`, and `effects`
- preserves links back to packed runtime fields when they still exist
- makes the packed fields clearly look transitional rather than primary

## Main idea

The real improvement is not just "smaller bytecode".

The improvement is:

**named operands become the source of truth, and packed words become an optimization layer.**
