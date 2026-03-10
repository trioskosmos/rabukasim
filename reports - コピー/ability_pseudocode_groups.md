## Summary
- Total Unique Abilities: 510
- Groups with Conflicts: 46
- Groups without Conflicts: 464

# Ability Pseudocode Grouping Report

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分の成功ライブカード置...
**Cards:** PL!-sd1-001-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_CARDS(ZONE="SUCCESS_PILE", PLAYER) {GE=2}
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND

TRIGGER: CONSTANT
EFFECT: COUNT_CARDS(ZONE="SUCCESS_PILE", PLAYER) -> COUNT;
EFFECT: ADD_BLADES(1, PER_CARD=COUNT) -> SELF
```

---

## Ability: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。...
**Cards:** PL!-sd1-002-SD, PL!S-PR-025-PR, PL!S-PR-027-PR, PL!HS-PR-014-PR, PL!N-sd1-006-SD, PL!SP-pb1-021-N, PL!S-bp2-016-N, PL!-pb1-019-N, PL!-pb1-025-N, PL!N-bp4-017-N, PL!N-bp4-020-N, PL!SP-bp4-015-N, PL!SP-bp4-019-N, PL!HS-PR-014-RM, PL!S-PR-025-RM, PL!S-PR-027-RM, PL!HS-sd1-015-SD, PL!S-sd1-008-SD

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-sd1-002-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!S-PR-025-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!S-PR-027-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!HS-PR-014-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!N-sd1-006-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!SP-pb1-021-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!S-bp2-016-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!-pb1-019-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!-pb1-025-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!N-bp4-017-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=2"} -> CARD_HAND`
- **PL!N-bp4-020-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=2"} -> CARD_HAND`
- **PL!SP-bp4-015-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!SP-bp4-019-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!HS-PR-014-RM**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!S-PR-025-RM**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!S-PR-027-RM**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!HS-sd1-015-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`
- **PL!S-sd1-008-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=2"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分の控え室からコスト4以下の『μ's』のメンバーカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：{{...
**Cards:** PL!-sd1-003-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_M_S, COST_LE_4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_OPTION(PLAYER) {OPTIONS=["RED", "GREEN", "PURPLE"]} -> COLOR; ADD_HEARTS(1) -> SELF {HEART_TYPE=COLOR, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『μ's』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!-sd1-004-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_REVEAL(5, Optional) {FILTER="UNIT_M_S, TYPE=LIVE"} -> CARD_HAND
```

---

## Ability: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。...
**Cards:** PL!-sd1-005-SD, PL!S-PR-026-PR, PL!N-PR-009-PR, PL!N-PR-012-PR, PL!N-PR-014-PR, PL!SP-bp1-011-R, PL!SP-bp1-011-P, PL!N-sd1-011-SD, PL!SP-sd1-006-SD, PL!SP-pb1-018-N, PL!S-bp2-009-R, PL!S-bp2-009-P, PL!HS-bp2-004-R, PL!HS-bp2-004-P, PL!S-pb1-004-R, PL!S-pb1-004-P＋, PL!-pb1-024-N, PL!-bp4-003-R, PL!-bp4-003-P, PL!N-PR-009-RM, PL!-sd1-005-RM, PL!S-sd1-015-SD, PL!N-PR-012-RM, PL!HS-sd1-009-SD, PL!N-PR-014-RM, PL!HS-PR-026-PR, PL!N-PR-019-PR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-sd1-005-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!S-PR-026-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-PR-009-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-PR-012-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-PR-014-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!SP-bp1-011-R**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!SP-bp1-011-P**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-sd1-011-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!SP-sd1-006-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!SP-pb1-018-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!S-bp2-009-R**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!S-bp2-009-P**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!HS-bp2-004-R**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!HS-bp2-004-P**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!S-pb1-004-R**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!S-pb1-004-P＋**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND`
- **PL!-pb1-024-N**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!-bp4-003-R**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!-bp4-003-P**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-PR-009-RM**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!-sd1-005-RM**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!S-sd1-015-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-PR-012-RM**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!HS-sd1-009-SD**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-PR-014-RM**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!HS-PR-026-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!N-PR-019-PR**: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。そうした場合、これにより公開したカードを自分の成功ライブカード置...
**Cards:** PL!-sd1-006-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: SELECT_REVEAL_HAND(1, Optional) {FILTER="TYPE=LIVE"} -> SUCCESS, TARGET_REVEALED
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_SUCCESS_PILE(1, PLAYER) -> TARGET_SUCCESS; MOVE_TO_HAND(TARGET_SUCCESS); MOVE_TO_SUCCESS_PILE(TARGET_REVEALED)
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。...
**Cards:** PL!-sd1-007-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(5, FROM="DECK_TOP") -> DISCARDED;
CONDITION: COUNT_CARDS(DISCARDED) {FILTER="TYPE=LIVE", GE=1}; DRAW(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のデッキの上からカードを10枚控え室に置...
**Cards:** PL!-sd1-008-SD

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)

COST: PAY_ENERGY(2)
EFFECT: MOVE_TO_DISCARD(10) {FROM="DECK_TOP"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の控え室に『μ's』のカードが25枚以上ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。...
**Cards:** PL!-sd1-009-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_CARDS(ZONE="CARD_DISCARD", PLAYER) {FILTER="UNIT_M_S", GE=25}
EFFECT: BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。...
**Cards:** PL!-sd1-011-SD, PL!-sd1-012-SD, PL!-sd1-016-SD, PL!N-PR-004-PR, PL!N-PR-006-PR, PL!N-PR-013-PR, PL!N-bp1-007-R, PL!N-bp1-007-P, PL!N-bp1-010-R, PL!N-bp1-010-P, PL!N-sd1-002-SD, PL!N-sd1-003-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(3) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!-sd1-015-SD, PL!HS-bp2-010-N

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-sd1-015-SD**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(5) {FILTER="TYPE=MEMBER"} -> CARD_HAND`
- **PL!HS-bp2-010-N**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE(5) {FILTER="TYPE_MEMBER"} -> CARD_HAND, DISCARD_REMAINDER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE(5) {FILTER="TYPE_MEMBER"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...
**Cards:** PL!-sd1-019-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード1枚につき、このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{hear...
**Cards:** PL!-sd1-022-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: COUNT_CARDS(ZONE="SUCCESS_PILE", PLAYER) -> COUNT;
EFFECT: HEART_COST_REDUCTION(2, PER_CARD=COUNT) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}の...
**Cards:** PL!-bp3-012-PR, PL!-bp3-011-N, PL!-bp3-012-N, PL!-bp3-013-N, PL!-bp3-012-RM

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-bp3-012-PR**: `TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(PLAYER) {OPTIONS=["RED", "GREEN", "PURPLE"]} -> COLOR;
EFFECT: COUNT_CARDS(ZONE="SUCCESS_PILE", PLAYER) -> COUNT;
EFFECT: ADD_HEARTS(1, PER_CARD=COUNT) -> SELF {HEART_TYPE=COLOR, DURATION="UNTIL_LIVE_END"}`
- **PL!-bp3-011-N**: `TRIGGER: ON_LIVE_START
EFFECT: COUNT_SUCCESS_LIVE(PLAYER) -> COUNT_VAL; CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=0, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_03.png|heart03}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_06.png|heart06}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}`
- **PL!-bp3-012-N**: `TRIGGER: ON_LIVE_START
EFFECT: COUNT_SUCCESS_LIVE(PLAYER) -> COUNT_VAL; CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=0, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_03.png|heart03}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_06.png|heart06}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}`
- **PL!-bp3-013-N**: `TRIGGER: ON_LIVE_START
EFFECT: COUNT_SUCCESS_LIVE(PLAYER) -> COUNT_VAL; CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=0, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_03.png|heart03}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_06.png|heart06}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}`
- **PL!-bp3-012-RM**: `TRIGGER: ON_LIVE_START
EFFECT: HEART_SELECT(1) {CHOICES=[1, 3, 6]} -> CHOICE
EFFECT: ADD_HEARTS(1) {HEART_TYPE=CHOICE, PER_CARD="SUCCESS_LIVE"} -> SELF`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_START
EFFECT: COUNT_SUCCESS_LIVE(PLAYER) -> COUNT_VAL; CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=0, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_03.png|heart03}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_06.png|heart06}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, PER_CARD=COUNT_VAL, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をアクティブにしてもよい。...
**Cards:** PL!-PR-001-PR, PL!-PR-002-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES
EFFECT: ACTIVATE_MEMBER(1) (Optional) -> SELF
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_03.png|heart03}}を3以上含むライブカードを1枚...
**Cards:** PL!-PR-003-PR

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="REQS_HAS_RED_GE_3"} -> CARD_HAND
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_01.png|heart01}}を3以上含むライブカードを1枚...
**Cards:** PL!-PR-004-PR

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="REQS_HAS_RED_GE_3"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}以下から1つを選ぶ。
・カードを1枚引き、手札を1枚控え室に置く。
・相手のステージにいるすべてのコスト2以下のメンバーをウェイトにする。...
**Cards:** PL!-PR-005-PR, PL!-PR-006-PR, PL!-PR-008-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_OPTION(PLAYER) {OPTIONS=["DRAW", "TAP_ALL_LE_2"]}
  OPTION: DRAW | EFFECT: DRAW(1); DISCARD_HAND(1)
  OPTION: TAP_ALL_LE_2 | EFFECT: SELECT_MEMBER(99) {FILTER="OPPONENT, COST_LE_2"} -> TARGETS; TAP_MEMBER(TARGETS)
```

---

## Ability: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状...
**Cards:** PL!-PR-007-PR, PL!-PR-009-PR, PL!S-bp3-012-N, PL!S-bp3-017-N, PL!N-bp3-017-N, PL!N-bp3-023-N

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-PR-007-PR**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(TARGET)`
- **PL!-PR-009-PR**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(TARGET)`
- **PL!S-bp3-012-N**: `TRIGGER: ON_PLAY, ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(TARGET)`
- **PL!S-bp3-017-N**: `TRIGGER: ON_PLAY, ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(TARGET)`
- **PL!N-bp3-017-N**: `TRIGGER: ON_PLAY, ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(TARGET)`
- **PL!N-bp3-023-N**: `TRIGGER: ON_PLAY, ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(TARGET)`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(TARGET)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。{{live_start.png|ライブ開始時...
**Cards:** PL!S-PR-013-PR, PL!S-PR-019-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(3) -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS_2
EFFECT: CONDITION: VALUE_EQ(SUCCESS_2, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!S-PR-016-PR, PL!S-PR-020-PR, PL!S-PR-021-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...
**Cards:** PL!S-PR-028-PR, PL!S-PR-032-PR, PL!S-PR-033-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)
```

---

## Ability: {{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!S-PR-029-PR, PL!S-PR-030-PR, PL!S-PR-031-PR

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {MIN=1, FILTER="COST_GE_13", AREA="ANY_STAGE"}
EFFECT: ADD_BLADES(2) -> SELF
```

---

## Ability: {{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。...
**Cards:** PL!N-bp1-019-PR, PL!N-bp1-014-N, PL!N-bp1-015-N, PL!N-bp1-019-N, PL!HS-bp1-010-N, PL!HS-bp1-014-N, PL!N-sd1-013-SD, PL!N-sd1-021-SD, PL!N-sd1-022-SD, PL!N-sd1-022-PRproteinbar, PL!N-sd1-013-PRproteinbar, PL!N-bp1-015-PRproteinbar, PL!N-bp1-019-PRproteinbar, PL!N-bp1-014-PRproteinbar, PL!N-sd1-021-PRproteinbar

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp1-019-PR**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-bp1-014-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER`
- **PL!N-bp1-015-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER`
- **PL!N-bp1-019-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!HS-bp1-010-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER`
- **PL!HS-bp1-014-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER`
- **PL!N-sd1-013-SD**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-sd1-021-SD**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-sd1-022-SD**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-sd1-022-PRproteinbar**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-sd1-013-PRproteinbar**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-bp1-015-PRproteinbar**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-bp1-019-PRproteinbar**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-bp1-014-PRproteinbar**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-sd1-021-PRproteinbar**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの...
**Cards:** PL!N-PR-003-PR, PL!N-PR-008-PR, PL!N-PR-010-PR

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER"}
COST: REVEAL_HAND(ALL) -> REVEALED_CARDS
CONDITION: COUNT_CARDS(REVEALED_CARDS) {FILTER="TYPE=LIVE", EQ=0}
EFFECT: LOOK_AND_CHOOSE_REVEAL(5, Optional) {FILTER="TYPE=LIVE"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}カードを2枚引き、手札を2枚控え室に置く。...
**Cards:** PL!N-PR-005-PR, PL!N-PR-007-PR, PL!N-PR-011-PR, PL!S-bp2-010-N, PL!N-bp3-024-N

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-PR-005-PR**: `TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(2)`
- **PL!N-PR-007-PR**: `TRIGGER: ON_PLAY
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER`
- **PL!N-PR-011-PR**: `TRIGGER: ON_PLAY
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER`
- **PL!S-bp2-010-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(2)`
- **PL!N-bp3-024-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(2)`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}自分のエネルギーが7枚以上ある場合、カードを1枚引く。...
**Cards:** PL!SP-PR-003-PR, PL!SP-PR-007-PR, PL!SP-PR-010-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_ENERGY(PLAYER) {GE=7}
EFFECT: DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...
**Cards:** PL!SP-PR-004-PR, PL!SP-PR-006-PR, PL!SP-PR-013-PR, PL!SP-bp1-021-N, PL!SP-sd1-014-SD, PL!SP-sd1-016-SD

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-PR-004-PR**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1, MODE="WAIT")`
- **PL!SP-PR-006-PR**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1, MODE="WAIT")`
- **PL!SP-PR-013-PR**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1, MODE="WAIT")`
- **PL!SP-bp1-021-N**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1)`
- **PL!SP-sd1-014-SD**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1)`
- **PL!SP-sd1-016-SD**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1)`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1, MODE="WAIT")
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これによりライブカードを控え室に置いた場合、さ...
**Cards:** PL!SP-PR-009-PR, PL!SP-PR-011-PR, PL!SP-PR-012-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1, Optional) -> DISCARDED;
EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"};
CONDITION: COUNT_CARDS(DISCARDED) {FILTER="TYPE=LIVE", GE=1}; DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}デッキの上からカードを5枚控え室に置く。...
**Cards:** PL!HS-bp2-011-PR, PL!HS-bp2-011-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(5) {FROM="DECK_TOP"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
{{live_start.png|ライブ開始...
**Cards:** PL!HS-PR-001-PR, PL!HS-PR-002-PR, PL!HS-PR-005-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(3) -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS_2
EFFECT: CONDITION: VALUE_EQ(SUCCESS_2, TRUE); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
**Cards:** PL!HS-PR-010-PR, PL!HS-PR-011-PR, PL!HS-PR-012-PR, PL!N-bp1-025-L, PL!SP-bp1-025-L, PL!HS-bp1-020-L, PL!N-sd1-026-SD, PL!N-sd1-027-SD, PL!SP-sd1-024-SD, PL!SP-sd1-025-SD

*No manual pseudocode found for this ability.*

---

## Ability: {{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_04.png|heart04}}{{heart_04.p...
**Cards:** PL!HS-PR-016-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2, Optional) -> DISCARDED; CONDITION: SAME_UNIT(DISCARDED)
EFFECT: ADD_HEARTS(2) -> SELF {HEART_TYPE=BLUE, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_05.png|heart05}}{{heart_05.p...
**Cards:** PL!HS-PR-017-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2, Optional) -> DISCARDED; CONDITION: SAME_UNIT(DISCARDED)
EFFECT: ADD_HEARTS(2) -> SELF {HEART_TYPE=PINK, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.p...
**Cards:** PL!HS-PR-018-PR, PL!HS-PR-022-PR, PL!SP-bp1-006-R, PL!SP-bp1-006-P, PL!SP-bp2-019-N, PL!SP-bp2-022-N, PL!S-pb1-016-N, PL!S-pb1-017-N, PL!S-pb1-018-N, PL!-bp4-010-N, PL!N-bp4-013-N, PL!HS-PR-018-RM

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!HS-PR-018-PR**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!HS-PR-022-PR**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!SP-bp1-006-R**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!SP-bp1-006-P**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!SP-bp2-019-N**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!SP-bp2-022-N**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!S-pb1-016-N**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!S-pb1-017-N**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!S-pb1-018-N**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}`
- **PL!-bp4-010-N**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1)
EFFECT: ADD_BLADES(2) -> PLAYER`
- **PL!N-bp4-013-N**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: ADD_BLADES(2) -> PLAYER`
- **PL!HS-PR-018-RM**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: ADD_BLADES(2) -> SELF`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{hea...
**Cards:** PL!HS-PR-019-PR, PL!HS-PR-019-RM

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!HS-PR-019-PR**: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3, FROM="DECK_TOP") -> DISCARDED;
CONDITION: COUNT_CARDS(DISCARDED) {FILTER="HEART_BLUE", EQ=3}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=BLUE, DURATION="UNTIL_LIVE_END"}`
- **PL!HS-PR-019-RM**: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
CONDITION: ALL_MEMBERS {FILTER="HEART_04", ZONE="DISCARDED_THIS"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3, FROM="DECK_TOP") -> DISCARDED;
CONDITION: COUNT_CARDS(DISCARDED) {FILTER="HEART_BLUE", EQ=3}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=BLUE, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分の控え室にあるメンバーカード2枚を好きな順番でデッキの一番上に置く。...
**Cards:** PL!HS-PR-020-PR, PL!HS-PR-023-PR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!HS-PR-020-PR**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: MOVE_TO_DECK(2) {FROM="DISCARD", TYPE_MEMBER} -> DECK_TOP`
- **PL!HS-PR-023-PR**: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_CARDS(2, FROM="DISCARD") {FILTER="TYPE=MEMBER"} -> TARGETS; MOVE_TO_DECK(TARGETS) {ORDER="CHOSEN"} -> DECK_TOP`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_CARDS(2, FROM="DISCARD") {FILTER="TYPE=MEMBER"} -> TARGETS; MOVE_TO_DECK(TARGETS) {ORDER="CHOSEN"} -> DECK_TOP
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{hea...
**Cards:** PL!HS-PR-021-PR, PL!HS-PR-021-RM

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!HS-PR-021-PR**: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3, FROM="DECK_TOP") -> DISCARDED;
CONDITION: COUNT_CARDS(DISCARDED) {FILTER="HEART_RED", EQ=3}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=RED, DURATION="UNTIL_LIVE_END"}`
- **PL!HS-PR-021-RM**: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
CONDITION: ALL_MEMBERS {FILTER="HEART_01", ZONE="DISCARDED_THIS"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=1} -> SELF`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3, FROM="DECK_TOP") -> DISCARDED;
CONDITION: COUNT_CARDS(DISCARDED) {FILTER="HEART_RED", EQ=3}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=RED, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}相手に何が好き？と聞く。
回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。
回答があなたの場...
**Cards:** LL-PR-004-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(PLAYER) {OPTIONS=["CHOC_STRAW_COOKIE", "YOU", "OTHER"]} -> CHOICE;
CONDITION: VALUE_EQ(CHOICE, "CHOC_STRAW_COOKIE"); DISCARD_HAND(1, PLAYER); DISCARD_HAND(1, OPPONENT);
CONDITION: VALUE_EQ(CHOICE, "YOU"); DRAW(1, PLAYER); DRAW(1, OPPONENT);
CONDITION: VALUE_EQ(CHOICE, "OTHER"); ADD_BLADES(1, PLAYER) {DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1, OPPONENT) {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分の控え室からメンバーカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札の「上原歩夢」と「澁谷かのん」と「日野下花帆」を、好きな組...
**Cards:** LL-bp1-001-R＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(3) {FILTER="Ayumu/Kanon/Kaho"} (Optional)
EFFECT: BOOST_SCORE(3) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!N-bp1-001-R, PL!N-bp1-001-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: ADD_BLADES(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
{{kidou.png|起動}}{{icon_ene...
**Cards:** PL!N-bp1-002-R＋, PL!N-bp1-002-P, PL!N-bp1-002-P＋, PL!N-bp1-002-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_ene...
**Cards:** PL!N-bp1-003-R＋, PL!N-bp1-003-P, PL!N-bp1-003-P＋, PL!N-bp1-003-SEC

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp1-003-R＋**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: COLOR_SELECT(1) -> PLAYER; ADD_HEARTS(1) -> PLAYER`
- **PL!N-bp1-003-P**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1)
EFFECT: COLOR_SELECT(1) -> PLAYER; ADD_HEARTS(1) -> PLAYER`
- **PL!N-bp1-003-P＋**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: COLOR_SELECT(1) -> PLAYER; ADD_HEARTS(1) -> PLAYER`
- **PL!N-bp1-003-SEC**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: COLOR_SELECT(1) -> PLAYER; ADD_HEARTS(1) -> PLAYER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1)
EFFECT: COLOR_SELECT(1) -> PLAYER; ADD_HEARTS(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}自分のステージにほかの『虹ヶ咲』のメンバーがいる場合、エネルギーを1枚アクティブにする。...
**Cards:** PL!N-bp1-004-R, PL!N-bp1-004-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER", FILTER="GROUP_ID=2"}
EFFECT: ACTIVATE_ENERGY(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!N-bp1-005-R, PL!N-bp1-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。
{...
**Cards:** PL!N-bp1-006-R＋, PL!N-bp1-006-P, PL!N-bp1-006-P＋, PL!N-bp1-006-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE), COUNT_PLAYED_THIS_TURN(PLAYER) {FILTER="UNIT_NIJIGASAKI", GE=1}; ACTIVATE_ENERGY(2)

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: DRAW(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のメンバーカードを1枚控え室に置く：自分の控え室から、これにより控え室に置いたメンバーカードより、コストの低いメンバーカードを...
**Cards:** PL!N-bp1-008-R, PL!N-bp1-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) {FILTER="TYPE=MEMBER"} -> TARGET_VAL
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="COST_LT_TARGET_VAL"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを2枚控え室に置く。その後、自分の控え室からメンバーカードを1枚手札に加える。...
**Cards:** PL!N-bp1-009-R, PL!N-bp1-009-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}; SELECT_RECOVER_MEMBER(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。そのライブカードを手札に加え、これにより公開されたほかのす...
**Cards:** PL!N-bp1-011-R, PL!N-bp1-011-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); REVEAL_UNTIL(FILTER="TYPE=LIVE") -> TARGET; MOVE_TO_HAND(TARGET); MOVE_TO_DISCARD(REMAINDER)
```

---

## Ability: {{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート...
**Cards:** PL!N-bp1-012-R＋, PL!N-bp1-012-P, PL!N-bp1-012-P＋, PL!N-bp1-012-SEC

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER) {GE=3}, COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER, FILTER="UNIT_NIJIGASAKI") {GE=1}
EFFECT: ADD_HEARTS(2) -> SELF; ADD_BLADES(2) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、エールにより公開された自分のカードの中から、『虹ヶ咲』のカードを1枚手札に加える。

(必要ハートを確認する...
**Cards:** PL!N-bp1-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER)
EFFECT: SELECT_CARDS(1) {ZONE="YELL_REVEALED", FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバーが持つ{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{...
**Cards:** PL!N-bp1-027-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: COUNT_HEART_COLORS(PLAYER) {FILTER="UNIT_NIJIGASAKI"} -> COUNT_VAL; BOOST_SCORE(1, PER_CARD=COUNT_VAL) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『虹ヶ咲』のメンバーがいる場合、こ...
**Cards:** PL!N-bp1-028-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE), COUNT_MEMBER(PLAYER) {FILTER="UNIT_NIJIGASAKI", GE=1}; BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブ中のカードが3枚以上ある場合、このカードのスコアを＋２する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロ...
**Cards:** PL!N-bp1-029-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER) {GE=3}
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分のステージにほかのメンバーがいない場合、自分はライブできない。...
**Cards:** PL!SP-bp1-001-R, PL!SP-bp1-001-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {MAX=0, TARGET="OTHER_MEMBER"}
EFFECT: PREVENT_LIVE -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。...
**Cards:** PL!SP-bp1-002-R＋, PL!SP-bp1-002-P, PL!SP-bp1-002-P＋, PL!SP-bp1-002-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: AREA="LEFT_SIDE"
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(2)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ...
**Cards:** PL!SP-bp1-003-R＋, PL!SP-bp1-003-P, PL!SP-bp1-003-P＋, PL!SP-bp1-003-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレ...
**Cards:** PL!SP-bp1-004-R, PL!SP-bp1-004-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: AREA="CENTER"
EFFECT: ADD_BLADES(5) -> SELF
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚まで公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!SP-bp1-005-R, PL!SP-bp1-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(5) {FILTER="GROUP_ID=3"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分のエネルギーが11枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。...
**Cards:** PL!SP-bp1-007-R＋, PL!SP-bp1-007-P, PL!SP-bp1-007-P＋, PL!SP-bp1-007-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_ENERGY(PLAYER) {GE=11}
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}カードを1枚引く。自分のステージに「米女メイ」がいる場合、さらにカードを1枚引く。...
**Cards:** PL!SP-bp1-008-R, PL!SP-bp1-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1); CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NAME=米女メイ", GE=1}; DRAW(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：カードを1枚引き、手札を1枚控え室に置く。...
**Cards:** PL!SP-bp1-009-R, PL!SP-bp1-009-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: DRAW(1); DISCARD_HAND(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分のデッキの上からカ...
**Cards:** PL!SP-bp1-010-R, PL!SP-bp1-010-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(5) {FILTER="GROUP_ID=3"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。...
**Cards:** PL!SP-bp1-012-N, PL!SP-sd1-008-SD, PL!SP-sd1-017-SD

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-bp1-012-N**: `TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(3) -> CARD_HAND`
- **PL!SP-sd1-008-SD**: `TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(3) -> CARD_HAND, DISCARD_REMAINDER`
- **PL!SP-sd1-017-SD**: `TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(3) -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(3) -> CARD_HAND
```

---

## Ability: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

(エールで出た{{icon_sco...
**Cards:** PL!SP-bp1-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER)
EFFECT: ENERGY_CHARGE(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる「澁谷かのん」1人は{{heart_05.png|heart05}}{{icon_blade.png|ブレード}...
**Cards:** PL!SP-bp1-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="NAME=澁谷かのん"} -> TARGET_1; ADD_HEARTS(1) -> TARGET_1 {HEART_TYPE=PINK, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_1 {DURATION="UNTIL_LIVE_END"}
EFFECT: SELECT_MEMBER(1) {FILTER="NAME=唐可可"} -> TARGET_2; ADD_HEARTS(1) -> TARGET_2 {HEART_TYPE=RED, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_2 {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NAME=澁谷かのん", GE=1}, COUNT_MEMBER(PLAYER) {FILTER="NAME=唐可可", GE=1}
EFFECT: DRAW(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストは{{heart_02.png|...
**Cards:** PL!SP-bp1-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_GROUP(5) {GROUP="Liella!", ZONE="STAGE,DISCARD", UNIQUE_NAMES}
EFFECT: SET_HEART_COST {RED=2, YELLOW=2, PURPLE=2}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のエネルギーが12枚以上ある場合、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}...
**Cards:** PL!SP-bp1-027-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUM_ENERGY {MIN=12}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}エネルギーを2枚アクティブにする。...
**Cards:** PL!HS-bp1-001-R, PL!HS-bp1-001-P, PL!N-sd1-008-SD, PL!N-sd1-008-RM

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_ENERGY(2) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}、このメンバーをステージから控え室に置く：自分の控え室からコスト15以下の『蓮ノ空』...
**Cards:** PL!HS-bp1-002-R, PL!HS-bp1-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); MOVE_TO_DISCARD(SELF) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_CARDS(1) {ZONE="DISCARD", FILTER="UNIT_HASUNOSORA, COST_LE=15"} -> TARGET; PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}
```

---

## Ability: {{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
...
**Cards:** PL!HS-bp1-003-R＋, PL!HS-bp1-003-P, PL!HS-bp1-003-P＋, PL!HS-bp1-003-SEC

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_HASUNOSORA, UNIQUE_NAMES", EQ=3}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_HASUNOSORA, COST_LE=4"} -> CARD_HAND
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自...
**Cards:** PL!HS-bp1-004-R＋, PL!HS-bp1-004-P, PL!HS-bp1-004-P＋, PL!HS-bp1-004-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_HASUNOSORA"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_CARDS(ZONE="LIVE_SLOTS") -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。...
**Cards:** PL!HS-bp1-005-R, PL!HS-bp1-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(3, MAX_CHOICE=3, Optional) -> DISCARDED
EFFECT: DRAW(COUNT_CARDS(DISCARDED))
```

---

## Ability: {{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場...
**Cards:** PL!HS-bp1-006-R＋, PL!HS-bp1-006-P, PL!HS-bp1-006-P＋, PL!HS-bp1-006-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NOT_SELF", GE=1}
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_COLOR() -> COLOR_VAL; ADD_HEARTS(1) -> SELF {HEART_TYPE=COLOR_VAL, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。...
**Cards:** PL!HS-bp1-007-R, PL!HS-bp1-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)

COST: PAY_ENERGY(2)
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。...
**Cards:** PL!HS-bp1-008-R, PL!HS-bp1-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3, FROM="DECK_TOP") -> DISCARDED; CONDITION: COUNT_CARDS(DISCARDED) {FILTER="TYPE_MEMBER", EQ=3}; DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『みらくらぱーく！』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!HS-bp1-009-R, PL!HS-bp1-009-P

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!HS-bp1-009-R**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {UNIT="Mirakura"} -> CARD_HAND, DISCARD_REMAINDER`
- **PL!HS-bp1-009-P**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_MIRAKURA"} -> CARD_HAND, DISCARD_REMAINDER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_MIRAKURA"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!HS-bp1-011-N, PL!-bp3-010-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="TYPE_LIVE"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: (エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)...
**Cards:** PL!HS-bp1-019-L, PL!N-sd1-025-SD, PL!SP-sd1-023-SD

*No manual pseudocode found for this ability.*

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『蓮ノ空』のライブカードを1枚手札に加える。

(必要ハートを確認する時、エールで出た{{icon_b...
**Cards:** PL!HS-bp1-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_CARDS(1) {ZONE="YELL_REVEALED", FILTER="UNIT_HASUNOSORA, TYPE_LIVE"} -> CARD_HAND
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを＋１する。

(エールをすべて行った後...
**Cards:** PL!HS-bp1-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="UNIT_HASUNOSORA, TYPE_MEMBER", GE=10}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高く、かつ自分のステージに『蓮ノ空』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状...
**Cards:** PL!HS-bp1-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER), COUNT_MEMBER(PLAYER) {FILTER="UNIT_HASUNOSORA", GE=1}
EFFECT: ENERGY_CHARGE(1)
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『虹ヶ咲』のライブカードを1枚まで公開して手札に加えてもよい。残りを控え室に置く。
{{live_start.png...
**Cards:** PL!N-sd1-001-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_REVEAL(5) {FILTER="UNIT_NIJIGASAKI, TYPE_LIVE"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(ALL) {FILTER="UNIT_NIJIGASAKI, NOT_SELF"} -> TARGETS; ADD_BLADES(1) -> TARGETS {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!N-sd1-004-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のメンバーカードを1枚手札に加える。...
**Cards:** PL!N-sd1-005-SD, PL!N-sd1-005-PRproteinbar

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-sd1-005-SD**: `TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND`
- **PL!N-sd1-005-PRproteinbar**: `TRIGGER: ACTIVATED
COST: DISCARD_HAND(2)
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...
**Cards:** PL!N-sd1-007-SD

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『虹ヶ...
**Cards:** PL!N-sd1-009-SD, PL!N-bp5-014-N

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-sd1-009-SD**: `TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2); DISCARD_HAND(1)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND`
- **PL!N-bp5-014-N**: `TRIGGER: ON_PLAY
EFFECT: DRAW(1)`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2); DISCARD_HAND(1)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy....
**Cards:** PL!N-sd1-010-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードのスコアを＋１する。

(エールをす...
**Cards:** PL!N-sd1-028-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: TOTAL_BLADES {MIN=10, AREA="STAGE"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分のエネルギー6枚につき、カードを1枚引く。...
**Cards:** PL!SP-sd1-001-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: COUNT_ENERGY(PLAYER) -> COUNT_VAL; DIV_VAL(COUNT_VAL, 6) -> DRAW_COUNT; DRAW(DRAW_COUNT)
```

---

## Ability: {{toujyou.png|登場}}手札からコスト4以下の『Liella!』のメンバーカードを1枚ステージに登場させてもよい。
（この効果で既にメンバーがいるエリアにも登場できる。ただし、このターンに...
**Cards:** PL!SP-sd1-002-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) {FROM="HAND", FILTER="GROUP_ID=3, COST_LE=4"} (Optional) -> TARGET; PLAY_MEMBER(TARGET)
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{ic...
**Cards:** PL!SP-sd1-003-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_BLADES(5) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。...
**Cards:** PL!SP-sd1-004-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: GRANT_ABILITY(SELF, TRIGGER="CONSTANT", CONDITION="IS_ON_STAGE", EFFECT="BOOST_SCORE(1)")
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自...
**Cards:** PL!SP-sd1-005-SD

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『Liella!』のメンバーカードを1枚手札に加...
**Cards:** PL!SP-sd1-007-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {FILTER="GROUP_ID=3"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーが9枚以上ある場合、自分のデッキの上からカードを5枚見る。その中から1枚を手札に加え、残り...
**Cards:** PL!SP-sd1-009-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_ENERGY(PLAYER) {GE=9}
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_REVEAL(5) -> CARD_HAND
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のエネルギーデッキから、エネルギーカード...
**Cards:** PL!SP-sd1-011-SD

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: ENERGY_CHARGE(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のエネルギーが9枚以上ある場合、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}...
**Cards:** PL!SP-sd1-026-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUM_ENERGY {MIN=9}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払わないかぎり、自分の手札を2枚控え室に置く。
{{live_s...
**Cards:** PL!SP-pb1-001-R, PL!SP-pb1-001-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを＋１する。...
**Cards:** PL!SP-pb1-002-R, PL!SP-pb1-002-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SUM_ENERGY {MIN=12}
EFFECT: BOOST_SCORE(1) -> PLAYER {TARGET="LIVE"}
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリ...
**Cards:** PL!SP-pb1-003-R, PL!SP-pb1-003-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NOT_UNIT_SYNCRISE", EQ=0}
EFFECT: CYCLE_AREAS(PLAYER, MODE="LEFT"); CYCLE_AREAS(OPPONENT, MODE="LEFT")
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーデッキから、エネルギーカードを1枚...
**Cards:** PL!SP-pb1-004-R, PL!SP-pb1-004-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1)

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(3) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...
**Cards:** PL!SP-pb1-005-R, PL!SP-pb1-005-P＋

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-pb1-005-R**: `TRIGGER: ON_PLAY
EFFECT: ENERGY_CHARGE(1)`
- **PL!SP-pb1-005-P＋**: `TRIGGER: ON_PLAY
EFFECT: ENERGY_CHARGE(1, MODE="WAIT") -> PLAYER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: ENERGY_CHARGE(1, MODE="WAIT") -> PLAYER
```

---

## Ability: {{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
(対...
**Cards:** PL!SP-pb1-006-R, PL!SP-pb1-006-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_POSITION_CHANGE(SELF), ON_PLAY(SELF)
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}エネルギーを2枚アクティブにする。...
**Cards:** PL!SP-pb1-007-R, PL!SP-pb1-007-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_ENERGY(2) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメ...
**Cards:** PL!SP-pb1-008-R, PL!SP-pb1-008-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1); SELECT_AREA(OTHER_AREA) -> TARGET_AREA; SWAP_AREA(SELF, TARGET_AREA)
```

---

## Ability: {{toujyou.png|登場}}自分のステージにほかの『5yncri5e!』のメンバーがいる場合、カードを1枚引く。...
**Cards:** PL!SP-pb1-009-R, PL!SP-pb1-009-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER", FILTER="GROUP_ID=3"}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを＋４する。...
**Cards:** PL!SP-pb1-010-R, PL!SP-pb1-010-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SUM_ENERGY {MIN=10}
EFFECT: INCREASE_COST(4) -> SELF
```

---

## Ability: {{toujyou.png|登場}}「鬼塚冬毬」以外の『Liella!』のメンバー1人をステージから控え室に置いてもよい：自分の控え室から、これにより控え室に置いたメンバーカードを1枚、そのメンバーが...
**Cards:** PL!SP-pb1-011-R, PL!SP-pb1-011-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_NAME='鬼塚冬毬'"} (Optional) -> TARGET; MOVE_TO_DISCARD(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『CatChu!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!SP-pb1-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_CATCHU"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『KALEIDOSCORE』のカードを1枚公開して手札に加えてもよい。残りを控え室に...
**Cards:** PL!SP-pb1-016-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_KALEIDOSCORE"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『5yncri5e!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!SP-pb1-017-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_SYNCRISE"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{jidou.png|自動}}このメンバーがエリアを移動するたび、カードを1枚引く。
(対戦相手のカードの効果でも発動する。)...
**Cards:** PL!SP-pb1-020-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_POSITION_CHANGE
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに名前の異なる『CatChu!』のメンバーが2人以上いる場合、エネルギーを6枚までアクティブにする。その後、自分のエネルギーがすべてアク...
**Cards:** PL!SP-pb1-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(UNIT_CATCHU, STAGE) >= 2
EFFECT: ACTIVATE_ENERGY(6)

TRIGGER: ON_LIVE_START
EFFECT: META_RULE(SCORE_RULE, ALL_ENERGY_ACTIVE) -> BOOST_SCORE(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに名前の異なる『KALEIDOSCORE』のメンバーが2人以上いる場合、このカードのスコアを＋１する。...
**Cards:** PL!SP-pb1-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_KALEIDOSCORE, UNIQUE_NAMES", GE=2}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{...
**Cards:** PL!SP-pb1-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: COUNT_MEMBER(PLAYER) {FILTER="UNIT_SYNCRISE, STATUS=ENTERED_OR_MOVED_THIS_TURN"} -> COUNT_VAL; REDUCE_HEART_COST(COUNT_VAL) -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_...
**Cards:** PL!S-bp2-001-R, PL!S-bp2-001-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) == 0, COUNT_SUCCESS_LIVE(OPPONENT) >= 1
EFFECT: ADD_BLADES(3) -> SELF
```

---

## Ability: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『Aqours』のライブカードを1枚手札に加える。...
**Cards:** PL!S-bp2-002-R, PL!S-bp2-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES(SELF)
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=1"} -> CARD_HAND
```

---

## Ability: {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、ライブ終了時まで、［緑ハート］を得る。...
**Cards:** PL!S-bp2-003-R, PL!S-bp2-003-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_YELL_REVEAL (Once per turn)
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="TYPE_LIVE", MIN=1}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=3, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場...
**Cards:** PL!S-bp2-004-R, PL!S-bp2-004-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_YELL_REVEAL (Once per turn)
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="TYPE_LIVE", EQ=0}
EFFECT: YELL_MULLIGAN
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを7枚見る。その中から{{heart_02.png|heart02}}か{{heart_04.png|he...
**Cards:** PL!S-bp2-005-R＋, PL!S-bp2-005-P, PL!S-bp2-005-P＋, PL!S-bp2-005-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE_REVEAL(7, choose_count=3) {COLOR_FILTER="RED/GREEN/BLUE", TYPE_MEMBER, TARGET=HAND, SOURCE=DECK, REMAINDER="DISCARD"}
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E...
**Cards:** PL!S-bp2-006-R, PL!S-bp2-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(4) (Optional)
EFFECT: PLAY_MEMBER_FROM_DISCARD(2) {TOTAL_COST_LE=4}
```

---

## Ability: {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。
{{live_start.png|...
**Cards:** PL!S-bp2-007-R＋, PL!S-bp2-007-P, PL!S-bp2-007-P＋, PL!S-bp2-007-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_YELL_REVEAL (Once per turn)
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="TYPE_LIVE", MIN=1}, HAND_COUNT(PLAYER) {LE=7}
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_START
COST: SELECT_CARDS(1) {FROM="HAND", FILTER="TYPE_LIVE"} -> TARGET; REVEAL(TARGET); MOVE_TO_DECK(TARGET, TO="DECK_BOTTOM") -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_REORDER_DISCARD(2)
```

---

## Ability: {{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。
{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場してお...
**Cards:** PL!S-bp2-008-R＋, PL!S-bp2-008-P, PL!S-bp2-008-P＋, PL!S-bp2-008-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) {FROM="DISCARD", TYPE_LIVE} -> TARGET; MOVE_TO_DECK(TARGET, TO="DECK_BOTTOM")

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_AQOURS, UNIQUE_NAMES", EQ=3}
EFFECT: COUNT_CARDS(ZONE="YELL_REVEALED", FILTER="TYPE_LIVE") -> LIVE_COUNT; CONDITION: VALUE_GE(LIVE_COUNT, 1); VALUE_GE(LIVE_COUNT, 3) -> IS_THREE; CONDITION: VALUE_EQ(IS_THREE, TRUE); BOOST_SCORE(2) -> SELF; ELSE; BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く。...
**Cards:** PL!S-bp2-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_TO_DECK(1) {ZONE="YELL_REVEALED", TYPE_LIVE, TO="DECK_BOTTOM"}
```

---

## Ability: {{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを＋２する。...
**Cards:** PL!S-bp2-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: DECK_REFRESHED_THIS_TURN
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブカード置き場に「MY舞☆TONIGHT」以外の『Aqours』のライブカードがある場合、ライブ終了時まで、自分のステージのメンバーは{{i...
**Cards:** PL!S-bp2-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_LIVE_ZONE(PLAYER) {FILTER="UNIT_AQOURS, NOT_NAME='MY舞☆TONIGHT'", MIN=1}
EFFECT: SELECT_MEMBER(ALL) -> TARGETS; ADD_BLADES(1) -> TARGETS {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jyouji.png|常時}}このカードは成功ライブカード置き場に置くことができない。
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。...
**Cards:** PL!S-bp2-024-L

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE -> SELF

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレー...
**Cards:** PL!S-bp2-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=2}
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2) -> TARGET {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これによ...
**Cards:** PL!SP-bp2-001-R＋, PL!SP-bp2-001-P, PL!SP-bp2-001-P＋, PL!SP-bp2-001-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中からコスト11以上のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!SP-bp2-002-R, PL!SP-bp2-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_REVEAL(3) {FILTER="COST_GE=11"} -> CARD_HAND, DISCARD_REMAINDER (Optional)
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...
**Cards:** PL!SP-bp2-003-R, PL!SP-bp2-003-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_POSITION_CHANGE (Once per turn)

EFFECT: ENERGY_CHARGE(1, MODE="WAIT") -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}自分のステージにいるメンバーのうち、センターエリアにいるメンバーが最も大きいコストを持つ場合、{{heart_03.png|heart03}}を得る。...
**Cards:** PL!SP-bp2-004-R, PL!SP-bp2-004-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: IS_CENTER(SELF); COUNT_MEMBER(PLAYER) {FILTER="COST_GT=GET_COST(SELF), NOT_CENTER", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=3}
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを7枚見る。その中から『Liella!...
**Cards:** PL!SP-bp2-005-R, PL!SP-bp2-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE(7) {FILTER="GROUP_ID=3"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。
{{kidou.png|起動}}{{turn...
**Cards:** PL!SP-bp2-006-R＋, PL!SP-bp2-006-P, PL!SP-bp2-006-P＋, PL!SP-bp2-006-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER)
EFFECT: SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND

TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) {FILTER="GROUP_ID=3, COST_LE=4"} -> DISCARDED
EFFECT: TRIGGER_REMOTE(DISCARDED, TRIGGER="ON_PLAY")
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『Liella!』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置...
**Cards:** PL!SP-bp2-007-R, PL!SP-bp2-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE(5) {FILTER="GROUP_ID=3, TYPE_MEMBER"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動...
**Cards:** PL!SP-bp2-008-R, PL!SP-bp2-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_AREA(PLAYER, NOT_SELF) -> TARGET_AREA; MOVE_MEMBER(SELF, TARGET_AREA)
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}...
**Cards:** PL!SP-bp2-009-R＋, PL!SP-bp2-009-P, PL!SP-bp2-009-P＋, PL!SP-bp2-009-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
```

---

## Ability: {{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。
{{live_start....
**Cards:** PL!SP-bp2-010-R＋, PL!SP-bp2-010-P, PL!SP-bp2-010-P＋, PL!SP-bp2-010-SEC

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: INCREASE_HEART_COST(1, HEART_TYPE=ANY, TARGET="OPPONENT_LIVE")

TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NOT_SELF", MIN=1}
EFFECT: REDUCE_YELL_COUNT(8) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。...
**Cards:** PL!SP-bp2-011-R, PL!SP-bp2-011-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(2) {FROM="DISCARD", TYPE_LIVE, UNIQUE_NAMES} -> OPTIONS; OPPONENT_CHOOSE(OPTIONS) -> TARGET; ADD_TO_HAND(TARGET)
```

---

## Ability: {{toujyou.png|登場}}自分の控え室からカードを1枚までデッキの一番上に置く。...
**Cards:** PL!SP-bp2-013-N, PL!SP-bp2-014-N, PL!SP-bp2-018-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) -> TARGET {FROM="DISCARD"}; MOVE_TO_DECK(TARGET, TO="DECK_TOP")
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_06.png|he...
**Cards:** PL!SP-bp2-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_02.png|he...
**Cards:** PL!SP-bp2-020-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_03.png|he...
**Cards:** PL!SP-bp2-021-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカード枚数が相手より少ない場合、このカードのスコアを＋１する。...
**Cards:** PL!SP-bp2-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) < COUNT_SUCCESS_LIVE(OPPONENT)
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分の手札の枚数が相手より多い場合、このカードのスコアを＋１する。...
**Cards:** PL!SP-bp2-024-L, PL!SP-bp2-024-SECL

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-bp2-024-L**: `TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAND_COUNT(PLAYER) > HAND_COUNT(OPPONENT)
EFFECT: BOOST_SCORE(1) -> SELF`
- **PL!SP-bp2-024-SECL**: `TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAND_SIZE {TARGET="PLAYER", GREATER_THAN="OPPONENT"}
EFFECT: BOOST_SCORE(1) -> SELF`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAND_SIZE {TARGET="PLAYER", GREATER_THAN="OPPONENT"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分...
**Cards:** PL!SP-bp2-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NAME_IN=['澁谷かのん', 'ウィーン·マルガレーテ', '鬼塚冬毬'], UNIQUE_NAMES", MIN=2}
EFFECT: SELECT_RECOVER_CARD(1) -> CARD_HAND {ZONE="YELL_REVEALED"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からスコア3以下の『蓮ノ空』のラ...
**Cards:** PL!HS-bp2-001-R, PL!HS-bp2-001-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=4, SCORE_LE=3"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを2枚まで手札に加える。
{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがい...
**Cards:** PL!HS-bp2-002-R＋, PL!HS-bp2-002-P, PL!HS-bp2-002-P＋, PL!HS-bp2-002-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_RECOVER_MEMBER(2) {FILTER="COST_LE=2"} -> CARD_HAND

TRIGGER: CONSTANT
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="COST_GT_SELF", MIN=1}
EFFECT: ADD_BLADES(3) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...
**Cards:** PL!HS-bp2-003-R, PL!HS-bp2-003-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_REORDER_DISCARD(3)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。
{{live_start...
**Cards:** PL!HS-bp2-005-R＋, PL!HS-bp2-005-P, PL!HS-bp2-005-P＋, PL!HS-bp2-005-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_MEMBER(PLAYER) {FILTER="NOT_SELF"} -> COUNT_VAL; CONDITION: VALUE_GT(COUNT_VAL, 0); SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_MIRAKURA"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_MEMBER(PLAYER) {FILTER="AREA_LEFT"} -> LEFT_VAL; COUNT_MEMBER(PLAYER) {FILTER="AREA_CENTER"} -> CENTER_VAL; COUNT_MEMBER(PLAYER) {FILTER="AREA_RIGHT"} -> RIGHT_VAL; CONDITION: VALUE_GT(LEFT_VAL, 0), VALUE_GT(CENTER_VAL, 0), VALUE_GT(RIGHT_VAL, 0); ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるメンバーを、それぞれ好きなエリアに移動させてもよい。
{{jyouji.png|常時}}自分のステージにいるほかの『みらくらぱーく！』のメンバー...
**Cards:** PL!HS-bp2-006-R, PL!HS-bp2-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(ALL) -> TARGETS; MOVE_MEMBER(TARGETS)

TRIGGER: CONSTANT
EFFECT: COUNT_MEMBER(PLAYER) {FILTER="UNIT_MIRAKURA, NOT_SELF"} -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF
```

---

## Ability: {{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live...
**Cards:** PL!HS-bp2-007-R＋, PL!HS-bp2-007-P, PL!HS-bp2-007-P＋, PL!HS-bp2-007-SEC

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!HS-bp2-007-R＋**: `TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_CERISE, COST_LT=SELF"}
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> DISCARDED
EFFECT: CONDITION: TYPE_EQ(DISCARDED, "MEMBER"); GET_NAME(DISCARDED) -> NAME_VAL; SELECT_MEMBER(1) {FILTER="NAME=NAME_VAL"} -> TARGET; ADD_HEARTS(1, HEART_TYPE=3) -> TARGET {DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET {DURATION="UNTIL_LIVE_END"}`
- **PL!HS-bp2-007-P**: `TRIGGER: ON_PLAY
CONDITION: BATON_PASS(PLAYER) {FILTER="UNIT_CERISE, COST_LT=SELF"}
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> DISCARDED
EFFECT: CONDITION: TYPE_EQ(DISCARDED, "MEMBER"); GET_NAME(DISCARDED) -> NAME_VAL; SELECT_MEMBER(1) {FILTER="NAME=NAME_VAL"} -> TARGET; ADD_HEARTS(1, HEART_TYPE=3) -> TARGET {DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET {DURATION="UNTIL_LIVE_END"}`
- **PL!HS-bp2-007-P＋**: `TRIGGER: ON_PLAY
CONDITION: BATON_PASS(PLAYER) {FILTER="UNIT_CERISE, COST_LT=SELF"}
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> DISCARDED
EFFECT: CONDITION: TYPE_EQ(DISCARDED, "MEMBER"); GET_NAME(DISCARDED) -> NAME_VAL; SELECT_MEMBER(1) {FILTER="NAME=NAME_VAL"} -> TARGET; ADD_HEARTS(1, HEART_TYPE=3) -> TARGET {DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET {DURATION="UNTIL_LIVE_END"}`
- **PL!HS-bp2-007-SEC**: `TRIGGER: ON_PLAY
CONDITION: BATON_PASS(PLAYER) {FILTER="UNIT_CERISE, COST_LT=SELF"}
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> DISCARDED
EFFECT: CONDITION: TYPE_EQ(DISCARDED, "MEMBER"); GET_NAME(DISCARDED) -> NAME_VAL; SELECT_MEMBER(1) {FILTER="NAME=NAME_VAL"} -> TARGET; ADD_HEARTS(1, HEART_TYPE=3) -> TARGET {DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET {DURATION="UNTIL_LIVE_END"}`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_CERISE, COST_LT=SELF"}
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> DISCARDED
EFFECT: CONDITION: TYPE_EQ(DISCARDED, "MEMBER"); GET_NAME(DISCARDED) -> NAME_VAL; SELECT_MEMBER(1) {FILTER="NAME=NAME_VAL"} -> TARGET; ADD_HEARTS(1, HEART_TYPE=3) -> TARGET {DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}このメンバーよりコストが低い『DOLLCHESTRA』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{...
**Cards:** PL!HS-bp2-008-R, PL!HS-bp2-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_DOLL, COST_LT=SELF"}
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合、ライブ終了時ま...
**Cards:** PL!HS-bp2-009-R, PL!HS-bp2-009-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_MIRAKURA, COST_LT=SELF"}
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!HS-bp2-012-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES(SELF)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="TYPE_MEMBER"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!HS-bp2-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES(SELF)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="TYPE_LIVE"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}カードを1枚引く。ライブ終了時まで、自分はライブできない。...
**Cards:** PL!HS-bp2-014-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1); RESTRICTION(LIVE, DURATION="UNTIL_LIVE_END")
```

---

## Ability: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、カードを2枚引き、手札を1枚控え室に置く。...
**Cards:** PL!HS-bp2-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES(SELF)
EFFECT: DRAW(2); DISCARD_HAND(1)
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...
**Cards:** PL!HS-bp2-016-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_REORDER_DISCARD(2)
```

---

## Ability: {{toujyou.png|登場}}自分の控え室にカードが10枚以上ある場合、カードを1枚引く。...
**Cards:** PL!HS-bp2-017-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_DISCARD {MIN=10}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、...
**Cards:** PL!HS-bp2-018-N

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
CONDITION: IS_MAIN_PHASE
COST: PAY_ENERGY(2)
EFFECT: PLAY_LIVE_FROM_DISCARD(1) -> LIVE_ZONE
EFFECT: REDUCE_LIVE_SET_LIMIT(1) {TARGET="NEXT_LIVE_SET"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{hear...
**Cards:** PL!HS-bp2-019-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="GROUP_ID=4", MIN=1}
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}} | EFFECT: SET_HEART_COST("1/1/0")
  OPTION: {{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}} | EFFECT: SET_HEART_COST("4/4/0")
  OPTION: {{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}} | EFFECT: SET_HEART_COST("5/5/0")
  OPTION: {{no_action.png|何もしない}} | EFFECT: NOP
```

---

## Ability: {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。
{{live_start.png|ライブ開始時}}自分...
**Cards:** PL!HS-bp2-020-L

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: ADD_TAG("UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA") -> SELF

TRIGGER: ON_LIVE_START
EFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="STAGE", FILTER="UNIT_HASU, UNIQUE_NAMES"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart...
**Cards:** PL!HS-bp2-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="GROUP_ID=4, BATON_TOUCHED", MIN=2}
EFFECT: REDUCE_HEART_REQ(1, HEART_TYPE=4) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の控え室に『スリーズブーケ』のライブカードが3枚以上ある場合、このカードのスコアを＋１する。...
**Cards:** PL!HS-bp2-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_DISCARD(PLAYER) {FILTER="UNIT_CERISE, TYPE_LIVE", MIN=3}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart...
**Cards:** PL!HS-bp2-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="GROUP_ID=4, BATON_TOUCHED", MIN=2}
EFFECT: REDUCE_HEART_REQ(1, HEART_TYPE=5) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに「徒町小鈴」が登場しており、かつ「徒町小鈴」よりコストの大きい「村野さやか」が登場している場合、このカードを成功させるための必要ハート...
**Cards:** PL!HS-bp2-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER(PLAYER) {NAME="徒町小鈴"} -> KOSUZU; HAS_MEMBER(PLAYER) {NAME="村野さやか"} -> SAYAKA; VALUE_GT(GET_COST(SAYAKA), GET_COST(KOSUZU))
EFFECT: REDUCE_HEART_REQ(3, HEART_TYPE=ANY) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart...
**Cards:** PL!HS-bp2-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="GROUP_ID=4, BATON_TOUCHED", MIN=2}
EFFECT: REDUCE_HEART_REQ(1, HEART_TYPE=1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージの右サイドエリアに「大沢瑠璃乃」が、左サイドエリアに「安養寺姫芽」が、センターエリアに「藤島慈」がそれぞれ登場している場合、このカードの...
**Cards:** PL!HS-bp2-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: MEMBER_AT_SLOT {NAME="Rurino", SLOT="RIGHT"}, MEMBER_AT_SLOT {NAME="Hime", SLOT="LEFT"}, MEMBER_AT_SLOT {NAME="Megu", SLOT="CENTER"}
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{jyouji.png|常時}}手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。
{{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置...
**Cards:** LL-bp2-001-R＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: COUNT_HAND(PLAYER) {FILTER="NOT_SELF"} -> COUNT_VAL; REDUCE_COST(COUNT_VAL)

TRIGGER: CONSTANT
EFFECT: PREVENT_BATON_TOUCH(SELF)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE) {FILTER="NAME_IN=['渡辺曜', '鬼塚夏美', '大沢瑠璃乃']"} -> DISCARD_COUNT
EFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); ADD_BLADES(1, PER_CARD=DISCARD_COUNT) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}相手の手札の枚数が自分より2枚以上多い場合、自分の控え室からライブカードを1枚手札に加える。...
**Cards:** PL!S-pb1-001-R, PL!S-pb1-001-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: SUM_VALUE(HAND_COUNT(OPPONENT), NEG(HAND_COUNT(PLAYER))) {GE=2}
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得...
**Cards:** PL!S-pb1-002-R, PL!S-pb1-002-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} -> OPPONENT
  OPTION: {{grant_ability.png|能力を得る}} | EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、このメンバーが元々持つハートはす...
**Cards:** PL!S-pb1-003-R, PL!S-pb1-003-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); TRANSFORM_HEART(SELF, FILTER="BASE") -> COLOR_GREEN {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND {ZONE="YELL_REVEALED"}
```

---

## Ability: {{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレ...
**Cards:** PL!S-pb1-005-R, PL!S-pb1-005-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: ENERGY_COUNT(PLAYER) < ENERGY_COUNT(OPPONENT)
EFFECT: ADD_BLADES(3) -> SELF
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_bla...
**Cards:** PL!S-pb1-006-R, PL!S-pb1-006-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_HAND(1) {FILTER="TYPE_LIVE"} -> REVEALED; REVEAL(REVEALED)
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) -> OPPONENT
  OPTION: {{no_action.png|何もしない}} | EFFECT: ADD_BLADES(4) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...
**Cards:** PL!S-pb1-007-R, PL!S-pb1-007-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="TYPE_LIVE", MIN=1}
EFFECT: ENERGY_CHARGE(1, STATUS="TAPPED")
```

---

## Ability: {{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...
**Cards:** PL!S-pb1-008-R, PL!S-pb1-008-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: CHOICE_PLAYER(BOTH) -> TARGET_PLAYER; LOOK_REORDER_DISCARD(2, TARGET=TARGET_PLAYER)
```

---

## Ability: {{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{ic...
**Cards:** PL!S-pb1-009-R, PL!S-pb1-009-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SUM_VALUE(COUNT_SUCCESS_LIVE(PLAYER), COUNT_SUCCESS_LIVE(OPPONENT)) {GE=3}
EFFECT: ADD_BLADES(3) -> SELF
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_04.png|heart04}}を2個以上持つメンバーカード...
**Cards:** PL!S-pb1-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE(4) {FILTER="(TYPE_MEMBER, HEART_TYPE=3, HEART_COUNT_GE=2) OR (TYPE_LIVE, HEART_TYPE=3, HEARTS_REQUIRED_GE=2)"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_02.png|heart02}}を2個以上持つメンバーカード...
**Cards:** PL!S-pb1-014-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE(4) {FILTER="(TYPE_MEMBER, HEART_TYPE=1, HEART_COUNT_GE=2) OR (TYPE_LIVE, HEART_TYPE=1, HEARTS_REQUIRED_GE=2)"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_05.png|heart05}}を2個以上持つメンバーカード...
**Cards:** PL!S-pb1-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE(4) {FILTER="(TYPE_MEMBER, HEART_TYPE=4, HEART_COUNT_GE=2) OR (TYPE_LIVE, HEART_TYPE=4, HEARTS_REQUIRED_GE=2)"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{...
**Cards:** PL!S-pb1-019-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=1"} {MIN=6}
EFFECT: NEGATE_SELF_TRIGGER(ON_LIVE_SUCCESS, DURATION="UNTIL_LIVE_END")

TRIGGER: ON_LIVE_SUCCESS
EFFECT: ENERGY_CHARGE(1, STATUS="TAPPED") -> OPPONENT
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_04.png|heart04}}が合計10個以上ある場合、このカードのス...
**Cards:** PL!S-pb1-020-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=3"} {MIN=10}
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手...
**Cards:** PL!S-pb1-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=5"} {MIN=4}; SURPLUS_HEARTS_COUNT(OPPONENT) {EQ=0}
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き...
**Cards:** PL!S-pb1-022-L, PL!S-pb1-022-L＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}
```

---

## Ability: {{live_success.png|ライブ成功時}}カードを2枚引き、手札を2枚控え室に置く。...
**Cards:** PL!S-pb1-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを1枚引き、手札を1枚控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.p...
**Cards:** PL!-bp3-001-R, PL!-bp3-001-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: DRAW(1); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|...
**Cards:** PL!-bp3-002-R, PL!-bp3-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(2) {FILTER="OPPONENT, COST_LE=4, STATUS=ACTIVE"} -> TARGETS; TAP_MEMBER(TARGETS)

TRIGGER: CONSTANT
EFFECT: COUNT_MEMBER {FILTER="OPPONENT, STATUS=TAPPED"} -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分の控え室から『μ's』のメンバーカードを1枚手札に加える。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブ...
**Cards:** PL!-bp3-003-R, PL!-bp3-003-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_MEMBER (Optional)
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}自分の成功ライブカード...
**Cards:** PL!-bp3-004-R＋, PL!-bp3-004-P, PL!-bp3-004-P＋, PL!-bp3-004-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: COUNT_MEMBER(PLAYER) -> COUNT_VAL; DRAW(COUNT_VAL); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=1}
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるすべてのメンバーをアクティブにする。...
**Cards:** PL!-bp3-005-R, PL!-bp3-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(ALL) {FILTER="STATUS=TAPPED"} -> TARGETS; ACTIVATE_MEMBER(TARGETS)
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}{...
**Cards:** PL!-bp3-006-R, PL!-bp3-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_SUCCESS_LIVE(PLAYER) -> COUNT_VAL; SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2, PER_CARD=COUNT_VAL) -> TARGET {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、1枚をデッキの上に置き、1枚を控え室に置く。...
**Cards:** PL!-bp3-007-R, PL!-bp3-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); LOOK_AND_CHOOSE_SPLIT(3) -> CARD_HAND(1), DECK_TOP(1), DISCARD(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。
{{live_start.png|ライ...
**Cards:** PL!-bp3-008-R＋, PL!-bp3-008-P, PL!-bp3-008-P＋, PL!-bp3-008-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=3, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイト...
**Cards:** PL!-bp3-009-R＋, PL!-bp3-009-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_STAGE {MIN=1, FILTER="COST_GE=13"}
EFFECT: DRAW(1)

TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_03.png|heart03}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_06.png|heart06}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: "{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイ...
**Cards:** PL!-bp3-009-P＋, PL!-bp3-009-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_STAGE {MIN=1, FILTER="COST_GE=13"}
EFFECT: DRAW(1)

TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_03.png|heart03}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_06.png|heart06}} | EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメ...
**Cards:** PL!-bp3-014-N, PL!-bp3-017-N, PL!-bp3-018-N, PL!N-bp3-022-N, PL!N-bp4-016-N

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-bp3-014-N**: `TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: LOOK_REORDER_DISCARD(2)`
- **PL!-bp3-017-N**: `TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: LOOK_REORDER_DISCARD(2)`
- **PL!-bp3-018-N**: `TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: LOOK_REORDER_DISCARD(2)`
- **PL!N-bp3-022-N**: `TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: LOOK_REORDER_DISCARD(2)`
- **PL!N-bp4-016-N**: `TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: LOOK_DECK(2) -> REVEALED
EFFECT: SELECT_REVEALED(ANY) -> DECK_TOP {ORDER="CHOICE"}
EFFECT: DISCARD_REMAINDER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: LOOK_DECK(2) -> REVEALED
EFFECT: SELECT_REVEALED(ANY) -> DECK_TOP {ORDER="CHOICE"}
EFFECT: DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。...
**Cards:** PL!-bp3-019-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {FILTER="GROUP_ID=0"} {MIN=2}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のデッキの上から、自分と相手のステージにいるメンバー1人につき、1枚公開する。それらの中にあるライブカード1枚につき、このカードのスコアを＋１する...
**Cards:** PL!-bp3-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: COUNT_MEMBER {FILTER="ANY"} -> COUNT_VAL; REVEAL_DECK_TOP(COUNT_VAL) -> REVEALED; COUNT_TYPE(REVEALED, "TYPE_LIVE") -> LIVE_COUNT; MOVE_TO_DISCARD(REVEALED)
EFFECT: BOOST_SCORE(1, PER_CARD=LIVE_COUNT) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードを成功させるための必要ハートは{{h...
**Cards:** PL!-bp3-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: TOTAL_BLADES(PLAYER) {MIN=10}
EFFECT: REDUCE_HEART_REQ(2) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{...
**Cards:** PL!-bp3-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=1}
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_03.png|heart03}} | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}
  OPTION: {{heart_06.png|heart06}} | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=2}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}このターン、自分が余剰ハートを持たない場合、このカードのスコアを＋１する。...
**Cards:** PL!-bp3-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_COUNT {MAX=0}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_bl...
**Cards:** PL!-bp3-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(3) -> TARGET {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: HEARTS_COUNT(PLAYER) > HEARTS_COUNT(OPPONENT)
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、...
**Cards:** PL!S-bp3-001-R＋, PL!S-bp3-001-P, PL!S-bp3-001-P＋, PL!S-bp3-001-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、このカードを手札に加えてもよい。この能力は、このカードが自分のエールによって公開されている場合のみ発動する。...
**Cards:** PL!S-bp3-002-R, PL!S-bp3-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: ZONE_EQ(SELF, "YELL_REVEALED"); SCORE(PLAYER) > SCORE(OPPONENT)
EFFECT: MOVE_TO_HAND(SELF) (Optional)
```

---

## Ability: {{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。
{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時...
**Cards:** PL!S-bp3-003-R＋, PL!S-bp3-003-P

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!S-bp3-003-R＋**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(3)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE, MAX=2) (Optional) -> DISCARD_COUNT
EFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2) -> TARGET {PER_CARD=DISCARD_COUNT, DURATION="UNTIL_LIVE_END"}`
- **PL!S-bp3-003-P**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"}
EFFECT: DRAW(3)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE, MAX=2)
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2) -> TARGET {PER_CARD=DISCARD_REMOVED, DURATION="UNTIL_LIVE_END"}`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(3)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE, MAX=2) (Optional) -> DISCARD_COUNT
EFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2) -> TARGET {PER_CARD=DISCARD_COUNT, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: "{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。
{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了...
**Cards:** PL!S-bp3-003-P＋, PL!S-bp3-003-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(3)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE, MAX=2) (Optional) -> DISCARD_COUNT
EFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2) -> TARGET {PER_CARD=DISCARD_COUNT, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!S-bp3-004-R, PL!S-bp3-004-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(4) {FILTER="TYPE_MEMBER"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの枚数が、相手がエールによって公開したカードの枚数より少ない場合、カードを1枚引く。...
**Cards:** PL!S-bp3-005-R, PL!S-bp3-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: REDUCE_YELL_COUNT {LESS_THAN="OPPONENT"}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメン...
**Cards:** PL!S-bp3-006-R＋, PL!S-bp3-006-P, PL!S-bp3-006-P＋, PL!S-bp3-006-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, GROUP_ID=1"} -> TARGET_STAGE; MOVE_TO_DISCARD(TARGET_STAGE) -> SUCCESS; GET_COST(TARGET_STAGE) -> BASE_COST
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {FILTER="GROUP_ID=1, COST_EQ=BASE_COST+2"} -> TARGET_DISCARD; PLAY_STAGE_SPECIFIC_SLOT(TARGET_DISCARD) {SLOT="SAME_SLOT"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤ...
**Cards:** PL!S-bp3-007-R, PL!S-bp3-007-P

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!S-bp3-007-R**: `TRIGGER: ACTIVATED (Once per turn)

COST: PAY_ENERGY(1)
EFFECT: SELECT_PLAYER(1) -> TARGET; MOVE_TO_DECK(1) {FILTER="TYPE_LIVE", FROM="DISCARD", TO="DECK_BOTTOM", PLAYER="TARGET"}
EFFECT: DRAW(1)`
- **PL!S-bp3-007-P**: `TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: SELECT_PLAYER(1) -> TARGET_PLAYER; SELECT_RECOVER_LIVE(1, PLAYER=TARGET_PLAYER) -> DECK_BOTTOM -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1)`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: SELECT_PLAYER(1) -> TARGET_PLAYER; SELECT_RECOVER_LIVE(1, PLAYER=TARGET_PLAYER) -> DECK_BOTTOM -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1)
```

---

## Ability: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。それがスコア6以上の『Aqours』のライブカードの場合、エネルギーを4枚アクテ...
**Cards:** PL!S-bp3-008-R, PL!S-bp3-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND -> CHOSEN_CARD
EFFECT: CONDITION: SELECT_CARD(CHOSEN_CARD) {FILTER="GROUP_ID=1, SCORE_GE=6"}; ACTIVATE_ENERGY(4)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを6枚見る。その中から『Aqours』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く...
**Cards:** PL!S-bp3-009-R, PL!S-bp3-009-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(6) {FILTER="GROUP_ID=1, TYPE_MEMBER"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるメンバーを1人までアクティブにする。...
**Cards:** PL!S-bp3-010-N, PL!S-bp3-011-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET)
```

---

## Ability: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、ステージにいるこのメンバーのコストを＋１する。...
**Cards:** PL!S-bp3-016-N

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: INCREASE_COST(1, PER_CARD="SUCCESS_LIVE") -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、...
**Cards:** PL!S-bp3-019-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: OR(YELL_PILE_CONTAINS {FILTER="TYPE_NOT=BLADE_HEART", MAX=0}, SURPLUS_HEARTS_COUNT {MIN=2})
EFFECT: SET_SCORE(4) -> SELF
```

---

## Ability: {{jidou.png|自動}}［ターン1回］エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい...
**Cards:** PL!S-bp3-020-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_YELL_REVEAL (Once per turn)
CONDITION: YELL_PILE_CONTAINS {FILTER="TYPE=BLADE_HEART", MAX=2}
EFFECT: DISCARD_YELL_PILE (Optional); RE_YELL
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の控え室にあるメンバーカード1枚をデッキの一番上に置いてもよい。そうした場合、ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_...
**Cards:** PL!S-bp3-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: SELECT_RECOVER_MEMBER(1) -> DECK_TOP (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(1) -> TARGET; ADD_BLADES(1) -> TARGET {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージのセンターエリアにコスト9以上の『Aqours』のメンバーがいる場合、以下から1つを選ぶ。
・ライブ終了時まで、自分のステージにいるメン...
**Cards:** PL!S-bp3-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="GROUP_ID=1, COST_GE=9", AREA="CENTER"}
EFFECT: SELECT_MODE(1)
  OPTION: ブレード | EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2) -> TARGET
  OPTION: WAIT | EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバー1人を選ぶ。そのメンバーが持つ{{icon_blade.png|ブレード}}が6つ以上の場合、このカード...
**Cards:** PL!S-bp3-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=1"}
CONDITION: BLADES {MIN=6}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメン...
**Cards:** PL!N-bp3-001-R＋, PL!N-bp3-001-P, PL!N-bp3-001-P＋, PL!N-bp3-001-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、自分のステージにいるこのメンバー以外の『虹ヶ咲』のメンバー1人は、そ...
**Cards:** PL!N-bp3-002-R, PL!N-bp3-002-P

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp3-002-R**: `TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: COLOR_SELECT(1) -> COLOR; SELECT_MEMBER(1) {FILTER="NOT_SELF, GROUP_ID=2"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=COLOR, DURATION="UNTIL_LIVE_END"}`
- **PL!N-bp3-002-P**: `TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: COLOR_SELECT(1) -> COLOR; SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=COLOR, DURATION="UNTIL_LIVE_END"}`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: COLOR_SELECT(1) -> COLOR; SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; ADD_HEARTS(1) -> TARGET {HEART_TYPE=COLOR, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ。そのカードの{{toujyou.png|登場}}能力1つを発動させる。
（{{toujyou....
**Cards:** PL!N-bp3-003-R, PL!N-bp3-003-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: TRIGGER_REMOTE(1) {FILTER="GROUP_ID=2, TYPE_MEMBER, COST_LE_4", FROM="DISCARD"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...
**Cards:** PL!N-bp3-004-R, PL!N-bp3-004-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND
```

---

## Ability: {{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。
{{live_start.png|ライブ開始時}}このターン、自分のステージ...
**Cards:** PL!N-bp3-005-R＋, PL!N-bp3-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_STAGE_ENTRY
CONDITION: COUNT_PLAYED_THIS_TURN {MIN=3}
EFFECT: DRAW_UNTIL(5)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_PLAYED_THIS_TURN {MIN=2}
EFFECT: BOOST_SCORE(1) -> PLAYER
```

---

## Ability: "{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。
{{live_start.png|ライブ開始時}}このターン、自分のステー...
**Cards:** PL!N-bp3-005-P＋, PL!N-bp3-005-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_MEMBER_PLAYED (Once per turn)
CONDITION: VALUE_EQ(COUNT_PLAYED_THIS_TURN, 3)
EFFECT: DRAW_UNTIL(5)

TRIGGER: ON_LIVE_START
CONDITION: VALUE_GE(COUNT_PLAYED_THIS_TURN, 2)
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）...
**Cards:** PL!N-bp3-006-R, PL!N-bp3-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: TAP_SELF
```

---

## Ability: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このメンバーをステージから控え室に置く：自分の手札からコスト13以下の「優木せつ菜」...
**Cards:** PL!N-bp3-007-R, PL!N-bp3-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); SACRIFICE_SELF
EFFECT: SELECT_HAND(1) {FILTER="NAME='Setsuna Yuki', COST_LE_13"} -> TARGET; PLAY_STAGE_SPECIFIC_SLOT(TARGET) {SLOT="SAME_SLOT", MODE="WAIT"}(Optional) -> TARGET_PLAYED
EFFECT: SELECT_ENERGY(1) -> ATTACH_MEMBER(TARGET_PLAYED)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。
{{live_start.png|ライブ開始時}}...
**Cards:** PL!N-bp3-008-R＋, PL!N-bp3-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}; ADD_HEARTS(1) -> TARGET {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。
{{live_start.png|ライブ開始時}...
**Cards:** PL!N-bp3-008-P＋, PL!N-bp3-008-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}; ADD_HEARTS(1) -> TARGET {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、...
**Cards:** PL!N-bp3-009-R＋, PL!N-bp3-009-P, PL!N-bp3-009-P＋, PL!N-bp3-009-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: SELECT_RECOVER_MEMBER(2) (Optional) -> DECK_BOTTOM -> CHOSEN_CARDS; CALC_SUM_COST(CHOSEN_CARDS) -> TOTAL_VAL
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 6); DRAW(1)
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 8); ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 25); GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるメンバーカードを2枚まで、好きな順番でデッキの一番下に置く。...
**Cards:** PL!N-bp3-010-R, PL!N-bp3-010-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: 自分 | EFFECT: SELECT_RECOVER_MEMBER(2) -> DECK_BOTTOM
  OPTION: 相手 | EFFECT: SELECT_RECOVER_MEMBER(2, TARGET="OPPONENT") -> DECK_BOTTOM_OPPONENT
```

---

## Ability: {{toujyou.png|登場}}相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ。そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合、ライブ終了時まで...
**Cards:** PL!N-bp3-011-R, PL!N-bp3-011-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, NOT_NAME='Mia'"} -> TARGET_MEMBER
EFFECT: CONDITION: HAS_MATCHING_HEART(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_COST(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_BASE_BLADE(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中から『虹ヶ咲』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!N-bp3-012-R, PL!N-bp3-012-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(4) {FILTER="GROUP_ID=2"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを2枚引く。（メンバーの下に置かれているエネルギーカードではコストを...
**Cards:** PL!N-bp3-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional)
EFFECT: DRAW(2)
```

---

## Ability: {{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_04.png|heart04}}の...
**Cards:** PL!N-bp3-014-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: {{heart_01.png|heart01}} | EFFECT: TRANSFORM_BASE_HEART(1) -> SELF
  OPTION: {{heart_03.png|heart03}} | EFFECT: TRANSFORM_BASE_HEART(3) -> SELF
  OPTION: {{heart_04.png|heart04}} | EFFECT: TRANSFORM_BASE_HEART(4) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{heart_02.png|heart02}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}の...
**Cards:** PL!N-bp3-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: {{heart_02.png|heart02}} | EFFECT: TRANSFORM_BASE_HEART(2) -> SELF
  OPTION: {{heart_05.png|heart05}} | EFFECT: TRANSFORM_BASE_HEART(5) -> SELF
  OPTION: {{heart_06.png|heart06}} | EFFECT: TRANSFORM_BASE_HEART(6) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバー1人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい。そうした場合、ライブ終了時まで、そのメンバーは...
**Cards:** PL!N-bp3-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="HAS_ATTACHED_ENERGY"} -> TARGET_MEMBER; SELECT_ATTACHED_ENERGY(VARIABLE, TARGET_MEMBER) -> REMOVED_COUNT; MOVE_TO_ENERGY_DECK(REMOVED_COUNT)
EFFECT: ADD_HEARTS(3) -> TARGET_MEMBER {HEART_TYPE=1, PER_CARD=REMOVED_COUNT, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にスコアが１か５のカードがある場合、このカードのスコアを＋１する。それらが両方ある場合、代わりにスコアを＋２する。...
**Cards:** PL!N-bp3-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: IF (SUCCESS_PILE_CONTAINS_SCORE(1)) { BOOST_SCORE(1) -> SELF }
EFFECT: IF (SUCCESS_PILE_CONTAINS_SCORE(5)) { BOOST_SCORE(1) -> SELF }
```

---

## Ability: {{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる...
**Cards:** PL!N-bp3-027-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_CONTAINS {HEART_TYPE=4, MIN=1}
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=2"}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る。その中から1枚までをデッキの上に置き、残りを控え室に置く。そ...
**Cards:** PL!N-bp3-028-L, PL!N-bp3-028-SECL

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp3-028-L**: `TRIGGER: ON_LIVE_START
EFFECT: COUNT_MEMBER {FILTER="GROUP_ID=2"} -> COUNT_VAL; LOOK_REORDER_DISCARD(COUNT_VAL)
EFFECT: REVEAL_DECK_TOP(1) -> REVEALED; CONDITION: SELECT_CARD(REVEALED) {FILTER="TYPE_LIVE"}; BOOST_SCORE(1) -> SELF`
- **PL!N-bp3-028-SECL**: `TRIGGER: ON_LIVE_START
EFFECT: LOOK_DECK_DYNAMIC_COUNT(1) {PER_CARD="STAGE", FILTER="GROUP_ID=2"}; MOVE_TO_DECK_TOP(1) (Optional); DISCARD_REMAINDER
EFFECT: REVEAL_DECK_TOP(1)
CONDITION: REVEALED_CARDS {FILTER="TYPE_LIVE"}
EFFECT: BOOST_SCORE(1) -> SELF`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_START
EFFECT: LOOK_DECK_DYNAMIC_COUNT(1) {PER_CARD="STAGE", FILTER="GROUP_ID=2"}; MOVE_TO_DECK_TOP(1) (Optional); DISCARD_REMAINDER
EFFECT: REVEAL_DECK_TOP(1)
CONDITION: REVEALED_CARDS {FILTER="TYPE_LIVE"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に{{icon_b_all.png|ALLブレード}}を持つカードが1枚以上ある場合、このカードのスコアを＋...
**Cards:** PL!N-bp3-030-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: YELL_PILE_CONTAINS {FILTER="HAS_ALL_BLADE"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを＋１する。...
**Cards:** PL!N-bp3-031-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: BOOST_SCORE(1, PER_CARD="STAGE", FILTER="STATUS=TAPPED") -> SELF
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚まで...
**Cards:** LL-bp3-001-R＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: MOVE_TO_DECK(6) {FILTER="Umi/Yoshiko/Rina", FROM="DISCARD"}
EFFECT: ACTIVATE_ENERGY(6) -> PLAYER

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(6)
EFFECT: ADD_BLADES(3) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカ...
**Cards:** PL!-pb1-001-R, PL!-pb1-001-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: ライブカード | EFFECT: REVEAL_UNTIL(TYPE_LIVE) -> CARD_HAND; DISCARD_REMAINDER
  OPTION: コスト10以上のメンバー | EFFECT: REVEAL_UNTIL(TYPE_MEMBER, COST_GE_10) -> CARD_HAND; DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元...
**Cards:** PL!-pb1-002-R, PL!-pb1-002-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY, ON_LIVE_START
CONDITION: ALL_MEMBERS {FILTER="UNIT_BIBI"}
COST: TAP_SELF (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BASE_BLADES_LE_3"} -> TARGET; TAP_MEMBER(TARGET)

TRIGGER: CONSTANT
CONDITION: SELECT_MEMBER(1) {FILTER="OPPONENT, STATUS=TAPPED"} -> TARGET_VAL
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=6, PER_CARD=TARGET_VAL}
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『Printemps』のメンバー1人につき、エネルギーを1枚アクティブにする。...
**Cards:** PL!-pb1-003-R, PL!-pb1-003-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: COUNT_MEMBER {FILTER="UNIT_PRINTEMPS"} -> COUNT_VAL; ACTIVATE_ENERGY(COUNT_VAL)
```

---

## Ability: {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時...
**Cards:** PL!-pb1-004-R, PL!-pb1-004-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: IS_CENTER
EFFECT: SUCCESS_PILE_COUNT {FILTER="GROUP_ID=0, HAS_SCORE=TRUE"} -> COUNT_VAL
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"} (CONDITION: VALUE_EQ(COUNT_VAL, 1))
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(2) -> PLAYER", DURATION="UNTIL_LIVE_END"} (CONDITION: VALUE_GE(COUNT_VAL, 2))
```

---

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にカードがある場合、カードを1枚引く。...
**Cards:** PL!-pb1-005-R, PL!-pb1-005-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_SUCCESS_LIVE {MIN=1}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く。その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く。...
**Cards:** PL!-pb1-006-R, PL!-pb1-006-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> DECK_TOP (Optional)
EFFECT: CONDITION: SELECT_MEMBER(1) {FILTER="OPPONENT, STATUS=TAPPED"}
EFFECT: DRAW(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカード...
**Cards:** PL!-pb1-007-R, PL!-pb1-007-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
CONDITION: SELECT_MEMBER(1) {FILTER="UNIT_LILY_WHITE, NOT_SELF"}
COST: SUCCESS_PILE_COUNT -> SUCCESS_VAL; SUB(3, SUCCESS_VAL) -> DISCARD_COUNT; DISCARD_HAND(DISCARD_COUNT)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}メンバーを3人までウェイトにしてもよい：これによりウェイト状態にしたメンバー1人につき、カードを1枚引く。...
**Cards:** PL!-pb1-008-R, PL!-pb1-008-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: SELECT_MEMBER(3) -> TARGETS; TAP_MEMBER(TARGETS) (Optional) -> TAPPED_COUNT
EFFECT: DRAW(TAPPED_COUNT)
```

---

## Ability: {{toujyou.png|登場}}相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする。
{{toujyou.png|登場}}このタ...
**Cards:** PL!-pb1-009-R, PL!-pb1-009-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BASE_BLADES_LE_1"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DISABLE_ACTIVATE_BY_EFFECT(ALL_MEMBERS) {DURATION="UNTIL_TURN_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるほかのメンバーは{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!-pb1-010-R, PL!-pb1-010-P＋

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-pb1-010-R**: `TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: ADD_BLADES(1) -> PLAYER {TARGET="OTHER_MEMBER"}`
- **PL!-pb1-010-P＋**: `TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: SELECT_MEMBER(ALL) {FILTER="OTHER_MEMBERS"} -> TARGET; ADD_BLADES(1) -> TARGET`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: SELECT_MEMBER(ALL) {FILTER="OTHER_MEMBERS"} -> TARGET; ADD_BLADES(1) -> TARGET
```

---

## Ability: {{toujyou.png|登場}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、相手のステージにいるコスト4以下のメンバー1人をウェイトにする。...
**Cards:** PL!-pb1-011-R, PL!-pb1-011-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: COUNT_GROUP {MIN=2, FILTER="UNIT_BIBI", UNIQUE_NAMES=TRUE}
EFFECT: TAP_OPPONENT(1) -> OPPONENT {FILTER="COST_LE_4"}
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいる『Printemps』のメンバーを1人までアクティブにする。...
**Cards:** PL!-pb1-012-R, PL!-pb1-012-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {FILTER="UNIT_PRINTEMPS"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する...
**Cards:** PL!-pb1-013-R, PL!-pb1-013-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: SELECT_HAND(1) {TARGET="OPPONENT_HIDDEN"} -> REVEAL -> REVEALED_CARD
EFFECT: CONDITION: SELECT_CARD(REVEALED_CARD) {FILTER="TYPE_LIVE"}
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jyouji.png|常時}}自分の成功ライブカード置き場に『lilywhite』のカードがある場合、手札にあるこのメンバーカードのコストは2減る。...
**Cards:** PL!-pb1-014-R, PL!-pb1-014-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SUCCESS_PILE_COUNT {FILTER="UNIT_LILYWHITE", MIN=1}
EFFECT: REDUCE_COST(2) -> PLAYER {ZONE="HAND"}
```

---

## Ability: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージに...
**Cards:** PL!-pb1-015-R, PL!-pb1-015-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY, ON_LIVE_START
CONDITION: IS_CENTER
COST: SELECT_MEMBER(1) {FILTER="UNIT_BIBI"} -> TARGET; TAP_MEMBER(TARGET) (Optional)
EFFECT: TAP_OPPONENT(1)

TRIGGER: ON_MEMBER_TAP {FILTER="OPPONENT, COST_LE_4", REASON="EFFECT"} (Once per turn)
EFFECT: DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中から『lilywhite』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!-pb1-016-R, PL!-pb1-016-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(4) {UNIT="lilywhite"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：カードを1枚引く。その後、このメンバーが『Printemps』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え...
**Cards:** PL!-pb1-017-R, PL!-pb1-017-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: DRAW(1); CONDITION: NOT BATON_FROM_UNIT_PRINTEMPS
EFFECT: DISCARD_HAND(1)
```

---

## Ability: {{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリア...
**Cards:** PL!-pb1-018-R, PL!-pb1-018-P＋

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-pb1-018-R**: `TRIGGER: ON_PLAY
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"}; PREVENT_PLAY_TO_SLOT -> SLOT
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"} -> OPPONENT; PREVENT_PLAY_TO_SLOT -> SLOT`
- **PL!-pb1-018-P＋**: `TRIGGER: ON_PLAY
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"}; PREVENT_PLAY_TO_SLOT -> SLOT 
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"} -> OPPONENT; PREVENT_PLAY_TO_SLOT -> SLOT`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"}; PREVENT_PLAY_TO_SLOT -> SLOT 
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"} -> OPPONENT; PREVENT_PLAY_TO_SLOT -> SLOT
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる『Printemps』のメンバーをアクティブにする。これによりウェイト状態のメンバーが3人以上アクティブ状態になったとき、このカー...
**Cards:** PL!-pb1-028-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(ALL) {FILTER="UNIT_PRINTEMPS"} -> PLAYER -> RECOVERY_COUNT
CONDITION: VALUE_GE(RECOVERY_COUNT, 3)
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカードが0枚で、かつ自分のステージにいるメンバーが『lilywhite』のみの場合、このカードのスコアを＋１する。...
**Cards:** PL!-pb1-029-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE {MAX=0}, COUNT_STAGE {ALL=TRUE, FILTER="UNIT_LILYWHITE"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}相手のステージにウェイト状態のメンバーがいる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart...
**Cards:** PL!-pb1-030-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SELECT_MEMBER(1) {FILTER="OPPONENT, STATUS=TAPPED"}
EFFECT: REDUCE_HEART_REQ(2) -> SELF

TRIGGER: ON_LIVE_SUCCESS
CONDITION: DISCARD_UNIQUE_NAMES_COUNT {FILTER="UNIT_BIBI, TYPE_MEMBER", MIN=2}
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_BIBI"} -> CARD_HAND
```

---

## Ability: {{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：エールにより公開された自分のカードの中から、『μ's』のメンバーカードを1枚手札に加える。...
**Cards:** PL!-pb1-031-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(1) {FILTER="GROUP_ID=0", SOURCE="YELL"} -> CARD_HAND
```

---

## Ability: {{live_success.png|ライブ成功時}}自分の成功ライブカード置き場に『μ's』のカードがある場合、カードを1枚引く。...
**Cards:** PL!-pb1-032-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_SUCCESS_LIVE {MIN=1, FILTER="GROUP_ID=0"}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを1枚引く。...
**Cards:** PL!-bp4-001-R, PL!-bp4-001-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COST_LEAD {TARGET="OPPONENT", MODE="REVERSED"}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあ...
**Cards:** PL!-bp4-002-R＋, PL!-bp4-002-P, PL!-bp4-002-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: HAS_LIVE_CARD {HAS_ABILITY=FALSE}
EFFECT: ADD_HEARTS(2) -> SELF {HEART_TYPE=6, DURATION="UNTIL_LIVE_END"}

TRIGGER: ACTIVATED (Once per turn)
CONDITION: SUM_SCORE {MIN=6}
COST: DISCARD_HAND(2)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
```

---

## Ability: {{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあ...
**Cards:** PL!-bp4-002-SEC

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: HAS_LIVE_CARD {HAS_ABILITY=FALSE}
EFFECT: ADD_HEARTS(2) -> SELF {HEART_TYPE=6, DURATION="UNTIL_LIVE_END"}

TRIGGER: ACTIVATED (Once per turn)
CONDITION: SUM_SCORE {MIN=7}
COST: DISCARD_HAND(2)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、エネルギーを2枚アクティブにする。...
**Cards:** PL!-bp4-004-R, PL!-bp4-004-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: SCORE_TOTAL {MIN=6}
EFFECT: ACTIVATE_ENERGY(2) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。
{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１す...
**Cards:** PL!-bp4-005-R＋, PL!-bp4-005-P, PL!-bp4-005-P＋, PL!-bp4-005-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="COST_LE_2"} -> CARD_HAND

TRIGGER: CONSTANT
CONDITION: IS_CENTER
EFFECT: BOOST_SCORE(1) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: IS_CENTER, NOT SELECT_MEMBER(1) {FILTER="GROUP_ID=0, BLADES_GE_5"}
EFFECT: MOVE_MEMBER(SELF) -> PLAYER {MODE="OUT_OF_CENTER"}
```

---

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合、自分のデッキの上からカードを5枚見る。その中から『μ's』のメンバーカードを1枚公開して手札に...
**Cards:** PL!-bp4-006-R, PL!-bp4-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: SCORE_TOTAL {MIN=3}
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="GROUP_ID=0"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１す...
**Cards:** PL!-bp4-007-R, PL!-bp4-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: SUCCESS_PILE_COUNT {MIN=1}, SUM_SCORE {LE=1}
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ステージにいるこのメンバーのコストを＋３する。...
**Cards:** PL!-bp4-008-R, PL!-bp4-008-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SCORE_TOTAL {MIN=6}
EFFECT: INCREASE_COST(3) -> SELF
```

---

## Ability: {{toujyou.png|登場}}相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。...
**Cards:** PL!-bp4-009-R, PL!-bp4-009-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: TAP_OPPONENT(1) -> OPPONENT
```

---

## Ability: {{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}...
**Cards:** PL!-bp4-011-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: SELECT_MEMBER(ALL) {FILTER="GROUP_ID=0, AREA=CENTER"} -> TARGET; ADD_BLADES(2) -> TARGET
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{heart_01.png|heart01}...
**Cards:** PL!-bp4-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: ADD_HEARTS(1) -> OTHER_MEMBER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持...
**Cards:** PL!-bp4-014-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_LIVE_CARD {HAS_ABILITY=FALSE}
EFFECT: ADD_BLADES(2) -> OTHER_MEMBER
```

---

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合、カードを1枚引く。...
**Cards:** PL!-bp4-016-N, PL!-bp5-015-N

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-bp4-016-N**: `TRIGGER: ON_PLAY
CONDITION: SCORE_TOTAL {MIN=3}
EFFECT: DRAW(1) -> PLAYER`
- **PL!-bp5-015-N**: `TRIGGER: ON_PLAY
CONDITION: SUCCESS_LIVE_SCORE_TOTAL {MIN=3}
EFFECT: DRAW(1)`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
CONDITION: SUCCESS_LIVE_SCORE_TOTAL {MIN=3}
EFFECT: DRAW(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}...
**Cards:** PL!-bp4-017-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: TAP_MEMBER(1) (Optional) -> SELF
EFFECT: ADD_BLADES(1) -> PLAYER {TARGET="CENTER", FILTER="GROUP_ID=0"}
```

---

## Ability: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}...
**Cards:** PL!-bp4-018-N

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SCORE_LEAD {TARGET="OPPONENT"}
EFFECT: ADD_BLADES(2) -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを＋５する。...
**Cards:** PL!-bp4-019-L

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: CARD_ZONE="SUCCESS_PILE", COUNT_MEMBER(1) {FILTER="GROUP_ID=0"}
EFFECT: BOOST_SCORE(5) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが『μ's』のみの場合、自分のステージにいるメンバー1人をポジションチェンジさせてもよい。
{{jyouji.png|常時...
**Cards:** PL!-bp4-020-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: ALL_MEMBERS {FILTER="GROUP_ID=0"}
EFFECT: SELECT_MEMBER(1) -> TARGET; MOVE_MEMBER(TARGET) -> PLAYER (Optional)

TRIGGER: CONSTANT
CONDITION: CARD_ZONE="SUCCESS_PILE", SELECT_MEMBER(1) {FILTER="GROUP_ID=0, AREA=CENTER"} -> TARGET_CENTER
EFFECT: ADD_BLADES(1) -> TARGET_CENTER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、このカードを成功させるための必要ハートを{{heart_00.png|heart...
**Cards:** PL!-bp4-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SCORE_TOTAL {MIN=6}
EFFECT: REDUCE_HEART_REQ(ALL) -> SELF

CONDITION: SCORE_TOTAL {MIN=9}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のセンターエリアに{{icon_blade.png|ブレード}}を9つ以上持つ『μ's』のメンバーがいる場合、このカードのスコアを＋２する。...
**Cards:** PL!-bp4-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SELECT_MEMBER(1) {FILTER="GROUP_ID=0, AREA=CENTER, BLADES_GE_9"}
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分が余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合、カードを1枚引く。...
**Cards:** PL!-bp4-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAS_EXCESS_HEART {FILTER="COLOR_PINK"}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!-bp4-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: ADD_BLADES(1) -> PLAYER {FILTER="GROUP_ID=0"}
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のエネルギーが相手より少ない場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...
**Cards:** PL!N-bp4-001-R, PL!N-bp4-001-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: ENERGY_LAGGING
EFFECT: ACTIVATE_ENERGY(1, MODE="WAIT") -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの一番上のカードを見る。自分はそのカードを控え室に置いてもよい。...
**Cards:** PL!N-bp4-002-R, PL!N-bp4-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: CHOICE_PLAYER(1) -> PLAYER_TARGET
EFFECT: LOOK_DECK_TOP(1, TARGET=PLAYER_TARGET) -> REVEALED_CARD
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: 控え室に置く | EFFECT: DISCARD_CARD(REVEALED_CARD)
  OPTION: デッキの上に置く | EFFECT: PASS
```

---

## Ability: {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、カードを1枚引く。...
**Cards:** PL!N-bp4-003-R, PL!N-bp4-003-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD {TARGET="OPPONENT"}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}カードを1枚引く。相手のステージにいるコスト9以下のメンバーを1人までウェイトにする。
{{live_start.png|ライブ開始時}}相手のステー...
**Cards:** PL!N-bp4-004-R＋, PL!N-bp4-004-P, PL!N-bp4-004-P＋, PL!N-bp4-004-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: DRAW(1); SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_9"} -> TARGET; TAP_MEMBER(1) -> TARGET (Optional)
EFFECT: COUNT_MEMBER {FILTER="OPPONENT, STATUS=TAPPED"} -> COUNT_VAL
EFFECT: SELECT_RECOVER_MEMBER(COUNT_VAL) {FILTER="GROUP_ID=2", ZONE="DISCARD"} -> DECK_TOP {ORDER="CHOICE"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|...
**Cards:** PL!N-bp4-005-R, PL!N-bp4-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: TAP_OPPONENT(2) {FILTER="COST_LE_4"}
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の手札からコスト4以下の『虹ヶ咲』のメンバーカードを1枚ステ...
**Cards:** PL!N-bp4-006-R, PL!N-bp4-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_HAND(1) {FILTER="GROUP_ID=2, COST_LE_4, TYPE_MEMBER"} -> PLAY_STAGE_EMPTY -> TARGET_PLAYED
EFFECT: CONDITION: SELECT_CARD(TARGET_PLAYED) {FILTER="HAS_HEART_REQUIRED_ANY_COLOR"}
EFFECT: TAP_MEMBER(TARGET_PLAYED)
```

---

## Ability: {{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{h...
**Cards:** PL!N-bp4-007-R＋, PL!N-bp4-007-P, PL!N-bp4-007-P＋, PL!N-bp4-007-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND; SELECT_RECOVER_LIVE(1, TARGET="OPPONENT") -> CARD_HAND_OPPONENT

TRIGGER: CONSTANT
CONDITION: SUM_ENERGY_OF_BOTH_PLAYERS {MIN=15}
EFFECT: ADD_HEARTS(2) -> SELF {HEART_TYPE=2}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER; PLACE_ENERGY_WAIT(1) -> OPPONENT
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：エネルギー1枚か『虹ヶ咲』のメンバー1人をアクティブにする。...
**Cards:** PL!N-bp4-008-R, PL!N-bp4-008-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1)
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: エネルギー1枚をアクティブにする | EFFECT: ACTIVATE_ENERGY(1)
  OPTION: 『虹ヶ咲』のメンバー1人をアクティブにする | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(1) -> TARGET
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを2枚引き、自分の手札を1枚デッキの一番上に置く。...
**Cards:** PL!N-bp4-009-R, PL!N-bp4-009-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUM_COST {TARGET="PLAYER", STAGE=TRUE, LESS_THAN="OPPONENT"}
EFFECT: DRAW(2) -> PLAYER; MOVE_TO_DECK(1) {FROM="HAND", TO="DECK_TOP"}
```

---

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード...
**Cards:** PL!N-bp4-010-R＋, PL!N-bp4-010-P, PL!N-bp4-010-P＋, PL!N-bp4-010-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: SELECT_SUCCESS_LIVE(1) {FILTER="GROUP_ID=2"} -> DISCARD (Optional)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=2", ZONE="DISCARD"} -> SUCCESS_PILE

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE_CARD(1) -> TARGET_LIVE; CONDITION: SUCCESS_PILE_CONTAINS_NAME(TARGET_LIVE)
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
{{live_success....
**Cards:** PL!N-bp4-011-R＋, PL!N-bp4-011-P, PL!N-bp4-011-P＋, PL!N-bp4-011-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: SELECT_HAND(1) {FILTER="TYPE_LIVE"} -> DISCARD (Optional)
EFFECT: HEART_COLOR_SELECT(1) -> COLOR; ADD_HEARTS(1) -> SELF {HEART_TYPE=COLOR, DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DISCARD_DECK(5)
CONDITION: DISCARD_UNIQUE_NAMES_COUNT {FILTER="GROUP_ID=2, TYPE_LIVE", MIN=3}
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND
```

---

## Ability: {{jyouji.png|常時}}相手の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ライブの合計スコアを＋１する。...
**Cards:** PL!N-bp4-012-R, PL!N-bp4-012-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SUM_SCORE {TARGET="OPPONENT", SUCCESS_PILE=TRUE, MIN=6}
EFFECT: BOOST_SCORE(1) -> PLAYER
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、このメンバーがアクティブ状態からウェイト状態になったとき、カードを1枚引き、手札を1枚控え室に置く。...
**Cards:** PL!N-bp4-018-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_SELF_TAPPED
CONDITION: MAIN_PHASE, TURN_PLAYER=SELF
EFFECT: DRAW(1); DISCARD_HAND(1) (Once per turn)
```

---

## Ability: {{toujyou.png|登場}}自分の控え室にあるカード1枚をデッキの一番上に置いてもよい。...
**Cards:** PL!N-bp4-021-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DECK(1) {FROM="DISCARD", TO="DECK_TOP"}
```

---

## Ability: {{toujyou.png|登場}}『虹ヶ咲」のメンバー1人をウェイトにしてもよい：カードを1枚引き、手札を1枚控え室に置く。...
**Cards:** PL!N-bp4-023-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=2"} -> TARGET; TAP_MEMBER(1) -> TARGET (Optional)
EFFECT: DRAW(1); DISCARD_HAND(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[紫ブレード]、{{ico...
**Cards:** PL!N-bp4-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: TRANSFORM_YELL_BLADES(ALL) -> 5 {FILTER="NOT_BLADE_TYPE_5", DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: SELECT_YELL(1) {FILTER="GROUP_ID=2, HAS_HEART_REQUIRED_ANY_COLOR"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そ...
**Cards:** PL!N-bp4-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_RECOVERED_FROM_DISCARD
CONDITION: MAIN_PHASE
EFFECT: SELECT_HAND(1) {FILTER="NAME='DIVE!'", TYPE_LIVE} -> LIVE_PLAY
EFFECT: REDUCE_LIVE_SET_LIMIT(1) {NEXT_TURN=TRUE}

TRIGGER: ON_SET_TO_LIVE_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=2"} -> TARGET; ADD_BLADES(2) -> TARGET
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード名が「EMOTION」のカード1枚につき、このカードのスコアを＋２し、成功させるための必要ハートを{{hear...
**Cards:** PL!N-bp4-027-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="SUCCESS_LIVE", FILTER="NAME=EMOTION"}
EFFECT: INCREASE_HEART_COST(3) {HEART_TYPE=0} -> SELF {PER_CARD="SUCCESS_LIVE", FILTER="NAME=EMOTION"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが4枚以上ある場合、このカードのスコアを＋１する。6枚以上ある場合、代わりにスコアを＋２する。...
**Cards:** PL!N-bp4-028-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_DISCARD {MIN=4, FILTER="GROUP_ID=2, TYPE_LIVE, UNIQUE_NAMES"}
EFFECT: BOOST_SCORE(1) -> SELF
CONDITION: COUNT_DISCARD {MIN=6, FILTER="GROUP_ID=2, TYPE_LIVE, UNIQUE_NAMES"}
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}このゲームの1ターン目のライブフェイズの場合、このカードのスコアを＋１し、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{ico...
**Cards:** PL!N-bp4-029-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START (Once per turn)

EFFECT: BOOST_SCORE(1) -> SELF; ADD_BLADES(1) -> PLAYER {FILTER="GROUP_ID=2", TARGET="MEMBER"}
```

---

## Ability: {{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。
・自分のエネルギーデッキから、エネルギー...
**Cards:** PL!N-bp4-030-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: CHOICE_MODE (MIN=1) -> PLAYER
  CONDITION: NOT_HAS_SUCCESS_LIVE {FILTER="GROUP_ID=2"} -> CHOICE_MODE(COUNT=1)
  OPTION: エネルギー | EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
  OPTION: メンバー | EFFECT: SELECT_RECOVER_MEMBER(1) -> CARD_HAND
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージのエリアすべてに『虹ヶ咲』のメンバーがいて、かつそれらのコストの合計が20以上の場合、カードを3枚引き、自分の手札を3枚好きな順番でデッ...
**Cards:** PL!N-bp4-031-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: IS_OCCUPIED_ALL_AREAS, ALL_MEMBERS {FILTER="GROUP_ID=2"}, SUM_COST {MIN=20}
EFFECT: DRAW(3); SELECT_HAND(3) -> DECK_TOP {ORDER="CHOICE"}
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるメンバーが『Liella!』のみで、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く...
**Cards:** PL!SP-bp4-001-R, PL!SP-bp4-001-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: ALL_MEMBERS {FILTER="GROUP_ID=3"}, ENERGY_COUNT {MIN=7}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを4枚見る。その中から必要ハートの合計が8以上の『Liella!』のライブカードを1枚公開して手札に加...
**Cards:** PL!SP-bp4-002-R, PL!SP-bp4-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_MEMBER (Optional)
EFFECT: LOOK_AND_CHOOSE(4) {FILTER="SUM_HEART_TOTAL_GE=8, GROUP_ID=3, TYPE_LIVE"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}【左サイド】【右サイド】カードを2枚引き、手札を2枚控え室に置く。（この能力は左サイドエリアか右サイドエリアに登場した場合のみ発動する。）
{{jyouji.png...
**Cards:** PL!SP-bp4-003-R, PL!SP-bp4-003-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: AREA_IN=["LEFT_SIDE", "RIGHT_SIDE"]
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER

TRIGGER: CONSTANT
CONDITION: AREA="CENTER"
EFFECT: ADD_BLADES(2) -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。
{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメン...
**Cards:** PL!SP-bp4-004-R＋, PL!SP-bp4-004-P, PL!SP-bp4-004-P＋, PL!SP-bp4-004-SEC

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: BATON_TOUCH_MOD(2) (Optional) -> SELF

TRIGGER: ON_PLAY
CONDITION: AREA="CENTER", BATON_TOUCH {FILTER="GROUP_ID=3", COUNT_EQ_2}
EFFECT: DRAW(2); PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=3, COST_LE_4"}
```

---

## Ability: {{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態...
**Cards:** PL!SP-bp4-005-R＋, PL!SP-bp4-005-P, PL!SP-bp4-005-P＋, PL!SP-bp4-005-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH {FILTER="GROUP_ID=3", COUNT_EQ_1, SUM_ENERGY_GE=7}
EFFECT: PLACE_ENERGY_WAIT(2) -> PLAYER

TRIGGER: CONSTANT
CONDITION: ENERGY_COUNT {MIN=10}
EFFECT: ADD_BLADES(3) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に、名前が異なる『Liella!』のメンバーカードが3枚以上ある場合、エールにより公開された自分のカードの中...
**Cards:** PL!SP-bp4-006-R, PL!SP-bp4-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: YELL_CARDS {FILTER="GROUP_ID=3, UNIQUE_NAMES", MIN=3}
EFFECT: SELECT_YELL(1) {FILTER="GROUP_ID=3, TYPE_LIVE"} -> CARD_HAND
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分の控え室から、スコア3以下の『Liella!』のライブカードを1枚手札に加える。...
**Cards:** PL!SP-bp4-007-R, PL!SP-bp4-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_POSITION_CHANGE (Once per turn)
CONDITION: IS_SELF_MOVE
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=3, SCORE_LE_3", ZONE="DISCARD"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}【左サイド】カードを2枚引き、手札を1枚控え室に置く。
{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。
{{live_start...
**Cards:** PL!SP-bp4-008-R＋, PL!SP-bp4-008-P, PL!SP-bp4-008-P＋, PL!SP-bp4-008-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: AREA="LEFT_SIDE"
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(1) -> PLAYER

TRIGGER: ON_PLAY
CONDITION: AREA="RIGHT_SIDE"
EFFECT: ACTIVATE_ENERGY(2) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: POSITION_CHANGE (Optional) -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分のステージにいるメンバーのコストの合計が相手より低いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{ico...
**Cards:** PL!SP-bp4-009-R, PL!SP-bp4-009-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SUM_COST {TARGET="PLAYER", STAGE=TRUE, LESS_THAN="OPPONENT"}
EFFECT: ADD_BLADES(3) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}このメンバーをウェイトにする：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト...
**Cards:** PL!SP-bp4-010-R, PL!SP-bp4-010-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1); TAP_SELF
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
```

---

## Ability: {{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。...
**Cards:** PL!SP-bp4-011-R＋, PL!SP-bp4-011-P, PL!SP-bp4-011-P＋, PL!SP-bp4-011-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
TRIGGER: ON_POSITION_CHANGE
CONDITION: IS_SELF_MOVE_OR_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BASE_BLADES_LE_3"} -> TARGET; TAP_MEMBER(1) -> TARGET
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_02.png|heart02}}を得る。...
**Cards:** PL!SP-bp4-012-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: ADD_HEARTS(1) {HEART_TYPE=2} -> SELF
```

---

## Ability: {{toujyou.png|登場}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエ...
**Cards:** PL!SP-bp4-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: POSITION_CHANGE (Optional) -> SELF
```

---

## Ability: {{jidou.png|自動}}カードの効果によって自分のエネルギー置き場にエネルギーカードが置かれるたび、ライブ終了時まで、{{heart_06.png|heart06}}を得る。(相手のカードの効...
**Cards:** PL!SP-bp4-016-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLACE_ENERGY_BY_EFFECT
EFFECT: ADD_HEARTS(1) {HEART_TYPE=6, DURATION="UNTIL_LIVE_END"} -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}【左サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blad...
**Cards:** PL!SP-bp4-017-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: AREA="LEFT_SIDE", HAS_MOVED_THIS_TURN
EFFECT: ADD_BLADES(2) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室から『Liella!』のカードを1枚手札に加える。...
**Cards:** PL!SP-bp4-018-N

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) {FILTER="Liella!", FROM="DISCARD"} -> CARD_HAND
```

---

## Ability: {{live_start.png|ライブ開始時}}【右サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blad...
**Cards:** PL!SP-bp4-020-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: AREA="RIGHT_SIDE", HAS_MOVED_THIS_TURN
EFFECT: ADD_BLADES(2) -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}自分のエネルギーが相手より多いかぎり、{{heart_06.png|heart06}}を得る。...
**Cards:** PL!SP-bp4-021-N

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: ENERGY_LEAD {TARGET="PLAYER"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=6} -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を2つまで支払ってもよい：ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{i...
**Cards:** PL!SP-bp4-022-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY {MAX=2} (Optional)
EFFECT: ADD_BLADES(1) -> PLAYER {PER_ENERGY_PAID=1}
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「澁谷かのん」「ウィーン・マルガレーテ」「鬼塚冬毬」のうちのメンバー1人と、これにより選んだメンバー以外の『L...
**Cards:** PL!SP-bp4-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="NAME_IN=['澁谷かのん', 'ウィーン・マルガレーテ', '鬼塚冬毬']"} -> TARGET_1; SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_TARGET=TARGET_1"} -> TARGET_2; ADD_BLADES(1) -> TARGET_1; ADD_BLADES(1) -> TARGET_2

TRIGGER: ON_LIVE_START
EFFECT: TRANSFORM_YELL_BLADES(ALL) -> 6 {FILTER="NOT_BLADE_TYPE_6", DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のセンターエリアにいる『Liella!』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを＋１する。
{{...
**Cards:** PL!SP-bp4-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: PLAYER_CENTER_COST_GT_OPPONENT_CENTER_COST {PLAYER_CENTER_FILTER="GROUP_ID=3"}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ON_LIVE_START
CONDITION: SELECT_MEMBER(1) {AREA="LEFT_SIDE", FILTER="GROUP_ID=3, HAS_HEART_02_X3"}
EFFECT: SELECT_MEMBER(1) {AREA="LEFT_SIDE", FILTER="GROUP_ID=3, HAS_HEART_02_X3"} -> TARGET; ADD_BLADES(2) -> TARGET
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ{{icon_blade.png|ブレード}}の数は3つに...
**Cards:** PL!SP-bp4-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {AREA="CENTER", FILTER="GROUP_ID=3"} -> TARGET; TRANSFORM_BLADES(ALL) -> 3 {TARGET=TARGET}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: SELECT_MEMBER(1) {AREA="CENTER", FILTER="GROUP_ID=3, MOVED_THIS_TURN"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に名前が異なる『Liella!』のメンバーカードが5枚以上ある場合、このカードのスコアを＋１する。
{{li...
**Cards:** PL!SP-bp4-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: YELL_CARDS {FILTER="GROUP_ID=3, UNIQUE_NAMES", MIN=5}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ON_LIVE_SUCCESS
CONDITION: ENERGY_COUNT {MIN=11}
EFFECT: DRAW(2); DISCARD_HAND(1)
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。(メンバーをそれぞれ...
**Cards:** PL!SP-bp4-027-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: ALL_MEMBERS {FILTER="GROUP_ID=3"}
EFFECT: FORMATION_CHANGE (Optional) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}アクティブ状態の自分のエネルギーがある場合、このカードのスコアを＋１する。...
**Cards:** PL!SP-bp4-028-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_ACTIVE_ENERGY
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}自分のデッキの上からカードを5枚見る。その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開...
**Cards:** LL-bp4-001-R＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="Eri/Karin/Ren"} -> CARD_HAND, DISCARD_REMAINDER
EFFECT: TAP_OPPONENT(99) -> OPPONENT {FILTER="COST_LE_REVEALED, BLADE_LE_3"}

TRIGGER: ON_LIVE_START
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="Eri/Karin/Ren"} -> CARD_HAND, DISCARD_REMAINDER
EFFECT: TAP_OPPONENT(99) -> OPPONENT {FILTER="COST_LE_REVEALED, BLADE_LE_3"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにこのメンバー以外のコスト11のメンバーがいる場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{...
**Cards:** PL!N-pb1-001-R, PL!N-pb1-001-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
CONDITION: HAS_MEMBER {FILTER="NOT_SELF, COST_EQ_11"}
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND

TRIGGER: CONSTANT
CONDITION: COUNT_LIVE_PLAY AREA {MIN=2}
EFFECT: ADD_BLADES(2) -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー2枚をこのメンバーの下に置いてもよい。
{{jyouji.png|常時}}このメンバーの下にエネルギーカードが2枚以上置かれて...
**Cards:** PL!N-pb1-002-R, PL!N-pb1-002-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: ENERGY_CHARGE(2) -> SELF (Optional)

TRIGGER: CONSTANT
CONDITION: COUNT_CHARGED_ENERGY {MIN=2}
EFFECT: BOOST_SCORE(1) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージ...
**Cards:** PL!N-pb1-003-R, PL!N-pb1-003-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (From Hand)
COST: PAY_ENERGY(2); DISCARD_SELF
EFFECT: DRAW(1); SELECT_MEMBER(1) {TARGET="PLAYER", FILTER="GROUP_ID=2"} -> TARGET; ADD_BLADES(1) -> TARGET
```

---

## Ability: {{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{live_s...
**Cards:** PL!N-pb1-004-R, PL!N-pb1-004-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: NO_SELF_POSITION_CHANGE_THIS_TURN
EFFECT: ADD_BLADES(2) -> SELF

TRIGGER: ON_LIVE_START
EFFECT: LOOK_DECK(1) -> REVEALED
CONDITION: REVEALED_CARD {TYPE_MEMBER, COST_LE_9}
EFFECT: MOVE_TO_HAND {FROM="REVEALED"}; POSITION_CHANGE(SELF)
CONDITION: NOT_MATCH_PREVIOUS
EFFECT: MOVE_TO_DISCARD {FROM="REVEALED"}
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。...
**Cards:** PL!N-pb1-005-R, PL!N-pb1-005-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_STAGE_ENTRY (Once per turn)
CONDITION: FILTER="COST=10"
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。...
**Cards:** PL!N-pb1-006-R, PL!N-pb1-006-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: TAP_MEMBER(1) -> SELF
EFFECT: ACTIVATE_ENERGY(1)
```

---

## Ability: {{jyouji.png|常時}}自分のライブ中のライブカードの必要ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03...
**Cards:** PL!N-pb1-007-R, PL!N-pb1-007-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: LIVE_HEART_REQUIRED_COLORS {COLORS=[1, 2, 3, 4, 5, 6]}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=0} -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。
{{toujyou.png|登場}}自分のステージにい...
**Cards:** PL!N-pb1-008-R, PL!N-pb1-008-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=2, TAPPED"}
EFFECT: REDUCE_COST(2) -> SELF

TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: MEMBER | EFFECT: ACTIVATE_MEMBER(1) -> PLAYER
  OPTION: ENERGY | EFFECT: ACTIVATE_ENERGY(2) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}このターン、ブレードハートを持たないメンバーカードが自分のライブカード置き場から控え室に置かれている場合、カードを1枚引き、ライブ終了時まで、{{he...
**Cards:** PL!N-pb1-009-R, PL!N-pb1-009-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_DISCARDED_THIS_TURN {MIN=1, FILTER="TYPE_MEMBER, NOT_HAS_BLADE_HEART", FROM="LIVE_AREA"}
EFFECT: DRAW(1) -> PLAYER; ADD_HEARTS(3) {HEART_COLORS="3,5,6"}
```

---

## Ability: {{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。...
**Cards:** PL!N-pb1-010-R, PL!N-pb1-010-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: エネルギー | EFFECT: ACTIVATE_ENERGY(1)
  OPTION: ライブカード | EFFECT: SELECT_RECOVER_LIVE(ANY, target_count=2) {FILTER="GROUP_ID=2"} -> DECK_TOP {ORDER="CHOICE"}
```

---

## Ability: {{jyouji.png|常時}}このメンバーの下にあるエネルギーカード1枚につき、{{icon_blade.png|ブレード}}を得る。
{{kidou.png|起動}}{{turn1.png|ター...
**Cards:** PL!N-pb1-011-R, PL!N-pb1-011-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: ADD_BLADES(1) -> SELF {PER_CARD="UNDER_MEMBER"}

TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_UNDER_SELF(1) {FROM="ENERGY"}
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにこのメンバー以外のコスト11のメンバーが登場したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状...
**Cards:** PL!N-pb1-012-R, PL!N-pb1-012-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_STAGE_ENTRY (Once per turn)
CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER", FILTER="COST=11"}
EFFECT: ACTIVATE_ENERGY(1, MODE="WAIT") -> PLAYER

TRIGGER: ON_LIVE_SUCCESS
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=2", ZONE="YELL_REVEALED"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「上原歩夢」のメンバーカードを1枚ステージ...
**Cards:** PL!N-pb1-013-R, PL!N-pb1-013-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='上原歩夢', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
```

---

## Ability: {{toujyou.png|登場}}「中須かすみ」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。...
**Cards:** PL!N-pb1-014-R, PL!N-pb1-014-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH {FILTER="NAME='中須かすみ'"}
EFFECT: DRAW(2); DISCARD_HAND(1)
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「桜坂しずく」のメンバーカードを1枚ステー...
**Cards:** PL!N-pb1-015-R, PL!N-pb1-015-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='桜坂しずく', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「朝香果林」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!N-pb1-016-R, PL!N-pb1-016-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_REVEAL(2) {FILTER="NAME=朝香果林"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「宮下愛」のメンバーカードを1枚ステージに...
**Cards:** PL!N-pb1-017-R, PL!N-pb1-017-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='宮下愛', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「近江彼方」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!N-pb1-018-R, PL!N-pb1-018-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_REVEAL(2) {FILTER="NAME=近江彼方"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}「優木せつ菜」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。...
**Cards:** PL!N-pb1-019-R, PL!N-pb1-019-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_FROM_NAME {NAME=优木雪菜}
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}「エマ・ヴェルデ」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。...
**Cards:** PL!N-pb1-020-R, PL!N-pb1-020-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH {FILTER="NAME='エマ・ヴェルデ'"}
EFFECT: DRAW(2); DISCARD_HAND(2)
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「天王寺璃奈」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!N-pb1-021-R, PL!N-pb1-021-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_REVEAL(2) {FILTER="NAME=天王寺璃奈"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}「三船栞子」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。...
**Cards:** PL!N-pb1-022-R, PL!N-pb1-022-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_FROM_NAME {NAME=三船栞子}
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「ミア・テイラー」のメンバーカードを1枚ス...
**Cards:** PL!N-pb1-023-R, PL!N-pb1-023-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='ミア・テイラー', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「鐘嵐珠」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!N-pb1-024-R, PL!N-pb1-024-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_REVEAL(2) {FILTER="NAME=鐘嵐珠"} -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを2枚見る。その中から1枚を手札に加え、残りを控え室に置く。...
**Cards:** PL!N-pb1-028-N, PL!N-pb1-035-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE_REVEAL(2) -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}{{heart_03.png|heart03}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}の...
**Cards:** PL!N-pb1-034-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: HEART_SELECT(1) {CHOICES=[3, 4, 5]} -> CHOICE
EFFECT: TRANSFORM_HEARTS(ALL) -> HEART_TYPE_CHOICE {TARGET=SELF, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_02.png|heart02}}か{{heart_06.png|heart06}}の...
**Cards:** PL!N-pb1-036-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: HEART_SELECT(1) {CHOICES=[1, 2, 6]} -> CHOICE
EFFECT: TRANSFORM_HEARTS(ALL) -> HEART_TYPE_CHOICE {TARGET=SELF, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを＋１する。さらに、自分...
**Cards:** PL!N-pb1-037-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT {FILTER="GROUP_ID=2"}
EFFECT: BOOST_SCORE(1) -> SELF
CONDITION: DID_ACTIVATE_MEMBER_BY_MEMBER_EFFECT {FILTER="GROUP_ID=2"}
EFFECT: BOOST_SCORE(2) -> SELF {REPLACE=TRUE}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が4の『虹ヶ咲』のライ...
**Cards:** PL!N-pb1-038-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUCCESS_LIVES_CONTAINS {FILTER="Nijigasaki, PINK=4"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が3の『虹ヶ咲』のライ...
**Cards:** PL!N-pb1-039-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUCCESS_LIVES_OR_CURRENT_LIVE {FILTER="GROUP_ID=2, HEARTS_PINK_EQ_3"}
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, HAS_HEART_PURPLE"} -> TARGET; ADD_HEARTS(5) {HEART_TYPE=6, DURATION="UNTIL_LIVE_END"} -> TARGET
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに同じ名前の『虹ヶ咲』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}...
**Cards:** PL!N-pb1-042-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=2, SAME_NAME=TRUE, FILTER="Nijigasaki"}
EFFECT: REDUCE_HEART_REQ(3) -> SELF
```

---

## Ability: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以...
**Cards:** PL!SP-bp5-001-SEC, PL!SP-bp5-001-R＋, PL!SP-bp5-001-P, PL!SP-bp5-001-AR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-bp5-001-SEC**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ウェイト | EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(1) -> TARGET
  OPTION: ドロー | EFFECT: DRAW(1)

TRIGGER: ACTIVATED (Once per turn)
COST: CHOICE_MODE(1) -> PLAYER
  OPTION: タップ | COST: TAP_SELF
  OPTION: ディスカード | COST: DISCARD_HAND(1)
EFFECT: ACTIVATE_ENERGY(1)`
- **PL!SP-bp5-001-R＋**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ウェイト | EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}
  OPTION: ドロー | EFFECT: DRAW(1)

TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_SELF_OR_DISCARD {CHOICE=["TAP_SELF", "DISCARD_HAND(1)"]}
EFFECT: ACTIVATE_ENERGY(1)`
- **PL!SP-bp5-001-P**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ウェイト | EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}
  OPTION: ドロー | EFFECT: DRAW(1)

TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_SELF_OR_DISCARD {CHOICE=["TAP_SELF", "DISCARD_HAND(1)"]}
EFFECT: ACTIVATE_ENERGY(1)`
- **PL!SP-bp5-001-AR**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ウェイト | EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}
  OPTION: ドロー | EFFECT: DRAW(1)

TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_SELF_OR_DISCARD {CHOICE=["TAP_SELF", "DISCARD_HAND(1)"]}
EFFECT: ACTIVATE_ENERGY(1)`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ウェイト | EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, COST_LE_4"} -> TARGET; TAP_MEMBER(1) -> TARGET
  OPTION: ドロー | EFFECT: DRAW(1)

TRIGGER: ACTIVATED (Once per turn)
COST: CHOICE_MODE(1) -> PLAYER
  OPTION: タップ | COST: TAP_SELF
  OPTION: ディスカード | COST: DISCARD_HAND(1)
EFFECT: ACTIVATE_ENERGY(1)
```

---

## Ability: {{toujyou.png|登場}}手札を2枚控え室に置いてもよい：自分の控え室から『EdelNote』のライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分のステージにこのメンバ...
**Cards:** PL!HS-bp5-007-AR, PL!HS-bp5-007-R, PL!HS-bp5-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(2) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="UNIT_EDELNOTE"} -> CARD_HAND

TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {FILTER="UNIT_EDELNOTE", NOT_SELF, MIN=1}
EFFECT: ADD_BLADES(2) -> SELF
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
{{live_succe...
**Cards:** PL!SP-bp5-020-N

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(1) (Optional)
EFFECT: DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『SaintSnow』のカードを1枚手札に加える。そうした場合、ライブ終了時まで、{{ic...
**Cards:** PL!S-bp5-009-P, PL!S-bp5-009-AR, PL!S-bp5-009-R

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="Unit='Saint Snow'"} -> CARD_HAND
CONDITION: RECOVERED_CARDS {MIN=1}
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{jyouji.png|常時}}自分と相手のステージの中で、このメンバーがほかのすべてのメンバーより多くのハートを持つかぎり、ライブの合計スコアを＋１する。...
**Cards:** PL!N-bp5-002-R, PL!N-bp5-002-P, PL!N-bp5-002-AR

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: MOST_HEARTS {AREA="BOTH_STAGE"}
EFFECT: BOOST_SCORE(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得...
**Cards:** PL!S-bp5-004-P, PL!S-bp5-004-R, PL!S-bp5-004-AR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!S-bp5-004-P**: `TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ブレード追加 | EFFECT: ADD_BLADES(1) -> OTHER_MEMBER {FILTER="GROUP_ID=1"}
  OPTION: ポジションチェンジ | EFFECT: MOVE_MEMBER(1) {FILTER="Unit='Saint Snow'"} -> AREA_CHOICE`
- **PL!S-bp5-004-R**: `TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ブレード追加 | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=1, NOT_SELF"} -> TARGET; ADD_BLADES(1) -> TARGET
  OPTION: ポジションチェンジ | EFFECT: SELECT_MEMBER(1) {FILTER="Unit='Saint Snow'"} -> TARGET; POSITION_CHANGE(1) -> TARGET`
- **PL!S-bp5-004-AR**: `TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ブレード追加 | EFFECT: ADD_BLADES(1) -> OTHER_MEMBER {FILTER="GROUP_ID=1"}
  OPTION: ポジションチェンジ | EFFECT: MOVE_MEMBER(1) {FILTER="Unit='Saint Snow'"} -> AREA_CHOICE`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ブレード追加 | EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=1, NOT_SELF"} -> TARGET; ADD_BLADES(1) -> TARGET
  OPTION: ポジションチェンジ | EFFECT: SELECT_MEMBER(1) {FILTER="Unit='Saint Snow'"} -> TARGET; POSITION_CHANGE(1) -> TARGET
```

---

## Ability: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}...
**Cards:** PL!-bp5-004-R＋, PL!-bp5-004-P, PL!-bp5-004-SEC, PL!-bp5-004-AR

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(4); REDUCE_COST_PER_GROUP(1)
EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_10"} -> OPPONENT

TRIGGER: ON_REVEAL (Once per turn)
CONDITION: YELL_REVEALED {FILTER="NOT_BLADE_HEART", MIN=3}
EFFECT: ADD_HEARTS(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}このメンバーよりコストが低いメンバーからバトンタッチして登場した場合、自分と相手はそれぞれ自身の手札の枚数が3枚になるまで手札を控え室に置き、その後、自分と相手はそ...
**Cards:** PL!-bp5-007-AR, PL!-bp5-007-R, PL!-bp5-007-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH {FILTER="COST_LT_SELF"}
EFFECT: DISCARD_UNTIL(3) -> PLAYER_AND_OPPONENT; DRAW_UNTIL(3) -> PLAYER_AND_OPPONENT
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを控え室に置いてもよい。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これにより控...
**Cards:** PL!SP-bp5-009-R, PL!SP-bp5-009-P, PL!SP-bp5-009-AR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: LOOP(5)
  COST: MOVE_TO_DISCARD(1) {FROM="DECK_TOP"} (Optional)
  EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
  CONDITION: DISCARDED_CARDS {FILTER="TYPE_LIVE"}
  EFFECT: TAP_SELF; BREAK_LOOP
```

---

## Ability: {{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_02.png|heart02}}か{{heart_06.png|heart06}}の...
**Cards:** PL!SP-bp5-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: HEART_SELECT(1) {CHOICES=[1, 2, 6]} -> CHOICE
EFFECT: ADD_HEARTS(1) {HEART_TYPE=CHOICE, DURATION="UNTIL_LIVE_END" } -> MEMBER {FILTER="MOVED_THIS_TURN"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札の『DOLLCHESTRA』のカードを1枚控え室に置いてもよい：自分のステージにいる『DOLLCHESTRA』のメンバー1人を選ぶ。ライブ終了時ま...
**Cards:** PL!HS-bp5-005-P, PL!HS-bp5-005-R, PL!HS-bp5-005-AR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!HS-bp5-005-P**: `TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {FILTER="UNIT_DOLLCHESTRA"} (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="UNIT_DOLLCHESTRA"} -> TARGET
EFFECT: SET_COST(SELF, TARGET_BASE_COST_MINUS_1) {DURATION="UNTIL_LIVE_END"}
CONDITION: SELF_COST {GE=10}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"} -> SELF`
- **PL!HS-bp5-005-R**: `TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {FILTER="UNIT_DOLLCHESTRA"} (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="UNIT_DOLLCHESTRA"} -> TARGET
EFFECT: SET_COST(SELF, TARGET_BASE_COST_MINUS_1) {DURATION="UNTIL_LIVE_END"}
CONDITION: COST_GE {VALUE=10}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}`
- **PL!HS-bp5-005-AR**: `TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {FILTER="UNIT_DOLLCHESTRA"} (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="UNIT_DOLLCHESTRA"} -> TARGET
EFFECT: SET_COST(SELF, TARGET_BASE_COST_MINUS_1) {DURATION="UNTIL_LIVE_END"}
CONDITION: COST_GE {VALUE=10}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {FILTER="UNIT_DOLLCHESTRA"} (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="UNIT_DOLLCHESTRA"} -> TARGET
EFFECT: SET_COST(SELF, TARGET_BASE_COST_MINUS_1) {DURATION="UNTIL_LIVE_END"}
CONDITION: SELF_COST {GE=10}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"} -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、{{heart_03.png|heart03}}{{heart_03.png|heart0...
**Cards:** PL!-bp5-008-AR, PL!-bp5-008-R, PL!-bp5-008-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: SCORE_TOTAL {MIN=6}
EFFECT: ADD_HEARTS(2) {HEART_TYPE=3} -> SELF
```

---

## Ability: {{toujyou.png|登場}}カードを1枚引き、手札を1枚デッキの一番下に置く。...
**Cards:** PL!S-sd1-018-SD, PL!S-bp5-014-N, PL!S-sd1-017-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1); MOVE_TO_DECK_BOTTOM(1)
```

---

## Ability: {{live_success.png|ライブ成功時}}カードを1枚引き、手札を1枚控え室に置く。...
**Cards:** PL!N-bp5-023-N, PL!S-sd1-014-SD, PL!N-bp5-016-N

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp5-023-N**: `TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!S-sd1-014-SD**: `TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(1); DISCARD_HAND(1)`
- **PL!N-bp5-016-N**: `TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(1); DISCARD_HAND(1) (Optional)`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(1); DISCARD_HAND(1) (Optional)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：ライブ終了時まで、これにより控え室に置いた『Liella!』のメンバーカード1枚につき、{...
**Cards:** PL!SP-bp5-005-SEC, PL!SP-bp5-005-R＋, PL!SP-bp5-005-P, PL!SP-bp5-005-AR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-bp5-005-SEC**: `TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
EFFECT: ADD_BLADES(1) -> SELF {PER_CARD="GROUP_ID=3, TYPE_MEMBER", ZONE="DISCARDED_THIS"}

TRIGGER: ON_MOVE_TO_DISCARD (Once per turn)
CONDITION: MAIN_PHASE
COST: PAY_ENERGY(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND`
- **PL!SP-bp5-005-R＋**: `TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
EFFECT: ADD_BLADES(1) -> SELF {PER_CARD="GROUP_ID=3, TYPE_MEMBER", ZONE="DISCARDED_THIS"}

TRIGGER: ON_MOVE_TO_DISCARD (Once per turn)
CONDITION: MAIN_PHASE
COST: PAY_ENERGY(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND`
- **PL!SP-bp5-005-P**: `TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
EFFECT: ADD_BLADES(1) -> SELF {PER_CARD="GROUP_ID=3, TYPE_MEMBER", ZONE="DISCARDED_THIS"}

TRIGGER: ON_MOVE_TO_DISCARD (Once per turn)
CONDITION: MAIN_PHASE
COST: PAY_ENERGY(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND`
- **PL!SP-bp5-005-AR**: `TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
EFFECT: ADD_BLADES(COUNT_MEMBER_LIELLA_DISCARDED) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_MOVE_TO_DISCARD
CONDITION: MAIN_PHASE
COST: PAY_ENERGY(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
EFFECT: ADD_BLADES(1) -> SELF {PER_CARD="GROUP_ID=3, TYPE_MEMBER", ZONE="DISCARDED_THIS"}

TRIGGER: ON_MOVE_TO_DISCARD (Once per turn)
CONDITION: MAIN_PHASE
COST: PAY_ENERGY(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND
```

---

## Ability: {{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：自分のデッキの上から、自分のライブの合計スコアに2を足した数に等しい枚数見る。その中からカードを1枚手札に加える。...
**Cards:** PL!-bp5-001-P, PL!-bp5-001-AR, PL!-bp5-001-SEC, PL!-bp5-001-R＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK_DYNAMIC_SCORE(2) -> CARD_HAND, DISCARD_REMAINDER
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーを『Aqours』か『SaintSnow』のメンバーがいるエリアにポジショ...
**Cards:** PL!S-bp5-111-R, PL!S-bp5-111-P＋

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!S-bp5-111-R**: `TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: POSITION_CHANGE(TARGET_SLOT) {FILTER="HAS_GROUP_AQOURS_OR_SAINT_SNOW"}

TRIGGER: ON_POSITION_CHANGE (Once per turn)
CONDITION: IS_SELF_MOVE
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BLADE_LE_2"} -> TARGET; TAP_MEMBER(1) -> TARGET`
- **PL!S-bp5-111-P＋**: `TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: POSITION_CHANGE(TARGET_SLOT) {FILTER="HAS_GROUP_AQOURS_OR_SAINT_SNOW"}

TRIGGER: ON_POSITION_CHANGE
CONDITION: IS_SELF_MOVE
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BLADE_LE_2"} -> TARGET; TAP_MEMBER(1) -> TARGET`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: POSITION_CHANGE(TARGET_SLOT) {FILTER="HAS_GROUP_AQOURS_OR_SAINT_SNOW"}

TRIGGER: ON_POSITION_CHANGE (Once per turn)
CONDITION: IS_SELF_MOVE
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BLADE_LE_2"} -> TARGET; TAP_MEMBER(1) -> TARGET
```

---

## Ability: {{toujyou.png|登場}}能力を持たないメンバーからバトンタッチして登場した場合、カードを1枚引く。
{{jyouji.png|常時}}能力を持たないメンバーカードを自分の手札から登場させる...
**Cards:** PL!S-bp5-001-SEC, PL!S-bp5-001-R＋, PL!S-bp5-001-P, PL!S-bp5-001-AR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH {FILTER="NOT_ABILITY"}
EFFECT: DRAW(1)

TRIGGER: CONSTANT
EFFECT: REDUCE_COST(1) {FILTER="NOT_ABILITY"} -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『Aqours』のメンバーカードを1枚公開...
**Cards:** PL!S-bp5-006-R, PL!S-bp5-006-P, PL!S-bp5-006-AR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=1, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブカード置き場にカードが2枚以上ある場合、カードを1枚引く。...
**Cards:** PL!-bp5-006-AR, PL!-bp5-006-P, PL!-bp5-006-R

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUCCESS_LIVE_COUNT {MIN=2}
EFFECT: DRAW(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『Aq...
**Cards:** PL!S-sd1-005-SD

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2); DISCARD_HAND(1)
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=1"} -> CARD_HAND
```

---

## Ability: {{jyouji.png|常時}}自分のステージにいるメンバーがちょうど2人であるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!N-PR-020-PR, PL!S-PR-037-PR

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {EQUAL=2}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5} -> SELF; ADD_BLADES(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『虹ヶ咲』のメンバーカードを1枚公開して手...
**Cards:** PL!N-bp5-009-R, PL!N-bp5-009-P, PL!N-bp5-009-AR

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=2, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER
```

---

## Ability: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、このメンバーがコスト10以上のブレードハートを持たない『虹ヶ咲』のメンバーとバトンタッチしていた場合、エネルギーを2枚ア...
**Cards:** PL!N-bp5-005-R＋, PL!N-bp5-005-SEC, PL!N-bp5-005-AR, PL!N-bp5-005-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES
CONDITION: BATON_TOUCH {FILTER="GROUP_ID=2, NOT_HAS_BLADE_HEART, COST_GE_10"}
EFFECT: ACTIVATE_ENERGY(2)
CONDITION: BATON_TOUCH {FILTER="GROUP_ID=2, NOT_HAS_BLADE_HEART, COST_GE_15"}
EFFECT: DRAW(1)
```

---

## Ability: {{kidou.png|起動}}【左サイド】{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを3枚引き、手札を2枚控え室に置く。これにより控え室に置いたカードの中にブレードハ...
**Cards:** PL!SP-bp5-002-P, PL!SP-bp5-002-R＋, PL!SP-bp5-002-SEC, PL!SP-bp5-002-AR

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
CONDITION: AREA="LEFT_SIDE"
COST: TAP_SELF
EFFECT: DRAW(3); DISCARD_HAND(2)
CONDITION: DISCARDED_CARDS {FILTER="NOT_HAS_BLADE_HEART", MIN=1}
EFFECT: ACTIVATE_SELF
CONDITION: DISCARDED_CARDS {FILTER="NOT_HAS_BLADE_HEART", MIN=2}
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『Aqours』のカードを1枚手札に加える。...
**Cards:** PL!S-sd1-002-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=1"} -> CARD_HAND
```

---

## Ability: {{jyouji.png|常時}}このメンバーは自分のアクティブフェイズにアクティブにしない。
{{live_success.png|ライブ成功時}}自分のステージにこのメンバー以外のメンバーがいる場...
**Cards:** PL!N-bp5-006-P, PL!N-bp5-006-AR, PL!N-bp5-006-R

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: NOT_ACTIVATE_DURING_PHASE

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_STAGE {MIN=2}
EFFECT: TAP_SELF
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：カードを1枚引き、ライブ終了時まで、{{heart_01.png|h...
**Cards:** PL!N-bp5-012-P, PL!N-bp5-012-R＋, PL!N-bp5-012-SEC, PL!N-bp5-012-AR

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_UNDER_SELF(1) {FROM="ENERGY"}
EFFECT: DRAW(1); ADD_HEARTS(1) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_TOTAL_GE_OPPONENT
EFFECT: PLACE_ENERGY_WAIT(COUNT_UNDER_SELF + 1) -> PLAYER
```

---

## Ability: {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このメンバーをステージから控え室に置く：自分の控え室からコスト15以下の『蓮ノ空』の...
**Cards:** PL!HS-bp1-002-RM

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); MOVE_TO_DISCARD(SELF)
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=4, COST_LE_15"} -> TARGET_SLOT
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：エネルギーを2枚アクティブにする。...
**Cards:** PL!N-bp5-008-AR, PL!N-bp5-008-P, PL!N-bp5-008-R

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PLACE_UNDER(1) {FROM="ENERGY"}
EFFECT: ACTIVATE_ENERGY(2)
```

---

## Ability: {{jyouji.png|常時}}自分のエネルギーがちょうど8枚あるかぎり、ライブの合計スコアを＋１する。
{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー2枚をエネル...
**Cards:** PL!SP-bp5-111-R, PL!SP-bp5-111-P＋

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-bp5-111-R**: `TRIGGER: CONSTANT
CONDITION: ENERGY_COUNT {EQUAL=8}
EFFECT: BOOST_SCORE(1) -> PLAYER

TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_ENERGY_TO_DECK(2)
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`
- **PL!SP-bp5-111-P＋**: `TRIGGER: CONSTANT
CONDITION: ENERGY_COUNT {EQUAL=8}
EFFECT: BOOST_SCORE(1) -> PLAYER

TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_ENERGY_DECK(2) {FROM="ENERGY"}
EFFECT: RECOVER_LIVE(1) -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: CONSTANT
CONDITION: ENERGY_COUNT {EQUAL=8}
EFFECT: BOOST_SCORE(1) -> PLAYER

TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_ENERGY_DECK(2) {FROM="ENERGY"}
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}以下から1つを選ぶ。
・自分の控え室にカード名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
・自分の控え室にグループ名が...
**Cards:** PL!N-bp5-011-AR, PL!N-bp5-011-P, PL!N-bp5-011-R

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp5-011-AR**: `TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ユニーク名 | CONDITION: UNIQUE_NAMES_LIVE_DISCARD {MIN=3}; EFFECT: RECOVER_LIVE(1) -> CARD_HAND
  OPTION: ユニークグループ | CONDITION: UNIQUE_GROUPS_LIVE_DISCARD {MIN=3}; EFFECT: RECOVER_LIVE(2) -> CARD_HAND`
- **PL!N-bp5-011-P**: `TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ユニーク名 | CONDITION: UNIQUE_NAMES_COUNT {MIN=3, ZONE="DISCARD", TYPE="LIVE"}; EFFECT: RECOVER_LIVE(1) -> CARD_HAND
  OPTION: ユニークグループ | CONDITION: UNIQUE_GROUPS_COUNT {MIN=3, ZONE="DISCARD", TYPE="LIVE"}; EFFECT: RECOVER_LIVE(2) -> CARD_HAND`
- **PL!N-bp5-011-R**: `TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ユニーク名 | CONDITION: UNIQUE_NAMES_LIVE_DISCARD {MIN=3}; EFFECT: RECOVER_LIVE(1) -> CARD_HAND
  OPTION: ユニークグループ | CONDITION: UNIQUE_GROUPS_LIVE_DISCARD {MIN=3}; EFFECT: RECOVER_LIVE(2) -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: ユニーク名 | CONDITION: UNIQUE_NAMES_COUNT {MIN=3, ZONE="DISCARD", TYPE="LIVE"}; EFFECT: RECOVER_LIVE(1) -> CARD_HAND
  OPTION: ユニークグループ | CONDITION: UNIQUE_GROUPS_COUNT {MIN=3, ZONE="DISCARD", TYPE="LIVE"}; EFFECT: RECOVER_LIVE(2) -> CARD_HAND
```

---

## Ability: {{jyouji.png|常時}}自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得...
**Cards:** PL!HS-bp5-002-SEC, PL!HS-bp5-002-AR, PL!HS-bp5-002-P, PL!HS-bp5-002-R＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: UNIQUE_COST_COUNT {MIN=3}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5}; ADD_BLADES(1) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2"} -> EMPTY_SLOT
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『μ's』のメンバーカードを1枚公開して手...
**Cards:** PL!-bp5-002-AR, PL!-bp5-002-P, PL!-bp5-002-R

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-bp5-002-AR**: `TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=0, COST_GE_9"}; MOVE_TO_HAND(1); DISCARD_REMAINDER`
- **PL!-bp5-002-P**: `TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=0, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER`
- **PL!-bp5-002-R**: `TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=0, COST_GE_9"}; MOVE_TO_HAND(1); DISCARD_REMAINDER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=0, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER
```

---

## Ability: {{jyouji.png|常時}}コスト10の『Liella!』のメンバーカードを自分の手札から登場させるためのコストは2減る。
{{live_start.png|ライブ開始時}}{{center.p...
**Cards:** PL!SP-bp5-003-R＋, PL!SP-bp5-003-P, PL!SP-bp5-003-SEC, PL!SP-bp5-003-AR

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: REDUCE_COST(2) {FILTER="GROUP_ID=3, COST_EQ_10"} -> PLAYER

TRIGGER: ON_LIVE_START (Center Only)
EFFECT: ACTIVATE_MEMBER(ALL) {FILTER="GROUP_ID=3"}; ACTIVATE_ENERGY(ALL)
```

---

## Ability: {{live_success.png|ライブ成功時}}自分が余剰ハートを持たない場合、ライブの合計スコアを＋１する。自分が余剰ハートを2つ以上持つ場合、ライブの合計スコアを－１する。この効果ではライブ...
**Cards:** PL!N-bp5-010-R, PL!N-bp5-010-AR, PL!N-bp5-010-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: EXTRA_HEARTS {EQUAL=0}
EFFECT: BOOST_SCORE(1) -> SELF
CONDITION: EXTRA_HEARTS {MIN=2}
EFFECT: BOOST_SCORE(-1) -> SELF {MIN_SCORE=0}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から各グループ名につき1枚ずつ公開し、3枚まで手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!SP-bp5-007-AR, PL!SP-bp5-007-P, PL!SP-bp5-007-R

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!SP-bp5-007-AR**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5); REVEAL_PER_GROUP(1)
EFFECT: MOVE_TO_HAND(3) (Optional); DISCARD_REMAINDER`
- **PL!SP-bp5-007-P**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5); SELECT_FROM_LOOKED(ANY, target_count=3) {FILTER="UNIQUE_GROUPS"} -> CARD_HAND`
- **PL!SP-bp5-007-R**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5); SELECT_FROM_LOOKED(ANY, target_count=3) {FILTER="UNIQUE_GROUPS"} -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5); SELECT_FROM_LOOKED(ANY, target_count=3) {FILTER="UNIQUE_GROUPS"} -> CARD_HAND
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、ライブ終了時まで、エールにより公開された自分のカードの中のライブカード1枚につき、{{heart_02.pn...
**Cards:** PL!S-sd1-001-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_REVEAL (Once per turn)
EFFECT: ADD_HEARTS(1) {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"} -> SELF {PER_CARD="TYPE_LIVE", ZONE="REVEALED", MAX=3}
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『蓮ノ空』のメンバー1人が元々持つハートをすべて{{heart_01.png|heart01}}にする。
{{l...
**Cards:** PL!HS-bp5-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=4"} -> TARGET; TRANSFORM_HEARTS(ALL) -> HEART_TYPE_1 {TARGET=TARGET}

TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=3, FILTER="Unit='みらくらぱーく！'"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_bl...
**Cards:** PL!HS-bp5-001-P, PL!HS-bp5-001-R＋, PL!HS-bp5-001-AR, PL!HS-bp5-001-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(4) {FROM="DECK_TOP"}
CONDITION: DISCARDED_CARDS {FILTER="TYPE_LIVE", MIN=1}
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2); REVEAL_HAND_LIVE(1) -> OPPONENT
EFFECT: RECOVER_LIVE(1) {FILTER="SAME_NAME_AS_REVEALED"} -> CARD_HAND
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、このメンバーがエリアを移動するか自分のエネルギー置き場にエネルギーが置かれたとき、カードを1枚引き、ラ...
**Cards:** PL!SP-bp5-004-SEC, PL!SP-bp5-004-R＋, PL!SP-bp5-004-P, PL!SP-bp5-004-AR

**Consolidated Pseudocode:**
```
TRIGGER: ON_POSITION_CHANGE (Once per turn)
CONDITION: IS_SELF_MOVE_OR_ENERGY_PLACED
EFFECT: DRAW(1); ADD_HEARTS(1) {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_06.png|heart06}}を3以上含むライブカードを1枚...
**Cards:** PL!-bp5-009-R, PL!-bp5-009-P, PL!-bp5-009-AR

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: RECOVER_LIVE(1) {FILTER="HEARTS_GE_3, HEART_TYPE=6"} -> CARD_HAND
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにエネルギーカードが下にあるメンバーがいる場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。...
**Cards:** PL!N-bp5-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="HAS_UNDER_ENERGY"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"} -> SELF
```

---

## Ability: {{toujyou.png|登場}}「徒町小鈴」以外の『蓮ノ空』のメンバーからバトンタッチして登場した場合、自分の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分のス...
**Cards:** PL!HS-sd1-005-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH {FILTER="GROUP_ID=4, NOT_NAME='徒町小鈴'"}
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

TRIGGER: CONSTANT
CONDITION: HAS_MEMBER {FILTER="NAME_IN=['村野さやか', '百生吟子', '安養寺姫芽']"}
EFFECT: ADD_BLADES(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。...
**Cards:** PL!S-sd1-013-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(5) {FROM="DECK_TOP"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分と相手の成功ライブカード置き場にあるカードの枚数が同じ場合、ライブ終了時まで、{{heart_02.png|heart02}}{{heart_02...
**Cards:** PL!N-bp5-007-AR, PL!N-bp5-007-P, PL!N-bp5-007-SEC, PL!N-bp5-007-R＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUCCESS_LIVE_COUNT_EQUAL_OPPONENT
EFFECT: ADD_HEARTS(2) {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: EXTRA_HEARTS {MIN=1}
EFFECT: DRAW(2); DISCARD_HAND(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：このメンバーはポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる...
**Cards:** PL!SP-bp5-006-R, PL!SP-bp5-006-AR, PL!SP-bp5-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
EFFECT: POSITION_CHANGE(SELF)
```

---

## Ability: {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をポジションチェンジさせてもよい。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置い...
**Cards:** PL!HS-bp5-003-R＋, PL!HS-bp5-003-P, PL!HS-bp5-003-AR, PL!HS-bp5-003-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES
EFFECT: POSITION_CHANGE(1) (Optional) -> PLAYER

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: ADD_HEARTS(1) {HEART_TYPE=0} -> MEMBER {FILTER="SAME_GROUP_AS_DISCARDED"}
```

---

## Ability: {{jyouji.png|常時}}自分のステージにいる『Liella!』のメンバーがこのターンにエリアを移動しているかぎり、手札にあるこのメンバーカードのコストは2減る。...
**Cards:** PL!SP-bp5-017-N

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: ANY_MEMBER_MOVED_THIS_TURN {FILTER="GROUP_ID=3"}
EFFECT: REDUCE_COST(2) -> SELF
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードが持つブレードハートの中に[桃ブレード]、[赤ブレード]、[黄ブレード]、...
**Cards:** PL!N-bp5-001-P, PL!N-bp5-001-R＋, PL!N-bp5-001-AR, PL!N-bp5-001-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_REVEAL (Once per turn)
CONDITION: YELL_REVEALED_UNIQUE_COLORS {MIN=3}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_REVEAL (Once per turn)
CONDITION: YELL_REVEALED_UNIQUE_COLORS {MIN=6}
EFFECT: GRANT_ABILITY(SELF, "TRIGGER: CONSTANT\nEFFECT: BOOST_SCORE(1) -> PLAYER") {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーを『Aqours』か『SaintSnow』のメンバーがいるエリアにポジショ...
**Cards:** PL!S-bp5-222-R, PL!S-bp5-222-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: POSITION_CHANGE(TARGET_SLOT) {FILTER="HAS_GROUP_AQOURS_OR_SAINT_SNOW"}

TRIGGER: ON_POSITION_CHANGE (Once per turn)
CONDITION: IS_SELF_MOVE
EFFECT: ACTIVATE_ENERGY(2)
```

---

## Ability: {{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：エールにより公開された自分のカードの中から、コスト2以下のメンバーカードか、スコア２以下のライブカードを1枚手札に...
**Cards:** PL!N-PR-021-PR, PL!SP-PR-016-PR, PL!HS-PR-027-PR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-PR-021-PR**: `TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: SELECT_YELL(1) {FILTER="(TYPE_MEMBER, COST_LE_2) OR (TYPE_LIVE, SCORE_LE_2)"} -> CARD_HAND`
- **PL!SP-PR-016-PR**: `TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_FROM_REVEALED(1) {FILTER="COST_LE_2 OR SCORE_LE_2"} -> CARD_HAND`
- **PL!HS-PR-027-PR**: `TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_FROM_REVEALED(1) {FILTER="COST_LE_2 OR SCORE_LE_2"} -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: SELECT_YELL(1) {FILTER="(TYPE_MEMBER, COST_LE_2) OR (TYPE_LIVE, SCORE_LE_2)"} -> CARD_HAND
```

---

## Ability: {{jyouji.png|常時}}相手の余剰ハートが2つ以上あるかぎり、自分のライブの合計スコアを＋１する。...
**Cards:** PL!S-bp5-008-R, PL!S-bp5-008-P, PL!S-bp5-008-AR

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: OPP_EXTRA_HEARTS {MIN=2}
EFFECT: BOOST_SCORE(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}手札の同じグループ名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.p...
**Cards:** PL!HS-bp5-006-R, PL!HS-bp5-006-AR, PL!HS-bp5-006-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) {FILTER="SAME_GROUP"} (Optional)
EFFECT: ADD_HEARTS(2) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに『A-RISE』のメンバーがいる場合、以下から1つを選ぶ。
・ウェイト状態のメンバー1人をアクティブにし、ライブ終了時まで、そのメンバ...
**Cards:** PL!-bp5-024-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="GROUP_ARISE"}
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: アクティブ | EFFECT: SELECT_MEMBER(1) {FILTER="WAIT"} -> TARGET; ACTIVATE_MEMBER(1) -> TARGET; ADD_BLADES(1) -> TARGET
  OPTION: ウェイト | EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BLADE_LE_3"} -> TARGET; TAP_MEMBER(1) -> TARGET
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：{{heart_03.png|heart03}}か{{heart_04.png|heart04}}か{{heart_0...
**Cards:** PL!S-bp5-005-AR, PL!S-bp5-005-R＋, PL!S-bp5-005-P, PL!S-bp5-005-SEC

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: HEART_SELECT(1) {CHOICES=[3, 4, 5]} -> CHOICE
EFFECT: ADD_HEARTS(1) {HEART_TYPE=CHOICE} -> MEMBER {FILTER="NOT_GROUP_AQOURS, PLAYED_THIS_TURN"}
```

---

## Ability: {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。
{{live_start.png|ライブ開始時}}手札...
**Cards:** PL!HS-sd1-020-SD

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: TREAT_AS_UNIT("スリーズブーケ, DOLLCHESTRA, みらくらぱーく！") -> SELF

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(ANY, target_count=3) {FILTER="GROUP_ID=4, TYPE_MEMBER"} (Optional)
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(1) -> TARGET {PER_CARD="DISCARDED_THIS"}
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のデッキの上からカードを4枚見る。その中からハートに{{heart_04.png|heart04}}を2つ以上持つメンバーカードを1枚公開して...
**Cards:** PL!S-bp5-007-P, PL!S-bp5-007-AR, PL!S-bp5-007-R

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!S-bp5-007-P**: `TRIGGER: ON_LIVE_SUCCESS
EFFECT: LOOK_DECK(4)
EFFECT: MOVE_TO_HAND(1) {FILTER="HEARTS_GE_2, HEART_TYPE=4"}; DISCARD_REMAINDER`
- **PL!S-bp5-007-AR**: `TRIGGER: ON_LIVE_SUCCESS
EFFECT: LOOK_DECK(4) {FILTER="TYPE_MEMBER, HEARTS_BLUE_GE_2"}; MOVE_TO_HAND(1) (Optional); DISCARD_REMAINDER`
- **PL!S-bp5-007-R**: `TRIGGER: ON_LIVE_SUCCESS
EFFECT: LOOK_DECK(4) {FILTER="TYPE_MEMBER, HEARTS_BLUE_GE_2"}; MOVE_TO_HAND(1) (Optional); DISCARD_REMAINDER`

**Selected Best (Longest):**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: LOOK_DECK(4) {FILTER="TYPE_MEMBER, HEARTS_BLUE_GE_2"}; MOVE_TO_HAND(1) (Optional); DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト9以下のメンバー1人をウェイトにする。
{{jyouji.png|常時}}このメンバーがウェイト状態で...
**Cards:** PL!-bp5-333-R, PL!-bp5-333-P＋

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_SELF (Optional)
EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_9"}

TRIGGER: CONSTANT
CONDITION: IS_WAIT
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5} -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分のエネルギーがちょうど8枚あるかぎり、ライブの合計スコアを＋１する。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}...
**Cards:** PL!SP-bp5-222-R, PL!SP-bp5-222-P＋

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: ENERGY_COUNT {EQUAL=8}
EFFECT: BOOST_SCORE(1) -> PLAYER

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
```

---

## Ability: {{toujyou.png|登場}}手札のブレードハートを持たないメンバーカードを2枚まで控え室に置いてもよい：自分の控え室から、これにより控え室に置いたカードと同じ枚数の『Aqours』のライブカー...
**Cards:** PL!S-bp5-003-P, PL!S-bp5-003-R, PL!S-bp5-003-AR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!S-bp5-003-P**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(ANY, target_count=2) {FILTER="NOT_HAS_BLADE_HEART", TYPE_MEMBER} (Optional)
EFFECT: RECOVER_LIVE(COUNT_DISCARDED) {FILTER="GROUP_ID=1"} -> CARD_HAND`
- **PL!S-bp5-003-R**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(2) {FILTER="NOT_HAS_BLADE_HEART"} (Optional)
EFFECT: RECOVER_LIVE(COUNT_DISCARDED) {FILTER="GROUP_ID=1"} -> CARD_HAND`
- **PL!S-bp5-003-AR**: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(2) {FILTER="NOT_HAS_BLADE_HEART"} (Optional)
EFFECT: RECOVER_LIVE(COUNT_DISCARDED) {FILTER="GROUP_ID=1"} -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(ANY, target_count=2) {FILTER="NOT_HAS_BLADE_HEART", TYPE_MEMBER} (Optional)
EFFECT: RECOVER_LIVE(COUNT_DISCARDED) {FILTER="GROUP_ID=1"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加える。残りを控え室に置く。...
**Cards:** PL!-bp5-222-R, PL!-bp5-222-P＋

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-bp5-222-R**: `TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(3); MOVE_TO_HAND(1); DISCARD_REMAINDER`
- **PL!-bp5-222-P＋**: `TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(3) -> CARD_HAND, DISCARD_REMAINDER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(3); MOVE_TO_HAND(1); DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージにコスト9以上の『EdelNote』...
**Cards:** PL!HS-bp5-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional)
CONDITION: HAS_MEMBER {FILTER="GROUP_ID=4, COST_GE_9"}
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: 登場 | EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=4, COST_LE_4"} -> EMPTY_SLOT
  OPTION: 必要ハート減少 | EFFECT: REDUCE_HEART_REQ(1) {HEART_TYPE=5} -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}相手のステージにいるすべてのメンバーのそれぞれのコストよりコストが高いメンバーが自分のステージにいる場合、ライブ終了時まで、{{icon_blade....
**Cards:** PL!S-bp5-016-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="COST_GT_ALL_OPPONENT"}
EFFECT: ADD_BLADES(2) -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるメンバーが持つハートに{{heart_02.png|heart02}}が合計5つ以上ある場合、相手のライブ開始時、相手のライブカード置き場にある...
**Cards:** PL!S-bp5-010-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: TOTAL_HEARTS {MIN=5, FILTER="HEART_TYPE=2"}
EFFECT: NEXT_OPPONENT_LIVE_START_MOD {HEART_REQ_INC(ALL, 0)}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『SunnyPassion』のメンバーカードかブレードハートを持つ『Liella!』...
**Cards:** PL!SP-bp5-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="UNIT_SUNNY_PASSION OR (GROUP_ID=3, HAS_BLADE_HEART), TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER
```

---

## Ability: {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分のエネルギーが6枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...
**Cards:** PL!SP-bp5-021-N

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD(SELF)
CONDITION: ENERGY_COUNT {MIN=6}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚控え室に置く。その後、自分の控え室から『A-RISE』のメンバーカードを1枚手札に加え...
**Cards:** PL!-bp5-010-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}; RECOVER_MEMBER(1) {FILTER="GROUP_ARISE"} -> CARD_HAND
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動したメンバーは{{icon_blade.png|ブレード}}を得る。
{{live_...
**Cards:** PL!S-bp5-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: ADD_BLADES(1) -> MEMBER {FILTER="MOVED_THIS_TURN"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: SELF_YELL_LIVE_COUNT {GT="OPPONENT_YELL_LIVE_COUNT"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる『Liella!』のメンバーが持つハートの総数が11以上の場合、このカードのスコアを＋１する。...
**Cards:** PL!SP-bp5-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: TOTAL_HEARTS {MIN=11, FILTER="GROUP_ID=3"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにグループ名がそれぞれ異なるメンバーが3人以上いる場合、ライブ終了時まで、自分のセンターエリアにいるメンバーは{{icon_all.pn...
**Cards:** LL-bp5-002-L

*No manual pseudocode found for this ability.*

---

## Ability: {{jyouji.png|常時}}自分のステージにいるコスト4以上の『スリーズブーケ』以外のメンバー1人につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード...
**Cards:** PL!HS-bp5-004-AR, PL!HS-bp5-004-R, PL!HS-bp5-004-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {FILTER="COST_GE_4, NOT_UNIT_CERISE_BOUQUET", MULTIPLIER=2}
EFFECT: ADD_BLADES(SELF, MULTIPLIER)
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブカード置き場にあるカードの必要ハートに含まれる{{heart_04.png|heart04}}の合計が4以上の場合、ライブ終了時まで、{{...
**Cards:** PL!S-bp5-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)
```

---

## Ability: {{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上ある場合、エールにより公開された自分のカードの中から、メンバーカードを2枚まで手札に加える。...
**Cards:** PL!S-bp5-019-L

*No manual pseudocode found for this ability.*

---

## Ability: {{jyouji.png|常時}}自分のステージに名前が異なるメンバーが3人以上いるかぎり、{{heart_03.png|heart03}}を得る。
{{kidou.png|起動}}{{turn1.p...
**Cards:** PL!-bp5-003-SEC, PL!-bp5-003-R＋, PL!-bp5-003-P, PL!-bp5-003-AR

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: UNIQUE_NAMES_COUNT {MIN=3}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=3} -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2); DISCARD_HAND(1)
CONDITION: DISCARDED_CARDS {FILTER="GROUP_ID=0"}
EFFECT: DRAW_MEMBER_FROM_DECK(2) {FILTER="ANY", LOOK=4}
CONDITION: NOT_DISCARDED_CARDS {FILTER="GROUP_ID=0"}
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを10枚控え室に置く。...
**Cards:** PL!S-bp5-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}自分と相手は、自身のステージのセンターにいるメンバーをポジションチェンジする。(センターにいるメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーが...
**Cards:** PL!SP-bp5-010-AR, PL!SP-bp5-010-P, PL!SP-bp5-010-R

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: POSITION_CHANGE_ALL {FILTER="AREA=CENTER"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{...
**Cards:** PL!HS-bp5-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}自分のステージにいるメンバーが持つハートに{{heart_05.png|heart05}}が合計5つ以上ある場合、相手のライブ開始時、相手のライブカード置き場にある...
**Cards:** PL!S-bp5-011-N

*No manual pseudocode found for this ability.*

---

## Ability: {{jyouji.png|常時}}【左サイド】{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。
...
**Cards:** PL!SP-bp5-011-R, PL!SP-bp5-011-AR, PL!SP-bp5-011-P

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: AREA="LEFT_SIDE"
EFFECT: ADD_HEARTS(3) {HEART_TYPE=2}

TRIGGER: CONSTANT
CONDITION: AREA="CENTER"
EFFECT: ADD_HEARTS(3) {HEART_TYPE=3}

TRIGGER: CONSTANT
CONDITION: AREA="RIGHT_SIDE"
EFFECT: ADD_HEARTS(3) {HEART_TYPE=5}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーが3人以上いて、かつ自分の控え室にカード名に「DreamBelievers」を含むライブカードがある場合、このカー...
**Cards:** PL!HS-sd1-018-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=3, FILTER="GROUP_ID=4"}, HAS_CARD_IN_DISCARD {FILTER="TYPE_LIVE, NAME_CONTAINS='DreamBelievers'"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに{{heart_02.png|heart02}}を4つ以上持つメンバーがいる場合、このカードのスコアを＋２し、必要ハートは{{hear...
**Cards:** PL!N-bp5-028-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1, FILTER="HEARTS_YELLOW_GE_4"}
EFFECT: BOOST_SCORE(2) -> SELF; OVERRIDE_HEART_REQ {HEARTS=[2, 2, 2, 2, 2, 2]} -> SELF
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『Liella!』のメンバーカードを1枚公...
**Cards:** PL!SP-bp5-008-AR, PL!SP-bp5-008-P, PL!SP-bp5-008-R

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=3, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブカード置き場にあるカードの必要ハートに含まれる{{heart_05.png|heart05}}の合計が4以上の場合、ライブ終了時まで、{{...
**Cards:** PL!S-bp5-017-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUCCESS_LIVE_REQUIREMENT_SUM {HEART_TYPE=5, MIN=4}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5} -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、自分のエネルギーデッキから、エネルギーカードを1枚アクティブ状態で置く。...
**Cards:** PL!-bp5-005-P, PL!-bp5-005-AR, PL!-bp5-005-R

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-bp5-005-P**: `TRIGGER: ON_PLAY
CONDITION: SCORE_TOTAL {MIN=6}
EFFECT: PLACE_ENERGY_WAIT(1) {ACTIVE=TRUE} -> PLAYER`
- **PL!-bp5-005-AR**: `TRIGGER: ON_PLAY
CONDITION: SUCCESS_LIVE_SCORE_TOTAL {GE=6}
EFFECT: PLACE_ENERGY_WAIT(1) {ACTIVE=TRUE} -> PLAYER`
- **PL!-bp5-005-R**: `TRIGGER: ON_PLAY
CONDITION: SCORE_TOTAL {MIN=6}
EFFECT: PLACE_ENERGY_WAIT(1) {ACTIVE=TRUE} -> PLAYER`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
CONDITION: SUCCESS_LIVE_SCORE_TOTAL {GE=6}
EFFECT: PLACE_ENERGY_WAIT(1) {ACTIVE=TRUE} -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{...
**Cards:** PL!N-bp5-026-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_HEART_TYPES {ALL=[1,2,3,4,5,6]}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ON_LIVE_SUCCESS
CONDITION: SELF_SCORE {EQUAL=3}
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『Aqours』のライブカードを1枚手札に加える。...
**Cards:** PL!S-sd1-019-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_YELL(1) {FILTER="GROUP_ID=1, TYPE_LIVE"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『蓮ノ空』のメンバーカードを1枚公開して手...
**Cards:** PL!HS-bp5-008-P, PL!HS-bp5-008-AR, PL!HS-bp5-008-R

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: TAP_SELF; DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=4, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_05.png|heart05}}か{{heart_06.pn...
**Cards:** PL!-bp5-014-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_DECK(4); MOVE_TO_HAND(1) {FILTER="TYPE_MEMBER, HEART_TYPE_ANY=[5,6]"}; DISCARD_REMAINDER
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを2枚控え室に置く。その後、自分の控え室からライブカード1枚を自分のデッキの一番上から4枚目に置いてもよい。...
**Cards:** PL!N-bp5-021-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}
EFFECT: MOVE_TO_DECK_TOP(1) {FILTER="TYPE_LIVE, FROM='DISCARD'", POS=4} (Optional)
```

---

## Ability: {{toujyou.png|登場}}このターン、自分のステージにいるほかのメンバーがエリアを移動している場合、カードを1枚引く。...
**Cards:** PL!SP-bp5-014-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: OTHER_MEMBER_MOVED_THIS_TURN
EFFECT: DRAW(1)
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png...
**Cards:** PL!N-bp5-003-AR, PL!N-bp5-003-P, PL!N-bp5-003-R

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp5-003-AR**: `TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1)
EFFECT: PAY_ENERGY(TARGET_SCORE) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND`
- **PL!N-bp5-003-P**: `TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1)
EFFECT: PAY_ENERGY(TARGET_SCORE) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND`
- **PL!N-bp5-003-R**: `TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1)
EFFECT: RECOVER_LIVE(1) {COST_TYPE="SCORE", COST_OPTIONAL=TRUE} -> CARD_HAND`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1)
EFFECT: PAY_ENERGY(TARGET_SCORE) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室からコスト2以下の『Aqours』のメンバーカードを1枚、メンバーのいないエリアに登場させる。（この効果で登場したメンバ...
**Cards:** PL!S-sd1-006-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=1, COST_LE_2" -> EMPTY_SLOT; LOCK_SLOT -> TARGET_SLOT
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：カードを1枚引く。...
**Cards:** PL!-PR-012-PR, PL!S-PR-038-PR, PL!SP-PR-017-PR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!-PR-012-PR**: `TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: DRAW(1)`
- **PL!S-PR-038-PR**: `TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: DRAW(1)`
- **PL!SP-PR-017-PR**: `TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: DRAW(1) -> PLAYER`

**Selected Best (Longest):**
```
TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにコスト10以上の『蓮ノ空』のメンバーが2人以上いる場合、このカードのスコアを＋１する。...
**Cards:** PL!HS-bp5-020-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=2, FILTER="GROUP_ID=4, COST_GE_10"}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつエールにより公開された自分のカードの中に{{icon_score.png|スコア}}...
**Cards:** PL!SP-bp5-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SUCCESS_LIVE_COUNT {MIN=2, TARGET="ANY_PLAYER"}, YELL_REVEALED {FILTER="TYPE_LIVE, HAS_SCORE", MIN=1}
EFFECT: BOOST_SCORE(2) -> SELF
```

---

## Ability: {{toujyou.png|登場}}手札の『蓮ノ空』のカードを1枚控え室に置いてもよい：自分の控え室からメンバーカードを1枚手札に加える。
{{jyouji.png|常時}}自分のステージに「日野下花...
**Cards:** PL!HS-sd1-004-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {FILTER="GROUP_ID=4"} (Optional)
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND

TRIGGER: CONSTANT
CONDITION: HAS_MEMBER {FILTER="NAME=日野下花帆 OR NAME=徒町小鈴 OR NAME=安養寺姫芽"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『Liella!』のカードが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状...
**Cards:** PL!SP-PR-018-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: YELL_REVEALED_COUNT {FILTER="GROUP_ID=3", MIN=7}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}自分のステージにいるこのメンバー以外の『A-RISE』のメンバー1人につき、{{heart_05.png|heart05}}を得る。
{{kidou.png|起動}}...
**Cards:** PL!-bp5-111-P＋, PL!-bp5-111-R

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5, PER_CARD="STAGE", FILTER="GROUP_ARISE, NOT_SELF"}

TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1)
EFFECT: SELECT_MEMBER(1) {FILTER="WAIT"} -> TARGET; ACTIVATE_MEMBER(1) -> TARGET
CONDITION: TARGET_IS_OPPONENT
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のライブカード置き場にあるこのカード以外の『蓮ノ空』のカード1枚につき、このカードの必要ハートを{{heart_04.png|heart04}}{...
**Cards:** PL!HS-bp5-019-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: REDUCE_HEART_REQ(2) {HEART_TYPE=4, PER_CARD="SUCCESS_LIVE", FILTER="GROUP_ID=4, NOT_SELF"} -> SELF
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『蓮ノ空』のカードを1枚手札に加える。...
**Cards:** PL!HS-sd1-014-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=4"} -> CARD_HAND
```

---

## Ability: {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の...
**Cards:** PL!N-bp5-004-R, PL!N-bp5-004-P, PL!N-bp5-004-AR

> [!WARNING]
> **Conflict Detected!** Multiple different pseudocodes found in this group.

- **PL!N-bp5-004-R**: `TRIGGER: ON_PLAY; TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: TAP_OPPONENT(1) {FILTER="BLADE=4"}`
- **PL!N-bp5-004-P**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: TAP_OPPONENT(1) {FILTER="BLADE=4"} -> OPPONENT`
- **PL!N-bp5-004-AR**: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: TAP_OPPONENT(1) {FILTER="BLADE=4"} -> OPPONENT`

**Selected Best (Longest):**
```
TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: TAP_OPPONENT(1) {FILTER="BLADE=4"} -> OPPONENT
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『Aqours』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...
**Cards:** PL!S-sd1-003-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=1, TYPE_LIVE"}; MOVE_TO_HAND(1) (Optional); DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつ自分のステージに名前の異なるメンバーが3人以上いる場合、このカードのスコアを＋１する。...
**Cards:** PL!N-bp5-027-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: SUCCESS_LIVE_COUNT {MIN=2, TARGET="ANY_PLAYER"}, UNIQUE_NAMES_COUNT {MIN=3}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_05.png|heart05}}を持つメンバーカードの場合、ライブ終了時まで、{{hea...
**Cards:** PL!HS-sd1-013-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
CONDITION: ALL_MEMBERS {FILTER="HEART_05", ZONE="DISCARDED_THIS"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5} -> SELF
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...
**Cards:** PL!N-bp5-019-N, PL!N-bp5-022-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND
```

---

## Ability: {{jidou.png|自動}}自分のステージにいるメンバーの{{live_start.png|ライブ開始時}}能力が解決するたび、そのメンバーが{{icon_all.png|ハート}}を持たない場合...
**Cards:** PL!N-bp5-030-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_ABILITY_RESOLVE {TYPE="ON_LIVE_START"}
CONDITION: TARGET_MEMBER_HAS_NO_HEARTS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=6}

TRIGGER: ON_ABILITY_RESOLVE {TYPE="ON_LIVE_SUCCESS"}
EFFECT: DRAW(1)
```

---

## Ability: {{live_start.png|ライブ開始時}}{{center.png|センター}}自分のステージの右サイドエリアと左サイドエリアにいるメンバーのコストが同じ場合、相手のステージにいる元々持つ{{...
**Cards:** PL!S-bp5-002-SEC, PL!S-bp5-002-AR, PL!S-bp5-002-R＋, PL!S-bp5-002-P

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START (Center Only)
CONDITION: SYNC_COST {AREA="SIDE_AREAS"}
EFFECT: TAP_OPPONENT(ALL) {FILTER="BLADE_LE_3"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにメンバーが1人以上いる場合、自分と相手はカードを1枚引き、手札を1枚控え室に置く。2人以上いる場合、さらに自分のステージにいる『μ's...
**Cards:** PL!-bp5-021-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1}
EFFECT: DRAW(1) -> ALL_PLAYERS; DISCARD_HAND(1) -> ALL_PLAYERS
CONDITION: COUNT_STAGE {MIN=2}
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} -> TARGET; ADD_HEARTS(1) {HEART_TYPE=3}
CONDITION: COUNT_STAGE {MIN=3}, UNIQUE_NAMES_COUNT {MIN=3}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のステージに『蓮ノ空』のメンバーがいる場合、カードを1枚引き、手札を1枚控え室に置く。...
**Cards:** PL!HS-sd1-017-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAS_MEMBER {FILTER="GROUP_ID=4"}
EFFECT: DRAW(1); DISCARD_HAND(1) -> PLAYER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに「中須かすみ」がいる場合、自分のデッキの上からカードを4枚公開する。自分はそれらの中から「中須かすみ」のカードを1枚選ぶ。ライブ終了時...
**Cards:** PL!N-bp5-029-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="NAME=中須かすみ"}
EFFECT: LOOK_DECK(4) {REVEAL=TRUE}; SELECT_CARD(1) {FILTER="NAME=中須かすみ", FROM="REVEALED"}
EFFECT: SELECT_MEMBER(1) {FILTER="NAME=中須かすみ"} -> TARGET; ADD_HEARTS(ALL) {HEART_TYPE="SELECTED_COLORS"}
EFFECT: DISCARD_REMAINDER
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{...
**Cards:** PL!N-bp5-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_HEART_TYPES {ALL=[1,2,3,4,5,6]}
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}手札の『蓮ノ空』のカードを2枚控え室に置いてもよい：{{heart_0...
**Cards:** PL!HS-sd1-008-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(1) -> PLAYER

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) {FILTER="GROUP_ID=4"} (Optional)
EFFECT: HEART_SELECT(1) {CHOICES=[1, 4, 5, 6]} -> CHOICE; SELECT_MEMBER(1) {FILTER="GROUP_ID=4, NOT_SELF"} -> TARGET; EFFECT: ADD_HEARTS(2) {HEART_TYPE=CHOICE} -> TARGET
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置いてもよい。そうした場合、相手はカードを1枚引く。...
**Cards:** PL!SP-bp5-027-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
COST: PLACE_ENERGY_WAIT(1) (Optional)
EFFECT: DRAW(1) -> OPPONENT
```

---

## Ability: {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。
{{live_start.png|ライブ開始時}}自分...
**Cards:** PL!HS-bp5-018-L

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
EFFECT: TREAT_AS_UNIT("スリーズブーケ, DOLLCHESTRA, みらくらぱーく！") -> SELF

TRIGGER: ON_LIVE_START
CONDITION: UNIQUE_NAMES_COUNT {MIN=3}, UNIQUE_COST_COUNT {MIN=3}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}{{icon_energy.png|E}}を好きな数支払ってもよい：これにより支払った{{icon_energy.png|E}}4つにつき、このカ...
**Cards:** PL!SP-bp5-025-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(ANY) (Optional)
EFFECT: BOOST_SCORE(1) {PER_ENERGY=4} -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが2枚以上あるか、自分のステージにいるメンバーが持つハートの中に{{heart_01.png|...
**Cards:** LL-bp5-001-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: YELL_REVEALED {FILTER="TYPE_LIVE", MIN=2} OR UNIQUE_HEART_TYPES {MIN=5} OR MEMBER_MOVED_THIS_TURN
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{toujyou.png|登場}}自分のステージに「大沢瑠璃乃」か「百生吟子」か「徒町小鈴」がいる場合、エネルギーを1枚アクティブにし、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
...
**Cards:** PL!HS-sd1-006-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
CONDITION: HAS_MEMBER {FILTER="NAME=大沢瑠璃乃 OR NAME=百生吟子 OR NAME=徒町小鈴"}
EFFECT: ACTIVATE_ENERGY(1); RECOVER_LIVE(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: ADD_BLADES(2) -> SELF
```

---

## Ability: {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から{{icon_score.png|スコア}}を持つ『Aqours』のライブカードを1枚手札...
**Cards:** PL!S-sd1-007-SD

**Consolidated Pseudocode:**
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=1, HAS_SCORE"} -> CARD_HAND
```

---

## Ability: {{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。こ...
**Cards:** PL!HS-sd1-002-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: LOOK_DECK(5) {TYPE_MEMBER}; MOVE_TO_HAND(1) (Optional); DISCARD_REMAINDER
CONDITION: DRAWN_CARDS {FILTER="GROUP_ID=4"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=5} -> SELF; ADD_BLADES(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のステージにいるこのメンバー以外の『蓮ノ空』のメンバー1人は、{{he...
**Cards:** PL!HS-sd1-003-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=4, NOT_SELF"} -> TARGET
EFFECT: ADD_HEARTS(1) {HEART_TYPE=1} -> TARGET; ADD_BLADES(1) -> TARGET
```

---

## Ability: {{toujyou.png|登場}}カードを1枚引く。...
**Cards:** PL!HS-bp5-011-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1)
```

---

## Ability: {{toujyou.png|登場}}相手のステージにいるコスト4以下のメンバー1人をウェイトにする。...
**Cards:** PL!-bp5-013-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}
```

---

## Ability: {{live_success.png|ライブ成功時}}自分が余剰ハートを3つ以上持っている場合、それらをすべて失い、このカードのスコアを＋１する。...
**Cards:** PL!S-bp5-020-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: EXTRA_HEARTS {MIN=3}
EFFECT: CONSUME_EXTRA_HEARTS(ALL); BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバー1人につき、カードを1枚引く。その後、これにより引いた枚数と同じ枚数を手札から控え室に置く。...
**Cards:** PL!S-sd1-020-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(1) {PER_CARD="STAGE", FILTER="GROUP_ID=1"}; DISCARD_HAND(1) {PER_CARD="DRAWN"}
```

---

## Ability: {{jidou.png|自動}}このメンバーがコスト10以上の『蓮ノ空』のメンバーとバトンタッチして控え室に置かれた
とき、エネルギーを2枚アクティブにする。...
**Cards:** PL!HS-sd1-001-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LEAVES
CONDITION: BATON_TOUCH {FILTER="GROUP_ID=4, COST_GE_10"}
EFFECT: ACTIVATE_ENERGY(2)
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『蓮ノ空』のメンバー1人を含むメンバーが2人以上おり、かつそれらのメンバーの...
**Cards:** PL!HS-bp5-017-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
CONDITION: HAS_MEMBER {FILTER="GROUP_ID=4"}, COUNT_STAGE {MIN=2}, UNIQUE_UNITS {AREA="STAGE", MIN=2}
EFFECT: BOOST_SCORE(1) -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_01.png|heart01}}を得る。...
**Cards:** PL!HS-PR-029-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: ADD_HEARTS(1) {HEART_TYPE=1} -> SELF
```

---

## Ability: {{toujyou.png|登場}}{{center.png|センター}}ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!SP-bp5-015-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY (Center Only)
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のセンターエリアに『μ's』のメンバーがいる場合、そのメンバーが持つ{{heart_03.png|heart03}}2つにつき、このカードの必要ハ...
**Cards:** PL!-bp5-020-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="GROUP_ID=0, AREA=CENTER"}
EFFECT: REDUCE_HEART_REQ(1) {HEART_TYPE=0, SCALE="0.5_PER_HEART_03_OF_CENTER", MAX=3} -> SELF
```

---

## Ability: {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!HS-bp5-014-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_POSITION_CHANGE (Once per turn)
EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{live_start.png|ライブ開始時}}{{heart_04.png|heart04}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}の...
**Cards:** PL!-bp5-011-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: HEART_SELECT(1) {CHOICES=[4, 5, 6]} -> CHOICE
EFFECT: ADD_HEARTS(SUCCESS_LIVE_COUNT) {HEART_TYPE=CHOICE, DURATION="UNTIL_LIVE_END"}
```

---

## Ability: {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|...
**Cards:** PL!HS-bp5-016-N

**Consolidated Pseudocode:**
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: TAP_OPPONENT(2) {FILTER="COST_LE_4"}

TRIGGER: CONSTANT
CONDITION: OPP_TAP_COUNT {GE=2}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=6}
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージに『Aqours』のメンバーと『SaintSnow』のメンバーがいて、かつそれらのメンバーのコストが合計20以上の場合、自分の控え室にあ...
**Cards:** PL!S-bp5-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="GROUP_ID=1"}, HAS_MEMBER {FILTER="NAME=SaintSnow"}, SUM_COST {FILTER="GROUP_ID=1 OR NAME=SaintSnow", MIN=20}
EFFECT: MOVE_TO_DECK(4) {FROM="DISCARD", FILTER="GROUP_ID=1 OR NAME=SaintSnow", TYPE_LIVE, TO="DECK_TOP"} (Optional)
```

---

## Ability: {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード1枚につき、このカードのスコアを＋２し、必要ハートを{{heart_01.png|heart01}}{{hea...
**Cards:** PL!-bp5-022-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="SUCCESS_LIVE"}
EFFECT: INCREASE_HEART_REQ(1) {HEART_TYPE="01/03/06/00", PER_CARD="SUCCESS_LIVE"} -> SELF
```

---

## Ability: {{live_success.png|ライブ成功時}}自分のステージに、元々持つハートの数より多い数のハートを持つメンバーがいる場合、カードを1枚引く。...
**Cards:** PL!HS-PR-028-PR

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAS_MEMBER {FILTER="EXTRA_HEARTS_GE_1"}
EFFECT: DRAW(1) -> PLAYER
```

---

## Ability: {{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。...
**Cards:** PL!SP-bp5-016-N

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: ENERGY_COUNT {GE=10}
EFFECT: ADD_HEARTS(2) {HEART_TYPE=6}
```

---

## Ability: {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『Aqours』のメンバーは{{icon_blade.png|ブレード}}を得る。...
**Cards:** PL!S-sd1-022-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: ADD_BLADES(1) -> PLAYER {FILTER="GROUP_ID=1", AREA="STAGE"}
```

---

## Ability: {{live_start.png|ライブ開始時}}カードを1枚引いてもよい。そうした場合、手札2枚を好きな順番でデッキの上に置く。...
**Cards:** PL!S-sd1-004-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: DRAW(1) (Optional); MOVE_TO_DECK(2) {FROM="HAND", TO="DECK_TOP"}
```

---

## Ability: {{live_start.png|ライブ開始時}}手札の『Aqours』のカードを1枚公開してもよい：これにより公開したカードをデッキの一番上か一番下に置き、ライブ終了時まで、{{icon_blade...
**Cards:** PL!S-sd1-009-SD

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
COST: REVEAL_HAND(1) {FILTER="GROUP_ID=1"} (Optional)
EFFECT: MOVE_TO_DECK(1) {FROM="REVEALED", TO="DECK_TOP_OR_BOTTOM"}; ADD_BLADES(1) -> SELF
```

---

## Ability: {{jyouji.png|常時}}自分のライブカード置き場に必要ハートの合計が8以上の『Liella!』のライブカードがあるかぎり、{{heart_03.png|heart03}}を得る。...
**Cards:** PL!SP-bp5-012-N

**Consolidated Pseudocode:**
```
TRIGGER: CONSTANT
CONDITION: HAS_LIVE_CARD {FILTER="GROUP_ID=3, HEARTS_SUM_GE=8", ZONE="SUCCESS_LIVE"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=3} -> SELF
```

---

## Ability: {{live_start.png|ライブ開始時}}自分のステージにいる{{heart_01.png|heart01}}と{{heart_06.png|heart06}}以外の色のハートを持つメンバー1...
**Cards:** PL!-bp5-023-L

**Consolidated Pseudocode:**
```
TRIGGER: ON_LIVE_START
EFFECT: REDUCE_HEART_REQ(1) {HEART_TYPE=0, PER_CARD="STAGE", FILTER="NOT_COLOR_RED, NOT_COLOR_ALL"} -> SELF
```

---
