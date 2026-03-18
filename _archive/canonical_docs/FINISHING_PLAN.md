# Finishing Plan

This file explains how to finish the canonical ability model migration from the current draft state.

## Goal

Reach a point where we can honestly say:

`Japanese text -> canonical code model -> engine execution`

with one semantic translation layer and real verification.

## Current state

What is already true:

- the canonical schema exists
- the cheaper model can draft canonical JSON
- the verification loop is fast
- the draft now mostly passes structural validation
- some cards already bridge-match the current compiled meaning

What is not true yet:

- the draft is not semantically reliable enough
- bridge-match coverage is still low
- canonical JSON is not executing in the engine
- the old pipeline is still the runtime authority

## Current measured status

Run:

```powershell
node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json
```

Current baseline:

- `614` total entries
- `609` structural validation pass
- `5` structural validation fail
- `609` bridge-supported
- `20` bridge matches
- `589` bridge mismatches

Interpretation:

- syntax is mostly under control
- semantics are still the real problem

## What remains

There are four remaining categories of work.

### 1. Fix the last structural defects

These are the easiest remaining problems.

Current pattern:

- `invalid_step_kind` under paths like `steps[0].condition[0]`

Meaning:

- some entries still encode condition payloads in the wrong shape

Done when:

- the draft reaches zero structural validation failures

### 2. Raise bridge matches aggressively

This is the main task.

Right now the draft is often:

- schema-valid
- still semantically wrong for the current compiled form

That means we need to target the biggest mismatch families.

Priority order:

1. simple chained effects
2. optional costs and success bindings
3. `if` / condition structure
4. select-and-use-target patterns
5. medium card families

Do not start with the hard tail.

### 3. Tighten the cheaper-model fix loop

The cheaper model should not rewrite everything blindly.

Use it to fix one mismatch family at a time:

- target vs `store_as`
- `(Optional)` handling
- semicolon effect splitting
- condition structure
- simple select bindings

After each pass:

1. rerun the draft test
2. compare bridge-match count
3. inspect 5-10 changed cards

If bridge matches do not go up, the pass was not good enough.

### 4. Add actual execution proof

Structural comparison is not enough.

Before declaring success, we need at least one real path where:

- a canonical entry is lowered into executable runtime behavior
- that behavior passes a real test

That is the final proof step.

## Recommended order

Follow this order exactly.

### Phase A: Structural cleanup

1. eliminate the remaining `invalid_step_kind` failures
2. rerun the draft test
3. lock in a zero-structural-failure baseline

### Phase B: Easy semantic wins

1. focus only on the easy/profile-clean pool
2. improve bridge matches for:
   - `DRAW`
   - `DRAW + DISCARD_HAND`
   - simple tap effects
   - simple single-target effects
3. rerun the draft test

Target:

- get bridge matches meaningfully above the current baseline before touching harder families

### Phase C: Medium family cleanup

Focus on:

- optional costs
- success bindings like `SUCCESS`
- `if` condition structure
- select-then-use-target patterns

Only move here once easy cards are stable.

### Phase D: Runtime proof

1. pick one already bridge-matching easy card
2. add a canonical-to-runtime execution path for that card
3. run a real rule or regression test through the canonical path

That is the finish line for “the new system works.”

## Rules for judging progress

Do not use “issue count” alone as the success metric.

Use these metrics in order:

1. structural validation failures
2. bridge-supported count
3. bridge-match count
4. real execution proof

The important metric is not “looks cleaner.”
The important metric is “more cards match current behavior honestly.”

## Suggested operating loop

For every fix batch:

1. apply the fix
2. run:

```powershell
node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json
```

3. record:

- structural validation pass/fail
- bridge match count
- bridge mismatch count

4. inspect a few cards manually
5. keep the change only if it improves real metrics

## What not to do

- do not declare success because pydantic passes
- do not declare success because review markers disappeared
- do not loosen the bridge so far that semantic mismatches vanish artificially
- do not change metadata/enums first

Metadata and enum cleanup should happen after the canonical model is stable enough to trust.

## When metadata/enums should change

Only after:

- the canonical model is stable
- common operations/targets/conditions are consistently represented
- bridge-match coverage is strong enough to trust the representation

Then:

- semantic metadata should describe named operations and concepts
- backend metadata can still describe bytecode/storage layout separately

## Best next action

Right now the best next action is:

1. fix the remaining five structural validation failures
2. improve the biggest mismatch family in the easy pool
3. rerun the draft test

That is the shortest path to turning this from a promising draft into a system we can actually rely on.
