# Meta Rules Documentation

The `O_META_RULE` (Opcode 29) handles various game rule modifications. It acts as a multiplexer where the specific rule change is determined by a sub-type encoded in the `attr` operand.

## Meta Rule Types

| ID | Type (String) | Description | Status |
|---|---|---|---|
| **0** | `cheer_mod` | **Cheer Modification**. Adds/Subtracts from the number of cards revealed during Performance Phase. | ✅ Implemented |
| **1** | `heart_rule` | **Heart Rule**. Treats specific icons (e.g., Blades) as Hearts during live checks. | ❌ Planned |
| **2** | `live` | **Live Rule**. Catch-all for live interaction rules / Rule Equivalence. | ⚠️ Placeholder |
| **3** | `shuffle` | **Shuffle Deck**. Shuffles the player's deck. | ❌ Planned |
| **4** | `opponent_trigger_allowed` | **Trigger Permission**. Allows opponent's effects to trigger off specific actions. | ❌ Planned |
| **5** | `lose_blade_heart` | **Lose Blade Heart**. Modifies blade/heart loss mechanics. | ❌ Planned |
| **6** | `re_cheer` | **Re-Cheer**. Allows re-triggering cheer logic. | ❌ Planned |
| **7** | `group_alias` | **Group Alias**. Treats multi-group members as belonging to all named groups. | ❌ Planned |
| **8** | `score_rule` | **Score Rule**. Modifies score calculation logic. | ❌ Planned |
| **9** | `PREVENT_SET_PILE` | **Prevent Success**. Prevents card from moving to success live pile. | ❌ Planned |
| **10** | `YELL_MULLIGAN` | **Yell Mulligan**. Re-yell if no live cards revealed. | ❌ Planned |
| **11** | `YELL_AGAIN` | **Yell Again**. Re-yell based on condition. | ❌ Planned |
| **12** | `MOVE_SUCCESS` | **Move Success**. Special move logic for success pile. | ❌ Planned |
| **13** | `RESET_HEARTS` | **Reset Hearts**. Reset yell hearts to 0. | ❌ Planned |

## Bytecode Encoding
Standard format: `[OP, VAL, ATTR, SLOT]`
- **OP**: 29 (`O_META_RULE`)
- **VAL**: The value associated with the rule (e.g., amount for `cheer_mod`).
- **ATTR**: The **Meta Rule Type ID**.
- **SLOT**: Context dependent (often unused 0).

---

## Research & Impact Analysis

An audit of `data/cards_compiled.json` reveals the following state of meta-rule implementation.

### The "Type 0" Fallback Issue
Previously, many cards defaulted to `attr=0` (cheer_mod) due to a missing mapping in the compiler. Phase 2 (Compiler Validation) is ongoing to restore correct sub-type mappings.

---

## Full Card Mapping Audit

## Type `cheer_mod` (attr=0)

### PL!HS-bp2-019-L - Bloom the smile, Bloom the dream! (ID: 30038)
- **Bytecode**: `[OP:29, V:1, A:0, S:1]`
- **Ability**: TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=4"}
EFFECT: SELECT_MODE(1) (Optional)
  OPTION: ピンク×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="PINK/PINK/ANY"}
  OPTION: グリーン×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="GREEN/GREEN/ANY"}
  OPTION: ブルー×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="BLUE/BLUE/ANY"}

### PL!HS-bp2-019-L - Bloom the smile, Bloom the dream! (ID: 30038)
- **Bytecode**: `[OP:29, V:1, A:0, S:1]`
- **Ability**: TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=4"}
EFFECT: SELECT_MODE(1) (Optional)
  OPTION: ピンク×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="PINK/PINK/ANY"}
  OPTION: グリーン×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="GREEN/GREEN/ANY"}
  OPTION: ブルー×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="BLUE/BLUE/ANY"}

### PL!HS-bp2-019-L - Bloom the smile, Bloom the dream! (ID: 30038)
- **Bytecode**: `[OP:29, V:1, A:0, S:1]`
- **Ability**: TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=4"}
EFFECT: SELECT_MODE(1) (Optional)
  OPTION: ピンク×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="PINK/PINK/ANY"}
  OPTION: グリーン×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="GREEN/GREEN/ANY"}
  OPTION: ブルー×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="BLUE/BLUE/ANY"}

### PL!HS-bp2-020-L - Link to the FUTURE (ID: 30039)
- **Bytecode**: `[OP:29, V:1, A:0, S:0]`
- **Ability**: TRIGGER: CONSTANT
EFFECT: ADD_TAG("UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA") -> SELF



### PL!N-bp4-026-L - DIVE! (ID: 30060)
- **Bytecode**: `[OP:29, V:1, A:0, S:1]`
- **Ability**: TRIGGER: ON_POSITION_CHANGE (From Discard to Hand)
CONDITION: MAIN_PHASE
EFFECT: SELECT_MODE(1) (Optional)
  OPTION: 「DIVE!」をパフォームする | EFFECT: PLAY_LIVE_FROM_HAND(1) {FILTER="NAME=DIVE!"}; REDUCE_LIVE_SET_LIMIT(1) {NEXT_TURN=TRUE}



### PL!SP-bp1-026-L - 未来予報ハレルヤ！ (ID: 30119)
- **Bytecode**: `[OP:29, V:1, A:0, S:0]`
- **Ability**: TRIGGER: ON_LIVE_START
CONDITION: COUNT_UNIQUE_NAMES {MIN=5, FILTER="GROUP_ID=3", AREA="STAGE_OR_DISCARD"}
EFFECT: SET_HEART_REQ {HEART_LIST=[2,2,3,3,6,6]} -> SELF
EFFECT: META_RULE {TYPE="ALL_BLADE_AS_ANY_HEART"} -> PLAYER

## Type `heart_rule` (attr=1)

### PL!SP-bp1-024-L - Tiny Stars (ID: 30114)
- **Bytecode**: `[OP:29, V:1, A:1, S:1]` [all_blade]
- **Ability**: TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {NAME="澁谷かのん", ZONE="STAGE"} -> TARGET_1; ADD_HEARTS(1) {HEART_TYPE=4, TARGET="TARGET_1", DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_1 {DURATION="UNTIL_LIVE_END"}
EFFECT: SELECT_MEMBER(1) {NAME="唐可可", ZONE="STAGE"} -> TARGET_2; ADD_HEARTS(1) {HEART_TYPE=0, TARGET="TARGET_2", DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_2 {DURATION="UNTIL_LIVE_END"}
EFFECT: META_RULE {TYPE="ALL_BLADE_AS_ANY_HEART"} -> PLAYER



### PL!SP-bp1-026-L - 未来予報ハレルヤ！ (ID: 30119)
- **Bytecode**: `[OP:29, V:1, A:1, S:1]` [all_blade]
- **Ability**: TRIGGER: ON_LIVE_START
CONDITION: COUNT_UNIQUE_NAMES {MIN=5, FILTER="GROUP_ID=3", AREA="STAGE_OR_DISCARD"}
EFFECT: SET_HEART_REQ {HEART_LIST=[2,2,3,3,6,6]} -> SELF
EFFECT: META_RULE {TYPE="ALL_BLADE_AS_ANY_HEART"} -> PLAYER

## Type `PREVENT_SET_TO_SUCCESS_PILE` (attr=9)

### PL!S-bp2-024-L - 君のこころは輝いてるかい？ (ID: 30091)
- **Bytecode**: `[OP:29, V:1, A:9, S:0]`
- **Ability**: TRIGGER: CONSTANT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE -> SELF



### PL!S-pb1-022-L - 逃走迷走メビウスループ (ID: 30104)
- **Bytecode**: `[OP:29, V:1, A:9, S:1]`
- **Ability**: TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}

### PL!S-pb1-022-L＋ - 逃走迷走メビウスループ (ID: 30105)
- **Bytecode**: `[OP:29, V:1, A:9, S:1]`
- **Ability**: TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}

### PL!S-pb1-022-L＋ - 逃走迷走メビウスループ (ID: 30106)
- **Bytecode**: `[OP:29, V:1, A:9, S:1]`
- **Ability**: TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}

### PL!S-pb1-022-L - 逃走迷走メビウスループ (ID: 30107)
- **Bytecode**: `[OP:29, V:1, A:9, S:1]`
- **Ability**: TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}

## Type `ACTION_YELL_MULLIGAN` (attr=10)

### PL!S-bp2-004-P - 黒澤ダイヤ (ID: 952)
- **Bytecode**: `[OP:29, V:1, A:10, S:1]`
- **Ability**: TRIGGER: ON_REVEAL (Once per turn)
CONDITION: NOT REVEALED_CONTAINS {TYPE_LIVE}
EFFECT: ACTION_YELL_MULLIGAN

### PL!S-bp2-004-R - 黒澤ダイヤ (ID: 953)
- **Bytecode**: `[OP:29, V:1, A:10, S:1]`
- **Ability**: TRIGGER: ON_REVEAL (Once per turn)
CONDITION: NOT REVEALED_CONTAINS {TYPE_LIVE}
EFFECT: ACTION_YELL_MULLIGAN

### PL!S-bp2-004-R - 黒澤ダイヤ (ID: 954)
- **Bytecode**: `[OP:29, V:1, A:10, S:1]`
- **Ability**: TRIGGER: ON_REVEAL (Once per turn)
CONDITION: NOT REVEALED_CONTAINS {TYPE_LIVE}
EFFECT: ACTION_YELL_MULLIGAN

### PL!S-bp2-004-P - 黒澤ダイヤ (ID: 955)
- **Bytecode**: `[OP:29, V:1, A:10, S:1]`
- **Ability**: TRIGGER: ON_REVEAL (Once per turn)
CONDITION: NOT REVEALED_CONTAINS {TYPE_LIVE}
EFFECT: ACTION_YELL_MULLIGAN

## Type `TRIGGER_YELL_AGAIN` (attr=11)

### PL!S-bp3-020-L - ダイスキだったらダイジョウブ！ (ID: 30095)
- **Bytecode**: `[OP:29, V:1, A:11, S:1]`
- **Ability**: TRIGGER: ON_REVEAL
CONDITION: TURN_1, COUNT_YELL_REVEALED {MAX=2, FILTER="HAS_BLADE_HEART"}
EFFECT: MOVE_TO_DISCARD(ALL) {ZONE="YELL_REVEALED"}; RESET_YELL_HEARTS; TRIGGER_YELL_AGAIN

## Type `MOVE_SUCCESS` (attr=12)

### PL!N-bp4-010-P - 三船栞子 (ID: 742)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-R＋ - 三船栞子 (ID: 743)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-P＋ - 三船栞子 (ID: 744)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-SEC - 三船栞子 (ID: 745)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-P＋ - 三船栞子 (ID: 746)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-R＋ - 三船栞子 (ID: 747)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-P - 三船栞子 (ID: 748)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-SEC - 三船栞子 (ID: 749)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-R＋ - 三船栞子 (ID: 750)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-P - 三船栞子 (ID: 751)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-P＋ - 三船栞子 (ID: 752)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-SEC - 三船栞子 (ID: 753)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-SEC - 三船栞子 (ID: 754)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-R＋ - 三船栞子 (ID: 755)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-P - 三船栞子 (ID: 756)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

### PL!N-bp4-010-P＋ - 三船栞子 (ID: 757)
- **Bytecode**: `[OP:29, V:1, A:12, S:1]`
- **Ability**: TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF

## Type `RESET_YELL_HEARTS` (attr=13)

### PL!S-bp3-020-L - ダイスキだったらダイジョウブ！ (ID: 30095)
- **Bytecode**: `[OP:29, V:1, A:13, S:1]`
- **Ability**: TRIGGER: ON_REVEAL
CONDITION: TURN_1, COUNT_YELL_REVEALED {MAX=2, FILTER="HAS_BLADE_HEART"}
EFFECT: MOVE_TO_DISCARD(ALL) {ZONE="YELL_REVEALED"}; RESET_YELL_HEARTS; TRIGGER_YELL_AGAIN
