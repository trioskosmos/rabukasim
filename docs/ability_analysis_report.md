# Ability Frame Analysis Report

Total abilities analyzed: 614
Abilities with issues: 138

## PL!HS-bp1-005-P#Ab0

**Text:** {{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。

**Frame Flow:** MOVE_TO_DISCARD → DRAW → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!HS-bp5-013-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{...

**Frame Flow:** MOVE_TO_DISCARD → DRAW → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!N-bp5-014-N#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『虹ヶ...

**Frame Flow:** MOVE_TO_DISCARD → DRAW → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!S-bp5-014-N#Ab0

**Text:** {{toujyou.png|登場}}カードを1枚引き、手札を1枚デッキの一番下に置く。

**Frame Flow:** MOVE_TO_DISCARD → DRAW → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!S-bp5-015-N#Ab0

**Text:** {{toujyou.png|登場}}自分のデッキの上からカードを10枚控え室に置く。

**Frame Flow:** MOVE_TO_DISCARD → DRAW → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!HS-bp2-005-P#Ab0

**Text:** {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。

**Frame Flow:** MOVE_TO_DISCARD → JUMP_IF_FALSE → SUM_VALUE → COUNT_STAGE → SUM_VALUE → JUMP_IF_FALSE → RECOVER_MEMBER → RETURN

**Issues:**
- Frame 3: Missing target_player: SELF for own stage check

---

## PL!-bp3-004-P#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → DRAW → MOVE_TO_DISCARD → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!-bp3-009-P#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → DRAW → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!HS-bp5-001-AR#Ab0

**Text:** {{toujyou.png|登場}}自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_bl...

**Frame Flow:** MOVE_TO_DISCARD → DISCARDED_CARDS → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp5-009-AR#Ab0

**Text:** {{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『SaintSnow』のカードを1枚手札に加える。そうした場合、ライブ終了時まで、{{ic...

**Frame Flow:** PAY_ENERGY → JUMP_IF_FALSE → RECOVER_MEMBER → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 4: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp5-004-AR#Ab0

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得...

**Frame Flow:** SELECT_MODE → JUMP → JUMP → ADD_BLADES → JUMP → MOVE_MEMBER → JUMP → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-pb1-012-P+#Ab0

**Text:** {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにこのメンバー以外のコスト11のメンバーが登場したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → ACTIVATE_ENERGY → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!N-pb1-005-P+#Ab0

**Text:** {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。

**Frame Flow:** GROUP_FILTER → JUMP_IF_FALSE → DRAW → RETURN

**Issues:**
- Frame 0: GROUP_FILTER missing target_player: SELF

---

## PL!-pb1-002-P+#Ab0

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元...

**Frame Flow:** GROUP_FILTER → JUMP_IF_FALSE → SET_TAPPED → JUMP_IF_FALSE → SELECT_MEMBER → MOVE_MEMBER → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Text has 'only' condition (のみ) but no SUM_VALUE for comparison - may not check properly
- Frame 0: GROUP_FILTER missing target_player: SELF
- Frame 0: GROUP_FILTER value=4 but text says 'only' - should check ALL members are in group

---

## PL!-pb1-003-P+#Ab0

**Text:** {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『Printemps』のメンバー1人につき、エネルギーを1枚アクティブにする。

**Frame Flow:** SET_TAPPED → JUMP_IF_FALSE → COUNT_STAGE → JUMP_IF_FALSE → ACTIVATE_ENERGY → RETURN

**Issues:**
- Frame 2: Missing target_player: SELF for own stage check

---

## PL!SP-bp1-008-P#Ab0

**Text:** {{toujyou.png|登場}}カードを1枚引く。自分のステージに「米女メイ」がいる場合、さらにカードを1枚引く。

**Frame Flow:** DRAW → COUNT_STAGE → JUMP_IF_FALSE → DRAW → RETURN

**Issues:**
- Frame 1: Missing target_player: SELF for own stage check

---

## PL!SP-pb1-003-P+#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリ...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → SWAP_AREA → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Text has 'only' condition (のみ) but no SUM_VALUE for comparison - may not check properly

---

## PL!SP-bp4-001-P#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバーが『Liella!』のみで、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く...

**Frame Flow:** GROUP_FILTER → COUNT_ENERGY → JUMP_IF_FALSE → ENERGY_CHARGE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Text has 'only' condition (のみ) but no SUM_VALUE for comparison - may not check properly
- Frame 0: GROUP_FILTER missing target_player: SELF

---

## PL!SP-pb1-009-P+#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにほかの『5yncri5e!』のメンバーがいる場合、カードを1枚引く。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → DRAW → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!N-bp1-004-P#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにほかの『虹ヶ咲』のメンバーがいる場合、エネルギーを1枚アクティブにする。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → ACTIVATE_ENERGY → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!HS-PR-019-PR#Ab0

**Text:** {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{hea...

**Frame Flow:** MOVE_TO_DISCARD → GROUP_FILTER → JUMP_IF_FALSE → ADD_HEARTS → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE
- Frame 1: GROUP_FILTER missing target_player: SELF

---

## PL!HS-bp1-008-P#Ab0

**Text:** {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。

**Frame Flow:** MOVE_TO_DISCARD → GROUP_FILTER → NOP → RETURN

**Issues:**
- Frame 1: GROUP_FILTER missing target_player: SELF

---

## PL!SP-bp5-014-N#Ab0

**Text:** {{toujyou.png|登場}}このターン、自分のステージにいるほかのメンバーがエリアを移動している場合、カードを1枚引く。

**Frame Flow:** NOP → JUMP_IF_FALSE → DRAW → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames

---

## PL!HS-sd1-013-SD#Ab0

**Text:** {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_05.png|heart05}}を持つメンバーカードの場合、ライブ終了時まで、{{hea...

**Frame Flow:** MOVE_TO_DISCARD → GROUP_FILTER → JUMP_IF_FALSE → ADD_HEARTS → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE
- Frame 1: GROUP_FILTER missing target_player: SELF

---

## PL!HS-bp1-004-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレー...

**Frame Flow:** PAY_ENERGY → JUMP_IF_FALSE → SUM_VALUE → GROUP_FILTER → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 3: GROUP_FILTER missing target_player: SELF

---

## PL!HS-bp2-005-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージのエリアすべてにメンバーが登場している場合、ライブ終了時まで、{{icon_b...

**Frame Flow:** PAY_ENERGY → JUMP_IF_FALSE → SUM_VALUE → COUNT_STAGE → COUNT_STAGE → COUNT_STAGE → SUM_VALUE → SUM_VALUE → SUM_VALUE → NOP → RETURN

**Issues:**
- Frame 3: Missing target_player: SELF for own stage check
- Frame 4: Missing target_player: SELF for own stage check
- Frame 5: Missing target_player: SELF for own stage check

---

## PL!N-bp3-005-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」...

**Frame Flow:** HAS_KEYWORD → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp2-009-P#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** COUNT_HAND → JUMP_IF_FALSE → DIV_VALUE → ADD_BLADES → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp1-006-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → MOVE_TO_DISCARD → JUMP_IF_FALSE → SUM_VALUE → JUMP_IF_FALSE → ADD_HEARTS → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!-bp4-005-P#Ab2

**Text:** {{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジシ...

**Frame Flow:** IS_CENTER → SELECT_MEMBER → JUMP_IF_FALSE → MOVE_MEMBER → RETURN

**Issues:**
- Frame 1: Missing target_player: SELF for own stage check

---

## PL!SP-bp2-010-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → REDUCE_YELL_COUNT → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!HS-bp2-021-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → REDUCE_HEART_REQ → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!HS-bp2-023-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → REDUCE_HEART_REQ → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!HS-bp2-025-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → REDUCE_HEART_REQ → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!SP-bp5-009-AR#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを控え室に置いてもよい。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これにより控...

**Frame Flow:** MOVE_TO_DISCARD → JUMP_IF_FALSE → ADD_BLADES → DISCARDED_CARDS → JUMP_IF_FALSE → MOVE_TO_DISCARD → JUMP_IF_FALSE → ADD_BLADES → DISCARDED_CARDS → JUMP_IF_FALSE → MOVE_TO_DISCARD → JUMP_IF_FALSE → ADD_BLADES → DISCARDED_CARDS → JUMP_IF_FALSE → MOVE_TO_DISCARD → JUMP_IF_FALSE → ADD_BLADES → DISCARDED_CARDS → JUMP_IF_FALSE → MOVE_TO_DISCARD → JUMP_IF_FALSE → ADD_BLADES → DISCARDED_CARDS → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target
- Frame 7: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target
- Frame 12: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target
- Frame 17: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target
- Frame 22: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp4-017-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}【左サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blad...

**Frame Flow:** HAS_KEYWORD → NOP → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames

---

## PL!SP-bp4-020-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}【右サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blad...

**Frame Flow:** HAS_KEYWORD → NOP → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames

---

## PL!HS-PR-016-PR#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_04.png|heart04}}{{heart_04.p...

**Frame Flow:** MOVE_TO_DISCARD → ADD_HEARTS → ADD_BLADES → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!HS-PR-017-PR#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_05.png|heart05}}{{heart_05.p...

**Frame Flow:** MOVE_TO_DISCARD → ADD_HEARTS → ADD_BLADES → RETURN

**Issues:**
- Frame 0: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!N-bp3-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る。その中から1枚までをデッキの上に置き、残りを控え室に置く。そ...

**Frame Flow:** NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-PR-013-PR#Ab1

**Text:** {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。{{live_start.png|ライブ開始時...

**Frame Flow:** PAY_ENERGY → JUMP_IF_FALSE → SUM_VALUE → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 4: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp5-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_02.png|heart02}}か{{heart_06.png|heart06}}の...

**Frame Flow:** COLOR_SELECT → ADD_HEARTS → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames

---

## PL!N-bp1-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『虹ヶ咲』のメンバーがいる場合、こ...

**Frame Flow:** PAY_ENERGY → JUMP_IF_FALSE → SUM_VALUE → COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 3: Missing target_player: SELF for own stage check
- Frame 5: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp5-017-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『蓮ノ空』のメンバー1人を含むメンバーが2人以上おり、かつそれらのメンバーの...

**Frame Flow:** PAY_ENERGY → JUMP_IF_FALSE → HAS_MEMBER → COUNT_STAGE → NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 3: Missing target_player: SELF for own stage check
- Frame 6: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp4-029-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}このゲームの1ターン目のライブフェイズの場合、このカードのスコアを+１し、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{ico...

**Frame Flow:** NOP → JUMP_IF_FALSE → BOOST_SCORE → ADD_BLADES → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-pb1-037-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを+１する。さらに、自分...

**Frame Flow:** HAS_KEYWORD → JUMP_IF_FALSE → BOOST_SCORE → HAS_KEYWORD → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target
- Frame 5: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-017-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}...

**Frame Flow:** MOVE_MEMBER → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp4-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}アクティブ状態の自分のエネルギーがある場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp5-022-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動したメンバーは{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-sd1-022-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『Aqours』のメンバーは{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-sd1-002-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。こ...

**Frame Flow:** MOVE_TO_DISCARD → JUMP_IF_FALSE → LOOK_DECK → ADD_TO_HAND → NOP → JUMP_IF_FALSE → ADD_HEARTS → ADD_BLADES → RETURN

**Issues:**
- Frame 7: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp5-016-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}相手のステージにいるすべてのメンバーのそれぞれのコストよりコストが高いメンバーが自分のステージにいる場合、ライブ終了時まで、{{icon_blade....

**Frame Flow:** HAS_MEMBER → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp5-027-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつ自分のステージに名前の異なるメンバーが3人以上いる場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_SUCCESS_LIVE → NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp1-027-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のエネルギーが12枚以上ある場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}...

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-sd1-026-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のエネルギーが9枚以上ある場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1...

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp5-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに{{heart_02.png|heart02}}を4つ以上持つメンバーがいる場合、このカードのスコアを+２し、必要ハートは{{hear...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp5-023-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『Aqours』のメンバーと『SaintSnow』のメンバーがいて、かつそれらのメンバーのコストが合計20以上の場合、自分の控え室にあ...

**Frame Flow:** HAS_MEMBER → HAS_MEMBER → COUNT_STAGE → JUMP_IF_FALSE → SELECT_CARDS → RETURN

**Issues:**
- Frame 2: Missing target_player: SELF for own stage check

---

## PL!HS-bp5-021-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『みらくらぱーく！』のメンバーが3人以上いる場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-sd1-018-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーが3人以上いて、かつ自分の控え室にカード名に「DreamBelievers」を含むライブカードがある場合、このカー...

**Frame Flow:** COUNT_GROUP → NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp2-019-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{hear...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → SELECT_MODE → JUMP → JUMP → JUMP → JUMP → SET_HEART_COST → JUMP → SET_HEART_COST → JUMP → SET_HEART_COST → JUMP → JUMP → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!SP-pb1-025-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{...

**Frame Flow:** COUNT_STAGE → REDUCE_HEART_REQ → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames

---

## PL!S-pb1-020-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_04.png|heart04}}が合計10個以上ある場合、このカードのス...

**Frame Flow:** COUNT_HEARTS → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp5-026-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Liella!』のメンバーが持つハートの総数が11以上の場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_HEARTS → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-pb1-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Printemps』のメンバーをアクティブにする。これによりウェイト状態のメンバーが3人以上アクティブ状態になったとき、このカー...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → ACTIVATE_MEMBER → SUM_VALUE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 5: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-020-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが『μ's』のみの場合、自分のステージにいるメンバー1人をポジションチェンジさせてもよい。

**Frame Flow:** GROUP_FILTER → JUMP_IF_FALSE → SELECT_MEMBER → MOVE_MEMBER → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Text has 'only' condition (のみ) but no SUM_VALUE for comparison - may not check properly
- Frame 0: GROUP_FILTER missing target_player: SELF
- Frame 0: GROUP_FILTER value=4 but text says 'only' - should check ALL members are in group

---

## PL!N-sd1-028-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードのスコアを+１する。
(エールをすべ...

**Frame Flow:** TOTAL_BLADES → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp5-026-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{...

**Frame Flow:** NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp5-015-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{...

**Frame Flow:** NOP → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp5-020-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにコスト10以上の『蓮ノ空』のメンバーが2人以上いる場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp5-021-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにメンバーが1人以上いる場合、自分と相手はカードを1枚引き、手札を1枚控え室に置く。2人以上いる場合、さらに自分のステージにいる『μ's...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → SET_TARGET_SELF → DRAW → MOVE_TO_DISCARD → SET_TARGET_OPPONENT → DRAW → MOVE_TO_DISCARD → COUNT_STAGE → JUMP_IF_FALSE → SET_TARGET_SELF → SELECT_MEMBER → ADD_HEARTS → COUNT_STAGE → NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 8: Missing target_player: SELF for own stage check
- Frame 13: Missing target_player: SELF for own stage check

---

## PL!N-pb1-042-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに同じ名前の『虹ヶ咲』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → REDUCE_HEART_REQ → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!HS-bp5-018-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージに名前とコストが両方ともそれぞれ異なるメンバーが3人以上いる場合、このカードのスコアを+１する。

**Frame Flow:** NOP → NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-pb1-023-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージに名前の異なる『CatChu!』のメンバーが2人以上いる場合、エネルギーを6枚までアクティブにする。その後、自分のエネルギーがすべてアク...

**Frame Flow:** COUNT_ENERGY_EXACT → JUMP_IF_FALSE → META_RULE → BOOST_SCORE → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-pb1-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに名前の異なる『KALEIDOSCORE』のメンバーが2人以上いる場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp4-031-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージのエリアすべてに『虹ヶ咲』のメンバーがいて、かつそれらのコストの合計が20以上の場合、カードを3枚引き、自分の手札を3枚好きな順番でデッ...

**Frame Flow:** NOP → GROUP_FILTER → SCORE_COMPARE → JUMP_IF_FALSE → DRAW → SELECT_CARDS → MOVE_TO_DECK → RETURN

**Issues:**
- Frame 1: Missing target_player: SELF for own stage check
- Frame 1: GROUP_FILTER missing target_player: SELF

---

## PL!S-bp3-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージのセンターエリアにコスト9以上の『Aqours』のメンバーがいる場合、以下から1つを選ぶ。
・ライブ終了時まで、自分のステージにいるメン...

**Frame Flow:** HAS_MEMBER → JUMP_IF_FALSE → SELECT_MODE → JUMP → JUMP → SELECT_MEMBER → ADD_BLADES → JUMP → TAP_OPPONENT → JUMP → RETURN

**Issues:**
- SELECT_MEMBER used but text specifies center area - should use COUNT_STAGE with STAGE_2

---

## PL!HS-bp2-026-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージの右サイドエリアに「大沢瑠璃乃」が、左サイドエリアに「安養寺姫芽」が、センターエリアに「藤島慈」がそれぞれ登場している場合、このカードの...

**Frame Flow:** GROUP_FILTER → GROUP_FILTER → GROUP_FILTER → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 1: Missing target_player: SELF for own stage check
- Frame 2: Missing target_player: SELF for own stage check
- Frame 0: GROUP_FILTER missing target_player: SELF
- Frame 1: GROUP_FILTER missing target_player: SELF
- Frame 2: GROUP_FILTER missing target_player: SELF
- Frame 4: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp4-024-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージの左サイドエリアにいる『Liella!』のメンバーが{{heart_02.png|heart02}}を3つ以上持つ場合、そのメンバーは、...

**Frame Flow:** SELECT_MEMBER → JUMP_IF_FALSE → SELECT_MEMBER → ADD_BLADES → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!SP-bp4-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のセンターエリアにいる『Liella!』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを+１する。

**Frame Flow:** SYNC_COST → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp3-022-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のデッキの上から、自分と相手のステージにいるメンバー1人につき、1枚公開する。それらの中にあるライブカード1枚につき、このカードのスコアを+１する...

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → MOVE_TO_DISCARD → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!-bp3-019-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_SUCCESS_LIVE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp1-029-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のライブ中のカードが3枚以上ある場合、このカードのスコアを+２する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー...

**Frame Flow:** GROUP_FILTER → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: GROUP_FILTER missing target_player: SELF
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-014-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持...

**Frame Flow:** HAS_LIVE_CARD → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-pb1-038-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が4の『虹ヶ咲』のライ...

**Frame Flow:** HAS_KEYWORD → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-021-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、このカードを成功させるための必要ハートを{{heart_00.png|heart...

**Frame Flow:** SCORE_TOTAL_CHECK → JUMP_IF_FALSE → REDUCE_HEART_REQ → SCORE_TOTAL_CHECK → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 5: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp3-024-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_SUCCESS_LIVE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-pb1-029-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカードが0枚で、かつ自分のステージにいるメンバーが『lilywhite』のみの場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_SUCCESS_LIVE → COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 1: Missing target_player: SELF for own stage check
- Text has 'only' condition (のみ) but no SUM_VALUE for comparison - may not check properly
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp2-023-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカード枚数が相手より少ない場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_SUCCESS_LIVE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-sd1-009-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の控え室に『μ's』のカードが25枚以上ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

**Frame Flow:** GROUP_FILTER → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: GROUP_FILTER missing target_player: SELF
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp2-022-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の控え室に『スリーズブーケ』のライブカードが3枚以上ある場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_DISCARD → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp4-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが4枚以上ある場合、このカードのスコアを+１する。6枚以上ある場合、代わりにスコアを+２する。

**Frame Flow:** COUNT_DISCARD → JUMP_IF_FALSE → BOOST_SCORE → COUNT_DISCARD → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target
- Frame 5: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp2-008-P#Ab1

**Text:** {{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開...

**Frame Flow:** COUNT_STAGE → GROUP_FILTER → SUM_VALUE → SUM_VALUE → SUM_VALUE → NOP → NOP → NOP → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 1: Missing target_player: SELF for own stage check
- Frame 1: GROUP_FILTER missing target_player: SELF

---

## LL-bp5-001-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが2枚以上あるか、自分のステージにいるメンバーが持つハートの中に{{heart_01.png|...

**Frame Flow:** NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp3-030-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に{{icon_b_all.png|ALLブレード}}を持つカードが1枚以上ある場合、このカードのスコアを+...

**Frame Flow:** NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp5-022-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}エールにより公開されている自分のライブカードの枚数が、エールにより公開されている相手のライブカードの枚数より多い場合、このカードのスコアを+１する...

**Frame Flow:** NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp5-016-N#Ab0

**Text:** {{live_success.png|ライブ成功時}}カードを1枚引き、手札を1枚控え室に置く。

**Frame Flow:** DRAW → MOVE_TO_DISCARD → RETURN

**Issues:**
- Frame 1: Optional MOVE_TO_DISCARD not followed by JUMP_IF_FALSE

---

## PL!N-bp5-006-AR#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージにこのメンバー以外のメンバーがいる場合、このメンバーをウェイトにする。

**Frame Flow:** COUNT_STAGE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!SP-bp4-006-P#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に、名前が異なる『Liella!』のメンバーカードが3枚以上ある場合、エールにより公開された自分のカードの中...

**Frame Flow:** NOP → GROUP_FILTER → RETURN

**Issues:**
- Frame 1: GROUP_FILTER missing target_player: SELF

---

## PL!SP-bp2-024-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分の手札の枚数が相手より多い場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_HAND → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp3-027-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる...

**Frame Flow:** NOP → COUNT_STAGE → JUMP_IF_FALSE → ENERGY_CHARGE → RETURN

**Issues:**
- Frame 1: Missing target_player: SELF for own stage check

---

## PL!S-bp2-022-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを+２する。

**Frame Flow:** DECK_REFRESHED → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp4-025-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分の『虹ヶ咲』のメンバーカードが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.p...

**Frame Flow:** GROUP_FILTER → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 0: GROUP_FILTER missing target_player: SELF
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-sd1-019-SD#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『Aqours』のライブカードを1枚手札に加える。

**Frame Flow:** GROUP_FILTER → RETURN

**Issues:**
- Frame 0: GROUP_FILTER missing target_player: SELF

---

## PL!HS-bp1-022-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを+１する。
(エールをすべて行った後、...

**Frame Flow:** HAS_KEYWORD → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp4-026-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に名前が異なる『Liella!』のメンバーカードが5枚以上ある場合、このカードのスコアを+１する。

**Frame Flow:** NOP → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp1-023-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高く、かつ自分のステージに『蓮ノ空』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状...

**Frame Flow:** SCORE_COMPARE → COUNT_STAGE → JUMP_IF_FALSE → ENERGY_CHARGE → RETURN

**Issues:**
- Frame 1: Missing target_player: SELF for own stage check

---

## PL!SP-bp5-023-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつエールにより公開された自分のカードの中に{{icon_score.png|スコア}}...

**Frame Flow:** COUNT_SUCCESS_LIVE → GROUP_FILTER → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 1: GROUP_FILTER missing target_player: SELF
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp2-025-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分...

**Frame Flow:** COUNT_STAGE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!SP-bp1-024-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。
(必要ハートを確認する時、エールで出た{{icon_b_all.png|...

**Frame Flow:** COUNT_STAGE → COUNT_STAGE → JUMP_IF_FALSE → DRAW → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 1: Missing target_player: SELF for own stage check

---

## PL!S-pb1-021-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手...

**Frame Flow:** COUNT_HEARTS → NOT_HAS_EXCESS_HEART → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp3-026-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを+１する。

**Frame Flow:** HEART_LEAD → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp4-025-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを+１する。

**Frame Flow:** COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-007-P#Ab1

**Text:** {{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１す...

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-pb1-004-P+#Ab1

**Text:** {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時...

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-pb1-013-P+#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する...

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp1-003-P#Ab0

**Text:** {{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!S-bp5-008-AR#Ab0

**Text:** {{jyouji.png|常時}}相手の余剰ハートが2つ以上あるかぎり、自分のライブの合計スコアを+１する。

**Frame Flow:** BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp5-111-P+#Ab0

**Text:** {{jyouji.png|常時}}自分のエネルギーがちょうど8枚あるかぎり、ライブの合計スコアを+１する。

**Frame Flow:** BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-pb1-002-P+#Ab0

**Text:** {{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを+１する。

**Frame Flow:** COUNT_ENERGY → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-018-N#Ab0

**Text:** {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}...

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp5-007-AR#Ab1

**Text:** {{jyouji.png|常時}}自分のステージにこのメンバー以外の『EdelNote』のメンバーがいるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード...

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-pb1-001-P+#Ab1

**Text:** {{jyouji.png|常時}}自分のライブ中のライブカードが2枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-pb1-004-P+#Ab0

**Text:** {{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames

---

## PL!HS-bp5-002-AR#Ab0

**Text:** {{jyouji.png|常時}}自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得...

**Frame Flow:** NOP → JUMP_IF_FALSE → ADD_HEARTS → ADD_BLADES → RETURN

**Issues:**
- Frame 3: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-PR-020-PR#Ab0

**Text:** {{jyouji.png|常時}}自分のステージにいるメンバーがちょうど2人であるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_HEARTS → ADD_BLADES → RETURN

**Issues:**
- Frame 1: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!N-bp1-012-P#Ab0

**Text:** {{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート...

**Frame Flow:** ADD_HEARTS → ADD_BLADES → RETURN

**Issues:**
- Frame 1: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-bp5-004-AR#Ab0

**Text:** {{jyouji.png|常時}}自分のステージにいるコスト4以上の『スリーズブーケ』以外のメンバー1人につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード...

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-020-L#Ab1

**Text:** {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!HS-sd1-005-SD#Ab1

**Text:** {{jyouji.png|常時}}自分のステージに「村野さやか」か「百生吟子」か「安養寺姫芽」がいるかぎり、{{icon_blade.png|ブレード}}を得る。

**Frame Flow:** ADD_BLADES → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-pb1-004-P+#Ab2

**Text:** {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時...

**Frame Flow:** BOOST_SCORE → RETURN

**Issues:**
- Frame 0: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!-bp4-019-L#Ab0

**Text:** {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを+５する。

**Frame Flow:** COUNT_SUCCESS_LIVE → JUMP_IF_FALSE → COUNT_STAGE → JUMP_IF_FALSE → BOOST_SCORE → RETURN

**Issues:**
- Frame 2: Missing target_player: SELF for own stage check
- Frame 4: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target

---

## PL!SP-bp5-017-N#Ab0

**Text:** {{jyouji.png|常時}}自分のステージにいる『Liella!』のメンバーがこのターンにエリアを移動しているかぎり、手札にあるこのメンバーカードのコストは2減る。

**Frame Flow:** NOP → REDUCE_COST → RETURN

**Issues:**
- Text mentions 'moved this turn' but no check_moved_this_turn flag in frames

---

## PL!SP-bp5-001-AR#Ab2

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以...

**Frame Flow:** SELECT_MODE → JUMP → JUMP → SET_TAPPED → JUMP → MOVE_TO_DISCARD → JUMP_IF_FALSE → ACTIVATE_ENERGY → RETURN

**Issues:**
- Frame 3: Optional SET_TAPPED not followed by JUMP_IF_FALSE

---

## PL!N-PR-003-PR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの...

**Frame Flow:** COUNT_STAGE → GROUP_FILTER → JUMP_IF_FALSE → LOOK_AND_CHOOSE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check
- Frame 1: Missing target_player: SELF for own stage check
- Frame 1: GROUP_FILTER missing target_player: SELF

---

## PL!N-pb1-003-P+#Ab0

**Text:** {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージ...

**Frame Flow:** DRAW → SELECT_MEMBER → ADD_BLADES → RETURN

**Issues:**
- Text has 'only' condition (のみ) but no SUM_VALUE for comparison - may not check properly

---

## PL!-pb1-007-P+#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカード...

**Frame Flow:** SELECT_MEMBER → JUMP_IF_FALSE → REDUCE_COST → MOVE_TO_DISCARD → RECOVER_LIVE → RETURN

**Issues:**
- Frame 0: Missing target_player: SELF for own stage check

---

## PL!-bp5-004-AR#Ab1

**Text:** {{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードの中にブレードハートを持たないメンバーカードが3枚以上ある場合、ライブ終了...

**Frame Flow:** GROUP_FILTER → JUMP_IF_FALSE → ADD_HEARTS → RETURN

**Issues:**
- Frame 0: GROUP_FILTER missing target_player: SELF

---

