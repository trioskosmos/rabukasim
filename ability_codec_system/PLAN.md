# Ability Codec Plan

This is the roadmap toward a writable ability system.

The target is not “better bytecode authoring.”
The target is a semantic ability format that can be written directly, validated directly, and then compiled into bytecode as a serialization step.

## End Goal

The final authoring flow should look like this:

1. Write a card in semantic form.
2. Validate the semantic shape.
3. Compile it into bytecode.
4. Load that bytecode in the engine.
5. Use the reverse decoder only for inspection, debugging, and regression tests.

That means writers should think in:

- trigger
- costs
- conditions
- effects
- choice blocks
- branch bodies
- targets
- flags
- named parameters

Writers should not need to think in:

- jump offsets
- packed bit layouts
- raw word ordering
- opcode tables unless they are looking at the reference guide

## What Already Exists

- Sparse frame decoding from compiled cards.
- Metadata-backed naming for opcodes, conditions, costs, triggers, targets, and slots.
- Negated `1xxx` frames represented explicitly as negated condition wrappers.
- Branch-aware choice extraction for `SELECT_MODE`.
- A reversible bytecode codec for inspection and preservation.

## What Is Still Missing

### 1. A writable semantic schema

This should be the thing authors write.

It needs to support:

- `trigger`
- `once_per_turn`
- `costs`
- `conditions`
- `effects`
- `choices`
- `branches`
- `targets`
- `filters`
- `flags`
- named numeric parameters

The schema should be readable and stable.

### 2. A canonical normalized form

The same card should always normalize to the same semantic shape.

Normalization should:

- fill defaults
- canonicalize targets
- canonicalize flag names
- sort or preserve lists only where ordering is meaningful
- expand short forms into explicit forms
- keep branch bodies nested

### 3. A semantic opcode reference

We need a generated guide for each opcode family that answers:

- what it means semantically
- which fields exist
- which fields are required
- which fields are optional
- what defaults are assumed
- whether it supports negation
- whether it supports branching
- how it maps to bytecode words

This is the “writing guide,” but it should describe semantics, not bit packing.

### 4. A full semantic-to-bytecode compiler

The compiler should take the writable schema and produce the current runtime layout.

It must know how to:

- pack values
- pack attrs
- pack slots
- emit branch tables
- generate jumps from nested choice blocks
- emit negated condition wrappers
- preserve the exact runtime meaning of the current cards

### 5. Validation

The writable schema needs strong validation so authors fail fast.

Validation should catch:

- missing required fields
- wrong target types
- invalid filters
- broken branch counts
- unsupported opcode combinations
- illegal optional/cost combinations
- bad negation placement

### 6. Round-trip tests

Every supported pattern should prove:

- semantic form -> bytecode -> semantic form
- bytecode -> semantic form -> bytecode
- branch blocks preserve option ordering
- negated conditions preserve meaning
- common parameter changes do not alter unrelated bits

## Migration Strategy

### Phase 1

Keep the sparse frame index as the inspection layer.

### Phase 2

Generate the opcode reference from `metadata.json` plus compiled examples.

### Phase 3

Expand the semantic schema for the common card shapes:

- plain effect
- optional cost
- simple condition
- negated condition
- modal choice
- branching effect
- multi-effect sequence

### Phase 4

Make the semantic form the primary writable input for new cards.

### Phase 5

Use bytecode only as the emitted runtime artifact, with the reverse decoder serving inspection and verification.

## What We Need to Keep Stable

- The runtime must keep receiving valid bytecode.
- The reverse decoder must stay exact enough for regression checks.
- The semantic schema must not expose layout details to writers.
- A small change in a card parameter should not require a new mental model from the author.

## Practical Deliverables

1. A generated opcode reference document.
2. A semantic card schema file.
3. A compiler from semantic cards to bytecode.
4. A reverse decoder from bytecode to semantic cards.
5. Regression tests for the common ability families.
6. Example cards written in the new semantic form.

## Success Criteria

The new system is done when:

- a new card can be written without touching raw bytecode
- a small variant of an old card is easy to express
- branch cards stay readable
- negated conditions stay obvious
- the engine still gets the same runtime bytecode it expects

