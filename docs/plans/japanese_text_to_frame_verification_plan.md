# Japanese Text to Frame Verification Plan

This document defines the working plan for building a reliable Japanese text -> semantic frame verifier for the ability system.

The goal is not to wire a new parser directly into gameplay. The goal is to make the authored ability source and the runtime behavior line up well enough that we can tell, for any card, whether the problem is:

- the Japanese text parser missing a rule family
- the authored frame source being wrong or incomplete
- the runtime still relying on a fallback or heuristic

## What the tests should prove

Card tests should stay behavior-first.

They should verify things like:

- the correct prompt appears
- the correct prompt options are available
- the ability moves cards to the right area
- the ability gives the right bonuses or penalties
- the ability respects its condition gates
- the ability does nothing when the condition is not met

They should not be framed as opcode-shape tests unless the test is specifically about parser or hydration behavior.

## Current source of truth

For parser and verification work, use:

- `data/ability_frame_source.json`

This is the authored source we should compare against the Japanese text.
The human-editable entry should be text-first, with `primary_text_jp` at the top of each ability record.

Do not use `data/cards_compiled.json` as the primary comparison target for parser work. That file is a compiled runtime artifact and may already reflect runtime lowering.

## Current system shape

The live ability pipeline is split across a small set of layers:

1. Japanese printed text in the card data
2. authored sparse frame source in `data/ability_frame_source.json`
3. compile-time lowering into runtime frame programs
4. interpreter execution
5. response/action generation and prompt resolution

This means the system can be correct in one layer and wrong in another. We need a verifier that can say which layer is responsible without depending on a hidden hydration bridge.

## Verification model

The verifier should work in two passes:

### Pass 1: text -> semantic intent

Parse the Japanese text into a semantic intent record.

The intent record should describe:

- trigger family
- cost family
- condition family
- action family
- source zone
- destination zone
- counts
- optionality
- selection family
- group / unit / card-type constraints

This parser does not need to understand every sentence perfectly at first.
It does need to classify the common families consistently and explicitly mark unknown pieces.

### Pass 2: source frame -> semantic intent

Normalize the authored frame source into the same semantic shape.

This is not a gameplay executor. It is a comparison model.

The normalizer should capture:

- opcodes
- required parameters
- source and destination zones
- selection family
- count family
- condition family
- prompt family

## Comparison rule

After both sides are normalized, compare:

- text intent
- frame intent

The result should be one of:

- `match`
- `parser_gap`
- `frame_gap`
- `ambiguous`
- `needs_review`

## What to avoid

- Do not use the current frame shape as the only truth source.
- Do not assume every current frame is right.
- Do not silently infer missing semantics when the frame is malformed.
- Do not turn behavior tests into opcode-shape tests.
- Do not wire the parser directly into runtime gameplay until the verifier is stable.

## Initial semantic families to support

These are the first families the parser should understand well enough for a full sweep:

- draw and discard
- optional discard costs
- look / reveal / choose from deck
- recover from discard
- move to deck top / bottom
- position change / move member
- select member / select cards
- count stage / hand / discard / energy / success pile
- energy charge / activate energy
- blade / heart / score modifiers
- baton-style conditional play/recovery

## Work checklist

### Source and documentation

- [x] Identify `data/ability_frame_source.json` as the comparison source for parser work
- [x] Keep card behavior tests focused on prompts, movement, bonuses, and condition gating
- [ ] Define the canonical semantic intent schema for the parser
- [ ] Define the same semantic intent schema for frame normalization

### Parser

- [ ] Replace brittle phrase matching with family-based Japanese text classification
- [ ] Normalize trigger, cost, condition, action, and selection families
- [ ] Mark unknowns explicitly instead of guessing
- [ ] Emit a per-card discrepancy report for the full source set

### Frame normalization

- [ ] Normalize source-frame opcodes into semantic families
- [ ] Detect missing required metadata for each family
- [ ] Distinguish malformed authored frames from parser gaps

### Verification

- [ ] Run a full sweep over all abilities using the authored source file
- [ ] Classify every mismatch by cause
- [ ] Keep the report stable enough to track progress over time

### Runtime cleanup

- [ ] Reduce or remove runtime text heuristics once the verifier covers the common families
- [ ] Remove compatibility branches that are no longer needed
- [ ] Keep only the fallbacks that are required for legacy or genuinely ambiguous cards

## Success criteria

This work is good enough when:

- most cards are classified without manual inspection
- remaining failures are clearly labeled as parser gaps or frame gaps
- behavior tests remain focused on real gameplay outcomes
- we can delete more heuristic code with confidence

## Notes

The key idea is to stop asking the codebase to “just know” what a card means.
Instead, each layer should explain its own interpretation clearly enough that we can compare them and identify the broken layer quickly.
