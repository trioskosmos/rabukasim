# Ability Frame Documentation
Generated from ability_frame_source.json
Total frame types: 103
Total frames: 2673
---

## RETURN
**Frequency:** 615 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```
**Matching text:** `{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。...`
**Card examples:** PL!S-bp2-004-P | 黒澤ダイヤ (ab#0), PL!S-bp2-004-R | 黒澤ダイヤ (ab#0)

---

## JUMP_IF_FALSE
**Frequency:** 469 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブカード置き場にあるカードの必要ハートに含まれる{{heart_04.png|heart04}}の合計が4以上の場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。...`
**Card examples:** PL!S-bp5-013-N | 黒澤ダイヤ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：自分のデッキの上から、自分のライブの合計スコアに2を足した数に等しい枚数見る。その中からカードを1枚手札に加える。残りを控え室に置く。...`
**Card examples:** PL!-bp5-001-AR | 高坂穂乃果 (ab#0), PL!-bp5-001-R+ | 高坂穂乃果 (ab#0), PL!-bp5-001-P | 高坂穂乃果 (ab#0)

---

## MOVE_TO_DISCARD
**Frequency:** 162 occurrences

### Parameter Variations
19 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "zone_mask": "Guest+Friend"
  },
  "slot": {
    "target_slot": "STAGE_1",
    "source_zone": "HAND",
    "dest_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。...`
**Card examples:** PL!HS-bp1-010-N | 日野下花帆 (ab#0), PL!HS-bp1-014-N | 大沢瑠璃乃 (ab#0), PL!N-bp1-014-N | 中須かすみ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。...`
**Card examples:** PL!-sd1-011-SD | 絢瀬 絵里 (ab#0), PL!-sd1-012-SD | 南 ことり (ab#0), PL!-sd1-016-SD | 東條 希 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "MOVE_TO_DISCARD",
  "value": 3,
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DECK_TOP",
    "dest_zone": "DISCARD"
  },
  "frame_index": 0
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!HS-bp5-013-N | 徒町 小鈴 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "remainder_zone": "DISCARD",
    "source_zone": "STAGE",
    "dest_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...`
**Card examples:** PL!N-bp1-002-P | 中須かすみ (ab#0), PL!N-bp1-002-R+ | 中須かすみ (ab#0), PL!N-bp1-002-P+ | 中須かすみ (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "HAND",
    "dest_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**Card examples:** PL!SP-PR-004-PR | 唐 可可 (ab#0), PL!SP-PR-006-PR | 平安名すみれ (ab#0), PL!SP-PR-013-PR | 鬼塚冬毬 (ab#0)

... and 14 more variations

---

## JUMP
**Frequency:** 111 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "JUMP",
  "value": 1,
  "frame_index": 3
}
```
**Matching text:** `{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。...`
**Card examples:** PL!SP-bp4-011-P | 鬼塚冬毬 (ab#0), PL!SP-bp4-011-R+ | 鬼塚冬毬 (ab#0), PL!SP-bp4-011-P+ | 鬼塚冬毬 (ab#0)

---

## ADD_BLADES
**Frequency:** 89 occurrences

### Parameter Variations
9 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ADD_BLADES",
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  },
  "frame_index": 3
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!HS-bp5-013-N | 徒町 小鈴 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "ADD_BLADES",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "AQOURS"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
・自分のステージにいる『SaintSnow』のメンバー1人をポジションチェンジさせる。(このメ...`
**Card examples:** PL!S-bp5-004-AR | 黒澤ダイヤ (ab#0), PL!S-bp5-004-R | 黒澤ダイヤ (ab#0), PL!S-bp5-004-P | 黒澤ダイヤ (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "ADD_BLADES",
  "frame_index": 5,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "STAGE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!HS-bp1-004-P | 夕霧綴理 (ab#1), PL!HS-bp1-004-R+ | 夕霧綴理 (ab#1), PL!HS-bp1-004-P+ | 夕霧綴理 (ab#1)

#### Variation 4
**Frame structure:**
```json
{
  "op": "ADD_BLADES",
  "frame_index": 1,
  "value": 2,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "target_slot": "STAGE_1",
    "remainder_zone": "STAGE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 2,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いたカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!S-bp3-003-P | 松浦果南 (ab#1), PL!S-bp3-003-R+ | 松浦果南 (ab#1), PL!S-bp3-003-P+ | 松浦果南 (ab#1)

#### Variation 5
**Frame structure:**
```json
{
  "op": "ADD_BLADES",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!HS-PR-001-PR | 日野下花帆 (ab#1), PL!HS-PR-002-PR | 村野さやか (ab#1), PL!HS-PR-005-PR | 大沢瑠璃乃 (ab#1)

... and 4 more variations

---

## DRAW
**Frequency:** 87 occurrences

### Parameter Variations
5 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "DRAW",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。...`
**Card examples:** PL!HS-bp1-010-N | 日野下花帆 (ab#0), PL!HS-bp1-014-N | 大沢瑠璃乃 (ab#0), PL!N-bp1-014-N | 中須かすみ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "DRAW",
  "value": 0,
  "attr": {
    "compare_accumulated": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  },
  "frame_index": 1
}
```
**Matching text:** `{{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。...`
**Card examples:** PL!HS-bp1-005-P | 大沢瑠璃乃 (ab#0), PL!HS-bp1-005-R | 大沢瑠璃乃 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "DRAW",
  "frame_index": 0,
  "value": 3,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。...`
**Card examples:** PL!S-bp3-003-P | 松浦果南 (ab#0), PL!S-bp3-003-R+ | 松浦果南 (ab#0), PL!S-bp3-003-P+ | 松浦果南 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "DRAW",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  },
  "params": {
    "per_card": "ENERGY",
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 6
    }
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のエネルギー6枚につき、カードを1枚引く。...`
**Card examples:** PL!SP-sd1-001-SD | 澁谷かのん (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "DRAW",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "AQOURS",
    "compare_accumulated": 1
  },
  "slot": {
    "target_slot": "STAGE_1",
    "remainder_zone": "STAGE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバー1人につき、カードを1枚引く。その後、これにより引いた枚数と同じ枚数を手札から控え室に置く。...`
**Card examples:** PL!S-sd1-020-SD | JIMO-AI Dash! (ab#0)

---

## ADD_HEARTS
**Frequency:** 81 occurrences

### Parameter Variations
14 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ADD_HEARTS",
  "frame_index": 5,
  "value": 2,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  },
  "params": {
    "heart_type": 0
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.png|heart01}}...`
**Card examples:** PL!HS-bp2-009-P | 安養寺 姫芽 (ab#0), PL!HS-bp2-009-R | 安養寺 姫芽 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "ADD_HEARTS",
  "frame_index": 3,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  },
  "params": {
    "heart_type": 0
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。...`
**Card examples:** PL!HS-PR-021-PR | 安養寺 姫芽 (ab#0), PL!HS-PR-021-RM | 安養寺 姫芽 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "ADD_HEARTS",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "card_type": "MEMBER"
  },
  "slot": {
    "target_slot": "CONTEXT"
  },
  "params": {
    "heart_type": 3
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。...`
**Card examples:** PL!HS-PR-019-PR | 百生 吟子 (ab#0), PL!HS-PR-019-RM | 百生 吟子 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "ADD_HEARTS",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER"
  },
  "slot": {
    "target_slot": "CONTEXT"
  },
  "params": {
    "heart_type": 4
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_05.png|heart05}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_05.png|heart05}}を得る。...`
**Card examples:** PL!HS-sd1-013-SD | 徒町小鈴 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "ADD_HEARTS",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "SUCCESS_PILE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    },
    "heart_type": "SELECTED"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハート...`
**Card examples:** PL!-bp3-011-N | 絢瀬絵里 (ab#0), PL!-bp3-012-N | 南ことり (ab#0), PL!-bp3-012-PR | 南 ことり (ab#0)

... and 9 more variations

---

## BOOST_SCORE
**Frequency:** 79 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "BOOST_SCORE",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。...`
**Card examples:** PL!N-bp3-005-P | 宮下 愛 (ab#1), PL!N-bp3-005-R+ | 宮下 愛 (ab#1), PL!N-bp3-005-P+ | 宮下 愛 (ab#1)

#### Variation 2
**Frame structure:**
```json
{
  "op": "BOOST_SCORE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "STAGE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバーが持つ{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_02.png|heart02}}、{{...`
**Card examples:** PL!N-bp1-027-L | Solitude Rain (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "BOOST_SCORE",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "HASUNOSORA",
    "unique_names": 1,
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "STAGE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 2,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを+２する。...`
**Card examples:** PL!HS-bp2-020-L | Link to the FUTURE (ab#1)

#### Variation 4
**Frame structure:**
```json
{
  "op": "BOOST_SCORE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "is_tapped": 1,
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "STAGE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを+１する。...`
**Card examples:** PL!N-bp3-031-L | MONSTER GIRLS (ab#0)

---

## SELECT_MEMBER
**Frequency:** 71 occurrences

### Parameter Variations
30 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1,
    "zone_mask": "Guest+Friend"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "HAND"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「上原歩夢」のメンバーカードを1枚ステージに登場させる。...`
**Card examples:** PL!N-pb1-013-P+ | 上原歩夢 (ab#0), PL!N-pb1-013-R | 上原歩夢 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "OPPONENT",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない...`
**Card examples:** PL!-PR-007-PR | 東條 希 (ab#0), PL!-PR-009-PR | 矢澤にこ (ab#0), PL!N-bp3-017-N | 宮下 愛 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。...`
**Card examples:** PL!SP-bp2-001-P | 澁谷かのん (ab#0), PL!SP-bp2-001-R+ | 澁谷かのん (ab#0), PL!SP-bp2-001-P+ | 澁谷かのん (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE",
    "area_idx": 2
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分と相手は、自身のステージのセンターにいるメンバーをポジションチェンジする。(センターにいるメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはセンターエリアに移動させる。)...`
**Card examples:** PL!SP-bp5-010-AR | ウィーン・マルガレーテ (ab#0), PL!SP-bp5-010-R | ウィーン・マルガレーテ (ab#0), PL!SP-bp5-010-P | ウィーン・マルガレーテ (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "target_player": "OPPONENT"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  },
  "params": {
    "filter": "BLADE_LE3"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。...`
**Card examples:** PL!-pb1-002-P+ | 絢瀬絵里 (ab#0), PL!-pb1-002-R | 絢瀬絵里 (ab#0)

... and 25 more variations

---

## NOP
**Frequency:** 70 occurrences

### Parameter Variations
22 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "NOP",
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  },
  "frame_index": 0
}
```
**Matching text:** `{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。...`
**Card examples:** PL!SP-bp4-011-P | 鬼塚冬毬 (ab#0), PL!SP-bp4-011-R+ | 鬼塚冬毬 (ab#0), PL!SP-bp4-011-P+ | 鬼塚冬毬 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "NOP",
  "frame_index": 0,
  "attr": {
    "unit_enabled": 1,
    "unit_id": "CERISE_BOUQUET"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。...`
**Card examples:** PL!HS-bp2-007-P | 百生 吟子 (ab#0), PL!HS-bp2-007-R+ | 百生 吟子 (ab#0), PL!HS-bp2-007-P+ | 百生 吟子 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "NOP",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "group_enabled": 1,
    "group_id": "LIELLA",
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。...`
**Card examples:** PL!SP-bp2-001-P | 澁谷かのん (ab#0), PL!SP-bp2-001-R+ | 澁谷かのん (ab#0), PL!SP-bp2-001-P+ | 澁谷かのん (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "NOP",
  "frame_index": 3,
  "value": 1,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『SaintSnow』のカードを1枚手札に加える。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!S-bp5-009-AR | 黒澤ルビィ (ab#0), PL!S-bp5-009-R | 黒澤ルビィ (ab#0), PL!S-bp5-009-P | 黒澤ルビィ (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "NOP",
  "frame_index": 3,
  "value": 0,
  "params": {
    "raw_cond": "UNIQUE_DISCARD_LIVE_NAMES_COUNT",
    "MIN": 3
  }
}
```
**Matching text:** `{{toujyou.png|登場}}以下から1つを選ぶ。
・自分の控え室にカード名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
・自分の控え室にグループ名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを2枚手札に加える。...`
**Card examples:** PL!N-bp5-011-AR | ミア・テイラー (ab#0), PL!N-bp5-011-R | ミア・テイラー (ab#0), PL!N-bp5-011-P | ミア・テイラー (ab#0)

... and 17 more variations

---

## SUM_VALUE
**Frequency:** 65 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SUM_VALUE",
  "frame_index": 4
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。...`
**Card examples:** PL!SP-bp1-002-P | 唐 可可 (ab#0), PL!SP-bp1-002-R+ | 唐 可可 (ab#0), PL!SP-bp1-002-P+ | 唐 可可 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SUM_VALUE",
  "frame_index": 4,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。...`
**Card examples:** PL!HS-bp2-005-P | 大沢瑠璃乃 (ab#0), PL!HS-bp2-005-R+ | 大沢瑠璃乃 (ab#0), PL!HS-bp2-005-P+ | 大沢瑠璃乃 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "SUM_VALUE",
  "frame_index": 0,
  "value": 2,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}相手の手札の枚数が自分より2枚以上多い場合、自分の控え室からライブカードを1枚手札に加える。...`
**Card examples:** PL!S-pb1-001-P+ | 高海千歌 (ab#0), PL!S-pb1-001-R | 高海千歌 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "SUM_VALUE",
  "frame_index": 4,
  "value": 6
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで...`
**Card examples:** PL!N-bp3-009-P | 天王寺璃奈 (ab#0), PL!N-bp3-009-R+ | 天王寺璃奈 (ab#0), PL!N-bp3-009-P+ | 天王寺璃奈 (ab#0)

---

## PAY_ENERGY
**Frequency:** 46 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PAY_ENERGY",
  "value": 2,
  "attr": {
    "is_optional": 1
  },
  "frame_index": 0
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...`
**Card examples:** PL!N-bp5-014-N | 中須かすみ (ab#0), PL!N-sd1-009-SD | 天王寺璃奈 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "PAY_ENERGY",
  "frame_index": 3,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払わないかぎり、自分の手札を2枚控え室に置く。...`
**Card examples:** PL!SP-pb1-001-P+ | 澁谷かのん (ab#0), PL!SP-pb1-001-R | 澁谷かのん (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "PAY_ENERGY",
  "frame_index": 0,
  "attr": {
    "is_optional": 1
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を2つまで支払ってもよい：ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!SP-bp4-022-N | 鬼塚冬毬 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "PAY_ENERGY",
  "frame_index": 0,
  "value": 2
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：これにより控え室に置いたカードが『μ's』のカードの場合、自分のデッキの上からカードを4枚見る。その中からカードを2枚手札...`
**Card examples:** PL!-bp5-003-AR | 南 ことり (ab#1), PL!-bp5-003-R+ | 南 ことり (ab#1), PL!-bp5-003-P | 南 ことり (ab#1)

---

## COUNT_STAGE
**Frequency:** 45 occurrences

### Parameter Variations
22 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 3,
  "attr": {
    "special_id": "Not Self"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。...`
**Card examples:** PL!HS-bp2-005-P | 大沢瑠璃乃 (ab#0), PL!HS-bp2-005-R+ | 大沢瑠璃乃 (ab#0), PL!HS-bp2-005-P+ | 大沢瑠璃乃 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。...`
**Card examples:** PL!-bp3-004-P | 園田海未 (ab#0), PL!-bp3-004-R+ | 園田海未 (ab#0), PL!-bp3-004-P+ | 園田海未 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "value_enabled": 1,
    "value_threshold": 13,
    "is_cost_type": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。...`
**Card examples:** PL!-bp3-009-P | 矢澤にこ (ab#0), PL!-bp3-009-R+ | 矢澤にこ (ab#0), PL!-bp3-009-P+ | 矢澤にこ (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにこのメンバー以外のコスト11のメンバーが登場したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**Card examples:** PL!N-pb1-012-P+ | 鐘 嵐珠 (ab#0), PL!N-pb1-012-R | 鐘 嵐珠 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 2,
  "attr": {
    "unit_enabled": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『Printemps』のメンバー1人につき、エネルギーを1枚アクティブにする。...`
**Card examples:** PL!-pb1-003-P+ | 南ことり (ab#0), PL!-pb1-003-R | 南ことり (ab#0)

... and 17 more variations

---

## LOOK_AND_CHOOSE
**Frequency:** 44 occurrences

### Parameter Variations
21 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "LOOK_AND_CHOOSE",
  "frame_index": 2,
  "value": {
    "count": 3,
    "reveal": 1
  },
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND",
    "remainder_zone": "DISCARD",
    "source_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。...`
**Card examples:** PL!-sd1-011-SD | 絢瀬 絵里 (ab#0), PL!-sd1-012-SD | 南 ことり (ab#0), PL!-sd1-016-SD | 東條 希 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "LOOK_AND_CHOOSE",
  "frame_index": 2,
  "value": {
    "count": 3,
    "reveal": 1
  },
  "slot": {
    "target_slot": "HAND",
    "remainder_zone": "DISCARD",
    "source_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。...`
**Card examples:** PL!SP-bp1-012-N | 澁谷かのん (ab#0), PL!SP-sd1-008-SD | 若菜四季 (ab#0), PL!SP-sd1-017-SD | 桜小路きな子 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "LOOK_AND_CHOOSE",
  "frame_index": 3,
  "value": {
    "count": 5
  },
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER",
    "group_enabled": 1,
    "group_id": "AQOURS",
    "value_enabled": 1,
    "value_threshold": 9,
    "is_cost_type": 1,
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『Aqours』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!S-bp5-006-AR | 津島善子 (ab#0), PL!S-bp5-006-R | 津島善子 (ab#0), PL!S-bp5-006-P | 津島善子 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "LOOK_AND_CHOOSE",
  "frame_index": 3,
  "value": {
    "count": 5
  },
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER",
    "group_enabled": 1,
    "value_enabled": 1,
    "value_threshold": 9,
    "is_cost_type": 1,
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『μ's』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!-bp5-002-AR | 絢瀬絵里 (ab#0), PL!-bp5-002-R | 絢瀬絵里 (ab#0), PL!-bp5-002-P | 絢瀬絵里 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "LOOK_AND_CHOOSE",
  "frame_index": 2,
  "value": {
    "count": 4
  },
  "attr": {
    "target_player": "SELF",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "remainder_zone": "DISCARD",
    "source_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_04.png|heart04}}を2個以上持つメンバーカードか、必要ハートに{{heart_04.png|heart04}}を2以上含むライブカードを1枚公開し...`
**Card examples:** PL!S-pb1-013-N | 黒澤ダイヤ (ab#0)

... and 16 more variations

---

## RECOVER_LIVE
**Frequency:** 43 occurrences

### Parameter Variations
13 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "RECOVER_LIVE",
  "value": 1,
  "attr": {
    "group_enabled": 1,
    "group_id": "NIJIGASAKI"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  },
  "frame_index": 3
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...`
**Card examples:** PL!N-bp5-014-N | 中須かすみ (ab#0), PL!N-sd1-009-SD | 天王寺璃奈 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "RECOVER_LIVE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "group_enabled": 1,
    "group_id": "HASUNOSORA",
    "zone_mask": "ALL",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。...`
**Card examples:** PL!HS-bp2-007-P | 百生 吟子 (ab#0), PL!HS-bp2-007-R+ | 百生 吟子 (ab#0), PL!HS-bp2-007-P+ | 百生 吟子 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "RECOVER_LIVE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "zone_mask": "ALL",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...`
**Card examples:** PL!N-bp1-003-P | 桜坂しずく (ab#0), PL!N-bp1-003-R+ | 桜坂しずく (ab#0), PL!N-bp1-003-P+ | 桜坂しずく (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "RECOVER_LIVE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。...`
**Card examples:** PL!N-bp4-007-P | 優木せつ菜 (ab#0), PL!N-bp4-007-R+ | 優木せつ菜 (ab#0), PL!N-bp4-007-P+ | 優木せつ菜 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "RECOVER_LIVE",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "OPPONENT",
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "STAGE_2",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。...`
**Card examples:** PL!N-bp4-007-P | 優木せつ菜 (ab#0), PL!N-bp4-007-R+ | 優木せつ菜 (ab#0), PL!N-bp4-007-P+ | 優木せつ菜 (ab#0)

... and 8 more variations

---

## MOVE_MEMBER
**Frequency:** 29 occurrences

### Parameter Variations
13 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "MOVE_MEMBER",
  "frame_index": 3,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT",
    "is_wait": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない...`
**Card examples:** PL!-PR-007-PR | 東條 希 (ab#0), PL!-PR-009-PR | 矢澤にこ (ab#0), PL!N-bp3-017-N | 宮下 愛 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "MOVE_MEMBER",
  "frame_index": 5,
  "value": 99,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  },
  "params": {
    "destination": "POSITION_CHANGE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
・自分のステージにいる『SaintSnow』のメンバー1人をポジションチェンジさせる。(このメ...`
**Card examples:** PL!S-bp5-004-AR | 黒澤ダイヤ (ab#0), PL!S-bp5-004-R | 黒澤ダイヤ (ab#0), PL!S-bp5-004-P | 黒澤ダイヤ (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "MOVE_MEMBER",
  "frame_index": 1,
  "value": 99,
  "attr": {
    "target_player": "BOTH",
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_1"
  },
  "params": {
    "destination": "POSITION_CHANGE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分と相手は、自身のステージのセンターにいるメンバーをポジションチェンジする。(センターにいるメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはセンターエリアに移動させる。)...`
**Card examples:** PL!SP-bp5-010-AR | ウィーン・マルガレーテ (ab#0), PL!SP-bp5-010-R | ウィーン・マルガレーテ (ab#0), PL!SP-bp5-010-P | ウィーン・マルガレーテ (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "MOVE_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "unit_enabled": 1,
    "unit_id": "BIBI",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "is_wait": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。...`
**Card examples:** PL!-pb1-015-P+ | 西木野真姫 (ab#0), PL!-pb1-015-R | 西木野真姫 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "MOVE_MEMBER",
  "frame_index": 5,
  "value": 1,
  "attr": {
    "target_player": "BOTH"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "is_wait": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の手札からコスト4以下の『虹ヶ咲』のメンバーカードを1枚ステージに登場させる。これにより登場したメンバーがブレードハートを持つ場合、このメンバーをウェイトにする...`
**Card examples:** PL!N-bp4-006-P | 近江彼方 (ab#0), PL!N-bp4-006-R | 近江彼方 (ab#0)

... and 8 more variations

---

## ENERGY_CHARGE
**Frequency:** 28 occurrences

### Parameter Variations
5 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ENERGY_CHARGE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_state": "WAIT"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "ENERGY_DECK"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**Card examples:** PL!SP-PR-004-PR | 唐 可可 (ab#0), PL!SP-PR-006-PR | 平安名すみれ (ab#0), PL!SP-PR-013-PR | 鬼塚冬毬 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "ENERGY_CHARGE",
  "frame_index": 4,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT",
    "is_wait": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。...`
**Card examples:** PL!SP-bp4-005-P | 葉月 恋 (ab#0), PL!SP-bp4-005-R+ | 葉月 恋 (ab#0), PL!SP-bp4-005-P+ | 葉月 恋 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "ENERGY_CHARGE",
  "frame_index": 4,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**Card examples:** PL!SP-pb1-004-P+ | 平安名すみれ (ab#0), PL!SP-pb1-004-R | 平安名すみれ (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "ENERGY_CHARGE",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "is_wait": 1
  },
  "slot": {
    "target_slot": "ENERGY",
    "source_zone": "ENERGY_DECK"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**Card examples:** PL!N-bp3-027-L | La Bella Patria (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "ENERGY_CHARGE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "is_wait": 1
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。
・自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
・自分の控え室からメンバーカードを1枚手札に加える。...`
**Card examples:** PL!N-bp4-030-L | Daydream Mermaid (ab#0)

---

## RECOVER_MEMBER
**Frequency:** 28 occurrences

### Parameter Variations
14 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "RECOVER_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "group_enabled": 1,
    "group_id": "LIELLA",
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。...`
**Card examples:** PL!SP-bp2-006-P | 桜小路きな子 (ab#0), PL!SP-bp2-006-R+ | 桜小路きな子 (ab#0), PL!SP-bp2-006-P+ | 桜小路きな子 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "RECOVER_MEMBER",
  "frame_index": 6,
  "value": 1,
  "attr": {
    "unit_enabled": 1,
    "unit_id": "MIRA_CRA_PARK",
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。...`
**Card examples:** PL!HS-bp2-005-P | 大沢瑠璃乃 (ab#0), PL!HS-bp2-005-R+ | 大沢瑠璃乃 (ab#0), PL!HS-bp2-005-P+ | 大沢瑠璃乃 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "RECOVER_MEMBER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "value_enabled": 1,
    "value_threshold": 2,
    "is_le": 1,
    "is_cost_type": 1,
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。...`
**Card examples:** PL!-bp4-005-P | 星空 凛 (ab#0), PL!-bp4-005-R+ | 星空 凛 (ab#0), PL!-bp4-005-P+ | 星空凛 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "RECOVER_MEMBER",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "value_enabled": 1,
    "value_threshold": 2,
    "is_le": 1,
    "is_cost_type": 1,
    "zone_mask": "ALL",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを2枚まで手札に加える。...`
**Card examples:** PL!HS-bp2-002-P | 村野さやか (ab#0), PL!HS-bp2-002-R+ | 村野さやか (ab#0), PL!HS-bp2-002-P+ | 村野さやか (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "RECOVER_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "zone_mask": "ALL",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『SaintSnow』のカードを1枚手札に加える。そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!S-bp5-009-AR | 黒澤ルビィ (ab#0), PL!S-bp5-009-R | 黒澤ルビィ (ab#0), PL!S-bp5-009-P | 黒澤ルビィ (ab#0)

... and 9 more variations

---

## COUNT_ENERGY
**Frequency:** 27 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_ENERGY",
  "frame_index": 2,
  "value": 7,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。...`
**Card examples:** PL!SP-bp4-005-P | 葉月 恋 (ab#0), PL!SP-bp4-005-R+ | 葉月 恋 (ab#0), PL!SP-bp4-005-P+ | 葉月 恋 (ab#0)

---

## SELECT_MODE
**Frequency:** 25 occurrences

### Parameter Variations
3 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SELECT_MODE",
  "frame_index": 2,
  "value": 2
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
・カードを1枚引く。...`
**Card examples:** PL!SP-bp5-001-AR | 澁谷かのん (ab#0), PL!SP-bp5-001-R+ | 澁谷かのん (ab#0), PL!SP-bp5-001-P | 澁谷かのん (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SELECT_MODE",
  "frame_index": 0,
  "value": 2,
  "slot": {
    "is_opponent": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。...`
**Card examples:** PL!S-pb1-002-P+ | 桜内梨子 (ab#0), PL!S-pb1-002-R | 桜内梨子 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "SELECT_MODE",
  "frame_index": 4,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージにコスト9以上の『EdelNote』のメンバーがいる場合、以下から1つを選ぶ。
・自分の控え室からコスト4以下の『EdelNote』のメ...`
**Card examples:** PL!HS-bp5-022-L | Retrofuture (ab#0)

---

## SELECT_CARDS
**Frequency:** 24 occurrences

### Parameter Variations
19 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SELECT_CARDS",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "card_type": "LIVE",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。...`
**Card examples:** PL!S-bp2-008-P | 小原鞠莉 (ab#0), PL!S-bp2-008-R+ | 小原鞠莉 (ab#0), PL!S-bp2-008-P+ | 小原鞠莉 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SELECT_CARDS",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室からカードを1枚までデッキの一番上に置く。...`
**Card examples:** PL!SP-bp2-013-N | 唐 可可 (ab#0), PL!SP-bp2-014-N | 嵐 千砂都 (ab#0), PL!SP-bp2-018-N | 米女メイ (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "SELECT_CARDS",
  "frame_index": 5,
  "value": 2,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "card_type": "LIVE",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。...`
**Card examples:** PL!N-pb1-010-P+ | 三船栞子 (ab#0), PL!N-pb1-010-R | 三船栞子 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "SELECT_CARDS",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "target_player": "SELF",
    "card_type": "LIVE",
    "unique_names": 1,
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。...`
**Card examples:** PL!SP-bp2-011-P | 鬼塚冬毬 (ab#0), PL!SP-bp2-011-R | 鬼塚冬毬 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "SELECT_CARDS",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1,
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "HAND"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札からコスト4以下の『Liella!』のメンバーカードを1枚ステージに登場させてもよい。
（この効果で既にメンバーがいるエリアにも登場できる。ただし、このターンにステージに登場したメンバーがいるエリアには登場できない。）...`
**Card examples:** PL!SP-sd1-002-SD | 唐 可可 (ab#0)

... and 14 more variations

---

## ACTIVATE_ENERGY
**Frequency:** 23 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ACTIVATE_ENERGY",
  "frame_index": 2,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。...`
**Card examples:** PL!SP-bp4-008-P | 若菜四季 (ab#1), PL!SP-bp4-008-R+ | 若菜四季 (ab#1), PL!SP-bp4-008-P+ | 若菜四季 (ab#1)

---

## GROUP_FILTER
**Frequency:** 23 occurrences

### Parameter Variations
13 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 0
}
```
**Matching text:** `{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。...`
**Card examples:** PL!N-pb1-005-P+ | 宮下 愛 (ab#0), PL!N-pb1-005-R | 宮下 愛 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 0,
  "value": 4,
  "attr": {
    "unit_enabled": 1,
    "unit_id": "BIBI"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。...`
**Card examples:** PL!-pb1-002-P+ | 絢瀬絵里 (ab#0), PL!-pb1-002-R | 絢瀬絵里 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 0,
  "value": 3,
  "attr": {
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいるメンバーが『Liella!』のみで、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**Card examples:** PL!SP-bp4-001-P | 澁谷かのん (ab#0), PL!SP-bp4-001-R | 澁谷かのん (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 1,
  "value": 4,
  "attr": {
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。...`
**Card examples:** PL!HS-PR-019-PR | 百生 吟子 (ab#0), PL!HS-PR-019-RM | 百生 吟子 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 1,
  "value": 3,
  "attr": {
    "card_type": "MEMBER"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。...`
**Card examples:** PL!HS-bp1-008-P | 徒町 小鈴 (ab#0), PL!HS-bp1-008-R | 徒町 小鈴 (ab#0)

... and 8 more variations

---

## HAS_KEYWORD
**Frequency:** 21 occurrences

### Parameter Variations
5 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "HAS_KEYWORD",
  "frame_index": 0,
  "value": 3,
  "attr": {
    "char_id_1": "LANZHU"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。...`
**Card examples:** PL!N-bp3-005-P | 宮下 愛 (ab#0), PL!N-bp3-005-R+ | 宮下 愛 (ab#0), PL!N-bp3-005-P+ | 宮下 愛 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "HAS_KEYWORD",
  "frame_index": 0,
  "attr": {
    "char_id_1": "LANZHU"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。...`
**Card examples:** PL!SP-bp4-004-P | 平安名すみれ (ab#1), PL!SP-bp4-004-R+ | 平安名すみれ (ab#1), PL!SP-bp4-004-P+ | 平安名すみれ (ab#1)

#### Variation 3
**Frame structure:**
```json
{
  "op": "HAS_KEYWORD",
  "frame_index": 5,
  "attr": {
    "char_id_1": "LANZHU"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。公開したカードがコスト9以下のメンバーカードの場合、公開したカードを手札に加え、このメンバーはポジションチェンジする。それ以外の場合、公開したカードを控え室に置く。...`
**Card examples:** PL!N-pb1-004-P+ | 朝香果林 (ab#1), PL!N-pb1-004-R | 朝香果林 (ab#1)

#### Variation 4
**Frame structure:**
```json
{
  "op": "HAS_KEYWORD",
  "frame_index": 0,
  "attr": {
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "keyword_energy": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを+１する。さらに、自分の『虹ヶ咲』のカードの効果によって自分のステージにいるウェイト状態のメンバーもアクティブにしていた場...`
**Card examples:** PL!N-pb1-037-L | Cara Tesoro (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "HAS_KEYWORD",
  "frame_index": 3,
  "attr": {
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "keyword_member": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを+１する。さらに、自分の『虹ヶ咲』のカードの効果によって自分のステージにいるウェイト状態のメンバーもアクティブにしていた場...`
**Card examples:** PL!N-pb1-037-L | Cara Tesoro (ab#0)

---

## BATON
**Frequency:** 21 occurrences

### Parameter Variations
7 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "BATON",
  "frame_index": 1,
  "value": 2,
  "attr": {
    "group_enabled": 1,
    "group_id": "LIELLA"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。...`
**Card examples:** PL!SP-bp4-004-P | 平安名すみれ (ab#1), PL!SP-bp4-004-R+ | 平安名すみれ (ab#1), PL!SP-bp4-004-P+ | 平安名すみれ (ab#1)

#### Variation 2
**Frame structure:**
```json
{
  "op": "BATON",
  "frame_index": 0
}
```
**Matching text:** `{{toujyou.png|登場}}「優木せつ菜」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。...`
**Card examples:** PL!N-pb1-019-P+ | 優木せつ菜 (ab#0), PL!N-pb1-019-R | 優木せつ菜 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "BATON",
  "frame_index": 2,
  "attr": {
    "unit_enabled": 1,
    "unit_id": "MIRA_CRA_PARK"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.png|heart01}}...`
**Card examples:** PL!HS-bp2-009-P | 安養寺 姫芽 (ab#0), PL!HS-bp2-009-R | 安養寺 姫芽 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "BATON",
  "frame_index": 0,
  "attr": {
    "char_id_1": "SHIORIKO"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}「三船栞子」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。...`
**Card examples:** PL!N-pb1-022-P+ | 三船栞子 (ab#0), PL!N-pb1-022-R | 三船栞子 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "BATON",
  "frame_index": 0,
  "attr": {
    "group_enabled": 1,
    "group_id": "HASUNOSORA"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}「徒町小鈴」以外の『蓮ノ空』のメンバーからバトンタッチして登場した場合、自分の控え室からライブカードを1枚手札に加える。...`
**Card examples:** PL!HS-sd1-005-SD | 徒町小鈴 (ab#0)

... and 2 more variations

---

## SET_TAPPED
**Frequency:** 20 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SET_TAPPED",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない...`
**Card examples:** PL!-PR-007-PR | 東條 希 (ab#0), PL!-PR-009-PR | 矢澤にこ (ab#0), PL!N-bp3-017-N | 宮下 愛 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SET_TAPPED",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『Aqours』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!S-bp5-006-AR | 津島善子 (ab#0), PL!S-bp5-006-R | 津島善子 (ab#0), PL!S-bp5-006-P | 津島善子 (ab#0)

---

## TAP_OPPONENT
**Frequency:** 20 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TAP_OPPONENT",
  "value": 1,
  "attr": {
    "target_player": "OPPONENT"
  },
  "params": {
    "filter": "BLADE_LE3"
  },
  "slot": {
    "target_slot": "STAGE_2"
  },
  "frame_index": 2
}
```
**Matching text:** `{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。...`
**Card examples:** PL!SP-bp4-011-P | 鬼塚冬毬 (ab#0), PL!SP-bp4-011-R+ | 鬼塚冬毬 (ab#0), PL!SP-bp4-011-P+ | 鬼塚冬毬 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "TAP_OPPONENT",
  "frame_index": 5,
  "value": 1,
  "attr": {
    "target_player": "OPPONENT",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1
  },
  "slot": {
    "target_slot": "STAGE_2"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
・カードを1枚引く。...`
**Card examples:** PL!SP-bp5-001-AR | 澁谷かのん (ab#0), PL!SP-bp5-001-R+ | 澁谷かのん (ab#0), PL!SP-bp5-001-P | 澁谷かのん (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "TAP_OPPONENT",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "target_player": "OPPONENT"
  },
  "slot": {
    "target_slot": "STAGE_2"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。...`
**Card examples:** PL!-pb1-015-P+ | 西木野真姫 (ab#0), PL!-pb1-015-R | 西木野真姫 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "TAP_OPPONENT",
  "frame_index": 9,
  "value": 1,
  "params": {
    "filter": "BLADE_LE3"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージに『A-RISE』のメンバーがいる場合、以下から1つを選ぶ。
・ウェイト状態のメンバー1人をアクティブにし、ライブ終了時まで、そのメンバーは{{icon_blade.png|ブレード}}を得る。
・相手のステージにいる元々持つ{{ico...`
**Card examples:** PL!-bp5-024-L | Private Wars (ab#0)

---

## COUNT_SUCCESS_LIVE
**Frequency:** 19 occurrences

### Parameter Variations
5 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_SUCCESS_LIVE",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の成功ライブカード置き場にカードがある場合、カードを1枚引く。...`
**Card examples:** PL!-pb1-005-P+ | 星空 凛 (ab#0), PL!-pb1-005-R | 星空 凛 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "COUNT_SUCCESS_LIVE",
  "frame_index": 3,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!-bp3-006-P | 西木野真姫 (ab#0), PL!-bp3-006-R | 西木野真姫 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "COUNT_SUCCESS_LIVE",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "group_enabled": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを+１する。...`
**Card examples:** PL!-bp3-019-L | 僕らのLIVE 君とのLIFE (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "COUNT_SUCCESS_LIVE",
  "frame_index": 0,
  "attr": {
    "group_enabled": 1,
    "group_id": "NIJIGASAKI"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。
・自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
・自分の控え室からメンバーカードを1枚手札に加える。...`
**Card examples:** PL!N-bp4-030-L | Daydream Mermaid (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "COUNT_SUCCESS_LIVE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "group_enabled": 1,
    "group_id": "MUSE"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを+５する。...`
**Card examples:** PL!-bp4-019-L | Angelic Angel (ab#0)

---

## HAS_MEMBER
**Frequency:** 16 occurrences

### Parameter Variations
8 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "HAS_MEMBER",
  "frame_index": 2,
  "attr": {
    "special_id": "Not Self"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにこのメンバー以外のコスト11のメンバーがいる場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...`
**Card examples:** PL!N-pb1-001-P+ | 上原歩夢 (ab#0), PL!N-pb1-001-R | 上原歩夢 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "HAS_MEMBER",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージに「大沢瑠璃乃」か「百生吟子」か「徒町小鈴」がいる場合、エネルギーを1枚アクティブにし、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。...`
**Card examples:** PL!HS-sd1-006-SD | 安養寺 姫芽 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "HAS_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "unit_enabled": 1,
    "unit_id": "EDEL_NOTE",
    "value_enabled": 1,
    "value_threshold": 9,
    "is_cost_type": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージにコスト9以上の『EdelNote』のメンバーがいる場合、以下から1つを選ぶ。
・自分の控え室からコスト4以下の『EdelNote』のメ...`
**Card examples:** PL!HS-bp5-022-L | Retrofuture (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "HAS_MEMBER",
  "frame_index": 2,
  "attr": {
    "group_enabled": 1,
    "group_id": "HASUNOSORA"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『蓮ノ空』のメンバー1人を含むメンバーが2人以上おり、かつそれらのメンバーのユニット名がそれぞれ異なる場合、このカードのスコアを+１する。...`
**Card examples:** PL!HS-bp5-017-L | Dream Believers（104期Ver.） (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "HAS_MEMBER",
  "frame_index": 0,
  "attr": {
    "target_player": "OPPONENT"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}相手のステージにいるすべてのメンバーのそれぞれのコストよりコストが高いメンバーが自分のステージにいる場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!S-bp5-016-N | 国木田花丸 (ab#0)

... and 3 more variations

---

## MOVE_TO_DECK
**Frequency:** 15 occurrences

### Parameter Variations
6 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "MOVE_TO_DECK",
  "value": 1,
  "slot": {
    "target_slot": "DECK_BOTTOM",
    "source_zone": "HAND"
  },
  "frame_index": 1
}
```
**Matching text:** `{{toujyou.png|登場}}カードを1枚引き、手札を1枚デッキの一番下に置く。...`
**Card examples:** PL!S-bp5-014-N | 渡辺 曜 (ab#0), PL!S-sd1-017-SD | 小原鞠莉 (ab#0), PL!S-sd1-018-SD | 黒澤ルビィ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "MOVE_TO_DECK",
  "frame_index": 1,
  "slot": {
    "dest_zone": "DECK_BOTTOM",
    "remainder_zone": "DECK_BOTTOM"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。...`
**Card examples:** PL!S-bp2-008-P | 小原鞠莉 (ab#0), PL!S-bp2-008-R+ | 小原鞠莉 (ab#0), PL!S-bp2-008-P+ | 小原鞠莉 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "MOVE_TO_DECK",
  "frame_index": 6,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT",
    "dest_zone": "DECK",
    "remainder_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。...`
**Card examples:** PL!N-pb1-010-P+ | 三船栞子 (ab#0), PL!N-pb1-010-R | 三船栞子 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "MOVE_TO_DECK",
  "frame_index": 1,
  "value": 1,
  "slot": {
    "dest_zone": "DECK",
    "remainder_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く。その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く。...`
**Card examples:** PL!-pb1-006-P+ | 西木野真姫 (ab#0), PL!-pb1-006-R | 西木野真姫 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "MOVE_TO_DECK",
  "frame_index": 4,
  "value": 1,
  "slot": {
    "target_slot": "STAGE_1",
    "source_zone": "HAND",
    "dest_zone": "DECK",
    "remainder_zone": "DECK_TOP"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを2枚引き、自分の手札を1枚デッキの一番上に置く。...`
**Card examples:** PL!N-bp4-009-P | 天王寺璃奈 (ab#0), PL!N-bp4-009-R | 天王寺璃奈 (ab#0)

... and 1 more variations

---

## REDUCE_HEART_REQ
**Frequency:** 14 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "REDUCE_HEART_REQ",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_04.png|heart04}}減らす。...`
**Card examples:** PL!HS-bp2-021-L | 眩耀夜行 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "REDUCE_HEART_REQ",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "STAGE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいる{{heart_01.png|heart01}}と{{heart_06.png|heart06}}以外の色のハートを持つメンバー1人につき、このカードの必要ハートを{{heart_00.png|heart0}}減らす。...`
**Card examples:** PL!-bp5-023-L | 乙姫心で恋宮殿 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "REDUCE_HEART_REQ",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。...`
**Card examples:** PL!SP-pb1-025-L | Jellyfish (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "REDUCE_HEART_REQ",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "HASUNOSORA",
    "special_id": "Not Self",
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "SUCCESS_PILE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 2,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブカード置き場にあるこのカード以外の『蓮ノ空』のカード1枚につき、このカードの必要ハートを{{heart_04.png|heart04}}{{heart_04.png|heart04}}減らす。...`
**Card examples:** PL!HS-bp5-019-L | ハナムスビ (ab#0)

---

## ADD_TO_HAND
**Frequency:** 13 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ADD_TO_HAND",
  "frame_index": 5,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。...`
**Card examples:** PL!N-bp1-011-P | ミア・テイラー (ab#0), PL!N-bp1-011-R | ミア・テイラー (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "ADD_TO_HAND",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_05.png|heart05}}か{{heart_06.png|heart06}}を持つメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!-bp5-014-N | 星空凛 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "ADD_TO_HAND",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『Aqours』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!S-sd1-003-SD | 松浦果南 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "ADD_TO_HAND",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分の控え室にある、自分のステージにいるすべてのメンバーと異なるグループ名を持つカード1枚を手札に加える。...`
**Card examples:** LL-bp5-002-L | Bring the LOVE！ (ab#1)

---

## DISCARDED_CARDS
**Frequency:** 12 occurrences

### Parameter Variations
5 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "DISCARDED_CARDS",
  "value": 3,
  "attr": {
    "card_type": "MEMBER"
  },
  "slot": {
    "target_slot": "CONTEXT"
  },
  "frame_index": 1
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!HS-bp5-013-N | 徒町 小鈴 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "DISCARDED_CARDS",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "card_type": "LIVE"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!HS-bp5-001-AR | 日野下花帆 (ab#0), PL!HS-bp5-001-R+ | 日野下花帆 (ab#0), PL!HS-bp5-001-P | 日野下花帆 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "DISCARDED_CARDS",
  "frame_index": 1,
  "value": 4,
  "attr": {
    "card_type": "MEMBER",
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。...`
**Card examples:** PL!HS-PR-021-PR | 安養寺 姫芽 (ab#0), PL!HS-PR-021-RM | 安養寺 姫芽 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "DISCARDED_CARDS",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "group_enabled": 1,
    "group_id": "MUSE"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：これにより控え室に置いたカードが『μ's』のカードの場合、自分のデッキの上からカードを4枚見る。その中からカードを2枚手札...`
**Card examples:** PL!-bp5-003-AR | 南 ことり (ab#1), PL!-bp5-003-R+ | 南 ことり (ab#1), PL!-bp5-003-P | 南 ことり (ab#1)

#### Variation 5
**Frame structure:**
```json
{
  "op": "DISCARDED_CARDS",
  "frame_index": 5,
  "value": 1,
  "attr": {
    "has_blade_heart": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{kidou.png|起動}}【左サイド】{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを3枚引き、手札を2枚控え室に置く。これにより控え室に置いたカードの中にブレードハートを持たないメンバーカードが1枚以上ある場合、このメンバーをアクティブにする。2枚ある場合、さらに...`
**Card examples:** PL!SP-bp5-002-AR | 唐 可可 (ab#0), PL!SP-bp5-002-R+ | 唐 可可 (ab#0), PL!SP-bp5-002-P | 唐 可可 (ab#0)

---

## ACTIVATE_MEMBER
**Frequency:** 12 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ACTIVATE_MEMBER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいる『Printemps』のメンバーを1人までアクティブにする。...`
**Card examples:** PL!-pb1-012-P+ | 南ことり (ab#0), PL!-pb1-012-R | 南ことり (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "ACTIVATE_MEMBER",
  "frame_index": 1,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいるすべてのメンバーをアクティブにする。...`
**Card examples:** PL!-bp3-005-P | 星空 凛 (ab#0), PL!-bp3-005-R | 星空 凛 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "ACTIVATE_MEMBER",
  "frame_index": 0,
  "value": 99,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{center.png|センター}}自分のステージにいるすべての『Liella!』のメンバーと、自分のすべてのエネルギーをアクティブにする。...`
**Card examples:** PL!SP-bp5-003-AR | 嵐 千砂都 (ab#1), PL!SP-bp5-003-R+ | 嵐 千砂都 (ab#1), PL!SP-bp5-003-P | 嵐 千砂都 (ab#1)

#### Variation 4
**Frame structure:**
```json
{
  "op": "ACTIVATE_MEMBER",
  "frame_index": 2,
  "value": 99,
  "attr": {
    "target_player": "SELF",
    "unit_enabled": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいる『Printemps』のメンバーをアクティブにする。これによりウェイト状態のメンバーが3人以上アクティブ状態になったとき、このカードのスコアを+１する。...`
**Card examples:** PL!-pb1-028-L | WAO-WAO Powerful day! (ab#0)

---

## LOOK_DECK
**Frequency:** 11 occurrences

### Parameter Variations
5 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "LOOK_DECK",
  "frame_index": 0,
  "value": 3
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...`
**Card examples:** PL!N-bp1-002-P | 中須かすみ (ab#0), PL!N-bp1-002-R+ | 中須かすみ (ab#0), PL!N-bp1-002-P+ | 中須かすみ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "LOOK_DECK",
  "frame_index": 2,
  "value": 5,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から各グループ名につき1枚ずつ公開し、3枚まで手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!SP-bp5-007-AR | 米女メイ (ab#0), PL!SP-bp5-007-R | 米女メイ (ab#0), PL!SP-bp5-007-P | 米女メイ (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "LOOK_DECK",
  "frame_index": 2,
  "value": 5,
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER",
    "group_enabled": 1,
    "group_id": "LIELLA",
    "has_blade_heart": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『SunnyPassion』のメンバーカードかブレードハートを持つ『Liella!』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!SP-bp5-013-N | 唐 可可 (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "LOOK_DECK",
  "frame_index": 0,
  "value": 5,
  "attr": {
    "target_player": "SELF",
    "card_type": "LIVE",
    "group_enabled": 1,
    "group_id": "AQOURS"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『Aqours』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!S-sd1-003-SD | 松浦果南 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "LOOK_DECK",
  "frame_index": 0,
  "value": 4,
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のデッキの上からカードを4枚見る。その中からハートに{{heart_04.png|heart04}}を2つ以上持つメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。...`
**Card examples:** PL!S-bp5-007-AR | 国木田花丸 (ab#0), PL!S-bp5-007-R | 国木田花丸 (ab#0), PL!S-bp5-007-P | 国木田花丸 (ab#0)

---

## GRANT_ABILITY
**Frequency:** 11 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "GRANT_ABILITY",
  "frame_index": 3,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、...`
**Card examples:** PL!-pb1-004-P+ | 園田海未 (ab#0), PL!-pb1-004-R | 園田海未 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "GRANT_ABILITY",
  "frame_index": 0,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。...`
**Card examples:** PL!SP-sd1-004-SD | 平安名すみれ (ab#0)

---

## COLOR_SELECT
**Frequency:** 11 occurrences

### Parameter Variations
3 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COLOR_SELECT",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "color_mask": "RED|GREEN|ANY"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハート...`
**Card examples:** PL!-bp3-011-N | 絢瀬絵里 (ab#0), PL!-bp3-012-N | 南ことり (ab#0), PL!-bp3-012-PR | 南 ことり (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "COLOR_SELECT",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。...`
**Card examples:** PL!N-bp1-003-P | 桜坂しずく (ab#1), PL!N-bp1-003-R+ | 桜坂しずく (ab#1), PL!N-bp1-003-P+ | 桜坂しずく (ab#1)

#### Variation 3
**Frame structure:**
```json
{
  "op": "COLOR_SELECT",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。...`
**Card examples:** PL!N-bp4-011-P | ミア・テイラー (ab#0), PL!N-bp4-011-R+ | ミア・テイラー (ab#0), PL!N-bp4-011-P+ | ミア・テイラー (ab#0)

---

## SCORE_COMPARE
**Frequency:** 10 occurrences

### Parameter Variations
3 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SCORE_COMPARE",
  "frame_index": 1,
  "value": 1,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。...`
**Card examples:** PL!-bp4-007-P | 東條 希 (ab#0), PL!-bp4-007-R | 東條 希 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SCORE_COMPARE",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを1枚引く。...`
**Card examples:** PL!-bp4-001-P | 高坂穂乃果 (ab#0), PL!-bp4-001-R | 高坂穂乃果 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "SCORE_COMPARE",
  "frame_index": 0
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き場にカードを置くことができない。...`
**Card examples:** PL!S-pb1-022-L | 逃走迷走メビウスループ (ab#0), PL!S-pb1-022-L+ | 逃走迷走メビウスループ (ab#0)

---

## COUNT_HEARTS
**Frequency:** 10 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_HEARTS",
  "frame_index": 0,
  "value": 5,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいるメンバーが持つハートに{{heart_02.png|heart02}}が合計5つ以上ある場合、相手のライブ開始時、相手のライブカード置き場にあるライブカード1枚は、成功させるための必要ハートが{{heart_00.png|heart0}}多くな...`
**Card examples:** PL!S-bp5-010-N | 高海千歌 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "COUNT_HEARTS",
  "frame_index": 0,
  "value": 6,
  "attr": {
    "group_enabled": 1,
    "group_id": "AQOURS"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.p...`
**Card examples:** PL!S-pb1-019-L | 元気全開DAY！DAY！DAY！ (ab#0)

---

## PLAY_MEMBER_FROM_DISCARD
**Frequency:** 9 occurrences

### Parameter Variations
8 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PLAY_MEMBER_FROM_DISCARD",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD",
    "is_reveal_until_live": 1,
    "is_baton_slot": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。...`
**Card examples:** PL!SP-bp4-004-P | 平安名すみれ (ab#1), PL!SP-bp4-004-R+ | 平安名すみれ (ab#1), PL!SP-bp4-004-P+ | 平安名すみれ (ab#1)

#### Variation 2
**Frame structure:**
```json
{
  "op": "PLAY_MEMBER_FROM_DISCARD",
  "frame_index": 2,
  "value": 2,
  "attr": {
    "target_player": "SELF",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1,
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から、コストの合計が4以下になるようにメンバーカードを2枚までステー...`
**Card examples:** PL!S-bp2-006-P | 津島善子 (ab#0), PL!S-bp2-006-R | 津島善子 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "PLAY_MEMBER_FROM_DISCARD",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "value_enabled": 1,
    "value_threshold": 2,
    "is_le": 1,
    "is_cost_type": 1,
    "is_tapped": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD",
    "is_empty_slot": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）...`
**Card examples:** PL!-pb1-018-P+ | 矢澤にこ (ab#0), PL!-pb1-018-R | 矢澤にこ (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "PLAY_MEMBER_FROM_DISCARD",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "OPPONENT",
    "value_enabled": 1,
    "value_threshold": 2,
    "is_le": 1,
    "is_cost_type": 1,
    "is_tapped": 1
  },
  "slot": {
    "target_slot": "STAGE_2",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）...`
**Card examples:** PL!-pb1-018-P+ | 矢澤にこ (ab#0), PL!-pb1-018-R | 矢澤にこ (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "PLAY_MEMBER_FROM_DISCARD",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室からコスト2以下の『Aqours』のメンバーカードを1枚、メンバーのいないエリアに登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）...`
**Card examples:** PL!S-sd1-006-SD | 津島善子 (ab#0)

... and 3 more variations

---

## META_RULE
**Frequency:** 8 occurrences

### Parameter Variations
7 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "META_RULE",
  "frame_index": 0,
  "value": 0,
  "params": {
    "raw_cond": "YELL_PILE_CONTAINS",
    "FILTER": "TYPE=LIVE",
    "EQ": 0
  }
}
```
**Matching text:** `{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。...`
**Card examples:** PL!S-bp2-004-P | 黒澤ダイヤ (ab#0), PL!S-bp2-004-R | 黒澤ダイヤ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "META_RULE",
  "frame_index": 1,
  "value": 0,
  "attr": {
    "is_optional": 1
  },
  "params": {
    "raw_effect": "DISCARD_YELL_PILE"
  }
}
```
**Matching text:** `{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。...`
**Card examples:** PL!S-bp2-004-P | 黒澤ダイヤ (ab#0), PL!S-bp2-004-R | 黒澤ダイヤ (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "META_RULE",
  "frame_index": 2,
  "value": 0,
  "params": {
    "raw_effect": "RE_YELL"
  }
}
```
**Matching text:** `{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。...`
**Card examples:** PL!S-bp2-004-P | 黒澤ダイヤ (ab#0), PL!S-bp2-004-R | 黒澤ダイヤ (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "META_RULE",
  "frame_index": 3,
  "params": {
    "offset": 1,
    "raw_effect": "SET_SOURCE_COST_FROM_SELECTED_MINUS"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}手札の『DOLLCHESTRA』のカードを1枚控え室に置いてもよい：自分のステージにいる『DOLLCHESTRA』のメンバー1人を選ぶ。ライブ終了時まで、このメンバーのコストは、選んだメンバーが元々持つコストより1低い値に等しくなる。これによりこのカ...`
**Card examples:** PL!HS-bp5-005-AR | 徒町 小鈴 (ab#0), PL!HS-bp5-005-R | 徒町 小鈴 (ab#0), PL!HS-bp5-005-P | 徒町 小鈴 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "META_RULE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "card_type": "LIVE"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージに名前の異なる『CatChu!』のメンバーが2人以上いる場合、エネルギーを6枚までアクティブにする。その後、自分のエネルギーがすべてアクティブ状態の場合、このカードのスコアを+１する。...`
**Card examples:** PL!SP-pb1-023-L | ディストーション (ab#1)

... and 2 more variations

---

## REDUCE_COST
**Frequency:** 8 occurrences

### Parameter Variations
6 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "REDUCE_COST",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{jyouji.png|常時}}コスト10の『Liella!』のメンバーカードを自分の手札から登場させるためのコストは2減る。...`
**Card examples:** PL!SP-bp5-003-AR | 嵐 千砂都 (ab#0), PL!SP-bp5-003-R+ | 嵐 千砂都 (ab#0), PL!SP-bp5-003-P | 嵐 千砂都 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "REDUCE_COST",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{jyouji.png|常時}}能力を持たないメンバーカードを自分の手札から登場させるためのコストは1減る。...`
**Card examples:** PL!S-bp5-001-AR | 高海千歌 (ab#1), PL!S-bp5-001-R+ | 高海千歌 (ab#1), PL!S-bp5-001-P | 高海千歌 (ab#1)

#### Variation 3
**Frame structure:**
```json
{
  "op": "REDUCE_COST",
  "frame_index": 1,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "HAND"
  }
}
```
**Matching text:** `{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。...`
**Card examples:** PL!N-pb1-008-P+ | エマ・ヴェルデ (ab#0), PL!N-pb1-008-R | エマ・ヴェルデ (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "REDUCE_COST",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "special_id": "Not Self",
    "compare_accumulated": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "HAND",
    "remainder_zone": "HAND",
    "is_dynamic": 1
  }
}
```
**Matching text:** `{{jyouji.png|常時}}手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。...`
**Card examples:** LL-bp2-001-R+ | 渡辺 曜&鬼塚夏美&大沢瑠璃乃 (ab#0)

#### Variation 5
**Frame structure:**
```json
{
  "op": "REDUCE_COST",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "unique_names": 1
  },
  "slot": {
    "target_slot": "STAGE_0"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：相手のステージにいるコスト10以下のメンバー1人をウェイトにする。この能力を起動するためのコストは...`
**Card examples:** PL!-bp5-004-AR | 園田海未 (ab#0), PL!-bp5-004-R+ | 園田海未 (ab#0), PL!-bp5-004-P | 園田海未 (ab#0)

... and 1 more variations

---

## PLAY_MEMBER_FROM_HAND
**Frequency:** 7 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PLAY_MEMBER_FROM_HAND",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「上原歩夢」のメンバーカードを1枚ステージに登場させる。...`
**Card examples:** PL!N-pb1-013-P+ | 上原歩夢 (ab#0), PL!N-pb1-013-R | 上原歩夢 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "PLAY_MEMBER_FROM_HAND",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1,
    "zone_mask": "Guest+Friend"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "is_empty_slot": 1
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の手札からコスト4以下の『虹ヶ咲』のメンバーカードを1枚ステージに登場させる。これにより登場したメンバーがブレードハートを持つ場合、このメンバーをウェイトにする...`
**Card examples:** PL!N-bp4-006-P | 近江彼方 (ab#0), PL!N-bp4-006-R | 近江彼方 (ab#0)

---

## SCORE_TOTAL_CHECK
**Frequency:** 7 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SCORE_TOTAL_CHECK",
  "frame_index": 0,
  "value": 6,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、自分のエネルギーデッキから、エネルギーカードを1枚アクティブ状態で置く。...`
**Card examples:** PL!-bp5-005-AR | 星空凛 (ab#0), PL!-bp5-005-R | 星空凛 (ab#0), PL!-bp5-005-P | 星空凛 (ab#0)

---

## IS_CENTER
**Frequency:** 7 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "IS_CENTER",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。...`
**Card examples:** PL!-pb1-015-P+ | 西木野真姫 (ab#0), PL!-pb1-015-R | 西木野真姫 (ab#0)

---

## LOOK_REORDER_DISCARD
**Frequency:** 5 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "LOOK_REORDER_DISCARD",
  "frame_index": 2,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）...`
**Card examples:** PL!-bp3-014-N | 星空 凛 (ab#0), PL!-bp3-017-N | 小泉花陽 (ab#0), PL!-bp3-018-N | 矢澤にこ (ab#0)

---

## COUNT_DISCARD
**Frequency:** 5 occurrences

### Parameter Variations
4 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_DISCARD",
  "frame_index": 0,
  "value": 10,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室にカードが10枚以上ある場合、カードを1枚引く。...`
**Card examples:** PL!HS-bp2-017-N | 徒町 小鈴 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "COUNT_DISCARD",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "card_type": "MEMBER",
    "has_blade_heart": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}このターン、ブレードハートを持たないメンバーカードが自分のライブカード置き場から控え室に置かれている場合、カードを1枚引き、ライブ終了時まで、{{heart_03.png|heart03}}{{heart_05.png|heart05}}{{hear...`
**Card examples:** PL!N-pb1-009-P+ | 天王寺璃奈 (ab#0), PL!N-pb1-009-R | 天王寺璃奈 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "COUNT_DISCARD",
  "frame_index": 0,
  "attr": {
    "card_type": "LIVE",
    "unit_enabled": 1,
    "unit_id": "CERISE_BOUQUET"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分の控え室に『スリーズブーケ』のライブカードが3枚以上ある場合、このカードのスコアを+１する。...`
**Card examples:** PL!HS-bp2-022-L | アオクハルカ (ab#0)

#### Variation 4
**Frame structure:**
```json
{
  "op": "COUNT_DISCARD",
  "frame_index": 0,
  "value": 4,
  "attr": {
    "card_type": "LIVE",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "unique_names": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが4枚以上ある場合、このカードのスコアを+１する。6枚以上ある場合、代わりにスコアを+２する。...`
**Card examples:** PL!N-bp4-028-L | stars we chase (ab#0)

---

## PLACE_ENERGY_UNDER_MEMBER
**Frequency:** 4 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PLACE_ENERGY_UNDER_MEMBER",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "source_zone": "ENERGY"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー2枚をこのメンバーの下に置いてもよい。...`
**Card examples:** PL!N-pb1-002-P+ | 中須かすみ (ab#0), PL!N-pb1-002-R | 中須かすみ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "PLACE_ENERGY_UNDER_MEMBER",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "source_zone": "ENERGY"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：エネルギーを2枚アクティブにする。...`
**Card examples:** PL!N-bp5-008-AR | エマ・ヴェルデ (ab#0), PL!N-bp5-008-R | エマ・ヴェルデ (ab#0), PL!N-bp5-008-P | エマ・ヴェルデ (ab#0)

---

## COUNT_GROUP
**Frequency:** 4 occurrences

### Parameter Variations
3 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_GROUP",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "unique_names": 1,
    "unit_enabled": 1,
    "unit_id": "BIBI"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、相手のステージにいるコスト4以下のメンバー1人をウェイトにする。...`
**Card examples:** PL!-pb1-011-P+ | 絢瀬絵里 (ab#0), PL!-pb1-011-R | 絢瀬絵里 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "COUNT_GROUP",
  "frame_index": 0,
  "value": 5,
  "attr": {
    "unique_names": 1,
    "group_enabled": 1,
    "group_id": "LIELLA",
    "zone_mask": "Friend"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_03.png|he...`
**Card examples:** PL!SP-bp1-026-L | 未来予報ハレルヤ！ (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "COUNT_GROUP",
  "frame_index": 0,
  "value": 3,
  "params": {
    "raw_cond": "UNIQUE_GROUPS_COUNT",
    "MIN": 3
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーが3人以上いて、かつ自分の控え室にカード名に「DreamBelievers」を含むライブカードがある場合、このカードのスコアを+１する。...`
**Card examples:** PL!HS-sd1-018-SD | Dream Believers（105期Ver.） (ab#0)

---

## SET_HEART_COST
**Frequency:** 4 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SET_HEART_COST",
  "frame_index": 2,
  "value": {
    "red": 2,
    "yellow": 2,
    "purple": 2
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_03.png|he...`
**Card examples:** PL!SP-bp1-026-L | 未来予報ハレルヤ！ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SET_HEART_COST",
  "frame_index": 7,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart...`
**Card examples:** PL!HS-bp2-019-L | Bloom the smile, Bloom the dream! (ab#0)

---

## INCREASE_COST
**Frequency:** 4 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "INCREASE_COST",
  "frame_index": 2,
  "value": 4,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを+４する。...`
**Card examples:** PL!SP-pb1-010-P+ | ウィーン・マルガレーテ (ab#0), PL!SP-pb1-010-R | ウィーン・マルガレーテ (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "INCREASE_COST",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "SUCCESS_PILE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、ステージにいるこのメンバーのコストを+１する。...`
**Card examples:** PL!S-bp3-016-N | 国木田花丸 (ab#0)

---

## SET_TARGET_SELF
**Frequency:** 3 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SET_TARGET_SELF",
  "frame_index": 2
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーよりコストが低いメンバーからバトンタッチして登場した場合、自分と相手はそれぞれ自身の手札の枚数が3枚になるまで手札を控え室に置き、その後、自分と相手はそれぞれカードを3枚引く。...`
**Card examples:** PL!-bp5-007-AR | 東條 希 (ab#0), PL!-bp5-007-R | 東條 希 (ab#0), PL!-bp5-007-P | 東條 希 (ab#0)

---

## SUCCESS_PILE_COUNT
**Frequency:** 3 occurrences

### Parameter Variations
3 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SUCCESS_PILE_COUNT",
  "frame_index": 1,
  "attr": {
    "group_enabled": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、...`
**Card examples:** PL!-pb1-004-P+ | 園田海未 (ab#0), PL!-pb1-004-R | 園田海未 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SUCCESS_PILE_COUNT",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。...`
**Card examples:** PL!-bp4-007-P | 東條 希 (ab#0), PL!-bp4-007-R | 東條 希 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "SUCCESS_PILE_COUNT",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "card_type": "LIVE",
    "special_id": "Same Name"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。...`
**Card examples:** PL!N-bp4-010-P | 三船栞子 (ab#1), PL!N-bp4-010-R+ | 三船栞子 (ab#1), PL!N-bp4-010-P+ | 三船栞子 (ab#1)

---

## REVEAL_UNTIL
**Frequency:** 3 occurrences

### Parameter Variations
3 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "REVEAL_UNTIL",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。...`
**Card examples:** PL!N-bp1-011-P | ミア・テイラー (ab#0), PL!N-bp1-011-R | ミア・テイラー (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "REVEAL_UNTIL",
  "frame_index": 7,
  "attr": {
    "card_type": "LIVE"
  },
  "slot": {
    "target_slot": "HAND",
    "is_reveal_until_live": 1,
    "is_baton_slot": 1
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開...`
**Card examples:** PL!-pb1-001-P+ | 高坂穂乃果 (ab#0), PL!-pb1-001-R | 高坂穂乃果 (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "REVEAL_UNTIL",
  "frame_index": 9,
  "slot": {
    "target_slot": "HAND"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開...`
**Card examples:** PL!-pb1-001-P+ | 高坂穂乃果 (ab#0), PL!-pb1-001-R | 高坂穂乃果 (ab#0)

---

## REVEAL_CARDS
**Frequency:** 3 occurrences

### Parameter Variations
3 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "REVEAL_CARDS",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "card_type": "LIVE",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く。...`
**Card examples:** PL!-sd1-006-SD | 西木野 真姫 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "REVEAL_CARDS",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "group_enabled": 1,
    "group_id": "AQOURS",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}手札の『Aqours』のカードを1枚公開してもよい：これにより公開したカードをデッキの一番上か一番下に置き、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!S-sd1-009-SD | 黒澤ルビィ (ab#0)

#### Variation 3
**Frame structure:**
```json
{
  "op": "REVEAL_CARDS",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "HAND"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji...`
**Card examples:** PL!-pb1-013-P+ | 園田海未 (ab#0), PL!-pb1-013-R | 園田海未 (ab#0)

---

## TRANSFORM_COLOR
**Frequency:** 3 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TRANSFORM_COLOR",
  "frame_index": 0,
  "value": 4,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[青ブレード]になる。...`
**Card examples:** PL!N-bp4-025-L | VIVID WORLD (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "TRANSFORM_COLOR",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "is_optional": 1
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置いてもよい。そうした場合、相手はカードを1枚引く。...`
**Card examples:** PL!SP-bp5-027-L | HOT PASSION!! (ab#0)

---

## IS_SELF_MOVE
**Frequency:** 3 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "IS_SELF_MOVE",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、エネルギーを2枚アクティブにする。...`
**Card examples:** PL!S-bp5-222-P+ | 鹿角理亞 (ab#1), PL!S-bp5-222-R | 鹿角理亞 (ab#1)

---

## MAIN_PHASE
**Frequency:** 3 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "MAIN_PHASE",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減...`
**Card examples:** PL!N-bp4-026-L | DIVE! (ab#0)

---

## ORDER_DECK
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ORDER_DECK",
  "frame_index": 1,
  "value": 3
}
```
**Matching text:** `{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。...`
**Card examples:** PL!N-bp1-002-P | 中須かすみ (ab#0), PL!N-bp1-002-R+ | 中須かすみ (ab#0), PL!N-bp1-002-P+ | 中須かすみ (ab#0)

---

## SET_TARGET_OPPONENT
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SET_TARGET_OPPONENT",
  "frame_index": 5
}
```
**Matching text:** `{{toujyou.png|登場}}このメンバーよりコストが低いメンバーからバトンタッチして登場した場合、自分と相手はそれぞれ自身の手札の枚数が3枚になるまで手札を控え室に置き、その後、自分と相手はそれぞれカードを3枚引く。...`
**Card examples:** PL!-bp5-007-AR | 東條 希 (ab#0), PL!-bp5-007-R | 東條 希 (ab#0), PL!-bp5-007-P | 東條 希 (ab#0)

---

## SWAP_AREA
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SWAP_AREA",
  "frame_index": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。...`
**Card examples:** PL!SP-pb1-008-P+ | 若菜四季 (ab#0), PL!SP-pb1-008-R | 若菜四季 (ab#0)

---

## PREVENT_PLAY_TO_SLOT
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PREVENT_PLAY_TO_SLOT",
  "frame_index": 1,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）...`
**Card examples:** PL!-pb1-018-P+ | 矢澤にこ (ab#0), PL!-pb1-018-R | 矢澤にこ (ab#0)

---

## TRIGGER_REMOTE
**Frequency:** 2 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TRIGGER_REMOTE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ。そのカードの{{toujyou.png|登場}}能力1つを発動させる。
（{{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。）...`
**Card examples:** PL!N-bp3-003-P | 桜坂しずく (ab#0), PL!N-bp3-003-R | 桜坂しずく (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "TRIGGER_REMOTE",
  "frame_index": 0,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。
({{toujyou.png|登場}}能力がコストを持つ...`
**Card examples:** PL!SP-bp2-006-P | 桜小路きな子 (ab#1), PL!SP-bp2-006-R+ | 桜小路きな子 (ab#1), PL!SP-bp2-006-P+ | 桜小路きな子 (ab#1)

---

## SYNC_COST
**Frequency:** 2 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SYNC_COST",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{center.png|センター}}自分のステージの右サイドエリアと左サイドエリアにいるメンバーのコストが同じ場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のすべてのメンバーをウェイトにする。...`
**Card examples:** PL!S-bp5-002-AR | 桜内梨子 (ab#0), PL!S-bp5-002-R+ | 桜内梨子 (ab#0), PL!S-bp5-002-P | 桜内梨子 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "SYNC_COST",
  "frame_index": 0,
  "attr": {
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "area_idx": 2,
    "comparison": "GT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のセンターエリアにいる『Liella!』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを+１する。...`
**Card examples:** PL!SP-bp4-024-L | ノンフィクション!! (ab#0)

---

## COUNT_HAND
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_HAND",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!SP-bp2-009-P | 鬼塚夏美 (ab#0), PL!SP-bp2-009-R+ | 鬼塚夏美 (ab#0), PL!SP-bp2-009-P+ | 鬼塚夏美 (ab#0)

---

## TRANSFORM_HEART
**Frequency:** 2 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TRANSFORM_HEART",
  "frame_index": 4,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、このメンバーが元々持つハートはすべて{{heart_04.png|heart04}}になる。{{live_success.png|ラ...`
**Card examples:** PL!S-pb1-003-P+ | 松浦果南 (ab#0), PL!S-pb1-003-R | 松浦果南 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "TRANSFORM_HEART",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『蓮ノ空』のメンバー1人が元々持つハートをすべて{{heart_01.png|heart01}}にする。...`
**Card examples:** PL!HS-bp5-021-L | ジョーショーキリュー (ab#0)

---

## TOTAL_BLADES
**Frequency:** 2 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TOTAL_BLADES",
  "frame_index": 0,
  "value": 10,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードのスコアを+１する。
(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)...`
**Card examples:** PL!N-sd1-028-SD | Dream with You (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "TOTAL_BLADES",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{heart_00.png|heart0}}少なくなる。...`
**Card examples:** PL!-bp3-023-L | ミはμ'sicのミ (ab#0)

---

## COUNT_LIVE_ZONE
**Frequency:** 2 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_LIVE_ZONE",
  "frame_index": 0,
  "attr": {
    "group_enabled": 1,
    "group_id": "AQOURS",
    "special_id": "Not Self"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブカード置き場に「MY舞☆TONIGHT」以外の『Aqours』のライブカードがある場合、ライブ終了時まで、自分のステージのメンバーは{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!S-bp2-023-L | MY舞☆TONIGHT (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "COUNT_LIVE_ZONE",
  "frame_index": 1,
  "value": 3,
  "attr": {
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。...`
**Card examples:** PL!N-bp4-011-P | ミア・テイラー (ab#1), PL!N-bp4-011-R+ | ミア・テイラー (ab#1), PL!N-bp4-011-P+ | ミア・テイラー (ab#1)

---

## INCREASE_HEART_COST
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "INCREASE_HEART_COST",
  "frame_index": 1,
  "value": 3,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード名が「EMOTION」のカード1枚につき、このカードのスコアを+２し、成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00...`
**Card examples:** PL!N-bp4-027-L | EMOTION (ab#0)

---

## PREVENT_SET_TO_SUCCESS_PILE
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PREVENT_SET_TO_SUCCESS_PILE",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き場にカードを置くことができない。...`
**Card examples:** PL!S-pb1-022-L | 逃走迷走メビウスループ (ab#0), PL!S-pb1-022-L+ | 逃走迷走メビウスループ (ab#0)

---

## PLAY_LIVE_FROM_DISCARD
**Frequency:** 2 occurrences

### Parameter Variations
2 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PLAY_LIVE_FROM_DISCARD",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカ...`
**Card examples:** PL!HS-bp2-018-N | 安養寺 姫芽 (ab#0)

#### Variation 2
**Frame structure:**
```json
{
  "op": "PLAY_LIVE_FROM_DISCARD",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "zone_mask": "Guest+Friend"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減...`
**Card examples:** PL!N-bp4-026-L | DIVE! (ab#0)

---

## REDUCE_LIVE_SET_LIMIT
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "REDUCE_LIVE_SET_LIMIT",
  "frame_index": 4,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカ...`
**Card examples:** PL!HS-bp2-018-N | 安養寺 姫芽 (ab#0)

---

## COUNT_BLADE_HEART_TYPES
**Frequency:** 2 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_BLADE_HEART_TYPES",
  "frame_index": 0,
  "value": 3,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードが持つブレードハートの中に[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}...`
**Card examples:** PL!N-bp5-001-AR | 上原歩夢 (ab#0), PL!N-bp5-001-R+ | 上原歩夢 (ab#0), PL!N-bp5-001-P | 上原歩夢 (ab#0)

---

## COUNT_HEART
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_HEART",
  "frame_index": 0,
  "value": 4,
  "attr": {
    "heart_type": "heart_04",
    "target_zone": "LIVE_PILE"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブカード置き場にあるカードの必要ハートに含まれる{{heart_04.png|heart04}}の合計が4以上の場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。...`
**Card examples:** PL!S-bp5-013-N | 黒澤ダイヤ (ab#0)

---

## ADD_HEART
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "ADD_HEART",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "heart_type": "heart_04",
    "duration": "LIVE_END"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブカード置き場にあるカードの必要ハートに含まれる{{heart_04.png|heart04}}の合計が4以上の場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。...`
**Card examples:** PL!S-bp5-013-N | 黒澤ダイヤ (ab#0)

---

## DRAW_UNTIL
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "DRAW_UNTIL",
  "frame_index": 2,
  "value": 5,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。...`
**Card examples:** PL!N-bp3-005-P | 宮下 愛 (ab#0), PL!N-bp3-005-R+ | 宮下 愛 (ab#0), PL!N-bp3-005-P+ | 宮下 愛 (ab#0)

---

## NEGATE_EFFECT
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "NEGATE_EFFECT",
  "frame_index": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。...`
**Card examples:** PL!SP-bp2-001-P | 澁谷かのん (ab#0), PL!SP-bp2-001-R+ | 澁谷かのん (ab#0), PL!SP-bp2-001-P+ | 澁谷かのん (ab#0)

---

## SWAP_ZONE
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SWAP_ZONE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "card_type": "LIVE",
    "zone_mask": "ALL",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "SUCCESS_PILE",
    "dest_zone": "DISCARD"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。...`
**Card examples:** PL!N-bp4-010-P | 三船栞子 (ab#0), PL!N-bp4-010-R+ | 三船栞子 (ab#0), PL!N-bp4-010-P+ | 三船栞子 (ab#0)

---

## AREA_CHECK
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "AREA_CHECK",
  "frame_index": 0
}
```
**Matching text:** `{{toujyou.png|登場}}【左サイド】【右サイド】カードを2枚引き、手札を2枚控え室に置く。（この能力は左サイドエリアか右サイドエリアに登場した場合のみ発動する。）...`
**Card examples:** PL!SP-bp4-003-P | 嵐 千砂都 (ab#0), PL!SP-bp4-003-R | 嵐 千砂都 (ab#0)

---

## OPPONENT_CHOOSE
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "OPPONENT_CHOOSE",
  "frame_index": 1,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。...`
**Card examples:** PL!SP-bp2-011-P | 鬼塚冬毬 (ab#0), PL!SP-bp2-011-R | 鬼塚冬毬 (ab#0)

---

## RESTRICTION
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "RESTRICTION",
  "frame_index": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{toujyou.png|登場}}カードを1枚引く。ライブ終了時まで、自分はライブできない。...`
**Card examples:** PL!HS-bp2-014-N | 大沢瑠璃乃 (ab#0)

---

## DIV_VALUE
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "DIV_VALUE",
  "frame_index": 2,
  "value": 2
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。...`
**Card examples:** PL!SP-bp2-009-P | 鬼塚夏美 (ab#0), PL!SP-bp2-009-R+ | 鬼塚夏美 (ab#0), PL!SP-bp2-009-P+ | 鬼塚夏美 (ab#0)

---

## CALC_SUM_COST
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "CALC_SUM_COST",
  "frame_index": 3
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで...`
**Card examples:** PL!N-bp3-009-P | 天王寺璃奈 (ab#0), PL!N-bp3-009-R+ | 天王寺璃奈 (ab#0), PL!N-bp3-009-P+ | 天王寺璃奈 (ab#0)

---

## REDUCE_YELL_COUNT
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "REDUCE_YELL_COUNT",
  "frame_index": 2,
  "value": 8,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。...`
**Card examples:** PL!SP-bp2-010-P | ウィーン・マルガレーテ (ab#1), PL!SP-bp2-010-R+ | ウィーン・マルガレーテ (ab#1), PL!SP-bp2-010-P+ | ウィーン・マルガレーテ (ab#1)

---

## SELECT_LIVE
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SELECT_LIVE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI",
    "card_type": "LIVE"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。...`
**Card examples:** PL!N-bp4-010-P | 三船栞子 (ab#1), PL!N-bp4-010-R+ | 三船栞子 (ab#1), PL!N-bp4-010-P+ | 三船栞子 (ab#1)

---

## COUNT_BLADES
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_BLADES",
  "frame_index": 1,
  "value": 6,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバー1人を選ぶ。そのメンバーが持つ{{icon_blade.png|ブレード}}が6つ以上の場合、このカードのスコアを+１する。...`
**Card examples:** PL!S-bp3-025-L | SUKI for you, DREAM for you! (ab#0)

---

## TRANSFORM_BLADES
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TRANSFORM_BLADES",
  "frame_index": 1,
  "value": 3,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ{{icon_blade.png|ブレード}}の数は3つになる。...`
**Card examples:** PL!SP-bp4-025-L | Special Color (ab#0)

---

## COUNT_ENERGY_EXACT
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "COUNT_ENERGY_EXACT",
  "frame_index": 0,
  "value": 0,
  "slot": {
    "target_slot": "STAGE_0"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のステージに名前の異なる『CatChu!』のメンバーが2人以上いる場合、エネルギーを6枚までアクティブにする。その後、自分のエネルギーがすべてアクティブ状態の場合、このカードのスコアを+１する。...`
**Card examples:** PL!SP-pb1-023-L | ディストーション (ab#1)

---

## HAS_LIVE_CARD
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "HAS_LIVE_CARD",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがある場合、ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{...`
**Card examples:** PL!-bp4-014-N | 星空 凛 (ab#0)

---

## INCREASE_HEART_REQ
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "INCREASE_HEART_REQ",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "compare_accumulated": 1
  },
  "slot": {
    "remainder_zone": "SUCCESS_PILE",
    "is_dynamic": 1
  },
  "params": {
    "scalar_dynamic": {
      "base_value": 1,
      "divisor": 1
    }
  }
}
```
**Matching text:** `{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード1枚につき、このカードのスコアを+２し、必要ハートを{{heart_01.png|heart01}}{{heart_03.png|heart03}}{{heart_06.png|heart06}}{{heart...`
**Card examples:** PL!-bp5-022-L | A song for You! You? You!! (ab#0)

---

## OPPONENT_ENERGY_DIFF
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "OPPONENT_ENERGY_DIFF",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のエネルギーが相手より少ない場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。...`
**Card examples:** PL!N-bp4-001-P | 上原歩夢 (ab#0), PL!N-bp4-001-R | 上原歩夢 (ab#0)

---

## SET_SCORE
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SET_SCORE",
  "frame_index": 2,
  "value": 4,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、このカードのスコアは４になる。...`
**Card examples:** PL!S-bp3-019-L | MIRACLE WAVE (ab#0)

---

## DECK_REFRESHED
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "DECK_REFRESHED",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを+２する。...`
**Card examples:** PL!S-bp2-022-L | 未熟DREAMER (ab#0)

---

## HAS_EXCESS_HEART
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "HAS_EXCESS_HEART",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分が余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合、カードを1枚引く。...`
**Card examples:** PL!-bp4-023-L | もぎゅっと"love"で接近中！ (ab#0)

---

## NOT_HAS_EXCESS_HEART
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "NOT_HAS_EXCESS_HEART",
  "frame_index": 1,
  "attr": {
    "target_player": "OPPONENT"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手が余剰のハートを持たずにライブを成功させていた場合、このカードのスコアを+２する。...`
**Card examples:** PL!S-pb1-021-L | Strawberry Trapper (ab#0)

---

## FORMATION_CHANGE
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "FORMATION_CHANGE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。(メンバーをそれぞれ好きなエリアに移動させる。この効果で1つのエリアに2人以上のメンバーを移動させることはできない。)...`
**Card examples:** PL!SP-bp4-027-L | Chance Day, Chance Way! (ab#0)

---

## HEART_LEAD
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "HEART_LEAD",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GT"
  }
}
```
**Matching text:** `{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを+１する。...`
**Card examples:** PL!-bp3-026-L | Oh,Love&Peace! (ab#1)

---

## BATON_TOUCH_MOD
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "BATON_TOUCH_MOD",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。...`
**Card examples:** PL!SP-bp4-004-P | 平安名すみれ (ab#0), PL!SP-bp4-004-R+ | 平安名すみれ (ab#0), PL!SP-bp4-004-P+ | 平安名すみれ (ab#0)

---

## PREVENT_BATON_TOUCH
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PREVENT_BATON_TOUCH",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置けない。...`
**Card examples:** LL-bp2-001-R+ | 渡辺 曜&鬼塚夏美&大沢瑠璃乃 (ab#1)

---

## PAY_ENERGY_DYNAMIC
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "PAY_ENERGY_DYNAMIC",
  "frame_index": 2,
  "value": 0,
  "attr": {
    "is_optional": 1
  },
  "params": {
    "source": "selected_live_score"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、そのライブカードを手札に加える。...`
**Card examples:** PL!N-bp5-003-AR | 桜坂しずく (ab#0), PL!N-bp5-003-R | 桜坂しずく (ab#0), PL!N-bp5-003-P | 桜坂しずく (ab#0)

---

## TYPE_CHECK
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TYPE_CHECK",
  "frame_index": 1,
  "value": 1
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji...`
**Card examples:** PL!-pb1-013-P+ | 園田海未 (ab#0), PL!-pb1-013-R | 園田海未 (ab#0)

---

## SELECT_PLAYER
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "SELECT_PLAYER",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
**Matching text:** `{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く。そうした場合、自分はカードを1枚引く。...`
**Card examples:** PL!S-bp3-007-P | 国木田花丸 (ab#0), PL!S-bp3-007-R | 国木田花丸 (ab#0)

---

## TARGET_MEMBER_HAS_NO_HEARTS
**Frequency:** 1 occurrences

### Parameter Variations
1 distinct parameter patterns observed.

#### Variation 1
**Frame structure:**
```json
{
  "op": "TARGET_MEMBER_HAS_NO_HEARTS",
  "frame_index": 0,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
**Matching text:** `{{jidou.png|自動}}自分のステージにいるメンバーの{{live_start.png|ライブ開始時}}能力が解決するたび、そのメンバーが{{icon_all.png|ハート}}を持たない場合、ライブ終了時まで、そのメンバーは{{icon_all.png|ハート}}を得る。...`
**Card examples:** PL!N-bp5-030-L | 繚乱！ビクトリーロード (ab#0)

---

