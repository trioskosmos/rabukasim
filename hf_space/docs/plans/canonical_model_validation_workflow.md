# Canonical Model Validation Workflow

## Goal

Use a cheaper model to draft canonical ability models without trusting it to be correct by default.

The model should only do:

- controlled extraction
- schema filling
- pattern matching

The codebase should do:

- validation
- lowering
- behavior verification

## Core rule

The model is allowed to be incomplete.

It is **not** allowed to invent semantics.

If unsure, output:

- `needs_review`
- `unknown_operand`
- `unknown_filter_fragment`
- `unknown_binding`
- `unsupported_pattern`

## Safe pipeline

1. Input

- Japanese text
- current pseudocode if available
- card metadata
- allowed schema
- allowed enums/dictionaries

2. Model draft

- produce canonical ability model JSON only
- optionally produce per-step confidence
- optionally produce a short explanation

3. Structural validation

- JSON parses
- schema version matches
- all step kinds are allowed
- all enum values are known
- all required fields exist
- no unknown extra keys unless explicitly allowed

4. Semantic validation

- referenced bindings exist before use
- optional steps only appear in allowed places
- `choose_one` has valid branches
- `if` blocks have a valid condition object
- slot/zone/filter/target fields use legal values
- repeated blocks do not reference out-of-scope bindings

5. Lowering validation

- canonical model lowers to backend form
- lowering does not require fallback magic
- unsupported canonical nodes are rejected cleanly

6. Behavior validation

- compare against current bytecode/backend behavior
- run targeted engine tests or scripted simulations
- compare state deltas, choices, and outcomes

7. Decision

- `accepted`
- `accepted_with_warning`
- `needs_review`
- `rejected`

## Validation rules

### A. Schema rules

- Every ability must have:
  - `trigger`
  - `steps`
- Optional top-level fields:
  - `once_per_turn`
  - `raw_text`
  - `pseudocode`
  - `notes`
- Every step must have:
  - `kind`
  - `op` or a control-flow field such as `condition`

### B. Allowed step kinds

Initial allowed set:

- `cost`
- `condition`
- `effect`
- `select`
- `assign`
- `if`
- `choose_one`
- `repeat`

Anything else is auto-rejected unless schema expands.

### C. Binding rules

- `store_as` names must be unique within a scope
- a binding must exist before use
- branch-local bindings do not escape unless explicitly promoted
- reserved names like `SELF`, `PLAYER`, `OPPONENT`, `TARGET` cannot be reused

### D. Expression rules

Allowed expression families:

- literal integer
- boolean
- enum
- reference to a prior binding
- simple arithmetic like `BASE_COST + 2`
- aggregate expressions like `SUM_COST(CHOSEN_CARDS)`

Disallow in first version:

- nested arbitrary expressions
- mixed free-form string math

### E. Filter rules

- filter objects must use named fields
- unknown filter fragments must be preserved as unresolved, not guessed
- packed filter integers are forbidden in canonical source data

### F. Control-flow rules

- `if` requires one condition object and one `then` list
- `choose_one` requires at least 2 branches
- each branch must be a list of valid steps
- `repeat` requires an explicit bound or repeat condition

### G. Review triggers

Auto-flag for human review if:

- confidence is below threshold
- unknown fields are present
- lowering falls back to opaque packed values
- behavior differs from current backend
- the ability contains nested generated abilities
- the ability contains repeated long chains

## Batch workflow

### Batch 0: Goldens

Manually author 10-20 gold-standard canonical models from real cards.

Use:

- very simple cards
- common medium cards
- ugly long cards

Purpose:

- prompt examples
- validator tests
- lowering tests

### Batch 1: Simple families

Convert only cards matching low-risk patterns:

- single effect
- two sequential effects
- no stored bindings
- no choose-one
- no optional cost

Expected examples:

- `DRAW(1)`
- `TAP_SELF`
- `DRAW(1); DISCARD_HAND(1)`

### Batch 2: Simple conditions and costs

Add:

- one precondition
- one optional cost
- one selection result

### Batch 3: Binding-heavy abilities

Add:

- `store_as`
- computed values
- later references
- aggregate count/sum operations

### Batch 4: Branching

Add:

- `if`
- `choose_one`
- conditional follow-up effects

### Batch 5: Long-tail weird cards

Add:

- repeated subroutines
- generated abilities
- unusual slot semantics
- cards that currently need custom logic

## Prompting rules for the cheap model

### What to provide

- exact schema
- allowed enum lists
- 3-5 in-family examples only
- instruction: never invent fields
- instruction: emit `needs_review` if uncertain

### What not to provide

- giant mixed examples from unrelated patterns
- packed bit-field explanations
- freedom to paraphrase semantics

### Required output shape

- JSON only
- no markdown
- no prose outside the object

## Confidence policy

The model should emit:

- `confidence`: `high`, `medium`, or `low`
- `review_reasons`: list of strings

Automatic policy:

- `high` + clean validation + clean behavior check => accept
- `medium` => accept only if behavior matches exactly
- `low` => review

## Repo implementation plan

1. Define canonical schema and pydantic validator.
2. Add enum dictionaries exported from existing metadata.
3. Add a batch conversion runner.
4. Add a verifier that lowers canonical model into current backend.
5. Add fixture-based golden tests.
6. Add review queues for failures.

## Suggested files

- `compiler/canonical_schema.py`
- `compiler/canonical_validator.py`
- `tools/batch_generate_canonical_models.py`
- `tools/verify_canonical_models.py`
- `tests/canonical_goldens/`

## Acceptance metric

A batch is considered healthy when:

- schema validation pass rate is high
- no invented fields appear
- behavior matches current backend on target cards
- review queue is mostly true edge cases, not common cards

## Main idea

Do not ask the cheap model to solve the game.

Ask it to fill a strict form, then make the code prove the form is usable.
