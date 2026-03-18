# Verification Report

## Current Status

We now have a real **hybrid preview path**:

- use `canonical` when the draft:
  - passes structural validation
  - is bridge-supported
  - matches the compiled legacy meaning
- otherwise fall back to the existing `legacy` compiled/pseudocode path

This is no longer just a future migration idea. It is testable today.

## Commands

Full draft verification:

```powershell
node tools/test_normalized_canonical_draft.js canonical_ability_model/drafts/canonical_full_draft.json
```

Hybrid rollout preview:

```powershell
node tools/build_hybrid_runtime_preview.js canonical_ability_model/drafts/canonical_full_draft.json
```

Unique-shape hybrid preview:

```powershell
node tools/build_hybrid_runtime_preview.js canonical_ability_model/drafts/canonical_full_draft.json --unique --out canonical_ability_model/reports/hybrid_runtime_preview.unique.json
```

## Latest Results

### Bridge verification

- total entries: `614`
- canonical validation pass: `609`
- canonical validation fail: `5`
- bridge-supported: `607`
- bridge matches: `277`
- bridge mismatches: `332`

### Hybrid preview

- total entries: `614`
- canonical selected: `277`
- legacy fallback: `337`
- validation failures forcing fallback: `5`
- bridge mismatches forcing fallback: `332`

### Unique-shape hybrid preview

- unique entries: `608`
- canonical selected: `271`
- legacy fallback: `337`

## What This Means

If we shipped a **canonical-first with legacy fallback** resolver today:

- about `45.1%` of the drafted entries would already take the canonical path
- the remaining `54.9%` would safely continue through the old compiled/pseudocode path

That is enough to evaluate the method in the current system without replacing the runtime authority yet.

## Output Artifacts

Hybrid preview report:

- [canonical_ability_model/reports/hybrid_runtime_preview.json](C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\canonical_ability_model\reports\hybrid_runtime_preview.json)

Unique-shape hybrid preview report:

- [canonical_ability_model/reports/hybrid_runtime_preview.unique.json](C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\canonical_ability_model\reports\hybrid_runtime_preview.unique.json)

Each entry records:

- `source`: `canonical` or `legacy`
- `fallback_reason`
- `canonical_plan` when canonical is selected
- `legacy_plan` when fallback is required

## Performance

Current verification speed is no longer a blocker.

- bridge verification: about `0.30s`
- hybrid preview build: about `0.60s`

## Remaining Blockers

The main remaining blockers are semantic, not infrastructural:

- malformed condition structure in a small number of entries
- bridge mismatches on medium/hard abilities
- gaps between canonical modeling and legacy compiled effect structure

## Bottom Line

Yes, we can actually use this method now in a staged way:

- `canonical` first where it is already proven
- `legacy` fallback everywhere else

That lets us test the new approach inside the current system instead of waiting for a full migration.
