# Why the remaining tests were still failing

This note explains the remaining failures that showed up in the last full Rust suite runs and why they were not already fixed.

The short version:
- The ability system was split across multiple representations for too long.
- The live engine uses instruction/frame decoding, but a lot of tooling, debug output, and tests still talk in legacy bytecode terms.
- Several failures are not isolated bugs. They are shared flow bugs that affect nested response windows, discard/recovery handling, or deck-top gating.
- Those shared bugs require rule-level confirmation and cross-cutting engine changes, not one-line fixes.

## Failure clusters

### `q201` and `q202`

These tests fail when the engine loses the nested response window after an on-play ability starts a follow-up cost or choice.

What the failure means:
- The game should remain in `Response` while the inner ability is still waiting on a discard/choice.
- Instead, the engine sometimes collapses back to `Main` too early, or resumes the wrong pending interaction.

Why it was not fixed immediately:
- The bug sits in the interaction stack / resumption path, not in a single card handler.
- Fixing it safely requires preserving the pending interaction while still allowing the outer ability to complete.
- That means touching the shared flow logic, then re-checking several cards that all use the same path.

### `q214`

This failure is in the recovery-cost path for live recovery.

What the failure means:
- The recovery ability should treat the cost as zero-energy in the relevant case.
- The engine still appears to be charging or resolving the frame in the wrong order.

Why it was not fixed immediately:
- Recovery uses the same shared frame resolver as other movement and discard flows.
- The behavior depends on whether the source frame is interpreted as a cost, a follow-up effect, or a gated activation condition.
- I needed to verify the actual rule text and frame metadata before changing that path, because the wrong fix would break other recovery and discard cards.

### `q234`

This failure is about Kinako’s deck-top cost requirement.

What the failure means:
- The card should not be activatable when the deck is too small.
- The runtime frame view was lossy, so the obvious frame dump looked empty or generic even though the authored sparse instruction data still contained the real deck-top marker.

Why it was not fixed immediately:
- The engine had two competing sources of truth: the lossy runtime frame view and the richer sparse instruction metadata.
- The actual gating rule had to be derived from the richer instruction source, not the decoded runtime frame alone.
- That made the fix easy to get wrong if rushed.

### `8844` and similar stage-state failures

These tests fail around stage composition and discard tracking.

What the failure means:
- The engine is not consistently tracking which names or categories are present on stage when later effects check for them.
- Some branches also depend on whether discarded cards are being counted in the correct zone.

Why it was not fixed immediately:
- These are shared state bookkeeping problems, not one card issue.
- They overlap with other pending interaction and recovery bugs, so a local tweak can hide the symptom but still leave the state model inconsistent.

### `q132`, `card_579`, `card_275`, `pb1_001_r`, `cost_13`, `mulligan`, and the remaining repros

These failures are broader rule-parity or state-transition cases.

What they mean:
- Some are pure rule interpretation problems.
- Some are interaction ordering problems.
- Some are tests that expose the wrong notion of when a cost is optional, when a trigger should suspend, or what zone/state should be sampled.

Why they were not fixed immediately:
- They are not all caused by the same code path.
- Several depend on the same underlying response and frame-resolution machinery, so fixing them piecemeal would risk regressions.
- I had to narrow the system to one canonical instruction path first, otherwise every fix risked being applied in the wrong representation.

## Why I had not already fixed them

The main reason is that the codebase was still carrying multiple overlapping mental models:
- authored card text
- Python semantic IR
- structured instruction IR
- runtime frame decoding
- legacy bytecode-compatible helpers

That made it easy to patch the visible symptom while leaving the real source of truth untouched.

The second reason is that several failures are coupled:
- `q201` and `q202` point to the same response-window bug.
- `q214` and some discard/recovery repros point to the same flow/resumption area.
- `q234` depends on whether the engine reads the canonical instruction metadata or a lossy runtime frame.

Because of that, “fix one failing test” was often the wrong strategy. The safer approach was to:
1. identify the canonical instruction model,
2. remove legacy Python IR from the live path,
3. make debugging speak the same language as the runtime,
4. then re-run the full suite and fix the remaining shared flow bugs from there.

## What this file is not

This is not a claim that the remaining failures are impossible to fix.
It is simply the honest reason they were still present when this note was written:
- some were still under investigation,
- some required rule verification,
- and some were waiting on the engine and UI to stop presenting legacy bytecode terminology as the default model.

