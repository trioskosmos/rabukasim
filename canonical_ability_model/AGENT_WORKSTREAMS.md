# Canonical Ability Model: Agent Workstreams

This is the agent-ready handoff for the canonical ability system.

Use this together with:

- [SOURCE_OF_TRUTH.md](C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\canonical_ability_model\SOURCE_OF_TRUTH.md)

This file is intentionally operational:

- one workstream per agent
- clear ownership
- concrete deliverables
- clear success conditions
- minimal overlap

## Shared Ground Truth

All agents should assume the following current state unless they verify and update it:

- authored canonical entries: `614`
- hybrid preview canonical-selected entries: `614`
- checked-in runtime canonical abilities: `614`
- checked-in runtime legacy abilities: `743`
- total runtime ability slots: `1,357`
- semantic validator status: `614 / 614` valid
- current runtime artifact used by Rust tests: `canonical_ability_model/reports/fallback_runtime_preview.json`

## Non-Negotiable Definitions

Use these terms consistently:

- `authored canonical entries`: entries in `drafts/canonical_full_draft.json`
- `canonical-selected entries`: entries marked canonical by `build_hybrid_runtime_preview.js`
- `canonical runtime abilities`: runtime slots with `source == "canonical"` in `fallback_runtime_preview.json`
- `runtime safety coverage`: all runtime slots executable by canonical or legacy

Do not call anything "100%" without naming which one it means.

## Workstream 1: Build Pipeline Repair

### Goal

Make the canonical pipeline reproducible from the current repo state.

### Why this matters

Right now the documented hybrid preview rebuild is not cleanly reproducible, and that blocks trustworthy progress measurement.

### Current known issue

- `node tools/build_hybrid_runtime_preview.js canonical_ability_model/drafts/canonical_full_draft.json`
- currently fails on at least one missing compiled lookup:
  - `Could not find compiled ability PL!-PR-003-PR#null`

### Primary ownership

- `tools/build_hybrid_runtime_preview.js`
- `tools/compare_canonical_to_compiled.js`

### Expected deliverables

- hybrid preview generation completes without fatal failure for canonical-only entries
- missing compiled matches are reported as data, not process-stopping errors
- updated summary/report semantics for:
  - compiled match found
  - compiled match missing
  - parity match
  - parity mismatch
  - canonical-only entries

### Constraints

- do not change canonical policy back to parity-gated
- do not silently drop entries
- preserve existing report fields where possible, but add clearer ones if needed

### Success condition

This command succeeds:

```powershell
node tools/build_hybrid_runtime_preview.js canonical_ability_model/drafts/canonical_full_draft.json
```

And its summary clearly separates:

- canonical-selectable entries
- entries missing compiled reference data
- parity warnings

## Workstream 2: Runtime Export Repair

### Goal

Make canonical-only entries actually appear in the runtime export.

### Why this matters

This is the main gap between:

- `614` canonical-selected entries at the hybrid layer
- `470` canonical runtime abilities in the actual runtime payload

### Current known issues

- `tools/build_fallback_runtime.js` logs many canonical-only entries
- many cannot be inserted because it cannot determine `card_id`
- the script summary is misleading:
  - `canonical_ready` currently counts canonical-only attempts, not total canonical runtime abilities

### Primary ownership

- `tools/build_fallback_runtime.js`

### Secondary read-only references

- `canonical_ability_model/reports/hybrid_runtime_preview.json`
- `data/cards_compiled.json`
- any card metadata source needed to map `card_no` to runtime card ids

### Expected deliverables

- reliable mapping from canonical draft entry to runtime card and ability slot
- corrected runtime export summary
- regenerated `fallback_runtime_preview.json` with more than `470` canonical runtime abilities
- ideally `614` canonical runtime abilities if the data supports it

### Constraints

- do not break Rust deserialization compatibility
- do not remove legacy entries while canonical replacement is incomplete
- avoid inventing runtime ids if the repo has a real mapping source

### Success condition

After a clean rebuild:

```powershell
node tools/build_fallback_runtime.js
```

The resulting runtime artifact has:

- canonical runtime ability count correctly reported (614)
- no misleading summary counters
- increased canonical runtime coverage (45.2% of 1,357 slots)

## Workstream 3: Reporting and Documentation Cleanup

### Goal

Normalize all docs and reports to the same vocabulary and current verified numbers.

### Why this matters

The repo currently mixes:

- authored coverage
- runtime canonical coverage
- safety coverage

That creates bad planning inputs.

### Primary ownership

- docs under `canonical_ability_model/`

### Suggested high-priority files

- `README.md`
- `COMPLETE_VERIFICATION_WORKFLOW.md`
- `EXPANSION_READINESS_REPORT.md`
- `FINAL_VERIFICATION_REPORT.md`
- `PHASE2_PHASE3_START_HERE.md`
- `PHASE2_PHASE3_EXPANSION_PLAN.md`
- `PHASE2_NEXT_DECISION.md`
- `TEST_USAGE_ANALYSIS.md`
- `HOW_TO_TEST_CANONICAL_IN_GAME.md`

### Expected deliverables

- one consistent definition block used across docs
- removal of contradictory claims
- report language that distinguishes:
  - authored canonical entries
  - canonical-selected entries
  - canonical runtime abilities
  - safety coverage
- explicit note that some older reports describe intended policy state, not the current runtime artifact

### Constraints

- do not rewrite implementation behavior in docs to make them nicer
- docs must match checked-in artifacts and reproducible commands

### Success condition

A new reader can answer these questions from the docs without confusion:

- how many canonical entries are authored?
- how many are runtime-selectable?
- how many are in the actual current runtime artifact?
- what is still legacy?
- what does "100%" mean in each document?

## Workstream 4: Pattern Cluster Backlog

### Goal

Replace card-by-card planning with repeated-pattern planning.

### Why this matters

The runtime has many repeated ability shapes. Efficiency comes from solving top clusters, not manually walking every slot.

### Current verified duplication facts

- `1,195` total runtime ability slots
- `799` unique `trigger + raw_text` pairs
- `400` unique `trigger + effects` shapes
- `322` unique `trigger + bytecode` signatures

Examples of repeated mechanics already observed:

- `ACTIVATED + RECOVER_LIVE(1)`
- `ACTIVATED + RECOVER_MEMBER(1)`
- `CONSTANT + BOOST_SCORE(1)`
- `ON_PLAY + DRAW(1); DISCARD_HAND(1)`

### Primary ownership

- reporting scripts under `tools/` or `canonical_ability_model/scripts/`
- generated analysis under `canonical_ability_model/reports/`

### Expected deliverables

- ranked cluster report for:
  - repeated legacy ability signatures
  - repeated runtime effect shapes
  - repeated canonical-like mechanic families
- top-N opportunity table:
  - cluster shape
  - number of affected runtime slots
  - current canonical support status
  - missing semantic/operator mapping
  - estimated conversion leverage

### Constraints

- optimize for migration leverage, not just pretty summaries
- clusters should be stable enough to drive actual implementation work

### Success condition

We can point agents at a ranked list of mechanic families instead of vague "convert more cards" instructions.

## Workstream 5: Canonical Vocabulary and Semantics Expansion

### Goal

Define and standardize the missing canonical operation mappings for repeated mechanics.

### Why this matters

The backlog is blocked less by quantity than by unresolved mechanic vocabulary.

### High-priority mechanic families

- `RECOVER_LIVE`
- `RECOVER_MEMBER`
- `BOOST_SCORE`
- energy/blade manipulation
- repeated target/filter patterns
- branching conditional patterns

### Primary ownership

- canonical op vocabulary and authoring guidance
- semantic validator extensions where needed

### Suggested files

- `CANONICAL_AUTHORING_GUIDE.md`
- `SEMANTIC_TESTING_GUIDE.md`
- `tools/canonical_semantic_validator.js`
- new spec docs if needed under `canonical_ability_model/`

### Expected deliverables

- canonical mapping spec for each mechanic family
- examples of valid canonical step structures
- explicit unsupported or review-only cases
- validator rules for newly formalized patterns where appropriate

### Constraints

- do not invent arbitrary ops without documenting them
- prefer stable reusable patterns over one-off card-specific encodings

### Success condition

Agents converting backlog entries can use a shared mechanic vocabulary instead of making local guesses.

## Workstream 6: Canonical Test Expansion

### Goal

Increase confidence in canonical execution beyond the current minimal runtime tests.

### Why this matters

Current canonical validation is broad but shallow, and Rust canonical tests are still small in scope.

### Primary ownership

- `engine_rust_src/tests/canonical_semantics.rs`
- `engine_rust_src/tests/phase1_fallback_handler.rs`
- any new canonical-focused Rust test files

### Expected deliverables

- more tests by operation family
- more tests for unsupported-op fallback behavior
- more tests for canonical metadata derivation
- targeted high-value card or mechanic tests

### Constraints

- keep tests tied to actual runtime artifacts where possible
- separate "canonical direct execution" tests from "fallback behavior" tests clearly

### Success condition

Canonical behavior confidence comes from engine-level tests, not just structural JSON validity.

## Recommended Delegation Order

If you are sending multiple agents, do it in this order:

1. `Build Pipeline Repair`
2. `Runtime Export Repair`
3. `Reporting and Documentation Cleanup`
4. `Pattern Cluster Backlog`
5. `Canonical Vocabulary and Semantics Expansion`
6. `Canonical Test Expansion`

Reason:

- the first two unblock trustworthy rebuilds and accurate measurement
- the next two make the backlog legible and scalable
- the last two improve quality and execution confidence

## Minimal Agent Brief Templates

### Agent 1: Pipeline Repair

Your job is to make canonical hybrid preview generation reproducible from current repo state without changing the non-parity policy. Own:

- `tools/build_hybrid_runtime_preview.js`
- `tools/compare_canonical_to_compiled.js`

Deliver:

- successful rebuild
- non-fatal handling of canonical-only entries
- clear summary output

### Agent 2: Runtime Export Repair

Your job is to make canonical-only entries show up in runtime export instead of being dropped due to missing mapping. Own:

- `tools/build_fallback_runtime.js`

Deliver:

- corrected mapping logic
- corrected summary counters
- increased canonical runtime ability count after rebuild

### Agent 3: Docs Cleanup

Your job is to normalize the docs to the verified current state in `SOURCE_OF_TRUTH.md`. Own docs only. Do not change code.

Deliver:

- consistent terminology
- removal of conflicting numbers
- explicit separation of authored, runtime, and safety coverage

### Agent 4: Cluster Analysis

Your job is to produce the ranked pattern backlog that turns the remaining migration into mechanic-family work instead of card-by-card work.

Deliver:

- cluster report
- top leverage mechanic families
- recommendation for first conversion waves

### Agent 5: Vocabulary Expansion

Your job is to define the canonical semantic patterns for the repeated mechanics the cluster report identifies.

Deliver:

- mechanic specs
- authoring examples
- validator updates if needed

### Agent 6: Test Expansion

Your job is to strengthen canonical runtime test confidence in Rust.

Deliver:

- new or improved canonical tests
- clearer separation of direct canonical execution vs fallback execution coverage

## Stop Conditions

An agent should stop and escalate if:

- they need to invent a new runtime identifier scheme
- they discover the canonical draft does not uniquely identify ability slots
- a proposed mapping would silently overwrite existing runtime abilities
- a mechanic family cannot be modeled without a new engine capability

## Final Success Picture

This consolidation effort is done when:

- the pipeline rebuilds cleanly
- runtime export reflects actual canonical-selected entries
- docs say one consistent thing
- the remaining migration is represented as pattern clusters
- mechanic-family specs exist for the top repeated gaps
- canonical runtime test confidence is materially stronger
