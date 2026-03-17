# Cheap Model Handoff

Use this file as the single handoff prompt/reference for a cheaper model that will draft canonical JSON abilities.

## Mission

Convert card ability text into the project's strict canonical JSON schema.

Target pipeline:

`Japanese text -> canonical code model -> engine execution`

The cheaper model is only responsible for drafting the canonical JSON. It is not the final semantic authority.

## Output rules

- Output JSON only.
- Do not include explanations.
- Do not invent new field names.
- Do not invent new op names, trigger names, target names, or zone names.
- Preserve the original ability text in both `raw_text` and `pseudocode`.
- If uncertain, still output valid JSON but mark uncertainty explicitly.

## Allowed uncertainty markers

Top-level `review_reasons` and step/filter `review_markers` may use:

- `needs_review`
- `unknown_operand`
- `unknown_filter_fragment`
- `unknown_binding`
- `unsupported_pattern`

If something is ambiguous, mark it. Do not guess.

## Canonical JSON shape

Top-level object:

- `schema_version`: `"v0"`
- `trigger`: string
- `once_per_turn`: boolean
- `pseudocode`: string
- `raw_text`: string
- `confidence`: `"high"` | `"medium"` | `"low"`
- `review_reasons`: string[]
- `steps`: CanonicalStep[]

Allowed step kinds:

- `cost`
- `condition`
- `effect`
- `select`
- `assign`
- `if`
- `choose_one`
- `repeat`

Allowed expression kinds:

- `{ "kind": "literal", "value": ... }`
- `{ "kind": "reference", "name": ... }`
- `{ "kind": "binary", "op": "add"|"sub"|"eq"|"gt"|"lt"|"ge"|"le", "left": ..., "right": ... }`

Filter shape:

- `filter: { "all_of": [...], "any_of": [...], "review_markers": [...] }`

Filter clause shape:

- `{ "field": string, "op": "eq"|"ne"|"gt"|"lt"|"ge"|"le"|"contains"|"in"|"exists", "value": ... }`

## Modeling rules

- Use `select` when cards/players/members are chosen and stored for later use.
- Use `condition` for checks.
- Use `effect` for actions that change game state.
- Use `assign` for computed or stored values.
- Use `choose_one` for modal choice.
- Use `if` when the behavior is structurally conditional.
- Use `store_as` only when later steps actually refer to the result.
- Use named fields like `count`, `target`, `zone`, `duration`, `filter`, `args`.
- Do not think in terms of bytecode words, packed attrs, bit positions, or storage layout.

## Target and binding rule

- Use `target` for who an effect applies to.
- Use `store_as` only for values or selections that later steps reference.
- Never put `SELF`, `PLAYER`, or `OPPONENT` in `store_as`.
- If the target is explicit or clearly implied by a stable pattern, fill `target`.
- If the target is uncertain, leave it unset and add review markers instead of guessing.
- If a step selects something for later reuse, that is usually `store_as`, not `target`.
- If a step applies an effect to someone immediately, that is usually `target`, not `store_as`.

## Legacy/unsafe surface forms

If these appear and cannot be normalized safely, mark for review instead of guessing:

- `OPTION:` blocks
- `EFFECT: CONDITION: ...`
- chained `-> X -> Y`
- raw boolean filter strings using `OR`
- embedded ability strings such as `GRANT_ABILITY(...) {ABILITY="..."}`

## Scope for the cheaper model

Start with easy/profile-clean cards only.

Safe first-wave families:

- `DRAW(1)`
- `DRAW(1); DISCARD_HAND(1)`
- `DRAW(2); DISCARD_HAND(1)`
- `DRAW(2); DISCARD_HAND(2)`
- single-step tap / move / restriction effects
- simple constant effects without selection or bindings

Avoid converting the hard tail first:

- `LOOK_AND_CHOOSE`
- `GRANT_ABILITY`
- complex binding chains
- raw boolean filters
- mode/option legacy syntax

## Recommended first cards

- `PL!N-sd1-009-SD`
- `PL!HS-bp1-006-P`
- `PL!N-bp3-006-P`
- `PL!HS-bp5-011-N`
- `PL!-bp5-013-N`

## Examples

### Example 1

Input:

```text
TRIGGER: ON_PLAY
EFFECT: DRAW(1)
```

Output:

```json
{
  "schema_version": "v0",
  "trigger": "ON_PLAY",
  "once_per_turn": false,
  "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)",
  "raw_text": "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)",
  "confidence": "high",
  "review_reasons": [],
  "steps": [
    {
      "kind": "effect",
      "op": "DRAW",
      "count": { "kind": "literal", "value": 1 },
      "target": "PLAYER",
      "args": {}
    }
  ]
}
```

### Example 2

Input:

```text
TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(1)
```

Output:

```json
{
  "schema_version": "v0",
  "trigger": "ON_PLAY",
  "once_per_turn": false,
  "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: DRAW(2); DISCARD_HAND(1)",
  "raw_text": "TRIGGER: ON_PLAY\nEFFECT: DRAW(2); DISCARD_HAND(1)",
  "confidence": "high",
  "review_reasons": [],
  "steps": [
    {
      "kind": "effect",
      "op": "DRAW",
      "count": { "kind": "literal", "value": 2 },
      "target": "PLAYER",
      "args": {}
    },
    {
      "kind": "effect",
      "op": "DISCARD_HAND",
      "count": { "kind": "literal", "value": 1 },
      "target": "PLAYER",
      "args": {}
    }
  ]
}
```

### Example 3

Input:

```text
TRIGGER: ON_PLAY
EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}
```

Output:

```json
{
  "schema_version": "v0",
  "trigger": "ON_PLAY",
  "once_per_turn": false,
  "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: TAP_OPPONENT(1) {FILTER=\"COST_LE_4\"}",
  "raw_text": "TRIGGER: ON_PLAY\nEFFECT: TAP_OPPONENT(1) {FILTER=\"COST_LE_4\"}",
  "confidence": "high",
  "review_reasons": [],
  "steps": [
    {
      "kind": "effect",
      "op": "TAP_OPPONENT",
      "count": { "kind": "literal", "value": 1 },
      "target": "PLAYER",
      "filter": {
        "all_of": [
          {
            "field": "cost",
            "op": "le",
            "value": 4
          }
        ]
      },
      "args": {}
    }
  ]
}
```

## Batch prompt template

Use this prompt template with the cheaper model:

```text
You are converting card ability text into strict canonical JSON.

Rules:
- Output JSON only.
- Do not invent fields or enum names.
- Preserve the original text in `raw_text` and `pseudocode`.
- If uncertain, output valid JSON with low confidence and review markers.
- Do not think in terms of bytecode or packed bits.

Convert this ability text:

{{ABILITY_TEXT}}
```

## Ground truth references for the human reviewer

These are for the human workflow around the cheaper model output:

- [Canonical Schema](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_schema.py)
- [Canonical Validator](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_validator.py)
- [Canonical Hub README](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/README.md)
- [First Wave Easy Candidates](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/FIRST_WAVE_EASY_CANDIDATES.md)
