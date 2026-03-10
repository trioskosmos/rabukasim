# Ability Pipeline Audit Report

## 1. Coverage Gap: Cards with Abilities but No Manual Pseudocode
**Count: 16 / 1045 cards with abilities**

- `LL-bp5-002-L` (Bring the LOVE！): {{live_start.png|ライブ開始時}}自分のステージにグループ名がそれぞれ異なるメンバーが3人以上いる場合、ライブ終了時まで、自分のセンターエリアに...
- `PL!HS-PR-010-PR` (Reflection in the mirror): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!HS-PR-011-PR` (Sparkly Spot): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!HS-PR-012-PR` (アイデンティティ): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!HS-bp1-019-L` (Dream Believers): (エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)...
- `PL!HS-bp1-020-L` (365 Days): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!N-bp1-025-L` (虹色Passions！): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!N-sd1-025-SD` (Colorful Dreams! Colorful Smiles!): (エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)...
- `PL!N-sd1-026-SD` (夢が僕らの太陽さ): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!N-sd1-027-SD` (Just Believe!!!): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!S-bp5-011-N` (桜内梨子): {{toujyou.png|登場}}自分のステージにいるメンバーが持つハートに{{heart_05.png|heart05}}が合計5つ以上ある場合、相手のライ...
- `PL!S-bp5-019-L` (not ALONE not HITORI): {{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上ある場合、エールにより公開された自分のカードの中から、...
- `PL!SP-bp1-025-L` (Starlight Prologue): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!SP-sd1-023-SD` (WE WILL!!): (エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)...
- `PL!SP-sd1-024-SD` (シェキラ☆☆☆): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...
- `PL!SP-sd1-025-SD` (未来は風のように): (必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)...

## 2. QA Data Without Test Coverage
**256 cards referenced in QA but not found in any test file**

- `LL-PR-004-PR`: QA refs: Q185
- `LL-bp1-001-R＋`: QA refs: Q90, Q89, Q69, Q65, Q62
- `LL-bp2-001-R＋`: QA refs: Q186, Q129, Q89, Q62
- `LL-bp3-001-R＋`: QA refs: Q165, Q89, Q62
- `PL!-bp3-002-P`: QA refs: Q144
- `PL!-bp3-002-R`: QA refs: Q144
- `PL!-bp3-003-P`: QA refs: Q145
- `PL!-bp3-003-R`: QA refs: Q145
- `PL!-bp3-004-P`: QA refs: Q146
- `PL!-bp3-004-P＋`: QA refs: Q146
- `PL!-bp3-004-R＋`: QA refs: Q146
- `PL!-bp3-004-SEC`: QA refs: Q146
- `PL!-bp3-008-P`: QA refs: Q145
- `PL!-bp3-008-P＋`: QA refs: Q145
- `PL!-bp3-008-R＋`: QA refs: Q145
- `PL!-bp3-008-SEC`: QA refs: Q145
- `PL!-bp3-019-L`: QA refs: Q147
- `PL!-bp3-023-L`: QA refs: Q148
- `PL!-bp3-025-L`: QA refs: Q142, Q36
- `PL!-bp3-026-L`: QA refs: Q172, Q150, Q149, Q36
- `PL!-bp4-009-P`: QA refs: Q189
- `PL!-pb1-001-P＋`: QA refs: Q167, Q166
- `PL!-pb1-001-R`: QA refs: Q167, Q166
- `PL!-pb1-008-P＋`: QA refs: Q183
- `PL!-pb1-008-R`: QA refs: Q183
- `PL!-pb1-009-P＋`: QA refs: Q180
- `PL!-pb1-009-R`: QA refs: Q180
- `PL!-pb1-013-P＋`: QA refs: Q176
- `PL!-pb1-013-R`: QA refs: Q176
- `PL!-pb1-015-P＋`: QA refs: Q177
- ... and 226 more

## 3. Pseudocode Exists but Bytecode is Empty
**1 cards have manual pseudocode but compiled to empty bytecode**

- `PL!-bp5-021-L`: `TRIGGER: ON_LIVE_START
CONDITION: COUNT_STAGE {MIN=1}
EFFECT: DRAW(1) -> ALL_PLA...`

## 4. Pseudocode Inconsistencies Within Same-Ability Groups
**46 ability groups have conflicting pseudocodes**

### Ability: `{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。...`
**4 different pseudocodes across 18 cards:**
- `PL!-sd1-002-SD`: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_MEMBER(1) -> CARD_HAND...`
- `PL!S-PR-025-PR`: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND...`
- `PL!S-PR-027-PR`: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: RECOVER_MEMBER(1) -> CARD_HAND...`

### Ability: `{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。...`
**3 different pseudocodes across 27 cards:**
- `PL!-sd1-005-SD`: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND...`
- `PL!S-PR-026-PR`: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND...`
- `PL!N-PR-009-PR`: `TRIGGER: ACTIVATED
COST: MOVE_TO_DISCARD
EFFECT: SELECT_RECOVER_LIVE(1) -> CARD_HAND...`

### Ability: `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**2 different pseudocodes across 2 cards:**
- `PL!-sd1-015-SD`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TR...`
- `PL!HS-bp2-010-N`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TR...`

### Ability: `{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}の...`
**3 different pseudocodes across 5 cards:**
- `PL!-bp3-012-PR`: `TRIGGER: ON_LIVE_START
EFFECT: SELECT_OPTION(PLAYER) {OPTIONS=["RED", "GREEN", "PURPLE"]} -> COLOR;
...`
- `PL!-bp3-011-N`: `TRIGGER: ON_LIVE_START
EFFECT: COUNT_SUCCESS_LIVE(PLAYER) -> COUNT_VAL; CHOICE_MODE -> PLAYER
  OPTI...`
- `PL!-bp3-012-N`: `TRIGGER: ON_LIVE_START
EFFECT: COUNT_SUCCESS_LIVE(PLAYER) -> COUNT_VAL; CHOICE_MODE -> PLAYER
  OPTI...`

### Ability: `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状...`
**2 different pseudocodes across 6 cards:**
- `PL!-PR-007-PR`: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALU...`
- `PL!-PR-009-PR`: `TRIGGER: ON_PLAY
TRIGGER: ON_LIVE_START
COST: TAP_SELF (Optional) -> SUCCESS
EFFECT: CONDITION: VALU...`
- `PL!S-bp3-012-N`: `TRIGGER: ON_PLAY, ON_LIVE_START
COST: TAP_SELF (Optional)
EFFECT: SELECT_MEMBER(1) {FILTER="OPPONENT...`

### Ability: `{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。...`
**2 different pseudocodes across 15 cards:**
- `PL!N-bp1-019-PR`: `TRIGGER: ON_PLAY
EFFECT: DRAW(1); DISCARD_HAND(1)...`
- `PL!N-bp1-014-N`: `TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER...`
- `PL!N-bp1-015-N`: `TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER...`

### Ability: `{{toujyou.png|登場}}カードを2枚引き、手札を2枚控え室に置く。...`
**2 different pseudocodes across 5 cards:**
- `PL!N-PR-005-PR`: `TRIGGER: ON_PLAY
EFFECT: DRAW(2); DISCARD_HAND(2)...`
- `PL!N-PR-007-PR`: `TRIGGER: ON_PLAY
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER...`
- `PL!N-PR-011-PR`: `TRIGGER: ON_PLAY
EFFECT: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER...`

### Ability: `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**2 different pseudocodes across 6 cards:**
- `PL!SP-PR-004-PR`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TR...`
- `PL!SP-PR-006-PR`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TR...`
- `PL!SP-PR-013-PR`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TR...`

### Ability: `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.p...`
**4 different pseudocodes across 12 cards:**
- `PL!HS-PR-018-PR`: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS...`
- `PL!HS-PR-022-PR`: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS...`
- `PL!SP-bp1-006-R`: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS...`

### Ability: `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{hea...`
**2 different pseudocodes across 2 cards:**
- `PL!HS-PR-019-PR`: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3, FROM="DECK_TOP") -> DISCARDED;
CONDITION: COUNT_CARDS(DI...`
- `PL!HS-PR-019-RM`: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
CONDITION: ALL_MEMBERS {FILTER="HEART_...`

### Ability: `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分の控え室にあるメンバーカード2枚を好きな順番でデッキの一番上に置く。...`
**2 different pseudocodes across 2 cards:**
- `PL!HS-PR-020-PR`: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: MOVE_TO_DECK(2) {FROM="DISCARD", TYPE_...`
- `PL!HS-PR-023-PR`: `TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS...`

### Ability: `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{hea...`
**2 different pseudocodes across 2 cards:**
- `PL!HS-PR-021-PR`: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3, FROM="DECK_TOP") -> DISCARDED;
CONDITION: COUNT_CARDS(DI...`
- `PL!HS-PR-021-RM`: `TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
CONDITION: ALL_MEMBERS {FILTER="HEART_...`

### Ability: `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_ene...`
**2 different pseudocodes across 4 cards:**
- `PL!N-bp1-003-R＋`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

TRIGGER: ON_...`
- `PL!N-bp1-003-P`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> C...`
- `PL!N-bp1-003-P＋`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) -> CARD_HAND

TRIGGER: ON_...`

### Ability: `{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。...`
**2 different pseudocodes across 3 cards:**
- `PL!SP-bp1-012-N`: `TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE...`
- `PL!SP-sd1-008-SD`: `TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(3) -> CARD_HAND, DISCARD_REM...`
- `PL!SP-sd1-017-SD`: `TRIGGER: ON_PLAY
COST: PAY_ENERGY(1) (Optional) -> SUCCESS
EFFECT: CONDITION: VALUE_EQ(SUCCESS, TRUE...`

### Ability: `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『みらくらぱーく！』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**2 different pseudocodes across 2 cards:**
- `PL!HS-bp1-009-R`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {UNIT="Mirakura"} -> CA...`
- `PL!HS-bp1-009-P`: `TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(5) {FILTER="UNIT_MIRAKURA"...`

... and 31 more groups

## 5. Variant Cards with Different Ability Text
**44 variant pairs have divergent ability text**

- `PL!HS-bp1-002-R` vs `PL!HS-bp1-002-RM`
- `PL!HS-bp1-002-P` vs `PL!HS-bp1-002-RM`
- `PL!SP-bp1-025-L＋` vs `PL!SP-bp1-025-L`
- `PL!-bp3-009-R＋` vs `PL!-bp3-009-P＋`
- `PL!-bp3-009-R＋` vs `PL!-bp3-009-SEC`
- `PL!-bp3-009-P` vs `PL!-bp3-009-P＋`
- `PL!-bp3-009-P` vs `PL!-bp3-009-SEC`
- `PL!-bp3-009-P＋` vs `PL!-bp3-009-R＋`
- `PL!-bp3-009-P＋` vs `PL!-bp3-009-P`
- `PL!-bp3-009-SEC` vs `PL!-bp3-009-R＋`
- `PL!-bp3-009-SEC` vs `PL!-bp3-009-P`
- `PL!S-bp3-003-R＋` vs `PL!S-bp3-003-P＋`
- `PL!S-bp3-003-R＋` vs `PL!S-bp3-003-SEC`
- `PL!S-bp3-003-P` vs `PL!S-bp3-003-P＋`
- `PL!S-bp3-003-P` vs `PL!S-bp3-003-SEC`
- `PL!S-bp3-003-P＋` vs `PL!S-bp3-003-R＋`
- `PL!S-bp3-003-P＋` vs `PL!S-bp3-003-P`
- `PL!S-bp3-003-SEC` vs `PL!S-bp3-003-R＋`
- `PL!S-bp3-003-SEC` vs `PL!S-bp3-003-P`
- `PL!N-bp3-005-R＋` vs `PL!N-bp3-005-P＋`

## 6. Complex (Multi-Trigger) Cards Without Test Coverage
**299 cards have 2+ triggers and no test references**

- `PL!SP-bp2-006-R＋` (桜小路きな子): **4 triggers**
- `PL!SP-bp2-006-P` (桜小路きな子): **4 triggers**
- `PL!SP-bp2-006-P＋` (桜小路きな子): **4 triggers**
- `PL!SP-bp2-006-SEC` (桜小路きな子): **4 triggers**
- `PL!-bp4-002-R＋` (絢瀬絵里): **4 triggers**
- `PL!-bp4-002-P` (絢瀬絵里): **4 triggers**
- `PL!-bp4-002-P＋` (絢瀬絵里): **4 triggers**
- `PL!-bp4-002-SEC` (絢瀬絵里): **4 triggers**
- `PL!N-bp5-030-L` (繚乱！ビクトリーロード): **4 triggers**
- `LL-bp1-001-R＋` (上原歩夢&澁谷かのん&日野下花帆): **3 triggers**
- `PL!HS-bp1-003-R＋` (乙宗 梢): **3 triggers**
- `PL!HS-bp1-003-P` (乙宗 梢): **3 triggers**
- `PL!HS-bp1-003-P＋` (乙宗 梢): **3 triggers**
- `PL!HS-bp1-003-SEC` (乙宗 梢): **3 triggers**
- `PL!S-bp2-008-R＋` (小原鞠莉): **3 triggers**
- `PL!S-bp2-008-P` (小原鞠莉): **3 triggers**
- `PL!S-bp2-008-P＋` (小原鞠莉): **3 triggers**
- `PL!S-bp2-008-SEC` (小原鞠莉): **3 triggers**
- `LL-bp2-001-R＋` (渡辺 曜&鬼塚夏美&大沢瑠璃乃): **3 triggers**
- `PL!S-pb1-019-L` (元気全開DAY！DAY！DAY！): **3 triggers**
- `PL!N-bp3-003-R` (桜坂しずく): **3 triggers**
- `PL!N-bp3-003-P` (桜坂しずく): **3 triggers**
- `PL!N-bp3-005-R＋` (宮下 愛): **3 triggers**
- `PL!N-bp3-005-P` (宮下 愛): **3 triggers**
- `PL!N-bp3-005-P＋` (宮下 愛): **3 triggers**
- `PL!N-bp3-005-SEC` (宮下 愛): **3 triggers**
- `PL!-pb1-002-R` (絢瀬絵里): **3 triggers**
- `PL!-pb1-002-P＋` (絢瀬絵里): **3 triggers**
- `PL!-pb1-004-R` (園田海未): **3 triggers**
- `PL!-pb1-004-P＋` (園田海未): **3 triggers**
- ... and 269 more

## 7. Pipeline Summary Statistics

| Metric | Count |
|---|---|
| Total cards in cards.json | 1787 |
| Cards with abilities | 1045 |
| Cards with manual pseudocode | 1046 |
| Cards with NO pseudocode (have ability) | 16 |
| QA items | 206 |
| Unique cards in QA | 257 |
| Cards referenced in tests | 8 |
| QA cards without tests | 256 |
| Pseudocode -> empty bytecode | 1 |
| Same-ability pseudocode conflicts | 46 |
| Complex untested cards (2+ triggers) | 299 |
| Compiled cards total | 1787 |
| **Pseudocode coverage rate** | **98.5%** |

## 8. Risk Assessment

### 🔴 Critical Risks
- **1 cards** have pseudocode that compiles to empty bytecode — these abilities are silently broken
- **46 ability groups** have multiple conflicting pseudocodes — the consolidated mapping picks one but may pick wrong

### 🟠 High Risks
- **16 cards** have abilities but no pseudocode at all — these parse raw JP text, likely producing garbage bytecode
- **256 QA-referenced cards** have no test coverage — official FAQs document edge cases that aren't verified

### 🟡 Medium Risks
- **299 complex multi-trigger cards** have no tests — these are most likely to have subtle bugs
- The parser (`parser_v2.py`) at 2066 lines has many alias mappings that can silently map wrong opcode

### Architectural Weakpoints
1. **Pseudocode is freeform text** → no schema validation, easy to write something the parser silently ignores
2. **Parser alias explosion** → 50+ aliases mean the same intent can be expressed many ways, causing silent divergence
3. **No round-trip verification** → bytecode is never decompiled back to pseudocode to verify semantic equivalence
4. **Consolidated mapping uses longest-wins** → a longer but wrong pseudocode beats a shorter correct one
5. **Variant cards share ability text but may need distinct pseudocode** due to group filters (e.g., Nijigasaki vs μ's)
6. **No compile-time warning for unrecognized pseudocode tokens** → typos pass silently
