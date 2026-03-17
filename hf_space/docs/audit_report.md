# Logic Robustness Audit Report

Generated bilingual audit for game logic verification.

## LL-PR-004-PR: 愛♡スクリ～ム！
**Original Japanese:**
{{live_start.png|ライブ開始時}}相手に何が好き？と聞く。
回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。
回答があなたの場合、自分と相手はカードを1枚引く。
回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: チョコミント/ストロベリー/クッキー＆クリーム | EFFECT: DISCARD_HAND(1) -> PLAYER; DISCARD_HAND(1) -> OPPONENT
  OPTION: あなた | EFFECT: DRAW(1) -> PLAYER; DRAW(1) -> OPPONENT
  OPTION: その他 | EFFECT: ADD_BLADES(1) -> PLAYER; ADD_BLADES(1) -> OPPONENT
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  モードを選択する  → 対象： 自分
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  チョコミント/ストロベリー/クッキー＆クリーム | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  手札を1枚控え室に置く  → 対象： 自分; 手札を1枚控え室に置く  → 対象： 相手
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  あなた | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを1枚引く  → 対象： 自分; カードを1枚引く  → 対象： 相手
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  その他 | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ブレードを1得る  → 対象： 自分; ブレードを1得る  → 対象： 相手

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a mode  targeting  Player
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  チョコミント/ストロベリー/クッキー＆クリーム | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Discard 1 card(s) from Hand  targeting  Player; Discard 1 card(s) from Hand  targeting  Opponent
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  あなた | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw 1 card(s)  targeting  Player; Draw 1 card(s)  targeting  Opponent
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  その他 | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Blade(s)  targeting  Player; Gain 1 Blade(s)  targeting  Opponent

---

## LL-bp4-001-R＋: 絢瀬絵里&朝香果林&葉月 恋
**Original Japanese:**
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}自分のデッキの上からカードを5枚見る。その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。その後、相手のステージにいる、これにより公開したカードのコスト以下で、かつ元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバーをすべてウェイトにする。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="Eri/Karin/Ren"} -> CARD_HAND, DISCARD_REMAINDER
EFFECT: TAP_OPPONENT(99) -> OPPONENT {FILTER="COST_LE_REVEALED, BLADE_LE_3"}

TRIGGER: ON_LIVE_START
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="Eri/Karin/Ren"} -> CARD_HAND, DISCARD_REMAINDER
EFFECT: TAP_OPPONENT(99) -> OPPONENT {FILTER="COST_LE_REVEALED, BLADE_LE_3"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを5枚見て選ぶ  (フィルタ=絢瀬 絵里/朝香 果林/葉月 恋)  → 対象： 手札, 残りを控え室に
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  相手のメンバーをすべてウェイトにする  → 対象： 相手  (フィルタ=公開されたカードのコスト以下, ブレード数 3以下)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを5枚見て選ぶ  (フィルタ=絢瀬 絵里/朝香 果林/葉月 恋)  → 対象： 手札, 残りを控え室に
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  相手のメンバーをすべてウェイトにする  → 対象： 相手  (フィルタ=公開されたカードのコスト以下, ブレード数 3以下)

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Look at cards and choose 5  (Filter=Eri/Karin/Ren)  targeting  Hand, Discard Remainder
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Rest all member(s) on stage  targeting  Opponent  (Filter=COST_LE_REVEALED, Blades <= 3)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Look at cards and choose 5  (Filter=Eri/Karin/Ren)  targeting  Hand, Discard Remainder
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Rest all member(s) on stage  targeting  Opponent  (Filter=COST_LE_REVEALED, Blades <= 3)

---

## PL!-bp3-006-P: 西木野真姫
**Original Japanese:**
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1)
EFFECT: BUFF_POWER(2) -> PLAYER {PER_CARD="SUCCESS_LIVE"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  手札を1枚控え室に置く
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  パワーを+2する  → 対象： 自分  (（〜の枚数につき）=成功ライブ)

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Hand
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain +2 Power  targeting  Player  (for each card in=Success Area)

---

## PL!-bp3-024-L: 夏色えがおで1,2,Jump!
**Original Japanese:**
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、選んだハートを1つ得る。
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、このカードのスコアを＋１する。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE {MIN=1}
EFFECT: SELECT_MODE(1)
  OPTION: ピンク | EFFECT: ADD_HEARTS(1) {HEART_TYPE=0} -> TARGET_MEMBER
  OPTION: レッド | EFFECT: ADD_HEARTS(1) {HEART_TYPE=1} -> TARGET_MEMBER
  OPTION: イエロー | EFFECT: ADD_HEARTS(1) {HEART_TYPE=2} -> TARGET_MEMBER
  OPTION: グリーン | EFFECT: ADD_HEARTS(1) {HEART_TYPE=3} -> TARGET_MEMBER
  OPTION: ブルー | EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> TARGET_MEMBER
  OPTION: パープル | EFFECT: ADD_HEARTS(1) {HEART_TYPE=5} -> TARGET_MEMBER

CONDITION: COUNT_SUCCESS_LIVE {MIN=2}
EFFECT: BOOST_SCORE(1) -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_SUCCESS_LIVE  (最小=レッド)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  モードを選択する
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ピンク | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=ピンク)  → 対象： TARGET_MEMBER
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  レッド | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=レッド)  → 対象： TARGET_MEMBER
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  イエロー | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=イエロー)  → 対象： TARGET_MEMBER
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  グリーン | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=グリーン)  → 対象： TARGET_MEMBER
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ブルー | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=ブルー)  → 対象： TARGET_MEMBER
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  パープル | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=パープル)  → 対象： TARGET_MEMBER
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_SUCCESS_LIVE  (最小=イエロー)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  スコアを＋1する  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_SUCCESS_LIVE  (Min=1)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a mode
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ピンク | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=0)  targeting  Target Member
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  レッド | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=1)  targeting  Target Member
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  イエロー | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=2)  targeting  Target Member
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  グリーン | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=3)  targeting  Target Member
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ブルー | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=4)  targeting  Target Member
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  パープル | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=5)  targeting  Target Member
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_SUCCESS_LIVE  (Min=2)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Add 1 to Live Score  targeting  This Card

---

## PL!-bp4-005-P: 星空 凛
**Original Japanese:**
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。
{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１する。
{{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: RECOVER_MEMBER(1) {FILTER="COST_LE_2"} -> CARD_HAND

TRIGGER: CONSTANT
EFFECT: BOOST_SCORE(1) -> SELF {MODE="CENTER_ONLY"}

TRIGGER: ON_LIVE_START
CONDITION: IS_CENTER, NOT COUNT_STAGE {FILTER="BLADE_GE_5, GROUP_ID=0"}
EFFECT: MOVE_MEMBER(1) -> PLAYER {MODE="OUT_OF_CENTER"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からメンバーを1枚手札に加える  (フィルタ=コスト 2以下)  → 対象： 手札

### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  スコアを＋1する  → 対象： このカード  (モード=センター限定)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  センターの場合, 〜でないなら COUNT_STAGE  (フィルタ=ブレード数 5以上, GROUP_ID=0)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  MOVE_MEMBER(1)  → 対象： 自分  (モード=センター以外へ)

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Member(s) from Discard  (Filter=Cost <= 2)  targeting  Hand

### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Add 1 to Live Score  targeting  This Card  (Mode=Center Only)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If in Center, If NOT COUNT_STAGE  (Filter=Blades >= 5, GROUP_ID=0)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Move a member on stage  targeting  Player  (Mode=Out of Center)

---

## PL!-bp4-008-P: 小泉花陽
**Original Japanese:**
{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ステージにいるこのメンバーのコストを＋３する。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
CONDITION: SCORE_TOTAL {MIN=6}
EFFECT: INCREASE_COST(3) -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  合計スコアをチェックする  (最小=6)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  コストを+3する  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  Total Score  (Min=6)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Cost +3  targeting  This Card

---

## PL!-pb1-001-P＋: 高坂穂乃果
**Original Japanese:**
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ACTIVATED
CONDITION: IS_CENTER, TURN_1
COST: TAP_MEMBER; DISCARD_HAND(1)
EFFECT: SELECT_MODE(1)
  OPTION: ライブカード | EFFECT: REVEAL_UNTIL(TYPE_LIVE) -> CARD_HAND, DISCARD_REMAINDER
  OPTION: コスト10以上 | EFFECT: REVEAL_UNTIL(COST_GE=10, TYPE_MEMBER) -> CARD_HAND, DISCARD_REMAINDER
```

**Friendly Japanese (Verification Mode):**
### ステップ  起動
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  センターの場合, ターン1回
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  自分のメンバーをウェイトにする; 手札を1枚控え室に置く
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  モードを選択する
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ライブカード | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  TYPE_LIVEが公開されるまでデッキをめくる  → 対象： 手札, 残りを控え室に
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  コスト10以上 | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  COST_GE=10, TYPE_MEMBERが公開されるまでデッキをめくる  → 対象： 手札, 残りを控え室に

**Friendly English (Internal Audit Mode):**
### Step  When Activated
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If in Center, Once per turn
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Rest  of your members; Discard 1 card(s) from Hand
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a mode
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ライブカード | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Reveal cards until TYPE_LIVE  targeting  Hand, Discard Remainder
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  コスト10以上 | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Reveal cards until COST_GE=10, TYPE_MEMBER  targeting  Hand, Discard Remainder

---

## PL!-pb1-009-P＋: 矢澤にこ
**Original Japanese:**
{{toujyou.png|登場}}相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする。
{{toujyou.png|登場}}このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: TAP_OPPONENT(1) -> OPPONENT {FILTER="BLADE_LE_1"}; PREVENT_ACTIVATE(ALL) -> PLAYER; PREVENT_ACTIVATE(ALL) -> OPPONENT
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  相手のメンバーを1人ウェイトにする  → 対象： 相手  (フィルタ=ブレード数が1以下); PREVENT_ACTIVATE(ALL)  → 対象： 自分; PREVENT_ACTIVATE(ALL)  → 対象： 相手

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Rest 1 member(s) on stage  targeting  Opponent  (Filter=Blades <= 1); Prevent members from being activated  targeting  Player; Prevent members from being activated  targeting  Opponent

---

## PL!-pb1-009-R: 矢澤にこ
**Original Japanese:**
{{toujyou.png|登場}}相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする。
{{toujyou.png|登場}}このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: TAP_OPPONENT(1) -> OPPONENT {FILTER="BLADE_LE_1"}; PREVENT_ACTIVATE(ALL) -> PLAYER; PREVENT_ACTIVATE(ALL) -> OPPONENT
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  相手のメンバーを1人ウェイトにする  → 対象： 相手  (フィルタ=ブレード数が1以下); PREVENT_ACTIVATE(ALL)  → 対象： 自分; PREVENT_ACTIVATE(ALL)  → 対象： 相手

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Rest 1 member(s) on stage  targeting  Opponent  (Filter=Blades <= 1); Prevent members from being activated  targeting  Player; Prevent members from being activated  targeting  Opponent

---

## PL!-pb1-030-L: Cutie Panther
**Original Japanese:**
{{live_start.png|ライブ開始時}}相手のステージにウェイト状態のメンバーがいる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。
{{live_success.png|ライブ成功時}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、自分の控え室から『BiBi』のメンバーカードを1枚手札に加える。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
CONDITION: OPPONENT_HAS_WAIT
EFFECT: REDUCE_HEART_REQ(2) -> SELF

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_GROUP {MIN=2, FILTER="UNIT_BIBI", UNIQUE_NAMES=TRUE}
EFFECT: RECOVER_MEMBER(1) {FILTER="UNIT_BIBI"} -> CARD_HAND
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  相手にウェイト状態のメンバーがいる場合
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  必要ハートを-2する  → 対象： このカード

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_GROUP  (最小=イエロー, フィルタ=BiBi, UNIQUE_NAMES=TRUE)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からメンバーを1枚手札に加える  (フィルタ=BiBi)  → 対象： 手札

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If Opponent has Rested member
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Reduce Heart requirement by 2  targeting  This Card

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_GROUP  (Min=2, Filter=BiBi, with unique names=Yes)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Member(s) from Discard  (Filter=BiBi)  targeting  Hand

---

## PL!HS-bp2-007-P: 百生 吟子
**Original Japanese:**
{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：これにより控え室に置いたカードがメンバーカードの場合、控え室に置いたカードと同じ名前を持つメンバー1人は、ライブ終了時まで、{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
CONDITION: BATON_PASS {UNIT="スリーズブーケ", COST_LT=SELF}
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) (Optional)
EFFECT: SELECT_MEMBER(1) {ZONE="STAGE", SAME_NAME_AS="DISCARDED"} -> TARGET; ADD_HEARTS(1) {HEART_TYPE=3, TARGET="TARGET", DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET {DURATION="UNTIL_LIVE_END"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  BATON_PASS  (UNIT=スリーズブーケ, COST_LT=このカード)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からライブカードを1枚手札に加える  (フィルタ=GROUP_ID=4)  → 対象： 手札

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  手札を1枚控え室に置く (Optional)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人を選ぶ  (ZONE=ステージ, SAME_NAME_AS=DISCARDED)  → 対象： TARGET; ハートを1得る  (ハートの色=グリーン, TARGET=TARGET, DURATION=ライブ終了時まで); ブレードを1得る  → 対象： TARGET  (DURATION=ライブ終了時まで)

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  BATON_PASS  (UNIT=スリーズブーケ, COST_LT=This Card)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Live(s) from Discard  (Filter=GROUP_ID=4)  targeting  Hand

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Hand (Optional)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 Member(s)  (Zone=Stage, SAME_NAME_AS=DISCARDED)  targeting  TARGET; Gain 1 Heart(s)  (Heart Color=3, Target=Target, Duration=Until Live Ends); Gain 1 Blade(s)  targeting  TARGET  (Duration=Until Live Ends)

---

## PL!HS-bp2-018-N: 安養寺 姫芽
**Original Japanese:**
{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ACTIVATED
CONDITION: IS_MAIN_PHASE
COST: PAY_ENERGY(2)
EFFECT: PLAY_LIVE_FROM_DISCARD(1) -> LIVE_ZONE
EFFECT: REDUCE_LIVE_SET_LIMIT(1) {TARGET="NEXT_LIVE_SET"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  起動
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  メインフェイズの場合
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  エネルギーを2支払う
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  PLAY_LIVE_FROM_DISCARD(1)  → 対象： LIVE_ZONE
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  セット上限を-1する  (TARGET=NEXT_LIVE_SET)

**Friendly English (Internal Audit Mode):**
### Step  When Activated
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  During Main Phase
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Pay 2 Energy
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Play a Live card from Discard  targeting  LIVE_ZONE
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Reduce Live Set limit by 1  (Target=NEXT_LIVE_SET)

---

## PL!HS-bp2-019-L: Bloom the smile, Bloom the dream!
**Original Japanese:**
{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=4"}
EFFECT: SELECT_MODE(1)
  OPTION: ピンク×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="PINK/PINK/ANY"}
  OPTION: グリーン×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="GREEN/GREEN/ANY"}
  OPTION: ブルー×2 | EFFECT: SET_HEART_COST("0/0/0/0/0/0") {ADD="BLUE/BLUE/ANY"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_STAGE  (最小=レッド, フィルタ=GROUP_ID=4)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  モードを選択する
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ピンク×2 | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SET_HEART_COST("0/0/0/0/0/0")  (ADD=ピンク/ピンク/どの色でもよい)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  グリーン×2 | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SET_HEART_COST("0/0/0/0/0/0")  (ADD=グリーン/グリーン/どの色でもよい)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ブルー×2 | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SET_HEART_COST("0/0/0/0/0/0")  (ADD=ブルー/ブルー/どの色でもよい)

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_STAGE  (Min=1, Filter=GROUP_ID=4)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a mode
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ピンク×2 | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  SET_HEART_COST("0/0/0/0/0/0")  (ADD=Pink/Pink/Any)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  グリーン×2 | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  SET_HEART_COST("0/0/0/0/0/0")  (ADD=Green/Green/Any)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ブルー×2 | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  SET_HEART_COST("0/0/0/0/0/0")  (ADD=Blue/Blue/Any)

---

## PL!HS-bp2-020-L: Link to the FUTURE
**Original Japanese:**
{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。
{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを＋２する。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
EFFECT: ADD_TAG("UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA") -> SELF

TRIGGER: ON_LIVE_START
EFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="STAGE", FILTER="UNIT_HASU, UNIQUE_NAMES"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  属性「"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA"」を得る  → 対象： このカード

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  スコアを＋2する  → 対象： このカード  (（〜の枚数につき）=ステージ, フィルタ=UNIT_HASU, UNIQUE_NAMES)

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain traits ("UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA")  targeting  This Card

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Add 2 to Live Score  targeting  This Card  (for each card in=Stage, Filter=UNIT_HASU, UNIQUE_NAMES)

---

## PL!N-bp1-002-P: 中須かすみ
**Original Japanese:**
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: LOOK_AND_CHOOSE_ORDER(3) {REMAINDER="DISCARD"}

TRIGGER: ACTIVATED
CONDITION: CHECK_IS_IN_DISCARD
COST: PAY_ENERGY(2); DISCARD_HAND(1)
EFFECT: PLAY_MEMBER_FROM_DISCARD(1) -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを3見て並べ替える  (残りのカード=控え室)

### ステップ  起動
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  控え室にいる場合
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  エネルギーを2支払う; 手札を1枚控え室に置く
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からメンバー1枚を登場させる  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Look at 3 cards and reorder  (Remainder=Discard Pile)

### Step  When Activated
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If in Discard Pile
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Pay 2 Energy; Discard 1 card(s) from Hand
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Play a Member from Discard  targeting  This Card

---

## PL!N-bp3-005-P: 宮下 愛
**Original Japanese:**
{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。
{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_STAGE_ENTRY
CONDITION: COUNT_PLAYED_THIS_TURN {MIN=3}
EFFECT: DRAW_UNTIL(5)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_PLAYED_THIS_TURN {MIN=2}
EFFECT: BOOST_SCORE(1) -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  メンバーが登場した時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_PLAYED_THIS_TURN  (最小=グリーン)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  DRAW_UNTIL(5)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_PLAYED_THIS_TURN  (最小=イエロー)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  スコアを＋1する  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  When member enters Stage
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_PLAYED_THIS_TURN  (Min=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw until you have 5 cards

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_PLAYED_THIS_TURN  (Min=2)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Add 1 to Live Score  targeting  Player

---

## PL!N-bp3-008-P: エマ・ヴェルデ
**Original Japanese:**
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のステージにいるこのメンバー以外のウェイト状態のメンバー1人をアクティブにする。そうした場合、ライブ終了時まで、これによりアクティブにしたメンバーと、このメンバーは、それぞれ{{heart_04.png|heart04}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ACTIVATED
CONDITION: TURN_1
COST: TAP_MEMBER(1) {FILTER="GROUP_ID=3", TARGET="OTHER_MEMBER"}
EFFECT: DRAW(1) -> PLAYER

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(2)
EFFECT: ACTIVATE_MEMBER(1) {FILTER="TAPPED", TARGET="OTHER_MEMBER"}; ADD_HEARTS(1) {HEART_TYPE=4, TARGET="ACTIVATE_AND_SELF"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  起動
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  ターン1回
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  自分のメンバー1人をウェイトにする  (フィルタ=GROUP_ID=3, TARGET=それ以外のメンバー)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを1枚引く  → 対象： 自分

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  手札を2枚控え室に置く
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人をアクティブにする  (フィルタ=ウェイト状態, TARGET=それ以外のメンバー); ハートを1得る  (ハートの色=ブルー, TARGET=アクティブにしたメンバーとこのカード)

**Friendly English (Internal Audit Mode):**
### Step  When Activated
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  Once per turn
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Rest 1 of your members  (Filter=GROUP_ID=3, Target=Other Member)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw 1 card(s)  targeting  Player

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 2 card(s) from Hand
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Activate 1 Member(s)  (Filter=Rested, Target=Other Member); Gain 1 Heart(s)  (Heart Color=4, Target=Target and This Card)

---

## PL!N-bp3-017-N: 宮下 愛
**Original Japanese:**
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
EFFECT: CHEER_REVEAL(1) -> SELF
TRIGGER: ON_REVEAL
EFFECT: TAP_MEMBER(99) {TARGET="OPPONENT", FILTER="COST_LE_4"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  1をエールとして公開する  → 対象： このカード

### ステップ  エールで公開された時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  自分のメンバーすべてをウェイトにする  (TARGET=相手, フィルタ=コスト 4以下)

**Friendly English (Internal Audit Mode):**
### Step  When Played

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Reveal via Cheer  targeting  This Card

### Step  When Revealed by Yell
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Rest all of your members  (Target=Opponent, Filter=Cost <= 4)

---

## PL!N-bp4-004-P: 朝香果林
**Original Japanese:**
{{live_start.png|ライブ開始時}}カードを1枚引く。相手のステージにいるコスト9以下のメンバーを1人までウェイトにする。
{{live_start.png|ライブ開始時}}相手のステージにいるウェイト状態のメンバーの数まで、自分の控え室にある『虹ヶ咲』のメンバーカードを選ぶ。それらを好きな順番でデッキの上に置く。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
EFFECT: DRAW(1) -> PLAYER; TAP_OPPONENT(1) {FILTER="COST_LE_9"}
EFFECT: ORDER_DECK(X) {PER_CARD="OPPONENT_STAGE", FILTER="TAPPED", FROM="DISCARD", TARGET_FILTER="GROUP_ID=2"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを1枚引く  → 対象： 自分; 相手のメンバーを1人ウェイトにする  (フィルタ=コスト 9以下)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ORDER_DECK(X)  (（〜の枚数につき）=OPPONENT_STAGE, フィルタ=ウェイト状態, FROM=控え室, TARGET_FILTER=GROUP_ID=2)

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw 1 card(s)  targeting  Player; Rest 1 member(s) on stage  (Filter=Cost <= 9)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Reorder the top X cards of Deck  (for each card in=OPPONENT_STAGE, Filter=Rested, From=Discard Pile, TARGET_FILTER=GROUP_ID=2)

---

## PL!N-bp4-007-P: 優木せつ菜
**Original Japanese:**
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。
{{live_success.png|ライブ成功時}}自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: RECOVER_LIVE(1) -> PLAYER; RECOVER_LIVE(1) -> OPPONENT

TRIGGER: CONSTANT
CONDITION: SUM_ENERGY {MIN=15, TARGET="BOTH"}
EFFECT: ADD_HEARTS(2) {HEART_TYPE=2}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: ACTIVATE_ENERGY(1, MODE="WAIT") -> PLAYER; ACTIVATE_ENERGY(1, MODE="WAIT") -> OPPONENT
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からライブカードを1枚手札に加える  → 対象： 自分; 控え室からライブカードを1枚手札に加える  → 対象： 相手

### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  SUM_ENERGY  (最小=15, TARGET=自分と相手)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを2得る  (ハートの色=イエロー)

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  エネルギー1, MODE="WAIT"をアクティブにする  → 対象： 自分; エネルギー1, MODE="WAIT"をアクティブにする  → 対象： 相手

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Live(s) from Discard  targeting  Player; Retrieve 1 Live(s) from Discard  targeting  Opponent

### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  SUM_ENERGY  (Min=15, Target=Both Players)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 2 Heart(s)  (Heart Color=2)

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Activate 1, MODE="WAIT" Energy  targeting  Player; Activate 1, MODE="WAIT" Energy  targeting  Opponent

---

## PL!N-bp4-010-P: 三船栞子
**Original Japanese:**
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  成功ライブからカードを1枚控え室に置く  (フィルタ=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カード1枚を成功ライブに置く  (フィルタ=GROUP_ID=3, FROM=控え室)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ライブカードを1枚選ぶ  (フィルタ=GROUP_ID=2, ZONE=成功した場合)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  成功した場合
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=ブルー)  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Success Area  (Filter=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Move 1 card(s) to Success Area  (Filter=GROUP_ID=3, From=Discard Pile)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a Live card  (Filter=GROUP_ID=2, Zone=If Successful)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If Successful
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=4)  targeting  This Card

---

## PL!N-bp4-010-P＋: 三船栞子
**Original Japanese:**
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  成功ライブからカードを1枚控え室に置く  (フィルタ=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カード1枚を成功ライブに置く  (フィルタ=GROUP_ID=3, FROM=控え室)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ライブカードを1枚選ぶ  (フィルタ=GROUP_ID=2, ZONE=成功した場合)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  成功した場合
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=ブルー)  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Success Area  (Filter=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Move 1 card(s) to Success Area  (Filter=GROUP_ID=3, From=Discard Pile)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a Live card  (Filter=GROUP_ID=2, Zone=If Successful)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If Successful
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=4)  targeting  This Card

---

## PL!N-bp4-010-R＋: 三船栞子
**Original Japanese:**
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  成功ライブからカードを1枚控え室に置く  (フィルタ=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カード1枚を成功ライブに置く  (フィルタ=GROUP_ID=3, FROM=控え室)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ライブカードを1枚選ぶ  (フィルタ=GROUP_ID=2, ZONE=成功した場合)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  成功した場合
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=ブルー)  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Success Area  (Filter=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Move 1 card(s) to Success Area  (Filter=GROUP_ID=3, From=Discard Pile)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a Live card  (Filter=GROUP_ID=2, Zone=If Successful)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If Successful
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=4)  targeting  This Card

---

## PL!N-bp4-010-SEC: 三船栞子
**Original Japanese:**
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
COST: DISCARD_SUCCESS_LIVE(1) {FILTER="GROUP_ID=3"}
EFFECT: MOVE_SUCCESS(1) {FILTER="GROUP_ID=3, FROM="DISCARD"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_LIVE(1) {FILTER="GROUP_ID=2, ZONE="SUCCESS"}
CONDITION: SUCCESS
EFFECT: ADD_HEARTS(1) {HEART_TYPE=4} -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  成功ライブからカードを1枚控え室に置く  (フィルタ=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カード1枚を成功ライブに置く  (フィルタ=GROUP_ID=3, FROM=控え室)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ライブカードを1枚選ぶ  (フィルタ=GROUP_ID=2, ZONE=成功した場合)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  成功した場合
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ハートを1得る  (ハートの色=ブルー)  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Success Area  (Filter=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Move 1 card(s) to Success Area  (Filter=GROUP_ID=3, From=Discard Pile)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a Live card  (Filter=GROUP_ID=2, Zone=If Successful)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If Successful
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 1 Heart(s)  (Heart Color=4)  targeting  This Card

---

## PL!N-bp4-011-P: ミア・テイラー
**Original Japanese:**
{{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {FILTER="TYPE_LIVE"}
EFFECT: COLOR_SELECT(1) -> PLAYER; ADD_HEARTS(1) -> PLAYER

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_TO_DISCARD(5) {FROM="DECK_TOP"}
CONDITION: COUNT_DISCARD {MIN=3, FILTER="TYPE_LIVE", UNIQUE_NAMES}
EFFECT: RECOVER_LIVE(1) -> CARD_HAND
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  手札を1枚控え室に置く  (フィルタ=TYPE_LIVE)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  COLOR_SELECT(1)  → 対象： 自分; ハートを1得る  → 対象： 自分

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カード5枚を控え室に置く  (FROM=DECK_TOP)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_DISCARD  (最小=グリーン, フィルタ=TYPE_LIVE, UNIQUE_NAMES)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からライブカードを1枚手札に加える  → 対象： 手札

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Hand  (Filter=Live card)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a Color  targeting  Player; Gain 1 Heart(s)  targeting  Player

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Discard 5 card(s)  (From=DECK_TOP)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_DISCARD  (Min=3, Filter=Live card, with unique names)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Live(s) from Discard  targeting  Hand

---

## PL!N-bp4-026-L: DIVE!
**Original Japanese:**
{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。
{{jidou.png|自動}}このカードが表向きでライブカード置き場に置かれたとき、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_POSITION_CHANGE (From Discard to Hand)
CONDITION: MAIN_PHASE
EFFECT: SELECT_MODE(1) (Optional)
  OPTION: 「DIVE!」をパフォームする | EFFECT: PLAY_LIVE_FROM_HAND(1) {FILTER="NAME=DIVE!"}; REDUCE_LIVE_SET_LIMIT(1) {NEXT_TURN=TRUE}

TRIGGER: ON_PLAY
EFFECT: SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} -> TARGET; ADD_BLADES(2) -> TARGET
```

**Friendly Japanese (Verification Mode):**
### ステップ  移動した時 (From Discard to Hand)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  MAIN_PHASE
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  モードを選択する (Optional)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  「DIVE!」をパフォームする | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  PLAY_LIVE_FROM_HAND(1)  (フィルタ=NAME=DIVE!); セット上限を-1する  (NEXT_TURN=TRUE)

### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人を選ぶ  (フィルタ=GROUP_ID=3)  → 対象： TARGET; ブレードを2得る  → 対象： TARGET

**Friendly English (Internal Audit Mode):**
### Step  When Position Changes (From Discard to Hand)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  MAIN_PHASE
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a mode (Optional)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  「DIVE!」をパフォームする | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Play 1 Live card(s) from Hand  (Filter=NAME=DIVE!); Reduce Live Set limit by 1  (Next Turn=Yes)

### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 Member(s)  (Filter=GROUP_ID=3)  targeting  TARGET; Gain 2 Blade(s)  targeting  TARGET

---

## PL!N-bp4-027-L: EMOTION
**Original Japanese:**
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード名が「EMOTION」のカード1枚につき、このカードのスコアを＋２し、成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}増やす。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
EFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="SUCCESS_LIVE", FILTER="NAME=EMOTION"}
EFFECT: INCREASE_HEART_COST(3) {HEART_TYPE=0} -> SELF {PER_CARD="SUCCESS_LIVE", FILTER="NAME=EMOTION"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  スコアを＋2する  → 対象： このカード  (（〜の枚数につき）=成功ライブ, フィルタ=NAME=EMOTION)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  INCREASE_HEART_COST(3)  (ハートの色=ピンク)  → 対象： このカード  (（〜の枚数につき）=成功ライブ, フィルタ=NAME=EMOTION)

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Add 2 to Live Score  targeting  This Card  (for each card in=Success Area, Filter=NAME=EMOTION)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Heart Cost +3  (Heart Color=0)  targeting  This Card  (for each card in=Success Area, Filter=NAME=EMOTION)

---

## PL!N-pb1-004-P＋: 朝香果林
**Original Japanese:**
{{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。公開したカードがコスト9以下のメンバーカードの場合、公開したカードを手札に加え、このメンバーはポジションチェンジする。それ以外の場合、公開したカードを控え室に置く。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
CONDITION: NOT MOVED_THIS_TURN
EFFECT: ADD_BLADES(2) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: REVEAL_CARDS(1) {FROM="DECK_TOP"}
CONDITION: TYPE_MEMBER {ZONE="REVEALED"}, COST_LE_9 {ZONE="REVEALED"}
EFFECT: MOVE_TO_HAND {FROM="REVEALED"}, POSITION_CHANGE -> SELF
CONDITION: NOT MATCH_PREVIOUS
EFFECT: MOVE_TO_DISCARD {FROM="REVEALED"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  〜でないなら MOVED_THIS_TURN
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ブレードを2得る  → 対象： 自分

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  REVEAL_CARDS(1)  (FROM=DECK_TOP)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  TYPE_MEMBER  (ZONE=REVEALED), COST_LE_9  (ZONE=REVEALED)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  MOVE_TO_HAND  (FROM=REVEALED), POSITION_CHANGE  → 対象： このカード
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  〜でないなら MATCH_PREVIOUS
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを控え室に置く  (FROM=REVEALED)

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If NOT MOVED_THIS_TURN
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Gain 2 Blade(s)  targeting  Player

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  REVEAL_CARDS(1)  (From=DECK_TOP)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  TYPE_MEMBER  (Zone=REVEALED), COST_LE_9  (Zone=REVEALED)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  MOVE_TO_HAND  (From=REVEALED), POSITION_CHANGE  targeting  This Card
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If NOT MATCH_PREVIOUS
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Discard  card(s)  (From=REVEALED)

---

## PL!N-pb1-008-P＋: エマ・ヴェルデ
**Original Japanese:**
{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。
{{toujyou.png|登場}}自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {MIN=1, FILTER="GROUP_ID=3, TAPPED"}
EFFECT: REDUCE_COST(2) -> SELF

TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> PLAYER
  OPTION: メンバー | EFFECT: ACTIVATE_MEMBER(1) -> PLAYER
  OPTION: エネルギー | EFFECT: ACTIVATE_ENERGY(2) -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_STAGE  (最小=レッド, フィルタ=GROUP_ID=3, ウェイト状態)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  REDUCE_COST(2)  → 対象： このカード

### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  モードを選択する  → 対象： 自分
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  メンバー | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人をアクティブにする  → 対象： 自分
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  エネルギー | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  エネルギー2をアクティブにする  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_STAGE  (Min=1, Filter=GROUP_ID=3, Rested)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Cost -2  targeting  This Card

### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a mode  targeting  Player
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  メンバー | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Activate 1 Member(s)  targeting  Player
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  エネルギー | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Activate 2 Energy  targeting  Player

---

## PL!S-bp2-004-P: 黒澤ダイヤ
**Original Japanese:**
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_REVEAL (Once per turn)
CONDITION: NOT REVEALED_CONTAINS {TYPE_LIVE}
EFFECT: ACTION_YELL_MULLIGAN
```

**Friendly Japanese (Verification Mode):**
### ステップ  エールで公開された時 (Once per turn)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  〜でないなら REVEALED_CONTAINS  (TYPE_LIVE)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  エールのやり直しを行う

**Friendly English (Internal Audit Mode):**
### Step  When Revealed by Yell (Once per turn)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If NOT REVEALED_CONTAINS  (Live card)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Perform Yell Mulligan

---

## PL!S-bp2-004-R: 黒澤ダイヤ
**Original Japanese:**
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_REVEAL (Once per turn)
CONDITION: NOT REVEALED_CONTAINS {TYPE_LIVE}
EFFECT: ACTION_YELL_MULLIGAN
```

**Friendly Japanese (Verification Mode):**
### ステップ  エールで公開された時 (Once per turn)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  〜でないなら REVEALED_CONTAINS  (TYPE_LIVE)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  エールのやり直しを行う

**Friendly English (Internal Audit Mode):**
### Step  When Revealed by Yell (Once per turn)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  If NOT REVEALED_CONTAINS  (Live card)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Perform Yell Mulligan

---

## PL!S-bp2-008-P: 小原鞠莉
**Original Japanese:**
{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。
{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを＋１する。ライブカードが3枚以上ある場合、代わりに合計スコアを＋２する。」を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DECK(1) {FROM="DISCARD", TYPE_LIVE} -> DECK_BOTTOM

TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_STAGE {MIN=3, AREA="STAGE", FILTER="Aqours", UNIQUE_NAME=TRUE}
EFFECT: BOOST_SCORE(1) {CONDITION="REVEALED_COUNT {MIN=1, TYPE_LIVE}"}; BOOST_SCORE(2) {CONDITION="REVEALED_COUNT {MIN=3, TYPE_LIVE}"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  MOVE_TO_DECK(1)  (FROM=控え室, TYPE_LIVE)  → 対象： DECK_BOTTOM

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_STAGE  (最小=グリーン, AREA=ステージ, フィルタ=Aqours, UNIQUE_NAME=TRUE)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  スコアを＋1する  (&nbsp;&nbsp;&nbsp;&nbsp;**条件:**=REVEALED_COUNT {MIN=1, TYPE_LIVE)"}; スコアを＋2する  (&nbsp;&nbsp;&nbsp;&nbsp;**条件:**=REVEALED_COUNT {MIN=3, TYPE_LIVE)"}

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Move 1 card(s) back to Deck  (From=Discard Pile, Live card)  targeting  DECK_BOTTOM

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_STAGE  (Min=3, Location=Stage, Filter=Aqours, UNIQUE_NAME=Yes)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Add 1 to Live Score  (&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**=REVEALED_COUNT {MIN=1, Live card)"}; Add 2 to Live Score  (&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**=REVEALED_COUNT {MIN=3, Live card)"}

---

## PL!S-bp2-024-L: 君のこころは輝いてるかい？
**Original Japanese:**
{{jyouji.png|常時}}このカードは成功ライブカード置き場に置くことができない。
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE -> SELF

TRIGGER: ON_LIVE_SUCCESS
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(1) -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  成功ライブに置くことができない  → 対象： このカード

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを2枚引く  → 対象： 自分; 手札を1枚控え室に置く  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Cannot be placed in Success Area  targeting  This Card

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw 2 card(s)  targeting  Player; Discard 1 card(s) from Hand  targeting  Player

---

## PL!S-bp3-007-P: 国木田花丸
**Original Japanese:**
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く。そうした場合、自分はカードを1枚引く。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ACTIVATED
CONDITION: TURN_1
COST: PAY_ENERGY(1)
EFFECT: SELECT_PLAYER(1) -> TARGET; MOVE_TO_DECK(1) {FILTER="TYPE_LIVE", FROM="DISCARD", TO="DECK_BOTTOM", PLAYER="TARGET"}
EFFECT: DRAW(1)
```

**Friendly Japanese (Verification Mode):**
### ステップ  起動
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  ターン1回
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  エネルギーを1支払う
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SELECT_PLAYER(1)  → 対象： TARGET; MOVE_TO_DECK(1)  (フィルタ=TYPE_LIVE, FROM=控え室, TO=DECK_BOTTOM, 自分=TARGET)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを1枚引く

**Friendly English (Internal Audit Mode):**
### Step  When Activated
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  Once per turn
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Pay 1 Energy
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a Player  targeting  TARGET; Move 1 card(s) back to Deck  (Filter=Live card, From=Discard Pile, TO=DECK_BOTTOM, Player=Target)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw 1 card(s)

---

## PL!S-bp3-019-L: MIRACLE WAVE
**Original Japanese:**
{{live_success.png|ライブ成功時}}このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、このカードのスコアは４になる。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: COUNT_YELL_REVEALED {MIN=0, FILTER="NOT_HAS_BLADE_HEART"}
CONDITION: EXTRA_HEARTS {MIN=2}
EFFECT: SET_SCORE(4) -> SELF {MODE="OR"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_YELL_REVEALED  (最小=ピンク, フィルタ=NOT_HAS_BLADE_HEART)
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  EXTRA_HEARTS  (最小=イエロー)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SET_SCORE(4)  → 対象： このカード  (モード=OR)

**Friendly English (Internal Audit Mode):**
### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_YELL_REVEALED  (Min=0, Filter=NOT_HAS_BLADE_HEART)
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  EXTRA_HEARTS  (Min=2)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Set Live Score to 4  targeting  This Card  (Mode=OR)

---

## PL!S-bp3-020-L: ダイスキだったらダイジョウブ！
**Original Japanese:**
{{jidou.png|自動}}［ターン1回］エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい。そのエールで得たブレードハートを失い、もう一度エールを行う。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_REVEAL
CONDITION: TURN_1, COUNT_YELL_REVEALED {MAX=2, FILTER="HAS_BLADE_HEART"}
EFFECT: MOVE_TO_DISCARD(ALL) {ZONE="YELL_REVEALED"}; RESET_YELL_HEARTS; TRIGGER_YELL_AGAIN
```

**Friendly Japanese (Verification Mode):**
### ステップ  エールで公開された時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  ターン1回, COUNT_YELL_REVEALED  (最大=イエロー, フィルタ=HAS_BLADE_HEART)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードALLを控え室に置く  (ZONE=YELL_REVEALED); エールのハートをリセットする; もう一度エールを行う

**Friendly English (Internal Audit Mode):**
### Step  When Revealed by Yell
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  Once per turn, COUNT_YELL_REVEALED  (Max=2, Filter=HAS_BLADE_HEART)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Discard ALL card(s)  (Zone=YELL_REVEALED); Reset Hearts gained from Yell; Trigger Yell again

---

## PL!S-bp3-024-L: Deep Resonance
**Original Japanese:**
{{live_start.png|ライブ開始時}}自分のステージのセンターエリアにコスト9以上の『Aqours』のメンバーがいる場合、以下から1つを選ぶ。
・ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
CONDITION: HAS_MEMBER {FILTER="GROUP_ID=1, COST_GE=9", AREA="CENTER"}
EFFECT: SELECT_MODE(1)
  OPTION: ブレード | EFFECT: SELECT_MEMBER(1) -> TARGET; ADD_BLADES(2) -> TARGET
  OPTION: ウェイト | EFFECT: TAP_MEMBER(1) {TARGET="OPPONENT", FILTER="COST_LE_4"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  HAS_MEMBER  (フィルタ=GROUP_ID=1, COST_GE=9, AREA=CENTER)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  モードを選択する
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ブレード | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人を選ぶ  → 対象： TARGET; ブレードを2得る  → 対象： TARGET
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ウェイト | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  自分のメンバー1人をウェイトにする  (TARGET=相手, フィルタ=コスト 4以下)

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  HAS_MEMBER  (Filter=GROUP_ID=1, COST_GE=9, Location=CENTER)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select a mode
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ブレード | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 Member(s)  targeting  TARGET; Gain 2 Blade(s)  targeting  TARGET
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ウェイト | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Rest 1 of your members  (Target=Opponent, Filter=Cost <= 4)

---

## PL!S-pb1-002-P＋: 桜内梨子
**Original Japanese:**
{{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: OPPONENT_CHOICE
  OPTION: ディスカード | COST: DISCARD_HAND(1) {TYPE_LIVE, TARGET="OPPONENT"}
  OPTION: スコア増加 | EFFECT: GRANT_ABILITY(SELF, "TRIGGER: CONSTANT\nEFFECT: BOOST_SCORE(1) -> PLAYER")
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  OPPONENT_CHOICE
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  ディスカード | &nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  手札を1枚控え室に置く  (TYPE_LIVE, TARGET=相手)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:**  スコア増加 | &nbsp;&nbsp;&nbsp;&nbsp;**効果:**  GRANT_ABILITY(このカード, "### ステップ  常時\nEFFECT スコアを＋1する  → 対象： 自分")

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  OPPONENT_CHOICE
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  ディスカード | &nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Hand  (Live card, Target=Opponent)

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:**  スコア増加 | &nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Grant new ability This Card, "### Step  Always Active\nEFFECT Add 1  targeting  Player" to Live Score

---

## PL!S-pb1-003-P＋: 松浦果南
**Original Japanese:**
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、このメンバーが元々持つハートはすべて{{heart_04.png|heart04}}になる。{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚手札に加える。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(2)
EFFECT: TRANSFORM_HEART(ALL) -> COLOR_GREEN

TRIGGER: ON_LIVE_SUCCESS
EFFECT: RECOVER_LIVE(1) {ZONE="YELL_REVEALED"} -> CARD_HAND
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  エネルギーを2支払う
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  TRANSFORM_HEART(ALL)  → 対象： COLOR_GREEN

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からライブカードを1枚手札に加える  (ZONE=YELL_REVEALED)  → 対象： 手札

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Pay 2 Energy
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Change Heart type to ALL  targeting  COLOR_GREEN

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Live(s) from Discard  (Zone=YELL_REVEALED)  targeting  Hand

---

## PL!S-pb1-019-L: 元気全開DAY！DAY！DAY！
**Original Japanese:**
{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
CONDITION: SUM_HEARTS {FILTER="GROUP_ID=1, HEART_TYPE=2", MIN=6}
EFFECT: NEGATE_EFFECT(SELF, TRIGGER="ON_LIVE_SUCCESS")

TRIGGER: ON_LIVE_SUCCESS
EFFECT: ENERGY_CHARGE(1, MODE="WAIT", TARGET="OPPONENT") -> OPPONENT
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  SUM_HEARTS  (フィルタ=GROUP_ID=1, HEART_TYPE=2, 最小=6)

&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  NEGATE_EFFECT(このカード, ### ステップ ="ライブ成功時")

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  ENERGY_CHARGE(1, MODE="WAIT", TARGET="相手")  → 対象： 相手

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  SUM_HEARTS  (Filter=GROUP_ID=1, HEART_TYPE=2, Min=6)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Negate an effect

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Charge 1, MODE="WAIT", TARGET="Opponent" Energy  targeting  Opponent

---

## PL!S-pb1-022-L: 逃走迷走メビウスループ
**Original Japanese:**
{{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き場にカードを置くことができない。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  SCORE_EQUAL_OPPONENT
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  成功ライブに置くことができない  (TARGET=自分と相手)

**Friendly English (Internal Audit Mode):**
### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  SCORE_EQUAL_OPPONENT
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Cannot be placed in Success Area  (Target=Both Players)

---

## PL!S-pb1-022-L＋: 逃走迷走メビウスループ
**Original Japanese:**
{{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き場にカードを置くことができない。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: SCORE_EQUAL_OPPONENT
EFFECT: PREVENT_SET_TO_SUCCESS_PILE {TARGET="BOTH"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  SCORE_EQUAL_OPPONENT
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  成功ライブに置くことができない  (TARGET=自分と相手)

**Friendly English (Internal Audit Mode):**
### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  SCORE_EQUAL_OPPONENT
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Cannot be placed in Success Area  (Target=Both Players)

---

## PL!SP-bp1-001-P: 澁谷かのん
**Original Japanese:**
{{jyouji.png|常時}}自分のステージにほかのメンバーがいない場合、自分はライブできない。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
CONDITION: COUNT_STAGE {MAX=0, TARGET="OTHER_MEMBER"}
EFFECT: PREVENT_LIVE -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_STAGE  (最大=ピンク, TARGET=それ以外のメンバー)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  PREVENT_LIVE  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_STAGE  (Max=0, Target=Other Member)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Prevent starting a Live  targeting  Player

---

## PL!SP-bp1-024-L: Tiny Stars
**Original Japanese:**
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる「澁谷かのん」1人は{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を、「唐可可」1人は{{heart_01.png|heart01}}{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。

(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {NAME="澁谷かのん", ZONE="STAGE"} -> TARGET_1; ADD_HEARTS(1) {HEART_TYPE=4, TARGET="TARGET_1", DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_1 {DURATION="UNTIL_LIVE_END"}
EFFECT: SELECT_MEMBER(1) {NAME="唐可可", ZONE="STAGE"} -> TARGET_2; ADD_HEARTS(1) {HEART_TYPE=0, TARGET="TARGET_2", DURATION="UNTIL_LIVE_END"}; ADD_BLADES(1) -> TARGET_2 {DURATION="UNTIL_LIVE_END"}
EFFECT: META_RULE {TYPE="ALL_BLADE_AS_ANY_HEART"} -> PLAYER

TRIGGER: ON_LIVE_SUCCESS
CONDITION: HAS_MEMBER {NAME="澁谷かのん"}, HAS_MEMBER {NAME="唐可可"}
EFFECT: DRAW(1) -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人を選ぶ  (カード名=澁谷かのん, ZONE=ステージ)  → 対象： TARGET_1; ハートを1得る  (ハートの色=ブルー, TARGET=対象1, DURATION=ライブ終了時まで); ブレードを1得る  → 対象： TARGET_1  (DURATION=ライブ終了時まで)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人を選ぶ  (カード名=唐可可, ZONE=ステージ)  → 対象： TARGET_2; ハートを1得る  (ハートの色=ピンク, TARGET=対象2, DURATION=ライブ終了時まで); ブレードを1得る  → 対象： TARGET_2  (DURATION=ライブ終了時まで)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  [特殊ルール]  (種類=ALLブレードを任意のハートとして扱う)  → 対象： 自分

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  HAS_MEMBER  (カード名=澁谷かのん), HAS_MEMBER  (カード名=唐可可)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを1枚引く  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 Member(s)  (Name=澁谷かのん, Zone=Stage)  targeting  TARGET_1; Gain 1 Heart(s)  (Heart Color=4, Target=Target 1, Duration=Until Live Ends); Gain 1 Blade(s)  targeting  TARGET_1  (Duration=Until Live Ends)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 Member(s)  (Name=唐可可, Zone=Stage)  targeting  TARGET_2; Gain 1 Heart(s)  (Heart Color=0, Target=Target 2, Duration=Until Live Ends); Gain 1 Blade(s)  targeting  TARGET_2  (Duration=Until Live Ends)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  [Special Rule ]  (Type=ALL-Blade counts as Any Color)  targeting  Player

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  HAS_MEMBER  (Name=澁谷かのん), HAS_MEMBER  (Name=唐可可)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw 1 card(s)  targeting  Player

---

## PL!SP-bp1-026-L: 未来予報ハレルヤ！
**Original Japanese:**
{{live_start.png|ライブ開始時}}自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}になる。

(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
CONDITION: COUNT_UNIQUE_NAMES {MIN=5, FILTER="GROUP_ID=3", AREA="STAGE_OR_DISCARD"}
EFFECT: SET_HEART_REQ {HEART_LIST=[2,2,3,3,6,6]} -> SELF
EFFECT: META_RULE {TYPE="ALL_BLADE_AS_ANY_HEART"} -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_UNIQUE_NAMES  (最小=パープル, フィルタ=GROUP_ID=3, AREA=STAGE_OR_DISCARD)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  必要ハートをに変更する  (ハートの色リスト=[2, イエロー, グリーン, グリーン, 6, 6])  → 対象： このカード
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  [特殊ルール]  (種類=ALLブレードを任意のハートとして扱う)  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_UNIQUE_NAMES  (Min=5, Filter=GROUP_ID=3, Location=Stage or Discard Pile)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Change required Hearts to   (Heart Colors=[2, 2, 3, 3, 6, 6])  targeting  This Card
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  [Special Rule ]  (Type=ALL-Blade counts as Any Color)  targeting  Player

---

## PL!SP-bp2-006-P: 桜小路きな子
**Original Japanese:**
{{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。
({{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。)

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
CONDITION: BATON_TOUCH
EFFECT: RECOVER_MEMBER(1) {ZONE="BATON_REPLACED", FILTER="GROUP_ID=3"} -> CARD_HAND

TRIGGER: ACTIVATED
CONDITION: TURN_1
COST: DISCARD_HAND(1) {FILTER="GROUP_ID=3, COST_LE=4"} -> TARGET_MEMBER
EFFECT: TRIGGER_REMOTE(TARGET_MEMBER, TRIGGER="ON_PLAY")
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  BATON_TOUCH
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からメンバーを1枚手札に加える  (ZONE=BATON_REPLACED, フィルタ=GROUP_ID=3)  → 対象： 手札

### ステップ  起動
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  ターン1回
&nbsp;&nbsp;&nbsp;&nbsp;**コスト:**  手札を1枚控え室に置く  (フィルタ=GROUP_ID=3, COST_LE=4)  → 対象： TARGET_MEMBER

&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  TRIGGER_REMOTE(TARGET_MEMBER, ### ステップ ="登場時")

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  BATON_TOUCH
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Member(s) from Discard  (Zone=BATON_REPLACED, Filter=GROUP_ID=3)  targeting  Hand

### Step  When Activated
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  Once per turn
&nbsp;&nbsp;&nbsp;&nbsp;**Cost:**  Discard 1 card(s) from Hand  (Filter=GROUP_ID=3, COST_LE=4)  targeting  Target Member
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Trigger an ability remotely

---

## PL!SP-bp2-010-P: ウィーン・マルガレーテ
**Original Japanese:**
{{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。
{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
EFFECT: INCREASE_HEART_COST(1) {HEART_TYPE=0, TARGET="OPPONENT_LIVE"}

TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1, TARGET="OTHER_MEMBER"}
EFFECT: REDUCE_YELL_COUNT(8) -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  INCREASE_HEART_COST(1)  (ハートの色=ピンク, TARGET=OPPONENT_LIVE)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  COUNT_STAGE  (最小=レッド, TARGET=それ以外のメンバー)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  REDUCE_YELL_COUNT(8)  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Heart Cost +1  (Heart Color=0, Target=OPPONENT_LIVE)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  COUNT_STAGE  (Min=1, Target=Other Member)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Reduce required Energy for Yell  targeting  Player

---

## PL!SP-bp4-004-P: 平安名すみれ
**Original Japanese:**
{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。
{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。

**Compiled Logic (Pseudocode):**
```
TRIGGER: CONSTANT
EFFECT: BATON_TOUCH_MOD(2) -> SELF

TRIGGER: ON_PLAY
CONDITION: AREA="CENTER", BATON_COUNT(2) {FILTER="GROUP_ID=3"}
EFFECT: DRAW(2) -> PLAYER; PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=3, COST_LE=4"}
```

**Friendly Japanese (Verification Mode):**
### ステップ  常時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  BATON_TOUCH_MOD(2)  → 対象： このカード

### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  AREA="CENTER", BATON_COUNT(2)  (フィルタ=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  カードを2枚引く  → 対象： 自分; 控え室からメンバー1枚を登場させる  (フィルタ=GROUP_ID=3, COST_LE=4)

**Friendly English (Internal Audit Mode):**
### Step  Always Active
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Modify Baton Touch condition  targeting  This Card

### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  AREA="CENTER", BATON_COUNT(2)  (Filter=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Draw 2 card(s)  targeting  Player; Play a Member from Discard  (Filter=GROUP_ID=3, COST_LE=4)

---

## PL!SP-bp4-023-L: Dazzling Game
**Original Japanese:**
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「澁谷かのん」「ウィーン・マルガレーテ」「鬼塚冬毬」のうちのメンバー1人と、これにより選んだメンバー以外の『Liella!』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。
{{live_start.png|ライブ開始時}}ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[紫ブレード]になる。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) {NAME_IN=['澁谷かのん', 'ウィーン·マルガレーテ', '鬼塚冬毬']} -> TARGET_1; SELECT_MEMBER(1) {FILTER="GROUP_ID=3", NOT_TARGET="TARGET_1"} -> TARGET_2; ADD_BLADES(1) -> PLAYER {TARGET="TARGET_1"}; ADD_BLADES(1) -> PLAYER {TARGET="TARGET_2"}
EFFECT: TRANSFORM_COLOR(ALL) -> COLOR_PURPLE
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人を選ぶ  (NAME_IN=['澁谷かのん', 'ウィーン·マルガレーテ', '鬼塚冬毬'])  → 対象： TARGET_1; メンバー1人を選ぶ  (フィルタ=GROUP_ID=3, NOT_TARGET=対象1)  → 対象： TARGET_2; ブレードを1得る  → 対象： 自分  (TARGET=対象1); ブレードを1得る  → 対象： 自分  (TARGET=対象2)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  TRANSFORM_COLOR(ALL)  → 対象： COLOR_PURPLE

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 Member(s)  (NAME_IN=['澁谷かのん', 'ウィーン·マルガレーテ', '鬼塚冬毬'])  targeting  TARGET_1; Select 1 Member(s)  (Filter=GROUP_ID=3, NOT_TARGET=Target 1)  targeting  TARGET_2; Gain 1 Blade(s)  targeting  Player  (Target=Target 1); Gain 1 Blade(s)  targeting  Player  (Target=Target 2)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Change color to ALL  targeting  COLOR_PURPLE

---

## PL!SP-bp4-025-L: Special Color
**Original Japanese:**
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ{{icon_blade.png|ブレード}}の数は3つになる。
{{live_success.png|ライブ成功時}}自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを＋１する。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_START
EFFECT: SET_BLADES(3) {TARGET="CENTER", FILTER="GROUP_ID=3"}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: AREA="CENTER", HAS_MOVED_THIS_TURN
EFFECT: BOOST_SCORE(1) -> SELF
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SET_BLADES(3)  (TARGET=CENTER, フィルタ=GROUP_ID=3)

### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  AREA="CENTER", HAS_MOVED_THIS_TURN
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  スコアを＋1する  → 対象： このカード

**Friendly English (Internal Audit Mode):**
### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Set Blades to 3  (Target=CENTER, Filter=GROUP_ID=3)

### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  AREA="CENTER", HAS_MOVED_THIS_TURN
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Add 1 to Live Score  targeting  This Card

---

## PL!SP-bp4-027-L: Chance Day, Chance Way!
**Original Japanese:**
{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。(メンバーをそれぞれ好きなエリアに移動させる。この効果で1つのエリアに2人以上のメンバーを移動させることはできない。)

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_LIVE_SUCCESS
CONDITION: ALL_MEMBER {FILTER="GROUP_ID=3"}
EFFECT: FORMATION_CHANGE -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  ライブ成功時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  ALL_MEMBER  (フィルタ=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  FORMATION_CHANGE  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  When Live Succeeds
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  ALL_MEMBER  (Filter=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Change Formation  targeting  Player

---

## PL!SP-bp5-001-P: N/A
**Original Japanese:**
N/A

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
CONDITION: HAS_LIVE_SET {FILTER="GROUP_ID=4, NOT_NAME=Dream Believers"}
EFFECT: RECOVER_MEMBER(1) {FILTER="GROUP_ID=4"} -> CARD_HAND

TRIGGER: ON_LIVE_START
EFFECT: SELECT_CARDS(1) {FROM="DISCARD", FILTER="GROUP_ID=4, COST_LE=4"}
EFFECT: GRANT_HEARTS {PER_CARD="REVEALED"} -> PLAYER
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  HAS_LIVE_SET  (フィルタ=GROUP_ID=4, NOT_NAME=Dream Believers)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  控え室からメンバーを1枚手札に加える  (フィルタ=GROUP_ID=4)  → 対象： 手札

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SELECT_CARDS(1)  (FROM=控え室, フィルタ=GROUP_ID=4, COST_LE=4)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  GRANT_HEARTS  (（〜の枚数につき）=REVEALED)  → 対象： 自分

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  HAS_LIVE_SET  (Filter=GROUP_ID=4, NOT_NAME=Dream Believers)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Retrieve 1 Member(s) from Discard  (Filter=GROUP_ID=4)  targeting  Hand

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 card(s)  (From=Discard Pile, Filter=GROUP_ID=4, COST_LE=4)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Grant  Hearts  (for each card in=REVEALED)  targeting  Player

---

## PL!SP-bp5-011-P: N/A
**Original Japanese:**
N/A

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
EFFECT: PLAY_MEMBER_FROM_HAND(1) {ZONE="DISCARD", FILTER="COST_LE=4"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_MEMBER(1) -> TARGET_MEMBER; ADD_HEARTS(TARGET_MEMBER) {HEART_TYPE=4}
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  PLAY_MEMBER_FROM_HAND(1)  (ZONE=控え室, フィルタ=COST_LE=4)

### ステップ  ライブ開始時
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  メンバー1人を選ぶ  → 対象： TARGET_MEMBER; ハートをTARGET_MEMBER得る  (ハートの色=ブルー)

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Play a Member from Hand  (Zone=Discard Pile, Filter=COST_LE=4)

### Step  When Live Starts
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Select 1 Member(s)  targeting  Target Member; Gain Target Member Heart(s)  (Heart Color=4)

---

## PL!SP-pb1-003-P＋: 嵐 千砂都
**Original Japanese:**
{{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる。

**Compiled Logic (Pseudocode):**
```
TRIGGER: ON_PLAY
CONDITION: ALL_MEMBER {FILTER="GROUP_ID=3"}
EFFECT: SWAP_AREA(ALL, MODE="CYCLE") -> BOTH_PLAYERS
```

**Friendly Japanese (Verification Mode):**
### ステップ  登場時
&nbsp;&nbsp;&nbsp;&nbsp;**条件:**  ALL_MEMBER  (フィルタ=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**効果:**  SWAP_AREA(ALL, MODE="CYCLE")  → 対象： BOTH_PLAYERS

**Friendly English (Internal Audit Mode):**
### Step  When Played
&nbsp;&nbsp;&nbsp;&nbsp;**Condition:**  ALL_MEMBER  (Filter=GROUP_ID=3)
&nbsp;&nbsp;&nbsp;&nbsp;**Effect:**  Swap card positions  targeting  BOTH_PLAYERS

---

## Generator Source Code
This report was automatically generated using the following script:

```python
import json
import os
import re

def generate_audit_report():
    cards_path = 'data/cards.json'
    pseudo_path = 'data/manual_pseudocode.json'
    output_path = 'docs/audit_report.md'

    with open(cards_path, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    with open(pseudo_path, 'r', encoding='utf-8') as f:
        pseudo = json.load(f)

    candidate_cards = [
        "PL!-pb1-009-P＋", "PL!-pb1-009-R", "PL!HS-bp2-019-L", "PL!HS-bp2-020-L",
        "PL!N-bp4-010-P", "PL!N-bp4-010-P＋", "PL!N-bp4-010-R＋", "PL!N-bp4-010-SEC",
        "PL!N-bp4-026-L", "PL!S-bp2-004-P", "PL!S-bp2-004-R", "PL!S-bp2-024-L",
        "PL!S-bp3-020-L", "PL!S-pb1-022-L", "PL!S-pb1-022-L＋", "PL!SP-bp1-024-L",
        "PL!SP-bp1-026-L", "PL!N-bp4-007-P", "PL!N-bp3-008-P", "PL!N-pb1-004-P＋",
        "PL!-bp3-024-L", "PL!SP-bp4-004-P", "PL!-bp3-006-P", "PL!N-bp3-017-N",
        "PL!N-bp4-011-P", "LL-PR-004-PR", "PL!N-bp3-005-P", "PL!S-pb1-019-L",
        "PL!SP-bp4-027-L", "PL!S-pb1-002-P＋", "PL!SP-bp5-001-P", "PL!-bp4-008-P",
        "PL!N-bp4-027-L", "LL-bp4-001-R＋", "PL!-bp4-005-P", "PL!S-bp2-008-P",
        "PL!N-bp4-004-P", "PL!HS-bp2-018-N", "PL!N-bp1-002-P", "PL!SP-bp5-011-P",
        "PL!SP-bp1-001-P", "PL!HS-bp2-007-P", "PL!N-pb1-008-P＋", "PL!-pb1-030-L",
        "PL!SP-bp2-010-P", "PL!-pb1-001-P＋", "PL!S-bp3-007-P", "PL!SP-bp4-025-L",
        "PL!S-bp3-019-L", "PL!SP-pb1-003-P＋", "PL!S-bp3-024-L", "PL!SP-bp4-023-L",
        "PL!S-pb1-003-P＋", "PL!SP-bp2-006-P"
    ]
    candidate_cards = sorted(list(set(candidate_cards)))

    char_names_jp = {
        "Honoka": "高坂 穂乃果", "Umi": "園田 海未", "Kotori": "南 ことり",
        "Hanayo": "小泉 花陽", "Rin": "星空 凛", "Maki": "西木野 真姫",
        "Eli": "絢瀬 絵里", "Nozomi": "東條 希", "Nico": "矢澤 にこ",
        "Chika": "高海 千歌", "Riko": "桜内 梨子", "Kanan": "松浦 果南",
        "Dia": "黒澤 ダイヤ", "You": "渡辺 曜", "Yoshiko": "津島 善子",
        "Hanamaru": "国木田 花丸", "Mari": "小原 鞠莉", "Ruby": "黒澤 ルビィ",
        "Ayumu": "上原 歩夢", "Kasumi": "中須 かすみ", "Shizuku": "桜坂 しずく",
        "Karin": "朝香 果林", "Ai": "宮下 愛", "Kanata": "近江 彼方",
        "Setsuna": "優木 せつ菜", "Emma": "エマ・ヴェルデ", "Rina": "天王寺 璃奈",
        "Shioriko": "三船 栞子", "Lanzhu": "鐘 嵐珠", "Mia": "ミア・テイラー",
        "Kanon": "澁谷 かのん", "Keke": "唐 可可", "Chisato": "嵐 千砂都",
        "Sumire": "平安名 すみれ", "Ren": "葉月 恋", "Kinako": "桜小路 きな子",
        "Mei": "米女 メイ", "Shiki": "若菜 四季", "Natsumi": "鬼塚 夏美",
        "Eri": "絢瀬 絵里"
    }

    maps = {
        "en": {
            "attrs": {
                "FILTER": "Filter", "MIN": "Min", "MAX": "Max", "COUNT": "Count",
                "PER_CARD": "for each card in", "PER_ENERGY": "for each energy in",
                "UNIT_HASU": "Hasunosora", "UNIT_LIEL": "Liella!", "UNIT_NIJI": "Nijigasaki",
                "UNIT_AQOURS": "Aqours", "UNIT_MUSES": "μ's", "UNIQUE_NAMES": "with unique names",
                "STAGE": "Stage", "DISCARD": "Discard Pile", "HAND": "Hand",
                "SUCCESS_LIVE": "Success Area", "NEXT_TURN": "Next Turn", "NAME": "Name",
                "GROUP_ID": "Group", "ZONE": "Zone", "HEART_TYPE": "Heart Color",
                "ANY": "Any", "PINK": "Pink", "RED": "Red", "YELLOW": "Yellow",
                "GREEN": "Green", "BLUE": "Blue", "PURPLE": "Purple",
                "COST_LE_REVEALED": "Cost <= Revealed Card", "BLADE_LE_3": "Blades <= 3",
                "BLADE_LE_2": "Blades <= 2", "BLADE_LE_1": "Blades <= 1", "STAGE_OR_DISCARD": "Stage or Discard Pile",
                "TYPE_LIVE": "Live card", "PLAYER": "Player", "OPPONENT": "Opponent", "SELF": "This Card",
                "TARGET": "Target", "TARGET_MEMBER": "Target Member", "BOTH": "Both Players",
                "SCORE_TOTAL": "Total Score", "COUNT_SUCCESS_LIVE": "Number of cards in Success Area",
                "COUNT_STAGE": "Number of cards on Stage", "COUNT_HAND": "Number of cards in Hand",
                "COUNT_DISCARD": "Number of cards in Discard Pile", "COUNT_ENERGY": "Number of Energy chips",
                "COUNT_UNIQUE_NAMES": "Number of unique member names", "HAS_MEMBER": "If you have specific Member",
                "HAS_COLOR": "If you have specific Color", "IS_CENTER": "If in Center",
                "REVEALED_CONTAINS": "If Revealed cards contain", "SCORE_EQUAL_OPPONENT": "If your score equals opponent's",
                "AREA": "Location", "FROM": "From", "DURATION": "Duration", "UNTIL_LIVE_END": "Until Live Ends",
                "TRUE": "Yes", "FALSE": "No", "ALL": "All", "CARD_HAND": "Hand", "DISCARD_REMAINDER": "Discard Remainder",
                "REMAINDER": "Remainder", "TARGET_1": "Target 1", "TARGET_2": "Target 2", "SUCCESS_SCORE": "Success Score",
                "LIVE_SET": "Live Set", "HEART_LIST": "Heart Colors", "TYPE": "Type",
                "ALL_BLADE_AS_ANY_HEART": "ALL-Blade counts as Any Color", "HEART_COST_REDUCE": "Reduce Heart Requirement",
                "MODE": "Mode", "CENTER_ONLY": "Center Only", "OUT_OF_CENTER": "Out of Center", "NOT": "If NOT", "GROUP": "Group",
                "UNIT_CERISE": "Cerise Bouquet", "UNIT_DOLL": "DOLLCHESTRA", "UNIT_MIRAKURA": "Mira-Cra Park!",
                "UNIT_BIBI": "BiBi", "OPPONENT_HAS_WAIT": "If Opponent has Rested member", "TURN_1": "Once per turn",
                "CHECK_IS_IN_DISCARD": "If in Discard Pile", "IS_MAIN_PHASE": "During Main Phase", "SUCCESS": "If Successful",
                "TAPPED": "Rested", "ACTIVATE_AND_SELF": "Target and This Card", "X": "X", "OTHER_MEMBER": "Other Member"
            },
            "opcodes": {
                "DRAW": "Draw {v} card(s)", "ADD_BLADES": "Gain {v} Blade(s)", "ADD_HEARTS": "Gain {v} Heart(s)",
                "BOOST_SCORE": "Add {v} to Live Score", "SELECT_MODE": "Select a mode",
                "TAP_OPPONENT": "Rest {v} member(s) on stage", "PREVENT_ACTIVATE": "Prevent members from being activated",
                "META_RULE": "[Special Rule: {v}]", "ADD_TAG": "Gain traits ({v})",
                "MOVE_SUCCESS": "Move {v} card(s) to Success Area", "SELECT_LIVE": "Select a Live card",
                "REDUCE_LIVE_SET_LIMIT": "Reduce Live Set limit by {v}", "ACTION_YELL_MULLIGAN": "Perform Yell Mulligan",
                "PREVENT_SET_TO_SUCCESS_PILE": "Cannot be placed in Success Area", "TRIGGER_YELL_AGAIN": "Trigger Yell again",
                "RESET_YELL_HEARTS": "Reset Hearts gained from Yell", "SET_HEART_REQ": "Change required Hearts to {v}",
                "MOVE_TO_DISCARD": "Discard {v} card(s)", "ACTIVATE_ENERGY": "Activate {v} Energy",
                "ACTIVATE_MEMBER": "Activate {v} Member(s)", "BATON_TOUCH_MOD": "Modify Baton Touch condition",
                "BUFF_POWER": "Gain +{v} Power", "CHEER_REVEAL": "Reveal via Cheer", "COLOR_SELECT": "Select a Color",
                "DISCARD_HAND": "Discard {v} card(s) from Hand", "DRAW_UNTIL": "Draw until you have {v} cards",
                "ENERGY_CHARGE": "Charge {v} Energy", "FORMATION_CHANGE": "Change Formation",
                "GRANT_ABILITY": "Grant new ability: {v}", "GRANT_HEARTS": "Grant {v} Hearts",
                "INCREASE_COST": "Cost +{v}", "INCREASE_HEART_COST": "Heart Cost +{v}",
                "LOOK_AND_CHOOSE": "Look at cards and choose {v}", "MOVE_MEMBER": "Move a member on stage",
                "MOVE_TO_DECK": "Move {v} card(s) back to Deck", "NEGATE_EFFECT": "Negate an effect",
                "ORDER_DECK": "Reorder the top {v} cards of Deck", "PLAY_LIVE_FROM_DISCARD": "Play a Live card from Discard",
                "PLAY_MEMBER_FROM_DISCARD": "Play a Member from Discard", "PLAY_MEMBER_FROM_HAND": "Play a Member from Hand",
                "PREVENT_LIVE": "Prevent starting a Live", "RECOVER_LIVE": "Retrieve {v} Live(s) from Discard",
                "RECOVER_MEMBER": "Retrieve {v} Member(s) from Discard", "REDUCE_COST": "Cost -{v}",
                "REDUCE_HEART_REQ": "Reduce Heart requirement by {v}", "REDUCE_YELL_COUNT": "Reduce required Energy for Yell",
                "REVEAL_UNTIL": "Reveal cards until {v}", "SELECT_CARDS": "Select {v} card(s)",
                "SELECT_PLAYER": "Select a Player", "SET_BLADES": "Set Blades to {v}",
                "SET_SCORE": "Set Live Score to {v}", "SWAP_AREA": "Swap card positions",
                "TRANSFORM_COLOR": "Change color to {v}", "TRANSFORM_HEART": "Change Heart type to {v}",
                "TRIGGER_REMOTE": "Trigger an ability remotely", "TAP_MEMBER": "Rest {v} of your members",
                "DISCARD_SUCCESS_LIVE": "Discard {v} card(s) from Success Area",
                "PLAY_LIVE_FROM_HAND": "Play {v} Live card(s) from Hand", "SELECT_MEMBER": "Select {v} Member(s)",
                "LOOK_AND_CHOOSE_ORDER": "Look at {v} cards and reorder", "PAY_ENERGY": "Pay {v} Energy",
                "ACTIVATE_ENERGY": "Activate {v} Energy"
            },
            "steps": {
                "TRIGGER": "### Step: {v}", "CONDITION": "&nbsp;&nbsp;&nbsp;&nbsp;**Condition:** {v}",
                "COST": "&nbsp;&nbsp;&nbsp;&nbsp;**Cost:** {v}", "EFFECT": "&nbsp;&nbsp;&nbsp;&nbsp;**Effect:** {v}",
                "OPTION": "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:** {v}",
                "ON_PLAY": "When Played", "ON_LIVE_START": "When Live Starts", "ON_LIVE_SUCCESS": "When Live Succeeds",
                "CONSTANT": "Always Active", "ACTIVATED": "When Activated", "ON_REVEAL": "When Revealed by Yell",
                "ON_POSITION_CHANGE": "When Position Changes", "TURN_START": "Turn Start", "TURN_END": "Turn End",
                "ON_STAGE_ENTRY": "When member enters Stage"
            }
        },
        "jp": {
            "attrs": {
                "FILTER": "フィルタ", "MIN": "最小", "MAX": "最大", "COUNT": "数",
                "PER_CARD": "（〜の枚数につき）", "PER_ENERGY": "（〜のエネルギーにつき）",
                "STAGE": "ステージ", "DISCARD": "控え室", "HAND": "手札",
                "SUCCESS_LIVE": "成功ライブ", "NAME": "カード名", "GROUP_ID": "グループ",
                "HEART_TYPE": "ハートの色", "ANY": "どの色でもよい", "PINK": "ピンク", "RED": "レッド",
                "YELLOW": "イエロー", "GREEN": "グリーン", "BLUE": "ブルー", "PURPLE": "パープル",
                "PLAYER": "自分", "OPPONENT": "相手", "SELF": "このカード", "BOTH": "自分と相手",
                "SCORE_TOTAL": "合計スコア", "COUNT_SUCCESS_LIVE": "成功ライブの枚数",
                "HAS_MEMBER": "特定のメンバーがいる場合", "NOT": "〜でない場合",
                "SCORE_EQUAL_OPPONENT": "自分と相手のスコアが同じ場合", "ALL": "すべて",
                "UNIT_LIEL": "Liella!", "UNIT_AQOURS": "Aqours", "UNIT_NIJI": "虹ヶ咲", "UNIT_MUSES": "μ's",
                "CARD_HAND": "手札", "DISCARD_REMAINDER": "残りを控え室に", "REMAINDER": "残りのカード",
                "TARGET_1": "対象1", "TARGET_2": "対象2", "UNTIL_LIVE_END": "ライブ終了時まで",
                "SUCCESS_SCORE": "成功時スコア", "LIVE_SET": "セットしたライブ",
                "COST_LE_REVEALED": "公開されたカードのコスト以下", "BLADE_LE_3": "ブレード数が3以下",
                "BLADE_LE_2": "ブレード数が2以下", "BLADE_LE_1": "ブレード数が1以下",
                "HEART_LIST": "ハートの色リスト", "TYPE": "種類", "ALL_BLADE_AS_ANY_HEART": "ALLブレードを任意のハートとして扱う",
                "HEART_COST_REDUCE": "必要ハートを減らす", "SCORE_TOTAL": "合計スコア",
                "MODE": "モード", "CENTER_ONLY": "センター限定", "OUT_OF_CENTER": "センター以外へ", "NOT": "〜でないなら", "GROUP": "協力体制",
                "UNIT_CERISE": "スリーズブーケ", "UNIT_DOLL": "DOLLCHESTRA", "UNIT_MIRAKURA": "みらくらぱーく！",
                "UNIT_BIBI": "BiBi", "OPPONENT_HAS_WAIT": "相手にウェイト状態のメンバーがいる場合", "TURN_1": "ターン1回",
                "CHECK_IS_IN_DISCARD": "控え室にいる場合", "IS_MAIN_PHASE": "メインフェイズの場合", "IS_CENTER": "センターの場合",
                "SUCCESS": "成功した場合", "TAPPED": "ウェイト状態", "ACTIVATE_AND_SELF": "アクティブにしたメンバーとこのカード",
                "X": "X", "OTHER_MEMBER": "それ以外のメンバー", "0": "ピンク", "1": "レッド", "2": "イエロー", "3": "グリーン", "4": "ブルー", "5": "パープル"
            },
            "opcodes": {
                "DRAW": "カードを{v}引く", "ADD_BLADES": "ブレードを{v}得る", "ADD_HEARTS": "ハートを{v}得る",
                "BOOST_SCORE": "スコアを＋{v}する", "SELECT_MODE": "モードを選択する",
                "TAP_OPPONENT": "相手のメンバーを{v}ウェイトにする", "META_RULE": "[特殊ルール: {v}]",
                "MOVE_SUCCESS": "カード{v}を成功ライブに置く", "ACTION_YELL_MULLIGAN": "エールのやり直しを行う",
                "PREVENT_SET_TO_SUCCESS_PILE": "成功ライブに置くことができない", "MOVE_TO_DISCARD": "カード{v}を控え室に置く",
                "DISCARD_HAND": "手札を{v}控え室に置く", "SELECT_MEMBER": "メンバー{v}を選ぶ",
                "LOOK_AND_CHOOSE": "カードを{v}見て選ぶ", "REDUCE_LIVE_SET_LIMIT": "セット上限を-{v}する",
                "SET_HEART_REQ": "必要ハートを{v}に変更する", "BUFF_POWER": "パワーを+{v}する",
                "TRIGGER_YELL_AGAIN": "もう一度エールを行う", "RESET_YELL_HEARTS": "エールのハートをリセットする",
                "SELECT_LIVE": "ライブカードを1枚選ぶ", "INCREASE_COST": "コストを+{v}する",
                "SCORE_TOTAL": "合計スコアをチェックする", "RECOVER_MEMBER": "控え室からメンバーを{v}手札に加える",
                "RECOVER_LIVE": "控え室からライブカードを{v}手札に加える", "REDUCE_HEART_REQ": "必要ハートを-{v}する",
                "ACTIVATE_ENERGY": "エネルギー{v}をアクティブにする", "CHEER_REVEAL": "{v}をエールとして公開する",
                "LOOK_AND_CHOOSE_ORDER": "カードを{v}見て並べ替える", "PAY_ENERGY": "エネルギーを{v}支払う",
                "PLAY_MEMBER_FROM_DISCARD": "控え室からメンバー{v}を登場させる", "ACTIVATE_MEMBER": "メンバー{v}をアクティブにする",
                "ADD_TAG": "属性「{v}」を得る", "REVEAL_UNTIL": "{v}が公開されるまでデッキをめくる", "TAP_MEMBER": "自分のメンバー{v}をウェイトにする",
                "DISCARD_SUCCESS_LIVE": "成功ライブからカードを{v}控え室に置く"
            },
            "steps": {
                "TRIGGER": "### ステップ: {v}", "CONDITION": "&nbsp;&nbsp;&nbsp;&nbsp;**条件:** {v}",
                "COST": "&nbsp;&nbsp;&nbsp;&nbsp;**コスト:** {v}", "EFFECT": "&nbsp;&nbsp;&nbsp;&nbsp;**効果:** {v}",
                "OPTION": "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:** {v}",
                "ON_PLAY": "登場時", "ON_LIVE_START": "ライブ開始時", "ON_LIVE_SUCCESS": "ライブ成功時",
                "CONSTANT": "常時", "ACTIVATED": "起動", "ON_REVEAL": "エールで公開された時",
                "ON_POSITION_CHANGE": "移動した時", "ON_STAGE_ENTRY": "メンバーが登場した時"
            }
        }
    }

    def translate_complex(raw_text, lang):
        if not raw_text or raw_text == "N/A": return "N/A"
        t = maps[lang]
        processed = raw_text

        def handle_patterns(val):
            val = re.sub(r'COST_LE_(\d+)', (lambda m: f"Cost <= {m.group(1)}" if lang == "en" else f"コスト {m.group(1)}以下"), val)
            val = re.sub(r'COST_GE_(\d+)', (lambda m: f"Cost >= {m.group(1)}" if lang == "en" else f"コスト {m.group(1)}以上"), val)
            val = re.sub(r'BLADE_LE_(\d+)', (lambda m: f"Blades <= {m.group(1)}" if lang == "en" else f"ブレード数 {m.group(1)}以下"), val)
            val = re.sub(r'BLADE_GE_(\d+)', (lambda m: f"Blades >= {m.group(1)}" if lang == "en" else f"ブレード数 {m.group(1)}以上"), val)
            # Handle technical terms that might be missed in attribute mapping but appear in direct strings
            if lang == "jp":
                val = val.replace("COST_LE_REVEALED", "公開されたカードのコスト以下")
            return val

        all_logic = {**t["opcodes"], **t["steps"]}
        for k in sorted(all_logic.keys(), key=len, reverse=True):
            replacement = all_logic[k]
            def sub_val(match):
                val = match.group(1).strip()
                if val == "99":
                    readable_val = "すべて" if lang == "jp" else "all"
                elif val.isdigit():
                    if lang == "jp":
                        if k in ["DRAW", "MOVE_SUCCESS", "MOVE_TO_DISCARD", "DISCARD_HAND", "LOOK_AND_CHOOSE", "RECOVER_MEMBER", "RECOVER_LIVE", "PLAY_MEMBER_FROM_DISCARD", "DISCARD_SUCCESS_LIVE"]:
                            readable_val = f"{val}枚"
                        elif k in ["SELECT_MEMBER", "TAP_OPPONENT", "ACTIVATE_MEMBER", "TAP_MEMBER"]:
                            readable_val = f"{val}人"
                        else:
                            readable_val = val
                    else:
                        readable_val = val
                else:
                    readable_val = handle_patterns(val)
                return replacement.replace("{v}", readable_val)
            processed = re.sub(rf'\b{k}\((.*?)\)', sub_val, processed)
            processed = re.sub(rf'\b{k}\b', replacement.replace("{v}", ""), processed)

        words_to_map = ["PLAYER", "OPPONENT", "SELF", "BOTH", "TARGET_MEMBER", "CARD_HAND", "DISCARD_REMAINDER", "SCORE_TOTAL", "NOT", "IS_CENTER", "TURN_1", "OPPONENT_HAS_WAIT", "CHECK_IS_IN_DISCARD", "IS_MAIN_PHASE", "SUCCESS", "TAPPED", "ACTIVATE_AND_SELF", "OTHER_MEMBER"]
        if lang == "jp":
            processed = processed.replace("->", " targeting ")
            for w in words_to_map:
                processed = re.sub(rf'\b{w}\b', t["attrs"].get(w, w), processed)
            processed = processed.replace(" targeting ", " → 対象：")
        else:
            processed = processed.replace("->", " targeting ")
            for w in words_to_map:
                processed = re.sub(rf'\b{w}\b', t["attrs"].get(w, w), processed)

        def sub_attr(match):
            content = match.group(1)
            translated_parts = []
            parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', content)
            for p in parts:
                p = p.strip().strip('"')
                if "=" in p:
                    k_v = p.split("=", 1)
                    if len(k_v) == 2:
                        k, v = k_v[0].strip(), k_v[1].strip().strip('"')
                        v_parts = v.split("/")
                        mapped_v_parts = []
                        for vp in v_parts:
                            vp = vp.strip()
                            if lang == "jp" and k == "FILTER":
                                jp_name = char_names_jp.get(vp, t["attrs"].get(vp, vp))
                                mapped_v_parts.append(handle_patterns(jp_name))
                            else:
                                mapped_v_parts.append(t["attrs"].get(vp, vp))
                        tv = "/".join(mapped_v_parts)
                        tv = handle_patterns(tv)
                        translated_parts.append(f"{t['attrs'].get(k, k)}={tv}")
                    else:
                        translated_parts.append(handle_patterns(t["attrs"].get(k_v[0], k_v[0])))
                else:
                    translated_parts.append(handle_patterns(t["attrs"].get(p, p)))
            return " (" + ", ".join(translated_parts) + ")"
        processed = re.sub(r'\{(.*?)\}', sub_attr, processed)

        if lang == "jp":
            processed = processed.replace("[特殊ルール: ]", "[特殊ルール]")
            processed = processed.replace("Specific Details", "詳細")
            processed = processed.replace("すべて枚", "すべて")
            processed = processed.replace("すべて人", "すべて")

        final_lines = []
        step_key = "### ステップ:" if lang == "jp" else "### Step:"
        for line in [l.strip() for l in processed.split('\n') if l.strip()]:
            final_lines.append(f"\n{line}" if step_key in line else line)
        return "\n".join(final_lines).replace(": ", " ").strip()

    report = "# Logic Robustness Audit Report\n\nGenerated bilingual audit for game logic verification.\n\n"
    for cid in candidate_cards:
        c, p = cards.get(cid, {}), pseudo.get(cid, {})
        report += f"## {cid}: {c.get('name', 'N/A')}\n**Original Japanese:**\n{c.get('ability', 'N/A')}\n\n"
        report += f"**Compiled Logic (Pseudocode):**\n```\n{p.get('pseudocode', 'N/A')}\n```\n\n"
        report += f"**Friendly Japanese (Verification Mode):**\n{translate_complex(p.get('pseudocode', 'N/A'), 'jp')}\n\n"
        report += f"**Friendly English (Internal Audit Mode):**\n{translate_complex(p.get('pseudocode', 'N/A'), 'en')}\n\n---\n\n"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Append the script itself to the report for self-documentation
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            script_content = f.read()
        report += "## Generator Source Code\nThis report was automatically generated using the following script:\n\n```python\n" + script_content + "\n```\n"
    except Exception as e:
        report += f"\n\n> [!WARNING]\n> Could not append generator script: {str(e)}\n"

    with open(output_path, 'w', encoding='utf-8-sig') as f: f.write(report)
    print(f"Report generated: {output_path}")

if __name__ == '__main__':
    generate_audit_report()

```
