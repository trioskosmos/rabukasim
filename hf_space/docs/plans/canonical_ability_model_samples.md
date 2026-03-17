# Canonical Ability Model Samples

## Goal

Reduce the pipeline to:

`Japanese text -> canonical ability model -> engine execution`

This document uses real compiled abilities to define what the canonical model must handle.

## Sample set

### Simple abilities

1. `PL!N-sd1-009-SD` / `天王寺璃奈`

```text
TRIGGER: ON_PLAY
EFFECT: DRAW(1)
```

Why it matters:

- minimum viable effect
- proves the model should not need control flow for trivial cards

2. `PL!N-bp3-006-P` / `近江彼方`

```text
TRIGGER: ON_PLAY
EFFECT: TAP_SELF
```

Why it matters:

- effect with no value operand
- proves opcodes should not be forced to carry `count/value`

3. `PL!HS-bp1-006-P` / `藤島 慈`

```text
TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(1)
```

Why it matters:

- sequential effects
- no branches, no conditions, still more than one step

### Medium abilities

4. `PL!-pb1-004-P＋` / `園田海未`

```text
TRIGGER: ON_PLAY
CONDITION: IS_CENTER
EFFECT: SUCCESS_PILE_COUNT {FILTER="GROUP_ID=0, HAS_SCORE=TRUE"} -> COUNT_VAL
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"} (CONDITION: VALUE_EQ(COUNT_VAL, 1))
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(2) -> PLAYER", DURATION="UNTIL_LIVE_END"} (CONDITION: VALUE_GE(COUNT_VAL, 2))
```

Why it matters:

- precondition plus computed temporary value
- conditional effects
- generated nested ability

5. `PL!HS-bp2-005-P` / `大沢瑠璃乃`

```text
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_MEMBER(PLAYER) {FILTER="AREA_LEFT"} (Optional) -> LEFT_VAL; COUNT_MEMBER(PLAYER) {FILTER="AREA_CENTER"} -> CENTER_VAL; COUNT_MEMBER(PLAYER) {FILTER="AREA_RIGHT"} -> RIGHT_VAL
CONDITION: VALUE_GT(LEFT_VAL, 0), VALUE_GT(CENTER_VAL, 0), VALUE_GT(RIGHT_VAL, 0); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

Why it matters:

- optional cost with success result
- multiple temporary values
- later condition depends on stored values

6. `PL!N-bp3-011-P` / `ミア・テイラー`

```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, NOT_NAME='Mia'"} -> TARGET_MEMBER
EFFECT: CONDITION: HAS_MATCHING_HEART(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_COST(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_BASE_BLADE(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

Why it matters:

- selection produces a bound target
- repeated condition/effect pattern over the same bound target

### Complex abilities

7. `PL!-bp3-024-L` / `夏色えがおで1,2,Jump!`

```text
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=1}
EFFECT: CHOICE_MODE -> PLAYER
OPTION: {{heart_01.png|heart01}} | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
OPTION: {{heart_03.png|heart03}} | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}
OPTION: {{heart_06.png|heart06}} | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}
```

Why it matters:

- choose-one UI branch
- branches are structurally similar
- options should be modeled explicitly, not as jump spaghetti

8. `PL!N-bp3-009-P` / `天王寺璃奈`

```text
TRIGGER: ON_LIVE_START
COST: SELECT_RECOVER_MEMBER(2) (Optional) -> DECK_BOTTOM -> CHOSEN_CARDS; CALC_SUM_COST(CHOSEN_CARDS) -> TOTAL_VAL
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 6); DRAW(1)
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 8); ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 25); GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
```

Why it matters:

- selected card collection is stored
- aggregate expression over a collection
- condition branches over a computed total

9. `PL!S-bp3-006-P` / `津島善子`

```text
TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, GROUP_ID=1"} -> TARGET_STAGE; MOVE_TO_DISCARD(TARGET_STAGE) -> SUCCESS; GET_COST(TARGET_STAGE) -> BASE_COST
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {FILTER="GROUP_ID=1, COST_EQ=BASE_COST+2"} -> TARGET_DISCARD; PLAY_STAGE_SPECIFIC_SLOT(TARGET_DISCARD) {SLOT="SAME_SLOT"}
```

Why it matters:

- activated timing
- chained dependent actions
- later filter depends on an earlier computed value
- slot semantics matter

10. `PL!SP-bp5-009-AR` / `鬼塚夏美`

```text
TRIGGER: ON_LIVE_START
COST: MOVE_TO_DISCARD(1) {FROM="DECK_TOP"} (Optional)
EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
CONDITION: DISCARDED_CARDS {FILTER="TYPE_LIVE"}
EFFECT: TAP_SELF
... repeated five times ...
```

Why it matters:

- very long text
- repeated subroutine pattern
- strongly suggests loops/repeat blocks should exist in the model

## What the canonical model must support

These samples suggest the model should have a small set of first-class step types.

### Core step types

- `cost`
- `condition`
- `effect`
- `select`
- `choose_one`
- `assign`
- `repeat`

### Core data concepts

- `target`
- `filter`
- `zone`
- `slot`
- `duration`
- `count_expr`
- `value_expr`
- `result_binding`

### Control-flow concepts

- `preconditions`
- `optional`
- `if`
- `branches`
- `store_as`
- `repeat_while` or explicit repeated block

## Suggested canonical model shape

For the repo, the best single source of truth probably looks like this:

```json
{
  "trigger": "ON_PLAY",
  "once_per_turn": false,
  "steps": [
    {
      "kind": "select",
      "op": "SELECT_MEMBER",
      "args": {
        "count": 1,
        "filter": { "owner": "OPPONENT", "not_name": "Mia" },
        "store_as": "target_member"
      }
    },
    {
      "kind": "if",
      "condition": {
        "op": "HAS_MATCHING_HEART",
        "args": { "left": "SELF", "right": "$target_member" }
      },
      "then": [
        {
          "kind": "effect",
          "op": "ADD_BLADES",
          "args": { "count": 1, "target": "SELF", "duration": "UNTIL_LIVE_END" }
        }
      ]
    }
  ]
}
```

## Design rules

1. The canonical model should use named operands, not packed numeric fields.
2. The canonical model should represent repeated patterns once, not five times if they are semantically a loop.
3. Selection results and computed values should be explicitly bound by name.
4. Conditions should be embeddable both as top-level guards and branch-local checks.
5. Bytecode should be derived from this model, not the other way around.

## Reduction of layers

This does not add a permanent extra layer if we remove the others.

Target end state:

- keep: JP text
- keep: canonical ability model
- keep: execution backend
- derive only as caches/views: pseudocode, bytecode, generated Rust

Remove as sources of truth:

- duplicate semantic forms
- duplicate effect/condition/cost and bytecode truths that can diverge
- opaque packed meaning as the primary authored representation

## Immediate next step

Implement the canonical model only for this sample set first.

If these 10 cases can be represented cleanly, the model is probably on the right track.
If not, the schema is still too close to the current bytecode mindset.
