# Cheap Model Fix Draft

Use this file as the single prompt/reference for fixing the current canonical draft.

## Task

You are fixing an existing canonical JSON draft for card abilities.

Your job is **not** to invent a new system.
Your job is to rewrite draft entries so they follow the canonical schema and the project rules more strictly.

Target pipeline:

`Japanese text -> canonical code model -> engine execution`

## Output contract

- Output valid JSON only.
- Do not include explanations.
- Preserve:
  - `card_no`
  - `schema_version`
  - `trigger`
  - `once_per_turn`
  - `pseudocode`
  - `raw_text`
- Keep `raw_text` as the actual Japanese card text.
- Keep `pseudocode` as the normalized pseudocode form.
- If uncertain, keep the entry valid but add:
  - low confidence
  - `review_reasons`
  - step/filter `review_markers`

## Core rule

Do not guess.

If a step cannot be safely normalized, mark it for review instead of inventing semantics.

Allowed review markers:

- `needs_review`
- `unknown_operand`
- `unknown_filter_fragment`
- `unknown_binding`
- `unsupported_pattern`

## Canonical schema rules

Top-level fields:

- `schema_version`: `"v0"`
- `trigger`: string
- `once_per_turn`: boolean
- `pseudocode`: string
- `raw_text`: string
- `confidence`: `"high"` | `"medium"` | `"low"`
- `review_reasons`: string[]
- `steps`: array

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

## Critical target/binding rules

- Use `target` for who an effect applies to.
- Use `store_as` only for values or selections that later steps reference.
- Never put `SELF`, `PLAYER`, or `OPPONENT` in `store_as`.
- If a step applies an effect immediately, that is usually `target`.
- If a step selects or computes something for later reuse, that is usually `store_as`.

## Known bad patterns to fix

These are the main draft defects to correct.

### 1. Reserved targets incorrectly placed in `store_as`

Bad:

```json
{
  "kind": "effect",
  "op": "BOOST_SCORE",
  "store_as": "SELF",
  "count": { "kind": "literal", "value": 3 }
}
```

Good:

```json
{
  "kind": "effect",
  "op": "BOOST_SCORE",
  "target": "SELF",
  "count": { "kind": "literal", "value": 3 }
}
```

### 2. `EFFECT: CONDITION: ...` turned into `effect/op=CONDITION`

Bad:

```json
{
  "kind": "effect",
  "op": "CONDITION"
}
```

Good:

- use a real `condition` step
- or use an `if` step with a proper condition structure
- if still unclear, keep it valid but mark `needs_review`

### 3. Semicolon-chained effects collapsed into one bad step

Bad:

```json
{
  "kind": "effect",
  "op": "DRAW",
  "store_as": "; DISCARD_HAND(1)",
  "count": { "kind": "literal", "value": 2 }
}
```

Good:

```json
[
  {
    "kind": "effect",
    "op": "DRAW",
    "target": "PLAYER",
    "count": { "kind": "literal", "value": 2 },
    "args": {}
  },
  {
    "kind": "effect",
    "op": "DISCARD_HAND",
    "target": "PLAYER",
    "count": { "kind": "literal", "value": 1 },
    "args": {}
  }
]
```

### 4. `(Optional)` or semicolon-chained text in `store_as`

`store_as` must only contain a single variable name. Any metadata like `(Optional)` or semicolon-chained operations must be moved to their proper fields or separate steps.

Bad:

```json
{
  "kind": "cost",
  "op": "DISCARD_HAND",
  "store_as": "(Optional)"
}
```

Good:

```json
{
  "kind": "cost",
  "op": "DISCARD_HAND",
  "optional": true
}
```

### 5. Filter strings inside `store_as` or `args`

Filters must be structured objects, not strings.

Bad:

```json
{
  "kind": "select",
  "op": "SELECT_MEMBER",
  "store_as": "(Optional) {FILTER=\"STATUS=TAPPED\"}"
}
```

Good:

```json
{
  "kind": "select",
  "op": "SELECT_MEMBER",
  "count": { "kind": "literal", "value": 1 },
  "optional": true,
  "store_as": "TARGET",
  "filter": {
    "all_of": [
      { "field": "status", "op": "eq", "value": "TAPPED" }
    ]
  }
}
```

### 6. Raw strings for counts in `args` instead of `count` field

Bad:

```json
{
  "kind": "effect",
  "op": "ADD_BLADES",
  "args": { "raw": "1, PER_CARD=DISCARD_COUNT" }
}
```

Good:

```json
{
  "kind": "effect",
  "op": "ADD_BLADES",
  "target": "SELF",
  "count": { "kind": "literal", "value": 1 },
  "args": {
    "per_card": { "kind": "reference", "name": "DISCARD_COUNT" }
  }
}
```

## Semantic Binding Standards

To ensure semantic correctness and compatibility with the verification harness, use these standardized binding names:

### Common Bindings
| Pattern | Standard Name | Usage |
| :--- | :--- | :--- |
| **Optional Cost Success** | `SUCCESS` | Use in `store_as` of a `(Optional)` cost. |
| **Variable Discard Count** | `DISCARD_COUNT` | Use in `store_as` of `SELECT_HAND(VARIABLE)`. |
| **Selection Result** | `TARGET` | Use in `store_as` for single card selection. |
| **Multiple Selection Result** | `TARGETS` | Use in `store_as` for multiple card selection. |
| **Counting Operations** | `COUNT_VAL` | Use in `store_as` for `COUNT_MEMBER` or similar. |

### Condition Structure Patterns

When an effect depends on a previous cost or selection, use explicit `if` blocks:

1. **After Optional Cost**:
   ```json
   {
     "kind": "if",
     "condition": { "kind": "condition", "op": "eq", "args": { "left": { "kind": "reference", "name": "SUCCESS" }, "right": { "kind": "literal", "value": true } } },
     "then": [ ... dependent effects ... ]
   }
   ```

2. **After Variable Discard**:
   ```json
   {
     "kind": "if",
     "condition": { "kind": "condition", "op": "gt", "args": { "left": { "kind": "reference", "name": "DISCARD_COUNT" }, "right": { "kind": "literal", "value": 0 } } },
     "then": [ ... effects per card ... ]
   }
   ```

### Selector-to-Effect Mapping

If a `select` step binds a value, the subsequent `effect` **MUST** use that binding as its `target`.

**Bad**:
`SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(1)`
**Good**:
`SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)` (JSON: `target: "TARGET"`)

---

## Filter Normalization Guide

Map pseudocode fragments to structured `FilterClause` objects:

- `COST_LE_4` -> `{ "field": "cost", "op": "le", "value": 4 }`
- `STATUS=TAPPED` -> `{ "field": "status", "op": "eq", "value": "TAPPED" }`
- `NAME_IN=['A', 'B']` -> `{ "field": "name", "op": "in", "value": ["A", "B"] }`
- `Umi/Yoshiko/Rina` -> `{ "field": "name", "op": "in", "value": ["園田海未", "津島善子", "天王寺璃奈"] }` (Use JP names if possible)

## Common Target Mappings

If `target` is missing, use these defaults if they match the context:

- `DRAW`, `DISCARD_HAND`, `ACTIVATE_ENERGY` -> `PLAYER`
- `BOOST_SCORE`, `ADD_BLADES`, `ADD_HEARTS` -> `SELF` (usually the member card acting)
- `TAP_OPPONENT` -> `OPPONENT` (usually targets the opponent player or their members)

## Legacy patterns that should usually be review-marked, not guessed

- `OPTION:` blocks
- `CHOICE_MODE`
- `SELECT_OPTION`
- chained `-> X -> Y`
- raw boolean filters with `OR`
- `LOOK_AND_CHOOSE`
- `GRANT_ABILITY`

## What to optimize for

Fix the draft so it becomes:

1. schema-valid
2. target/binding-correct
3. split into proper steps
4. conservative when uncertain

## Good examples

### Example A

Input draft:

```json
{
  "card_no": "PL!HS-bp1-006-P",
  "schema_version": "v0",
  "trigger": "ON_PLAY",
  "once_per_turn": false,
  "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: DRAW(2); DISCARD_HAND(1)",
  "raw_text": "{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。",
  "confidence": "high",
  "review_reasons": [],
  "steps": [
    {
      "kind": "effect",
      "op": "DRAW",
      "store_as": "; DISCARD_HAND(1)",
      "count": { "kind": "literal", "value": 2 }
    }
  ]
}
```

Fixed output:

```json
{
  "card_no": "PL!HS-bp1-006-P",
  "schema_version": "v0",
  "trigger": "ON_PLAY",
  "once_per_turn": false,
  "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: DRAW(2); DISCARD_HAND(1)",
  "raw_text": "{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。",
  "confidence": "high",
  "review_reasons": [],
  "steps": [
    {
      "kind": "effect",
      "op": "DRAW",
      "target": "PLAYER",
      "count": { "kind": "literal", "value": 2 },
      "args": {}
    },
    {
      "kind": "effect",
      "op": "DISCARD_HAND",
      "target": "PLAYER",
      "count": { "kind": "literal", "value": 1 },
      "args": {}
    }
  ]
}
```

### Example B

Input draft:

```json
{
  "card_no": "LL-bp1-001-R＋",
  "schema_version": "v0",
  "trigger": "ON_LIVE_START",
  "once_per_turn": false,
  "pseudocode": "TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(3) {FILTER=\"Ayumu/Kanon/Kaho\"} (Optional)\nEFFECT: BOOST_SCORE(3) -> SELF",
  "raw_text": " ... ",
  "confidence": "low",
  "review_reasons": ["issue_in_step_DISCARD_HAND"],
  "steps": [
    {
      "kind": "cost",
      "op": "DISCARD_HAND",
      "count": { "kind": "literal", "value": 3 },
      "review_markers": ["unknown_filter_fragment"]
    },
    {
      "kind": "effect",
      "op": "BOOST_SCORE",
      "store_as": "SELF",
      "count": { "kind": "literal", "value": 3 }
    }
  ]
}
```

Fixed output:

```json
{
  "card_no": "LL-bp1-001-R＋",
  "schema_version": "v0",
  "trigger": "ON_LIVE_START",
  "once_per_turn": false,
  "pseudocode": "TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(3) {FILTER=\"Ayumu/Kanon/Kaho\"} (Optional)\nEFFECT: BOOST_SCORE(3) -> SELF",
  "raw_text": " ... ",
  "confidence": "low",
  "review_reasons": ["issue_in_step_DISCARD_HAND"],
  "steps": [
    {
      "kind": "cost",
      "op": "DISCARD_HAND",
      "count": { "kind": "literal", "value": 3 },
      "optional": true,
      "review_markers": ["unknown_filter_fragment"]
    },
    {
      "kind": "effect",
      "op": "BOOST_SCORE",
      "target": "SELF",
      "count": { "kind": "literal", "value": 3 }
    }
  ]
}
```

```

### Example C

Input draft (with multi-issue step):

```json
{
  "card_no": "LL-bp2-001-R＋",
  "schema_version": "v0",
  "trigger": "ON_LIVE_START",
  "pseudocode": "TRIGGER: ON_LIVE_START\nCOST: SELECT_HAND(VARIABLE) {FILTER=\"NAME_IN=['渡辺曜', '鬼塚夏美', '大沢瑠璃乃']\"} (Optional) -> DISCARD_COUNT\nEFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); ADD_BLADES(1, PER_CARD=DISCARD_COUNT) -> SELF {DURATION=\"UNTIL_LIVE_END\"}",
  "steps": [
    {
      "kind": "select",
      "op": "SELECT_HAND",
      "args": { "raw": "VARIABLE" },
      "store_as": "(Optional)",
      "filter": { "all_of": [{ "field": "name", "op": "in", "value": ["渡辺曜", "鬼塚夏美", "大沢瑠璃乃"] }] }
    },
    {
      "kind": "if",
      "condition": {
        "kind": "binary", "op": "gt",
        "left": { "kind": "reference", "name": "DISCARD_COUNT" },
        "right": { "kind": "literal", "value": 0 }
      },
      "then": [
        {
          "kind": "effect",
          "op": "ADD_BLADES",
          "args": { "raw": "1, PER_CARD=DISCARD_COUNT" },
          "store_as": "SELF {DURATION=\"UNTIL_LIVE_END\"}"
        }
      ]
    }
  ]
}
```

Fixed output:

```json
{
  "card_no": "LL-bp2-001-R＋",
  "schema_version": "v0",
  "trigger": "ON_LIVE_START",
  "pseudocode": "TRIGGER: ON_LIVE_START\nCOST: SELECT_HAND(VARIABLE) {FILTER=\"NAME_IN=['渡辺曜', '鬼塚夏美', '大沢瑠璃乃']\"} (Optional) -> DISCARD_COUNT\nEFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); ADD_BLADES(1, PER_CARD=DISCARD_COUNT) -> SELF {DURATION=\"UNTIL_LIVE_END\"}",
  "steps": [
    {
      "kind": "select",
      "op": "SELECT_HAND",
      "count": { "kind": "reference", "name": "VARIABLE" },
      "optional": true,
      "store_as": "DISCARD_COUNT",
      "filter": {
        "all_of": [
          { "field": "name", "op": "in", "value": ["渡辺曜", "鬼塚夏美", "大沢瑠璃乃"] }
        ]
      }
    },
    {
      "kind": "if",
      "condition": {
        "kind": "condition",
        "op": "VALUE_GT",
        "args": {
          "left": { "kind": "reference", "name": "DISCARD_COUNT" },
          "right": { "kind": "literal", "value": 0 }
        }
      },
      "then": [
        {
          "kind": "effect",
          "op": "ADD_BLADES",
          "target": "SELF",
          "count": { "kind": "literal", "value": 1 },
          "duration": "UNTIL_LIVE_END",
          "args": {
            "per_card": { "kind": "reference", "name": "DISCARD_COUNT" }
          }
        }
      ]
    }
  ]
}
```

## Practical instruction

Take each existing draft entry and fix it in place.

Do not rewrite everything from scratch unless the current entry is clearly malformed.

Prefer small, conservative corrections over large reinterpretations.

## Input placeholder

Fix this draft entry:

```json
{{DRAFT_ENTRY_JSON}}
```
