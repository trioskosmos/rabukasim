# Deep Ability Scan Report

Total abilities scanned: 614
Abilities with issues: 215

## Issue Summary

- Missing frames: 87
- Wrong opcodes: 54
- Needs enhancement: 27
- Structural issues: 132

## PL!N-bp5-014-N#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-PR-007-PR#Ab0

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない

### Needs Enhancement

**Frame 3:**
- Issue: Text says 'may' (してもよい) but MOVE_MEMBER not marked optional
- Current: is_optional: missing
- Fix: Add is_optional: 1 to attr

---

## PL!SP-bp4-008-P#Ab1

**Text:** {{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp1-001-P#Ab0

**Text:** {{toujyou.png|登場}}エネルギーを2枚アクティブにする。

### Structural Issues

**Frame 0:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp2-005-P#Ab0

**Text:** {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。

### Missing Frames

**Frame 3:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!HS-bp5-001-AR#Ab0

**Text:** {{toujyou.png|登場}}自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-015-N#Ab0

**Text:** {{toujyou.png|登場}}{{center.png|センター}}ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-006-P+#Ab1

**Text:** {{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
(対戦相手のカードの効果でも発動する。)

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp5-009-AR#Ab0

**Text:** {{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『SaintSnow』のカードを1枚手札に加える。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 4:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-PR-016-PR#Ab0

**Text:** {{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp5-004-AR#Ab0

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
・自分のステージにいる『SaintSnow』のメンバー1人をポジションチェンジさせる。(このメ

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-005-P+#Ab0

**Text:** {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。

### Missing Frames

**Frame 0:**
- Issue: GROUP_FILTER missing target_slot specification
- Fix: Add target_slot based on text (STAGE_0, STAGE_1, STAGE_2)

---

## PL!-pb1-002-P+#Ab0

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。

### Wrong Opcode

**Frame 0:**
- Issue: GROUP_FILTER used for 'only' condition (value=4)
- Current: GROUP_FILTER
- Fix: Use COUNT_STAGE sequence: count group members, sum, count total, compare with SUM_VALUE EQ

### Needs Enhancement

**Frame 5:**
- Issue: Text says 'may' (してもよい) but MOVE_MEMBER not marked optional
- Current: is_optional: missing
- Fix: Add is_optional: 1 to attr

---

## PL!SP-pb1-011-P+#Ab0

**Text:** {{toujyou.png|登場}}「鬼塚冬毬」以外の『Liella!』のメンバー1人をステージから控え室に置いてもよい：自分の控え室から、これにより控え室に置いたメンバーカードを1枚、そのメンバーがいたエリアに登場させる。

### Missing Frames

**Frame 0:**
- Issue: SELECT_MEMBER missing target_slot specification
- Fix: Add target_slot based on text (STAGE_0, STAGE_1, STAGE_2)

---

## PL!HS-bp2-008-P#Ab0

**Text:** {{toujyou.png|登場}}このメンバーよりコストが低い『DOLLCHESTRA』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-010-P+#Ab0

**Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。

### Structural Issues

**Frame 3:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-008-P+#Ab1

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする。

### Structural Issues

**Frame 5:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-003-P+#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる。

### Needs Enhancement

**Frame 0:**
- Issue: Text mentions center area but frame targets wrong slot
- Current: target_slot: STAGE_0, area_idx: None
- Fix: Set target_slot: STAGE_2 or area_idx: 2

---

## PL!SP-bp4-001-P#Ab0

**Text:** {{toujyou.png|登場}}自分のステージにいるメンバーが『Liella!』のみで、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

### Missing Frames

**Frame 0:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

### Wrong Opcode

**Frame 0:**
- Issue: GROUP_FILTER used for 'only' condition (value=3)
- Current: GROUP_FILTER
- Fix: Use COUNT_STAGE sequence: count group members, sum, count total, compare with SUM_VALUE EQ

---

## PL!HS-bp1-008-P#Ab0

**Text:** {{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。

### Missing Frames

**Frame 1:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!-bp4-004-P#Ab0

**Text:** {{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、エネルギーを2枚アクティブにする。

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-pb1-006-P+#Ab0

**Text:** {{toujyou.png|登場}}自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く。その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く。

### Needs Enhancement

**Frame 2:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

---

## PL!N-bp4-023-N#Ab0

**Text:** {{toujyou.png|登場}}『虹ヶ咲」のメンバー1人をウェイトにしてもよい：カードを1枚引き、手札を1枚控え室に置く。

### Missing Frames

**Frame 0:**
- Issue: SELECT_MEMBER missing target_slot specification
- Fix: Add target_slot based on text (STAGE_0, STAGE_1, STAGE_2)

---

## PL!HS-sd1-006-SD#Ab0

**Text:** {{toujyou.png|登場}}自分のステージに「大沢瑠璃乃」か「百生吟子」か「徒町小鈴」がいる場合、エネルギーを1枚アクティブにし、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-010-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-PR-007-PR#Ab1

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない

### Needs Enhancement

**Frame 3:**
- Issue: Text says 'may' (してもよい) but MOVE_MEMBER not marked optional
- Current: is_optional: missing
- Fix: Add is_optional: 1 to attr

---

## PL!SP-bp5-001-AR#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにするか、手札を1枚控え室に置く：エネルギーを1枚アクティブにする。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp5-003-AR#Ab1

**Text:** {{live_start.png|ライブ開始時}}{{center.png|センター}}自分のステージにいるすべての『Liella!』のメンバーと、自分のすべてのエネルギーをアクティブにする。

### Structural Issues

**Frame 1:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp2-005-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージのエリアすべてにメンバーが登場している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Missing Frames

**Frame 3:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

**Frame 4:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

**Frame 5:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!-bp3-008-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい：ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。

### Missing Frames

**Frame 0:**
- Issue: SELECT_MEMBER missing target_slot specification
- Fix: Add target_slot based on text (STAGE_0, STAGE_1, STAGE_2)

### Needs Enhancement

**Frame 0:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

---

## PL!N-bp3-005-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp2-009-P#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-005-P#Ab2

**Text:** {{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場

### Needs Enhancement

**Frame 1:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

**Frame 1:**
- Issue: Text mentions center area but frame targets wrong slot
- Current: target_slot: STAGE_0, area_idx: None
- Fix: Set target_slot: STAGE_2 or area_idx: 2

---

## PL!HS-PR-001-PR#Ab1

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 4:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-PR-009-PR#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これによりライブカードを控え室に置いた場合、さらにカードを1枚引く。

### Missing Frames

**Frame 1:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-009-AR#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを控え室に置いてもよい。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これにより控え室に置いたカードがライブカードの場合、このメンバーをウェイトにする。自分はこの手順をさらに4回まで

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

**Frame 7:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

**Frame 12:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

**Frame 17:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

**Frame 22:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp1-001-P#Ab0

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-017-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}【左サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（この能力は左サイドエリアにいる場合のみ発動する。）

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-020-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}【右サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（この能力は右サイドエリアにいる場合のみ発動する。）

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-007-P+#Ab0

**Text:** {{live_start.png|ライブ開始時}}エネルギーを2枚アクティブにする。

### Structural Issues

**Frame 0:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-PR-016-PR#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}{{icon_blade.pn

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-PR-017-PR#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}{{icon_blade.pn

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp1-005-P#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 4:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp3-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る。その中から1枚までをデッキの上に置き、残りを控え室に置く。その後、自分のデッキの一番上のカードを1枚公開する。これによりライブカードを公開した場合、このカードの

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-PR-013-PR#Ab1

**Text:** {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよ

### Structural Issues

**Frame 4:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## LL-bp3-001-R+#Ab1

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp1-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『虹ヶ咲』のメンバーがいる場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|

### Wrong Opcode

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!HS-bp5-017-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『蓮ノ空』のメンバー1人を含むメンバーが2人以上おり、かつそれらのメンバーのユニット名がそれぞれ異なる場合、このカードのスコアを+１する。

### Missing Frames

**Frame 3:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

### Wrong Opcode

**Frame 6:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!N-bp4-029-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}このゲームの1ターン目のライブフェイズの場合、このカードのスコアを+１し、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-037-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを+１する。さらに、自分の『虹ヶ咲』のカードの効果によって自分のステージにいるウェイト状態のメンバーもアクティブにしていた場

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-011-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Wrong Opcode

**Frame 2:**
- Issue: SELECT_MEMBER used for automatic center area check
- Current: SELECT_MEMBER
- Fix: COUNT_STAGE with STAGE_2 target and JUMP_IF_FALSE

### Needs Enhancement

**Frame 2:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

---

## PL!-bp4-017-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}アクティブ状態の自分のエネルギーがある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-023-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「澁谷かのん」「ウィーン・マルガレーテ」「鬼塚冬毬」のうちのメンバー1人と、これにより選んだメンバー以外の『Liella!』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。

### Needs Enhancement

**Frame 0:**
- Issue: Text mentions Liella! but frame has no group_id filter
- Current: group_enabled: 0
- Fix: Add attr: {group_enabled: 1, group_id: "LIELLA"}

---

## PL!S-bp5-022-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、このターン中にエリアを移動したメンバーは{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-sd1-022-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『Aqours』のメンバーは{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## LL-bp1-001-R+#Ab1

**Text:** {{live_start.png|ライブ開始時}}手札の「上原歩夢」と「澁谷かのん」と「日野下花帆」を、好きな組み合わせで合計3枚、控え室に置いてもよい：ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+３する。」を得る。
（手札のこのカードもこの効果で控え室に置ける。）

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-sd1-009-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札の『Aqours』のカードを1枚公開してもよい：これにより公開したカードをデッキの一番上か一番下に置き、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 8:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-sd1-004-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 4:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-sd1-003-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_b

### Structural Issues

**Frame 4:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-sd1-002-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。これにより『蓮ノ空』のカードを手札に加えた場合、ライブ終了時まで、{{heart_05.png|hea

### Structural Issues

**Frame 7:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## LL-PR-004-PR#Ab0

**Text:** {{live_start.png|ライブ開始時}}相手に何が好き？と聞く。
回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。
回答があなたの場合、自分と相手はカードを1枚引く。
回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにい

### Structural Issues

**Frame 6:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp5-016-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}相手のステージにいるすべてのメンバーのそれぞれのコストよりコストが高いメンバーが自分のステージにいる場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-027-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつ自分のステージに名前の異なるメンバーが3人以上いる場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp1-027-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のエネルギーが12枚以上ある場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-sd1-026-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のエネルギーが9枚以上ある場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに{{heart_02.png|heart02}}を4つ以上持つメンバーがいる場合、このカードのスコアを+２し、必要ハートは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!S-bp5-023-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『Aqours』のメンバーと『SaintSnow』のメンバーがいて、かつそれらのメンバーのコストが合計20以上の場合、自分の控え室にある『Aqours』と『SaintSnow』のライブカードを4枚まで好きな順番でデッキの上に置いてもよ

### Needs Enhancement

**Frame 2:**
- Issue: Text mentions Aqours but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "AQOURS"}

---

## PL!HS-bp5-021-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『みらくらぱーく！』のメンバーが3人以上いる場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!HS-sd1-018-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーが3人以上いて、かつ自分の控え室にカード名に「DreamBelievers」を含むライブカードがある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-025-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。

### Missing Frames

**Frame 0:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!S-pb1-020-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_04.png|heart04}}が合計10個以上ある場合、このカードのスコアを+２する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-026-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Liella!』のメンバーが持つハートの総数が11以上の場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-pb1-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『Printemps』のメンバーをアクティブにする。これによりウェイト状態のメンバーが3人以上アクティブ状態になったとき、このカードのスコアを+１する。

### Wrong Opcode

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!-bp4-020-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが『μ's』のみの場合、自分のステージにいるメンバー1人をポジションチェンジさせてもよい。

### Wrong Opcode

**Frame 0:**
- Issue: GROUP_FILTER used for 'only' condition (value=4)
- Current: GROUP_FILTER
- Fix: Use COUNT_STAGE sequence: count group members, sum, count total, compare with SUM_VALUE EQ

### Needs Enhancement

**Frame 2:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

---

## PL!N-sd1-028-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-026-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-015-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp5-020-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにコスト10以上の『蓮ノ空』のメンバーが2人以上いる場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!-bp5-021-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージにメンバーが1人以上いる場合、自分と相手はカードを1枚引き、手札を1枚控え室に置く。2人以上いる場合、さらに自分のステージにいる『μ's』のメンバー1人は、ライブ終了時まで、{{heart_03.png|heart03}}を得る。3人以

### Missing Frames

**Frame 13:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

### Needs Enhancement

**Frame 0:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

**Frame 8:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

**Frame 13:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

---

## PL!HS-bp5-018-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージに名前とコストが両方ともそれぞれ異なるメンバーが3人以上いる場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-023-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分のステージに名前の異なる『CatChu!』のメンバーが2人以上いる場合、エネルギーを6枚までアクティブにする。その後、自分のエネルギーがすべてアクティブ状態の場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージに名前の異なる『KALEIDOSCORE』のメンバーが2人以上いる場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!N-bp4-031-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージのエリアすべてに『虹ヶ咲』のメンバーがいて、かつそれらのコストの合計が20以上の場合、カードを3枚引き、自分の手札を3枚好きな順番でデッキの上に置く。

### Missing Frames

**Frame 1:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!S-bp3-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージのセンターエリアにコスト9以上の『Aqours』のメンバーがいる場合、以下から1つを選ぶ。
・ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード

### Needs Enhancement

**Frame 5:**
- Issue: Text mentions Aqours but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "AQOURS"}

**Frame 5:**
- Issue: Text mentions center area but frame targets wrong slot
- Current: target_slot: CONTEXT, area_idx: None
- Fix: Set target_slot: STAGE_2 or area_idx: 2

---

## PL!HS-bp2-026-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のステージの右サイドエリアに「大沢瑠璃乃」が、左サイドエリアに「安養寺姫芽」が、センターエリアに「藤島慈」がそれぞれ登場している場合、このカードのスコアを+２する。

### Missing Frames

**Frame 0:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

**Frame 1:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

### Wrong Opcode

**Frame 4:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 4:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-022-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のセンターエリアに{{icon_blade.png|ブレード}}を9つ以上持つ『μ's』のメンバーがいる場合、このカードのスコアを+２する。

### Needs Enhancement

**Frame 0:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

**Frame 0:**
- Issue: Text mentions center area but frame targets wrong slot
- Current: target_slot: STAGE_0, area_idx: None
- Fix: Set target_slot: STAGE_2 or area_idx: 2

---

## PL!SP-bp4-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のセンターエリアにいる『Liella!』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp2-023-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のライブカード置き場に「MY舞☆TONIGHT」以外の『Aqours』のライブカードがある場合、ライブ終了時まで、自分のステージのメンバーは{{icon_blade.png|ブレード}}を得る。

### Needs Enhancement

**Frame 2:**
- Issue: Text mentions Aqours but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "AQOURS"}

---

## PL!-bp3-019-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp1-029-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のライブ中のカードが3枚以上ある場合、このカードのスコアを+２する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-014-N#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがある場合、ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-038-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が4の『虹ヶ咲』のライブカードがある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-021-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。スコアの合計が９以上の場合、さらにこのカードのスコアを+１する。

### Wrong Opcode

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp3-024-L#Ab1

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp3-024-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分のステージに

### Needs Enhancement

**Frame 6:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

**Frame 9:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

**Frame 12:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

---

## PL!-pb1-029-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカードが0枚で、かつ自分のステージにいるメンバーが『lilywhite』のみの場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!SP-bp2-023-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカード枚数が相手より少ない場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-sd1-009-SD#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の控え室に『μ's』のカードが25枚以上ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp2-022-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の控え室に『スリーズブーケ』のライブカードが3枚以上ある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp4-028-L#Ab0

**Text:** {{live_start.png|ライブ開始時}}自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが4枚以上ある場合、このカードのスコアを+１する。6枚以上ある場合、代わりにスコアを+２する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp2-008-P#Ab1

**Text:** {{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを+１する。ライブカードが

### Missing Frames

**Frame 0:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

**Frame 1:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## LL-bp5-001-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが2枚以上あるか、自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{heart_05.png|

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp3-025-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}このターン、自分が余剰ハートを持たない場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp3-030-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に{{icon_b_all.png|ALLブレード}}を持つカードが1枚以上ある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp5-022-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}エールにより公開されている自分のライブカードの枚数が、エールにより公開されている相手のライブカードの枚数より多い場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-010-AR#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分が余剰ハートを持たない場合、ライブの合計スコアを+１する。自分が余剰ハートを2つ以上持つ場合、ライブの合計スコアを－１する。この効果ではライブの合計スコアは０未満にはならない。

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

**Frame 5:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-006-AR#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージにこのメンバー以外のメンバーがいる場合、このメンバーをウェイトにする。

### Missing Frames

**Frame 0:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!SP-pb1-001-P+#Ab1

**Text:** {{live_success.png|ライブ成功時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|

### Structural Issues

**Frame 4:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-006-P#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に、名前が異なる『Liella!』のメンバーカードが3枚以上ある場合、エールにより公開された自分のカードの中から『Liella!』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 1:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!N-bp4-001-P#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分のエネルギーが相手より少ない場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp2-024-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分の手札の枚数が相手より多い場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp2-022-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを+２する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp4-025-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分の『虹ヶ咲』のメンバーカードが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.p

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-sd1-019-SD#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『Aqours』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: GROUP_FILTER not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!HS-bp1-022-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-026-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に名前が異なる『Liella!』のメンバーカードが5枚以上ある場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-023-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分か相手の成功ライブカード置き場にカードが2枚以上あり、かつエールにより公開された自分のカードの中に{{icon_score.png|スコア}}を持つライブカードが1枚以上ある場合、このカードのスコアを+２する。

### Wrong Opcode

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp5-020-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分が余剰ハートを3つ以上持っている場合、それらをすべて失い、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp2-025-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分のカードの中から、カードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!SP-bp1-024-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)

### Missing Frames

**Frame 0:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!S-pb1-021-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手が余剰のハートを持たずにライブを成功させていた場合、このカードのスコアを+２する。

### Wrong Opcode

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 3:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-027-L#Ab0

**Text:** {{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。(メンバーをそれぞれ好きなエリアに移動させる。この効果で1つのエリアに2人以上のメンバーを移動させることはできない。)

### Missing Frames

**Frame 0:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

### Needs Enhancement

**Frame 2:**
- Issue: Text mentions Liella! but frame has no group_id filter
- Current: group_enabled: 0
- Fix: Add attr: {group_enabled: 1, group_id: "LIELLA"}

---

## PL!-bp3-026-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-025-L#Ab1

**Text:** {{live_success.png|ライブ成功時}}自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを+１する。

### Wrong Opcode

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!-bp4-005-P#Ab1

**Text:** {{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを+１する。

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-007-P#Ab1

**Text:** {{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-pb1-004-P+#Ab1

**Text:** {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-pb1-013-P+#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp1-003-P#Ab0

**Text:** {{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp3-009-P#Ab1

**Text:** {{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp4-012-P#Ab0

**Text:** {{jyouji.png|常時}}相手の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ライブの合計スコアを+１する。

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-002-AR#Ab0

**Text:** {{jyouji.png|常時}}自分と相手のステージの中で、このメンバーがほかのすべてのメンバーより多くのハートを持つかぎり、ライブの合計スコアを+１する。

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-002-P+#Ab1

**Text:** {{jyouji.png|常時}}このメンバーの下にエネルギーカードが2枚以上置かれているかぎり、ライブの合計スコアを+１する。
(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp3-001-P#Ab1

**Text:** {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。（この能力はセンターエリ

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp5-008-AR#Ab0

**Text:** {{jyouji.png|常時}}相手の余剰ハートが2つ以上あるかぎり、自分のライブの合計スコアを+１する。

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-111-P+#Ab0

**Text:** {{jyouji.png|常時}}自分のエネルギーがちょうど8枚あるかぎり、ライブの合計スコアを+１する。

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-002-P+#Ab0

**Text:** {{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを+１する。

### Structural Issues

**Frame 2:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-018-N#Ab0

**Text:** {{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp5-007-AR#Ab1

**Text:** {{jyouji.png|常時}}自分のステージにこのメンバー以外の『EdelNote』のメンバーがいるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-001-P+#Ab1

**Text:** {{jyouji.png|常時}}自分のライブ中のライブカードが2枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-pb1-004-P+#Ab0

**Text:** {{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp4-003-P#Ab1

**Text:** {{jyouji.png|常時}}{{center.png|センター}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp5-002-AR#Ab0

**Text:** {{jyouji.png|常時}}自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 3:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-PR-020-PR#Ab0

**Text:** {{jyouji.png|常時}}自分のステージにいるメンバーがちょうど2人であるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 1:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp1-012-P#Ab0

**Text:** {{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得

### Structural Issues

**Frame 1:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-PR-029-PR#Ab0

**Text:** {{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 1:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp5-004-AR#Ab0

**Text:** {{jyouji.png|常時}}自分のステージにいるコスト4以上の『スリーズブーケ』以外のメンバー1人につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-020-L#Ab1

**Text:** {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-sd1-005-SD#Ab1

**Text:** {{jyouji.png|常時}}自分のステージに「村野さやか」か「百生吟子」か「安養寺姫芽」がいるかぎり、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp1-004-P#Ab0

**Text:** {{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-pb1-004-P+#Ab2

**Text:** {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、

### Structural Issues

**Frame 0:**
- Issue: BOOST_SCORE uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-019-L#Ab0

**Text:** {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを+５する。

### Wrong Opcode

**Frame 4:**
- Issue: BOOST_SCORE uses CONTEXT but text says 'this card'
- Current: target_slot: CONTEXT
- Fix: Should use CARD_SELF or similar explicit target

---

## PL!-PR-003-PR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_03.png|heart03}}を3以上含むライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-PR-004-PR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_01.png|heart01}}を3以上含むライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-bp5-009-AR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_06.png|heart06}}を3以上含むライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-bp1-012-P#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp5-111-P+#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー2枚をエネルギーデッキに置く：自分の控え室にあるライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-sd1-005-PRproteinbar#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のメンバーカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-PR-012-PR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：カードを1枚引く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!HS-bp1-007-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp1-003-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-pb1-006-P+#Ab0

**Text:** {{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。

### Structural Issues

**Frame 0:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-001-AR#Ab2

**Text:** {{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
・カードを1枚引く。
{{kidou.png|起動}}{{tur

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

**Frame 3:**
- Issue: Optional SET_TAPPED missing JUMP_IF_FALSE after
- Fix: Add JUMP_IF_FALSE to skip effect if cost not paid

### Structural Issues

**Frame 7:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp3-004-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-pb1-011-P+#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-sd1-007-SD#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!S-bp3-006-P#Ab0

**Text:** {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Needs Enhancement

**Frame 4:**
- Issue: Text mentions center area but frame targets wrong slot
- Current: target_slot: CONTEXT, area_idx: None
- Fix: Set target_slot: STAGE_2 or area_idx: 2

---

## PL!S-bp3-001-P#Ab0

**Text:** {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。（この能力はセンターエリ

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

**Frame 2:**
- Issue: SELECT_MEMBER missing target_slot specification
- Fix: Add target_slot based on text (STAGE_0, STAGE_1, STAGE_2)

### Needs Enhancement

**Frame 2:**
- Issue: Text mentions center area but frame targets wrong slot
- Current: target_slot: , area_idx: None
- Fix: Set target_slot: STAGE_2 or area_idx: 2

---

## PL!HS-bp1-004-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!HS-bp5-001-AR#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札のライブカードを1枚公開する：自分の控え室から、これにより公開したカードのカード名がすべて含まれるライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-bp5-003-AR#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：これにより控え室に置いたカードが『μ's』のカードの場合、自分のデッキの上からカードを4枚見る。その中からカードを2枚手札

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!HS-bp5-002-AR#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアに登場させる。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!S-bp5-111-P+#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーを『Aqours』か『SaintSnow』のメンバーがいるエリアにポジションチェンジする。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!HS-bp1-003-P#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-bp3-009-P#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-bp3-001-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを1枚引き、手札を1枚控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp1-009-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：カードを1枚引き、手札を1枚控え室に置く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-bp3-008-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-bp3-008-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

**Frame 0:**
- Issue: SELECT_MEMBER missing target_slot specification
- Fix: Add target_slot based on text (STAGE_0, STAGE_1, STAGE_2)

---

## PL!N-bp5-012-AR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：カードを1枚引き、ライブ終了時まで、{{heart_01.png|heart01}}を得る。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp5-005-AR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：ライブ終了時まで、これにより控え室に置いた『Liella!』のメンバーカード1枚につき、{{icon_blade.png|ブレード}}を得る。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 2:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp2-006-P#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。
({{toujyou.png|登場}}能力がコストを持つ

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-bp1-006-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 3:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp4-002-P#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp5-002-AR#Ab0

**Text:** {{kidou.png|起動}}【左サイド】{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを3枚引き、手札を2枚控え室に置く。これにより控え室に置いたカードの中にブレードハートを持たないメンバーカードが1枚以上ある場合、このメンバーをアクティブにする。2枚ある場合、さらに

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 8:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-008-AR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：エネルギーを2枚アクティブにする。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 1:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-006-AR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}デッキの上からカードを3枚控え室に置く：このメンバーはポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-bp5-003-AR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、そのライブカードを手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-PR-003-PR#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

**Frame 0:**
- Issue: COUNT_STAGE not followed by JUMP_IF_FALSE
- Fix: Add JUMP_IF_FALSE to skip effect if condition fails

---

## PL!-pb1-001-P+#Ab0

**Text:** {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp1-010-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!S-sd1-005-SD#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『Aqours』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!S-sd1-007-SD#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から{{icon_score.png|スコア}}を持つ『Aqours』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-pb1-013-P+#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!HS-bp2-001-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からスコア3以下の『蓮ノ空』のライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp4-010-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}このメンバーをウェイトにする：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-bp2-008-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!S-bp3-007-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く。そうした場合、自分はカードを1枚引く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-bp1-008-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のメンバーカードを1枚控え室に置く：自分の控え室から、これにより控え室に置いたメンバーカードより、コストの低いメンバーカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!S-pb1-006-P+#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.p

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 6:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-bp5-111-P+#Ab1

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：ウェイト状態のメンバー1人をアクティブにする。これにより相手のステージにいるメンバーをアクティブにした場合、自分の控え室からライブカードを1枚手札に加える。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!N-bp4-008-P#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：エネルギー1枚か『虹ヶ咲』のメンバー1人をアクティブにする。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 3:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!-pb1-007-P+#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力を起動するためのコストは、自分の成功ライブカード置き場にあるカード1枚に

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Needs Enhancement

**Frame 0:**
- Issue: Text mentions μ's but frame has wrong/missing group_id
- Fix: Add attr: {group_enabled: 1, group_id: "MUSE"}

---

## PL!S-bp3-008-P#Ab0

**Text:** {{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。それがスコア6以上の『Aqours』のライブカードの場合、エネルギーを4枚アクティブにする。

### Structural Issues

**Frame 4:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-bp5-020-N#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!SP-sd1-011-SD#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## PL!-sd1-008-SD#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のデッキの上からカードを10枚控え室に置く。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

---

## LL-bp3-001-R+#Ab0

**Text:** {{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚までアクティブにする。

### Missing Frames

**Frame 0:**
- Issue: Missing once-per-turn check for ターン1回 startup ability
- Fix: Add CHECK_ONCE_PER_TURN as first frame

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!N-bp5-005-AR#Ab0

**Text:** {{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、このメンバーがコスト10以上のブレードハートを持たない『虹ヶ咲』のメンバーとバトンタッチしていた場合、エネルギーを2枚アクティブにする。コスト15以上のブレードハートを持たない『虹ヶ咲』のメンバーの場合、さらにカードを1

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-sd1-001-SD#Ab0

**Text:** {{jidou.png|自動}}このメンバーがコスト10以上の『蓮ノ空』のメンバーとバトンタッチして控え室に置かれた
とき、エネルギーを2枚アクティブにする。

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!S-bp5-222-P+#Ab1

**Text:** {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、エネルギーを2枚アクティブにする。

### Structural Issues

**Frame 2:**
- Issue: ACTIVATE_ENERGY uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!SP-pb1-006-P+#Ab0

**Text:** {{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
(対戦相手のカードの効果でも発動する。)

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

## PL!HS-bp5-014-N#Ab0

**Text:** {{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。

### Structural Issues

**Frame 0:**
- Issue: ADD_BLADES uses CONTEXT but no prior member selection
- Fix: Add SELECT_MEMBER before or use explicit target

---

