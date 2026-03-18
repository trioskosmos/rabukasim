# First Wave Easy Candidates

This file tracks the lowest-friction migration pool inside the current standard-profile pass set.

## Current count

- `73` abilities currently classify as `easy`
- source: `node tools/classify_standard_profile_candidates.js`

Important: `easy` here means:

- passes the current standard pseudocode profile
- does not trip the current medium/hard complexity heuristics

It does **not** mean already migrated or already runtime-proven from canonical form.

## Recommended first cards

These are good first cards because they are simple, readable, and representative:

1. `PL!N-sd1-009-SD`

- [draw one](/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/draw_one_on_play.json)
- raw text:

```text
TRIGGER: ON_PLAY
EFFECT: DRAW(1)
```

2. `PL!HS-bp1-006-P`

- [draw then discard](/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/draw_then_discard_on_play.json)
- raw text:

```text
TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(1)
```

3. `PL!N-bp3-006-P`

- raw text:

```text
TRIGGER: ON_PLAY
EFFECT: TAP_SELF
```

4. `PL!HS-bp5-011-N`

- raw text:

```text
TRIGGER: ON_PLAY
EFFECT: DRAW(1)
```

5. `PL!-bp5-013-N`

- raw text:

```text
TRIGGER: ON_PLAY
EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}
```

## Good first-wave families

These appear repeatedly in the easy pool:

- `DRAW(1)`
- `DRAW(1); DISCARD_HAND(1)`
- `DRAW(2); DISCARD_HAND(1)`
- `DRAW(2); DISCARD_HAND(2)`
- single-step tap / move / restriction effects
- simple constant effects without selection or bindings

## Notable exclusions

Some things may look simple but are intentionally not in the easy pool:

- abilities with `COST:`
- abilities with `CONDITION:`
- abilities with explicit selections or counts
- abilities with stored bindings like `-> TARGET`
- `LOOK_AND_CHOOSE`
- `GRANT_ABILITY`

Those are still good candidates, just not first-wave easy ones.

## Repro

```powershell
node tools/classify_standard_profile_candidates.js
```
