# Method Evaluation

## Question

Can the canonical draft + verification method realistically replace the current multi-layer pseudocode-heavy workflow?

## Short answer

Yes, as the **authoring and validation method**.

Not yet as the **runtime authority**.

## Why the answer is yes

The new method is already proving useful in ways the old layered pseudocode pipeline is not:

1. It creates one explicit structured representation instead of spreading meaning across:
   - pseudocode
   - parsed ability objects
   - conditions/effects objects
   - bytecode

2. It gives us measurable verification:
   - structural validation
   - bridge matching against current compiled meaning
   - fast iteration

3. It exposes uncertainty honestly with review markers instead of hiding it inside parser heuristics.

4. It is already fast enough to use in an iterative workflow.

## Current evidence

### Existing pseudocode pipeline

- `1356` compiled abilities in the current runtime data
- `1138` already fit the stricter standard pseudocode profile
- `218` still rely on legacy/non-standard pseudocode forms

This shows the old pseudocode surface is still workable, but it is not stable enough to be the long-term semantic authority.

### Current canonical draft method

Run:

```powershell
node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json
```

Current result:

- `614` total entries
- `609` structural validation pass
- `5` structural validation fail
- `607` bridge-supported
- `277` bridge matches
- `332` bridge mismatches

This is not enough to replace the old pipeline yet, but it is enough to show the method is real and testable.

### Current hybrid rollout preview

Run:

```powershell
node tools/build_hybrid_runtime_preview.js canonical_ability_model/drafts/canonical_full_draft.json
```

Current result:

- `614` total entries
- `277` would use the canonical path today
- `337` would fall back to the existing legacy compiled/pseudocode path

This is the first real proof that the method can be used inside the current system as a staged rollout, not only as a future design target.

## Why this is better than the old layered approach

The old approach relies on parser and compiler layers silently compensating for:

- inline conditions
- option block variants
- raw boolean filters
- chained destinations
- alias-heavy pseudocode forms

That makes correctness hard to inspect.

The canonical method is better because:

- each step is explicit
- bindings are explicit
- targets are explicit
- failures are measurable
- fixes can be targeted by mismatch family

## Why it still cannot fully replace the old path yet

The remaining problem is semantic agreement, not speed and not raw syntax.

The current draft still misses many compiled behaviors because:

- some condition structures are still malformed
- some medium/hard abilities are over-abstracted or under-normalized
- select/binding/optional-cost semantics are not always aligned with current compiled meaning

So today:

- good enough to use as the new drafting/cleanup/verification layer
- not good enough to replace the current engine input end-to-end

## Speed question

The process is now fast enough to be practical.

Full check:

```powershell
node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json
```

Unique-mode check:

```powershell
node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json --unique
```

Current timing is around a fraction of a second, so verification speed is no longer the blocker.

## Recommendation

Use this method to replace the old layered pseudocode workflow in stages:

1. Keep old compiled behavior as the runtime truth for now.
2. Use canonical drafting + bridge verification as the new migration workflow.
3. Raise bridge-match coverage on easy and medium families.
4. Only after that, move metadata/enums and runtime authority toward the canonical model.

## Bottom line

This method is useful.

It is already better than the old layered pseudocode workflow for:

- explicitness
- debuggability
- measurement
- iterative fixing

But it is not finished enough yet to fully replace the old runtime pipeline.
