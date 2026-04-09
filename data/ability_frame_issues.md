# Ability Frame Issues - Mismatches Between Frames and JP Text

**File analyzed:** `ability_frame_source.json`
**Generated:** 2026-04-09
**Issues found:** 42

| Severity | Count |
|----------|-------|
| CRITICAL | 3 |
| HIGH | 29 |
| MEDIUM | 10 |

---

## Issue 1: ``
**Severity:** CRITICAL

**Cards:**
- PL!S-bp2-004-P | 黒澤ダイヤ
- PL!S-bp2-004-R | 黒澤ダイヤ

**Frame opcodes:** `META_RULE → RETURN`

**Primary JP Text:**
> {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。

**Problem(s):**
- Text: complex yell-repeat mechanic; Frame: only META_RULE placeholder

---

## Issue 2: ``
**Severity:** CRITICAL

**Cards:**
- PL!HS-bp2-020-L | Link to the FUTURE

**Frame opcodes:** `META_RULE → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。

**Problem(s):**
- Text: card treated as multiple groups; Frame: empty/META_RULE placeholder only

---

## Issue 3: ``
**Severity:** CRITICAL

**Cards:**
- PL!HS-sd1-020-SD | Link to the FUTURE（104期Ver.）

**Frame opcodes:** `META_RULE → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。

**Problem(s):**
- Text: card treated as multiple groups; Frame: empty/META_RULE placeholder only

---

## Issue 4: ``
**Severity:** HIGH

**Cards:**
- PL!HS-bp1-010-N | 日野下花帆
- PL!HS-bp1-014-N | 大沢瑠璃乃
- PL!N-bp1-014-N | 中須かすみ

**Frame opcodes:** `DRAW → MOVE_TO_DISCARD → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。

**Problem(s):**
- Shared frame for cards with different abilities: Card '黒澤ダイヤ (ab#0)' differs in: has_live_card, discard

---

## Issue 5: ``
**Severity:** HIGH

**Cards:**
- PL!HS-bp1-005-P | 大沢瑠璃乃
- PL!HS-bp1-005-R | 大沢瑠璃乃
- PL!HS-bp5-011-N | 大沢瑠璃乃

**Frame opcodes:** `DRAW → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。

**Problem(s):**
- Shared frame for cards with different abilities: Card '大沢瑠璃乃 (ab#0)' differs in: discard; Card '徒町 小鈴 (ab#0)' differs in: draw; Card '中須かすみ (ab#0)' differs in: has_live_card, to_hand, draw; Card '渡辺 曜 (ab#0)' differs in: deck_bottom, to_deck, discard, draw; Card '津島善子 (ab#0)' differs in: draw

---

## Issue 6: ``
**Severity:** HIGH

**Cards:**
- PL!S-bp2-008-P | 小原鞠莉
- PL!S-bp2-008-R+ | 小原鞠莉
- PL!S-bp2-008-P+ | 小原鞠莉

**Frame opcodes:** `SELECT_CARDS → MOVE_TO_DECK → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。

**Problem(s):**
- Shared frame for cards with different abilities: Card '唐 可可 (ab#0)' differs in: has_live_card, deck_top, deck_bottom

---

## Issue 7: ``
**Severity:** HIGH

**Cards:**
- PL!SP-bp4-011-P | 鬼塚冬毬
- PL!SP-bp4-011-R+ | 鬼塚冬毬

**Frame opcodes:** `NOP → JUMP_IF_FALSE → SELECT_MEMBER → MOVE_MEMBER → RETURN`

**Primary JP Text:**
> {{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 8: ``
**Severity:** HIGH

**Cards:**
- PL!N-bp4-010-P | 三船栞子
- PL!N-bp4-010-R+ | 三船栞子

**Frame opcodes:** `JUMP_IF_FALSE → RECOVER_LIVE → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。

**Problem(s):**
- Text: swap live cards (success<->discard); Frame: only recovers from discard (half implemented)

---

## Issue 9: ``
**Severity:** HIGH

**Cards:**
- PL!-pb1-002-P+ | 絢瀬絵里
- PL!-pb1-002-R | 絢瀬絵里

**Frame opcodes:** `GROUP_FILTER → JUMP_IF_FALSE → SET_TAPPED → JUMP_IF_FALSE → SELECT_MEMBER → MOVE_MEMBER → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 10: ``
**Severity:** HIGH

**Cards:**
- PL!-pb1-009-P+ | 矢澤にこ
- PL!-pb1-009-R | 矢澤にこ

**Frame opcodes:** `SELECT_MEMBER → MOVE_MEMBER → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする。

**Problem(s):**
- Text: blade count <= 1; Frame: missing blade count check

---

## Issue 11: ``
**Severity:** HIGH

**Cards:**
- LL-bp4-001-R+ | 絢瀬絵里&朝香果林&葉月 恋

**Frame opcodes:** `LOOK_AND_CHOOSE → TAP_OPPONENT → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}自分のデッキの上からカードを5枚見る。その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。その後、相手のステージにいる、これにより公開したカードのコスト以下で、かつ元々持つ{{icon_blade.png|...

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 12: ``
**Severity:** HIGH

**Cards:**
- PL!S-bp5-002-AR | 桜内梨子
- PL!S-bp5-002-R+ | 桜内梨子

**Frame opcodes:** `SYNC_COST → JUMP_IF_FALSE → TAP_OPPONENT → RETURN`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}{{center.png|センター}}自分のステージの右サイドエリアと左サイドエリアにいるメンバーのコストが同じ場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のすべてのメンバーをウェイトにする。

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 13: ``
**Severity:** HIGH

**Cards:**
- PL!-bp5-024-L | Private Wars

**Frame opcodes:** `HAS_MEMBER → JUMP_IF_FALSE → SELECT_MODE → JUMP → JUMP → SELECT_MEMBER → ACTIVATE_MEMBER → ADD_BLADES → JUMP → SELECT_MEMBER → MOVE_MEMBER → JUMP → RETURN`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}自分のステージに『A-RISE』のメンバーがいる場合、以下から1つを選ぶ。
・ウェイト状態のメンバー1人をアクティブにし、ライブ終了時まで、そのメンバーは{{icon_blade.png|ブレード}}を得る。
・相手のステージにいる元々持つ{{icon_blade.png|ブレード}}が3つ以下のメンバー1人...

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 14: ``
**Severity:** HIGH

**Cards:**
- LL-bp4-001-R+ | 絢瀬絵里&朝香果林&葉月 恋

**Frame opcodes:** `LOOK_AND_CHOOSE → TAP_OPPONENT → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}自分のデッキの上からカードを5枚見る。その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。その後、相手のステージにいる、これにより公開したカードのコスト以下で、かつ元々持つ{{icon_blade.png|...

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 15: ``
**Severity:** HIGH

**Cards:**
- PL!-bp5-001-AR | 高坂穂乃果
- PL!-bp5-001-R+ | 高坂穂乃果
- PL!-bp5-001-P | 高坂穂乃果

**Frame opcodes:** `MOVE_TO_DISCARD → JUMP_IF_FALSE → RETURN`

**Primary JP Text:**
> {{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：自分のデッキの上から、自分のライブの合計スコアに2を足した数に等しい枚数見る。その中からカードを1枚手札に加える。残りを控え室に置く。

**Problem(s):**
- Shared frame for cards with different abilities: Card '徒町小鈴 (ab#0)' differs in: has_live_card

---

## Issue 16: ``
**Severity:** HIGH

**Cards:**
- LL-bp5-001-L | Live with a smile!
- PL!-bp3-025-L | タカラモノズ
- PL!N-bp3-030-L | Love U my friends

**Frame opcodes:** `NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN`

**Primary JP Text:**
> {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが2枚以上あるか、自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{heart_05.png|...

**Problem(s):**
- Shared frame for cards with different abilities: Card 'タカラモノズ (ab#0)' differs in: has_live_card; Card 'Love U my friends (ab#0)' differs in: has_live_card

---

## Issue 17: ``
**Severity:** HIGH

**Cards:**
- PL!-bp4-005-P | 星空 凛
- PL!-bp4-005-R+ | 星空 凛
- PL!-bp4-005-P+ | 星空凛

**Frame opcodes:** `BOOST_SCORE → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを+１する。

**Problem(s):**
- Shared frame for cards with different abilities: Card '東條 希 (ab#1)' differs in: has_live_card; Card '園田海未 (ab#1)' differs in: has_live_card; Card '園田海未 (ab#1)' differs in: has_live_card; Card '天王寺璃奈 (ab#1)' differs in: deck_bottom, to_deck, draw; Card '鐘 嵐珠 (ab#0)' differs in: has_live_card; Card '中須かすみ (ab#1)' differs in: to_deck

---

## Issue 18: ``
**Severity:** HIGH

**Cards:**
- PL!HS-bp2-002-P | 村野さやか
- PL!HS-bp2-002-R+ | 村野さやか
- PL!HS-bp2-002-P+ | 村野さやか

**Frame opcodes:** `BATON → JUMP_IF_FALSE → COUNT_ENERGY → JUMP_IF_FALSE → ENERGY_CHARGE → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Problem(s):**
- Shared frame for cards with different abilities: Card '高海千歌 (ab#0)' differs in: has_live_card; Card '黒澤ルビィ (ab#0)' differs in: has_live_card

---

## Issue 19: ``
**Severity:** HIGH

**Cards:**
- PL!-bp4-018-N | 矢澤にこ
- PL!HS-bp5-007-AR | セラス 柳田 リリエンフェルト
- PL!HS-bp5-007-R | セラス 柳田 リリエンフェルト

**Frame opcodes:** `ADD_BLADES → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Problem(s):**
- Shared frame for cards with different abilities: Card 'セラス 柳田 リリエンフェルト (ab#1)' differs in: has_live_card; Card '朝香果林 (ab#0)' differs in: has_live_card; Card '嵐 千砂都 (ab#1)' differs in: has_live_card

---

## Issue 20: ``
**Severity:** HIGH

**Cards:**
- PL!-bp3-002-P | 絢瀬絵里
- PL!-bp3-002-R | 絢瀬絵里
- PL!-sd1-001-SD | 高坂 穂乃果

**Frame opcodes:** `ADD_BLADES → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。

**Problem(s):**
- Shared frame for cards with different abilities: Card '高坂 穂乃果 (ab#1)' differs in: has_live_card

---

## Issue 21: ``
**Severity:** HIGH

**Cards:**
- PL!-bp5-003-AR | 南 ことり
- PL!-bp5-003-R+ | 南 ことり
- PL!-bp5-003-P | 南 ことり

**Frame opcodes:** `NOP → JUMP_IF_FALSE → ADD_HEARTS → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}自分のステージに名前が異なるメンバーが3人以上いるかぎり、{{heart_03.png|heart03}}を得る。

**Problem(s):**
- Shared frame for cards with different abilities: Card '澁谷かのん (ab#0)' differs in: has_live_card

---

## Issue 22: ``
**Severity:** HIGH

**Cards:**
- PL!-bp4-002-P | 絢瀬絵里
- PL!-bp4-002-R+ | 絢瀬絵里
- PL!-bp4-002-P+ | 絢瀬絵里

**Frame opcodes:** `ADD_HEARTS → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart0...

**Problem(s):**
- Shared frame for cards with different abilities: Card '葉月 恋 (ab#0)' differs in: has_live_card

---

## Issue 23: ``
**Severity:** HIGH

**Cards:**
- PL!HS-bp5-016-N | 桂城 泉
- PL!N-pb1-007-P+ | 優木せつ菜
- PL!N-pb1-007-R | 優木せつ菜

**Frame opcodes:** `ADD_HEARTS → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}相手のステージにウェイト状態のメンバーが2人以上いるかぎり、{{heart_06.png|heart06}}を得る。

**Problem(s):**
- Shared frame for cards with different abilities: Card '優木せつ菜 (ab#0)' differs in: has_live_card

---

## Issue 24: ``
**Severity:** HIGH

**Cards:**
- PL!HS-sd1-005-SD | 徒町小鈴
- PL!-bp4-020-L | Love wing bell

**Frame opcodes:** `ADD_BLADES → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。

**Problem(s):**
- Shared frame for cards with different abilities: Card '徒町小鈴 (ab#1)' differs in: has_live_card

---

## Issue 25: ``
**Severity:** HIGH

**Cards:**
- PL!SP-pb1-010-P+ | ウィーン・マルガレーテ
- PL!SP-pb1-010-R | ウィーン・マルガレーテ

**Frame opcodes:** `INCREASE_COST → RETURN`

**Primary JP Text:**
> {{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを+４する。

**Problem(s):**
- Text requires energy >= 10; Frame lacks energy count check

---

## Issue 26: ``
**Severity:** HIGH

**Cards:**
- PL!-pb1-002-P+ | 絢瀬絵里
- PL!-pb1-002-R | 絢瀬絵里

**Frame opcodes:** `ADD_HEARTS → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。
{{jyouji.png|常時}}相手のステージにいるウェイ...

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 27: ``
**Severity:** HIGH

**Cards:**
- PL!-PR-003-PR | 南ことり
- PL!-PR-004-PR | 園田海未
- PL!-bp4-003-P | 南 ことり

**Frame opcodes:** `MOVE_TO_DISCARD → RECOVER_LIVE → RETURN`

**Primary JP Text:**
> {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_03.png|heart03}}を3以上含むライブカードを1枚手札に加える。

**Problem(s):**
- Shared frame for cards with different abilities: Card '鐘 嵐珠 (ab#1)' differs in: discard; Card '柊摩央 (ab#1)' differs in: discard

---

## Issue 28: ``
**Severity:** HIGH

**Cards:**
- PL!-PR-012-PR | 小泉花陽
- PL!HS-bp1-007-P | 百生 吟子
- PL!HS-bp1-007-R | 百生 吟子

**Frame opcodes:** `DRAW → RETURN`

**Primary JP Text:**
> {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：カードを1枚引く。

**Problem(s):**
- Shared frame for cards with different abilities: Card '百生 吟子 (ab#0)' differs in: discard

---

## Issue 29: ``
**Severity:** HIGH

**Cards:**
- PL!N-pb1-006-P+ | 近江彼方
- PL!N-pb1-006-R | 近江彼方
- PL!SP-bp5-001-AR | 澁谷かのん

**Frame opcodes:** `ACTIVATE_ENERGY → RETURN`

**Primary JP Text:**
> {{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。

**Problem(s):**
- Shared frame for cards with different abilities: Card '澁谷かのん (ab#2)' differs in: discard, draw

---

## Issue 30: ``
**Severity:** HIGH

**Cards:**
- PL!N-bp3-004-P | 朝香果林
- PL!N-bp3-004-R | 朝香果林
- PL!N-pb1-011-P+ | ミア・テイラー

**Frame opcodes:** `MOVE_TO_DISCARD → RECOVER_LIVE → RETURN`

**Primary JP Text:**
> {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。

**Problem(s):**
- Shared frame for cards with different abilities: Card 'ミア・テイラー (ab#1)' differs in: deck_bottom, to_deck, discard

---

## Issue 31: ``
**Severity:** HIGH

**Cards:**
- PL!SP-bp4-011-P | 鬼塚冬毬
- PL!SP-bp4-011-R+ | 鬼塚冬毬

**Frame opcodes:** `NOP → JUMP_IF_FALSE → SELECT_MEMBER → MOVE_MEMBER → RETURN`

**Primary JP Text:**
> {{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。

**Problem(s):**
- Text: blade count <= 3; Frame: missing blade count check

---

## Issue 32: ``
**Severity:** HIGH

**Cards:**
- PL!S-bp5-111-P+ | 鹿角聖良
- PL!S-bp5-111-R | 鹿角聖良

**Frame opcodes:** `IS_SELF_MOVE → JUMP_IF_FALSE → SELECT_MEMBER → MOVE_MEMBER → RETURN`

**Primary JP Text:**
> {{jidou.png|自動}}このメンバーがエリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が2つ以下のメンバー1人をウェイトにする。

**Problem(s):**
- Text: blade count <= 2; Frame: missing blade count check

---

## Issue 33: ``
**Severity:** MEDIUM

**Cards:**
- PL!SP-bp2-006-P | 桜小路きな子
- PL!SP-bp2-006-R+ | 桜小路きな子

**Frame opcodes:** `BATON → JUMP_IF_FALSE → RECOVER_MEMBER → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。

**Problem(s):**
- Text: recover card discarded by THIS baton; Frame: lacks discard tracking

---

## Issue 34: ``
**Severity:** MEDIUM

**Cards:**
- PL!N-pb1-010-P+ | 三船栞子
- PL!N-pb1-010-R | 三船栞子

**Frame opcodes:** `SELECT_MODE → JUMP → JUMP → ACTIVATE_ENERGY → JUMP → RECOVER_LIVE → JUMP → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。

**Problem(s):**
- Text: put live card to deck; Frame: uses RECOVER_LIVE (wrong dest, should be MOVE_TO_DECK)

---

## Issue 35: ``
**Severity:** MEDIUM

**Cards:**
- PL!SP-bp2-011-P | 鬼塚冬毬
- PL!SP-bp2-011-R | 鬼塚冬毬

**Frame opcodes:** `SELECT_CARDS → OPPONENT_CHOOSE → ADD_TO_HAND → RETURN`

**Primary JP Text:**
> {{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。

**Problem(s):**
- Text: select LIVE card; Frame: SELECT_CARDS lacks LIVE type filter

---

## Issue 36: ``
**Severity:** MEDIUM

**Cards:**
- PL!HS-PR-020-PR | 徒町 小鈴
- PL!HS-PR-023-PR | 桂城 泉

**Frame opcodes:** `PAY_ENERGY → JUMP_IF_FALSE → SUM_VALUE → JUMP_IF_FALSE → SELECT_CARDS → MOVE_TO_DECK → RETURN`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分の控え室にあるメンバーカード2枚を好きな順番でデッキの一番上に置く。

**Problem(s):**
- Text: put to deck TOP; Frame: MOVE_TO_DECK lacks top position

---

## Issue 37: ``
**Severity:** MEDIUM

**Cards:**
- PL!N-bp4-009-P | 天王寺璃奈
- PL!N-bp4-009-R | 天王寺璃奈

**Frame opcodes:** `SCORE_COMPARE → JUMP_IF_FALSE → DRAW → MOVE_TO_DECK → RETURN`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを2枚引き、自分の手札を1枚デッキの一番上に置く。

**Problem(s):**
- Text: put hand cards to deck top; Frame: lacks hand card selection
- Text: put to deck top; Frame: lacks deck top specification
- Text: put to deck TOP; Frame: MOVE_TO_DECK lacks top position

---

## Issue 38: ``
**Severity:** MEDIUM

**Cards:**
- PL!S-sd1-004-SD | 黒澤ダイヤ

**Frame opcodes:** `DRAW → MOVE_TO_DECK → RETURN`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}カードを1枚引いてもよい。そうした場合、手札2枚を好きな順番でデッキの上に置く。

**Problem(s):**
- Text: put hand cards to deck top; Frame: lacks hand card selection
- Text: put to deck top; Frame: lacks deck top specification
- Text: put to deck TOP; Frame: MOVE_TO_DECK lacks top position

---

## Issue 39: ``
**Severity:** MEDIUM

**Cards:**
- PL!S-sd1-009-SD | 黒澤ルビィ

**Frame opcodes:** `REVEAL_CARDS → JUMP_IF_FALSE → MOVE_TO_DECK → ADD_BLADES → RETURN`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}手札の『Aqours』のカードを1枚公開してもよい：これにより公開したカードをデッキの一番上か一番下に置き、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。

**Problem(s):**
- Text: put to deck TOP; Frame: MOVE_TO_DECK lacks top position

---

## Issue 40: ``
**Severity:** MEDIUM

**Cards:**
- PL!S-bp5-023-L | Awaken the power

**Frame opcodes:** `HAS_MEMBER → HAS_MEMBER → SCORE_COMPARE → JUMP_IF_FALSE → MOVE_TO_DECK → RETURN`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}自分のステージに『Aqours』のメンバーと『SaintSnow』のメンバーがいて、かつそれらのメンバーのコストが合計20以上の場合、自分の控え室にある『Aqours』と『SaintSnow』のライブカードを4枚まで好きな順番でデッキの上に置いてもよい。

**Problem(s):**
- Text: put to deck TOP; Frame: MOVE_TO_DECK lacks top position

---

## Issue 41: ``
**Severity:** MEDIUM

**Cards:**
- PL!S-bp3-005-P | 渡辺 曜
- PL!S-bp3-005-R | 渡辺 曜

**Frame opcodes:** `NOP → JUMP_IF_FALSE → DRAW → RETURN`

**Primary JP Text:**
> {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの枚数が、相手がエールによって公開したカードの枚数より少ない場合、カードを1枚引く。

**Problem(s):**
- Text: compare yell counts; Frame: uses NOP check (not proper comparison)

---

## Issue 42: ``
**Severity:** MEDIUM

**Cards:**
- PL!S-bp2-021-L | 未体験HORIZON

**Frame opcodes:** `MOVE_TO_DECK → RETURN`

**Primary JP Text:**
> {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く。

**Problem(s):**
- Text: put to deck BOTTOM; Frame: MOVE_TO_DECK lacks bottom position

---
