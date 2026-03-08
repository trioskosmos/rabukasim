# QA Test Plans

## Q205
**Question:** 自分のライブ中のライブカードが2枚あり、片方のライブカードの必要ハートには
{{heart_01.png|heart01}}
{{heart_02.png|heart02}}
{{heart_03.png|heart03}}
が、他方には
{{heart_04.png|heart04}}
{{heart_05.png|heart05}}
{{heart_06.png|heart06}}
が含まれています。
このとき、このカードは
{{icon_all.png|ハート}}
を得ますか？

**Answer:** はい、得ます。

**Related Cards:**
- PL!N-pb1-007-P＋ (優木せつ菜)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: LIVE_HEART_REQUIRED_COLORS {COLORS=[1, 2, 3, 4, 5, 6]}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=0} -> SELF
- PL!N-pb1-007-R (優木せつ菜)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: LIVE_HEART_REQUIRED_COLORS {COLORS=[1, 2, 3, 4, 5, 6]}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=0} -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q204
**Question:** 自分のステージにいるメンバーが、「PL!N-pb1-016-R 朝香果林」と「LL-bp4-001-R+ 絢瀬絵里&朝香果林&葉月 恋」や「PL!N-pb1-021-R 天王寺璃奈」と「 LL-bp3-001-R+ 園田海未&津島善子&天王寺璃奈」のような状況でも、このカードのライブ開始時の効果の条件を満たしますか？

**Answer:** はい。満たします。

**Related Cards:**
- PL!N-pb1-042-L (Eternalize Love!!)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=2, SAME_NAME=TRUE, FILTER="Nijigasaki"}
EFFECT: REDUCE_HEART_REQ(3) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q200
**Question:** このカードの能力で「PL!N-sd1-013-SD 上原歩夢」を登場させたとき、そのカードの登場能力は使用できますか？

**Answer:** はい。できます。

**Related Cards:**
- PL!N-pb1-013-P＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='上原歩夢', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-013-R (上原歩夢)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='上原歩夢', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q199
**Question:** このカードの能力で登場させたメンバーを、そのターンのうちにバトンタッチすることはできますか？

**Answer:** いいえ。できません。

**Related Cards:**
- PL!N-pb1-013-P＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='上原歩夢', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-013-R (上原歩夢)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='上原歩夢', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-015-P＋ (桜坂しずく)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='桜坂しずく', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-015-R (桜坂しずく)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='桜坂しずく', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-017-P＋ (宮下 愛)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='宮下愛', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-017-R (宮下 愛)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='宮下愛', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-023-P＋ (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='ミア・テイラー', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)
- PL!N-pb1-023-R (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NAME='ミア・テイラー', COST_LE_4", ZONE="HAND"} -> TARGET; PLAY_MEMBER(TARGET)

**Planned Board:**
- Member in hand ready to play.
- Member(s) on stage to baton touch.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.
- Perform baton touch and verify outcome.

---

## Q198
**Question:** このカードとバトンタッチしてコスト11のメンバーが登場した場合、このカードの自動能力は発動できますか？

**Answer:** いいえ。できません。

**Related Cards:**
- PL!N-pb1-012-P＋ (鐘 嵐珠)
  - **Ability:** TRIGGER: ON_STAGE_ENTRY (Once per turn)
CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER", FILTER="COST=11"}
EFFECT: ACTIVATE_ENERGY(1, MODE="WAIT") -> PLAYER

TRIGGER: ON_LIVE_SUCCESS
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=2", ZONE="YELL_REVEALED"} -> CARD_HAND
- PL!N-pb1-012-R (鐘 嵐珠)
  - **Ability:** TRIGGER: ON_STAGE_ENTRY (Once per turn)
CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER", FILTER="COST=11"}
EFFECT: ACTIVATE_ENERGY(1, MODE="WAIT") -> PLAYER

TRIGGER: ON_LIVE_SUCCESS
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=2", ZONE="YELL_REVEALED"} -> CARD_HAND

**Planned Board:**
- Member in hand ready to play.
- Member(s) on stage to baton touch.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.
- Perform baton touch and verify outcome.

---

## Q194
**Question:** {{jyouji.png|常時}}
このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。
---
2人のメンバーとバトンタッチする際、2人の中にこのターン中に登場したメンバーを含んでいてもバトンタッチできますか？

**Answer:** いいえ、2人とも前のターンから登場している必要があります。

**Related Cards:**
- PL!SP-bp4-004-R＋ (平安名すみれ)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: BATON_TOUCH_MOD(2) (Optional) -> SELF

TRIGGER: ON_PLAY
CONDITION: AREA="CENTER", BATON_TOUCH {FILTER="GROUP_ID=3", COUNT_EQ_2}
EFFECT: DRAW(2); PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=3, COST_LE_4"}

**Planned Board:**
- Member in hand ready to play.
- Member(s) on stage to baton touch.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.
- Perform baton touch and verify outcome.

---

## Q193
**Question:** 2人のメンバーとバトンタッチした際、このメンバーが登場できるエリアはどこになりますか？

**Answer:** バトンタッチした2人のメンバーがいたエリアのうち、いずれかのエリアに登場します。登場するエリアはプレイヤーが任意に選べます。

**Related Cards:**
- PL!SP-bp4-004-R＋ (平安名すみれ)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: BATON_TOUCH_MOD(2) (Optional) -> SELF

TRIGGER: ON_PLAY
CONDITION: AREA="CENTER", BATON_TOUCH {FILTER="GROUP_ID=3", COUNT_EQ_2}
EFFECT: DRAW(2); PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=3, COST_LE_4"}

**Planned Board:**
- Member in hand ready to play.
- Member(s) on stage to baton touch.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.
- Perform baton touch and verify outcome.

---

## Q192
**Question:** ライブ成功時効果によって公開されたブレードハートの色が変更されており、かつALLハートをエールによって得た場合、PL!N-bp03-030-Lのライブ成功時効果の条件を満たしますか？

**Answer:** いいえ。満たしません。

**Related Cards:**
- PL!N-bp3-030-L (Love U my friends)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: YELL_PILE_CONTAINS {FILTER="HAS_ALL_BLADE"}
EFFECT: BOOST_SCORE(1) -> SELF
- PL!N-bp4-025-L (VIVID WORLD)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: TRANSFORM_YELL_BLADES(ALL) -> 5 {FILTER="NOT_BLADE_TYPE_5", DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: SELECT_YELL(1) {FILTER="GROUP_ID=2, HAS_HEART_REQUIRED_ANY_COLOR"}
EFFECT: BOOST_SCORE(1) -> SELF
- PL!SP-bp4-023-L (Dazzling Game)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="NAME_IN=['澁谷かのん', 'ウィーン・マルガレーテ', '鬼塚冬毬']"} -> TARGET_1; SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_TARGET=TARGET_1"} -> TARGET_2; ADD_BLADES(1) -> TARGET_1; ADD_BLADES(1) -> TARGET_2

TRIGGER: ON_LIVE_START
EFFECT: TRANSFORM_YELL_BLADES(ALL) -> 6 {FILTER="NOT_BLADE_TYPE_6", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q191
**Question:** ライブ成功時効果が発動した際、同じ効果を２回選ぶことができますか？

**Answer:** いいえ。できません。

**Related Cards:**
- PL!N-bp4-030-L (Daydream Mermaid)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
EFFECT: CHOICE_MODE (MIN=1) -> PLAYER
  CONDITION: NOT_HAS_SUCCESS_LIVE {FILTER="GROUP_ID=2"} -> CHOICE_MODE(COUNT=1)
  OPTION: エネルギー | EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
  OPTION: メンバー | EFFECT: SELECT_RECOVER_MEMBER(1) -> CARD_HAND

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q190
**Question:** 好きなハートの色を選ぶとき、ALLハートを選ぶことはできますか？

**Answer:** いいえ。できません。

**Related Cards:**
- PL!N-bp4-011-P (ミア・テイラー)
  - **Ability:** {{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。

**Planned Board:**
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q187
**Question:** 「これにより選んだメンバー以外の『Liella!』のメンバー１人は、
{{icon_blade.png|ブレード}}
を得る。」について、選んだメンバー以外のメンバーを選ぶ必要がありますか？

**Answer:** はい。あります。

**Related Cards:**
- PL!SP-bp4-023-L (Dazzling Game)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="NAME_IN=['澁谷かのん', 'ウィーン・マルガレーテ', '鬼塚冬毬']"} -> TARGET_1; SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_TARGET=TARGET_1"} -> TARGET_2; ADD_BLADES(1) -> TARGET_1; ADD_BLADES(1) -> TARGET_2

TRIGGER: ON_LIVE_START
EFFECT: TRANSFORM_YELL_BLADES(ALL) -> 6 {FILTER="NOT_BLADE_TYPE_6", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q186
**Question:** 『
{{jyouji.png|常時}}
手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。』について、
手札の枚数によって、LL-bp2-001-R+のコストは0になりますか？

**Answer:** はい、なります。

**Related Cards:**
- LL-bp2-001-R＋ (渡辺 曜&鬼塚夏美&大沢瑠璃乃)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: COUNT_HAND(PLAYER) {FILTER="NOT_SELF"} -> COUNT_VAL; REDUCE_COST(COUNT_VAL)

TRIGGER: CONSTANT
EFFECT: PREVENT_BATON_TOUCH(SELF)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE) {FILTER="NAME_IN=['渡辺曜', '鬼塚夏美', '大沢瑠璃乃']"} -> DISCARD_COUNT
EFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); ADD_BLADES(1, PER_CARD=DISCARD_COUNT) -> SELF {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q185
**Question:** {{live_start.png|ライブ開始時}}
能力による質問への回答が「クッキー＆クリームよりもあなた」でした。
この場合、どの回答として扱いますか？

**Answer:** 質問者と回答者のお互いが正しく認識できる場合、回答が一字一句同じものである必要はありません。
対戦相手がどの回答として答えたのか確認をしてください。

**Related Cards:**
- LL-PR-004-PR (愛♡スクリ～ム！)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(PLAYER) {OPTIONS=["CHOC_STRAW_COOKIE", "YOU", "OTHER"]} -> CHOICE;
CONDITION: VALUE_EQ(CHOICE, "CHOC_STRAW_COOKIE"); DISCARD_HAND(1, PLAYER); DISCARD_HAND(1, OPPONENT);
CONDITION: VALUE_EQ(CHOICE, "YOU"); DRAW(1, PLAYER); DRAW(1, OPPONENT);
CONDITION: VALUE_EQ(CHOICE, "OTHER"); ADD_BLADES(1, PLAYER) {DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1, OPPONENT) {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q184
**Question:** エネルギーカードをメンバーカードの下に置いているとき、メンバーカードの下に置かれたエネルギーカードはエネルギーの数として数えますか？

**Answer:** いいえ。数えません。
エネルギーの枚数を参照する際、メンバーカードの下に置かれたエネルギーカードは参照しません。

**Related Cards:**
- PL!N-bp3-001-P (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-001-P＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-001-R＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-007-P (優木せつ菜)
  - **Ability:** TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); SACRIFICE_SELF
EFFECT: SELECT_HAND(1) {FILTER="NAME='Setsuna Yuki', COST_LE_13"} -> TARGET; PLAY_STAGE_SPECIFIC_SLOT(TARGET) {SLOT="SAME_SLOT", MODE="WAIT"}(Optional) -> TARGET_PLAYED
EFFECT: SELECT_ENERGY(1) -> ATTACH_MEMBER(TARGET_PLAYED)
- PL!N-bp3-007-R (優木せつ菜)
  - **Ability:** TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); SACRIFICE_SELF
EFFECT: SELECT_HAND(1) {FILTER="NAME='Setsuna Yuki', COST_LE_13"} -> TARGET; PLAY_STAGE_SPECIFIC_SLOT(TARGET) {SLOT="SAME_SLOT", MODE="WAIT"}(Optional) -> TARGET_PLAYED
EFFECT: SELECT_ENERGY(1) -> ATTACH_MEMBER(TARGET_PLAYED)
- PL!N-bp3-013-N (上原歩夢)
  - **Ability:** TRIGGER: ON_PLAY
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional)
EFFECT: DRAW(2)
- PL!N-bp3-001-SEC (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q182
**Question:** 『
{{live_success.png|ライブ成功時}}
このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、このカードのスコアは４になる。』について、
ウェイト状態などによってエールで公開したカードが０枚の場合、このライブカードのスコアはいくつになりますか？

**Answer:** 「エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合」という条件を満たすため、ライブに成功した際のスコアは4となります。

**Related Cards:**
- PL!S-bp3-019-L (MIRACLE WAVE)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: OR(YELL_PILE_CONTAINS {FILTER="TYPE_NOT=BLADE_HEART", MAX=0}, SURPLUS_HEARTS_COUNT {MIN=2})
EFFECT: SET_SCORE(4) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q180
**Question:** 『
{{toujyou.png|登場}}
このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。』について、この効果が発動したターンにアクティブフェイズを迎えました。そのアクティブフェイズでメンバーをアクティブにできますか？

**Answer:** はい、できます。

**Related Cards:**
- PL!-pb1-009-R (矢澤にこ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BASE_BLADES_LE_1"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DISABLE_ACTIVATE_BY_EFFECT(ALL_MEMBERS) {DURATION="UNTIL_TURN_END"}
- PL!-pb1-009-P＋ (矢澤にこ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, BASE_BLADES_LE_1"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DISABLE_ACTIVATE_BY_EFFECT(ALL_MEMBERS) {DURATION="UNTIL_TURN_END"}

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q179
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいる『Printemps』のメンバーをアクティブにする。これによりウェイト状態のメンバーが３人以上アクティブ状態になったとき、このカードのスコアを＋１する。』について、元々アクティブ状態のメンバーが３枚いる状態でこの効果を解決した際、スコアを＋１することはできますか？

**Answer:** いいえ、できません。
この効果によって、ウェイト状態のメンバー3人以上をアクティブにする必要があります。

**Related Cards:**
- PL!-pb1-028-L (WAO-WAO Powerful day!)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(ALL) {FILTER="UNIT_PRINTEMPS"} -> PLAYER -> RECOVERY_COUNT
CONDITION: VALUE_GE(RECOVERY_COUNT, 3)
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q178
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいる『Printemps』のメンバーをアクティブにする。』について、メンバーを複数枚アクティブにするにすることはできますか？

**Answer:** はい、できます。

**Related Cards:**
- PL!-pb1-028-L (WAO-WAO Powerful day!)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(ALL) {FILTER="UNIT_PRINTEMPS"} -> PLAYER -> RECOVERY_COUNT
CONDITION: VALUE_GE(RECOVERY_COUNT, 3)
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q177
**Question:** 『
{{jidou.png|自動}}
{{turn1.png|ターン1回}}
自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト４以下のメンバーがウェイト状態になったとき、カードを１枚引く。』について、条件を満たした場合でも自動能力の効果を解決しないことはできますか？

**Answer:** いいえ、必ず解決する必要があります。

**Related Cards:**
- PL!-pb1-015-P＋ (西木野真姫)
  - **Ability:** TRIGGER: ON_PLAY, ON_LIVE_START
CONDITION: IS_CENTER
COST: SELECT_MEMBER(1) {FILTER="UNIT_BIBI"} -> TARGET; TAP_MEMBER(TARGET) (Optional)
EFFECT: TAP_OPPONENT(1)

TRIGGER: ON_MEMBER_TAP {FILTER="OPPONENT, COST_LE_4", REASON="EFFECT"} (Once per turn)
EFFECT: DRAW(1)
- PL!-pb1-015-R (西木野真姫)
  - **Ability:** TRIGGER: ON_PLAY, ON_LIVE_START
CONDITION: IS_CENTER
COST: SELECT_MEMBER(1) {FILTER="UNIT_BIBI"} -> TARGET; TAP_MEMBER(TARGET) (Optional)
EFFECT: TAP_OPPONENT(1)

TRIGGER: ON_MEMBER_TAP {FILTER="OPPONENT, COST_LE_4", REASON="EFFECT"} (Once per turn)
EFFECT: DRAW(1)

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q176
**Question:** 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
:自分の手札を相手は見ないで１枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時までこのメンバーは「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。』について、公開するのは自分の手札ですか？相手の手札ですか？

**Answer:** 自分の手札を公開します。

**Related Cards:**
- PL!-pb1-013-P＋ (園田海未)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: SELECT_HAND(1) {TARGET="OPPONENT_HIDDEN"} -> REVEAL -> REVEALED_CARD
EFFECT: CONDITION: SELECT_CARD(REVEALED_CARD) {FILTER="TYPE_LIVE"}
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!-pb1-013-R (園田海未)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: SELECT_HAND(1) {TARGET="OPPONENT_HIDDEN"} -> REVEAL -> REVEALED_CARD
EFFECT: CONDITION: SELECT_CARD(REVEALED_CARD) {FILTER="TYPE_LIVE"}
EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q175
**Question:** 『
{{live_start.png|ライブ開始時}}
手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、
{{heart_04.png|heart04}}
{{heart_04.png|heart04}}
{{icon_blade.png|ブレード}}
{{icon_blade.png|ブレード}}
を得る。』などについて、この能力を使用しているメンバーカードと同じユニットの必要はありますか？

**Answer:** いいえ、同じユニットである必要はありません。
手札から控え室に置くカードのユニットが同じである必要があります。ただし、「μ's」や「Aqours」など、グループ名は参照できません。

**Related Cards:**
- PL!HS-PR-017-PR (村野さやか)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2, Optional) -> DISCARDED; CONDITION: SAME_UNIT(DISCARDED)
EFFECT: ADD_HEARTS(2) -> SELF {HEART_TYPE=PINK, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!HS-PR-016-PR (日野下花帆)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2, Optional) -> DISCARDED; CONDITION: SAME_UNIT(DISCARDED)
EFFECT: ADD_HEARTS(2) -> SELF {HEART_TYPE=BLUE, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q174
**Question:** 『
{{live_success.png|ライブ成功時}}
このターン、自分が余剰ハートに
{{heart_04.png|heart04}}
を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。』について、ステージに緑ハートがなくエールによってALLハートを3枚獲得してライブ成功した時、ライブ成功時能力は使えますか？

**Answer:** いいえ。使えません。

**Related Cards:**
- PL!N-bp3-027-L (La Bella Patria)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_CONTAINS {HEART_TYPE=4, MIN=1}
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=2"}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q173
**Question:** 『
{{live_success.png|ライブ成功時}}
このターン、自分が余剰ハートに
{{heart_04.png|heart04}}
を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。』について、この能力を持つカードを2枚同時にライブをしました。この時、余剰ハートが
{{heart_04.png|heart04}}
1つの場合、それぞれの能力は使用できますか？

**Answer:** はい、可能です。

**Related Cards:**
- PL!N-bp3-027-L (La Bella Patria)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_CONTAINS {HEART_TYPE=4, MIN=1}
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=2"}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q172
**Question:** 『
{{live_success.png|ライブ成功時}}
自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを＋１する。』について、ハートの総数を数えるとき、能力によって得たハートも含みますか？

**Answer:** はい、含みます。ただし、エールによって得たブレードハートは含みません。

**Related Cards:**
- PL!-bp3-026-L (Oh,Love&Peace!)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(3) -> TARGET {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: HEARTS_COUNT(PLAYER) > HEARTS_COUNT(OPPONENT)
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q171
**Question:** 『ライブ終了時まで』と指定のある能力を使用したターンのパフォーマンスフェイズにライブを行わなかった場合、どうなりますか。

**Answer:** ライブを行ったかどうかにかかわらず、ライブ終了時を期限とする能力はライブ勝敗判定フェイズの終了時に無くなります。

**Related Cards:**
- PL!HS-bp2-008-P (徒町 小鈴)
  - **Ability:** TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_DOLL, COST_LT=SELF"}
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!HS-bp2-008-R (徒町 小鈴)
  - **Ability:** TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_DOLL, COST_LT=SELF"}
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!HS-bp2-009-P (安養寺 姫芽)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_MIRAKURA, COST_LT=SELF"}
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}
- PL!HS-bp2-009-R (安養寺 姫芽)
  - **Ability:** TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
CONDITION: BATON_TOUCH(PLAYER) {FILTER="UNIT_MIRAKURA, COST_LT=SELF"}
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}
- PL!HS-PR-019-PR (百生 吟子)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
CONDITION: ALL_MEMBERS {FILTER="HEART_04", ZONE="DISCARDED_THIS"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF
- PL!HS-PR-021-PR (安養寺 姫芽)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
CONDITION: ALL_MEMBERS {FILTER="HEART_01", ZONE="DISCARDED_THIS"}
EFFECT: ADD_HEARTS(1) {HEART_TYPE=1} -> SELF
- PL!N-bp3-011-P (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, NOT_NAME='Mia'"} -> TARGET_MEMBER
EFFECT: CONDITION: HAS_MATCHING_HEART(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_COST(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_BASE_BLADE(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-011-R (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT, NOT_NAME='Mia'"} -> TARGET_MEMBER
EFFECT: CONDITION: HAS_MATCHING_HEART(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_COST(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: HAS_MATCHING_BASE_BLADE(SELF, TARGET_MEMBER); ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-P (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-P＋ (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-R＋ (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-pb1-002-P＋ (桜内梨子)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} -> OPPONENT
  OPTION: {{grant_ability.png|能力を得る}} | EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-pb1-002-R (桜内梨子)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} -> OPPONENT
  OPTION: {{grant_ability.png|能力を得る}} | EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-pb1-006-P＋ (津島善子)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_HAND(1) {FILTER="TYPE_LIVE"} -> REVEALED; REVEAL(REVEALED)
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) -> OPPONENT
  OPTION: {{no_action.png|何もしない}} | EFFECT: ADD_BLADES(4) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!S-pb1-006-R (津島善子)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_HAND(1) {FILTER="TYPE_LIVE"} -> REVEALED; REVEAL(REVEALED)
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) -> OPPONENT
  OPTION: {{no_action.png|何もしない}} | EFFECT: ADD_BLADES(4) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!S-PR-016-PR (黒澤ダイヤ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!S-PR-020-PR (小原鞠莉)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!S-PR-021-PR (黒澤ルビィ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-P (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-P＋ (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-R＋ (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-SEC (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp2-001-P (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
- PL!SP-bp2-001-P＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
- PL!SP-bp2-001-R＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
- PL!SP-bp2-001-SEC (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
- PL!SP-pb1-006-P＋ (桜小路きな子)
  - **Ability:** TRIGGER: ON_POSITION_CHANGE(SELF), ON_PLAY(SELF)
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-pb1-006-R (桜小路きな子)
  - **Ability:** TRIGGER: ON_POSITION_CHANGE(SELF), ON_PLAY(SELF)
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-sd1-004-SD (平安名すみれ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: GRANT_ABILITY(SELF, TRIGGER="CONSTANT", CONDITION="IS_ON_STAGE", EFFECT="BOOST_SCORE(1)")
- PL!S-bp3-001-SEC (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q167
**Question:** 『
{{kidou.png|起動}}
{{center.png|センター}}
{{turn1.png|ターン1回}}
このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。』について。
メインデッキにも控え室にもライブカードかコスト10以上のメンバーカードがない状態で、この能力を使った場合、どうなりますか？

**Answer:** 効果や処理は実行可能な限り解決し、一部でも実行可能な場合はその一部を解決します。まったく解決できない場合は何も行いません。
この場合、メインデッキのカードをすべて公開してリフレッシュを行い、さらに新しいメインデッキのカードをすべて公開した時点で『選んだカードが公開されるまで、自分のデッキの一番上からカードを1枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。』の解決を終了します。
続いて『そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。』を解決します。手札に加えるライブカードはなく、公開したカードを控え室に置き、リフレッシュを行います。

**Related Cards:**
- PL!-pb1-001-P＋ (高坂穂乃果)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: ライブカード | EFFECT: REVEAL_UNTIL(TYPE_LIVE) -> CARD_HAND; DISCARD_REMAINDER
  OPTION: コスト10以上のメンバー | EFFECT: REVEAL_UNTIL(TYPE_MEMBER, COST_GE_10) -> CARD_HAND; DISCARD_REMAINDER
- PL!-pb1-001-R (高坂穂乃果)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: ライブカード | EFFECT: REVEAL_UNTIL(TYPE_LIVE) -> CARD_HAND; DISCARD_REMAINDER
  OPTION: コスト10以上のメンバー | EFFECT: REVEAL_UNTIL(TYPE_MEMBER, COST_GE_10) -> CARD_HAND; DISCARD_REMAINDER

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q166
**Question:** 『
{{kidou.png|起動}}
{{center.png|センター}}
{{turn1.png|ターン1回}}
このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。』について。
この能力の効果の解決中に、メインデッキのカードが無くなりました。「リフレッシュ」の処理はどうなりますか？

**Answer:** 能力に効果によって公開しているカードを含めずに「リフレッシュ」をして控え室のカードを新たなメインデッキにします。その後、効果の解決を再開します。

**Related Cards:**
- PL!-pb1-001-P＋ (高坂穂乃果)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: ライブカード | EFFECT: REVEAL_UNTIL(TYPE_LIVE) -> CARD_HAND; DISCARD_REMAINDER
  OPTION: コスト10以上のメンバー | EFFECT: REVEAL_UNTIL(TYPE_MEMBER, COST_GE_10) -> CARD_HAND; DISCARD_REMAINDER
- PL!-pb1-001-R (高坂穂乃果)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: CHOICE_MODE -> PLAYER
  OPTION: ライブカード | EFFECT: REVEAL_UNTIL(TYPE_LIVE) -> CARD_HAND; DISCARD_REMAINDER
  OPTION: コスト10以上のメンバー | EFFECT: REVEAL_UNTIL(TYPE_MEMBER, COST_GE_10) -> CARD_HAND; DISCARD_REMAINDER

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q165
**Question:** 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚までアクティブにする。』について。
「園田海未」と「津島善子」と「天王寺璃奈」をそれぞれ1枚以上含める必要はありますか？

**Answer:** いいえ、ありません。
「園田海未」と「津島善子」と「天王寺璃奈」のいずれか合計6枚をシャッフルしてデッキの下に置くことで能力を使用することができます。

**Related Cards:**
- LL-bp3-001-R＋ (園田海未&津島善子&天王寺璃奈)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DECK(6) {FILTER="Umi/Yoshiko/Rina", FROM="DISCARD"}
EFFECT: ACTIVATE_ENERGY(6) -> PLAYER

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(6)
EFFECT: ADD_BLADES(3) -> PLAYER

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q164
**Question:** 『
{{live_start.png|ライブ開始時}}
控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、
{{icon_all.png|ハート}}
を得る。合計が25の場合、ライブ終了時まで、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。』について。
この能力の「控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい」で、相手の控え室にあるメンバーカードをデッキの下に置くことはできますか？

**Answer:** いいえ、できません。
自分の控え室にあるカードをデッキの下に置く必要があります。

**Related Cards:**
- PL!N-bp3-009-R＋ (天王寺璃奈)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_RECOVER_MEMBER(2) (Optional) -> DECK_BOTTOM -> CHOSEN_CARDS; CALC_SUM_COST(CHOSEN_CARDS) -> TOTAL_VAL
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 6); DRAW(1)
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 8); ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 25); GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-009-P＋ (天王寺璃奈)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_RECOVER_MEMBER(2) (Optional) -> DECK_BOTTOM -> CHOSEN_CARDS; CALC_SUM_COST(CHOSEN_CARDS) -> TOTAL_VAL
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 6); DRAW(1)
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 8); ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 25); GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-009-SEC (天王寺璃奈)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_RECOVER_MEMBER(2) (Optional) -> DECK_BOTTOM -> CHOSEN_CARDS; CALC_SUM_COST(CHOSEN_CARDS) -> TOTAL_VAL
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 6); DRAW(1)
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 8); ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 25); GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-009-P (天王寺璃奈)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_RECOVER_MEMBER(2) (Optional) -> DECK_BOTTOM -> CHOSEN_CARDS; CALC_SUM_COST(CHOSEN_CARDS) -> TOTAL_VAL
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 6); DRAW(1)
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 8); ADD_HEARTS(1) -> SELF {HEART_TYPE=0, DURATION="UNTIL_LIVE_END"}
EFFECT: CONDITION: VALUE_EQ(TOTAL_VAL, 25); GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q163
**Question:** 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。』について。
相手の『虹ヶ咲』のメンバーカードをウェイトにできますか？

**Answer:** いいえ、できません。
自分の『虹ヶ咲』のメンバーのみウェイトにすることができます。

**Related Cards:**
- PL!N-bp3-008-R＋ (エマ・ヴェルデ)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}; ADD_HEARTS(1) -> TARGET {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-008-P (エマ・ヴェルデ)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}; ADD_HEARTS(1) -> TARGET {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-008-P＋ (エマ・ヴェルデ)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}; ADD_HEARTS(1) -> TARGET {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-008-SEC (エマ・ヴェルデ)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=2, NOT_SELF"} -> TARGET; TAP_MEMBER(TARGET)
EFFECT: DRAW(1)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, STATUS=TAPPED"} -> TARGET; ACTIVATE_MEMBER(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(1) -> SELF {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}; ADD_HEARTS(1) -> TARGET {HEART_TYPE=4, DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q159
**Question:** 『
{{toujyou.png|登場}}
自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ。そのカードの
{{toujyou.png|登場}}
能力1つを発動させる。
（
{{toujyou.png|登場}}
能力がコストを持つ場合、支払って発動させる。）』
この能力で「このメンバーをウェイトにしてもよい」をコストに持つ
{{toujyou.png|登場}}
能力を発動できますか？

**Answer:** いいえ、できません。

**Related Cards:**
- PL!N-bp3-003-R (桜坂しずく)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: TRIGGER_REMOTE(1) {FILTER="GROUP_ID=2, TYPE_MEMBER, COST_LE_4", FROM="DISCARD"}
- PL!N-bp3-003-P (桜坂しずく)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: TRIGGER_REMOTE(1) {FILTER="GROUP_ID=2, TYPE_MEMBER, COST_LE_4", FROM="DISCARD"}

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q158
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは
{{icon_blade.png|ブレード}}
{{icon_blade.png|ブレード}}
を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）』などについて。
この能力を使用して
{{icon_blade.png|ブレード}}
{{icon_blade.png|ブレード}}
はステージにいるメンバー全員が得ますか？

**Answer:** はい、得ます。

**Related Cards:**
- PL!N-bp3-001-R＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-001-P (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-001-P＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-001-SEC (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q157
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは
{{icon_blade.png|ブレード}}
{{icon_blade.png|ブレード}}
を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）』などについて。
エネルギー置き場のウェイト状態のエネルギーをメンバーの下に置くことはできますか？

**Answer:** はい、可能です。
エネルギーの状態に限らずメンバーの下に置くことができます。

**Related Cards:**
- PL!N-bp3-001-R＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-001-P (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-001-P＋ (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}
- PL!N-bp3-007-R (優木せつ菜)
  - **Ability:** TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); SACRIFICE_SELF
EFFECT: SELECT_HAND(1) {FILTER="NAME='Setsuna Yuki', COST_LE_13"} -> TARGET; PLAY_STAGE_SPECIFIC_SLOT(TARGET) {SLOT="SAME_SLOT", MODE="WAIT"}(Optional) -> TARGET_PLAYED
EFFECT: SELECT_ENERGY(1) -> ATTACH_MEMBER(TARGET_PLAYED)
- PL!N-bp3-007-P (優木せつ菜)
  - **Ability:** TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); SACRIFICE_SELF
EFFECT: SELECT_HAND(1) {FILTER="NAME='Setsuna Yuki', COST_LE_13"} -> TARGET; PLAY_STAGE_SPECIFIC_SLOT(TARGET) {SLOT="SAME_SLOT", MODE="WAIT"}(Optional) -> TARGET_PLAYED
EFFECT: SELECT_ENERGY(1) -> ATTACH_MEMBER(TARGET_PLAYED)
- PL!N-bp3-013-N (上原歩夢)
  - **Ability:** TRIGGER: ON_PLAY
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional)
EFFECT: DRAW(2)
- PL!N-bp3-001-SEC (上原歩夢)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: SELECT_ENERGY(1) -> ATTACH_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1); SELECT_MEMBER(ALL) {FILTER="PLAYER"} -> TARGETS; ADD_BLADES(2) -> TARGETS {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q156
**Question:** 『
{{jidou.png|自動}}
{{turn1.png|ターン1回}}
エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい。そのエールで得たブレードハートを失い、もう一度エールを行う。』について。
「[PL!S-bp3-020-L]ダイスキだったらダイジョウブ！」2枚でライブをしている時、この能力を使用した場合、この能力を使用していないもう1枚の能力でもう一度エールを行えますか？

**Answer:** はい、可能です。

**Related Cards:**
- PL!S-bp3-020-L (ダイスキだったらダイジョウブ！)
  - **Ability:** TRIGGER: ON_YELL_REVEAL (Once per turn)
CONDITION: YELL_PILE_CONTAINS {FILTER="TYPE=BLADE_HEART", MAX=2}
EFFECT: DISCARD_YELL_PILE (Optional); RE_YELL

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q155
**Question:** 『
{{jyouji.png|常時}}
自分の成功ライブカード置き場にあるカード1枚につき、ステージにいるこのメンバーのコストを＋１する。』について。
自分の成功ライブカード置き場に1枚ある場合、このカードを登場させるコストは＋１されますか？

**Answer:** いいえ、されません。
この能力はステージにいる場合、コストが＋１されます。

**Related Cards:**
- PL!S-bp3-016-N (国木田花丸)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: INCREASE_COST(1, PER_CARD="SUCCESS_LIVE") -> SELF

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q154
**Question:** 『
{{kidou.png|起動}}
{{center.png|センター}}
{{turn1.png|ターン1回}}
このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる。（この能力はセンターエリアに登場している場合のみ起動できる。）』について。
自分の控え室に「そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカード」がない場合、どうなりますか？

**Answer:** 自分の控え室からメンバーカードを登場させず、そのままこの能力の処理を終わります。

**Related Cards:**
- PL!S-bp3-006-R＋ (津島善子)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, GROUP_ID=1"} -> TARGET_STAGE; MOVE_TO_DISCARD(TARGET_STAGE) -> SUCCESS; GET_COST(TARGET_STAGE) -> BASE_COST
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {FILTER="GROUP_ID=1, COST_EQ=BASE_COST+2"} -> TARGET_DISCARD; PLAY_STAGE_SPECIFIC_SLOT(TARGET_DISCARD) {SLOT="SAME_SLOT"}
- PL!S-bp3-006-P (津島善子)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, GROUP_ID=1"} -> TARGET_STAGE; MOVE_TO_DISCARD(TARGET_STAGE) -> SUCCESS; GET_COST(TARGET_STAGE) -> BASE_COST
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {FILTER="GROUP_ID=1, COST_EQ=BASE_COST+2"} -> TARGET_DISCARD; PLAY_STAGE_SPECIFIC_SLOT(TARGET_DISCARD) {SLOT="SAME_SLOT"}
- PL!S-bp3-006-P＋ (津島善子)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, GROUP_ID=1"} -> TARGET_STAGE; MOVE_TO_DISCARD(TARGET_STAGE) -> SUCCESS; GET_COST(TARGET_STAGE) -> BASE_COST
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {FILTER="GROUP_ID=1, COST_EQ=BASE_COST+2"} -> TARGET_DISCARD; PLAY_STAGE_SPECIFIC_SLOT(TARGET_DISCARD) {SLOT="SAME_SLOT"}
- PL!S-bp3-006-SEC (津島善子)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: TAP_SELF; DISCARD_HAND(1)
EFFECT: SELECT_MEMBER(1) {FILTER="NOT_SELF, GROUP_ID=1"} -> TARGET_STAGE; MOVE_TO_DISCARD(TARGET_STAGE) -> SUCCESS; GET_COST(TARGET_STAGE) -> BASE_COST
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {FILTER="GROUP_ID=1, COST_EQ=BASE_COST+2"} -> TARGET_DISCARD; PLAY_STAGE_SPECIFIC_SLOT(TARGET_DISCARD) {SLOT="SAME_SLOT"}

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q153
**Question:** 『
{{live_success.png|ライブ成功時}}
エールにより公開された自分のカードの枚数が、相手がエールによって公開したカードの枚数より少ない場合、カードを1枚引く。』について。
相手がライブをしていないときどうなりますか？

**Answer:** 相手がライブをしていない場合、エールにより公開されたカードが0枚のときと同じ扱いとなります。

**Related Cards:**
- PL!S-bp3-005-R (渡辺 曜)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: REDUCE_YELL_COUNT {LESS_THAN="OPPONENT"}
EFFECT: DRAW(1) -> PLAYER
- PL!S-bp3-005-P (渡辺 曜)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: REDUCE_YELL_COUNT {LESS_THAN="OPPONENT"}
EFFECT: DRAW(1) -> PLAYER

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q152
**Question:** 『
{{kidou.png|起動}}
{{center.png|センター}}
{{turn1.png|ターン1回}}
メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）』について。
この能力で相手のメンバーをウェイトにして能力を使用できますか？

**Answer:** いいえ、できません。

**Related Cards:**
- PL!S-bp3-001-R＋ (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-P (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-P＋ (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-SEC (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.
- Check score calculation.

---

## Q151
**Question:** 『
{{kidou.png|起動}}
{{center.png|センター}}
{{turn1.png|ターン1回}}
メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）』について。
この能力でウェイトにしたメンバーがステージから離れました。「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」の能力で合計スコアを＋１することはできますか？

**Answer:** いいえ、できません。
{{kidou.png|起動}}
能力の効果で
{{jyouji.png|常時}}
能力を得たこのメンバーカードがステージから離れることで、この
{{jyouji.png|常時}}
能力が無くなるため、合計スコアは＋１されません。

**Related Cards:**
- PL!S-bp3-001-R＋ (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-P (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-P＋ (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-bp3-001-SEC (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
CONDITION: IS_CENTER(SELF)
COST: SELECT_MEMBER(1) -> TARGET; TAP_MEMBER(TARGET)
EFFECT: GRANT_ABILITY(TARGET) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.
- Check score calculation.

---

## Q150
**Question:** 『
{{live_success.png|ライブ成功時}}
自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを＋１する。』について。
自分のステージに、ハートの数が2,3,5のメンバーがいます。相手のステージには、ハートの数が3,6のメンバーがいます。このとき、ライブ成功時の効果は発動しますか？

**Answer:** はい、発動します。
自分のステージのいるメンバーのハートの総数は10、相手のステージにいるメンバーのハートの総数は9となり、自分のほうが多いため発動します。

**Related Cards:**
- PL!-bp3-026-L (Oh,Love&Peace!)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(3) -> TARGET {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: HEARTS_COUNT(PLAYER) > HEARTS_COUNT(OPPONENT)
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q149
**Question:** 『
{{live_success.png|ライブ成功時}}
自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを＋１する。』について。
ハートの総数とはどのハートのことですか？

**Answer:** メンバーが持つ基本ハートの数を、色を無視して数えた値のことです。
例えば、
{{heart_03.png|heart03}}
{{heart_03.png|heart03}}
{{heart_03.png|heart03}}
{{heart_01.png|heart01}}
{{heart_06.png|heart06}}
を持つメンバーの場合、そのメンバーのハートの数は5つとなります。

**Related Cards:**
- PL!-bp3-026-L (Oh,Love&Peace!)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(3) -> TARGET {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: HEARTS_COUNT(PLAYER) > HEARTS_COUNT(OPPONENT)
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q148
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいるメンバーが持つ
{{icon_blade.png|ブレード}}
の合計が10以上の場合、このカードを成功させるための必要ハートは
{{heart_00.png|heart0}}
{{heart_00.png|heart0}}
少なくなる。』について。
この能力で自分のステージにいるウェイト状態のメンバーの
{{icon_blade.png|ブレード}}
は含みますか？

**Answer:** はい、含みます。

**Related Cards:**
- PL!-bp3-023-L (ミはμ'sicのミ)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: TOTAL_BLADES(PLAYER) {MIN=10}
EFFECT: REDUCE_HEART_REQ(2) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q147
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。』について。
この能力の「自分のライブ中の『μ's』のカードが2枚以上ある場合」を満たさず、このカードがスコア0の時、成功ライブカード置き場に置けますか？

**Answer:** はい、可能です。
スコア０の場合でもライブに勝利すれば成功ライブカード置き場に置くことができます。

**Related Cards:**
- PL!-bp3-019-L (僕らのLIVE 君とのLIFE)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {FILTER="GROUP_ID=0"} {MIN=2}
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q146
**Question:** 『
{{toujyou.png|登場}}
自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。』について。
この能力を使用する時、能力を発動しているステージに「[PL!-bp3-004-R＋]園田 海未」のみの場合、カードを1枚引けますか？

**Answer:** はい、可能です。
能力を発動メンバーも含めてステージにいるメンバーを数えます。

**Related Cards:**
- PL!-bp3-004-R＋ (園田海未)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: COUNT_MEMBER(PLAYER) -> COUNT_VAL; DRAW(COUNT_VAL); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=1}
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
- PL!-bp3-004-P (園田海未)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: COUNT_MEMBER(PLAYER) -> COUNT_VAL; DRAW(COUNT_VAL); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=1}
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
- PL!-bp3-004-P＋ (園田海未)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: COUNT_MEMBER(PLAYER) -> COUNT_VAL; DRAW(COUNT_VAL); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=1}
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
- PL!-bp3-004-SEC (園田海未)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: COUNT_MEMBER(PLAYER) -> COUNT_VAL; DRAW(COUNT_VAL); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE(PLAYER) {MIN=1}
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q145
**Question:** 『
{{toujyou.png|登場}}
このメンバーをウェイトにしてもよい：自分の控え室から『μ's』のメンバーカードを1枚手札に加える。（ウェイト状態のメンバーが持つ
{{icon_blade.png|ブレード}}
は、エールで公開する枚数を増やさない。）』などについて。
自分の控え室にメンバーカードがない時にこの能力を使用できますか？

**Answer:** はい、可能です。
ただし、手札に加えられるカードが控え室にある場合は必ず手札に加えます。

**Related Cards:**
- PL!-bp3-003-R (南ことり)
  - **Ability:** TRIGGER: ON_PLAY
COST: TAP_MEMBER (Optional)
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!-bp3-003-P (南ことり)
  - **Ability:** TRIGGER: ON_PLAY
COST: TAP_MEMBER (Optional)
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!-bp3-008-R＋ (小泉花陽)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=3, DURATION="UNTIL_LIVE_END"}
- PL!-bp3-008-P＋ (小泉花陽)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=3, DURATION="UNTIL_LIVE_END"}
- PL!-bp3-008-SEC (小泉花陽)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=3, DURATION="UNTIL_LIVE_END"}
- PL!-bp3-008-P (小泉花陽)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: TAP_SELF
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=0"} (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ADD_HEARTS(2) -> SELF {HEART_TYPE=3, DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Member in hand ready to play.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q144
**Question:** 『
{{toujyou.png|登場}}
手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ
{{icon_blade.png|ブレード}}
は、エールで公開する枚数を増やさない。）』について。
相手のステージにいるコスト4のメンバーが1人の時にこの能力を使用しました。相手のメンバーはウェイトにできますか？

**Answer:** はい、可能です。
「～まで」の能力は指定された数字以内の数字を選択することができます。

**Related Cards:**
- PL!-bp3-002-R (絢瀬絵里)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(2) {FILTER="OPPONENT, COST_LE=4, STATUS=ACTIVE"} -> TARGETS; TAP_MEMBER(TARGETS)

TRIGGER: CONSTANT
EFFECT: COUNT_MEMBER {FILTER="OPPONENT, STATUS=TAPPED"} -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF
- PL!-bp3-002-P (絢瀬絵里)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_MEMBER(2) {FILTER="OPPONENT, COST_LE=4, STATUS=ACTIVE"} -> TARGETS; TAP_MEMBER(TARGETS)

TRIGGER: CONSTANT
EFFECT: COUNT_MEMBER {FILTER="OPPONENT, STATUS=TAPPED"} -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF

**Planned Board:**
- Member in hand ready to play.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q142
**Question:** 余剰ハートを持つとは、どのような状態ですか？

**Answer:** ライブカードの必要ハートよりもステージのメンバーが持つ基本ハートとエールで獲得したブレードハートが多い状態です。
例えば、必要ハートが
{{heart_02.png|heart02}}
{{heart_02.png|heart02}}
{{heart_01.png|heart01}}
の時、基本ハートとエールで獲得したハートが
{{heart_02.png|heart02}}
{{heart_02.png|heart02}}
{{blade_heart01.png|ハート}}
{{blade_heart01.png|ハート}}
の場合、余剰ハートは
{{heart_01.png|heart01}}
1つになります。

**Related Cards:**
- PL!S-pb1-021-L (Strawberry Trapper)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=5"} {MIN=4}; SURPLUS_HEARTS_COUNT(OPPONENT) {EQ=0}
EFFECT: BOOST_SCORE(2) -> SELF
- PL!-bp3-025-L (タカラモノズ)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_COUNT {MAX=0}
EFFECT: BOOST_SCORE(1) -> SELF
- PL!N-bp3-027-L (La Bella Patria)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_CONTAINS {HEART_TYPE=4, MIN=1}
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=2"}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER

**Planned Board:**
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q132
**Question:** 『
{{live_success.png|ライブ成功時}}
自分のステージにいる『Aqours』のメンバーが持つハートに、
{{heart_05.png|heart05}}
が合計4個以上あり、このターン、相手が余剰のハートを持たずにライブを成功させていた場合、このカードのスコアを＋２する。』について。
自分が先行の場合、この能力が発動しますか？

**Answer:** はい、発動します。
{{live_success.png|ライブ成功時}}
能力の効果はライブ勝敗判定フェイズで発動するため、条件を満たせばする加算することができます。

**Related Cards:**
- PL!S-pb1-021-L (Strawberry Trapper)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=5"} {MIN=4}; SURPLUS_HEARTS_COUNT(OPPONENT) {EQ=0}
EFFECT: BOOST_SCORE(2) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q131
**Question:** 『
{{live_start.png|ライブ開始時}}
自分か相手を選ぶ。自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。』について。
相手が先行の場合、相手のライブ開始時に能力を使用できますか？

**Answer:** いいえ、発動できません。
{{live_start.png|ライブ開始時}}
能力の効果は自分のライブ開始時に発動します。

**Related Cards:**
- PL!S-pb1-008-R (小原鞠莉)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: CHOICE_PLAYER(BOTH) -> TARGET_PLAYER; LOOK_REORDER_DISCARD(2, TARGET=TARGET_PLAYER)
- PL!S-pb1-008-P＋ (小原鞠莉)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: CHOICE_PLAYER(BOTH) -> TARGET_PLAYER; LOOK_REORDER_DISCARD(2, TARGET=TARGET_PLAYER)

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q130
**Question:** 『
{{toujyou.png|登場}}
相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。』について。
この能力を使用したターンにライブを行いませんでした。、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」は次のターンも得ている状態ですか？

**Answer:** いいえ、ライブを行わない場合でもライブ勝敗判定フェイズの終了時に能力は消滅します。

**Related Cards:**
- PL!S-pb1-002-R (桜内梨子)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} -> OPPONENT
  OPTION: {{grant_ability.png|能力を得る}} | EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}
- PL!S-pb1-002-P＋ (桜内梨子)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: CHOICE_MODE -> OPPONENT
  OPTION: {{discard.png|控え室に置く}} | COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"} -> OPPONENT
  OPTION: {{grant_ability.png|能力を得る}} | EFFECT: GRANT_ABILITY(SELF) {ABILITY="TRIGGER: CONSTANT, EFFECT: BOOST_SCORE(1) -> PLAYER", DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.
- Check score calculation.

---

## Q129
**Question:** 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。』について。
手札が「[LL-bp2-001-R＋]渡辺 曜&鬼塚夏美&大沢瑠璃乃」を含めて5枚の時、「[LL-bp2-001-R＋]渡辺 曜&鬼塚夏美&大沢瑠璃乃」を公開した場合、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」は得ますか？

**Answer:** いいえ、得ません。
「[LL-bp2-001-R＋]渡辺 曜&鬼塚夏美&大沢瑠璃乃」の『
{{jyouji.png|常時}}
手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。』の能力によってコストが下がっているため、条件を満たさず「公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合」は満たしません。

**Related Cards:**
- PL!SP-bp1-003-R＋ (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-P (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-P＋ (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-SEC (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- LL-bp2-001-R＋ (渡辺 曜&鬼塚夏美&大沢瑠璃乃)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: COUNT_HAND(PLAYER) {FILTER="NOT_SELF"} -> COUNT_VAL; REDUCE_COST(COUNT_VAL)

TRIGGER: CONSTANT
EFFECT: PREVENT_BATON_TOUCH(SELF)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE) {FILTER="NAME_IN=['渡辺曜', '鬼塚夏美', '大沢瑠璃乃']"} -> DISCARD_COUNT
EFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); ADD_BLADES(1, PER_CARD=DISCARD_COUNT) -> SELF {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q128
**Question:** 『
{{live_success.png|ライブ成功時}}
自分の手札の枚数が相手より多い場合、このカードのスコアを＋１する。』について。
{{icon_draw.png|ドロー}}
によって手札の枚数が相手より多くなった場合、どうなりますか？

**Answer:** {{live_success.png|ライブ成功時}}
能力の効果はライブ勝敗判定フェイズで発動します。
そのため、ドローアイコンを解決したことで条件を満たし、
{{live_success.png|ライブ成功時}}
能力の効果を発動することができます。

**Related Cards:**
- PL!SP-bp2-024-L (ビタミンSUMMER！)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAND_SIZE {TARGET="PLAYER", GREATER_THAN="OPPONENT"}
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q126
**Question:** 『
{{jidou.png|自動}}
{{turn1.png|ターン1回}}
このメンバーがエリアを移動したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。』について。
この能力をもつカードがステージから控え室に移動したときも発動しますか？

**Answer:** いいえ、発動しません。
ステージに登場しているこの能力をもつメンバーが左サイドエリア、センターエリア、右サイドエリアのいずれかのエリアに移動した時に発動する自動能力です。

**Related Cards:**
- PL!SP-bp2-003-R (嵐 千砂都)
  - **Ability:** TRIGGER: ON_POSITION_CHANGE (Once per turn)

EFFECT: ENERGY_CHARGE(1, MODE="WAIT") -> PLAYER
- PL!SP-bp2-003-P (嵐 千砂都)
  - **Ability:** TRIGGER: ON_POSITION_CHANGE (Once per turn)

EFFECT: ENERGY_CHARGE(1, MODE="WAIT") -> PLAYER

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q125
**Question:** 『
{{jyouji.png|常時}}
このカードは成功ライブカード置き場に置くことができない。』について。
この能力をもつライブカードを成功ライブカード置き場と入れ替える効果などで成功ライブカード置き場に置くことができますか？

**Answer:** いいえ、できません。

**Related Cards:**
- PL!S-bp2-024-L (君のこころは輝いてるかい？)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE -> SELF

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!-sd1-006-SD (西木野 真姫)
  - **Ability:** TRIGGER: ON_PLAY
COST: SELECT_REVEAL_HAND(1, Optional) {FILTER="TYPE=LIVE"} -> SUCCESS, TARGET_REVEALED
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_SUCCESS_PILE(1, PLAYER) -> TARGET_SUCCESS; MOVE_TO_HAND(TARGET_SUCCESS); MOVE_TO_SUCCESS_PILE(TARGET_REVEALED)

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q124
**Question:** 『
{{toujyou.png|登場}}
手札を1枚控え室に置いてもよい：自分のデッキの上からカードを7枚見る。その中から
{{heart_02.png|heart02}}
か
{{heart_04.png|heart04}}
か
{{heart_05.png|heart05}}
を持つメンバーカードを3枚まで公開して手札に加えてもよい。残りを控え室に置く。』について。
この能力で
{{blade_heart02.png|ハート}}
か
{{blade_heart04.png|ハート}}
か
{{blade_heart05.png|ハート}}
を参照してメンバーカードを手札に加えられますか？

**Answer:** いいえ、加えられません。
基本ハートに
{{heart_02.png|heart02}}
か
{{heart_04.png|heart04}}
か
{{heart_05.png|heart05}}
をもつメンバーカードを手札に加えられます。
{{blade_heart02.png|ハート}}
と[]緑ブレードハートと
{{blade_heart05.png|ハート}}
は参照しません。

**Related Cards:**
- PL!S-bp2-005-R＋ (渡辺 曜)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE_REVEAL(7, choose_count=3) {COLOR_FILTER="RED/GREEN/BLUE", TYPE_MEMBER, TARGET=HAND, SOURCE=DECK, REMAINDER="DISCARD"}
- PL!S-bp2-005-P (渡辺 曜)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE_REVEAL(7, choose_count=3) {COLOR_FILTER="RED/GREEN/BLUE", TYPE_MEMBER, TARGET=HAND, SOURCE=DECK, REMAINDER="DISCARD"}
- PL!S-bp2-005-SEC (渡辺 曜)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE_REVEAL(7, choose_count=3) {COLOR_FILTER="RED/GREEN/BLUE", TYPE_MEMBER, TARGET=HAND, SOURCE=DECK, REMAINDER="DISCARD"}

**Planned Board:**
- Member in hand ready to play.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q123
**Question:** 『
{{kidou.png|起動}}
このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。』について。
控え室にライブカードがない状態で、この能力は使用できますか？

**Answer:** はい、使用できます。
ライブカードが控え室に1枚以上ある場合は必ず手札に加える必要があります。

**Related Cards:**
- PL!SP-bp1-011-R (鬼塚冬毬)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!SP-bp1-011-P (鬼塚冬毬)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-sd1-011-SD (ミア・テイラー)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!SP-sd1-006-SD (桜小路きな子)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!SP-pb1-018-N (米女メイ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-bp2-009-R (黒澤ルビィ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-bp2-009-P (黒澤ルビィ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-pb1-004-R (黒澤ダイヤ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-pb1-004-P＋ (黒澤ダイヤ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-PR-026-PR (桜内梨子)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!-sd1-005-SD (星空 凛)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-PR-012-PR (三船栞子)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-PR-009-PR (優木せつ菜)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-PR-014-PR (鐘 嵐珠)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q122
**Question:** 『
{{toujyou.png|登場}}
自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。』について。
自分のメインデッキが3枚の時にこの能力を使用してデッキの上から3枚見ているとき、リフレッシュは行いますか？

**Answer:** いいえ、リフレッシュは行いません。
デッキのカードのすべて見ていますが、それらはデッキから移動していないため、リフレッシュは行いません。
見たカード全てを控え室に置いた場合、リフレッシュを行います。

**Related Cards:**
- PL!N-bp1-002-R＋ (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q121
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のライブカード置き場に「MY舞☆TONIGHT」以外の『Aqours』のライブカードがある場合、ライブ終了時まで、自分のステージのメンバーは
{{icon_blade.png|ブレード}}
を得る。』について。
{{icon_blade.png|ブレード}}
を得るのは自分のステージのメンバーいずれか1人だけですか？

**Answer:** いいえ、自分のステージのメンバー全員が
{{icon_blade.png|ブレード}}
を得ます。

**Related Cards:**
- PL!S-bp2-023-L (MY舞☆TONIGHT)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: COUNT_LIVE_ZONE(PLAYER) {FILTER="UNIT_AQOURS, NOT_NAME='MY舞☆TONIGHT'", MIN=1}
EFFECT: SELECT_MEMBER(ALL) -> TARGETS; ADD_BLADES(1) -> TARGETS {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q119
**Question:** 『
{{live_success.png|ライブ成功時}}
自分の手札の枚数が相手より多い場合、このカードのスコアを＋１する。』について。
この能力を使用して効果を解決したあと、手札の枚数が増減しました。この能力を持つカードのスコアも増減しますか？

**Answer:** いいえ、増減しません。
この能力を使用して効果を解決する時点の手札の枚数を参照して、「このカードのスコアを＋１する」の効果が有効になるかどうかが決まります。この能力の効果を解決したあとに手札の枚数が増減したとしても、「このカードのスコアを＋１する」の効果が、有効から無効、または、無効から有効にはなりません。

**Related Cards:**
- PL!SP-bp2-024-L (ビタミンSUMMER！)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAND_SIZE {TARGET="PLAYER", GREATER_THAN="OPPONENT"}
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q118
**Question:** 『
{{toujyou.png|登場}}
自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。』について。
ライブカードを1枚しか選べなかった場合、相手はその1枚を選んで、そのカードを自分の手札に加えることはできますか？

**Answer:** いいえ、できません。
カード名の異なるライブカードを2枚選ばなかった場合、「そうした場合」を満たさないため、「相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。」の効果は解決しません。

**Related Cards:**
- PL!SP-bp2-011-R (鬼塚冬毬)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(2) {FROM="DISCARD", TYPE_LIVE, UNIQUE_NAMES} -> OPTIONS; OPPONENT_CHOOSE(OPTIONS) -> TARGET; ADD_TO_HAND(TARGET)
- PL!SP-bp2-011-P (鬼塚冬毬)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(2) {FROM="DISCARD", TYPE_LIVE, UNIQUE_NAMES} -> OPTIONS; OPPONENT_CHOOSE(OPTIONS) -> TARGET; ADD_TO_HAND(TARGET)

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q116
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいるメンバーが持つブレードの合計が10以上の場合、このカードのスコアを＋１する。』について。
ブレードの合計が10以上で、エールによって公開される自分のカードの枚数が減る効果が有効なため、公開される枚数が9枚以下になる場合であっても、このカードのスコアを＋１することはできますか？

**Answer:** はい、このカードのスコアを＋１します。

**Related Cards:**
- PL!N-sd1-028-SD (Dream with You)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: TOTAL_BLADES {MIN=10, AREA="STAGE"}
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q114
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージに「徒町小鈴」が登場しており、かつ「徒町小鈴」よりコストの大きい「村野さやか」が登場している場合、このカードを成功させるための必要ハートを
{{heart_00.png|heart0}}
{{heart_00.png|heart0}}
{{heart_00.png|heart0}}
減らす。』について。
「徒町小鈴」と「村野さやか」はこの能力を使うターンに登場して、自分のステージにいる必要がありますか？

**Answer:** いいえ、この能力を使うときに自分のステージにいる必要はありますが、この能力を使うターンに登場している必要はありません。

**Related Cards:**
- PL!HS-bp2-024-L (レディバグ)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER(PLAYER) {NAME="徒町小鈴"} -> KOSUZU; HAS_MEMBER(PLAYER) {NAME="村野さやか"} -> SAYAKA; VALUE_GT(GET_COST(SAYAKA), GET_COST(KOSUZU))
EFFECT: REDUCE_HEART_REQ(3, HEART_TYPE=ANY) -> SELF

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q113
**Question:** 『
{{jidou.png|自動}}
{{turn1.png|ターン1回}}
エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、
{{heart_06.png|heart06}}
を得る。』などについて。
ブレードがないなど何らかの理由でエールを行わなかった場合、この能力は発動しますか？

**Answer:** いいえ、発動しません。

**Related Cards:**
- PL!SP-bp2-015-N (平安名すみれ)
  - **Ability:** TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}
- PL!SP-bp2-020-N (鬼塚夏美)
  - **Ability:** TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}
- PL!SP-bp2-021-N (ウィーン・マルガレーテ)
  - **Ability:** TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q112
**Question:** 『
{{jidou.png|自動}}
{{turn1.png|ターン1回}}
エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、
{{heart_06.png|heart06}}
を得る。』などについて。
{{icon_b_all.png|ALLブレード}}
、
{{icon_score.png|スコア}}
、
{{icon_draw.png|ドロー}}
はブレードハートに含まれますか？

**Answer:** はい、含まれます。

**Related Cards:**
- PL!SP-bp2-015-N (平安名すみれ)
  - **Ability:** TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}
- PL!SP-bp2-020-N (鬼塚夏美)
  - **Ability:** TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}
- PL!SP-bp2-021-N (ウィーン・マルガレーテ)
  - **Ability:** TRIGGER: ON_YELL_REVEAL
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="HAS_BLADE_HEART", EQ=0}
EFFECT: ADD_HEARTS(1) -> SELF {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q109
**Question:** 『
{{live_start.png|ライブ開始時}}
ライブ終了時まで、自分の手札2枚につき、
{{icon_blade.png|ブレード}}
を得る。』について。
この能力を使用して効果を解決したあと、手札の枚数が増減しました。この効果で得た
{{icon_blade.png|ブレード}}
の数も増減しますか？

**Answer:** いいえ、増減しません。
この能力を使用して効果を解決する時点の手札の枚数を参照して、得られる
{{icon_blade.png|ブレード}}
の数は決まります。
この効果を解決したあとに手札の枚数が増減したとしても、この効果で得た
{{icon_blade.png|ブレード}}
の数は増減しません。

**Related Cards:**
- PL!SP-bp2-009-R＋ (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!SP-bp2-009-P (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!SP-bp2-009-P＋ (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!SP-bp2-009-SEC (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q108
**Question:** 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの
{{toujyou.png|登場}}
能力1つを発動させる。(
{{toujyou.png|登場}}
能力がコストを持つ場合、支払って発動させる。)』について。
この
{{kidou.png|起動}}
能力の効果で発動する
{{toujyou.png|登場}}
能力は、この
{{kidou.png|起動}}
能力を使ったカードが持っている能力として扱いますか？

**Answer:** いいえ、控え室に置いたメンバーカードが持つ
{{toujyou.png|登場}}
能力として扱います。
（例）「[PL!SP-pb1-009]鬼塚夏美」の『
{{toujyou.png|登場}}
自分のステージにほかの『5yncri5e!』のメンバーがいる場合、カードを1枚引く。』を発動した場合、この能力を持つ「鬼塚夏美」のほかに自分のステージに『5yncri5e!』のメンバーがいる場合、カードを引きます。
（例）「[PL!SP-bp1-002]唐 可可」の『
{{toujyou.png|登場}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。』を発動した場合、この能力を持つ「唐 可可」が左サイドエリアに登場していないため、カードは引きません。

**Related Cards:**
- PL!SP-bp2-006-R＋ (桜小路きな子)
  - **Ability:** TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER)
EFFECT: SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND

TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) {FILTER="GROUP_ID=3, COST_LE=4"} -> DISCARDED
EFFECT: TRIGGER_REMOTE(DISCARDED, TRIGGER="ON_PLAY")
- PL!SP-bp2-006-P (桜小路きな子)
  - **Ability:** TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER)
EFFECT: SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND

TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) {FILTER="GROUP_ID=3, COST_LE=4"} -> DISCARDED
EFFECT: TRIGGER_REMOTE(DISCARDED, TRIGGER="ON_PLAY")
- PL!SP-bp2-006-P＋ (桜小路きな子)
  - **Ability:** TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER)
EFFECT: SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND

TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) {FILTER="GROUP_ID=3, COST_LE=4"} -> DISCARDED
EFFECT: TRIGGER_REMOTE(DISCARDED, TRIGGER="ON_PLAY")
- PL!SP-bp2-006-SEC (桜小路きな子)
  - **Ability:** TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH(PLAYER)
EFFECT: SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND

TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) {FILTER="GROUP_ID=3, COST_LE=4"} -> DISCARDED
EFFECT: TRIGGER_REMOTE(DISCARDED, TRIGGER="ON_PLAY")

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q107
**Question:** 『
{{jidou.png|自動}}
{{turn1.png|ターン1回}}
エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。』
『
{{live_success.png|ライブ成功時}}
エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを＋１する。』について。
1つ目の能力で、もう一度エールを行いました。2つ目の能力で、1回目のエールにより公開された自分のカードと2回目のエールにより公開された自分のカードの両方を参照しますか？

**Answer:** いいえ、2つ目の能力を使用する時点で公開されている、2回目のエールにより公開された自分のカードのみ参照します。

**Related Cards:**
- PL!S-bp2-004-R (黒澤ダイヤ)
  - **Ability:** TRIGGER: NONE
EFFECT: META_RULE(1) {RULE=10}
- PL!S-bp2-004-P (黒澤ダイヤ)
  - **Ability:** TRIGGER: NONE
EFFECT: META_RULE(1) {RULE=10}
- PL!HS-bp1-022-L (AWOKE)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="UNIT_HASUNOSORA, TYPE_MEMBER", GE=10}
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q106
**Question:** 『
{{toujyou.png|登場}}
自分のステージにいる『Liella!』のメンバー1人のすべての
{{live_start.png|ライブ開始時}}
能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。』について。
すべての
{{live_start.png|ライブ開始時}}
能力が無効になっているメンバーを選んで、もう一度無効にすることで、自分の控え室から『Liella!』のカードを1枚手札に加えることはできますか？

**Answer:** いいえ、できません。
無効である能力がさらに無効にはならないため、「無効にした場合」の条件を満たしていません。

**Related Cards:**
- PL!SP-bp2-001-R＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
- PL!SP-bp2-001-P (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
- PL!SP-bp2-001-P＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND
- PL!SP-bp2-001-SEC (澁谷かのん)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} (Optional) -> TARGET; NEGATE_EFFECT(TARGET, TRIGGER="ON_LIVE_START") -> SUCCESS; CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_RECOVER_MEMBER(1) {ZONE="DISCARD", FILTER="GROUP_ID=3"} -> CARD_HAND

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q105
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを＋２する。』について。
ステージに「[LL-bp2-001]渡辺 曜&鬼塚夏美&大沢瑠璃乃」など複数の名前を持つカードがある場合、どのように参照されますか？

**Answer:** 例えば、『蓮ノ空』のメンバーのうち「大沢瑠璃乃」の名前を持つカードのように参照されます。

**Related Cards:**
- PL!SP-bp1-026-L (未来予報ハレルヤ！)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: COUNT_GROUP(5) {GROUP="Liella!", ZONE="STAGE,DISCARD", UNIQUE_NAMES}
EFFECT: SET_HEART_COST {RED=2, YELLOW=2, PURPLE=2}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q102
**Question:** 『
{{toujyou.png|登場}}
手札を1枚控え室に置いてもよい：ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。』について。
メインデッキにも控え室にもライブカードがない状態で、この能力を使った場合、どうなりますか？

**Answer:** 効果や処理は実行可能な限り解決し、一部でも実行可能な場合はその一部を解決します。まったく解決できない場合は何も行いません。
この場合、メインデッキのカードをすべて公開してリフレッシュを行い、さらに新しいメインデッキのカードをすべて公開した時点で『ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。』の解決を終了します。
続いて『そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。』を解決します。手札に加えるライブカードはなく、公開したカードを控え室に置き、リフレッシュを行います。

**Related Cards:**
- PL!N-bp1-011-R (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); REVEAL_UNTIL(FILTER="TYPE=LIVE") -> TARGET; MOVE_TO_HAND(TARGET); MOVE_TO_DISCARD(REMAINDER)
- PL!N-bp1-011-P (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); REVEAL_UNTIL(FILTER="TYPE=LIVE") -> TARGET; MOVE_TO_HAND(TARGET); MOVE_TO_DISCARD(REMAINDER)

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q99
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを
{{heart_00.png|heart0}}
減らす。』について。
この自動能力の効果を解決する時点で、ステージにいる「このターンに登場、かつエリアを移動した『5yncri5e!』のメンバー」は2人分として数えますか？

**Answer:** いいえ、2人分としては数えず、1人分として数えます。

**Related Cards:**
- PL!SP-pb1-025-L (Jellyfish)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_MEMBER(PLAYER) {FILTER="UNIT_SYNCRISE, STATUS=ENTERED_OR_MOVED_THIS_TURN"} -> COUNT_VAL; REDUCE_HEART_COST(COUNT_VAL) -> SELF

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q98
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを
{{heart_00.png|heart0}}
減らす。』について。
この自動能力の効果を解決する時点で、ステージにいない「このターンに登場、またはエリアを移動した『5yncri5e!』のメンバー」は1人分として数えますか？

**Answer:** いいえ、数えません。

**Related Cards:**
- PL!SP-pb1-025-L (Jellyfish)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_MEMBER(PLAYER) {FILTER="UNIT_SYNCRISE, STATUS=ENTERED_OR_MOVED_THIS_TURN"} -> COUNT_VAL; REDUCE_HEART_COST(COUNT_VAL) -> SELF

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q95
**Question:** 『
{{toujyou.png|登場}}
「鬼塚冬毬」以外の『Liella!』のメンバー1人をステージから控え室に置いてもよい：自分の控え室から、これにより控え室に置いたメンバーカードを1枚、そのメンバーがいたエリアに登場させる。』について。
この能力のコストで控え室に置いたメンバーカードと同じカード名を持つ、控え室に置いたメンバーカード以外のメンバーカードを登場させることはできますか？

**Answer:** いいえ、できません。
この能力の効果で登場させることができるのは、この能力のコストで控え室に置いたメンバーカードのみです。
なお、登場させるメンバーカードは新しいカードとして扱うため、ステージにいた時に適用されていた効果などは適用されていない状態で登場します。

**Related Cards:**
- PL!SP-pb1-011-R (鬼塚冬毬)
  - **Ability:** TRIGGER: ON_PLAY
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_NAME='鬼塚冬毬'"} (Optional) -> TARGET; MOVE_TO_DISCARD(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}
- PL!SP-pb1-011-P＋ (鬼塚冬毬)
  - **Ability:** TRIGGER: ON_PLAY
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_NAME='鬼塚冬毬'"} (Optional) -> TARGET; MOVE_TO_DISCARD(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q94
**Question:** 『
{{jidou.png|自動}}
このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、ブレードブレードを得る。』について。
例えば、このメンバーカードが登場して、その後、このメンバーカードが別のエリアに移動した場合、この自動能力は合わせて2回発動しますか？

**Answer:** はい、登場した時と移動した時の合わせて2回発動します。

**Related Cards:**
- PL!SP-pb1-006-R (桜小路きな子)
  - **Ability:** TRIGGER: ON_POSITION_CHANGE(SELF), ON_PLAY(SELF)
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-pb1-006-P＋ (桜小路きな子)
  - **Ability:** TRIGGER: ON_POSITION_CHANGE(SELF), ON_PLAY(SELF)
EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q93
**Question:** 『
{{live_start.png|ライブ開始時}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
支払わないかぎり、自分の手札を2枚控え室に置く。』について。
{{icon_energy.png|E}}
{{icon_energy.png|E}}
を支払わず、自分の手札が1枚以下の場合、どうなりますか？

**Answer:** 効果や処理は実行可能な限り解決し、一部でも実行可能な場合はその一部を解決します。まったく解決できない場合は何も行いません。
手札が1枚の場合、その1枚を控え室に置きます。手札が0枚の場合、特に何も行いません。

**Related Cards:**
- PL!SP-pb1-001-R (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF
- PL!SP-pb1-001-P＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q92
**Question:** 『
{{live_start.png|ライブ開始時}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
支払わないかぎり、自分の手札を2枚控え室に置く。』について。
アクティブ状態のエネルギーが1枚以下の場合、
{{icon_energy.png|E}}
{{icon_energy.png|E}}
を支払うことはできますか？また、アクティブ状態のエネルギーが2枚以上の場合、
{{icon_energy.png|E}}
{{icon_energy.png|E}}
を支払わないことはできますか？

**Answer:** コストはすべて支払う必要があります。アクティブ状態のエネルギーが1枚以下の場合、
{{icon_energy.png|E}}
{{icon_energy.png|E}}
を支払うことはできません。1枚だけ支払うということもできません。
コストを支払うかどうかは選択できます。
{{icon_energy.png|E}}
{{icon_energy.png|E}}
を支払える状況であったとしても、支払わないことを選択できます。
コストを支払わなかった場合、「自分の手札を2枚控え室に置く。」の効果を解決します。

**Related Cards:**
- PL!SP-pb1-001-R (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF
- PL!SP-pb1-001-P＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q91
**Question:** 『
{{live_start.png|ライブ開始時}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
支払わないかぎり、自分の手札を2枚控え室に置く。』について。
ライブを行わない場合、この自動能力は発動しないですか？

**Answer:** はい、発動しません。

**Related Cards:**
- PL!SP-pb1-001-R (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF
- PL!SP-pb1-001-P＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q89
**Question:** このカードはグループ名やユニット名を持っていますか？

**Answer:** カードに記載されているグループ名は持っていますが、カードに記載されていないユニット名は持っていません。

**Related Cards:**
- LL-bp1-001-R＋ (上原歩夢&澁谷かのん&日野下花帆)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(3) {FILTER="Ayumu/Kanon/Kaho"} (Optional)
EFFECT: BOOST_SCORE(3) -> SELF
- LL-bp2-001-R＋ (渡辺 曜&鬼塚夏美&大沢瑠璃乃)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: COUNT_HAND(PLAYER) {FILTER="NOT_SELF"} -> COUNT_VAL; REDUCE_COST(COUNT_VAL)

TRIGGER: CONSTANT
EFFECT: PREVENT_BATON_TOUCH(SELF)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(VARIABLE) {FILTER="NAME_IN=['渡辺曜', '鬼塚夏美', '大沢瑠璃乃']"} -> DISCARD_COUNT
EFFECT: CONDITION: VALUE_GT(DISCARD_COUNT, 0); ADD_BLADES(1, PER_CARD=DISCARD_COUNT) -> SELF {DURATION="UNTIL_LIVE_END"}
- LL-bp3-001-R＋ (園田海未&津島善子&天王寺璃奈)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DECK(6) {FILTER="Umi/Yoshiko/Rina", FROM="DISCARD"}
EFFECT: ACTIVATE_ENERGY(6) -> PLAYER

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(6)
EFFECT: ADD_BLADES(3) -> PLAYER

**Planned Board:**
- Setup board according to question context.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q82
**Question:** 『
{{toujyou.png|登場}}
手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『みらくらぱーく！』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。』について。
この能力の効果でライブカードの「[PL!HS-bp1-023]ド！ド！ド！」や「[PL!HS-PR-012]アイデンティティ」を手札に加えることはできますか？

**Answer:** はい、できます。
「[PL!HS-bp1-023]ド！ド！ド！」や「[PL!HS-PR-012]アイデンティティ」は『みらくらぱーく！』のカードのため、この能力の効果で手札に加えることができます。

**Related Cards:**
- PL!HS-bp1-009-R (安養寺 姫芽)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_MIRAKURA"} -> CARD_HAND, DISCARD_REMAINDER
- PL!HS-bp1-009-P (安養寺 姫芽)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_MIRAKURA"} -> CARD_HAND, DISCARD_REMAINDER

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q81
**Question:** 『
{{jyouji.png|常時}}
自分のステージのエリアすべてに「蓮ノ空」のメンバーが登場しており、かつ名前が異なる場合、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。』について。
ステージに「[LL-bp1-001]上原歩夢&澁谷かのん&日野下花帆」がある場合、どのように参照されますか？

**Answer:** 『蓮ノ空』のメンバーのうち「日野下花帆」の名前を持つカードとして参照されます。

**Related Cards:**
- PL!HS-bp1-003-R＋ (乙宗 梢)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_HASUNOSORA, UNIQUE_NAMES", EQ=3}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_HASUNOSORA, COST_LE=4"} -> CARD_HAND
- PL!HS-bp1-003-P (乙宗 梢)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_HASUNOSORA, UNIQUE_NAMES", EQ=3}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_HASUNOSORA, COST_LE=4"} -> CARD_HAND
- PL!HS-bp1-003-P＋ (乙宗 梢)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_HASUNOSORA, UNIQUE_NAMES", EQ=3}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_HASUNOSORA, COST_LE=4"} -> CARD_HAND
- PL!HS-bp1-003-SEC (乙宗 梢)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_HASUNOSORA, UNIQUE_NAMES", EQ=3}
EFFECT: BOOST_SCORE(1) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(1)
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_HASUNOSORA, COST_LE=4"} -> CARD_HAND

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.
- Check score calculation.

---

## Q80
**Question:** 『
{{kidou.png|起動}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
、このメンバーをステージから控え室に置く：自分の控え室からコスト15以下の「蓮ノ空」のメンバーカードを1枚、このメンバーがいたエリアに登場させる。』について。
このメンバーカードが登場したターンにこの能力を使用しても、このターンに登場したメンバーカードがエリアに置かれているため、効果でメンバーカードを登場させることはできないですか？

**Answer:** いいえ、効果でメンバーカードが登場します。
起動能力のコストでこのメンバーカードがステージから控え室に置かれることにより、このエリアにはこのターンに登場したメンバーカードが置かれていない状態になるため、そのエリアにメンバーカードを登場させることができます。

**Related Cards:**
- PL!HS-bp1-002-R (村野さやか)
  - **Ability:** TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); MOVE_TO_DISCARD(SELF) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_CARDS(1) {ZONE="DISCARD", FILTER="UNIT_HASUNOSORA, COST_LE=15"} -> TARGET; PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}
- PL!HS-bp1-002-P (村野さやか)
  - **Ability:** TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); MOVE_TO_DISCARD(SELF) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_CARDS(1) {ZONE="DISCARD", FILTER="UNIT_HASUNOSORA, COST_LE=15"} -> TARGET; PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q79
**Question:** 『
{{kidou.png|起動}}
このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。』などについて。
このメンバーカードが登場したターンにこの能力を使用しました。このターン中、このメンバーカードが置かれていたエリアにメンバーカードを登場させることはできますか？

**Answer:** はい、できます。
起動能力のコストでこのメンバーカードがステージから控え室に置かれることにより、このエリアにはこのターンに登場したメンバーカードが置かれていない状態になるため、そのエリアにメンバーカードを登場させることができます。

**Related Cards:**
- PL!SP-bp1-011-R (鬼塚冬毬)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!SP-bp1-011-P (鬼塚冬毬)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-sd1-011-SD (ミア・テイラー)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!SP-sd1-006-SD (桜小路きな子)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-sd1-006-SD (近江彼方)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!SP-pb1-018-N (米女メイ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!SP-pb1-021-N (ウィーン・マルガレーテ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!HS-PR-014-PR (日野下花帆)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!S-bp2-009-R (黒澤ルビィ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-bp2-009-P (黒澤ルビィ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-bp2-016-N (国木田花丸)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!S-pb1-004-R (黒澤ダイヤ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-pb1-004-P＋ (黒澤ダイヤ)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-PR-025-PR (高海千歌)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!S-PR-026-PR (桜内梨子)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-PR-027-PR (松浦果南)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!-sd1-002-SD (絢瀬 絵里)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!-sd1-005-SD (星空 凛)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!S-bp3-008-R (小原鞠莉)
  - **Ability:** TRIGGER: ACTIVATED
COST: SACRIFICE_SELF
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND -> CHOSEN_CARD
EFFECT: CONDITION: SELECT_CARD(CHOSEN_CARD) {FILTER="GROUP_ID=1, SCORE_GE=6"}; ACTIVATE_ENERGY(4)
- PL!S-bp3-008-P (小原鞠莉)
  - **Ability:** TRIGGER: ACTIVATED
COST: SACRIFICE_SELF
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND -> CHOSEN_CARD
EFFECT: CONDITION: SELECT_CARD(CHOSEN_CARD) {FILTER="GROUP_ID=1, SCORE_GE=6"}; ACTIVATE_ENERGY(4)
- PL!-pb1-019-N (高坂穂乃果)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!-pb1-024-N (西木野真姫)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!-pb1-025-N (東條 希)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND
- PL!N-PR-012-PR (三船栞子)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-PR-009-PR (優木せつ菜)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
- PL!N-PR-014-PR (鐘 嵐珠)
  - **Ability:** TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q78
**Question:** 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。」を得る。』について。
この能力を使用したあと、このメンバーカードがステージから離れました。『
{{jyouji.png|常時}}
ライブの合計スコアを＋１する。』の能力で合計スコアを＋１することはできますか？

**Answer:** いいえ、できません。
{{kidou.png|起動}}
能力の効果で
{{jyouji.png|常時}}
能力を得たこのメンバーカードがステージから離れることで、この
{{jyouji.png|常時}}
能力が無くなるため、合計スコアは＋１されません。

**Related Cards:**
- PL!SP-bp1-003-R＋ (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-P (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-P＋ (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!SP-bp1-003-SEC (嵐 千砂都)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: SELECT_CARDS(ANY, FROM="HAND") -> TARGETS; SUM_COST(TARGETS) -> TOTAL; CONDITION: IN_VAL(TOTAL, [10,20,30,40,50]); REVEAL_CARDS(TARGETS) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q77
**Question:** 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
手札を1枚控え室に置く：このターン、自分のステージに「虹ヶ咲」のメンバーが登場している場合、エネルギーを2枚アクティブにする。』について。
このターン中に登場したメンバーがこのカードだけの状況です。「自分のステージに「虹ヶ咲」のメンバーが登場している場合」の条件は満たしていますか？

**Answer:** はい、条件を満たしています。

**Related Cards:**
- PL!N-bp1-006-R＋ (近江彼方)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE), COUNT_PLAYED_THIS_TURN(PLAYER) {FILTER="UNIT_NIJIGASAKI", GE=1}; ACTIVATE_ENERGY(2)

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: DRAW(1)
- PL!N-bp1-006-P (近江彼方)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE), COUNT_PLAYED_THIS_TURN(PLAYER) {FILTER="UNIT_NIJIGASAKI", GE=1}; ACTIVATE_ENERGY(2)

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: DRAW(1)
- PL!N-bp1-006-P＋ (近江彼方)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE), COUNT_PLAYED_THIS_TURN(PLAYER) {FILTER="UNIT_NIJIGASAKI", GE=1}; ACTIVATE_ENERGY(2)

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: DRAW(1)
- PL!N-bp1-006-SEC (近江彼方)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE), COUNT_PLAYED_THIS_TURN(PLAYER) {FILTER="UNIT_NIJIGASAKI", GE=1}; ACTIVATE_ENERGY(2)

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(2)
EFFECT: DRAW(1)

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q76
**Question:** 『
{{kidou.png|起動}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。』について。
メンバーカードがあるエリアに登場させることはできますか？

**Answer:** はい、できます。
その場合、指定したエリアに置かれているメンバーカードは控え室に置かれます。
ただし、このターンに登場しているメンバーのいるエリアを指定することはできません。

**Related Cards:**
- PL!N-bp1-002-R＋ (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-P (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-P＋ (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-SEC (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q75
**Question:** 『
{{kidou.png|起動}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。』について。
この能力で登場したメンバーを対象にこのターン手札のメンバーとバトンタッチはできますか？

**Answer:** いいえ、できません。登場したターン中はバトンタッチはできません。登場した次のターン以降はバトンタッチができます。

**Related Cards:**
- PL!N-bp1-002-R＋ (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-P (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-P＋ (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-SEC (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)

**Planned Board:**
- Member in hand ready to play.
- Member(s) on stage to baton touch.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.
- Perform baton touch and verify outcome.

---

## Q74
**Question:** 『
{{live_start.png|ライブ開始時}}
自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するための必要ハートは
{{heart_02.png|heart02}}
{{heart_02.png|heart02}}
{{heart_03.png|heart03}}
{{heart_03.png|heart03}}
{{heart_06.png|heart06}}
{{heart_06.png|heart06}}
になる。』について。
ステージまたは控え室に「[LL-bp1-001]上原歩夢&澁谷かのん&日野下花帆」など複数の名前を持つカードがある場合、どのように参照されますか？

**Answer:** 例えば、『Liella!』のメンバーのうち「澁谷かのん」の名前を持つカードとして参照されます。

**Related Cards:**
- PL!SP-bp1-026-L (未来予報ハレルヤ！)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: COUNT_GROUP(5) {GROUP="Liella!", ZONE="STAGE,DISCARD", UNIQUE_NAMES}
EFFECT: SET_HEART_COST {RED=2, YELLOW=2, PURPLE=2}

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q73
**Question:** 『
{{toujyou.png|登場}}
手札を1枚控え室に置いてもよい：ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。』について。
この能力の効果の解決中に、メインデッキのカードが無くなりました。「リフレッシュ」の処理はどうなりますか？

**Answer:** 能力に効果によって公開しているカードを含めずに「リフレッシュ」をして控え室のカードを新たなメインデッキにします。その後、効果の解決を再開します。

**Related Cards:**
- PL!N-bp1-011-R (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); REVEAL_UNTIL(FILTER="TYPE=LIVE") -> TARGET; MOVE_TO_HAND(TARGET); MOVE_TO_DISCARD(REMAINDER)
- PL!N-bp1-011-P (ミア・テイラー)
  - **Ability:** TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); REVEAL_UNTIL(FILTER="TYPE=LIVE") -> TARGET; MOVE_TO_HAND(TARGET); MOVE_TO_DISCARD(REMAINDER)

**Planned Board:**
- Live card(s) set up.
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Play member and check effects.

---

## Q68
**Question:** 『自分はライブできない』とはどのような状態ですか？

**Answer:** 『ライブできない』状態のプレイヤーは、ライブカードセットフェイズでライブカード置き場に手札のカードを裏向きで置くことはできますが、パフォーマンスフェイズで表向きにしたカードの中にライブカードがあったとしても、そのライブカードを含めて控え室に置きます。
その結果、ライブカード置き場にライブカードが置かれていないため、ライブは行われません。（
{{live_start.png|ライブ開始時}}
の能力は使えず、エールも行いません）

**Related Cards:**
- PL!SP-bp1-001-R (澁谷かのん)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {MAX=0, TARGET="OTHER_MEMBER"}
EFFECT: PREVENT_LIVE -> PLAYER
- PL!SP-bp1-001-P (澁谷かのん)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {MAX=0, TARGET="OTHER_MEMBER"}
EFFECT: PREVENT_LIVE -> PLAYER
- PL!HS-bp2-014-N (大沢瑠璃乃)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: DRAW(1); RESTRICTION(LIVE, DURATION="UNTIL_LIVE_END")

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q67
**Question:** 『
{{live_start.png|ライブ開始時}}
自分のステージにいる『虹ヶ咲』のメンバーが持つ
{{heart_01.png|heart01}}
、
{{heart_04.png|heart04}}
、
{{heart_05.png|heart05}}
、
{{heart_02.png|heart02}}
、
{{heart_03.png|heart03}}
、
{{heart_06.png|heart06}}
のうち1色につき、このカードのスコアを＋１する。』について。
この能力の効果で
{{icon_all.png|ハート}}
は任意の色として扱うことができますか？

**Answer:** いいえ、扱えません。
{{icon_all.png|ハート}}
はライブの必要ハートの確認を行う時に任意の色として扱いますが、ライブ開始時には任意の色として扱いません。

**Related Cards:**
- PL!N-bp1-027-L (Solitude Rain)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HEART_COLORS(PLAYER) {FILTER="UNIT_NIJIGASAKI"} -> COUNT_VAL; BOOST_SCORE(1, PER_CARD=COUNT_VAL) -> SELF

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q66
**Question:** 『ライブの合計スコアが相手より高い場合』について。
自分のライブカード置き場にライブカードがあり、相手のライブカード置き場にライブカードがない場合、この条件は満たしますか？

**Answer:** はい、満たします。自分のライブカード置き場にライブカードがあり、相手のライブカード置き場にライブカードがない場合、自分のライブの合計スコアがいくつであっても、相手より合計スコアが高いものとして扱います。

**Related Cards:**
- PL!N-bp1-026-L (Poppin' Up!)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER)
EFFECT: SELECT_CARDS(1) {ZONE="YELL_REVEALED", FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND
- PL!SP-bp1-023-L (START!! True dreams)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER)
EFFECT: ENERGY_CHARGE(1)

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q64
**Question:** 『
{{live_start.png|ライブ開始時}}
自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するための必要ハートは
{{heart_02.png|heart02}}
{{heart_02.png|heart02}}
{{heart_03.png|heart03}}
{{heart_03.png|heart03}}
{{heart_06.png|heart06}}
{{heart_06.png|heart06}}
になる。』について。
控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、ステージにいなくても条件を満たしていますか？

**Answer:** はい、条件を満たしています。

**Related Cards:**
- PL!SP-bp1-026-L (未来予報ハレルヤ！)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: COUNT_GROUP(5) {GROUP="Liella!", ZONE="STAGE,DISCARD", UNIQUE_NAMES}
EFFECT: SET_HEART_COST {RED=2, YELLOW=2, PURPLE=2}

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q63
**Question:** 能力の効果でメンバーカードをステージに登場させる場合、能力のコストとは別に、手札から登場させる場合と同様にメンバーカードのコストを支払いますか？

**Answer:** いいえ、支払いません。効果で登場する場合、メンバーカードのコストは支払いません。

**Related Cards:**
- PL!N-bp1-002-R＋ (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-P (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-P＋ (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!N-bp1-002-SEC (中須かすみ)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)

TRIGGER: ACTIVATED (In Discard)
COST: PAY_ENERGY(2); DISCARD_HAND(1) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(SELF)
- PL!HS-bp1-002-R (村野さやか)
  - **Ability:** TRIGGER: ACTIVATED
COST: PAY_ENERGY(2); MOVE_TO_DISCARD(SELF) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); SELECT_CARDS(1) {ZONE="DISCARD", FILTER="UNIT_HASUNOSORA, COST_LE=15"} -> TARGET; PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}
- PL!SP-sd1-002-SD (唐 可可)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) {FROM="HAND", FILTER="GROUP_ID=3, COST_LE=4"} (Optional) -> TARGET; PLAY_MEMBER(TARGET)
- PL!SP-pb1-011-R (鬼塚冬毬)
  - **Ability:** TRIGGER: ON_PLAY
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_NAME='鬼塚冬毬'"} (Optional) -> TARGET; MOVE_TO_DISCARD(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}
- PL!SP-pb1-011-P＋ (鬼塚冬毬)
  - **Ability:** TRIGGER: ON_PLAY
COST: SELECT_MEMBER(1) {FILTER="GROUP_ID=3, NOT_NAME='鬼塚冬毬'"} (Optional) -> TARGET; MOVE_TO_DISCARD(TARGET) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); PLAY_MEMBER(TARGET) {REPRO_AREA=TRUE}

**Planned Board:**
- Member in hand ready to play.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Play member and check effects.

---

## Q38
**Question:** 「ライブ中のカード」とはどのようなカードですか？

**Answer:** ライブカード置き場に表向きに置かれているライブカードです。

**Related Cards:**
- PL!N-bp1-012-R＋ (鐘 嵐珠)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER) {GE=3}, COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER, FILTER="UNIT_NIJIGASAKI") {GE=1}
EFFECT: ADD_HEARTS(2) -> SELF; ADD_BLADES(2) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
- PL!N-bp1-012-P (鐘 嵐珠)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER) {GE=3}, COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER, FILTER="UNIT_NIJIGASAKI") {GE=1}
EFFECT: ADD_HEARTS(2) -> SELF; ADD_BLADES(2) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
- PL!N-bp1-012-P＋ (鐘 嵐珠)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER) {GE=3}, COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER, FILTER="UNIT_NIJIGASAKI") {GE=1}
EFFECT: ADD_HEARTS(2) -> SELF; ADD_BLADES(2) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
- PL!N-bp1-012-SEC (鐘 嵐珠)
  - **Ability:** TRIGGER: CONSTANT
CONDITION: COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER) {GE=3}, COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER, FILTER="UNIT_NIJIGASAKI") {GE=1}
EFFECT: ADD_HEARTS(2) -> SELF; ADD_BLADES(2) -> SELF

TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND
- PL!N-bp1-029-L (Eutopia)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: COUNT_CARDS(ZONE="LIVE_SLOTS", PLAYER) {GE=3}
EFFECT: BOOST_SCORE(2) -> SELF
- PL!HS-bp1-004-R＋ (夕霧綴理)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_HASUNOSORA"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_CARDS(ZONE="LIVE_SLOTS") -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!HS-bp1-004-P (夕霧綴理)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_HASUNOSORA"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_CARDS(ZONE="LIVE_SLOTS") -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!HS-bp1-004-P＋ (夕霧綴理)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_HASUNOSORA"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_CARDS(ZONE="LIVE_SLOTS") -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}
- PL!HS-bp1-004-SEC (夕霧綴理)
  - **Ability:** TRIGGER: ACTIVATED (Once per turn)
COST: PAY_ENERGY(3)
EFFECT: SELECT_RECOVER_LIVE(1) {FILTER="UNIT_HASUNOSORA"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); COUNT_CARDS(ZONE="LIVE_SLOTS") -> COUNT_VAL; ADD_BLADES(1, PER_CARD=COUNT_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q36
**Question:** {{live_success.png|ライブ成功時}}
とはいつのことですか？

**Answer:** 両方のプレイヤーのパフォーマンスフェイズを行った後、ライブ勝敗判定フェイズで、ライブに勝利したプレイヤーを決定する前のタイミングです。

**Related Cards:**
- PL!N-bp1-026-L (Poppin' Up!)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER)
EFFECT: SELECT_CARDS(1) {ZONE="YELL_REVEALED", FILTER="UNIT_NIJIGASAKI"} -> CARD_HAND
- PL!SP-bp1-023-L (START!! True dreams)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER)
EFFECT: ENERGY_CHARGE(1)
- PL!SP-bp1-024-L (Tiny Stars)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {FILTER="NAME=澁谷かのん"} -> TARGET_1; ADD_HEARTS(1) -> TARGET_1 {HEART_TYPE=PINK, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_1 {DURATION="UNTIL_LIVE_END"}
EFFECT: SELECT_MEMBER(1) {FILTER="NAME=唐可可"} -> TARGET_2; ADD_HEARTS(1) -> TARGET_2 {HEART_TYPE=RED, DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_2 {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NAME=澁谷かのん", GE=1}, COUNT_MEMBER(PLAYER) {FILTER="NAME=唐可可", GE=1}
EFFECT: DRAW(1)
- PL!HS-bp1-021-L (Holiday∞Holiday)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_CARDS(1) {ZONE="YELL_REVEALED", FILTER="UNIT_HASUNOSORA, TYPE_LIVE"} -> CARD_HAND
- PL!HS-bp1-022-L (AWOKE)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="UNIT_HASUNOSORA, TYPE_MEMBER", GE=10}
EFFECT: BOOST_SCORE(1) -> SELF
- PL!HS-bp1-023-L (ド！ド！ド！)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_LEAD(PLAYER), COUNT_MEMBER(PLAYER) {FILTER="UNIT_HASUNOSORA", GE=1}
EFFECT: ENERGY_CHARGE(1)
- PL!SP-pb1-001-R (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF
- PL!SP-pb1-001-P＋ (澁谷かのん)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(2) {OPTION_1="PAY_ENERGY(2)", OPTION_2="DISCARD_HAND(2)"}

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(6) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); BOOST_SCORE(1) -> SELF
- PL!SP-pb1-004-R (平安名すみれ)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1)

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(3) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1)
- PL!SP-pb1-004-P＋ (平安名すみれ)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); ENERGY_CHARGE(1)

TRIGGER: ON_LIVE_SUCCESS
COST: PAY_ENERGY(3) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); DRAW(1)
- PL!S-bp2-008-R＋ (小原鞠莉)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) {FROM="DISCARD", TYPE_LIVE} -> TARGET; MOVE_TO_DECK(TARGET, TO="DECK_BOTTOM")

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_AQOURS, UNIQUE_NAMES", EQ=3}
EFFECT: COUNT_CARDS(ZONE="YELL_REVEALED", FILTER="TYPE_LIVE") -> LIVE_COUNT; CONDITION: VALUE_GE(LIVE_COUNT, 1); VALUE_GE(LIVE_COUNT, 3) -> IS_THREE; CONDITION: VALUE_EQ(IS_THREE, TRUE); BOOST_SCORE(2) -> SELF; ELSE; BOOST_SCORE(1) -> SELF
- PL!S-bp2-008-P (小原鞠莉)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) {FROM="DISCARD", TYPE_LIVE} -> TARGET; MOVE_TO_DECK(TARGET, TO="DECK_BOTTOM")

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_AQOURS, UNIQUE_NAMES", EQ=3}
EFFECT: COUNT_CARDS(ZONE="YELL_REVEALED", FILTER="TYPE_LIVE") -> LIVE_COUNT; CONDITION: VALUE_GE(LIVE_COUNT, 1); VALUE_GE(LIVE_COUNT, 3) -> IS_THREE; CONDITION: VALUE_EQ(IS_THREE, TRUE); BOOST_SCORE(2) -> SELF; ELSE; BOOST_SCORE(1) -> SELF
- PL!S-bp2-008-P＋ (小原鞠莉)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) {FROM="DISCARD", TYPE_LIVE} -> TARGET; MOVE_TO_DECK(TARGET, TO="DECK_BOTTOM")

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_AQOURS, UNIQUE_NAMES", EQ=3}
EFFECT: COUNT_CARDS(ZONE="YELL_REVEALED", FILTER="TYPE_LIVE") -> LIVE_COUNT; CONDITION: VALUE_GE(LIVE_COUNT, 1); VALUE_GE(LIVE_COUNT, 3) -> IS_THREE; CONDITION: VALUE_EQ(IS_THREE, TRUE); BOOST_SCORE(2) -> SELF; ELSE; BOOST_SCORE(1) -> SELF
- PL!S-bp2-008-SEC (小原鞠莉)
  - **Ability:** TRIGGER: ON_PLAY
EFFECT: SELECT_CARDS(1) {FROM="DISCARD", TYPE_LIVE} -> TARGET; MOVE_TO_DECK(TARGET, TO="DECK_BOTTOM")

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="UNIT_AQOURS, UNIQUE_NAMES", EQ=3}
EFFECT: COUNT_CARDS(ZONE="YELL_REVEALED", FILTER="TYPE_LIVE") -> LIVE_COUNT; CONDITION: VALUE_GE(LIVE_COUNT, 1); VALUE_GE(LIVE_COUNT, 3) -> IS_THREE; CONDITION: VALUE_EQ(IS_THREE, TRUE); BOOST_SCORE(2) -> SELF; ELSE; BOOST_SCORE(1) -> SELF
- PL!S-bp2-024-L (君のこころは輝いてるかい？)
  - **Ability:** TRIGGER: CONSTANT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE -> SELF

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!SP-bp2-009-R＋ (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!SP-bp2-009-P (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!SP-bp2-009-P＋ (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!SP-bp2-009-SEC (鬼塚夏美)
  - **Ability:** TRIGGER: ON_LIVE_START
EFFECT: COUNT_HAND(PLAYER) -> HAND_VAL; DIV_VALUE(HAND_VAL, 2) -> BLADE_VAL; ADD_BLADES(BLADE_VAL) -> SELF {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2); DISCARD_HAND(1)
- PL!S-pb1-003-R (松浦果南)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); TRANSFORM_HEART(SELF, FILTER="BASE") -> COLOR_GREEN {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND {ZONE="YELL_REVEALED"}
- PL!S-pb1-003-P＋ (松浦果南)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE); TRANSFORM_HEART(SELF, FILTER="BASE") -> COLOR_GREEN {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND {ZONE="YELL_REVEALED"}
- PL!S-pb1-007-R (国木田花丸)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="TYPE_LIVE", MIN=1}
EFFECT: ENERGY_CHARGE(1, STATUS="TAPPED")
- PL!S-pb1-007-P＋ (国木田花丸)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_YELL_REVEALED(PLAYER) {FILTER="TYPE_LIVE", MIN=1}
EFFECT: ENERGY_CHARGE(1, STATUS="TAPPED")
- PL!S-pb1-019-L (元気全開DAY！DAY！DAY！)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=1"} {MIN=6}
EFFECT: NEGATE_SELF_TRIGGER(ON_LIVE_SUCCESS, DURATION="UNTIL_LIVE_END")

TRIGGER: ON_LIVE_SUCCESS
EFFECT: ENERGY_CHARGE(1, STATUS="TAPPED") -> OPPONENT
- PL!S-pb1-021-L (Strawberry Trapper)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=5"} {MIN=4}; SURPLUS_HEARTS_COUNT(OPPONENT) {EQ=0}
EFFECT: BOOST_SCORE(2) -> SELF
- PL!S-pb1-022-L (逃走迷走メビウスループ)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}
- PL!S-pb1-022-L＋ (逃走迷走メビウスループ)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}
- PL!S-pb1-024-L (僕らの走ってきた道は・・・)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER
- PL!-sd1-019-SD (START:DASH!!)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
EFFECT: LOOK_AND_CHOOSE_ORDER(3, ANY) -> DECK_TOP; MOVE_TO_DISCARD(REMAINDER)
- PL!-bp3-025-L (タカラモノズ)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_COUNT {MAX=0}
EFFECT: BOOST_SCORE(1) -> SELF
- PL!-bp3-026-L (Oh,Love&Peace!)
  - **Ability:** TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2) (Optional)
EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(3) -> TARGET {DURATION="UNTIL_LIVE_END"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: HEARTS_COUNT(PLAYER) > HEARTS_COUNT(OPPONENT)
EFFECT: BOOST_SCORE(1) -> SELF
- PL!S-bp3-019-L (MIRACLE WAVE)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: OR(YELL_PILE_CONTAINS {FILTER="TYPE_NOT=BLADE_HEART", MAX=0}, SURPLUS_HEARTS_COUNT {MIN=2})
EFFECT: SET_SCORE(4) -> SELF
- PL!N-bp3-027-L (La Bella Patria)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: SURPLUS_HEARTS_CONTAINS {HEART_TYPE=4, MIN=1}
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=2"}
EFFECT: PLACE_ENERGY_WAIT(1) -> PLAYER
- PL!N-bp3-030-L (Love U my friends)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: YELL_PILE_CONTAINS {FILTER="HAS_ALL_BLADE"}
EFFECT: BOOST_SCORE(1) -> SELF
- PL!N-bp3-031-L (MONSTER GIRLS)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
EFFECT: BOOST_SCORE(1, PER_CARD="STAGE", FILTER="STATUS=TAPPED") -> SELF
- PL!-pb1-030-L (Cutie Panther)
  - **Ability:** TRIGGER: ON_LIVE_START
CONDITION: SELECT_MEMBER(1) {FILTER="OPPONENT, STATUS=TAPPED"}
EFFECT: REDUCE_HEART_REQ(2) -> SELF

TRIGGER: ON_LIVE_SUCCESS
CONDITION: DISCARD_UNIQUE_NAMES_COUNT {FILTER="UNIT_BIBI, TYPE_MEMBER", MIN=2}
EFFECT: SELECT_RECOVER_MEMBER(1) {FILTER="UNIT_BIBI"} -> CARD_HAND
- PL!-pb1-031-L (輝夜の城で踊りたい)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(1) {FILTER="GROUP_ID=0", SOURCE="YELL"} -> CARD_HAND
- PL!-pb1-032-L (SENTIMENTAL StepS)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_SUCCESS_LIVE {MIN=1, FILTER="GROUP_ID=0"}
EFFECT: DRAW(1) -> PLAYER
- PL!S-bp2-022-L (未熟DREAMER)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: DECK_REFRESHED_THIS_TURN
EFFECT: BOOST_SCORE(2) -> SELF
- PL!S-bp2-021-L (未体験HORIZON)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_TO_DECK(1) {ZONE="YELL_REVEALED", TYPE_LIVE, TO="DECK_BOTTOM"}
- PL!SP-bp2-025-L (Bubble Rise)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_MEMBER(PLAYER) {FILTER="NAME_IN=['澁谷かのん', 'ウィーン·マルガレーテ', '鬼塚冬毬'], UNIQUE_NAMES", MIN=2}
EFFECT: SELECT_RECOVER_CARD(1) -> CARD_HAND {ZONE="YELL_REVEALED"}
- PL!SP-bp2-024-L (ビタミンSUMMER！)
  - **Ability:** TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAND_SIZE {TARGET="PLAYER", GREATER_THAN="OPPONENT"}
EFFECT: BOOST_SCORE(1) -> SELF

**Planned Board:**
- Live card(s) set up.
- Include related cards in relevant zones (hand/stage/live).

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q143
**Question:** {{center.png|センター}}
とはどのような能力ですか？

**Answer:** {{center.png|センター}}
はステージのセンターエリアにいるときにのみ有効な能力です。
センターエリア以外では使用できません。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q141
**Question:** メンバーの下にあるエネルギーがあるメンバーとバトンタッチしてメンバーを登場させた場合、どうなりますか？

**Answer:** メンバーの下にあったエネルギーはエネルギーデッキに移動します。
バトンタッチしたメンバーにはメンバー下にあるエネルギーカードがない状態で登場します。

**Planned Board:**
- Member in hand ready to play.
- Member(s) on stage to baton touch.

**Planned Action:**
- Play member and check effects.
- Perform baton touch and verify outcome.

---

## Q140
**Question:** メンバーの下にあるエネルギーがあるメンバーが控え室や手札に移動する場合、どうなりますか？

**Answer:** メンバーカードのみを移動し、メンバーカードが重ねられていないエネルギーはエネルギーデッキに移動します。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q139
**Question:** メンバーの下にあるエネルギーがある状態でエリアを移動する場合、どうなりますか？

**Answer:** 他のエリアに移動する場合、メンバーの下にあるエネルギーカードは移動するメンバーと同時にエリアを移動します。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q138
**Question:** メンバーの下にあるエネルギーを使ってメンバーを登場できますか？

**Answer:** いいえできません。
メンバーの下にあるエネルギーカードはアクティブ状態とウェイト状態を持たず、コストの支払いに使用できません。

**Planned Board:**
- Member in hand ready to play.

**Planned Action:**
- Play member and check effects.

---

## Q137
**Question:** 既にウェイト状態のメンバーをコストで「ウェイトにする」ことはできますか？

**Answer:** いいえ、できません。
「ウェイトにする」とは、アクティブ状態のメンバーをウェイト状態にすることを意味します。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q136
**Question:** ウェイト状態のメンバーをエリアを移動する場合、どうなりますか？

**Answer:** ウェイト状態のまま移動させます。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q135
**Question:** ウェイト状態のメンバーはアクティブ状態になりますか？

**Answer:** 自分のアクティブフェイズでウェイト状態のメンバーを全てアクティブにします。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q134
**Question:** ウェイト状態のメンバーとバトンタッチはできますか？

**Answer:** はい、可能です。
ウェイト状態のメンバーとバトンタッチで登場する場合、アクティブ状態で登場させます。
ただし、このターン登場したメンバーとバトンタッチは行えません。

**Planned Board:**
- Member(s) on stage to baton touch.

**Planned Action:**
- Perform baton touch and verify outcome.

---

## Q133
**Question:** メンバーがウェイト状態のときどうなりますか？

**Answer:** エールを行う時、ウェイト状態のメンバーの
{{icon_blade.png|ブレード}}
はエールで公開する枚数に含みません。
エールを行う時はアクティブ状態のメンバー
{{icon_blade.png|ブレード}}
の数だけエールのチェックを行います。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q104
**Question:** 『デッキの上からカードを5枚控え室に置く。』などの効果について。
メインデッキの枚数が控え室に置く枚数より少ないか同じ場合、どのような手順で行えばいいですか？

**Answer:** 例えば、メインデッキが4枚で上からカードを5枚控え室に置く場合、以下の手順で処理をします。〈【1】メインデッキの上からカードを4枚控え室に置きます。【2】メインデッキがなくなったので、この効果で控え室に置いたカードを含めてリフレッシュを行い、新たなメインデッキとします。【3】さらにカードを1枚（【1】の4枚と合わせて合計5枚）控え室に置きます。〉

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q101
**Question:** エールとしてカードをめくる処理の途中で、メインデッキが0枚になったためリフレッシュを行い、再開した処理の途中で、新しいメインデッキと控え室のカードが0枚になりました。どうすればいいですか？

**Answer:** 効果や処理は実行可能な限り解決し、一部でも実行可能な場合はその一部を解決します。まったく解決できない場合は何も行いません。
この場合、新しいメインデッキのカードがすべてめくられた時点で、エールとしてカードをめくる処理を終了します。
その後、何らかの理由でメインデッキにカードがなく控え室にカードがある状態になった時点で、リフレッシュを行います。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q100
**Question:** エールとしてカードをめくる処理で、必要な枚数をめくったと同時にメインデッキが0枚になりました。エールとしてめくったカードはリフレッシュするカードに含まれますか？

**Answer:** いいえ、含まれません。
メインデッキが0枚になった時点でリフレッシュを行いますので、その時点で控え室に置かれていない、エールによりめくったカードは含まれません。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q88
**Question:** プレイヤーの任意で、手札を控え室に置いたり、ステージのメンバーカードを控え室に置いたり、ステージのメンバーカードを別のエリアに移動したり、アクティブ状態のカードをウェイト状態にするなどの操作を行うことはできますか？

**Answer:** いいえ、できません。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q86
**Question:** 『自分のデッキの上からカードを5枚見る。その中から～』などの効果について。
メインデッキの枚数と見る枚数が同じ場合、どのような手順で行えばいいですか？

**Answer:** 以下の手順で処理をします。〈【1】メインデッキの上からカードを5枚見ます。【2】『その中から～』以降の効果を解決します。〉
メインデッキの枚数と見る枚数が同じ場合、リフレッシュは行いません。なお、効果を解決した結果、メインデッキが0枚になった場合、その時点でリフレッシュを行います。見ていたカードが控え室に置かれたと同時にメインデッキが0枚になった場合、控え室に置かれたカードを含めてリフレッシュを行います。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q85
**Question:** 『自分のデッキの上からカードを5枚見る。その中から～』などの効果について。
メインデッキの枚数が見る枚数より少ない場合、どのような手順で行えばいいですか？

**Answer:** 例えば、メインデッキが4枚で上からカードを5枚見る場合、以下の手順で処理をします。〈【1】メインデッキの上からカードを4枚見ます。【2】さらに見る必要があるので、リフレッシュを行い、見ている元のメインデッキのカードの下に重ねる形で、新たなメインデッキとします。【3】さらにカードを1枚（【1】の4枚と合わせて合計5枚）見ます。【4】『その中から～』以降の効果を解決します。〉

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q83
**Question:** 自分のライブカード置き場に表向きのライブカードが複数枚ある状態でライブに勝利しました。成功ライブカード置き場にそれらのライブカードすべてを置くことができますか？

**Answer:** いいえ、1枚を選んで置きます。
複数枚のライブカードでライブに勝利した場合、それらのライブカードから1枚を選んで、成功ライブカード置き場に置きます。また、成功ライブカード置き場に置くカードは、プレイヤー自身が選びます。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q72
**Question:** 自分のステージにメンバーカードがない状況です。ライブカードセットフェイズに手札のカードをライブカード置き場に置くことはできますか？

**Answer:** はい、できます。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q71
**Question:** エリアにメンバーカードが置かれ、そのメンバーカードがそのエリアから別の領域に移動しました。同じターンに、メンバーカードがないこのエリアにメンバーカードを登場させたり、何らかの効果でメンバーカードを置くことはできますか？

**Answer:** はい、できます。

**Planned Board:**
- Member in hand ready to play.

**Planned Action:**
- Play member and check effects.

---

## Q61
**Question:** {{turn1.png|ターン1回}}
である自動能力が条件を満たして発動しました。同じターンの別のタイミングで発動した時に使いたいので、このタイミングでは使わないことはできますか？

**Answer:** はい、使わないことができます。使わなかった場合、別のタイミングでもう一度条件を満たせば、この自動能力がもう一度発動します。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q60
**Question:** {{turn1.png|ターン1回}}
でない自動能力が条件を満たして発動しました。この能力を使わないことはできますか？

**Answer:** いいえ、使う必要があります。コストを支払うことで効果を解決できる自動能力の場合、コストを支払わないということはできます。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q59
**Question:** ステージにいるメンバーが
{{turn1.png|ターン1回}}
である能力を使い、その後、ステージから控え室に置かれました。同じターンに、そのメンバーがステージに置かれました。このメンバーは
{{turn1.png|ターン1回}}
である能力を使うことができますか？

**Answer:** はい、使うことができます。領域を移動（ステージ間の移動を除きます）したカードは、新しいカードとして扱います。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q58
**Question:** {{turn1.png|ターン1回}}
である能力を持つ同じメンバーがステージに2枚あります。それぞれの能力を1回ずつ使うことができますか？

**Answer:** はい、同じターンに、それぞれ1回ずつ使うことができます。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q57
**Question:** 『◯◯ができない』という効果が有効な状況で、『◯◯をする』という効果を解決することになりました。◯◯をすることはできますか？

**Answer:** いいえ、できません。このような場合、禁止する効果が優先されます。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q54
**Question:** 何らかの理由で、同時に成功ライブカード置き場に置かれているカードが3枚以上（ハーフデッキの場合は2枚以上）になった場合、ゲームの勝敗はどうなりますか？

**Answer:** そのゲームは引き分けになります。ただし、大会などで個別にルールが定められている場合、そのルールに沿って勝敗を決定します。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q52
**Question:** Aさんが先攻、Bさんが後攻のターンで、スコアが同じため両方のプレイヤーがライブに勝利して、既に成功ライブカード置き場にカードが2枚（ハーフデッキの場合は1枚）あったため、両方のプレイヤーがカードを置けませんでした。次のターンの先攻・後攻はどうなりますか？

**Answer:** Aさんが先攻、Bさんが後攻のままです。成功ライブカード置き場にカードを置いたプレイヤーがいない場合、次のターンの先攻・後攻は変わりません。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q51
**Question:** Aさんが先攻、Bさんが後攻のターンで、スコアが同じため両方のプレイヤーがライブに勝利して、Bさんは成功ライブカード置き場にカードを置きましたが、Aさんは既に成功ライブカード置き場にカードが2枚（ハーフデッキの場合は1枚）あったため、カードを置けませんでした。次のターンの先攻・後攻はどうなりますか？

**Answer:** Bさんが先攻、Aさんが後攻になります。この場合、Bさんだけが成功ライブカード置き場にカードを置いたので、次のターンはBさんが先攻になります。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q50
**Question:** Aさんが先攻、Bさんが後攻のターンで、スコアが同じため両方のプレイヤーがライブに勝利して、両方のプレイヤーが成功ライブカード置き場にカードを置きました。次のターンの先攻・後攻はどうなりますか？

**Answer:** Aさんが先攻、Bさんが後攻のままです。両方のプレイヤーが成功ライブカード置き場にカードを置いた場合、次のターンの先攻・後攻は変わりません。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.
- Check score calculation.

---

## Q46
**Question:** 『
{{jyouji.png|常時}}
自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、
{{icon_all.png|ハート}}
{{icon_all.png|ハート}}
{{icon_blade.png|ブレード}}
{{icon_blade.png|ブレード}}
を得る。』について。
この能力の効果で得られる
{{icon_all.png|ハート}}
を、どの色のハートとして扱うかを決めるのはいつですか？

**Answer:** パフォーマンスフェイズで、必要ハートを満たしているかどうかを確認する時に決めます。

**Planned Board:**
- Live card(s) set up.
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q45
**Question:** エールのチェックで公開された
{{icon_b_all.png|ALLブレード}}
は、どのような効果を発揮しますか？

**Answer:** パフォーマンスフェイズで、必要ハートを満たしているかどうかを確認する時に、
{{icon_b_all.png|ALLブレード}}
1つにつき、任意の色（
{{heart_01.png|heart01}}
、
{{heart_04.png|heart04}}
、
{{heart_05.png|heart05}}
、
{{heart_02.png|heart02}}
、
{{heart_03.png|heart03}}
、
{{heart_06.png|heart06}}
）のハートアイコン1つとして扱います。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q44
**Question:** エールのチェックで公開された
{{icon_score.png|スコア}}
は、どのような効果を発揮しますか？

**Answer:** ライブカードの合計スコアを確認する時に、
{{icon_score.png|スコア}}
1つにつき、合計スコアに1を加算します。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Check score calculation.

---

## Q43
**Question:** エールのチェックで公開された
{{icon_draw.png|ドロー}}
は、どのような効果を発揮しますか？

**Answer:** エールのチェックをすべて行った後、
{{icon_draw.png|ドロー}}
1つにつき、カードを1枚引きます。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q42
**Question:** エールのチェック中に出たブレードハートの効果や発動した能力は、いつ使えますか？

**Answer:** そのエールのチェックをすべて行った後に使います。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q41
**Question:** エールのチェックで公開したカードは、いつ控え室に置きますか？

**Answer:** ライブ勝敗判定フェイズで、ライブに勝利したプレイヤーがライブカードを成功ライブカード置き場に置いた後、残りのカードを控え室に置くタイミングで控え室に置きます。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q40
**Question:** エールのチェックを行っている途中で、必要ハートの条件を満たすことがわかりました。残りのエールのチェックを行わないことはできますか？

**Answer:** いいえ、できません。エールのチェックをすべて行った後に、必要ハートの条件を確認します。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q39
**Question:** エールの確認を行わなくても、必要ハートの条件を満たすことがわかっています。エールのチェックを行わないことはできますか？

**Answer:** いいえ、できません。エールのチェックをすべて行った後に、必要ハートの条件を確認します。

**Planned Board:**
- Yell deck prepared or required hearts checked.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q37
**Question:** {{live_start.png|ライブ開始時}}
や
{{live_success.png|ライブ成功時}}
の自動能力は、同じタイミングで何回でも使えますか？

**Answer:** いいえ、1回だけ使えます。
{{live_start.png|ライブ開始時}}
や
{{live_success.png|ライブ成功時}}
になった時に1回だけ能力が発動するため、そのタイミングでは1回だけその能力を使うことができます。
複数の
{{live_start.png|ライブ開始時}}
や
{{live_success.png|ライブ成功時}}
の自動能力がある場合、それぞれの能力が発動するため、それぞれの能力を1回ずつ使います。
なお、複数の自動能力が同時に発動した場合、そのプレイヤーが使う能力の順番を選びます。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q33
**Question:** {{live_start.png|ライブ開始時}}
とはいつのことですか？

**Answer:** パフォーマンスフェイズでライブカード置き場のカードをすべて表にして、ライブカード以外のカードすべてを控え室に置いた後、エールの確認を行う前のタイミングです。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q31
**Question:** ライブカード置き場に同じカードを2枚以上置くことはできますか？

**Answer:** はい、できます。カードナンバーが同じカード、カード名が同じカードであっても、2枚以上置くことができます。

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q30
**Question:** ステージに同じカードを2枚以上登場させることはできますか？

**Answer:** はい、できます。カードナンバーが同じカード、カード名が同じカードであっても、2枚以上登場させることができます。

**Planned Board:**
- Member in hand ready to play.

**Planned Action:**
- Play member and check effects.

---

## Q28
**Question:** メンバーカードが置かれているエリアに、「バトンタッチ」をせずにメンバーを登場させることはできますか？

**Answer:** はい、できます。その場合、登場させるメンバーカードのコストと同じ枚数だけ、エネルギー置き場のエネルギーカードをアクティブ状態（縦向き状態）からウェイト状態（横向き状態）にして登場させて、もともとそのエリアに置かれていたメンバーカードを控え室に置きます。

**Planned Board:**
- Member in hand ready to play.
- Member(s) on stage to baton touch.

**Planned Action:**
- Play member and check effects.
- Perform baton touch and verify outcome.

---

## Q22
**Question:** ドローフェイズでカードを引き忘れていたことに気づきました。どうすればいいですか？

**Answer:** お互いに忘れていたことがはっきり分かる場合は、対戦相手に確認をとってから、本来引くべきカードを引いてください。ただし、手札の枚数は頻繁に変わって確認が難しいため、特に引き忘れないように気をつけてください。大会の対戦中にはっきり分からなくなってしまった場合は、ジャッジに確認をしてもらってください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q21
**Question:** エネルギーフェイズでエネルギーカードを置き忘れていたことに気づきました。どうすればいいですか？

**Answer:** お互いに忘れていたことがはっきり分かる場合は、対戦相手に確認をとってから、本来置くべきエネルギーカードをエネルギー置き場に置いてください。大会の対戦中にはっきり分からなくなってしまった場合は、ジャッジに確認をしてもらってください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q20
**Question:** アクティブフェイズでエネルギーカードをアクティブにし忘れていたことに気づきました。どうすればいいですか？

**Answer:** お互いに忘れていたことがはっきり分かる場合は、対戦相手に確認をとってから、本来アクティブになるべきエネルギーカードをアクティブにしてください。大会の対戦中にはっきり分からなくなってしまった場合は、ジャッジに確認をしてもらってください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q15
**Question:** エネルギーデッキ置き場とエネルギー置き場のカードの置き方に決まりはありますか？

**Answer:** エネルギーデッキ置き場に置くエネルギーデッキはすべて裏向きに置いてください。エネルギー置き場に置くカードはすべて表向きに置いてください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q14
**Question:** デッキをシャッフルをする際に、気をつけることはありますか？

**Answer:** シャッフルを行うプレイヤー自身が、どこにどのカードがあるかわからなくなるように、しっかりと無作為化をしてください。その後、対戦相手にシャッフル（カット）を行ってもらってください。また、自分のカードか相手のカードであるかに関わらず、シャッフルをする際は、カードが折れたりしないよう丁寧に扱ってください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q13
**Question:** 大会で「注意」や「警告」という言葉を聞きました。これはなんですか？

**Answer:** 大会で、遅刻をしたり、うっかりルール上の違反などをしてしまった場合に、啓蒙の意味を込めてジャッジの判断でプレイヤーに与えられるその大会中の罰則（ペナルティ）です。「注意」や「警告」といった罰則自体はゲームの勝敗には直接影響しませんので、違反などを繰り返し行なわないように気を付けてゲームをプレイしましょう。ただし、同じ大会中に「警告」にあたる違反を繰り返したり大きな違反になってしまった場合は、対戦について「敗北」となってしまうことがあります。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q12
**Question:** 対戦中にルール上の問題が発生したり、ゲームが進まないなどの進行上のトラブルが発生した時はどうすればいいですか？

**Answer:** その時点でお互いにゲームのプレイをいったん止めて、手を挙げて近くのスタッフやジャッジを呼んで、その判断に従ってください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q11
**Question:** 大会で使用するデッキについて、気をつけることはありますか？

**Answer:** デッキの枚数に過不足がないか、構築条件（同じカードナンバーのカードは4枚まで、など）に合わせてデッキを用意できているかをチェックしましょう。また、メインデッキとエネルギーデッキのスリーブは、異なる柄やイラストのものを使いましょう。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q10
**Question:** 大会で使用するエネルギーデッキについて、スリーブを使用する必要はありますか？また、スリーブを使用する場合、異なる柄やイラストのスリーブを組み合わせて使用することができますか？

**Answer:** いいえ、必ずしもスリーブを使用する必要はありません。スリーブを使用する場合、異なる柄やイラストのスリーブを組み合わせて使用することができますが、メインデッキと区別をするため、メインデッキと同じ柄やイラストのスリーブは使用できません。
カードローダーなども使用できますが、過度に厚みがあるなど対戦に支障がでないよう注意してください。大会で、ジャッジが必要と判断した場合、スリーブなどの使い方について調整を求められる場合があります。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q9
**Question:** 大会で使用するメインデッキについて、スリーブを使用する必要はありますか？

**Answer:** はい、柄やイラストが統一されているスリーブを使用してください。
大会で、メインデッキにスリーブを使用していなかったり、透明スリーブのみを使用しているといった状況が確認された場合、ジャッジから柄やイラストが統一されているスリーブを使用するように求められる場合があります。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q8
**Question:** カードを保護するスリーブをデッキで使う際に、気をつけることはありますか？

**Answer:** スリーブの状態からカードの見分けがつかないようにしましょう。例えば、一部のスリーブに傷や汚れついていたり角が折れ曲がったりしていると、他のカードと見分けがついてしまいます。このような見分けがつく状態になってしまった場合、スリーブを交換してください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q7
**Question:** エネルギーデッキを構築するとき、同じカードは何枚まで使用することができますか？

**Answer:** エネルギーデッキは、同じカードを好きな枚数入れることができます。（同じカードを12枚入れることもできます。）

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q6
**Question:** カード名や能力が同一で、カードナンバーが異なるカードがあります。メインデッキにこれらのカードを4枚ずつ入れることはできますか？

**Answer:** はい、カードナンバーが異なる場合、それぞれ4枚まで入れることができます。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q5
**Question:** カードナンバーが同一で、レアリティが異なるカードがあります。メインデッキにこれらのカードを4枚ずつ入れることはできますか？

**Answer:** いいえ、カードナンバー同一の場合、あわせて4枚までしかいれることはできません。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q4
**Question:** メインデッキを構築するとき、同じカードは何枚まで使用することができますか？

**Answer:** カードナンバーが一致するカードを同じカードとして扱い、原則としてメインデッキに同じカードは4枚まで使用することができます。カードに記載されている「LL-bp1-001-R+」などの文字列のうち、レアリティの記号を除いた「LL-bp1-001」の部分がカードナンバーです。（ハーフデッキの場合も同様です。）

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q3
**Question:** メインデッキを構築するとき、メンバーカードとライブカードは好きな枚数で組み合わせることができますか？

**Answer:** いいえ、決まった枚数にする必要があります。メンバーカードが48枚、ライブカードが12枚、合計で60枚になるようにメインデッキを構築してください。（ハーフデッキの場合、メンバーカードが24枚、ライブカードが6枚、合計で30枚。）

**Planned Board:**
- Live card(s) set up.

**Planned Action:**
- Start live and verify outcome matches answer.

---

## Q2
**Question:** 大会に参加する際に、気をつけることはありますか？

**Answer:** まず、大会の開催日時や参加方法をチェックしましょう。公式ホームページやブシナビで、大会の日程やルールをチェックすることができます。当日はデッキやブシナビをインストールしたスマホなどを忘れず持って行きましょう。会場ではスタッフのアナウンスを聞き漏らさないよう注意し、スタッフやジャッジの指示に従って大会に参加してください。また、いつでも対戦相手をはじめすべての関係者に対する敬意やマナーを忘れずに大会や対戦を楽しんでください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---

## Q1
**Question:** 商品はどこで購入できますか？

**Answer:** 全国のカードショップを中心にお買い求めいただけます。ラブカ公式サイトの各商品情報やお店を探すページにも、ショップ一覧が掲載されていますので参考にしてみてください。

**Planned Board:**
- Setup board according to question context.

**Planned Action:**
- Execute action described in question and verify answer.

---
