# Comprehensive Ability Frame Audit Report

Total abilities analyzed: 614
Total issues found: 64

## Summary by Severity

- **CRITICAL**: 2 issues
- **WARNING**: 38 issues
- **INFO**: 24 issues

## Issues by Type

- MISSING_CONDITIONAL_JUMP: 36
- MISSING_OPTION_NAMES: 24
- WRONG_FRAMES_FOR_SUCCESS_BLADES: 2
- MISSING_FLAVOR_OPTIONS: 1
- INCOMPLETE_FLAVOR_OPTIONS: 1

## Detailed Issues

### CRITICAL Issues (Must Fix)

#### Ability #454 - PL!S-bp2-001-P

**Issue Type:** WRONG_FRAMES_FOR_SUCCESS_BLADES

**Text:** {{jyouji.png|常時}}自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Current Frames:** BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN

**Expected:** Should check success pile count then add blades

**Recommendation:** Replace BATON/COUNT_ENERGY/ENERGY_CHARGE with COUNT_SUCCESS/ADD_BLADES

---

#### Ability #456 - PL!S-pb1-009-P+

**Issue Type:** WRONG_FRAMES_FOR_SUCCESS_BLADES

**Text:** {{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Current Frames:** BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE, RETURN

**Expected:** Should check success pile count then add blades

**Recommendation:** Replace BATON/COUNT_ENERGY/ENERGY_CHARGE with COUNT_SUCCESS/ADD_BLADES

---

### WARNING Issues (Should Fix)

#### Ability #0 - PL!S-bp2-004-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場

**Current Frames:** META_RULE, META_RULE, META_RULE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #2 - PL!S-bp5-013-N

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}自分のライブカード置き場にあるカードの必要ハートに含まれる{{heart_04.png|heart04}}の合計が4以上の場合、ライブ終了時まで、{{

**Current Frames:** DRAW, MOVE_TO_DISCARD, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #6 - PL!HS-bp5-013-N

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{

**Current Frames:** MOVE_TO_DISCARD, DRAW, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #64 - PL!S-bp5-004-AR

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得

**Current Frames:** SELECT_MODE, JUMP, JUMP, ADD_BLADES, JUMP, MOVE_MEMBER, JUMP, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #73 - PL!SP-bp5-010-AR

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}自分と相手は、自身のステージのセンターにいるメンバーをポジションチェンジする。(センターにいるメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーが

**Current Frames:** SELECT_MEMBER, MOVE_MEMBER, SELECT_MEMBER, MOVE_MEMBER, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #97 - PL!SP-pb1-008-P+

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメ

**Current Frames:** DRAW, SWAP_AREA, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #121 - PL!S-pb1-002-P+

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得

**Current Frames:** SELECT_MODE, JUMP, JUMP, MOVE_TO_DISCARD, JUMP, GRANT_ABILITY, JUMP, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #149 - PL!SP-bp2-011-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。

**Current Frames:** SELECT_CARDS, OPPONENT_CHOOSE, ADD_TO_HAND, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #150 - PL!N-bp3-003-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ。そのカードの{{toujyou.png|登場}}能力1つを発動させる。
（{{toujyou.

**Current Frames:** TRIGGER_REMOTE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #157 - PL!SP-bp4-013-N

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエ

**Current Frames:** MOVE_MEMBER, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #175 - PL!S-bp5-010-N

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバーが持つハートに{{heart_02.png|heart02}}が合計5つ以上ある場合、相手のライブ開始時、相手のライブカード置き場にある

**Current Frames:** COUNT_HEARTS, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #203 - PL!SP-bp4-008-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメ

**Current Frames:** MOVE_MEMBER, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #281 - PL!S-sd1-004-SD

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}カードを1枚引いてもよい。そうした場合、手札2枚を好きな順番でデッキの上に置く。

**Current Frames:** DRAW, SELECT_CARDS, MOVE_TO_DECK, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #302 - LL-PR-004-PR

**Issue Type:** MISSING_FLAVOR_OPTIONS

**Text:** {{live_start.png|ライブ開始時}}相手に何が好き？と聞く。
回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。
回答があなたの場合、自分と相手はカードを1枚引く。
回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにい

**Current Frames:** SELECT_MODE, JUMP, JUMP, DRAW, DRAW, JUMP, ADD_BLADES, ADD_BLADES, JUMP, RETURN

**Expected:** Flavor choice ability should have option_names with flavor names

**Recommendation:** Add option_names: ["チョコミント", "ストロベリーフレイバー", "クッキー＆クリーム", "あなた"]

---

#### Ability #302 - LL-PR-004-PR

**Issue Type:** INCOMPLETE_FLAVOR_OPTIONS

**Text:** {{live_start.png|ライブ開始時}}相手に何が好き？と聞く。
回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。
回答があなたの場合、自分と相手はカードを1枚引く。
回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る。

**Current Frames:** SELECT_MODE, JUMP, JUMP, DRAW, DRAW, JUMP, ADD_BLADES, ADD_BLADES, JUMP, RETURN

**Expected:** Should have 4 flavor options: ['チョコミント', 'ストロベリーフレイバー', 'クッキー＆クリーム', 'あなた']

**Recommendation:** Add option_names: ['チョコミント', 'ストロベリーフレイバー', 'クッキー＆クリーム', 'あなた']

---

#### Ability #302 - LL-PR-004-PR

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}相手に何が好き？と聞く。
回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。
回答があなたの場

**Current Frames:** SELECT_MODE, JUMP, JUMP, DRAW, DRAW, JUMP, ADD_BLADES, ADD_BLADES, JUMP, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #319 - PL!S-pb1-019-L

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{

**Current Frames:** COUNT_HEARTS, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #324 - PL!N-bp3-025-L

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバー1人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい。そうした場合、ライブ終了時まで、そのメンバーは

**Current Frames:** SELECT_MEMBER, ADD_HEARTS, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #363 - PL!N-bp3-026-L

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にスコアが１か５のカードがある場合、このカードのスコアを+１する。それらが両方ある場合、代わりにスコアを+２する。

**Current Frames:** RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #385 - PL!N-bp5-006-AR

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_success.png|ライブ成功時}}自分のステージにこのメンバー以外のメンバーがいる場合、このメンバーをウェイトにする。

**Current Frames:** COUNT_STAGE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #392 - PL!SP-bp4-006-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に、名前が異なる『Liella!』のメンバーカードが3枚以上ある場合、エールにより公開された自分のカードの中

**Current Frames:** NOP, GROUP_FILTER, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #399 - PL!S-pb1-019-L

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{

**Current Frames:** ENERGY_CHARGE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #427 - PL!SP-bp2-025-L

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分

**Current Frames:** COUNT_STAGE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #445 - PL!N-bp3-009-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、

**Current Frames:** BOOST_SCORE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #449 - PL!S-bp3-001-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、

**Current Frames:** BOOST_SCORE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #474 - PL!SP-bp1-001-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{jyouji.png|常時}}自分のステージにほかのメンバーがいない場合、自分はライブできない。

**Current Frames:** RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #487 - PL!N-bp1-012-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート

**Current Frames:** ADD_HEARTS, ADD_BLADES, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #491 - PL!S-PR-029-PR

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Current Frames:** NOP, ADD_BLADES, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #497 - PL!SP-bp1-004-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレ

**Current Frames:** ADD_BLADES, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #501 - PL!-pb1-014-P+

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{jyouji.png|常時}}自分の成功ライブカード置き場に『lilywhite』のカードがある場合、手札にあるこのメンバーカードのコストは2減る。

**Current Frames:** NOP, REDUCE_COST, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #503 - PL!-pb1-004-P+

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時

**Current Frames:** BOOST_SCORE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #524 - PL!SP-bp1-003-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ

**Current Frames:** RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #547 - PL!SP-bp2-006-P

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyo

**Current Frames:** TRIGGER_REMOTE, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #553 - PL!SP-bp5-006-AR

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：このメンバーはポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる

**Current Frames:** MOVE_MEMBER, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #557 - PL!N-pb1-003-P+

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージ

**Current Frames:** DRAW, SELECT_MEMBER, ADD_BLADES, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #568 - PL!S-pb1-006-P+

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_bla

**Current Frames:** SELECT_CARDS, SELECT_MODE, JUMP, JUMP, MOVE_TO_DISCARD, JUMP, ADD_BLADES, JUMP, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #596 - PL!S-bp3-020-L

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{jidou.png|自動}}［ターン1回］エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい

**Current Frames:** NOP, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

#### Ability #612 - PL!-pb1-015-P+

**Issue Type:** MISSING_CONDITIONAL_JUMP

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージに

**Current Frames:** DRAW, RETURN

**Expected:** Ability has conditional text but no JUMP_IF_FALSE frame

**Recommendation:** Add JUMP_IF_FALSE frame after condition check

---

### INFO (Suggestions)

#### Ability #63 - PL!-PR-005-PR

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・カードを1枚引き、手札を1枚控え室に置く。
・相手のステージにいるすべてのコスト2以下のメンバーをウェイトにする。

**Current Frames:** SELECT_MODE, JUMP, JUMP, DRAW, MOVE_TO_DISCARD, JUMP, SELECT_MEMBER, MOVE_MEMBER, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #64 - PL!S-bp5-004-AR

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得

**Current Frames:** SELECT_MODE, JUMP, JUMP, ADD_BLADES, JUMP, MOVE_MEMBER, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #65 - PL!N-bp5-011-AR

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・自分の控え室にカード名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
・自分の控え室にグループ名が

**Current Frames:** SELECT_MODE, JUMP, JUMP, NOP, JUMP_IF_FALSE, RECOVER_LIVE, RETURN, NOP, JUMP_IF_FALSE, RECOVER_LIVE, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #101 - PL!N-pb1-010-P+

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。

**Current Frames:** SELECT_MODE, JUMP, JUMP, ACTIVATE_ENERGY, JUMP, SELECT_CARDS, MOVE_TO_DECK

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #121 - PL!S-pb1-002-P+

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得

**Current Frames:** SELECT_MODE, JUMP, JUMP, MOVE_TO_DISCARD, JUMP, GRANT_ABILITY, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #127 - PL!N-pb1-008-P+

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする。

**Current Frames:** SELECT_MODE, JUMP, JUMP, ACTIVATE_MEMBER, JUMP, ACTIVATE_ENERGY, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #195 - PL!SP-bp5-001-AR

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにするか、手札を1枚控え室に置く：エネルギーを1枚アクティブにする。

**Current Frames:** PAY_ENERGY, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, TAP_OPPONENT, JUMP, DRAW, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #232 - PL!N-bp3-014-N

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_04.png|heart04}}の

**Current Frames:** SELECT_MODE, JUMP, JUMP, JUMP, JUMP, JUMP, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #233 - PL!N-bp3-015-N

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}{{heart_02.png|heart02}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}の

**Current Frames:** SELECT_MODE, JUMP, JUMP, JUMP, JUMP, JUMP, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #236 - PL!SP-pb1-001-P+

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払わないかぎり、自分の手札を2枚控え室に置く。

**Current Frames:** SELECT_MODE, JUMP, JUMP, PAY_ENERGY, JUMP, MOVE_TO_DISCARD, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #252 - PL!N-bp4-002-P

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの一番上のカードを見る。自分はそのカードを控え室に置いてもよい。

**Current Frames:** SELECT_MODE, JUMP, JUMP, JUMP, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #254 - PL!N-bp3-010-P

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるメンバーカードを2枚まで、好きな順番でデッキの一番下に置く。

**Current Frames:** SELECT_MODE, JUMP, JUMP, RECOVER_MEMBER, JUMP, RECOVER_MEMBER, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #269 - PL!HS-bp5-022-L

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージにコスト9以上の『EdelNote』

**Current Frames:** PAY_ENERGY, JUMP_IF_FALSE, HAS_MEMBER, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, PLAY_MEMBER_FROM_DISCARD, JUMP, REDUCE_HEART_REQ, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #293 - PL!S-sd1-009-SD

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}手札の『Aqours』のカードを1枚公開してもよい：これにより公開したカードをデッキの一番上か一番下に置き、ライブ終了時まで、{{icon_blade

**Current Frames:** REVEAL_CARDS, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, MOVE_TO_DECK, JUMP, MOVE_TO_DECK, ADD_BLADES, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #312 - PL!-bp5-024-L

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『A-RISE』のメンバーがいる場合、以下から1つを選ぶ。
・ウェイト状態のメンバー1人をアクティブにし、ライブ終了時まで、そのメンバ

**Current Frames:** HAS_MEMBER, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, SELECT_MEMBER, ACTIVATE_MEMBER, ADD_BLADES, JUMP, TAP_OPPONENT, RETURN, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #316 - PL!HS-bp2-019-L

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{hear

**Current Frames:** COUNT_STAGE, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, JUMP, JUMP, SET_HEART_COST, JUMP, SET_HEART_COST, JUMP, SET_HEART_COST, JUMP, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #341 - PL!S-bp3-024-L

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}自分のステージのセンターエリアにコスト9以上の『Aqours』のメンバーがいる場合、以下から1つを選ぶ。
・ライブ終了時まで、自分のステージにいるメン

**Current Frames:** HAS_MEMBER, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, SELECT_MEMBER, ADD_BLADES, JUMP, TAP_OPPONENT, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #362 - PL!-bp3-024-L

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{

**Current Frames:** COUNT_SUCCESS_LIVE, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, JUMP, SELECT_MEMBER, ADD_HEARTS, JUMP, SELECT_MEMBER, ADD_HEARTS, JUMP, SELECT_MEMBER, ADD_HEARTS, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #418 - PL!N-bp4-030-L

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。
・自分のエネルギーデッキから、エネルギー

**Current Frames:** COUNT_SUCCESS_LIVE, JUMP_IF_FALSE, SELECT_MODE, JUMP, JUMP, ENERGY_CHARGE, JUMP, RECOVER_MEMBER, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #526 - PL!SP-bp5-001-AR

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以

**Current Frames:** SELECT_MODE, JUMP, JUMP, SET_TAPPED, JUMP_IF_FALSE, JUMP, MOVE_TO_DISCARD, JUMP_IF_FALSE, ACTIVATE_ENERGY, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #540 - PL!-bp3-009-P

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か

**Current Frames:** SELECT_MODE, JUMP, JUMP, JUMP, ADD_HEARTS, JUMP, ADD_HEARTS, JUMP, ADD_HEARTS, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #556 - PL!-pb1-001-P+

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカ

**Current Frames:** IS_CENTER, JUMP_IF_FALSE, SET_TAPPED, MOVE_TO_DISCARD, SELECT_MODE, JUMP, JUMP, REVEAL_UNTIL, JUMP, REVEAL_UNTIL, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #568 - PL!S-pb1-006-P+

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_bla

**Current Frames:** SELECT_CARDS, SELECT_MODE, JUMP, JUMP, MOVE_TO_DISCARD, JUMP, ADD_BLADES, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---

#### Ability #570 - PL!N-bp4-008-P

**Issue Type:** MISSING_OPTION_NAMES

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：エネルギー1枚か『虹ヶ咲』のメンバー1人をアクティブにする。

**Current Frames:** SELECT_MODE, JUMP, JUMP, ACTIVATE_ENERGY, JUMP, SELECT_MEMBER, ACTIVATE_MEMBER, JUMP, RETURN

**Expected:** SELECT_MODE should have descriptive option_names

**Recommendation:** Add option_names array describing each choice

---


## Frame Usage Statistics

| Frame | Count |
|-------|-------|
| RETURN | 615 |
| JUMP_IF_FALSE | 502 |
| MOVE_TO_DISCARD | 166 |
| JUMP | 114 |
| DRAW | 92 |
| ADD_BLADES | 88 |
| ADD_HEARTS | 81 |
| BOOST_SCORE | 79 |
| SELECT_MEMBER | 70 |
| NOP | 68 |
| SUM_VALUE | 64 |
| COUNT_STAGE | 50 |
| PAY_ENERGY | 46 |
| LOOK_AND_CHOOSE | 45 |
| RECOVER_LIVE | 42 |
| MOVE_MEMBER | 29 |
| ENERGY_CHARGE | 28 |
| RECOVER_MEMBER | 28 |
| COUNT_ENERGY | 27 |
| SELECT_MODE | 26 |
| SELECT_CARDS | 24 |
| ACTIVATE_ENERGY | 23 |
| BATON | 21 |
| GROUP_FILTER | 21 |
| HAS_KEYWORD | 20 |
| TAP_OPPONENT | 20 |
| SET_TAPPED | 19 |
| COUNT_SUCCESS_LIVE | 19 |
| HAS_MEMBER | 16 |
| MOVE_TO_DECK | 14 |
| REDUCE_HEART_REQ | 14 |
| ADD_TO_HAND | 13 |
| ACTIVATE_MEMBER | 12 |
| LOOK_DECK | 11 |
| DISCARDED_CARDS | 11 |
| GRANT_ABILITY | 11 |
| COLOR_SELECT | 11 |
| SCORE_COMPARE | 10 |
| COUNT_HEARTS | 10 |
| PLAY_MEMBER_FROM_DISCARD | 9 |
| META_RULE | 8 |
| REDUCE_COST | 8 |
| PLAY_MEMBER_FROM_HAND | 7 |
| SCORE_TOTAL_CHECK | 7 |
| IS_CENTER | 7 |
| LOOK_REORDER_DISCARD | 5 |
| COUNT_DISCARD | 5 |
| PLACE_ENERGY_UNDER_MEMBER | 4 |
| COUNT_GROUP | 4 |
| SET_HEART_COST | 4 |
| INCREASE_COST | 4 |
| SET_TARGET_SELF | 3 |
| MOVE_TO_HAND | 3 |
| SUCCESS_PILE_COUNT | 3 |
| REVEAL_UNTIL | 3 |
| REVEAL_CARDS | 3 |
| TRANSFORM_COLOR | 3 |
| IS_SELF_MOVE | 3 |
| MAIN_PHASE | 3 |
| ORDER_DECK | 2 |
| SWAP_ZONE | 2 |
| SET_TARGET_OPPONENT | 2 |
| SWAP_AREA | 2 |
| PREVENT_PLAY_TO_SLOT | 2 |
| TRIGGER_REMOTE | 2 |
| SYNC_COST | 2 |
| COUNT_HAND | 2 |
| TRANSFORM_HEART | 2 |
| TOTAL_BLADES | 2 |
| COUNT_LIVE_ZONE | 2 |
| INCREASE_HEART_COST | 2 |
| PREVENT_SET_TO_SUCCESS_PILE | 2 |
| PLAY_LIVE_FROM_DISCARD | 2 |
| REDUCE_LIVE_SET_LIMIT | 2 |
| COUNT_BLADE_HEART_TYPES | 2 |
| DRAW_UNTIL | 1 |
| NEGATE_EFFECT | 1 |
| AREA_CHECK | 1 |
| OPPONENT_CHOOSE | 1 |
| RESTRICTION | 1 |
| DIV_VALUE | 1 |
| CALC_SUM_COST | 1 |
| REDUCE_YELL_COUNT | 1 |
| SELECT_LIVE | 1 |
| COUNT_BLADES | 1 |
| TRANSFORM_BLADES | 1 |
| COUNT_ENERGY_EXACT | 1 |
| HAS_LIVE_CARD | 1 |
| INCREASE_HEART_REQ | 1 |
| OPPONENT_ENERGY_DIFF | 1 |
| SET_SCORE | 1 |
| DECK_REFRESHED | 1 |
| HAS_EXCESS_HEART | 1 |
| NOT_HAS_EXCESS_HEART | 1 |
| FORMATION_CHANGE | 1 |
| HEART_LEAD | 1 |
| BATON_TOUCH_MOD | 1 |
| PREVENT_BATON_TOUCH | 1 |
| PAY_ENERGY_DYNAMIC | 1 |
| TYPE_CHECK | 1 |
| SELECT_PLAYER | 1 |
| TARGET_MEMBER_HAS_NO_HEARTS | 1 |
