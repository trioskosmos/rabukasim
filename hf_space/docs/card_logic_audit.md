# Card Logic Audit Log

This log documents the mapping between original Japanese card text, regenerated English pseudocode, and the resulting bytecode sequences.

## LL-PR-004-PR - 愛♡スクリ～ム！

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}相手に何が好き？と聞く。
回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。
回答があなたの場合、自分と相手はカードを1枚引く。
回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(1) -> OPPONENT {{"options": ["\u300c\u5927\u597d\u304d\uff01\u300d\u3068\u7b54\u3048\u308b", "\u300c\u307e\u3042\u307e\u3042\u300d\u3068\u7b54\u3048\u308b"]}}
    Options:
      1: MOVE_MEMBER(1)->PLAYER, MOVE_MEMBER(1)->OPPONENT
      2: SWAP_CARDS(1)->PLAYER, SWAP_CARDS(1)->OPPONENT
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 16777216, 2, 1, 0, 0, 0, 2, 3, 0, 0, 0, 10, 1, 0, 0, 4, 10, 1, 0, 0, 2, 2, 4, 0, 0, 0, 11, 1, 0, 0, 4, 11, 1, 0, 0, 2, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## LL-bp1-001-R＋ - 上原歩夢&澁谷かのん&日野下花帆

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からメンバーカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札の「上原歩夢」と「澁谷かのん」と「日野下花帆」を、好きな組み合わせで合計3枚、控え室に置いてもよい：ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋３する。」を得る。
（手札のこのカードもこの効果で控え室に置ける。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: META_RULE(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 3, 7995392, 537545344, 6, 3, 1, 0, 0, 0, 16, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## LL-bp2-001-R＋ - 渡辺 曜&鬼塚夏美&大沢瑠璃乃

### Japanese Ability
```text
{{jyouji.png|常時}}手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。
{{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置けない。
{{live_start.png|ライブ開始時}}手札の「渡辺曜」と「鬼塚夏美」と「大沢瑠璃乃」を、好きな枚数控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いた枚数1枚につき、{{icon_blade.png|ブレード}}を得る。
（手札のこのカードもこの効果で控え室に置ける。）
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ENERGY_CHARGE(1) -> SELF {{"per_card": "HAND", "filter": "NOT_SELF", "value_enabled": true, "value_threshold": 1}}

TRIGGER: CONSTANT
EFFECT: UNKNOWN(90)(1) -> PLAYER {{"raw_val": "SELF"}}

TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "per_card": "DISCARD_COUNT", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[13, 1, 1, 318767104, 268487680, 1, 0, 0, 0, 0]`
- Ability 2: `[90, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[74, 99, 8519680, 537675648, 393222, 3, 2, 0, 0, 0, 0, 0, 0, 0, 48, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## LL-bp3-001-R＋ - 園田海未&津島善子&天王寺璃奈

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚までアクティブにする。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
EFFECT: UNKNOWN(81)(6) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(3) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[74, 6, 3801088, 537133568, 5701639, 3, 1, 0, 0, 0, 81, 6, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 6, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## LL-bp4-001-R＋ - 絢瀬絵里&朝香果林&葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}自分のデッキの上からカードを5枚見る。その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。その後、相手のステージにいる、これにより公開したカードのコスト以下で、かつ元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバーをすべてウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"filter": "Eri/Karin/Ren", "destination": "discard", "choose_count": 1}}; SET_HEARTS(99) -> OPPONENT {{"filter": "COST_LE_REVEALED, BLADE_LE_3"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"filter": "Eri/Karin/Ren", "destination": "discard", "choose_count": 1}}; SET_HEARTS(99) -> OPPONENT {{"filter": "COST_LE_REVEALED, BLADE_LE_3"}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483643, 5898240, 393216, 67334, 32, 99, 2, 0, 2, 1, 0, 0, 0, 0]`
- Ability 2: `[41, -2147483643, 5898240, 393216, 67334, 32, 99, 2, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!-PR-001-PR - 高坂穂乃果

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をアクティブにしてもよい。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: UNKNOWN(43)(1) -> SELF (Optional)
```

### Bytecode Sequences
- Ability 1: `[43, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-PR-002-PR - 絢瀬絵里

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をアクティブにしてもよい。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: UNKNOWN(43)(1) -> SELF (Optional)
```

### Bytecode Sequences
- Ability 1: `[43, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-PR-003-PR - 南ことり

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_03.png|heart03}}を3以上含むライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(2)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "REQS_HAS_RED_GE_3", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-PR-004-PR - 園田海未

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_01.png|heart01}}を3以上含むライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(2)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "REQS_HAS_RED_GE_3", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-PR-005-PR - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}以下から1つを選ぶ。
・カードを1枚引き、手札を1枚控え室に置く。
・相手のステージにいるすべてのコスト2以下のメンバーをウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"OPTIONS": ["DRAW", "TAP_ALL_LE_2"], "raw_val": "PLAYER", "options": ["DRAW", "TAP_ALL_LE_2"]}}
    Options:
      1: MOVE_MEMBER(1)->PLAYER, UNK(1)->PLAYER {{"source": "HAND", "destination": "discard"}}
      2: UNK(99)->PLAYER {{"filter": "OPPONENT, COST_LE_2", "destination": "targets"}}, UNK(1)->PLAYER {{"raw_val": "TARGETS"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 3, 0, 0, 0, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 2, 4, 0, 0, 0, 65, 99, -989855742, 0, 262148, 53, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-PR-006-PR - 西木野真姫

### Japanese Ability
```text
{{toujyou.png|登場}}以下から1つを選ぶ。
・カードを1枚引き、手札を1枚控え室に置く。
・相手のステージにいるすべてのコスト2以下のメンバーをウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"OPTIONS": ["DRAW", "TAP_ALL_LE_2"], "raw_val": "PLAYER", "options": ["DRAW", "TAP_ALL_LE_2"]}}
    Options:
      1: MOVE_MEMBER(1)->PLAYER, UNK(1)->PLAYER {{"source": "HAND", "destination": "discard"}}
      2: UNK(99)->PLAYER {{"filter": "OPPONENT, COST_LE_2", "destination": "targets"}}, UNK(1)->PLAYER {{"raw_val": "TARGETS"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 3, 0, 0, 0, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 2, 4, 0, 0, 0, 65, 99, -989855742, 0, 262148, 53, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-PR-007-PR - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-PR-008-PR - 小泉花陽

### Japanese Ability
```text
{{toujyou.png|登場}}以下から1つを選ぶ。
・カードを1枚引き、手札を1枚控え室に置く。
・相手のステージにいるすべてのコスト2以下のメンバーをウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"OPTIONS": ["DRAW", "TAP_ALL_LE_2"], "raw_val": "PLAYER", "options": ["DRAW", "TAP_ALL_LE_2"]}}
    Options:
      1: MOVE_MEMBER(1)->PLAYER, UNK(1)->PLAYER {{"source": "HAND", "destination": "discard"}}
      2: UNK(99)->PLAYER {{"filter": "OPPONENT, COST_LE_2", "destination": "targets"}}, UNK(1)->PLAYER {{"raw_val": "TARGETS"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 3, 0, 0, 0, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 2, 4, 0, 0, 0, 65, 99, -989855742, 0, 262148, 53, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-PR-009-PR - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-001-P - 高坂穂乃果

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを1枚引き、手札を1枚控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーを1人までアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "STATUS=TAPPED", "destination": "target"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 1, 536870912, 262148, 43, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-001-R - 高坂穂乃果

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：カードを1枚引き、手札を1枚控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーを1人までアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "STATUS=TAPPED", "destination": "target"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 1, 536870912, 262148, 43, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-002-P - 絢瀬絵里

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
{{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(2) -> PLAYER {{"filter": "OPPONENT, COST_LE=4, STATUS=ACTIVE", "destination": "targets"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGETS"}}

TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "OPPONENT, STATUS=TAPPED", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; SWAP_CARDS(1) -> SELF {{"per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 65, 2, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[29, 1, 2, 0, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!-bp3-002-R - 絢瀬絵里

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
{{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(2) -> PLAYER {{"filter": "OPPONENT, COST_LE=4, STATUS=ACTIVE", "destination": "targets"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGETS"}}

TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "OPPONENT, STATUS=TAPPED", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; SWAP_CARDS(1) -> SELF {{"per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 65, 2, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[29, 1, 2, 0, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!-bp3-003-P - 南ことり

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分の控え室から『μ's』のメンバーカードを1枚手札に加える。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[53, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp3-003-R - 南ことり

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分の控え室から『μ's』のメンバーカードを1枚手札に加える。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[53, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp3-004-P - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; MOVE_MEMBER(1) -> PLAYER {{"raw_val": "COUNT_VAL"}}; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[218, 1, 0, 0, 48, 58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp3-004-P＋ - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; MOVE_MEMBER(1) -> PLAYER {{"raw_val": "COUNT_VAL"}}; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[218, 1, 0, 0, 48, 58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp3-004-R＋ - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; MOVE_MEMBER(1) -> PLAYER {{"raw_val": "COUNT_VAL"}}; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[218, 1, 0, 0, 48, 58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp3-004-SEC - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; MOVE_MEMBER(1) -> PLAYER {{"raw_val": "COUNT_VAL"}}; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[218, 1, 0, 0, 48, 58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp3-005-P - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるすべてのメンバーをアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"filter": "STATUS=TAPPED", "destination": "targets", "raw_val": "ALL"}}; UNKNOWN(43)(1) -> PLAYER {{"raw_val": "TARGETS"}}
```

### Bytecode Sequences
- Ability 1: `[65, 99, 1, 0, 262148, 43, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-005-R - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるすべてのメンバーをアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"filter": "STATUS=TAPPED", "destination": "targets", "raw_val": "ALL"}}; UNKNOWN(43)(1) -> PLAYER {{"raw_val": "TARGETS"}}
```

### Bytecode Sequences
- Ability 1: `[65, 99, 1, 0, 262148, 43, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-006-P - 西木野真姫

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_SUCCESS_LIVE", "raw_val": "PLAYER"}}; UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}}; SWAP_CARDS(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target", "per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 0, 4, 65, 1, 1, 0, 262148, 11, 2, 1, 268435456, 268487425, 1, 0, 0, 0, 0]`

---

## PL!-bp3-006-R - 西木野真姫

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_SUCCESS_LIVE", "raw_val": "PLAYER"}}; UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}}; SWAP_CARDS(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target", "per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 0, 4, 65, 1, 1, 0, 262148, 11, 2, 1, 268435456, 268487425, 1, 0, 0, 0, 0]`

---

## PL!-bp3-007-P - 東條 希

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、1枚をデッキの上に置き、1枚を控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(3) -> CARD_HAND {{"raw_effect": "LOOK_AND_CHOOSE_SPLIT"}}
```

### Bytecode Sequences
- Ability 1: `[58, 2, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 29, 3, 0, 0, 6, 1, 0, 0, 0, 0]`

---

## PL!-bp3-007-R - 東條 希

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、1枚をデッキの上に置き、1枚を控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(3) -> CARD_HAND {{"raw_effect": "LOOK_AND_CHOOSE_SPLIT"}}
```

### Bytecode Sequences
- Ability 1: `[58, 2, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 29, 3, 0, 0, 6, 1, 0, 0, 0, 0]`

---

## PL!-bp3-008-P - 小泉花陽

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい：ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=0", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 3, "duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[15, 1, 17, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 16, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 12, 2, 3, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-008-P＋ - 小泉花陽

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい：ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=0", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 3, "duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[15, 1, 17, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 16, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 12, 2, 3, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-008-R＋ - 小泉花陽

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい：ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=0", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 3, "duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[15, 1, 17, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 16, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 12, 2, 3, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-008-SEC - 小泉花陽

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい：ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=0", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 3, "duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[15, 1, 17, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 16, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 12, 2, 3, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-009-P - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "COST_GE=13", "raw_cond": "COUNT_STAGE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_01.png", "{{heart_03.png", "{{heart_06.png"]}}
    Options:
      1: SEARCH_DECK(1)->SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}
      2: SEARCH_DECK(1)->SELF {{"heart_type": 2, "duration": "UNTIL_LIVE_END"}}
      3: SEARCH_DECK(1)->SELF {{"heart_type": 5, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[203, 1, -1694498816, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[30, 3, 0, 0, 0, 2, 2, 0, 0, 0, 2, 3, 0, 0, 0, 2, 4, 0, 0, 0, 12, 1, 0, 0, 4, 2, 5, 0, 0, 0, 12, 1, 2, 0, 4, 2, 3, 0, 0, 0, 12, 1, 5, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-bp3-009-P＋ - 矢澤にこ

### Japanese Ability
```text
"{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "COST_GE=13", "raw_cond": "COUNT_STAGE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_01.png", "{{heart_03.png", "{{heart_06.png"]}}
    Options:
      1: SEARCH_DECK(1)->SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}
      2: SEARCH_DECK(1)->SELF {{"heart_type": 2, "duration": "UNTIL_LIVE_END"}}
      3: SEARCH_DECK(1)->SELF {{"heart_type": 5, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[203, 1, -1694498816, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[30, 3, 0, 0, 0, 2, 2, 0, 0, 0, 2, 3, 0, 0, 0, 2, 4, 0, 0, 0, 12, 1, 0, 0, 4, 2, 5, 0, 0, 0, 12, 1, 2, 0, 4, 2, 3, 0, 0, 0, 12, 1, 5, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-bp3-009-R＋ - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "COST_GE=13", "raw_cond": "COUNT_STAGE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_01.png", "{{heart_03.png", "{{heart_06.png"]}}
    Options:
      1: SEARCH_DECK(1)->SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}
      2: SEARCH_DECK(1)->SELF {{"heart_type": 2, "duration": "UNTIL_LIVE_END"}}
      3: SEARCH_DECK(1)->SELF {{"heart_type": 5, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[203, 1, -1694498816, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[30, 3, 0, 0, 0, 2, 2, 0, 0, 0, 2, 3, 0, 0, 0, 2, 4, 0, 0, 0, 12, 1, 0, 0, 4, 2, 5, 0, 0, 0, 12, 1, 2, 0, 4, 2, 3, 0, 0, 0, 12, 1, 5, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-bp3-009-SEC - 矢澤にこ

### Japanese Ability
```text
"{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "COST_GE=13", "raw_cond": "COUNT_STAGE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0)
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_01.png", "{{heart_03.png", "{{heart_06.png"]}}
    Options:
      1: SEARCH_DECK(1)->SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}
      2: SEARCH_DECK(1)->SELF {{"heart_type": 2, "duration": "UNTIL_LIVE_END"}}
      3: SEARCH_DECK(1)->SELF {{"heart_type": 5, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[203, 1, -1694498816, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[30, 3, 0, 0, 0, 2, 2, 0, 0, 0, 2, 3, 0, 0, 0, 2, 4, 0, 0, 0, 12, 1, 0, 0, 4, 2, 5, 0, 0, 0, 12, 1, 2, 0, 4, 2, 3, 0, 0, 0, 12, 1, 5, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-bp3-010-N - 高坂穂乃果

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "TYPE_LIVE", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 5, 9, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!-bp3-011-N - 絢瀬絵里

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"choices": [1, 3, 6], "destination": "choice"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "CHOICE", "per_card": "SUCCESS_LIVE", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 74, 4, 12, 1, 1, 268435456, 268491264, 1, 0, 0, 0, 0]`

---

## PL!-bp3-012-N - 南ことり

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"choices": [1, 3, 6], "destination": "choice"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "CHOICE", "per_card": "SUCCESS_LIVE", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 74, 4, 12, 1, 1, 268435456, 268491264, 1, 0, 0, 0, 0]`

---

## PL!-bp3-012-PR - 南 ことり

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"choices": [1, 3, 6], "destination": "choice"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "CHOICE", "per_card": "SUCCESS_LIVE", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 74, 4, 12, 1, 1, 268435456, 268491264, 1, 0, 0, 0, 0]`

---

## PL!-bp3-013-N - 園田海未

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"choices": [1, 3, 6], "destination": "choice"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "CHOICE", "per_card": "SUCCESS_LIVE", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 74, 4, 12, 1, 1, 268435456, 268491264, 1, 0, 0, 0, 0]`

---

## PL!-bp3-014-N - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-015-N - 西木野真姫

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp3-016-N - 東條 希

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp3-017-N - 小泉花陽

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-018-N - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-019-L - 僕らのLIVE 君とのLIFE

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"FILTER": "GROUP_ID=0", "MIN": 2, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[218, 2, 16, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-020-L - Snow halation

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp3-020-L＋ - Snow halation

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp3-021-L - 愛してるばんざーい!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp3-022-L - ユメノトビラ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のデッキの上から、自分と相手のステージにいるメンバー1人につき、1枚公開する。それらの中にあるライブカード1枚につき、このカードのスコアを＋１する。その後、これにより公開したカードを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "ANY", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "revealed", "raw_effect": "REVEAL_DECK_TOP", "raw_val": "COUNT_VAL"}}; ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "live_count", "raw_effect": "COUNT_TYPE"}}; UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REVEALED"}}; META_RULE(1) -> SELF {{"per_card": "LIVE_COUNT", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 29, 1, 0, 0, 4, 29, 0, 0, 0, 4, 58, 1, 1, 0, 262148, 16, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!-bp3-023-L - ミはμ'sicのミ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{heart_00.png|heart0}}少なくなる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(240) {{"MIN": 10, "val": "PLAYER", "raw_cond": "TOTAL_BLADES"}}
EFFECT: UNKNOWN(48)(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[240, 0, 0, 0, 48, 48, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-024-L - 夏色えがおで1,2,Jump!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、選んだハートを1つ得る。
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_01.png", "{{heart_03.png", "{{heart_06.png"]}}
    Options:
      1: UNK(1)->PLAYER {{"filter": "GROUP_ID=0", "destination": "target"}}, SEARCH_DECK(1)->PLAYER {{"heart_type": 0, "duration": "UNTIL_LIVE_END", "destination": "target"}}
      2: UNK(1)->PLAYER {{"filter": "GROUP_ID=0", "destination": "target"}}, SEARCH_DECK(1)->PLAYER {{"heart_type": 2, "duration": "UNTIL_LIVE_END", "destination": "target"}}
      3: UNK(1)->PLAYER {{"filter": "GROUP_ID=0", "destination": "target"}}, SEARCH_DECK(1)->PLAYER {{"heart_type": 5, "duration": "UNTIL_LIVE_END", "destination": "target"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 2, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[218, 1, 0, 0, 48, 30, 3, 0, 0, 0, 2, 2, 0, 0, 0, 2, 4, 0, 0, 0, 2, 6, 0, 0, 0, 65, 1, 17, 0, 262148, 12, 1, 0, 0, 4, 2, 7, 0, 0, 0, 65, 1, 17, 0, 262148, 12, 1, 2, 0, 4, 2, 4, 0, 0, 0, 65, 1, 17, 0, 262148, 12, 1, 5, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`
- Ability 2: `[218, 2, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-025-L - タカラモノズ

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートを持たない場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"MAX": 0, "raw_cond": "SURPLUS_HEARTS_COUNT"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp3-026-L - Oh,Love&Peace!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}}; SWAP_CARDS(3) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target"}}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(237) {TARGET=OPPONENT, {"val": "0", "comparison": "GT", "raw_cond": "HEARTS_COUNT"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[58, 2, 0, 536870912, 6, 3, 2, 0, 0, 0, 65, 1, 1, 0, 262148, 11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[237, 0, 0, 0, 16, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-001-P - 高坂穂乃果

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=COST, {"TARGET": "OPPONENT", "MODE": "REVERSED", "raw_cond": "COST_LEAD", "comparison": "GT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 16, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-001-R - 高坂穂乃果

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=COST, {"TARGET": "OPPONENT", "MODE": "REVERSED", "raw_cond": "COST_LEAD", "comparison": "GT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 16, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-002-P - 絢瀬絵里

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(214) {{"HAS_ABILITY": false, "raw_cond": "HAS_LIVE_CARD"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6, "duration": "UNTIL_LIVE_END"}}

TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[220, 6, 0, 0, 48, 58, 2, 0, 0, 6, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp4-002-P＋ - 絢瀬絵里

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(214) {{"HAS_ABILITY": false, "raw_cond": "HAS_LIVE_CARD"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6, "duration": "UNTIL_LIVE_END"}}

TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[220, 6, 0, 0, 48, 58, 2, 0, 0, 6, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp4-002-R＋ - 絢瀬絵里

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(214) {{"HAS_ABILITY": false, "raw_cond": "HAS_LIVE_CARD"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6, "duration": "UNTIL_LIVE_END"}}

TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[220, 6, 0, 0, 48, 58, 2, 0, 0, 6, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp4-002-SEC - 絢瀬絵里

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が７以上の場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(214) {{"HAS_ABILITY": false, "raw_cond": "HAS_LIVE_CARD"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6, "duration": "UNTIL_LIVE_END"}}

TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[220, 6, 0, 0, 48, 58, 2, 0, 0, 6, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp4-003-P - 南 ことり

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp4-003-R - 南 ことり

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-bp4-004-P - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SCORE_TOTAL", "comparison": "GE"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 6, 0, 0, 48, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-004-R - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SCORE_TOTAL", "comparison": "GE"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 6, 0, 0, 48, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-005-P - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。
{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１する。
{{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "COST_LE_2", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: META_RULE(1) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}, NOT UNKNOWN(306) {{"FILTER": "GROUP_ID=0, BLADES_GE_5", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: PLACE_UNDER(1) -> PLAYER {{"mode": "OUT_OF_CENTER", "raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, -989855744, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[206, 0, 0, 0, 48, 1306, 1, 16, 0, 48, 20, 1, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!-bp4-005-P＋ - 星空凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。
{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１する。
{{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "COST_LE_2", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: META_RULE(1) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}, NOT UNKNOWN(306) {{"FILTER": "GROUP_ID=0, BLADES_GE_5", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: PLACE_UNDER(1) -> PLAYER {{"mode": "OUT_OF_CENTER", "raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, -989855744, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[206, 0, 0, 0, 48, 1306, 1, 16, 0, 48, 20, 1, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!-bp4-005-R＋ - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。
{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１する。
{{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "COST_LE_2", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: META_RULE(1) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}, NOT UNKNOWN(306) {{"FILTER": "GROUP_ID=0, BLADES_GE_5", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: PLACE_UNDER(1) -> PLAYER {{"mode": "OUT_OF_CENTER", "raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, -989855744, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[206, 0, 0, 0, 48, 1306, 1, 16, 0, 48, 20, 1, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!-bp4-005-SEC - 星空凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。
{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１する。
{{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "COST_LE_2", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: META_RULE(1) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}, NOT UNKNOWN(306) {{"FILTER": "GROUP_ID=0, BLADES_GE_5", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: PLACE_UNDER(1) -> PLAYER {{"mode": "OUT_OF_CENTER", "raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, -989855744, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[206, 0, 0, 0, 48, 1306, 1, 16, 0, 48, 20, 1, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!-bp4-006-P - 西木野真姫

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合、自分のデッキの上からカードを5枚見る。その中から『μ's』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 3, "raw_cond": "SCORE_TOTAL", "comparison": "GE"}}
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"filter": "GROUP_ID=0", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[220, 3, 0, 0, 48, 41, -2147483643, 16, 0, 67334, 1, 0, 0, 0, 0]`

---

## PL!-bp4-006-R - 西木野真姫

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合、自分のデッキの上からカードを5枚見る。その中から『μ's』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 3, "raw_cond": "SCORE_TOTAL", "comparison": "GE"}}
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"filter": "GROUP_ID=0", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[220, 3, 0, 0, 48, 41, -2147483643, 16, 0, 67334, 1, 0, 0, 0, 0]`

---

## PL!-bp4-007-P - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(307) {{"MIN": 1, "raw_cond": "SUCCESS_PILE_COUNT"}}, UNKNOWN(220) {TYPE=SCORE, {"LE": 1, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[307, 1, 0, 0, 48, 220, 1, 0, 0, 48, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-007-R - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが1枚以上あり、かつスコアの合計が１以下の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(307) {{"MIN": 1, "raw_cond": "SUCCESS_PILE_COUNT"}}, UNKNOWN(220) {TYPE=SCORE, {"LE": 1, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[307, 1, 0, 0, 48, 220, 1, 0, 0, 48, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-008-P - 小泉花陽

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ステージにいるこのメンバーのコストを＋３する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SCORE_TOTAL", "comparison": "GE"}}
EFFECT: UNKNOWN(70)(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[70, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-008-R - 小泉花陽

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ステージにいるこのメンバーのコストを＋３する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SCORE_TOTAL", "comparison": "GE"}}
EFFECT: UNKNOWN(70)(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[70, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-009-P - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_HEARTS(1) -> OPPONENT
```

### Bytecode Sequences
- Ability 1: `[32, 1, 2, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!-bp4-009-R - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_HEARTS(1) -> OPPONENT
```

### Bytecode Sequences
- Ability 1: `[32, 1, 2, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!-bp4-010-N - 高坂穂乃果

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-011-N - 絢瀬絵里

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"filter": "GROUP_ID=0, AREA=CENTER", "destination": "target", "raw_val": "ALL"}}; SWAP_CARDS(2) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 99, 17, 0, 1074003972, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-012-N - 南 ことり

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp4-013-N - 園田海未

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{heart_01.png|heart01}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SEARCH_DECK(1) -> PLAYER {{"destination": "other_member"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-014-N - 星空 凛

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがある場合、ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(214) {{"HAS_ABILITY": false, "raw_cond": "HAS_LIVE_CARD"}}
EFFECT: SWAP_CARDS(2) -> PLAYER {{"destination": "other_member"}}
```

### Bytecode Sequences
- Ability 1: `[214, 0, 0, 0, 48, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-015-N - 西木野真姫

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp4-016-N - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"MIN": 3, "raw_cond": "SUCCESS_LIVE_SCORE_TOTAL"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[0, 3, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-017-N - 小泉花陽

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> PLAYER {TARGET=CENTER, {"filter": "GROUP_ID=0"}}
```

### Bytecode Sequences
- Ability 1: `[53, 1, 0, 536870912, 4, 3, 1, 0, 0, 0, 11, 1, 17, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-018-N - 矢澤にこ

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=SCORE, {"TARGET": "OPPONENT", "raw_cond": "SCORE_LEAD", "comparison": "GT"}}
EFFECT: SWAP_CARDS(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-019-L - Angelic Angel

### Japanese Ability
```text
{{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを＋５する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: NONE {{"comparison": "EQ", "val": "SUCCESS_PILE", "raw_cond": "CARD_ZONE"}}, UNKNOWN(203) {{"FILTER": "GROUP_ID=0", "val": "1", "raw_cond": "COUNT_MEMBER"}}
EFFECT: META_RULE(5) -> SELF
```

### Bytecode Sequences
- Ability 1: `[16, 5, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-020-L - Love wing bell

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが『μ's』のみの場合、自分のステージにいるメンバー1人をポジションチェンジさせてもよい。
{{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(209) {{"FILTER": "GROUP_ID=0", "raw_cond": "ALL_MEMBERS"}, ALL}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}}; PLACE_UNDER(1) -> PLAYER {{"raw_val": "TARGET"}} (Optional)

TRIGGER: CONSTANT
CONDITION: NONE {{"comparison": "EQ", "val": "SUCCESS_PILE", "raw_cond": "CARD_ZONE"}}, UNKNOWN(306) {TARGET=TARGET_CENTER, {"FILTER": "GROUP_ID=0, AREA=CENTER", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: SWAP_CARDS(1) -> PLAYER {{"destination": "target_center"}}
```

### Bytecode Sequences
- Ability 1: `[209, 4, 16, 0, 48, 65, 1, 1, 0, 262148, 20, 99, 99, 536870912, 1, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-021-L - ?←HEARTBEAT

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。スコアの合計が９以上の場合、さらにこのカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"MIN": 6, "raw_cond": "SCORE_TOTAL", "comparison": "GE"}}
EFFECT: UNKNOWN(48)(99) -> SELF {{"raw_val": "ALL"}}; META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[220, 6, 0, 0, 48, 48, 99, 0, 0, 4, 220, 9, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-022-L - No brand girls

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のセンターエリアに{{icon_blade.png|ブレード}}を9つ以上持つ『μ's』のメンバーがいる場合、このカードのスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(306) {{"FILTER": "GROUP_ID=0, AREA=CENTER, BLADES_GE_9", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: META_RULE(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[306, 1, 16, 0, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-023-L - もぎゅっと"love"で接近中！

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分が余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(238) {{"FILTER": "COLOR_PINK", "raw_cond": "HAS_EXCESS_HEART"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[238, 0, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-024-L - 小夜啼鳥恋詩

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> PLAYER {{"filter": "GROUP_ID=0"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 17, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-bp4-025-L - 微熱からMystery

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-bp4-026-L - ダイヤモンドプリンセスの憂鬱

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-pb1-001-P＋ - 高坂穂乃果

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30e9\u30a4\u30d6\u30ab\u30fc\u30c9", "\u30b3\u30b9\u30c810\u4ee5\u4e0a\u306e\u30e1\u30f3\u30d0\u30fc"]}}
    Options:
      1: UNK(0)->CARD_HAND {{"card_type": "live"}}, ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "DISCARD_REMAINDER"}}
      2: UNK(0)->CARD_HAND {{"card_type": "member", "comparison": "GE", "value": 10}}, ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "DISCARD_REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 51, 0, 0, 0, 4, 58, 1, 0, 0, 6, 30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 3, 0, 0, 0, 69, 0, 8, 0, 33554438, 29, 1, 0, 0, 4, 2, 4, 0, 0, 0, 69, 0, 0, 0, 6, 29, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-pb1-001-R - 高坂穂乃果

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30e9\u30a4\u30d6\u30ab\u30fc\u30c9", "\u30b3\u30b9\u30c810\u4ee5\u4e0a\u306e\u30e1\u30f3\u30d0\u30fc"]}}
    Options:
      1: UNK(0)->CARD_HAND {{"card_type": "live"}}, ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "DISCARD_REMAINDER"}}
      2: UNK(0)->CARD_HAND {{"card_type": "member", "comparison": "GE", "value": 10}}, ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "DISCARD_REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 51, 0, 0, 0, 4, 58, 1, 0, 0, 6, 30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 3, 0, 0, 0, 69, 0, 8, 0, 33554438, 29, 1, 0, 0, 4, 2, 4, 0, 0, 0, 69, 0, 0, 0, 6, 29, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!-pb1-002-P＋ - 絢瀬絵里

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。
{{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{heart_06.png|heart06}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(209) {{"FILTER": "UNIT_BIBI", "raw_cond": "ALL_MEMBERS"}, ALL}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(209) {{"FILTER": "UNIT_BIBI", "raw_cond": "ALL_MEMBERS"}, ALL}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(306) {TARGET=TARGET_VAL, {"FILTER": "OPPONENT, STATUS=TAPPED", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 6, "per_card": "TARGET_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[209, 4, 327680, 0, 48, 51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, 2, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[209, 4, 327680, 0, 48, 51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, 2, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[12, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!-pb1-002-R - 絢瀬絵里

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。
{{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{heart_06.png|heart06}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(209) {{"FILTER": "UNIT_BIBI", "raw_cond": "ALL_MEMBERS"}, ALL}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(209) {{"FILTER": "UNIT_BIBI", "raw_cond": "ALL_MEMBERS"}, ALL}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(306) {TARGET=TARGET_VAL, {"FILTER": "OPPONENT, STATUS=TAPPED", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 6, "per_card": "TARGET_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[209, 4, 327680, 0, 48, 51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, 2, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[209, 4, 327680, 0, 48, 51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, 2, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[12, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!-pb1-003-P＋ - 南ことり

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『Printemps』のメンバー1人につき、エネルギーを1枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "UNIT_PRINTEMPS", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; UNKNOWN(81)(1) -> PLAYER {{"raw_val": "COUNT_VAL"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 29, 1, 65537, 0, 4, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-003-R - 南ことり

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『Printemps』のメンバー1人につき、エネルギーを1枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "UNIT_PRINTEMPS", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; UNKNOWN(81)(1) -> PLAYER {{"raw_val": "COUNT_VAL"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 29, 1, 65537, 0, 4, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-004-P＋ - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを＋２する。」を得る。（この能力はセンターエリアに登場した場合のみ発動する。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "GROUP_ID=0, HAS_SCORE=TRUE", "destination": "count_val", "raw_effect": "SUCCESS_PILE_COUNT"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}; UNKNOWN(60)(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER

TRIGGER: CONSTANT
EFFECT: META_RULE(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 29, 1, 17, 0, 4, 60, 1, 0, 0, 4, 60, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-004-R - 園田海未

### Japanese Ability
```text
{{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを＋２する。」を得る。（この能力はセンターエリアに登場した場合のみ発動する。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "GROUP_ID=0, HAS_SCORE=TRUE", "destination": "count_val", "raw_effect": "SUCCESS_PILE_COUNT"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}; UNKNOWN(60)(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER

TRIGGER: CONSTANT
EFFECT: META_RULE(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 29, 1, 17, 0, 4, 60, 1, 0, 0, 4, 60, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-005-P＋ - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にカードがある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[218, 1, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-005-R - 星空 凛

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にカードがある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[218, 1, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-006-P＋ - 西木野真姫

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く。その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=0", "destination": "deck_top", "source": "discard"}} (Optional); MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[15, 1, 17, 551550976, 458756, 306, 1, 2, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-006-R - 西木野真姫

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く。その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=0", "destination": "deck_top", "source": "discard"}} (Optional); MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[15, 1, 17, 551550976, 458756, 306, 1, 2, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-007-P＋ - 東條 希

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力を起動するためのコストは、自分の成功ライブカード置き場にあるカード1枚につき、控え室に置く手札の数が1枚減る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(306) {{"FILTER": "UNIT_LILY_WHITE, NOT_SELF", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[306, 1, 196608, 50331648, 48, 58, 0, 0, 0, 6, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-pb1-007-R - 東條 希

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力を起動するためのコストは、自分の成功ライブカード置き場にあるカード1枚につき、控え室に置く手札の数が1枚減る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(306) {{"FILTER": "UNIT_LILY_WHITE, NOT_SELF", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[306, 1, 196608, 50331648, 48, 58, 0, 0, 0, 6, 15, 1, 16, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-pb1-008-P＋ - 小泉花陽

### Japanese Ability
```text
{{toujyou.png|登場}}メンバーを3人までウェイトにしてもよい：これによりウェイト状態にしたメンバー1人につき、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER {{"raw_val": "TAPPED_COUNT"}}
```

### Bytecode Sequences
- Ability 1: `[65, 3, 0, 0, 0, 53, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-008-R - 小泉花陽

### Japanese Ability
```text
{{toujyou.png|登場}}メンバーを3人までウェイトにしてもよい：これによりウェイト状態にしたメンバー1人につき、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER {{"raw_val": "TAPPED_COUNT"}}
```

### Bytecode Sequences
- Ability 1: `[65, 3, 0, 0, 0, 53, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-009-P＋ - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする。
{{toujyou.png|登場}}このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_1", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"duration": "UNTIL_TURN_END", "raw_effect": "DISABLE_ACTIVATE_BY_EFFECT", "raw_val": "ALL_MEMBERS"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 2, 0, 262148, 53, 1, 0, 0, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-009-R - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする。
{{toujyou.png|登場}}このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_1", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"duration": "UNTIL_TURN_END", "raw_effect": "DISABLE_ACTIVATE_BY_EFFECT", "raw_val": "ALL_MEMBERS"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 2, 0, 262148, 53, 1, 0, 0, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-010-P＋ - 高坂穂乃果

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるほかのメンバーは{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"filter": "OTHER_MEMBERS", "destination": "target", "raw_val": "ALL"}}; SWAP_CARDS(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 65, 99, 1, 0, 262148, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-010-R - 高坂穂乃果

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるほかのメンバーは{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"filter": "OTHER_MEMBERS", "destination": "target", "raw_val": "ALL"}}; SWAP_CARDS(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 65, 99, 1, 0, 262148, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-011-P＋ - 絢瀬絵里

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(208) {{"MIN": 2, "FILTER": "UNIT_BIBI", "UNIQUE_NAMES": true, "raw_cond": "COUNT_GROUP"}}
EFFECT: SET_HEARTS(1) -> OPPONENT {{"filter": "COST_LE_4"}}
```

### Bytecode Sequences
- Ability 1: `[208, 2, 360448, 0, 48, 32, 1, -922746878, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!-pb1-011-R - 絢瀬絵里

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(208) {{"MIN": 2, "FILTER": "UNIT_BIBI", "UNIQUE_NAMES": true, "raw_cond": "COUNT_GROUP"}}
EFFECT: SET_HEARTS(1) -> OPPONENT {{"filter": "COST_LE_4"}}
```

### Bytecode Sequences
- Ability 1: `[208, 2, 360448, 0, 48, 32, 1, -922746878, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!-pb1-012-P＋ - 南ことり

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいる『Printemps』のメンバーを1人までアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(43)(1) -> PLAYER {{"filter": "UNIT_PRINTEMPS"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[43, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-012-R - 南ことり

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいる『Printemps』のメンバーを1人までアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(43)(1) -> PLAYER {{"filter": "UNIT_PRINTEMPS"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[43, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-013-P＋ - 園田海未

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: TAP_MEMBER(1) -> CARD_HAND {TARGET=CARD_HAND, {"destination": "reveal", "reveal_target": "OPPONENT_HIDDEN", "source": "HAND", "selection_mode": "HIDDEN"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[40, 1, 0, 0, 6, 232, 1, 0, 0, 0, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-013-R - 園田海未

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: TAP_MEMBER(1) -> CARD_HAND {TARGET=CARD_HAND, {"destination": "reveal", "reveal_target": "OPPONENT_HIDDEN", "source": "HAND", "selection_mode": "HIDDEN"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[40, 1, 0, 0, 6, 232, 1, 0, 0, 0, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-014-P＋ - 星空 凛

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場に『lilywhite』のカードがある場合、手札にあるこのメンバーカードのコストは2減る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(307) {{"FILTER": "UNIT_LILYWHITE", "MIN": 1, "raw_cond": "SUCCESS_PILE_COUNT"}}
EFFECT: ENERGY_CHARGE(2) -> PLAYER {{"zone": "HAND"}}
```

### Bytecode Sequences
- Ability 1: `[13, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-014-R - 星空 凛

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場に『lilywhite』のカードがある場合、手札にあるこのメンバーカードのコストは2減る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(307) {{"FILTER": "UNIT_LILYWHITE", "MIN": 1, "raw_cond": "SUCCESS_PILE_COUNT"}}
EFFECT: ENERGY_CHARGE(2) -> PLAYER {{"zone": "HAND"}}
```

### Bytecode Sequences
- Ability 1: `[13, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-015-P＋ - 西木野真姫

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: SET_HEARTS(1) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: SET_HEARTS(1) -> PLAYER

TRIGGER: UNKNOWN(14)
(Once per turn)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 53, 1, 327680, 536870912, 4, 3, 1, 0, 0, 0, 32, 1, 1, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[206, 0, 0, 0, 48, 53, 1, 327680, 536870912, 4, 3, 1, 0, 0, 0, 32, 1, 1, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-015-R - 西木野真姫

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: SET_HEARTS(1) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(206) {{"raw_cond": "IS_CENTER"}}
EFFECT: SET_HEARTS(1) -> PLAYER

TRIGGER: UNKNOWN(14)
(Once per turn)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 53, 1, 327680, 536870912, 4, 3, 1, 0, 0, 0, 32, 1, 1, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[206, 0, 0, 0, 48, 53, 1, 327680, 536870912, 4, 3, 1, 0, 0, 0, 32, 1, 1, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-016-P＋ - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中から『lilywhite』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {UNIT="lilywhite", {"choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 4, 196609, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!-pb1-016-R - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中から『lilywhite』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {UNIT="lilywhite", {"choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 4, 196609, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!-pb1-017-P＋ - 小泉花陽

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：カードを1枚引く。その後、このメンバーが『Printemps』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 3, 0, 0, 0, 10, 1, 0, 0, 4, 1000, 0, 0, 0, 48, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!-pb1-017-R - 小泉花陽

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：カードを1枚引く。その後、このメンバーが『Printemps』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 3, 0, 0, 0, 10, 1, 0, 0, 4, 1000, 0, 0, 0, 48, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!-pb1-018-P＋ - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(63)(1) -> PLAYER {{"filter": "COST_LE_2", "destination": "STAGE_EMPTY", "state": "WAIT"}}; UNKNOWN(71)(1) -> PLAYER {{"destination": "slot"}}; UNKNOWN(63)(1) -> OPPONENT {{"filter": "COST_LE_2", "destination": "STAGE_EMPTY", "state": "WAIT"}}; UNKNOWN(71)(1) -> OPPONENT {{"destination": "slot"}}
```

### Bytecode Sequences
- Ability 1: `[63, 1, -989855743, 0, 67567620, 71, 1, 0, 0, 4, 63, 1, -989855742, 0, 67567620, 71, 1, 0, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!-pb1-018-R - 矢澤にこ

### Japanese Ability
```text
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(63)(1) -> PLAYER {{"filter": "COST_LE_2", "destination": "STAGE_EMPTY", "state": "WAIT"}}; UNKNOWN(71)(1) -> PLAYER {{"destination": "slot"}}; UNKNOWN(63)(1) -> OPPONENT {{"filter": "COST_LE_2", "destination": "STAGE_EMPTY", "state": "WAIT"}}; UNKNOWN(71)(1) -> OPPONENT {{"destination": "slot"}}
```

### Bytecode Sequences
- Ability 1: `[63, 1, -989855743, 0, 67567620, 71, 1, 0, 0, 4, 63, 1, -989855742, 0, 67567620, 71, 1, 0, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!-pb1-019-N - 高坂穂乃果

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-pb1-020-N - 絢瀬絵里

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-pb1-021-N - 南ことり

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-pb1-022-N - 園田海未

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-pb1-023-N - 星空 凛

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-pb1-024-N - 西木野真姫

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-pb1-025-N - 東條 希

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-pb1-026-N - 小泉花陽

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-pb1-027-N - 矢澤にこ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-pb1-028-L - WAO-WAO Powerful day!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいる『Printemps』のメンバーをアクティブにする。これによりウェイト状態のメンバーが3人以上アクティブ状態になったとき、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "UNIT_PRINTEMPS, STATUS=TAPPED", "destination": "recovery_count", "raw_effect": "COUNT_MEMBER"}}; UNKNOWN(43)(99) -> PLAYER {{"filter": "UNIT_PRINTEMPS", "raw_val": "ALL"}}; META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[29, 1, 65537, 0, 4, 43, 99, 65537, 0, 4, 0, 3, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-029-L - 知らないLove＊教えてLove

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカードが0枚で、かつ自分のステージにいるメンバーが『lilywhite』のみの場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MAX": 0, "raw_cond": "COUNT_SUCCESS_LIVE"}}, UNKNOWN(203) {{"ALL": true, "FILTER": "UNIT_LILYWHITE", "raw_cond": "COUNT_STAGE"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[218, 0, 0, 0, 48, 203, 4, 196608, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-030-L - Cutie Panther

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}相手のステージにウェイト状態のメンバーがいる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。
{{live_success.png|ライブ成功時}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、自分の控え室から『BiBi』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(306) {{"FILTER": "OPPONENT, STATUS=TAPPED", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: UNKNOWN(48)(2) -> SELF

TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"FILTER": "UNIT_BIBI, TYPE_MEMBER", "MIN": 2, "raw_cond": "DISCARD_UNIQUE_NAMES_COUNT"}}
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "UNIT_BIBI", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[306, 1, 2, 0, 48, 48, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[0, 2, 327684, 0, 48, 17, 1, 327680, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-pb1-031-L - 輝夜の城で踊りたい

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：エールにより公開された自分のカードの中から、『μ's』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
EFFECT: UNKNOWN(41)(1) -> CARD_HAND {{"filter": "GROUP_ID=0", "source": "YELL", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 1, 16, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!-pb1-032-L - SENTIMENTAL StepS

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分の成功ライブカード置き場に『μ's』のカードがある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 1, "FILTER": "GROUP_ID=0", "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[218, 1, 16, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-pb1-033-L - KiRa-KiRa Sensation!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-001-SD - 高坂 穂乃果

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(218) {TARGET=SELF, {"GE": 2, "zone": "SUCCESS_PILE", "raw_cond": "COUNT_CARDS"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}

TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "count", "raw_effect": "COUNT_CARDS", "zone": "SUCCESS_PILE"}}; SWAP_CARDS(1) -> SELF {{"per_card": "COUNT", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[218, 2, 0, 0, 48, 15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[29, 0, 0, 0, 4, 11, 1, 1, 268435456, 268491264, 1, 0, 0, 0, 0]`

---

## PL!-sd1-002-SD - 絢瀬 絵里

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-sd1-003-SD - 南 ことり

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト4以下の『μ's』のメンバーカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "UNIT_M_S, COST_LE_4", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["RED", "GREEN", "PURPLE"], "destination": "color", "raw_val": "PLAYER"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "COLOR", "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, -909705216, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 30, 1, 0, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-sd1-004-SD - 園田 海未

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『μ's』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"filter": "UNIT_M_S, TYPE=LIVE", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, 5, 13041672, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!-sd1-005-SD - 星空 凛

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!-sd1-006-SD - 西木野 真姫

### Japanese Ability
```text
{{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
COST: REVEAL_HAND(0) {{"FILTER": "TYPE=LIVE", "destination": "success"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "target_success", "raw_effect": "SELECT_SUCCESS_PILE"}}; UNKNOWN(44)(1) -> PLAYER {{"raw_val": "TARGET_SUCCESS"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "MOVE_TO_SUCCESS_PILE", "raw_val": "TARGET_REVEALED"}}
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 29, 1, 0, 0, 4, 44, 1, 0, 0, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-sd1-007-SD - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(5) -> PLAYER {FROM=DECK_TOP}; MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 5, 1, 0, 65540, 309, 1, 8, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-sd1-008-SD - 小泉 花陽

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のデッキの上からカードを10枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: UNKNOWN(58)(10) -> PLAYER {FROM=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[58, 10, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!-sd1-009-SD - 矢澤 にこ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の控え室に『μ's』のカードが25枚以上ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(209) {{"FILTER": "UNIT_M_S", "GE": 25, "zone": "CARD_DISCARD", "val": "PLAYER", "raw_cond": "COUNT_CARDS"}}
EFFECT: META_RULE(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[209, 25, 13041664, 14680064, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!-sd1-010-SD - 高坂 穂乃果

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-011-SD - 絢瀬 絵里

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!-sd1-012-SD - 南 ことり

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!-sd1-013-SD - 園田 海未

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-014-SD - 星空 凛

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-015-SD - 西木野 真姫

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 5, 5, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!-sd1-016-SD - 東條 希

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!-sd1-017-SD - 小泉 花陽

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-018-SD - 矢澤 にこ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-019-SD - START:DASH!!

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`

---

## PL!-sd1-020-SD - きっと青春が聞こえる

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-021-SD - これからのSomeday

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!-sd1-022-SD - 僕らは今のなかで

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード1枚につき、このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{heart_00.png|heart0}}少なくなる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "count", "raw_effect": "COUNT_CARDS", "zone": "SUCCESS_PILE"}}; ACTIVATE_MEMBER(2) -> SELF {{"raw_effect": "HEART_COST_REDUCTION", "per_card": "COUNT", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[29, 0, 0, 0, 4, 29, 2, 1, 268435456, 268491264, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-001-PR - 日野下花帆

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 536870912, 65542, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-002-PR - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 536870912, 65542, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-003-PR - 乙宗 梢

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-PR-004-PR - 夕霧綴理

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-PR-005-PR - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 536870912, 65542, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-006-PR - 藤島 慈

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-PR-007-PR - 百生 吟子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-PR-008-PR - 徒町 小鈴

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-PR-009-PR - 安養寺 姫芽

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-PR-010-PR - Reflection in the mirror

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-011-PR - Sparkly Spot

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-012-PR - アイデンティティ

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-014-PR - 日野下花帆

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-016-PR - 日野下花帆

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0) {{"destination": "discarded"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": "BLUE", "duration": "UNTIL_LIVE_END"}}; SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 12, 2, 0, 0, 4, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-017-PR - 村野さやか

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0) {{"destination": "discarded"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": "PINK", "duration": "UNTIL_LIVE_END"}}; SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 12, 2, 0, 0, 4, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-018-PR - 大沢瑠璃乃

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-019-PR - 百生 吟子

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(3) -> PLAYER {FROM=DECK_TOP} (Optional); SEARCH_DECK(1) -> SELF {{"heart_type": 4}}
```

### Bytecode Sequences
- Ability 1: `[58, 3, 1, 536870912, 65540, 209, 4, 0, 14680064, 48, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-020-PR - 徒町 小鈴

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分の控え室にあるメンバーカード2枚を好きな順番でデッキの一番上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(74)(2) -> PLAYER {FROM=DISCARD, {"filter": "TYPE=MEMBER", "destination": "targets"}}; SET_BLADES(1) -> PLAYER {{"order": "CHOSEN", "destination": "deck_top", "raw_val": "TARGETS"}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 74, 2, 5, 0, 458756, 31, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-021-PR - 安養寺 姫芽

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(3) -> PLAYER {FROM=DECK_TOP} (Optional); SEARCH_DECK(1) -> SELF {{"heart_type": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 3, 1, 536870912, 65540, 209, 4, 0, 14680064, 48, 12, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-022-PR - 桂城 泉

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分の控え室にあるメンバーカード2枚を好きな順番でデッキの一番上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-PR-023-PR - セラス 柳田 リリエンフェルト

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(74)(2) -> PLAYER {FROM=DISCARD, {"filter": "TYPE=MEMBER", "destination": "targets"}}; SET_BLADES(1) -> PLAYER {{"order": "CHOSEN", "destination": "deck_top", "raw_val": "TARGETS"}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 74, 2, 5, 0, 458756, 31, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-001-P - 日野下花帆

### Japanese Ability
```text
{{toujyou.png|登場}}エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(81)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-001-R - 日野下花帆

### Japanese Ability
```text
{{toujyou.png|登場}}エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(81)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-002-P - 村野さやか

### Japanese Ability
```text
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}、このメンバーをステージから控え室に置く：自分の控え室からコスト15以下の『蓮ノ空』のメンバーカードを1枚、このメンバーがいたエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: ENERGY(2), SACRIFICE_SELF(0) {{"destination": "success"}}
EFFECT: UNKNOWN(74)(1) -> PLAYER {{"zone": "DISCARD", "filter": "UNIT_HASUNOSORA, COST_LE=15", "destination": "target"}}; UNKNOWN(63)(1) -> PLAYER {{"repro_area": true, "raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 74, 1, -551878511, 14680064, 458756, 63, 1, 1, 0, 458756, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-002-R - 村野さやか

### Japanese Ability
```text
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}、このメンバーをステージから控え室に置く：自分の控え室からコスト15以下の『蓮ノ空』のメンバーカードを1枚、このメンバーがいたエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: ENERGY(2), SACRIFICE_SELF(0) {{"destination": "success"}}
EFFECT: UNKNOWN(74)(1) -> PLAYER {{"zone": "DISCARD", "filter": "UNIT_HASUNOSORA, COST_LE=15", "destination": "target"}}; UNKNOWN(63)(1) -> PLAYER {{"repro_area": true, "raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 74, 1, -551878511, 14680064, 458756, 63, 1, 1, 0, 458756, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-003-P - 乙宗 梢

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_HASUNOSORA, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: META_RULE(1) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "UNIT_HASUNOSORA, COST_LE=4", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[17, 1, -920977264, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-003-P＋ - 乙宗 梢

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_HASUNOSORA, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: META_RULE(1) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "UNIT_HASUNOSORA, COST_LE=4", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[17, 1, -920977264, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-003-R＋ - 乙宗 梢

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_HASUNOSORA, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: META_RULE(1) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "UNIT_HASUNOSORA, COST_LE=4", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[17, 1, -920977264, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-003-SEC - 乙宗 梢

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_HASUNOSORA, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: META_RULE(1) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "UNIT_HASUNOSORA, COST_LE=4", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[17, 1, -920977264, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-004-P - 夕霧綴理

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "UNIT_HASUNOSORA", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_CARDS", "raw_val": "ZONE=\"LIVE_SLOTS\""}} (Optional); SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 1769617, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-004-P＋ - 夕霧綴理

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "UNIT_HASUNOSORA", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_CARDS", "raw_val": "ZONE=\"LIVE_SLOTS\""}} (Optional); SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 1769617, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-004-R＋ - 夕霧綴理

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "UNIT_HASUNOSORA", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_CARDS", "raw_val": "ZONE=\"LIVE_SLOTS\""}} (Optional); SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 1769617, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-004-SEC - 夕霧綴理

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "UNIT_HASUNOSORA", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_CARDS", "raw_val": "ZONE=\"LIVE_SLOTS\""}} (Optional); SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 1769617, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-005-P - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
COST: DISCARD_HAND(0) {{"destination": "discarded"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER {{"raw_val": "COUNT_CARDS(DISCARDED"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-005-R - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
COST: DISCARD_HAND(0) {{"destination": "discarded"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER {{"raw_val": "COUNT_CARDS(DISCARDED"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-006-P - 藤島 慈

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "GE": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "color_val", "raw_effect": "SELECT_COLOR"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "COLOR_VAL", "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 1, 0, 50331648, 48, 58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-006-P＋ - 藤島 慈

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "GE": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "color_val", "raw_effect": "SELECT_COLOR"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "COLOR_VAL", "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 1, 0, 50331648, 48, 58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-006-R＋ - 藤島 慈

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "GE": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "color_val", "raw_effect": "SELECT_COLOR"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "COLOR_VAL", "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 1, 0, 50331648, 48, 58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-006-SEC - 藤島 慈

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "GE": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "color_val", "raw_effect": "SELECT_COLOR"}}; SEARCH_DECK(1) -> SELF {{"heart_type": "COLOR_VAL", "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 1, 0, 50331648, 48, 58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-007-P - 百生 吟子

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-007-R - 百生 吟子

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-008-P - 徒町 小鈴

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(3) -> PLAYER {FROM=DECK_TOP, {"destination": "discarded"}}
```

### Bytecode Sequences
- Ability 1: `[58, 3, 1, 0, 65540, 209, 3, 4, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-008-R - 徒町 小鈴

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(3) -> PLAYER {FROM=DECK_TOP, {"destination": "discarded"}}
```

### Bytecode Sequences
- Ability 1: `[58, 3, 1, 0, 65540, 209, 3, 4, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-009-P - 安養寺 姫芽

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『みらくらぱーく！』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "UNIT_MIRAKURA", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 5, 2031617, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-009-R - 安養寺 姫芽

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『みらくらぱーく！』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "UNIT_MIRAKURA", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 5, 2031617, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-010-N - 日野下花帆

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-011-N - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "TYPE_LIVE", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 5, 9, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-012-N - 乙宗 梢

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-bp1-012-PR - 乙宗 梢

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-bp1-013-N - 夕霧綴理

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-bp1-014-N - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-015-N - 藤島 慈

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-bp1-016-N - 百生 吟子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-bp1-017-N - 徒町 小鈴

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-bp1-018-N - 安養寺 姫芽

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!HS-bp1-019-L - Dream Believers

### Japanese Ability
```text
(エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
```

### Bytecode Sequences
- Ability 1: `[1, 0, 0, 0, 0]`

---

## PL!HS-bp1-020-L - 365 Days

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-021-L - Holiday∞Holiday

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『蓮ノ空』のライブカードを1枚手札に加える。

(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
EFFECT: UNKNOWN(74)(1) -> CARD_HAND {{"zone": "YELL_REVEALED", "filter": "UNIT_HASUNOSORA, TYPE_LIVE"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1769624, 536870912, 65542, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-022-L - AWOKE

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(226) {{"FILTER": "UNIT_HASUNOSORA, TYPE_MEMBER", "GE": 10, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[226, 10, 0, 8192, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp1-023-L - ド！ド！ド！

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高く、かつ自分のステージに『蓮ノ空』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=SCORE, {"val": "PLAYER", "raw_cond": "SCORE_LEAD", "comparison": "GT"}}, UNKNOWN(203) {{"FILTER": "UNIT_HASUNOSORA", "GE": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 16, 203, 1, 1769616, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-001-P - 日野下花帆

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からスコア3以下の『蓮ノ空』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2) {{"destination": "success"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=4, SCORE_LE=3", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 15, 1, 144, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-001-R - 日野下花帆

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からスコア3以下の『蓮ノ空』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2) {{"destination": "success"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=4, SCORE_LE=3", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 15, 1, 144, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-002-P - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを2枚まで手札に加える。
{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(2) -> CARD_HAND {{"filter": "COST_LE=2", "source": "discard"}} (Optional)

TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "COST_GT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[17, 2, -989855744, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-002-P＋ - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを2枚まで手札に加える。
{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(2) -> CARD_HAND {{"filter": "COST_LE=2", "source": "discard"}} (Optional)

TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "COST_GT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[17, 2, -989855744, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-002-R＋ - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを2枚まで手札に加える。
{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(2) -> CARD_HAND {{"filter": "COST_LE=2", "source": "discard"}} (Optional)

TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "COST_GT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[17, 2, -989855744, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-002-SEC - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを2枚まで手札に加える。
{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(2) -> CARD_HAND {{"filter": "COST_LE=2", "source": "discard"}} (Optional)

TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"FILTER": "COST_GT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[17, 2, -989855744, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-003-P - 乙宗 梢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(125)(3) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 125, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-003-R - 乙宗 梢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(125)(3) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 125, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-004-P - 夕霧綴理

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-004-R - 夕霧綴理

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-005-P - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージのエリアすべてにメンバーが登場している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "NOT_SELF", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_LEFT", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_CENTER", "destination": "center_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_RIGHT", "destination": "right_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 0, 0, 0, 0, 48, 0, 1, 2031616, 0, 48, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 8, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 29, 1, 1, 0, 4, 29, 1, 1, 0, 4, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 2, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-005-P＋ - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージのエリアすべてにメンバーが登場している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "NOT_SELF", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_LEFT", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_CENTER", "destination": "center_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_RIGHT", "destination": "right_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 0, 0, 0, 0, 48, 0, 1, 2031616, 0, 48, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 8, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 29, 1, 1, 0, 4, 29, 1, 1, 0, 4, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 2, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-005-R＋ - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージのエリアすべてにメンバーが登場している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "NOT_SELF", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_LEFT", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_CENTER", "destination": "center_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_RIGHT", "destination": "right_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 0, 0, 0, 0, 48, 0, 1, 2031616, 0, 48, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 8, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 29, 1, 1, 0, 4, 29, 1, 1, 0, 4, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 2, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-005-SEC - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージのエリアすべてにメンバーが登場している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "NOT_SELF", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_LEFT", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_CENTER", "destination": "center_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "AREA_RIGHT", "destination": "right_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 0, 0, 0, 0, 48, 0, 1, 2031616, 0, 48, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 8, 0, 0, 0, 312, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 29, 1, 1, 0, 4, 29, 1, 1, 0, 4, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 0, 0, 0, 48, 0, 2, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-006-P - 藤島 慈

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーを、それぞれ好きなエリアに移動させてもよい。
{{jyouji.png|常時}}自分のステージにいるほかの『みらくらぱーく！』のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"destination": "targets", "raw_val": "ALL"}}; PLACE_UNDER(1) -> PLAYER {{"raw_val": "TARGETS"}}

TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "UNIT_MIRAKURA, NOT_SELF", "destination": "count_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; SWAP_CARDS(1) -> SELF {{"per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[65, 99, 1, 0, 262148, 20, 99, 99, 0, 1, 1, 0, 0, 0, 0]`
- Ability 2: `[29, 1, 2031617, 50331648, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-006-R - 藤島 慈

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーを、それぞれ好きなエリアに移動させてもよい。
{{jyouji.png|常時}}自分のステージにいるほかの『みらくらぱーく！』のメンバー1人につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"destination": "targets", "raw_val": "ALL"}}; PLACE_UNDER(1) -> PLAYER {{"raw_val": "TARGETS"}}

TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "UNIT_MIRAKURA, NOT_SELF", "destination": "count_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; SWAP_CARDS(1) -> SELF {{"per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[65, 99, 1, 0, 262148, 20, 99, 99, 0, 1, 1, 0, 0, 0, 0]`
- Ability 2: `[29, 1, 2031617, 50331648, 4, 11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-007-P - 百生 吟子

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：これにより控え室に置いたカードがメンバーカードの場合、控え室に置いたカードと同じ名前を持つメンバー1人は、ライブ終了時まで、{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"FILTER": "UNIT_CERISE, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_PASS"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=4", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "name_val", "raw_effect": "GET_NAME", "raw_val": "DISCARDED"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME=NAME_VAL", "destination": "target"}}; SEARCH_DECK(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target", "heart_type": "3"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 1769472, 0, 48, 15, 1, 144, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 1, 0, 536870912, 6, 3, 5, 0, 0, 0, 0, 0, 0, 0, 48, 29, 1, 0, 0, 4, 65, 1, 1, 0, 262148, 12, 1, 0, 0, 4, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-007-P＋ - 百生 吟子

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：これにより控え室に置いたカードがメンバーカードの場合、控え室に置いたカードと同じ名前を持つメンバー1人は、ライブ終了時まで、{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"FILTER": "UNIT_CERISE, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_PASS"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=4", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "name_val", "raw_effect": "GET_NAME", "raw_val": "DISCARDED"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME=NAME_VAL", "destination": "target"}}; SEARCH_DECK(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target", "heart_type": "3"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 1769472, 0, 48, 15, 1, 144, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 1, 0, 536870912, 6, 3, 5, 0, 0, 0, 0, 0, 0, 0, 48, 29, 1, 0, 0, 4, 65, 1, 1, 0, 262148, 12, 1, 0, 0, 4, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-007-R＋ - 百生 吟子

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：これにより控え室に置いたカードがメンバーカードの場合、控え室に置いたカードと同じ名前を持つメンバー1人は、ライブ終了時まで、{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"FILTER": "UNIT_CERISE, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_PASS"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=4", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "name_val", "raw_effect": "GET_NAME", "raw_val": "DISCARDED"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME=NAME_VAL", "destination": "target"}}; SEARCH_DECK(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target", "heart_type": "3"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 1769472, 0, 48, 15, 1, 144, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 1, 0, 536870912, 6, 3, 5, 0, 0, 0, 0, 0, 0, 0, 48, 29, 1, 0, 0, 4, 65, 1, 1, 0, 262148, 12, 1, 0, 0, 4, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-007-SEC - 百生 吟子

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：これにより控え室に置いたカードがメンバーカードの場合、控え室に置いたカードと同じ名前を持つメンバー1人は、ライブ終了時まで、{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"FILTER": "UNIT_CERISE, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_PASS"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=4", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "name_val", "raw_effect": "GET_NAME", "raw_val": "DISCARDED"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME=NAME_VAL", "destination": "target"}}; SEARCH_DECK(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target", "heart_type": "3"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 1769472, 0, 48, 15, 1, 144, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 1, 0, 536870912, 6, 3, 5, 0, 0, 0, 0, 0, 0, 0, 48, 29, 1, 0, 0, 4, 65, 1, 1, 0, 262148, 12, 1, 0, 0, 4, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-008-P - 徒町 小鈴

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーよりコストが低い『DOLLCHESTRA』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "UNIT_DOLL, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 1900544, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-008-R - 徒町 小鈴

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーよりコストが低い『DOLLCHESTRA』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "UNIT_DOLL, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 1900544, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-009-P - 安養寺 姫芽

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.png|heart01}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "UNIT_MIRAKURA, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 1, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 231, 0, 2031616, 0, 0, 312, 0, 0, 0, 48, 12, 2, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-009-R - 安養寺 姫芽

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：このメンバーよりコストが低い『みらくらぱーく！』のメンバーからバトンタッチして登場した場合、ライブ終了時まで、{{heart_01.png|heart01}}{{heart_01.png|heart01}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "UNIT_MIRAKURA, COST_LT=SELF", "val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 1, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 231, 0, 2031616, 0, 0, 312, 0, 0, 0, 48, 12, 2, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-010-N - 日野下花帆

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 5, 5, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-011-N - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}デッキの上からカードを5枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(5) -> PLAYER {FROM=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[58, 5, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-011-PR - 村野さやか

### Japanese Ability
```text
{{toujyou.png|登場}}デッキの上からカードを5枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(5) -> PLAYER {FROM=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[58, 5, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-012-N - 乙宗 梢

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"filter": "TYPE_MEMBER", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483643, 4, 0, 67334, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-013-N - 夕霧綴理

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"filter": "TYPE_LIVE", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483643, 8, 0, 67334, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-014-N - 大沢瑠璃乃

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引く。ライブ終了時まで、自分はライブできない。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; TRIGGER_REMOTE(0) -> PLAYER {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 35, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-015-N - 藤島 慈

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-016-N - 百生 吟子

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-017-N - 徒町 小鈴

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室にカードが10枚以上ある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(205) {{"MIN": 10, "raw_cond": "COUNT_DISCARD"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[205, 10, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-018-N - 安養寺 姫芽

### Japanese Ability
```text
{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
CONDITION: NONE {{"raw_cond": "IS_MAIN_PHASE"}}
EFFECT: UNKNOWN(76)(1) -> PLAYER {{"destination": "live_zone"}}; UNKNOWN(77)(1) -> PLAYER {TARGET=NEXT_LIVE_SET}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 64, 2, 0, 0, 0, 76, 1, 1, 0, 458756, 77, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-019-L - Bloom the smile, Bloom the dream!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "GROUP_ID=4", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_01.png", "{{heart_04.png", "{{heart_05.png", "{{no_action.png"]}}
    Options:
      1: UNK(1)->PLAYER {{"raw_val": "1/1/0"}}
      2: UNK(1)->PLAYER {{"raw_val": "4/4/0"}}
      3: UNK(1)->PLAYER {{"raw_val": "5/5/0"}}
      4: DRAW(1)->PLAYER
```

### Bytecode Sequences
- Ability 1: `[203, 0, 144, 0, 48, 30, 4, 0, 0, 0, 2, 3, 0, 0, 0, 2, 4, 0, 0, 0, 2, 5, 0, 0, 0, 2, 6, 0, 0, 0, 83, 0, 0, 0, 4, 2, 7, 0, 0, 0, 83, 0, 0, 0, 4, 2, 5, 0, 0, 0, 83, 0, 0, 0, 4, 2, 3, 0, 0, 0, 0, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-020-L - Link to the FUTURE

### Japanese Ability
```text
{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。
{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> SELF {{"tag": "\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\"", "raw_val": "\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\""}}

TRIGGER: ON_LIVE_START
EFFECT: META_RULE(2) -> SELF {{"per_card": "STAGE", "filter": "UNIT_HASU, UNIQUE_NAMES", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 2, 1769473, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-021-L - 眩耀夜行

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_04.png|heart04}}減らす。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "GROUP_ID=4, BATON_TOUCHED", "MIN": 2, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(48)(1) -> SELF {{"heart_type": "4"}}
```

### Bytecode Sequences
- Ability 1: `[203, 0, 144, 0, 48, 48, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-022-L - アオクハルカ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の控え室に『スリーズブーケ』のライブカードが3枚以上ある場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(205) {{"FILTER": "UNIT_CERISE, TYPE_LIVE", "MIN": 3, "val": "PLAYER", "raw_cond": "COUNT_DISCARD"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[205, 0, 1769480, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-023-L - Mirage Voyage

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_05.png|heart05}}減らす。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "GROUP_ID=4, BATON_TOUCHED", "MIN": 2, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(48)(1) -> SELF {{"heart_type": "5"}}
```

### Bytecode Sequences
- Ability 1: `[203, 0, 144, 0, 48, 48, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-024-L - レディバグ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに「徒町小鈴」が登場しており、かつ「徒町小鈴」よりコストの大きい「村野さやか」が登場している場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(201) {TARGET=KOSUZU, {"NAME": "\u5f92\u753a\u5c0f\u9234", "val": "PLAYER", "raw_cond": "HAS_MEMBER"}}, UNKNOWN(201) {TARGET=SAYAKA, {"NAME": "\u6751\u91ce\u3055\u3084\u304b", "val": "PLAYER", "raw_cond": "HAS_MEMBER"}}, NONE {{"val": "GET_COST(SAYAKA", "raw_cond": "VALUE_GT"}}
EFFECT: UNKNOWN(48)(3) -> SELF {{"heart_type": "ANY"}}
```

### Bytecode Sequences
- Ability 1: `[201, 0, 0, 8704, 48, 201, 0, 0, 7936, 48, 0, 0, 0, 0, 48, 48, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-025-L - ココン東西

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_01.png|heart01}}減らす。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "GROUP_ID=4, BATON_TOUCHED", "MIN": 2, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(48)(1) -> SELF {{"heart_type": "1"}}
```

### Bytecode Sequences
- Ability 1: `[203, 0, 144, 0, 48, 48, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!HS-bp2-026-L - みらくりえーしょん

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージの右サイドエリアに「大沢瑠璃乃」が、左サイドエリアに「安養寺姫芽」が、センターエリアに「藤島慈」がそれぞれ登場している場合、このカードのスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(209) {{"NAME": "Rurino", "SLOT": "RIGHT", "raw_cond": "MEMBER_AT_SLOT"}}, UNKNOWN(209) {{"NAME": "Hime", "SLOT": "LEFT", "raw_cond": "MEMBER_AT_SLOT"}}, UNKNOWN(209) {{"NAME": "Megu", "SLOT": "CENTER", "raw_cond": "MEMBER_AT_SLOT"}}
EFFECT: META_RULE(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[209, 0, 0, 8320, 48, 209, 0, 0, 8832, 48, 209, 0, 0, 8448, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-PR-003-PR - 上原歩夢

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "raw_cond": "COUNT_STAGE"}}, UNKNOWN(209) {{"FILTER": "TYPE=LIVE", "EQ": 0, "val": "REVEALED_CARDS", "raw_cond": "COUNT_CARDS"}}
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "TYPE=LIVE", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[203, 1, 0, 0, 48, 209, 0, 8, 0, 48, 41, 5, 9, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!N-PR-004-PR - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-PR-005-PR - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-PR-006-PR - 朝香果林

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-PR-007-PR - 宮下 愛

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-PR-008-PR - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "raw_cond": "COUNT_STAGE"}}, UNKNOWN(209) {{"FILTER": "TYPE=LIVE", "EQ": 0, "val": "REVEALED_CARDS", "raw_cond": "COUNT_CARDS"}}
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "TYPE=LIVE", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[203, 1, 0, 0, 48, 209, 0, 8, 0, 48, 41, 5, 9, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!N-PR-009-PR - 優木せつ菜

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-PR-010-PR - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札をすべて公開する：自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "raw_cond": "COUNT_STAGE"}}, UNKNOWN(209) {{"FILTER": "TYPE=LIVE", "EQ": 0, "val": "REVEALED_CARDS", "raw_cond": "COUNT_CARDS"}}
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "TYPE=LIVE", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[203, 1, 0, 0, 48, 209, 0, 8, 0, 48, 41, 5, 9, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!N-PR-011-PR - 天王寺璃奈

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-PR-012-PR - 三船栞子

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-PR-013-PR - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-PR-014-PR - 鐘 嵐珠

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-001-P - 上原歩夢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-001-R - 上原歩夢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-002-P - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}

TRIGGER: ACTIVATED
COST: ENERGY(2), DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(57)(1) -> PLAYER {{"raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`
- Ability 2: `[312, 0, 0, 0, 48, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-002-P＋ - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}

TRIGGER: ACTIVATED
COST: ENERGY(2), DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(57)(1) -> PLAYER {{"raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`
- Ability 2: `[312, 0, 0, 0, 48, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-002-R＋ - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}

TRIGGER: ACTIVATED
COST: ENERGY(2), DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(57)(1) -> PLAYER {{"raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`
- Ability 2: `[312, 0, 0, 0, 48, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-002-SEC - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}

TRIGGER: ACTIVATED
COST: ENERGY(2), DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(57)(1) -> PLAYER {{"raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`
- Ability 2: `[312, 0, 0, 0, 48, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-003-P - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER (Optional); SEARCH_DECK(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 15, 1, 0, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 45, 1, 1, 536870912, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-003-P＋ - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER (Optional); SEARCH_DECK(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 15, 1, 0, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 45, 1, 1, 536870912, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-003-R＋ - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER (Optional); SEARCH_DECK(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 15, 1, 0, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 45, 1, 1, 536870912, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-003-SEC - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER (Optional); SEARCH_DECK(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 15, 1, 0, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 45, 1, 1, 536870912, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-004-P - 朝香果林

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにほかの『虹ヶ咲』のメンバーがいる場合、エネルギーを1枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "FILTER": "GROUP_ID=2", "raw_cond": "COUNT_STAGE"}}
EFFECT: UNKNOWN(81)(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[203, 1, 80, 0, 48, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-004-R - 朝香果林

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにほかの『虹ヶ咲』のメンバーがいる場合、エネルギーを1枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "FILTER": "GROUP_ID=2", "raw_cond": "COUNT_STAGE"}}
EFFECT: UNKNOWN(81)(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[203, 1, 80, 0, 48, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-005-P - 宮下 愛

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-005-R - 宮下 愛

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-006-P - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 226, 1, 0, 4096, 48, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-006-P＋ - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 226, 1, 0, 4096, 48, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-006-R＋ - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 226, 1, 0, 4096, 48, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-006-SEC - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 226, 1, 0, 4096, 48, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-007-P - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-007-R - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-008-P - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のメンバーカードを1枚控え室に置く：自分の控え室から、これにより控え室に置いたメンバーカードより、コストの低いメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"FILTER": "TYPE=MEMBER", "destination": "target_val"}}
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "COST_LT_TARGET_VAL", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, -1056964608, 283115520, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-008-R - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のメンバーカードを1枚控え室に置く：自分の控え室から、これにより控え室に置いたメンバーカードより、コストの低いメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"FILTER": "TYPE=MEMBER", "destination": "target_val"}}
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "COST_LT_TARGET_VAL", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, -1056964608, 283115520, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-009-P - 天王寺璃奈

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを2枚控え室に置く。その後、自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(2) -> PLAYER {FROM=DECK_TOP}; SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 58, 2, 1, 0, 65540, 17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-009-R - 天王寺璃奈

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを2枚控え室に置く。その後、自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(58)(2) -> PLAYER {FROM=DECK_TOP}; SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 58, 2, 1, 0, 65540, 17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-010-P - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-010-R - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-011-P - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(69)(1) -> PLAYER {{"destination": "target", "raw_val": "FILTER=\"TYPE=LIVE\""}} (Optional); UNKNOWN(44)(1) -> PLAYER {{"raw_val": "TARGET"}}; UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 69, 1, 1, 536870912, 4, 44, 1, 0, 0, 4, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-011-R - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける。そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(69)(1) -> PLAYER {{"destination": "target", "raw_val": "FILTER=\"TYPE=LIVE\""}} (Optional); UNKNOWN(44)(1) -> PLAYER {{"raw_val": "TARGET"}}; UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 69, 1, 1, 536870912, 4, 44, 1, 0, 0, 4, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-012-P - 鐘 嵐珠

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(209) {{"GE": 3, "zone": "LIVE_SLOTS", "val": "PLAYER", "raw_cond": "COUNT_CARDS"}}, NONE {{"GE": 1, "val": "PLAYER", "zone": "LIVE_SLOTS", "filter": "UNIT_NIJIGASAKI", "raw_cond": "COUNT_CARDS_IN_ZONE"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6}}; SWAP_CARDS(2) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-012-P＋ - 鐘 嵐珠

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(209) {{"GE": 3, "zone": "LIVE_SLOTS", "val": "PLAYER", "raw_cond": "COUNT_CARDS"}}, NONE {{"GE": 1, "val": "PLAYER", "zone": "LIVE_SLOTS", "filter": "UNIT_NIJIGASAKI", "raw_cond": "COUNT_CARDS_IN_ZONE"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6}}; SWAP_CARDS(2) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-012-R＋ - 鐘 嵐珠

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(209) {{"GE": 3, "zone": "LIVE_SLOTS", "val": "PLAYER", "raw_cond": "COUNT_CARDS"}}, NONE {{"GE": 1, "val": "PLAYER", "zone": "LIVE_SLOTS", "filter": "UNIT_NIJIGASAKI", "raw_cond": "COUNT_CARDS_IN_ZONE"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6}}; SWAP_CARDS(2) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-012-SEC - 鐘 嵐珠

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(209) {{"GE": 3, "zone": "LIVE_SLOTS", "val": "PLAYER", "raw_cond": "COUNT_CARDS"}}, NONE {{"GE": 1, "val": "PLAYER", "zone": "LIVE_SLOTS", "filter": "UNIT_NIJIGASAKI", "raw_cond": "COUNT_CARDS_IN_ZONE"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 6}}; SWAP_CARDS(2) -> SELF

TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[12, 2, 6, 0, 4, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-013-N - 上原歩夢

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-014-N - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-015-N - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-016-N - 朝香果林

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-017-N - 宮下 愛

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-018-N - 近江彼方

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-019-N - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-019-PR - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-020-N - エマ・ヴェルデ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-021-N - 天王寺璃奈

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-022-N - 三船栞子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-023-N - ミア・テイラー

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-024-N - 鐘 嵐珠

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp1-025-L - 虹色Passions！

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-026-L - Poppin' Up!

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、エールにより公開された自分のカードの中から、『虹ヶ咲』のカードを1枚手札に加える。

(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=SCORE, {"val": "PLAYER", "raw_cond": "SCORE_LEAD", "comparison": "GT"}}
EFFECT: UNKNOWN(74)(1) -> CARD_HAND {{"zone": "YELL_REVEALED", "filter": "UNIT_NIJIGASAKI", "reveal": "True", "pick": "1"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 16, 74, 1, 13041744, 536870912, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-027-L - Solitude Rain

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバーが持つ{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_06.png|heart06}}のうち1色につき、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "UNIT_NIJIGASAKI", "destination": "count_val", "raw_effect": "COUNT_HEART_COLORS", "raw_val": "PLAYER"}}; META_RULE(1) -> SELF {{"per_card": "COUNT_VAL", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 13041745, 0, 4, 16, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-028-L - Butterfly

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『虹ヶ咲』のメンバーがいる場合、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 203, 1, 13041744, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp1-029-L - Eutopia

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のライブ中のカードが3枚以上ある場合、このカードのスコアを＋２する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(209) {{"GE": 3, "zone": "LIVE_SLOTS", "val": "PLAYER", "raw_cond": "COUNT_CARDS"}}
EFFECT: META_RULE(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[209, 3, 0, 0, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-001-P - 上原歩夢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(99) -> PLAYER {{"filter": "PLAYER", "destination": "targets", "raw_val": "ALL"}}; SWAP_CARDS(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "targets"}}
```

### Bytecode Sequences
- Ability 1: `[97, 1, 0, 536870912, 196608, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 10, 1, 0, 0, 4, 65, 99, 1, 0, 262148, 11, 2, 0, 0, 1, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-001-P＋ - 上原歩夢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(99) -> PLAYER {{"filter": "PLAYER", "destination": "targets", "raw_val": "ALL"}}; SWAP_CARDS(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "targets"}}
```

### Bytecode Sequences
- Ability 1: `[97, 1, 0, 536870912, 196608, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 10, 1, 0, 0, 4, 65, 99, 1, 0, 262148, 11, 2, 0, 0, 1, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-001-R＋ - 上原歩夢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(99) -> PLAYER {{"filter": "PLAYER", "destination": "targets", "raw_val": "ALL"}}; SWAP_CARDS(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "targets"}}
```

### Bytecode Sequences
- Ability 1: `[97, 1, 0, 536870912, 196608, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 10, 1, 0, 0, 4, 65, 99, 1, 0, 262148, 11, 2, 0, 0, 1, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-001-SEC - 上原歩夢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(99) -> PLAYER {{"filter": "PLAYER", "destination": "targets", "raw_val": "ALL"}}; SWAP_CARDS(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "targets"}}
```

### Bytecode Sequences
- Ability 1: `[97, 1, 0, 536870912, 196608, 3, 4, 0, 0, 0, 312, 0, 0, 0, 48, 10, 1, 0, 0, 4, 65, 99, 1, 0, 262148, 11, 2, 0, 0, 1, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-002-P - 中須かすみ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、自分のステージにいるこのメンバー以外の『虹ヶ咲』のメンバー1人は、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"destination": "color"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=2, NOT_SELF", "destination": "target"}}; SEARCH_DECK(1) -> PLAYER {{"heart_type": "COLOR", "duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 45, 1, 1, 0, 4, 65, 1, 81, 50331648, 262148, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-002-R - 中須かすみ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、自分のステージにいるこのメンバー以外の『虹ヶ咲』のメンバー1人は、そのハートを1つ得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"destination": "color"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=2, NOT_SELF", "destination": "target"}}; SEARCH_DECK(1) -> PLAYER {{"heart_type": "COLOR", "duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 3, 0, 0, 0, 45, 1, 1, 0, 4, 65, 1, 81, 50331648, 262148, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-003-P - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ。そのカードの{{toujyou.png|登場}}能力1つを発動させる。
（{{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(47)(1) -> PLAYER {FROM=DISCARD, {"filter": "GROUP_ID=2, TYPE_MEMBER, COST_LE_4"}}
```

### Bytecode Sequences
- Ability 1: `[47, 1, -922746795, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-003-R - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室にあるコスト4以下の『虹ヶ咲』のメンバーカードを1枚選ぶ。そのカードの{{toujyou.png|登場}}能力1つを発動させる。
（{{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(47)(1) -> PLAYER {FROM=DISCARD, {"filter": "GROUP_ID=2, TYPE_MEMBER, COST_LE_4"}}
```

### Bytecode Sequences
- Ability 1: `[47, 1, -922746795, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-004-P - 朝香果林

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0), DISCARD_HAND(1)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 80, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-004-R - 朝香果林

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: TAP_SELF(0), DISCARD_HAND(1)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 80, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-005-P - 宮下 愛

### Japanese Ability
```text
{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。
{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"MIN": 3, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(66)(5) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"MIN": 2, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 3, 0, 4096, 48, 66, 5, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 2, 0, 4096, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-005-P＋ - 宮下 愛

### Japanese Ability
```text
"{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。
{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"MIN": 3, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(66)(5) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"MIN": 2, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 3, 0, 4096, 48, 66, 5, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 2, 0, 4096, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-005-R＋ - 宮下 愛

### Japanese Ability
```text
{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。
{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"MIN": 3, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(66)(5) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"MIN": 2, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 3, 0, 4096, 48, 66, 5, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 2, 0, 4096, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-005-SEC - 宮下 愛

### Japanese Ability
```text
"{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。
{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"MIN": 3, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(66)(5) -> PLAYER

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"MIN": 2, "raw_cond": "COUNT_PLAYED_THIS_TURN", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 3, 0, 4096, 48, 66, 5, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 2, 0, 4096, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-006-P - 近江彼方

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "TAP_SELF"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-006-R - 近江彼方

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "TAP_SELF"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-007-P - 優木せつ菜

### Japanese Ability
```text
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このメンバーをステージから控え室に置く：自分の手札からコスト13以下の「優木せつ菜」のメンバーカードを1枚、このメンバーがいたエリアに登場させる。その後、自分のエネルギー置き場にあるエネルギー1枚をそのメンバーの下に置く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: ENERGY(2), SACRIFICE_SELF(0)
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "NAME='Setsuna Yuki', COST_LE_13", "destination": "target", "raw_effect": "SELECT_HAND"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"slot": "SAME_SLOT", "mode": "WAIT", "raw_effect": "PLAY_STAGE_SPECIFIC_SLOT", "raw_val": "TARGET"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "attach_member", "raw_effect": "SELECT_ENERGY"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, -620756991, 0, 4, 29, 1, 0, 536870912, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-007-R - 優木せつ菜

### Japanese Ability
```text
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このメンバーをステージから控え室に置く：自分の手札からコスト13以下の「優木せつ菜」のメンバーカードを1枚、このメンバーがいたエリアに登場させる。その後、自分のエネルギー置き場にあるエネルギー1枚をそのメンバーの下に置く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: ENERGY(2), SACRIFICE_SELF(0)
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "NAME='Setsuna Yuki', COST_LE_13", "destination": "target", "raw_effect": "SELECT_HAND"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"slot": "SAME_SLOT", "mode": "WAIT", "raw_effect": "PLAY_STAGE_SPECIFIC_SLOT", "raw_val": "TARGET"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "attach_member", "raw_effect": "SELECT_ENERGY"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, -620756991, 0, 4, 29, 1, 0, 536870912, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-008-P - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のステージにいるこのメンバー以外のウェイト状態のメンバー1人をアクティブにする。そうした場合、ライブ終了時まで、これによりアクティブにしたメンバーと、このメンバーは、それぞれ{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: MOVE_MEMBER(1) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, STATUS=TAPPED"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}} (Optional); SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 80, 50331648, 0, 53, 0, 0, 0, 4, 10, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 2, 0, 536870912, 6, 3, 5, 0, 0, 0, 65, 1, 1, 587202560, 262148, 43, 1, 0, 0, 4, 312, 0, 0, 0, 48, 12, 1, 4, 536870912, 4, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-008-P＋ - エマ・ヴェルデ

### Japanese Ability
```text
"{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のステージにいるこのメンバー以外のウェイト状態のメンバー1人をアクティブにする。そうした場合、ライブ終了時まで、これによりアクティブにしたメンバーと、このメンバーは、それぞれ{{heart_04.png|heart04}}を得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: MOVE_MEMBER(1) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, STATUS=TAPPED"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}} (Optional); SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 80, 50331648, 0, 53, 0, 0, 0, 4, 10, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 2, 0, 536870912, 6, 3, 5, 0, 0, 0, 65, 1, 1, 587202560, 262148, 43, 1, 0, 0, 4, 312, 0, 0, 0, 48, 12, 1, 4, 536870912, 4, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-008-R＋ - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のステージにいるこのメンバー以外のウェイト状態のメンバー1人をアクティブにする。そうした場合、ライブ終了時まで、これによりアクティブにしたメンバーと、このメンバーは、それぞれ{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: MOVE_MEMBER(1) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, STATUS=TAPPED"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}} (Optional); SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 80, 50331648, 0, 53, 0, 0, 0, 4, 10, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 2, 0, 536870912, 6, 3, 5, 0, 0, 0, 65, 1, 1, 587202560, 262148, 43, 1, 0, 0, 4, 312, 0, 0, 0, 48, 12, 1, 4, 536870912, 4, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-008-SEC - エマ・ヴェルデ

### Japanese Ability
```text
"{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のステージにいるこのメンバー以外のウェイト状態のメンバー1人をアクティブにする。そうした場合、ライブ終了時まで、これによりアクティブにしたメンバーと、このメンバーは、それぞれ{{heart_04.png|heart04}}を得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: MOVE_MEMBER(1) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, STATUS=TAPPED"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}} (Optional); SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 80, 50331648, 0, 53, 0, 0, 0, 4, 10, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 2, 0, 536870912, 6, 3, 5, 0, 0, 0, 65, 1, 1, 587202560, 262148, 43, 1, 0, 0, 4, 312, 0, 0, 0, 48, 12, 1, 4, 536870912, 4, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-009-P - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; SEARCH_DECK(1) -> SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[74, 2, 0, 536870912, 458759, 31, 2, 0, 0, 5243392, 3, 7, 0, 0, 0, 106, 0, 0, 0, 0, 312, 6, 0, 0, 48, 10, 1, 0, 0, 4, 312, 8, 0, 0, 48, 12, 1, 0, 0, 4, 312, 25, 0, 0, 48, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-009-P＋ - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; SEARCH_DECK(1) -> SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[74, 2, 0, 536870912, 458759, 31, 2, 0, 0, 5243392, 3, 7, 0, 0, 0, 106, 0, 0, 0, 0, 312, 6, 0, 0, 48, 10, 1, 0, 0, 4, 312, 8, 0, 0, 48, 12, 1, 0, 0, 4, 312, 25, 0, 0, 48, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-009-R＋ - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; SEARCH_DECK(1) -> SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[74, 2, 0, 536870912, 458759, 31, 2, 0, 0, 5243392, 3, 7, 0, 0, 0, 106, 0, 0, 0, 0, 312, 6, 0, 0, 48, 10, 1, 0, 0, 4, 312, 8, 0, 0, 48, 12, 1, 0, 0, 4, 312, 25, 0, 0, 48, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-009-SEC - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; SEARCH_DECK(1) -> SELF {{"heart_type": 0, "duration": "UNTIL_LIVE_END"}}; UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[74, 2, 0, 536870912, 458759, 31, 2, 0, 0, 5243392, 3, 7, 0, 0, 0, 106, 0, 0, 0, 0, 312, 6, 0, 0, 48, 10, 1, 0, 0, 4, 312, 8, 0, 0, 48, 12, 1, 0, 0, 4, 312, 25, 0, 0, 48, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-010-P - 三船栞子

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるメンバーカードを2枚まで、好きな順番でデッキの一番下に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u81ea\u5206", "\u76f8\u624b"]}}
    Options:
      1: SELECT_MODE(2)->PLAYER {{"destination": "deck_bottom", "source": "discard"}}
      2: SELECT_MODE(2)->OPPONENT {TARGET=OPPONENT, {"destination": "deck_bottom_opponent", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 17, 2, 1, 551550976, 458756, 2, 3, 0, 0, 0, 17, 2, 2, 551550976, 458754, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-010-R - 三船栞子

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるメンバーカードを2枚まで、好きな順番でデッキの一番下に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u81ea\u5206", "\u76f8\u624b"]}}
    Options:
      1: SELECT_MODE(2)->PLAYER {{"destination": "deck_bottom", "source": "discard"}}
      2: SELECT_MODE(2)->OPPONENT {TARGET=OPPONENT, {"destination": "deck_bottom_opponent", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 17, 2, 1, 551550976, 458756, 2, 3, 0, 0, 0, 17, 2, 2, 551550976, 458754, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-011-P - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ。そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。それぞれのメンバーのコストが同じ場合、元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, NOT_NAME='Mia", "destination": "target_member"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 2, 0, 262148, 0, 0, 0, 0, 48, 11, 1, 0, 0, 4, 0, 0, 0, 0, 48, 11, 1, 0, 0, 4, 0, 0, 0, 0, 48, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-011-R - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ。そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。それぞれのメンバーのコストが同じ場合、元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, NOT_NAME='Mia", "destination": "target_member"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 2, 0, 262148, 0, 0, 0, 0, 48, 11, 1, 0, 0, 4, 0, 0, 0, 0, 48, 11, 1, 0, 0, 4, 0, 0, 0, 0, 48, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-012-P - 鐘 嵐珠

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中から『虹ヶ咲』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "GROUP_ID=2", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 4, 81, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-012-R - 鐘 嵐珠

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中から『虹ヶ咲』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "GROUP_ID=2", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 4, 81, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-013-N - 上原歩夢

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを2枚引く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[97, 1, 0, 536870912, 196608, 3, 1, 0, 0, 0, 10, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-014-N - 中須かすみ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_04.png|heart04}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_01.png", "{{heart_03.png", "{{heart_04.png"]}}
    Options:
      1: ACTIVATE_MEMBER(1)->SELF {{"raw_effect": "TRANSFORM_BASE_HEART"}}
      2: ACTIVATE_MEMBER(3)->SELF {{"raw_effect": "TRANSFORM_BASE_HEART"}}
      3: ACTIVATE_MEMBER(4)->SELF {{"raw_effect": "TRANSFORM_BASE_HEART"}}
```

### Bytecode Sequences
- Ability 1: `[30, 3, 0, 0, 0, 2, 2, 0, 0, 0, 2, 3, 0, 0, 0, 2, 4, 0, 0, 0, 29, 1, 0, 0, 4, 2, 5, 0, 0, 0, 29, 3, 0, 0, 4, 2, 3, 0, 0, 0, 29, 4, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-015-N - 桜坂しずく

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_02.png|heart02}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["{{heart_02.png", "{{heart_05.png", "{{heart_06.png"]}}
    Options:
      1: ACTIVATE_MEMBER(2)->SELF {{"raw_effect": "TRANSFORM_BASE_HEART"}}
      2: ACTIVATE_MEMBER(5)->SELF {{"raw_effect": "TRANSFORM_BASE_HEART"}}
      3: ACTIVATE_MEMBER(6)->SELF {{"raw_effect": "TRANSFORM_BASE_HEART"}}
```

### Bytecode Sequences
- Ability 1: `[30, 3, 0, 0, 0, 2, 2, 0, 0, 0, 2, 3, 0, 0, 0, 2, 4, 0, 0, 0, 29, 2, 0, 0, 4, 2, 5, 0, 0, 0, 29, 5, 0, 0, 4, 2, 3, 0, 0, 0, 29, 6, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-016-N - 朝香果林

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp3-017-N - 宮下 愛

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-018-N - 近江彼方

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp3-019-N - 優木せつ菜

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp3-020-N - エマ・ヴェルデ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp3-021-N - 天王寺璃奈

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp3-022-N - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-023-N - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-024-N - 鐘 嵐珠

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-025-L - Awakening Promise

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバー1人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい。そうした場合、ライブ終了時まで、そのメンバーは、これによって置いたエネルギーカード1枚につき、［赤ハート］［赤ハート］［赤ハート］を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "HAS_ATTACHED_ENERGY", "destination": "target_member"}}; ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "removed_count", "raw_effect": "SELECT_ATTACHED_ENERGY"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "MOVE_TO_ENERGY_DECK", "raw_val": "REMOVED_COUNT"}}; SEARCH_DECK(3) -> PLAYER {{"heart_type": 1, "per_card": "REMOVED_COUNT", "duration": "UNTIL_LIVE_END", "destination": "target_member", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 1, 0, 262148, 29, 0, 0, 0, 4, 29, 1, 0, 0, 4, 12, 3, 1, 268435456, 268487425, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-026-L - サイコーハート

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にスコアが１か５のカードがある場合、このカードのスコアを＋１する。それらが両方ある場合、代わりにスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"boost_score(1) -> self": true, "raw_effect": "IF"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"boost_score(1) -> self": true, "raw_effect": "IF"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-027-L - La Bella Patria

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"HEART_TYPE": 4, "MIN": 1, "raw_cond": "SURPLUS_HEARTS_CONTAINS"}}, UNKNOWN(203) {{"MIN": 1, "FILTER": "GROUP_ID=2", "raw_cond": "COUNT_STAGE"}}
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[0, 1, 0, 0, 48, 203, 1, 80, 0, 48, 23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-028-L - ツナガルコネクト

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る。その中から1枚までをデッキの上に置き、残りを控え室に置く。その後、自分のデッキの一番上のカードを1枚公開する。これによりライブカードを公開した場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"per_card": "STAGE", "filter": "GROUP_ID=2", "raw_effect": "LOOK_DECK_DYNAMIC_COUNT", "value_enabled": true, "value_threshold": 1}}; ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "MOVE_TO_DECK_TOP"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "DISCARD_REMAINDER"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "REVEAL_DECK_TOP"}}; META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[29, 1, 81, 268435456, 268487425, 29, 1, 0, 536870912, 4, 29, 1, 0, 0, 4, 29, 1, 0, 0, 4, 0, 0, 8, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-029-L - 未来ハーモニー

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp3-030-L - Love U my friends

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に{{icon_b_all.png|ALLブレード}}を持つカードが1枚以上ある場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"FILTER": "HAS_ALL_BLADE", "raw_cond": "YELL_PILE_CONTAINS"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-031-L - MONSTER GIRLS

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
EFFECT: META_RULE(1) -> SELF {{"per_card": "STAGE", "filter": "STATUS=TAPPED", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[16, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`

---

## PL!N-bp3-032-L - THE SECRET NiGHT

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp4-001-P - 上原歩夢

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分のエネルギーが相手より少ない場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(225) {{"raw_cond": "ENERGY_LAGGING", "comparison": "GE", "diff": 1}}
EFFECT: UNKNOWN(81)(1) -> PLAYER {{"mode": "WAIT"}}
```

### Bytecode Sequences
- Ability 1: `[225, 1, 0, 0, 48, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-001-R - 上原歩夢

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分のエネルギーが相手より少ない場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(225) {{"raw_cond": "ENERGY_LAGGING", "comparison": "GE", "diff": 1}}
EFFECT: UNKNOWN(81)(1) -> PLAYER {{"mode": "WAIT"}}
```

### Bytecode Sequences
- Ability 1: `[225, 1, 0, 0, 48, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-002-P - 中須かすみ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの一番上のカードを見る。自分はそのカードを控え室に置いてもよい。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "player_target", "raw_effect": "CHOICE_PLAYER"}}; ACTIVATE_MEMBER(1) -> PLAYER {TARGET=PLAYER_TARGET, {"destination": "revealed_card", "raw_effect": "LOOK_DECK_TOP"}}; ADD_TO_HAND(1) -> PLAYER {{"options": ["\u63a7\u3048\u5ba4\u306b\u7f6e\u304f", "\u30c7\u30c3\u30ad\u306e\u4e0a\u306b\u7f6e\u304f"]}}
    Options:
      1: ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "DISCARD_CARD", "raw_val": "REVEALED_CARD"}}
      2: ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "PASS"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 29, 1, 0, 0, 4, 30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 29, 1, 0, 0, 4, 2, 3, 0, 0, 0, 29, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-002-R - 中須かすみ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの一番上のカードを見る。自分はそのカードを控え室に置いてもよい。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "player_target", "raw_effect": "CHOICE_PLAYER"}}; ACTIVATE_MEMBER(1) -> PLAYER {TARGET=PLAYER_TARGET, {"destination": "revealed_card", "raw_effect": "LOOK_DECK_TOP"}}; ADD_TO_HAND(1) -> PLAYER {{"options": ["\u63a7\u3048\u5ba4\u306b\u7f6e\u304f", "\u30c7\u30c3\u30ad\u306e\u4e0a\u306b\u7f6e\u304f"]}}
    Options:
      1: ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "DISCARD_CARD", "raw_val": "REVEALED_CARD"}}
      2: ACTIVATE_MEMBER(1)->PLAYER {{"raw_effect": "PASS"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 29, 1, 0, 0, 4, 30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 29, 1, 0, 0, 4, 2, 3, 0, 0, 0, 29, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-003-P - 桜坂しずく

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=SCORE, {"TARGET": "OPPONENT", "raw_cond": "SCORE_LEAD", "comparison": "GT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 16, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-003-R - 桜坂しずく

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=SCORE, {"TARGET": "OPPONENT", "raw_cond": "SCORE_LEAD", "comparison": "GT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 16, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-004-P - 朝香果林

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}カードを1枚引く。相手のステージにいるコスト9以下のメンバーを1人までウェイトにする。
{{live_start.png|ライブ開始時}}相手のステージにいるウェイト状態のメンバーの数まで、自分の控え室にある『虹ヶ咲』のメンバーカードを選ぶ。それらを好きな順番でデッキの上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_9", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "OPPONENT, STATUS=TAPPED", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "deck_top", "source": "discard", "raw_val": "COUNT_VAL"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 65, 1, -754974718, 0, 262148, 53, 1, 3, 536870912, 4, 29, 1, 2, 0, 4, 17, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-004-P＋ - 朝香果林

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}カードを1枚引く。相手のステージにいるコスト9以下のメンバーを1人までウェイトにする。
{{live_start.png|ライブ開始時}}相手のステージにいるウェイト状態のメンバーの数まで、自分の控え室にある『虹ヶ咲』のメンバーカードを選ぶ。それらを好きな順番でデッキの上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_9", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "OPPONENT, STATUS=TAPPED", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "deck_top", "source": "discard", "raw_val": "COUNT_VAL"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 65, 1, -754974718, 0, 262148, 53, 1, 3, 536870912, 4, 29, 1, 2, 0, 4, 17, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-004-R＋ - 朝香果林

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}カードを1枚引く。相手のステージにいるコスト9以下のメンバーを1人までウェイトにする。
{{live_start.png|ライブ開始時}}相手のステージにいるウェイト状態のメンバーの数まで、自分の控え室にある『虹ヶ咲』のメンバーカードを選ぶ。それらを好きな順番でデッキの上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_9", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "OPPONENT, STATUS=TAPPED", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "deck_top", "source": "discard", "raw_val": "COUNT_VAL"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 65, 1, -754974718, 0, 262148, 53, 1, 3, 536870912, 4, 29, 1, 2, 0, 4, 17, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-004-SEC - 朝香果林

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}カードを1枚引く。相手のステージにいるコスト9以下のメンバーを1人までウェイトにする。
{{live_start.png|ライブ開始時}}相手のステージにいるウェイト状態のメンバーの数まで、自分の控え室にある『虹ヶ咲』のメンバーカードを選ぶ。それらを好きな順番でデッキの上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_9", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "OPPONENT, STATUS=TAPPED", "destination": "count_val", "raw_effect": "COUNT_MEMBER"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "deck_top", "source": "discard", "raw_val": "COUNT_VAL"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 65, 1, -754974718, 0, 262148, 53, 1, 3, 536870912, 4, 29, 1, 2, 0, 4, 17, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-005-P - 宮下 愛

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_HEARTS(2) -> PLAYER {{"filter": "COST_LE_4"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 32, 2, -922746879, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-005-R - 宮下 愛

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_HEARTS(2) -> PLAYER {{"filter": "COST_LE_4"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 32, 2, -922746879, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-006-P - 近江彼方

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の手札からコスト4以下の『虹ヶ咲』のメンバーカードを1枚ステージに登場させる。これにより登場したメンバーがブレードハートを持つ場合、このメンバーをウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "GROUP_ID=2, COST_LE_4, TYPE_MEMBER", "destination": "play_stage_empty", "raw_effect": "SELECT_HAND"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET_PLAYED"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 3, 0, 0, 0, 29, 1, -922746795, 0, 4, 0, 0, 0, 0, 48, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-006-R - 近江彼方

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の手札からコスト4以下の『虹ヶ咲』のメンバーカードを1枚ステージに登場させる。これにより登場したメンバーがブレードハートを持つ場合、このメンバーをウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "GROUP_ID=2, COST_LE_4, TYPE_MEMBER", "destination": "play_stage_empty", "raw_effect": "SELECT_HAND"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET_PLAYED"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 3, 0, 0, 0, 29, 1, -922746795, 0, 4, 0, 0, 0, 0, 48, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-007-P - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。
{{live_success.png|ライブ成功時}}自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}; ORDER_DECK(1) -> OPPONENT {TARGET=OPPONENT, {"destination": "card_hand_opponent", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: NONE {{"MIN": 15, "raw_cond": "SUM_ENERGY_OF_BOTH_PLAYERS"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 2}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}; SET_SCORE(1) -> OPPONENT {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 15, 1, 2, 14680064, 458754, 1, 0, 0, 0, 0]`
- Ability 2: `[12, 2, 2, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[23, 1, 0, 0, 134217732, 23, 1, 0, 0, 134217730, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-007-P＋ - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。
{{live_success.png|ライブ成功時}}自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}; ORDER_DECK(1) -> OPPONENT {TARGET=OPPONENT, {"destination": "card_hand_opponent", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: NONE {{"MIN": 15, "raw_cond": "SUM_ENERGY_OF_BOTH_PLAYERS"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 2}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}; SET_SCORE(1) -> OPPONENT {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 15, 1, 2, 14680064, 458754, 1, 0, 0, 0, 0]`
- Ability 2: `[12, 2, 2, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[23, 1, 0, 0, 134217732, 23, 1, 0, 0, 134217730, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-007-R＋ - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。
{{live_success.png|ライブ成功時}}自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}; ORDER_DECK(1) -> OPPONENT {TARGET=OPPONENT, {"destination": "card_hand_opponent", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: NONE {{"MIN": 15, "raw_cond": "SUM_ENERGY_OF_BOTH_PLAYERS"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 2}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}; SET_SCORE(1) -> OPPONENT {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 15, 1, 2, 14680064, 458754, 1, 0, 0, 0, 0]`
- Ability 2: `[12, 2, 2, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[23, 1, 0, 0, 134217732, 23, 1, 0, 0, 134217730, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-007-SEC - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。
{{live_success.png|ライブ成功時}}自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}; ORDER_DECK(1) -> OPPONENT {TARGET=OPPONENT, {"destination": "card_hand_opponent", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: NONE {{"MIN": 15, "raw_cond": "SUM_ENERGY_OF_BOTH_PLAYERS"}}
EFFECT: SEARCH_DECK(2) -> SELF {{"heart_type": 2}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}; SET_SCORE(1) -> OPPONENT {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 15, 1, 2, 14680064, 458754, 1, 0, 0, 0, 0]`
- Ability 2: `[12, 2, 2, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[23, 1, 0, 0, 134217732, 23, 1, 0, 0, 134217730, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-008-P - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：エネルギー1枚か『虹ヶ咲』のメンバー1人をアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1)
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30a8\u30cd\u30eb\u30ae\u30fc1\u679a\u3092\u30a2\u30af\u30c6\u30a3\u30d6\u306b\u3059\u308b", "\u300e\u8679\u30f6\u54b2\u300f\u306e\u30e1\u30f3\u30d0\u30fc1\u4eba\u3092\u30a2\u30af\u30c6\u30a3\u30d6\u306b\u3059\u308b"]}}
    Options:
      1: UNK(1)->PLAYER
      2: UNK(1)->PLAYER {{"filter": "GROUP_ID=2, STATUS=TAPPED", "destination": "target"}}, UNK(1)->PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 81, 1, 0, 0, 4, 2, 4, 0, 0, 0, 65, 1, 81, 0, 262148, 43, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-008-R - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：エネルギー1枚か『虹ヶ咲』のメンバー1人をアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1)
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30a8\u30cd\u30eb\u30ae\u30fc1\u679a\u3092\u30a2\u30af\u30c6\u30a3\u30d6\u306b\u3059\u308b", "\u300e\u8679\u30f6\u54b2\u300f\u306e\u30e1\u30f3\u30d0\u30fc1\u4eba\u3092\u30a2\u30af\u30c6\u30a3\u30d6\u306b\u3059\u308b"]}}
    Options:
      1: UNK(1)->PLAYER
      2: UNK(1)->PLAYER {{"filter": "GROUP_ID=2, STATUS=TAPPED", "destination": "target"}}, UNK(1)->PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 81, 1, 0, 0, 4, 2, 4, 0, 0, 0, 65, 1, 81, 0, 262148, 43, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-009-P - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを2枚引き、自分の手札を1枚デッキの一番上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(220) {TYPE=COST, {"TARGET": "PLAYER", "STAGE": true, "LESS_THAN": "OPPONENT", "raw_cond": "SUM_COST", "comparison": "GE"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; SET_BLADES(1) -> PLAYER {FROM=HAND, TO=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 48, 10, 2, 0, 0, 4, 31, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-009-R - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーのコストの合計が相手より低い場合、カードを2枚引き、自分の手札を1枚デッキの一番上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(220) {TYPE=COST, {"TARGET": "PLAYER", "STAGE": true, "LESS_THAN": "OPPONENT", "raw_cond": "SUM_COST", "comparison": "GE"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; SET_BLADES(1) -> PLAYER {FROM=HAND, TO=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 48, 10, 2, 0, 0, 4, 31, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-010-P - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "success_pile", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(68)(1) -> PLAYER {{"destination": "target_live"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[3, 1, 0, 0, 0, 15, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[68, 1, 1, 0, 65540, 0, 0, 0, 0, 48, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-010-P＋ - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "success_pile", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(68)(1) -> PLAYER {{"destination": "target_live"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[3, 1, 0, 0, 0, 15, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[68, 1, 1, 0, 65540, 0, 0, 0, 0, 48, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-010-R＋ - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "success_pile", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(68)(1) -> PLAYER {{"destination": "target_live"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[3, 1, 0, 0, 0, 15, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[68, 1, 1, 0, 65540, 0, 0, 0, 0, 48, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-010-SEC - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。
{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ORDER_DECK(1) -> PLAYER {{"filter": "GROUP_ID=2", "zone": "DISCARD", "destination": "success_pile", "source": "discard"}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(68)(1) -> PLAYER {{"destination": "target_live"}}; SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[3, 1, 0, 0, 0, 15, 1, 81, 551550976, 458756, 1, 0, 0, 0, 0]`
- Ability 2: `[68, 1, 1, 0, 65540, 0, 0, 0, 0, 48, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-011-P - ミア・テイラー

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {{"FILTER": "TYPE=LIVE", "OPTIONAL": true}}
EFFECT: UNKNOWN(45)(1) -> PLAYER; SEARCH_DECK(1) -> PLAYER {UNTIL=LIVE_END}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: UNKNOWN(58)(5) -> CARD_DECK_TOP; UNKNOWN(44)(1) -> PLAYER {{"filter": "TYPE=LIVE, GROUP=\u8679\u30f6\u54b2", "zone": "DISCARD"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 5, 0, 0, 262152, 230, 3, 0, 14680064, 48, 44, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-011-P＋ - ミア・テイラー

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {{"FILTER": "TYPE=LIVE", "OPTIONAL": true}}
EFFECT: UNKNOWN(45)(1) -> PLAYER; SEARCH_DECK(1) -> PLAYER {UNTIL=LIVE_END}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: UNKNOWN(58)(5) -> CARD_DECK_TOP; UNKNOWN(44)(1) -> PLAYER {{"filter": "TYPE=LIVE, GROUP=\u8679\u30f6\u54b2", "zone": "DISCARD"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 5, 0, 0, 262152, 230, 3, 0, 14680064, 48, 44, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-011-R＋ - ミア・テイラー

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {{"FILTER": "TYPE=LIVE", "OPTIONAL": true}}
EFFECT: UNKNOWN(45)(1) -> PLAYER; SEARCH_DECK(1) -> PLAYER {UNTIL=LIVE_END}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: UNKNOWN(58)(5) -> CARD_DECK_TOP; UNKNOWN(44)(1) -> PLAYER {{"filter": "TYPE=LIVE, GROUP=\u8679\u30f6\u54b2", "zone": "DISCARD"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 5, 0, 0, 262152, 230, 3, 0, 14680064, 48, 44, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-011-SEC - ミア・テイラー

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。
{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(1) {{"FILTER": "TYPE=LIVE", "OPTIONAL": true}}
EFFECT: UNKNOWN(45)(1) -> PLAYER; SEARCH_DECK(1) -> PLAYER {UNTIL=LIVE_END}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: UNKNOWN(58)(5) -> CARD_DECK_TOP; UNKNOWN(44)(1) -> PLAYER {{"filter": "TYPE=LIVE, GROUP=\u8679\u30f6\u54b2", "zone": "DISCARD"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 0, 4, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[58, 5, 0, 0, 262152, 230, 3, 0, 14680064, 48, 44, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-012-P - 鐘 嵐珠

### Japanese Ability
```text
{{jyouji.png|常時}}相手の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ライブの合計スコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"TARGET": "OPPONENT", "SUCCESS_PILE": true, "MIN": 6, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-012-R - 鐘 嵐珠

### Japanese Ability
```text
{{jyouji.png|常時}}相手の成功ライブカード置き場にあるカードのスコアの合計が６以上であるかぎり、ライブの合計スコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(220) {TYPE=SCORE, {"TARGET": "OPPONENT", "SUCCESS_PILE": true, "MIN": 6, "raw_cond": "SUM_SCORE", "comparison": "GE"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-013-N - 上原歩夢

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-014-N - 中須かすみ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp4-015-N - 桜坂しずく

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp4-016-N - 朝香果林

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-017-N - 宮下 愛

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-018-N - 近江彼方

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、このメンバーがアクティブ状態からウェイト状態になったとき、カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: UNKNOWN(305) {{"raw_cond": "MAIN_PHASE"}}, NONE {{"comparison": "EQ", "val": "SELF", "raw_cond": "TURN_PLAYER"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[305, 0, 0, 0, 48, 0, 0, 0, 0, 0, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-019-N - 優木せつ菜

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp4-020-N - エマ・ヴェルデ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-021-N - 天王寺璃奈

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室にあるカード1枚をデッキの一番上に置いてもよい。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_BLADES(1) -> PLAYER {FROM=DISCARD, TO=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[31, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-022-N - 三船栞子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp4-023-N - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}『虹ヶ咲」のメンバー1人をウェイトにしてもよい：カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 80, 0, 0, 53, 1, 0, 536870912, 4, 3, 2, 0, 0, 0, 10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-024-N - 鐘 嵐珠

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp4-025-L - VIVID WORLD

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[青ブレード]になる。
{{live_success.png|ライブ成功時}}エールにより公開された自分の『虹ヶ咲』のメンバーカードが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がある場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: PLAY_MEMBER_FROM_HAND(4) -> PLAYER {{"filter": "NOT_BLADE_TYPE_5", "duration": "UNTIL_LIVE_END", "destination": "5", "raw_val": "ALL", "source_color": 0}}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(209) {{"FILTER": "GROUP_ID=2, HAS_HEART_REQUIRED_ANY_COLOR", "val": "1", "raw_cond": "SELECT_YELL", "zone": "yell"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[39, 4, 1, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[209, 1, 80, 0, 49, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-026-L - DIVE!

### Japanese Ability
```text
{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。
{{jidou.png|自動}}このカードが表向きでライブカード置き場に置かれたとき、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
CONDITION: UNKNOWN(305) {{"raw_cond": "MAIN_PHASE"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "NAME='DIVE!", "type_live": true, "destination": "live_play", "raw_effect": "SELECT_HAND"}}; UNKNOWN(77)(1) -> PLAYER {{"next_turn": true}}

TRIGGER: NONE
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=2", "destination": "target"}}; SWAP_CARDS(2) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[305, 0, 0, 0, 48, 29, 1, 1, 0, 4, 77, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 81, 0, 262148, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-027-L - EMOTION

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード名が「EMOTION」のカード1枚につき、このカードのスコアを＋２し、成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}増やす。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: META_RULE(2) -> SELF {{"per_card": "SUCCESS_LIVE", "filter": "NAME=EMOTION", "value_enabled": true, "value_threshold": 1}}; UNKNOWN(61)(3) -> SELF {{"heart_type": 0}}
```

### Bytecode Sequences
- Ability 1: `[16, 2, 1, 268435456, 268491264, 61, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-028-L - stars we chase

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが4枚以上ある場合、このカードのスコアを＋１する。6枚以上ある場合、代わりにスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(205) {{"MIN": 4, "FILTER": "GROUP_ID=2, TYPE_LIVE, UNIQUE_NAMES", "raw_cond": "COUNT_DISCARD"}}
EFFECT: META_RULE(1) -> SELF; META_RULE(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[205, 4, 88, 0, 48, 16, 1, 0, 0, 4, 205, 6, 88, 0, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-029-L - Rise Up High!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}このゲームの1ターン目のライブフェイズの場合、このカードのスコアを＋１し、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: NONE {{"val": "1", "raw_cond": "IS_TURN"}}
EFFECT: META_RULE(1) -> SELF; SWAP_CARDS(1) -> MEMBER_SELECT {TARGET=MEMBER, {"filter": "GROUP_ID=2"}}
```

### Bytecode Sequences
- Ability 1: `[0, 1, 0, 0, 48, 16, 1, 0, 0, 4, 11, 1, 80, 0, 10, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-030-L - Daydream Mermaid

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。
・自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
・自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(218) {{"FILTER": "GROUP_ID=2", "raw_cond": "HAS_SUCCESS_LIVE"}}
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}} (Optional); SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}} (Optional)

TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"FILTER": "GROUP_ID=2", "raw_cond": "NOT_HAS_SUCCESS_LIVE"}}
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30a8\u30cd\u30eb\u30ae\u30fc", "\u30e1\u30f3\u30d0\u30fc"]}}
    Options:
      1: SET_SCORE(1)->PLAYER {{"wait": true}}
      2: SELECT_MODE(1)->CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[218, 0, 80, 0, 48, 23, 1, 0, 536870912, 134217732, 17, 1, 0, 551550976, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[0, 0, 80, 0, 48, 30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 23, 1, 0, 0, 134217732, 2, 3, 0, 0, 0, 17, 1, 0, 14680064, 458758, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-031-L - NEO SKY, NEO MAP!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージのエリアすべてに『虹ヶ咲』のメンバーがいて、かつそれらのコストの合計が20以上の場合、カードを3枚引き、自分の手札を3枚好きな順番でデッキの上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: NONE {{"raw_cond": "IS_OCCUPIED_ALL_AREAS"}}, UNKNOWN(209) {{"FILTER": "GROUP_ID=2", "raw_cond": "ALL_MEMBERS"}, ALL}, UNKNOWN(220) {TYPE=COST, {"MIN": 20, "raw_cond": "SUM_COST", "comparison": "GE"}}
EFFECT: MOVE_MEMBER(3) -> PLAYER; ACTIVATE_MEMBER(3) -> PLAYER {{"order": "CHOICE", "destination": "deck_top", "raw_effect": "SELECT_HAND"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 209, 4, 80, 0, 48, 220, 20, 0, 0, 48, 10, 3, 0, 0, 4, 29, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-bp4-032-L - Blue!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-bp4-032-L＋ - Blue!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-001-P＋ - 上原歩夢

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにこのメンバー以外のコスト11のメンバーがいる場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分のライブ中のライブカードが2枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(201) {{"FILTER": "NOT_SELF, COST_EQ_11", "raw_cond": "HAS_MEMBER"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: NONE {{"MIN": 2, "raw_cond": "COUNT_LIVE_PLAY"}}
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 201, 0, 0, 50331648, 48, 15, 1, 80, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-001-R - 上原歩夢

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにこのメンバー以外のコスト11のメンバーがいる場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分のライブ中のライブカードが2枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(201) {{"FILTER": "NOT_SELF, COST_EQ_11", "raw_cond": "HAS_MEMBER"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "source": "discard"}}

TRIGGER: CONSTANT
CONDITION: NONE {{"MIN": 2, "raw_cond": "COUNT_LIVE_PLAY"}}
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 201, 0, 0, 50331648, 48, 15, 1, 80, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-002-P＋ - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー2枚をこのメンバーの下に置いてもよい。
{{jyouji.png|常時}}このメンバーの下にエネルギーカードが2枚以上置かれているかぎり、ライブの合計スコアを＋１する。
(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(2) -> SELF (Optional)

TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 2, "raw_cond": "COUNT_CHARGED_ENERGY"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[23, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-002-R - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー2枚をこのメンバーの下に置いてもよい。
{{jyouji.png|常時}}このメンバーの下にエネルギーカードが2枚以上置かれているかぎり、ライブの合計スコアを＋１する。
(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(2) -> SELF (Optional)

TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 2, "raw_cond": "COUNT_CHARGED_ENERGY"}}
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[23, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-003-P＋ - 桜坂しずく

### Japanese Ability
```text
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{icon_blade.png|ブレード}}を得る。この能力は、このカードが手札にある場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: ENERGY(2), DISCARD_HAND(1)
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(1) -> PLAYER {TARGET=PLAYER, {"filter": "GROUP_ID=2", "destination": "target"}}; SWAP_CARDS(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 65, 1, 81, 0, 262148, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-003-R - 桜坂しずく

### Japanese Ability
```text
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{icon_blade.png|ブレード}}を得る。この能力は、このカードが手札にある場合のみ起動できる。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: ENERGY(2), DISCARD_HAND(1)
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(65)(1) -> PLAYER {TARGET=PLAYER, {"filter": "GROUP_ID=2", "destination": "target"}}; SWAP_CARDS(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 65, 1, 81, 0, 262148, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-004-P＋ - 朝香果林

### Japanese Ability
```text
{{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。公開したカードがコスト9以下のメンバーカードの場合、公開したカードを手札に加え、このメンバーはポジションチェンジする。それ以外の場合、公開したカードを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: NONE {{"raw_cond": "NO_SELF_POSITION_CHANGE_THIS_TURN"}}
EFFECT: SWAP_CARDS(2) -> SELF

TRIGGER: ON_LIVE_START
EFFECT: NEGATE_EFFECT(1) -> PLAYER {{"destination": "revealed"}}; UNKNOWN(44)(1) -> PLAYER {FROM=REVEALED}; PLACE_UNDER(1) -> PLAYER {{"raw_val": "SELF"}}; UNKNOWN(58)(1) -> PLAYER {FROM=REVEALED}
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[14, 1, 0, 0, 4, 0, 0, 0, 0, 48, 44, 1, 0, 0, 4, 20, 1, 1, 0, 65540, 0, 0, 0, 0, 48, 58, 1, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-004-R - 朝香果林

### Japanese Ability
```text
{{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。公開したカードがコスト9以下のメンバーカードの場合、公開したカードを手札に加え、このメンバーはポジションチェンジする。それ以外の場合、公開したカードを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: NONE {{"raw_cond": "NO_SELF_POSITION_CHANGE_THIS_TURN"}}
EFFECT: SWAP_CARDS(2) -> SELF

TRIGGER: ON_LIVE_START
EFFECT: NEGATE_EFFECT(1) -> PLAYER {{"destination": "revealed"}}; UNKNOWN(44)(1) -> PLAYER {FROM=REVEALED}; PLACE_UNDER(1) -> PLAYER {{"raw_val": "SELF"}}; UNKNOWN(58)(1) -> PLAYER {FROM=REVEALED}
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[14, 1, 0, 0, 4, 0, 0, 0, 0, 48, 44, 1, 0, 0, 4, 20, 1, 1, 0, 65540, 0, 0, 0, 0, 48, 58, 1, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-005-P＋ - 宮下 愛

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
(Once per turn)
CONDITION: UNKNOWN(209) {{"comparison": "EQ", "val": "COST=10", "raw_cond": "FILTER"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[209, 0, 0, 0, 0, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-005-R - 宮下 愛

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
(Once per turn)
CONDITION: UNKNOWN(209) {{"comparison": "EQ", "val": "COST=10", "raw_cond": "FILTER"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[209, 0, 0, 0, 0, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-006-P＋ - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: UNKNOWN(20)(1) {{"destination": "self"}}
EFFECT: UNKNOWN(81)(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-006-R - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: UNKNOWN(20)(1) {{"destination": "self"}}
EFFECT: UNKNOWN(81)(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-007-P＋ - 優木せつ菜

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のライブカードの必要ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がそれぞれ1以上含まれるかぎり、{{icon_all.png|ハート}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: NONE {{"COLORS": [0, 1, 2, 3, 4, 5], "raw_cond": "LIVE_HEART_REQUIRED_COLORS"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 6}}
```

### Bytecode Sequences
- Ability 1: `[12, 1, 6, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-007-R - 優木せつ菜

### Japanese Ability
```text
{{jyouji.png|常時}}自分のライブ中のライブカードの必要ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がそれぞれ1以上含まれるかぎり、{{icon_all.png|ハート}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: NONE {{"COLORS": [0, 1, 2, 3, 4, 5], "raw_cond": "LIVE_HEART_REQUIRED_COLORS"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 6}}
```

### Bytecode Sequences
- Ability 1: `[12, 1, 6, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-008-P＋ - エマ・ヴェルデ

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。
{{toujyou.png|登場}}自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "GROUP_ID=2, TAPPED", "raw_cond": "COUNT_STAGE"}}
EFFECT: ENERGY_CHARGE(2) -> SELF

TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["MEMBER", "ENERGY"]}}
    Options:
      1: UNK(1)->PLAYER
      2: UNK(2)->PLAYER
```

### Bytecode Sequences
- Ability 1: `[13, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 43, 1, 0, 0, 4, 2, 3, 0, 0, 0, 81, 2, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-008-R - エマ・ヴェルデ

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。
{{toujyou.png|登場}}自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "GROUP_ID=2, TAPPED", "raw_cond": "COUNT_STAGE"}}
EFFECT: ENERGY_CHARGE(2) -> SELF

TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["MEMBER", "ENERGY"]}}
    Options:
      1: UNK(1)->PLAYER
      2: UNK(2)->PLAYER
```

### Bytecode Sequences
- Ability 1: `[13, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 43, 1, 0, 0, 4, 2, 3, 0, 0, 0, 81, 2, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-009-P＋ - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}このターン、ブレードハートを持たないメンバーカードが自分のライブカード置き場から控え室に置かれている場合、カードを1枚引き、ライブ終了時まで、{{heart_03.png|heart03}}{{heart_05.png|heart05}}{{heart_06.png|heart06}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(205) {{"MIN": 1, "FILTER": "TYPE_MEMBER, NOT_HAS_BLADE_HEART", "FROM": "LIVE_AREA", "raw_cond": "COUNT_DISCARDED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER; SEARCH_DECK(3) -> PLAYER {{"heart_colors": "3,5,6"}}
```

### Bytecode Sequences
- Ability 1: `[205, 1, 4, 0, 48, 10, 1, 0, 0, 4, 12, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-009-R - 天王寺璃奈

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}このターン、ブレードハートを持たないメンバーカードが自分のライブカード置き場から控え室に置かれている場合、カードを1枚引き、ライブ終了時まで、{{heart_03.png|heart03}}{{heart_05.png|heart05}}{{heart_06.png|heart06}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(205) {{"MIN": 1, "FILTER": "TYPE_MEMBER, NOT_HAS_BLADE_HEART", "FROM": "LIVE_AREA", "raw_cond": "COUNT_DISCARDED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER; SEARCH_DECK(3) -> PLAYER {{"heart_colors": "3,5,6"}}
```

### Bytecode Sequences
- Ability 1: `[205, 1, 4, 0, 48, 10, 1, 0, 0, 4, 12, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-010-P＋ - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30a8\u30cd\u30eb\u30ae\u30fc", "\u30e9\u30a4\u30d6\u30ab\u30fc\u30c9"]}}
    Options:
      1: UNK(1)->PLAYER
      2: ORDER_DECK(0)->PLAYER {{"filter": "GROUP_ID=2", "destination": "deck_top", "source": "discard", "target_count": "2"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 81, 1, 0, 0, 4, 2, 3, 0, 0, 0, 15, 0, 81, 551550976, 458756, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-010-R - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}以下から1つを選ぶ。
・エネルギーを1枚アクティブにする。
・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30a8\u30cd\u30eb\u30ae\u30fc", "\u30e9\u30a4\u30d6\u30ab\u30fc\u30c9"]}}
    Options:
      1: UNK(1)->PLAYER
      2: ORDER_DECK(0)->PLAYER {{"filter": "GROUP_ID=2", "destination": "deck_top", "source": "discard", "target_count": "2"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 81, 1, 0, 0, 4, 2, 3, 0, 0, 0, 15, 0, 81, 551550976, 458756, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-011-P＋ - ミア・テイラー

### Japanese Ability
```text
{{jyouji.png|常時}}このメンバーの下にあるエネルギーカード1枚につき、{{icon_blade.png|ブレード}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: SWAP_CARDS(1) -> SELF {{"per_card": "UNDER_MEMBER", "value_enabled": true, "value_threshold": 1}}

TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 80, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-011-R - ミア・テイラー

### Japanese Ability
```text
{{jyouji.png|常時}}このメンバーの下にあるエネルギーカード1枚につき、{{icon_blade.png|ブレード}}を得る。
{{kidou.png|起動}}{{turn1.png|ターン1回}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: SWAP_CARDS(1) -> SELF {{"per_card": "UNDER_MEMBER", "value_enabled": true, "value_threshold": 1}}

TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 1, 268435456, 268487424, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 80, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-012-P＋ - 鐘 嵐珠

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにこのメンバー以外のコスト11のメンバーが登場したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『虹ヶ咲』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
(Once per turn)
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "FILTER": "COST=11", "raw_cond": "COUNT_STAGE"}}
EFFECT: UNKNOWN(81)(1) -> PLAYER {{"mode": "WAIT"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "zone": "YELL_REVEALED", "source": "discard"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[203, 1, 0, 0, 48, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[17, 1, 80, 536870912, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-012-R - 鐘 嵐珠

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにこのメンバー以外のコスト11のメンバーが登場したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『虹ヶ咲』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
(Once per turn)
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "FILTER": "COST=11", "raw_cond": "COUNT_STAGE"}}
EFFECT: UNKNOWN(81)(1) -> PLAYER {{"mode": "WAIT"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "GROUP_ID=2", "zone": "YELL_REVEALED", "source": "discard"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[203, 1, 0, 0, 48, 81, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[17, 1, 80, 536870912, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-013-P＋ - 上原歩夢

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「上原歩夢」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u4e0a\u539f\u6b69\u5922', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-013-R - 上原歩夢

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「上原歩夢」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u4e0a\u539f\u6b69\u5922', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-014-P＋ - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}「中須かすみ」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "NAME='\u4e2d\u9808\u304b\u3059\u307f", "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-014-R - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}「中須かすみ」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "NAME='\u4e2d\u9808\u304b\u3059\u307f", "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-015-P＋ - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「桜坂しずく」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u685c\u5742\u3057\u305a\u304f', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-015-R - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「桜坂しずく」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u685c\u5742\u3057\u305a\u304f', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-016-P＋ - 朝香果林

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「朝香果林」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u671d\u9999\u679c\u6797", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 3072, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-016-R - 朝香果林

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「朝香果林」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u671d\u9999\u679c\u6797", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 3072, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-017-P＋ - 宮下 愛

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「宮下愛」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u5bae\u4e0b\u611b', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-017-R - 宮下 愛

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「宮下愛」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u5bae\u4e0b\u611b', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-018-P＋ - 近江彼方

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「近江彼方」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u8fd1\u6c5f\u5f7c\u65b9", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 3328, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-018-R - 近江彼方

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「近江彼方」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u8fd1\u6c5f\u5f7c\u65b9", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 3328, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-019-P＋ - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}「優木せつ菜」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"NAME": "\u4f18\u6728\u96ea\u83dc", "raw_cond": "BATON_FROM_NAME"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-019-R - 優木せつ菜

### Japanese Ability
```text
{{toujyou.png|登場}}「優木せつ菜」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"NAME": "\u4f18\u6728\u96ea\u83dc", "raw_cond": "BATON_FROM_NAME"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-020-P＋ - エマ・ヴェルデ

### Japanese Ability
```text
{{toujyou.png|登場}}「エマ・ヴェルデ」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "NAME='\u30a8\u30de\u30fb\u30f4\u30a7\u30eb\u30c7", "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-020-R - エマ・ヴェルデ

### Japanese Ability
```text
{{toujyou.png|登場}}「エマ・ヴェルデ」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "NAME='\u30a8\u30de\u30fb\u30f4\u30a7\u30eb\u30c7", "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-021-P＋ - 天王寺璃奈

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「天王寺璃奈」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u5929\u738b\u5bfa\u7483\u5948", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 3712, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-021-R - 天王寺璃奈

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「天王寺璃奈」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u5929\u738b\u5bfa\u7483\u5948", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 3712, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-022-P＋ - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}「三船栞子」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"NAME": "\u4e09\u8239\u681e\u5b50", "raw_cond": "BATON_FROM_NAME"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 3840, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-022-R - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}「三船栞子」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"NAME": "\u4e09\u8239\u681e\u5b50", "raw_cond": "BATON_FROM_NAME"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 3840, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-023-P＋ - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「ミア・テイラー」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u30df\u30a2\u30fb\u30c6\u30a4\u30e9\u30fc', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-023-R - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「ミア・テイラー」のメンバーカードを1枚ステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME='\u30df\u30a2\u30fb\u30c6\u30a4\u30e9\u30fc', COST_LE_4", "zone": "HAND", "destination": "target"}}; UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 65, 1, -922746879, 12582912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-024-P＋ - 鐘 嵐珠

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「鐘嵐珠」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u9418\u5d50\u73e0", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 4096, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-024-R - 鐘 嵐珠

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「鐘嵐珠」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"filter": "NAME=\u9418\u5d50\u73e0", "destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[41, -2147483646, 0, 4096, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-025-N - 上原歩夢

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-026-N - 中須かすみ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-027-N - 桜坂しずく

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-028-N - 朝香果林

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを2枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, -2147483646, 0, 0, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-029-N - 宮下 愛

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-030-N - 近江彼方

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-031-N - 優木せつ菜

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-032-N - エマ・ヴェルデ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-033-N - 天王寺璃奈

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-034-N - 三船栞子

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_03.png|heart03}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"choices": [3, 4, 5], "destination": "choice"}}; ACTIVATE_MEMBER(99) -> SELF {TARGET=SELF, {"duration": "UNTIL_LIVE_END", "destination": "heart_type_choice", "raw_effect": "TRANSFORM_HEARTS", "raw_val": "ALL"}}
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 56, 4, 29, 99, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-035-N - ミア・テイラー

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを2枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(2) -> CARD_HAND {{"destination": "discard", "choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, -2147483646, 0, 0, 67334, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-036-N - 鐘 嵐珠

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_02.png|heart02}}か{{heart_06.png|heart06}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(45)(1) -> PLAYER {{"choices": [1, 2, 6], "destination": "choice"}}; ACTIVATE_MEMBER(99) -> SELF {TARGET=SELF, {"duration": "UNTIL_LIVE_END", "destination": "heart_type_choice", "raw_effect": "TRANSFORM_HEARTS", "raw_val": "ALL"}}
```

### Bytecode Sequences
- Ability 1: `[45, 1, 1, 70, 4, 29, 99, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-037-L - Cara Tesoro

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを＋１する。さらに、自分の『虹ヶ咲』のカードの効果によって自分のステージにいるウェイト状態のメンバーもアクティブにしていた場合、代わりにスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"FILTER": "GROUP_ID=2", "raw_cond": "DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT", "keyword": "DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT"}}
EFFECT: META_RULE(1) -> SELF; META_RULE(2) -> SELF {{"replace": true}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 80, 1073741824, 48, 16, 1, 0, 0, 4, 226, 0, 80, -2147483648, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-038-L - PHOENIX

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が4の『虹ヶ咲』のライブカードがある場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"FILTER": "Nijigasaki, PINK=4", "raw_cond": "SUCCESS_LIVES_CONTAINS", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-039-L - Stellar Stream

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が3の『虹ヶ咲』のライブカードがある場合、ライブ終了時まで、自分のステージにいる{{heart_06.png|heart06}}を持つ『虹ヶ咲』のメンバー1人は{{heart_06.png|heart06}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: NONE {{"FILTER": "GROUP_ID=2, HEARTS_PINK_EQ_3", "raw_cond": "SUCCESS_LIVES_OR_CURRENT_LIVE"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=2, HAS_HEART_PURPLE", "destination": "target"}}; SEARCH_DECK(5) -> PLAYER {{"heart_type": 6, "duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 80, 0, 48, 65, 1, 81, 0, 262148, 12, 5, 6, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-pb1-040-L - どこにいても君は君

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-041-L - PASTEL

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-041-L＋ - PASTEL

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-pb1-042-L - Eternalize Love!!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに同じ名前の『虹ヶ咲』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"MIN": 2, "SAME_NAME": true, "FILTER": "Nijigasaki", "raw_cond": "COUNT_STAGE"}}
EFFECT: UNKNOWN(48)(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[203, 2, 80, 0, 48, 48, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-001-SD - 上原歩夢

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『虹ヶ咲』のライブカードを1枚まで公開して手札に加えてもよい。残りを控え室に置く。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のステージにいるほかの『虹ヶ咲』のメンバーは{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "UNIT_NIJIGASAKI, TYPE_LIVE", "reveal": "True", "pick": "1", "dest_discard": "True", "choose_count": 1}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"filter": "UNIT_NIJIGASAKI, NOT_SELF", "destination": "targets", "raw_val": "ALL"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "targets"}}
```

### Bytecode Sequences
- Ability 1: `[41, -1073741819, 13041753, 0, 65540, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 1, 0, 536870912, 0, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 65, 99, 13041745, 50331648, 262148, 11, 1, 0, 0, 1, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-002-SD - 中須かすみ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-003-SD - 桜坂しずく

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-004-SD - 朝香果林

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-005-SD - 宮下 愛

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: DISCARD_HAND(2)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-006-SD - 近江彼方

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-007-SD - 優木せつ菜

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(2)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "UNIT_NIJIGASAKI", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 13041744, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-008-SD - エマ・ヴェルデ

### Japanese Ability
```text
{{toujyou.png|登場}}エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(81)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-009-SD - 天王寺璃奈

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-010-SD - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_04.png|heart04}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_START
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 4, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 12, 1, 4, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-011-SD - ミア・テイラー

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-012-SD - 鐘 嵐珠

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-013-SD - 上原歩夢

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-014-SD - 中須かすみ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-015-SD - 桜坂しずく

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-016-SD - 朝香果林

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-017-SD - 宮下 愛

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-018-SD - 近江彼方

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-019-SD - 優木せつ菜

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-020-SD - エマ・ヴェルデ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-021-SD - 天王寺璃奈

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-022-SD - 三船栞子

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-023-SD - ミア・テイラー

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-024-SD - 鐘 嵐珠

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!N-sd1-025-SD - Colorful Dreams! Colorful Smiles!

### Japanese Ability
```text
(エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
```

### Bytecode Sequences
- Ability 1: `[1, 0, 0, 0, 0]`

---

## PL!N-sd1-026-SD - 夢が僕らの太陽さ

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-027-SD - Just Believe!!!

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!N-sd1-028-SD - Dream with You

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(240) {{"MIN": 10, "AREA": "STAGE", "raw_cond": "TOTAL_BLADES"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[240, 10, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-013-PR - 高海千歌

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 536870912, 65542, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-014-PR - 桜内梨子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-PR-015-PR - 松浦果南

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-PR-016-PR - 黒澤ダイヤ

### Japanese Ability
```text
{{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-017-PR - 渡辺 曜

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-PR-018-PR - 津島善子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-PR-019-PR - 国木田花丸

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}} (Optional)

TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 536870912, 65542, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-020-PR - 小原鞠莉

### Japanese Ability
```text
{{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-021-PR - 黒澤ルビィ

### Japanese Ability
```text
{{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-022-PR - HAPPY PARTY TRAIN

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-PR-023-PR - 恋になりたいAQUARIUM

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-PR-024-PR - 勇気はどこに?君の胸に!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-PR-025-PR - 高海千歌

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-PR-026-PR - 桜内梨子

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-PR-027-PR - 松浦果南

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-PR-028-PR - 黒澤ダイヤ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`

---

## PL!S-PR-029-PR - 渡辺 曜

### Japanese Ability
```text
{{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "COST_GE_13", "AREA": "ANY_STAGE", "raw_cond": "COUNT_STAGE"}}
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-030-PR - 津島善子

### Japanese Ability
```text
{{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "COST_GE_13", "AREA": "ANY_STAGE", "raw_cond": "COUNT_STAGE"}}
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-031-PR - 国木田花丸

### Japanese Ability
```text
{{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"MIN": 1, "FILTER": "COST_GE_13", "AREA": "ANY_STAGE", "raw_cond": "COUNT_STAGE"}}
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-PR-032-PR - 小原鞠莉

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`

---

## PL!S-PR-033-PR - 黒澤ルビィ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: CHEER_REVEAL(3) -> PLAYER {{"destination": "deck_top"}} (Optional); UNKNOWN(58)(1) -> PLAYER {{"raw_val": "REMAINDER"}}
```

### Bytecode Sequences
- Ability 1: `[14, 3, 0, 0, 0, 28, 3, 0, 0, 0, 58, 1, 1, 0, 262148, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-001-P - 高海千歌

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(218) {TARGET=SELF, {"val": "= 0", "comparison": "EQ", "raw_cond": "COUNT_SUCCESS_LIVE"}}, UNKNOWN(218) {TARGET=OPPONENT, {"val": "1", "comparison": "GE", "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-001-R - 高海千歌

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(218) {TARGET=SELF, {"val": "= 0", "comparison": "EQ", "raw_cond": "COUNT_SUCCESS_LIVE"}}, UNKNOWN(218) {TARGET=OPPONENT, {"val": "1", "comparison": "GE", "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-002-P - 桜内梨子

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『Aqours』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=1", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 15, 1, 48, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-002-R - 桜内梨子

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『Aqours』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=1", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 15, 1, 48, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-003-P - 松浦果南

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、ライブ終了時まで、［緑ハート］を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 3, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 12, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-003-R - 松浦果南

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、ライブ終了時まで、［緑ハート］を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 3, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 12, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-004-P - 黒澤ダイヤ

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"rule": 10}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-004-R - 黒澤ダイヤ

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"rule": 10}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-005-P - 渡辺 曜

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを7枚見る。その中から{{heart_02.png|heart02}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}を持つメンバーカードを3枚まで公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(7) -> CARD_HAND {TARGET=HAND, {"color_filter": "RED/GREEN/BLUE", "type_member": true, "source": "DECK", "remainder": "DISCARD", "choose_count": "3"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 7, 0, 536870912, 67334, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-005-P＋ - 渡辺 曜

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを7枚見る。その中から{{heart_02.png|heart02}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}を持つメンバーカードを3枚まで公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(7) -> CARD_HAND {TARGET=HAND, {"color_filter": "RED/GREEN/BLUE", "type_member": true, "source": "DECK", "remainder": "DISCARD", "choose_count": "3"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 7, 0, 536870912, 67334, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-005-R＋ - 渡辺 曜

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを7枚見る。その中から{{heart_02.png|heart02}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}を持つメンバーカードを3枚まで公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(7) -> CARD_HAND {TARGET=HAND, {"color_filter": "RED/GREEN/BLUE", "type_member": true, "source": "DECK", "remainder": "DISCARD", "choose_count": "3"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 7, 0, 536870912, 67334, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-005-SEC - 渡辺 曜

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを7枚見る。その中から{{heart_02.png|heart02}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}を持つメンバーカードを3枚まで公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(7) -> CARD_HAND {TARGET=HAND, {"color_filter": "RED/GREEN/BLUE", "type_member": true, "source": "DECK", "remainder": "DISCARD", "choose_count": "3"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 7, 0, 536870912, 67334, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-006-P - 津島善子

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から、コストの合計が4以下になるようにメンバーカードを2枚までステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(63)(2) -> PLAYER {{"total_cost_le": 4}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 4, 0, 536870912, 0, 3, 1, 0, 0, 0, 63, 2, -922746879, 536870912, 458756, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-006-R - 津島善子

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から、コストの合計が4以下になるようにメンバーカードを2枚までステージに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(63)(2) -> PLAYER {{"total_cost_le": 4}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 4, 0, 536870912, 0, 3, 1, 0, 0, 0, 63, 2, -922746879, 536870912, 458756, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-007-P - 国木田花丸

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。
{{live_start.png|ライブ開始時}}手札のライブカードを1枚公開し、デッキの一番下に置いてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}, NONE {{"LE": 7, "val": "PLAYER", "raw_cond": "HAND_COUNT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 0, 7, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[74, 1, 8, 536870912, 393222, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-007-P＋ - 国木田花丸

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。
{{live_start.png|ライブ開始時}}手札のライブカードを1枚公開し、デッキの一番下に置いてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}, NONE {{"LE": 7, "val": "PLAYER", "raw_cond": "HAND_COUNT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 0, 7, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[74, 1, 8, 536870912, 393222, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-007-R＋ - 国木田花丸

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。
{{live_start.png|ライブ開始時}}手札のライブカードを1枚公開し、デッキの一番下に置いてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}, NONE {{"LE": 7, "val": "PLAYER", "raw_cond": "HAND_COUNT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 0, 7, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[74, 1, 8, 536870912, 393222, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-007-SEC - 国木田花丸

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。
{{live_start.png|ライブ開始時}}手札のライブカードを1枚公開し、デッキの一番下に置いてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}, NONE {{"LE": 7, "val": "PLAYER", "raw_cond": "HAND_COUNT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(125)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 0, 7, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[74, 1, 8, 536870912, 393222, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-008-P - 小原鞠莉

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。
{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを＋１する。ライブカードが3枚以上ある場合、代わりに合計スコアを＋２する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=DISCARD, {"type_live": true, "destination": "target"}} (Optional); SET_BLADES(0) -> PLAYER {TO=DECK_BOTTOM}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_AQOURS, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "live_count", "raw_effect": "COUNT_CARDS", "zone": "YELL_REVEALED", "filter": "TYPE_LIVE"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1, 536870912, 458756, 31, 0, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 3, 13041664, 0, 48, 29, 0, 9, 0, 4, 0, 1, 0, 0, 48, 0, 3, 0, 0, 48, 312, 0, 0, 0, 48, 0, 2, 0, 0, 48, 0, 0, 0, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-008-P＋ - 小原鞠莉

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。
{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを＋１する。ライブカードが3枚以上ある場合、代わりに合計スコアを＋２する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=DISCARD, {"type_live": true, "destination": "target"}} (Optional); SET_BLADES(0) -> PLAYER {TO=DECK_BOTTOM}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_AQOURS, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "live_count", "raw_effect": "COUNT_CARDS", "zone": "YELL_REVEALED", "filter": "TYPE_LIVE"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1, 536870912, 458756, 31, 0, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 3, 13041664, 0, 48, 29, 0, 9, 0, 4, 0, 1, 0, 0, 48, 0, 3, 0, 0, 48, 312, 0, 0, 0, 48, 0, 2, 0, 0, 48, 0, 0, 0, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-008-R＋ - 小原鞠莉

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。
{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを＋１する。ライブカードが3枚以上ある場合、代わりに合計スコアを＋２する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=DISCARD, {"type_live": true, "destination": "target"}} (Optional); SET_BLADES(0) -> PLAYER {TO=DECK_BOTTOM}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_AQOURS, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "live_count", "raw_effect": "COUNT_CARDS", "zone": "YELL_REVEALED", "filter": "TYPE_LIVE"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1, 536870912, 458756, 31, 0, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 3, 13041664, 0, 48, 29, 0, 9, 0, 4, 0, 1, 0, 0, 48, 0, 3, 0, 0, 48, 312, 0, 0, 0, 48, 0, 2, 0, 0, 48, 0, 0, 0, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-008-SEC - 小原鞠莉

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。
{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを＋１する。ライブカードが3枚以上ある場合、代わりに合計スコアを＋２する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=DISCARD, {"type_live": true, "destination": "target"}} (Optional); SET_BLADES(0) -> PLAYER {TO=DECK_BOTTOM}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_AQOURS, UNIQUE_NAMES", "EQ": 3, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "live_count", "raw_effect": "COUNT_CARDS", "zone": "YELL_REVEALED", "filter": "TYPE_LIVE"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1, 536870912, 458756, 31, 0, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 3, 13041664, 0, 48, 29, 0, 9, 0, 4, 0, 1, 0, 0, 48, 0, 3, 0, 0, 48, 312, 0, 0, 0, 48, 0, 2, 0, 0, 48, 0, 0, 0, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-009-P - 黒澤ルビィ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-009-R - 黒澤ルビィ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-010-N - 高海千歌

### Japanese Ability
```text
{{toujyou.png|登場}}カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-011-N - 桜内梨子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-012-N - 松浦果南

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-013-N - 黒澤ダイヤ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-014-N - 渡辺 曜

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-015-N - 津島善子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-016-N - 国木田花丸

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-017-N - 小原鞠莉

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-018-N - 黒澤ルビィ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-019-L - WATER BLUE NEW WORLD

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=1", "destination": "choice_target"}}; META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[65, 1, 49, 0, 262148, 224, 6, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-020-L - DREAMY COLOR

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp2-021-L - 未体験HORIZON

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
EFFECT: SET_BLADES(1) -> PLAYER {TO=DECK_BOTTOM, {"zone": "YELL_REVEALED", "type_live": true}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[31, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-022-L - 未熟DREAMER

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(227) {{"raw_cond": "DECK_REFRESHED_THIS_TURN"}}
EFFECT: META_RULE(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[227, 0, 0, 0, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-023-L - MY舞☆TONIGHT

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のライブカード置き場に「MY舞☆TONIGHT」以外の『Aqours』のライブカードがある場合、ライブ終了時まで、自分のステージのメンバーは{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(230) {{"FILTER": "UNIT_AQOURS, NOT_NAME='MY\u821e\u2606TONIGHT", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_LIVE_ZONE"}}
EFFECT: UNKNOWN(65)(99) -> PLAYER {{"destination": "targets", "raw_val": "ALL"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "targets"}}
```

### Bytecode Sequences
- Ability 1: `[230, 0, 13041664, 0, 48, 65, 99, 1, 0, 262148, 11, 1, 0, 0, 1, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-024-L - 君のこころは輝いてるかい？

### Japanese Ability
```text
{{jyouji.png|常時}}このカードは成功ライブカード置き場に置くことができない。
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: UNKNOWN(80)(1) -> SELF

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[80, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-025-L - 青空Jumping Heart

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"MIN": 2, "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}}; SWAP_CARDS(2) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[218, 2, 0, 0, 48, 65, 1, 1, 0, 262148, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp2-026-L - ユメ語るよりユメ歌おう

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp3-001-P - 高海千歌

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "TARGET"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 65, 1, 0, 0, 0, 53, 0, 0, 0, 4, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-001-P＋ - 高海千歌

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "TARGET"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 65, 1, 0, 0, 0, 53, 0, 0, 0, 4, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-001-R＋ - 高海千歌

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "TARGET"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 65, 1, 0, 0, 0, 53, 0, 0, 0, 4, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-001-SEC - 高海千歌

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(60)(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "raw_val": "TARGET"}}

TRIGGER: CONSTANT
EFFECT: META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 65, 1, 0, 0, 0, 53, 0, 0, 0, 4, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-002-P - 桜内梨子

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、このカードを手札に加えてもよい。この能力は、このカードが自分のエールによって公開されている場合のみ発動する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"val": "\"YELL_REVEALED\"", "raw_cond": "ZONE_EQ"}}, NONE {{"val": "SCORE(OPPONENT)", "comparison": "GT", "raw_cond": "SCORE"}}
EFFECT: UNKNOWN(44)(1) -> PLAYER {{"raw_val": "SELF"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 0, 0, 0, 0, 16, 44, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-002-R - 桜内梨子

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、このカードを手札に加えてもよい。この能力は、このカードが自分のエールによって公開されている場合のみ発動する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"val": "\"YELL_REVEALED\"", "raw_cond": "ZONE_EQ"}}, NONE {{"val": "SCORE(OPPONENT)", "comparison": "GT", "raw_cond": "SCORE"}}
EFFECT: UNKNOWN(44)(1) -> PLAYER {{"raw_val": "SELF"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 0, 0, 0, 0, 16, 44, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-003-P - 松浦果南

### Japanese Ability
```text
{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。
{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いたカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {{"FILTER": "TYPE_LIVE"}}
EFFECT: MOVE_MEMBER(3) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0)
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}} (Optional); SWAP_CARDS(2) -> PLAYER {{"per_card": "DISCARD_REMOVED", "duration": "UNTIL_LIVE_END", "destination": "target", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[10, 3, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 1, 536870912, 262148, 11, 2, 1, 268435456, 268487425, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-003-P＋ - 松浦果南

### Japanese Ability
```text
"{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。
{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いたカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {{"FILTER": "TYPE_LIVE"}}
EFFECT: MOVE_MEMBER(3) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0)
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}} (Optional); SWAP_CARDS(2) -> PLAYER {{"per_card": "DISCARD_REMOVED", "duration": "UNTIL_LIVE_END", "destination": "target", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[10, 3, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 1, 536870912, 262148, 11, 2, 1, 268435456, 268487425, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-003-R＋ - 松浦果南

### Japanese Ability
```text
{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。
{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いたカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {{"FILTER": "TYPE_LIVE"}}
EFFECT: MOVE_MEMBER(3) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0)
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}} (Optional); SWAP_CARDS(2) -> PLAYER {{"per_card": "DISCARD_REMOVED", "duration": "UNTIL_LIVE_END", "destination": "target", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[10, 3, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 1, 536870912, 262148, 11, 2, 1, 268435456, 268487425, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-003-SEC - 松浦果南

### Japanese Ability
```text
"{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。
{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いたカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) {{"FILTER": "TYPE_LIVE"}}
EFFECT: MOVE_MEMBER(3) -> PLAYER (Optional)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0)
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}} (Optional); SWAP_CARDS(2) -> PLAYER {{"per_card": "DISCARD_REMOVED", "duration": "UNTIL_LIVE_END", "destination": "target", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[10, 3, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[65, 1, 1, 536870912, 262148, 11, 2, 1, 268435456, 268487425, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-004-P - 黒澤ダイヤ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 4, 5, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-004-R - 黒澤ダイヤ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 4, 5, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-005-P - 渡辺 曜

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの枚数が、相手がエールによって公開したカードの枚数より少ない場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"LESS_THAN": "OPPONENT", "raw_cond": "REDUCE_YELL_COUNT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-005-R - 渡辺 曜

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの枚数が、相手がエールによって公開したカードの枚数より少ない場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"LESS_THAN": "OPPONENT", "raw_cond": "REDUCE_YELL_COUNT"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-006-P - 津島善子

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, GROUP_ID=1", "destination": "target_stage"}}; UNKNOWN(58)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET_STAGE"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "base_cost", "raw_effect": "GET_COST", "raw_val": "TARGET_STAGE"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=1, COST_EQ=BASE_COST+2", "destination": "target_discard", "source": "discard"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"slot": "SAME_SLOT", "raw_effect": "PLAY_STAGE_SPECIFIC_SLOT", "raw_val": "TARGET_DISCARD"}}
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 51, 0, 0, 0, 4, 58, 1, 0, 0, 6, 65, 1, 49, 50331648, 262148, 58, 1, 1, 0, 262148, 29, 1, 0, 0, 4, 312, 0, 0, 0, 48, 17, 1, -2063597519, 367001600, 458756, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-006-P＋ - 津島善子

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, GROUP_ID=1", "destination": "target_stage"}}; UNKNOWN(58)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET_STAGE"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "base_cost", "raw_effect": "GET_COST", "raw_val": "TARGET_STAGE"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=1, COST_EQ=BASE_COST+2", "destination": "target_discard", "source": "discard"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"slot": "SAME_SLOT", "raw_effect": "PLAY_STAGE_SPECIFIC_SLOT", "raw_val": "TARGET_DISCARD"}}
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 51, 0, 0, 0, 4, 58, 1, 0, 0, 6, 65, 1, 49, 50331648, 262148, 58, 1, 1, 0, 262148, 29, 1, 0, 0, 4, 312, 0, 0, 0, 48, 17, 1, -2063597519, 367001600, 458756, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-006-R＋ - 津島善子

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, GROUP_ID=1", "destination": "target_stage"}}; UNKNOWN(58)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET_STAGE"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "base_cost", "raw_effect": "GET_COST", "raw_val": "TARGET_STAGE"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=1, COST_EQ=BASE_COST+2", "destination": "target_discard", "source": "discard"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"slot": "SAME_SLOT", "raw_effect": "PLAY_STAGE_SPECIFIC_SLOT", "raw_val": "TARGET_DISCARD"}}
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 51, 0, 0, 0, 4, 58, 1, 0, 0, 6, 65, 1, 49, 50331648, 262148, 58, 1, 1, 0, 262148, 29, 1, 0, 0, 4, 312, 0, 0, 0, 48, 17, 1, -2063597519, 367001600, 458756, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-006-SEC - 津島善子

### Japanese Ability
```text
{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる。（この能力はセンターエリアに登場している場合のみ起動できる。）
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NOT_SELF, GROUP_ID=1", "destination": "target_stage"}}; UNKNOWN(58)(1) -> PLAYER {{"destination": "success", "raw_val": "TARGET_STAGE"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "base_cost", "raw_effect": "GET_COST", "raw_val": "TARGET_STAGE"}}; SELECT_MODE(1) -> PLAYER {{"filter": "GROUP_ID=1, COST_EQ=BASE_COST+2", "destination": "target_discard", "source": "discard"}}; ACTIVATE_MEMBER(1) -> PLAYER {{"slot": "SAME_SLOT", "raw_effect": "PLAY_STAGE_SPECIFIC_SLOT", "raw_val": "TARGET_DISCARD"}}
```

### Bytecode Sequences
- Ability 1: `[206, 0, 0, 0, 48, 51, 0, 0, 0, 4, 58, 1, 0, 0, 6, 65, 1, 49, 50331648, 262148, 58, 1, 1, 0, 262148, 29, 1, 0, 0, 4, 312, 0, 0, 0, 48, 17, 1, -2063597519, 367001600, 458756, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-007-P - 国木田花丸

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く。そうした場合、自分はカードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: UNKNOWN(67)(1) -> PLAYER {{"destination": "target_player"}}; ORDER_DECK(1) -> PLAYER {{"destination": "deck_bottom", "source": "discard", "player": "TARGET_PLAYER"}}; MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[67, 1, 0, 0, 4, 15, 1, 1, 14680064, 458756, 312, 0, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-007-R - 国木田花丸

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分か相手を選ぶ。自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く。そうした場合、自分はカードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: UNKNOWN(67)(1) -> PLAYER {{"destination": "target_player"}}; ORDER_DECK(1) -> PLAYER {{"destination": "deck_bottom", "source": "discard", "player": "TARGET_PLAYER"}}; MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[67, 1, 0, 0, 4, 15, 1, 1, 14680064, 458756, 312, 0, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-008-P - 小原鞠莉

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。それがスコア6以上の『Aqours』のライブカードの場合、エネルギーを4枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}; UNKNOWN(81)(4) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 0, 0, 48, 0, 48, 81, 4, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-008-R - 小原鞠莉

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。それがスコア6以上の『Aqours』のライブカードの場合、エネルギーを4枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}; UNKNOWN(81)(4) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 0, 0, 48, 0, 48, 81, 4, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-009-P - 黒澤ルビィ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを6枚見る。その中から『Aqours』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(6) -> PLAYER {{"filter": "GROUP_ID=1, TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 6, 53, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-009-R - 黒澤ルビィ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを6枚見る。その中から『Aqours』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(6) -> PLAYER {{"filter": "GROUP_ID=1, TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 6, 53, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-010-N - 高海千歌

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーを1人までアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "STATUS=TAPPED", "destination": "target"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 1, 536870912, 262148, 43, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-011-N - 桜内梨子

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーを1人までアクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "STATUS=TAPPED", "destination": "target"}} (Optional); UNKNOWN(43)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 1, 536870912, 262148, 43, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-012-N - 松浦果南

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-013-N - 黒澤ダイヤ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp3-014-N - 渡辺 曜

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp3-015-N - 津島善子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp3-016-N - 国木田花丸

### Japanese Ability
```text
{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、ステージにいるこのメンバーのコストを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: UNKNOWN(70)(1) -> SELF {{"per_card": "SUCCESS_LIVE", "value_enabled": true, "value_threshold": 1}}
```

### Bytecode Sequences
- Ability 1: `[70, 1, 1, 268435456, 268491264, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-017-N - 小原鞠莉

### Japanese Ability
```text
{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}

TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, COST_LE_4", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[51, 0, 0, 536870912, 4, 3, 2, 0, 0, 0, 65, 1, -922746878, 0, 262148, 53, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-018-N - 黒澤ルビィ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp3-019-L - MIRACLE WAVE

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、このカードのスコアは４になる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"raw_cond": "OR", "clauses": [{"type": 0, "value": 0, "attr": 0, "is_negated": false, "params": {"FILTER": "TYPE_NOT=BLADE_HEART", "MAX": 0, "raw_cond": "YELL_PILE_CONTAINS"}}, {"type": 0, "value": 0, "attr": 0, "is_negated": false, "params": {"MIN": 2, "raw_cond": "SURPLUS_HEARTS_COUNT"}}]}}
EFFECT: COLOR_SELECT(4) -> SELF
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 37, 4, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-020-L - ダイスキだったらダイジョウブ！

### Japanese Ability
```text
{{jidou.png|自動}}［ターン1回］エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい。そのエールで得たブレードハートを失い、もう一度エールを行う。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
(Once per turn)
CONDITION: NONE {{"FILTER": "TYPE=BLADE_HEART", "MAX": 2, "raw_cond": "YELL_PILE_CONTAINS"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "DISCARD_YELL_PILE"}} (Optional); ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "RE_YELL"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 29, 1, 0, 536870912, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-021-L - 想いよひとつになれ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の控え室にあるメンバーカード1枚をデッキの一番上に置いてもよい。そうした場合、ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"destination": "target"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 0, 536870912, 458759, 31, 1, 0, 0, 5243136, 3, 3, 0, 0, 0, 312, 0, 0, 0, 48, 65, 1, 1, 0, 262148, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-022-L - Fantastic Departure!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp3-023-L - KOKORO Magic “A to Z”

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-bp3-024-L - Deep Resonance

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージのセンターエリアにコスト9以上の『Aqours』のメンバーがいる場合、以下から1つを選ぶ。
・ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(201) {{"FILTER": "GROUP_ID=1, COST_GE=9", "AREA": "CENTER", "raw_cond": "HAS_MEMBER"}}
EFFECT: ADD_TO_HAND(1) -> PLAYER {{"options": ["\u30d6\u30ec\u30fc\u30c9", "WAIT"]}}
    Options:
      1: UNK(1)->PLAYER {{"destination": "target"}}, SWAP_CARDS(2)->PLAYER {{"destination": "target"}}
      2: SET_HEARTS(1)->PLAYER {{"filter": "COST_LE_4"}}
```

### Bytecode Sequences
- Ability 1: `[201, 0, -1828716496, 0, 1073741872, 30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 3, 0, 0, 0, 65, 1, 1, 0, 262148, 11, 2, 0, 0, 4, 2, 3, 0, 0, 0, 32, 1, -922746879, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!S-bp3-025-L - SUKI for you, DREAM for you!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバー1人を選ぶ。そのメンバーが持つ{{icon_blade.png|ブレード}}が6つ以上の場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=1"}}; META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[65, 1, 49, 0, 262148, 224, 6, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-001-P＋ - 高海千歌

### Japanese Ability
```text
{{toujyou.png|登場}}相手の手札の枚数が自分より2枚以上多い場合、自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(312) {{"GE": 2, "val": "HAND_COUNT(OPPONENT", "raw_cond": "SUM_VALUE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[312, 2, 0, 0, 48, 15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-001-R - 高海千歌

### Japanese Ability
```text
{{toujyou.png|登場}}相手の手札の枚数が自分より2枚以上多い場合、自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(312) {{"GE": 2, "val": "HAND_COUNT(OPPONENT", "raw_cond": "SUM_VALUE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[312, 2, 0, 0, 48, 15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-002-P＋ - 桜内梨子

### Japanese Ability
```text
{{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> OPPONENT {{"options": ["{{discard.png", "{{grant_ability.png"]}}
    Options:
      1: UNK(1)->SELF {{"FILTER": "TYPE_LIVE", "destination": "opponent"}}
      2: UNK(1)->PLAYER {{"ability": "TRIGGER: CONSTANT,  BOOST_SCORE(1) -> PLAYER", "duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 16777216, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 58, 1, 8, 0, 6, 2, 3, 0, 0, 0, 60, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-002-R - 桜内梨子

### Japanese Ability
```text
{{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ADD_TO_HAND(1) -> OPPONENT {{"options": ["{{discard.png", "{{grant_ability.png"]}}
    Options:
      1: UNK(1)->SELF {{"FILTER": "TYPE_LIVE", "destination": "opponent"}}
      2: UNK(1)->PLAYER {{"ability": "TRIGGER: CONSTANT,  BOOST_SCORE(1) -> PLAYER", "duration": "UNTIL_LIVE_END", "raw_val": "SELF"}}
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 16777216, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 58, 1, 8, 0, 6, 2, 3, 0, 0, 0, 60, 1, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-003-P＋ - 松浦果南

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、このメンバーが元々持つハートはすべて{{heart_04.png|heart04}}になる。{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(73)(0) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "color_green", "filter": "BASE"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"zone": "YELL_REVEALED", "source": "discard"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 73, 0, 1, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 0, 536870912, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-003-R - 松浦果南

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、このメンバーが元々持つハートはすべて{{heart_04.png|heart04}}になる。{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(73)(0) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "color_green", "filter": "BASE"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"zone": "YELL_REVEALED", "source": "discard"}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 73, 0, 1, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[15, 1, 0, 536870912, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-004-P＋ - 黒澤ダイヤ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-004-R - 黒澤ダイヤ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-005-P＋ - 渡辺 曜

### Japanese Ability
```text
{{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"val": "ENERGY_COUNT(OPPONENT)", "comparison": "LT", "raw_cond": "ENERGY_COUNT"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-005-R - 渡辺 曜

### Japanese Ability
```text
{{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"val": "ENERGY_COUNT(OPPONENT)", "comparison": "LT", "raw_cond": "ENERGY_COUNT"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-006-P＋ - 津島善子

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ADD_TO_HAND(1) -> OPPONENT {{"options": ["{{discard.png", "{{no_action.png"]}}
    Options:
      1: UNK(1)->SELF {{"destination": "opponent"}}
      2: SWAP_CARDS(4)->SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 8, 0, 393222, 30, 2, 0, 0, 16777216, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 58, 1, 0, 0, 6, 2, 3, 0, 0, 0, 11, 4, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-006-R - 津島善子

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ADD_TO_HAND(1) -> OPPONENT {{"options": ["{{discard.png", "{{no_action.png"]}}
    Options:
      1: UNK(1)->SELF {{"destination": "opponent"}}
      2: SWAP_CARDS(4)->SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 8, 0, 393222, 30, 2, 0, 0, 16777216, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 58, 1, 0, 0, 6, 2, 3, 0, 0, 0, 11, 4, 0, 0, 4, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-007-P＋ - 国木田花丸

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: SET_SCORE(1) -> PLAYER {{"status": "TAPPED"}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-007-R - 国木田花丸

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(226) {{"FILTER": "TYPE_LIVE", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: SET_SCORE(1) -> PLAYER {{"status": "TAPPED"}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-008-P＋ - 小原鞠莉

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "target_player", "raw_effect": "CHOICE_PLAYER", "raw_val": "BOTH"}}; UNKNOWN(125)(2) -> PLAYER {TARGET=TARGET_PLAYER}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-008-R - 小原鞠莉

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "target_player", "raw_effect": "CHOICE_PLAYER", "raw_val": "BOTH"}}; UNKNOWN(125)(2) -> PLAYER {TARGET=TARGET_PLAYER}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 125, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-009-P＋ - 黒澤ルビィ

### Japanese Ability
```text
{{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(312) {{"GE": 3, "val": "COUNT_SUCCESS_LIVE(PLAYER", "raw_cond": "SUM_VALUE"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-009-R - 黒澤ルビィ

### Japanese Ability
```text
{{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(312) {{"GE": 3, "val": "COUNT_SUCCESS_LIVE(PLAYER", "raw_cond": "SUM_VALUE"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-010-N - 高海千歌

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-pb1-011-N - 桜内梨子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-pb1-012-N - 松浦果南

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-pb1-013-N - 黒澤ダイヤ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_04.png|heart04}}を2個以上持つメンバーカードか、必要ハートに{{heart_04.png|heart04}}を2以上含むライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "(TYPE_MEMBER, HEART_TYPE=3, HEART_COUNT_GE=2) OR (TYPE_LIVE, HEART_TYPE=3, HEARTS_REQUIRED_GE=2)", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 4, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-014-N - 渡辺 曜

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_02.png|heart02}}を2個以上持つメンバーカードか、必要ハートに{{heart_02.png|heart02}}を2以上含むライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "(TYPE_MEMBER, HEART_TYPE=1, HEART_COUNT_GE=2) OR (TYPE_LIVE, HEART_TYPE=1, HEARTS_REQUIRED_GE=2)", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 4, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-015-N - 津島善子

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_05.png|heart05}}を2個以上持つメンバーカードか、必要ハートに{{heart_05.png|heart05}}を2以上含むライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "(TYPE_MEMBER, HEART_TYPE=4, HEART_COUNT_GE=2) OR (TYPE_LIVE, HEART_TYPE=4, HEARTS_REQUIRED_GE=2)", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 4, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-016-N - 国木田花丸

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-017-N - 小原鞠莉

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-018-N - 黒澤ルビィ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-019-L - 元気全開DAY！DAY！DAY！

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(223) {{"FILTER": "GROUP_ID=1, HEART_TYPE=1", "MIN": 6, "raw_cond": "SUM_HEARTS"}}
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"raw_effect": "NEGATE_SELF_TRIGGER", "duration": "UNTIL_LIVE_END"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: SET_SCORE(1) -> OPPONENT {{"status": "TAPPED"}}
```

### Bytecode Sequences
- Ability 1: `[223, 6, 48, 0, 48, 29, 0, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[23, 1, 0, 0, 2, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-020-L - トリコリコPLEASE!!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_04.png|heart04}}が合計10個以上ある場合、このカードのスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(223) {{"FILTER": "GROUP_ID=1, HEART_TYPE=3", "MIN": 10, "raw_cond": "SUM_HEARTS"}}
EFFECT: META_RULE(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[223, 10, 48, 0, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-021-L - Strawberry Trapper

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手が余剰のハートを持たずにライブを成功させていた場合、このカードのスコアを＋２する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(223) {{"FILTER": "GROUP_ID=1, HEART_TYPE=5", "MIN": 4, "raw_cond": "SUM_HEARTS"}}, NONE {{"EQ": 0, "val": "OPPONENT", "raw_cond": "SURPLUS_HEARTS_COUNT"}}
EFFECT: META_RULE(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[223, 4, 48, 0, 48, 0, 0, 0, 0, 48, 16, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-022-L - 逃走迷走メビウスループ

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き場にカードを置くことができない。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, {"raw_cond": "SCORE_EQUAL_OPPONENT", "comparison": "EQ"}}
EFFECT: UNKNOWN(80)(1) -> PLAYER {TARGET=BOTH}
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 0, 80, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-022-L＋ - 逃走迷走メビウスループ

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き場にカードを置くことができない。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, {"raw_cond": "SCORE_EQUAL_OPPONENT", "comparison": "EQ"}}
EFFECT: UNKNOWN(80)(1) -> PLAYER {TARGET=BOTH}
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 0, 80, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!S-pb1-023-L - Next SPARKLING!!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-pb1-023-L＋ - Next SPARKLING!!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!S-pb1-024-L - 僕らの走ってきた道は・・・

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を2枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-003-PR - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーが7枚以上ある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 7, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[213, 7, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-004-PR - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-005-PR - 嵐 千砂都

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-PR-006-PR - 平安名すみれ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-007-PR - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーが7枚以上ある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 7, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[213, 7, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-008-PR - 桜小路きな子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-PR-009-PR - 米女メイ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これによりライブカードを控え室に置いた場合、さらにカードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0) {{"destination": "discarded"}}
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 0, 0, 4, 209, 1, 8, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-010-PR - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーが7枚以上ある場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 7, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[213, 7, 0, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-011-PR - 鬼塚夏美

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これによりライブカードを控え室に置いた場合、さらにカードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0) {{"destination": "discarded"}}
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 0, 0, 4, 209, 1, 8, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-012-PR - ウィーン・マルガレーテ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。これによりライブカードを控え室に置いた場合、さらにカードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(0) {{"destination": "discarded"}}
EFFECT: SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 1, 0, 0, 4, 209, 1, 8, 0, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-PR-013-PR - 鬼塚冬毬

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-001-P - 澁谷かのん

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにほかのメンバーがいない場合、自分はライブできない。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"MAX": 0, "TARGET": "OTHER_MEMBER", "raw_cond": "COUNT_STAGE"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "PREVENT_LIVE"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-001-R - 澁谷かのん

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにほかのメンバーがいない場合、自分はライブできない。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(203) {{"MAX": 0, "TARGET": "OTHER_MEMBER", "raw_cond": "COUNT_STAGE"}}
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"raw_effect": "PREVENT_LIVE"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-002-P - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 10, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-002-P＋ - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 10, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-002-R＋ - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 10, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-002-SEC - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 10, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-003-P - 嵐 千砂都

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ACTIVATE_MEMBER(20) -> PLAYER {{"trigger": "CONSTANT", "effect": "BOOST_SCORE(1)", "duration": "UNTIL_LIVE_END", "raw_effect": "IF"}}
```

### Bytecode Sequences
- Ability 1: `[29, 20, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-003-P＋ - 嵐 千砂都

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ACTIVATE_MEMBER(20) -> PLAYER {{"trigger": "CONSTANT", "effect": "BOOST_SCORE(1)", "duration": "UNTIL_LIVE_END", "raw_effect": "IF"}}
```

### Bytecode Sequences
- Ability 1: `[29, 20, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-003-R＋ - 嵐 千砂都

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ACTIVATE_MEMBER(20) -> PLAYER {{"trigger": "CONSTANT", "effect": "BOOST_SCORE(1)", "duration": "UNTIL_LIVE_END", "raw_effect": "IF"}}
```

### Bytecode Sequences
- Ability 1: `[29, 20, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-003-SEC - 嵐 千砂都

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
EFFECT: ACTIVATE_MEMBER(20) -> PLAYER {{"trigger": "CONSTANT", "effect": "BOOST_SCORE(1)", "duration": "UNTIL_LIVE_END", "raw_effect": "IF"}}
```

### Bytecode Sequences
- Ability 1: `[29, 20, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-004-P - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: SWAP_CARDS(5) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 5, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-004-R - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}ステージのセンターエリアにいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: SWAP_CARDS(5) -> SELF
```

### Bytecode Sequences
- Ability 1: `[11, 5, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-005-P - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚まで公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "GROUP_ID=3", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 5, 113, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-005-R - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚まで公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "GROUP_ID=3", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 5, 113, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-006-P - 桜小路きな子

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-006-R - 桜小路きな子

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-007-P - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーが11枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 11, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[213, 11, 0, 0, 48, 15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-007-P＋ - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーが11枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 11, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[213, 11, 0, 0, 48, 15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-007-R＋ - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーが11枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 11, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[213, 11, 0, 0, 48, 15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-007-SEC - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーが11枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 11, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[213, 11, 0, 0, 48, 15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-008-P - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引く。自分のステージに「米女メイ」がいる場合、さらにカードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 203, 1, 0, 6016, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-008-R - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引く。自分のステージに「米女メイ」がいる場合、さらにカードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 203, 1, 0, 6016, 48, 0, 1, 0, 0, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-009-P - 鬼塚夏美

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-009-R - 鬼塚夏美

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：カードを1枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1)
EFFECT: MOVE_MEMBER(1) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-010-P - ウィーン・マルガレーテ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2), DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "GROUP_ID=3", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 41, 5, 113, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-010-R - ウィーン・マルガレーテ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2), DISCARD_HAND(1) {{"destination": "success"}}
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "GROUP_ID=3", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 41, 5, 113, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-011-P - 鬼塚冬毬

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-011-R - 鬼塚冬毬

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-012-N - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-013-N - 唐 可可

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-013-PR - 唐 可可

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-014-N - 嵐 千砂都

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-015-N - 平安名すみれ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-016-N - 葉月 恋

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-017-N - 桜小路きな子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-018-N - 米女メイ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-019-N - 若菜四季

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-020-N - 鬼塚夏美

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-021-N - ウィーン・マルガレーテ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-022-N - 鬼塚冬毬

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp1-023-L - START!! True dreams

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。

(エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(220) {TARGET=OPPONENT, TYPE=SCORE, {"val": "PLAYER", "raw_cond": "SCORE_LEAD", "comparison": "GT"}}
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[220, 0, 0, 0, 16, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-024-L - Tiny Stars

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる「澁谷かのん」1人は{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を、「唐可可」1人は{{heart_01.png|heart01}}{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。

(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME=\u6f81\u8c37\u304b\u306e\u3093", "destination": "target_1"}}; SEARCH_DECK(1) -> PLAYER {{"heart_type": "PINK", "duration": "UNTIL_LIVE_END", "destination": "target_1"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target_1"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME=\u5510\u53ef\u53ef", "destination": "target_2"}}; SEARCH_DECK(1) -> PLAYER {{"heart_type": "RED", "duration": "UNTIL_LIVE_END", "destination": "target_2"}}; SWAP_CARDS(1) -> PLAYER {{"duration": "UNTIL_LIVE_END", "destination": "target_2"}}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(203) {{"FILTER": "NAME=\u6f81\u8c37\u304b\u306e\u3093", "GE": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}, UNKNOWN(203) {{"FILTER": "NAME=\u5510\u53ef\u53ef", "GE": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[65, 1, 1, 5248, 262148, 12, 1, 0, 0, 4, 11, 1, 0, 0, 4, 65, 1, 1, 5376, 262148, 12, 1, 0, 0, 4, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 1, 0, 5248, 48, 203, 1, 0, 5376, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-025-L - Starlight Prologue

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-025-L＋ - Starlight Prologue

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-026-L - 未来予報ハレルヤ！

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}になる。

(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(208) {{"GROUP": "Liella!", "ZONE": "STAGE,DISCARD", "UNIQUE_NAMES": true, "val": "5", "raw_cond": "COUNT_GROUP"}}
EFFECT: UNKNOWN(83)(1) -> PLAYER {{"red": 2, "yellow": 2, "purple": 2}}
```

### Bytecode Sequences
- Ability 1: `[208, 5, 32768, 8388608, 48, 83, 2097696, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp1-027-L - Sing！Shine！Smile！

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のエネルギーが12枚以上ある場合、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(213) {{"MIN": 12, "raw_cond": "SUM_ENERGY"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[213, 12, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-001-P - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=3"}} (Optional); LOOK_AND_CHOOSE(0) -> PLAYER {{"destination": "success", "trigger": "ON_LIVE_START"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 113, 536870912, 262148, 27, 0, 0, 0, 4, 312, 0, 0, 0, 48, 0, 1, 112, 14680064, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-001-P＋ - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=3"}} (Optional); LOOK_AND_CHOOSE(0) -> PLAYER {{"destination": "success", "trigger": "ON_LIVE_START"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 113, 536870912, 262148, 27, 0, 0, 0, 4, 312, 0, 0, 0, 48, 0, 1, 112, 14680064, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-001-R＋ - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=3"}} (Optional); LOOK_AND_CHOOSE(0) -> PLAYER {{"destination": "success", "trigger": "ON_LIVE_START"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 113, 536870912, 262148, 27, 0, 0, 0, 4, 312, 0, 0, 0, 48, 0, 1, 112, 14680064, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-001-SEC - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=3"}} (Optional); LOOK_AND_CHOOSE(0) -> PLAYER {{"destination": "success", "trigger": "ON_LIVE_START"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 113, 536870912, 262148, 27, 0, 0, 0, 4, 312, 0, 0, 0, 48, 0, 1, 112, 14680064, 48, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-002-P - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中からコスト11以上のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"filter": "COST_GE=11", "destination": "discard", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[41, -2147483645, -1761607680, 536870912, 67334, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-002-R - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中からコスト11以上のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"filter": "COST_GE=11", "destination": "discard", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[41, -2147483645, -1761607680, 536870912, 67334, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-003-P - 嵐 千砂都

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
(Once per turn)
EFFECT: SET_SCORE(1) -> PLAYER {{"mode": "WAIT", "wait": true}}
```

### Bytecode Sequences
- Ability 1: `[23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-003-R - 嵐 千砂都

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
(Once per turn)
EFFECT: SET_SCORE(1) -> PLAYER {{"mode": "WAIT", "wait": true}}
```

### Bytecode Sequences
- Ability 1: `[23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-004-P - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにいるメンバーのうち、センターエリアにいるメンバーが最も大きいコストを持つ場合、{{heart_03.png|heart03}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}, UNKNOWN(203) {{"FILTER": "COST_GT=GET_COST(SELF), NOT_CENTER", "EQ": 0, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 3}}
```

### Bytecode Sequences
- Ability 1: `[12, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-004-R - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにいるメンバーのうち、センターエリアにいるメンバーが最も大きいコストを持つ場合、{{heart_03.png|heart03}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(206) {{"val": "SELF", "raw_cond": "IS_CENTER"}}, UNKNOWN(203) {{"FILTER": "COST_GT=GET_COST(SELF), NOT_CENTER", "EQ": 0, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 3}}
```

### Bytecode Sequences
- Ability 1: `[12, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-005-P - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを7枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(7) -> PLAYER {{"filter": "GROUP_ID=3", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 7, 113, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-005-R - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを7枚見る。その中から『Liella!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(7) -> PLAYER {{"filter": "GROUP_ID=3", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 7, 113, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-006-P - 桜小路きな子

### Japanese Ability
```text
{{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。
({{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"zone": "DISCARD", "filter": "GROUP_ID=3", "source": "discard"}}

TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"FILTER": "GROUP_ID=3, COST_LE=4", "destination": "discarded"}}
EFFECT: UNKNOWN(47)(0) -> PLAYER {{"trigger": "ON_PLAY"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 17, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[47, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-006-P＋ - 桜小路きな子

### Japanese Ability
```text
{{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。
({{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"zone": "DISCARD", "filter": "GROUP_ID=3", "source": "discard"}}

TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"FILTER": "GROUP_ID=3, COST_LE=4", "destination": "discarded"}}
EFFECT: UNKNOWN(47)(0) -> PLAYER {{"trigger": "ON_PLAY"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 17, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[47, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-006-R＋ - 桜小路きな子

### Japanese Ability
```text
{{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。
({{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"zone": "DISCARD", "filter": "GROUP_ID=3", "source": "discard"}}

TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"FILTER": "GROUP_ID=3, COST_LE=4", "destination": "discarded"}}
EFFECT: UNKNOWN(47)(0) -> PLAYER {{"trigger": "ON_PLAY"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 17, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[47, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-006-SEC - 桜小路きな子

### Japanese Ability
```text
{{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。
({{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"val": "PLAYER", "raw_cond": "BATON_TOUCH"}}
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"zone": "DISCARD", "filter": "GROUP_ID=3", "source": "discard"}}

TRIGGER: ACTIVATED
(Once per turn)
COST: DISCARD_HAND(1) {{"FILTER": "GROUP_ID=3, COST_LE=4", "destination": "discarded"}}
EFFECT: UNKNOWN(47)(0) -> PLAYER {{"trigger": "ON_PLAY"}}
```

### Bytecode Sequences
- Ability 1: `[231, 0, 0, 0, 0, 17, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`
- Ability 2: `[47, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-007-P - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『Liella!』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "GROUP_ID=3, TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 5, 117, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-007-R - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『Liella!』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "GROUP_ID=3, TYPE_MEMBER", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 5, 117, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-008-P - 若菜四季

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1) {{"destination": "success"}}
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "target_area", "raw_effect": "SELECT_AREA"}}; PLACE_UNDER(0) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 29, 0, 0, 0, 4, 20, 0, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-008-R - 若菜四季

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1) {{"destination": "success"}}
EFFECT: ACTIVATE_MEMBER(0) -> PLAYER {{"destination": "target_area", "raw_effect": "SELECT_AREA"}}; PLACE_UNDER(0) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[312, 0, 0, 0, 48, 29, 0, 0, 0, 4, 20, 0, 1, 0, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-009-P - 鬼塚夏美

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "hand_val", "raw_effect": "COUNT_HAND", "raw_val": "PLAYER"}}; UNKNOWN(126)(2) -> PLAYER {{"destination": "blade_val"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "raw_val": "BLADE_VAL"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 126, 2, 0, 0, 0, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-009-P＋ - 鬼塚夏美

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "hand_val", "raw_effect": "COUNT_HAND", "raw_val": "PLAYER"}}; UNKNOWN(126)(2) -> PLAYER {{"destination": "blade_val"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "raw_val": "BLADE_VAL"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 126, 2, 0, 0, 0, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-009-R＋ - 鬼塚夏美

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "hand_val", "raw_effect": "COUNT_HAND", "raw_val": "PLAYER"}}; UNKNOWN(126)(2) -> PLAYER {{"destination": "blade_val"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "raw_val": "BLADE_VAL"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 126, 2, 0, 0, 0, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-009-SEC - 鬼塚夏美

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。
{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "hand_val", "raw_effect": "COUNT_HAND", "raw_val": "PLAYER"}}; UNKNOWN(126)(2) -> PLAYER {{"destination": "blade_val"}}; SWAP_CARDS(1) -> SELF {{"duration": "UNTIL_LIVE_END", "raw_val": "BLADE_VAL"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 126, 2, 0, 0, 0, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-010-P - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。
{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: UNKNOWN(61)(1) -> PLAYER {TARGET=OPPONENT_LIVE, {"heart_type": "ANY"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(62)(8) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[61, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 0, 0, 50331648, 48, 62, 8, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-010-P＋ - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。
{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: UNKNOWN(61)(1) -> PLAYER {TARGET=OPPONENT_LIVE, {"heart_type": "ANY"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(62)(8) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[61, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 0, 0, 50331648, 48, 62, 8, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-010-R＋ - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。
{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: UNKNOWN(61)(1) -> PLAYER {TARGET=OPPONENT_LIVE, {"heart_type": "ANY"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(62)(8) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[61, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 0, 0, 50331648, 48, 62, 8, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-010-SEC - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。
{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: UNKNOWN(61)(1) -> PLAYER {TARGET=OPPONENT_LIVE, {"heart_type": "ANY"}}

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "NOT_SELF", "MIN": 1, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(62)(8) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[61, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[203, 0, 0, 50331648, 48, 62, 8, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-011-P - 鬼塚冬毬

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(2) -> PLAYER {FROM=DISCARD, {"type_live": true, "unique_names": true, "destination": "options"}} (Optional); UNKNOWN(75)(1) -> PLAYER {{"destination": "target", "raw_val": "OPTIONS"}}; UNKNOWN(44)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[74, 2, 32769, 536870912, 458756, 75, 1, 0, 0, 4, 44, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-011-R - 鬼塚冬毬

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室にある、カード名の異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(2) -> PLAYER {FROM=DISCARD, {"type_live": true, "unique_names": true, "destination": "options"}} (Optional); UNKNOWN(75)(1) -> PLAYER {{"destination": "target", "raw_val": "OPTIONS"}}; UNKNOWN(44)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[74, 2, 32769, 536870912, 458756, 75, 1, 0, 0, 4, 44, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-012-N - 澁谷かのん

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp2-013-N - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からカードを1枚までデッキの一番上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=DISCARD, {"destination": "target"}} (Optional); SET_BLADES(0) -> PLAYER {TO=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1, 536870912, 458756, 31, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-014-N - 嵐 千砂都

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からカードを1枚までデッキの一番上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=DISCARD, {"destination": "target"}} (Optional); SET_BLADES(0) -> PLAYER {TO=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1, 536870912, 458756, 31, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-015-N - 平安名すみれ

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_06.png|heart06}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
CONDITION: UNKNOWN(226) {{"FILTER": "HAS_BLADE_HEART", "EQ": 0, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 5, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 12, 1, 5, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-016-N - 葉月 恋

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp2-017-N - 桜小路きな子

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp2-018-N - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}自分の控え室からカードを1枚までデッキの一番上に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=DISCARD, {"destination": "target"}} (Optional); SET_BLADES(0) -> PLAYER {TO=DECK_TOP}
```

### Bytecode Sequences
- Ability 1: `[74, 1, 1, 536870912, 458756, 31, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-019-N - 若菜四季

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-020-N - 鬼塚夏美

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_02.png|heart02}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
CONDITION: UNKNOWN(226) {{"FILTER": "HAS_BLADE_HEART", "EQ": 0, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 1, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 12, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-021-N - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_03.png|heart03}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
CONDITION: UNKNOWN(226) {{"FILTER": "HAS_BLADE_HEART", "EQ": 0, "val": "PLAYER", "raw_cond": "COUNT_YELL_REVEALED", "keyword": "YELL_COUNT"}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 2, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 8192, 48, 12, 1, 2, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-022-N - 鬼塚冬毬

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(2) -> SELF
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-023-L - Go!! リスタート

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカード枚数が相手より少ない場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(218) {TARGET=SELF, {"val": "COUNT_SUCCESS_LIVE(OPPONENT)", "comparison": "LT", "raw_cond": "COUNT_SUCCESS_LIVE"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[218, 0, 0, 0, 32, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-024-L - ビタミンSUMMER！

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分の手札の枚数が相手より多い場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(204) {{"TARGET": "PLAYER", "GREATER_THAN": "OPPONENT", "raw_cond": "HAND_SIZE"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[204, 0, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-025-L - Bubble Rise

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分のカードの中から、カードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(203) {{"FILTER": "NAME_IN=['\u6f81\u8c37\u304b\u306e\u3093', '\u30a6\u30a3\u30fc\u30f3\u00b7\u30de\u30eb\u30ac\u30ec\u30fc\u30c6', '\u9b3c\u585a\u51ac\u6bec'], UNIQUE_NAMES", "MIN": 2, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: ACTIVATE_MEMBER(1) -> CARD_HAND {{"zone": "YELL_REVEALED", "raw_effect": "SELECT_RECOVER_CARD"}}
```

### Bytecode Sequences
- Ability 1: `[203, 0, 6684672, 5248, 48, 29, 1, 0, 0, 6, 1, 0, 0, 0, 0]`

---

## PL!SP-bp2-026-L - 笑顔のPromise

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp2-027-L - UNIVERSE!!

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp4-001-P - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーが『Liella!』のみで、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(209) {{"FILTER": "GROUP_ID=3", "raw_cond": "ALL_MEMBERS"}, ALL}, UNKNOWN(213) {{"MIN": 7, "raw_cond": "ENERGY_COUNT"}}
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[209, 4, 112, 0, 48, 213, 7, 0, 0, 48, 23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-001-R - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーが『Liella!』のみで、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(209) {{"FILTER": "GROUP_ID=3", "raw_cond": "ALL_MEMBERS"}, ALL}, UNKNOWN(213) {{"MIN": 7, "raw_cond": "ENERGY_COUNT"}}
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[209, 4, 112, 0, 48, 213, 7, 0, 0, 48, 23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-002-P - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを4枚見る。その中から必要ハートの合計が8以上の『Liella!』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "SUM_HEART_TOTAL_GE=8, GROUP_ID=3, TYPE_LIVE", "reveal": "True", "pick": "1", "dest_discard": "True", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 41, -1073741820, 285212793, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-002-R - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを4枚見る。その中から必要ハートの合計が8以上の『Liella!』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(4) -> PLAYER {{"filter": "SUM_HEART_TOTAL_GE=8, GROUP_ID=3, TYPE_LIVE", "reveal": "True", "pick": "1", "dest_discard": "True", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[51, 0, 0, 536870912, 4, 3, 1, 0, 0, 0, 41, -1073741820, 285212793, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-003-P - 嵐 千砂都

### Japanese Ability
```text
{{toujyou.png|登場}}【左サイド】【右サイド】カードを2枚引き、手札を2枚控え室に置く。（この能力は左サイドエリアか右サイドエリアに登場した場合のみ発動する。）
{{jyouji.png|常時}}{{center.png|センター}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(234) {{"comparison": "EQ", "val": "[\"LEFT_SIDE", "raw_cond": "AREA_IN", "keyword": "AREA_CHECK"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: SWAP_CARDS(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[234, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-003-R - 嵐 千砂都

### Japanese Ability
```text
{{toujyou.png|登場}}【左サイド】【右サイド】カードを2枚引き、手札を2枚控え室に置く。（この能力は左サイドエリアか右サイドエリアに登場した場合のみ発動する。）
{{jyouji.png|常時}}{{center.png|センター}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(234) {{"comparison": "EQ", "val": "[\"LEFT_SIDE", "raw_cond": "AREA_IN", "keyword": "AREA_CHECK"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(2) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: SWAP_CARDS(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[234, 0, 0, 0, 0, 10, 2, 0, 0, 4, 58, 2, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-004-P - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。
{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: REDUCE_HEART_REQ(2) -> SELF (Optional)

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}, BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 2, "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(63)(1) -> PLAYER {{"filter": "GROUP_ID=3, COST_LE_4", "destination": "BATON_TOUCHED"}}
```

### Bytecode Sequences
- Ability 1: `[36, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 231, 2, 112, 0, 0, 10, 2, 0, 0, 4, 63, 1, -922746767, 0, 34013188, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-004-P＋ - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。
{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: REDUCE_HEART_REQ(2) -> SELF (Optional)

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}, BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 2, "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(63)(1) -> PLAYER {{"filter": "GROUP_ID=3, COST_LE_4", "destination": "BATON_TOUCHED"}}
```

### Bytecode Sequences
- Ability 1: `[36, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 231, 2, 112, 0, 0, 10, 2, 0, 0, 4, 63, 1, -922746767, 0, 34013188, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-004-R＋ - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。
{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: REDUCE_HEART_REQ(2) -> SELF (Optional)

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}, BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 2, "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(63)(1) -> PLAYER {{"filter": "GROUP_ID=3, COST_LE_4", "destination": "BATON_TOUCHED"}}
```

### Bytecode Sequences
- Ability 1: `[36, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 231, 2, 112, 0, 0, 10, 2, 0, 0, 4, 63, 1, -922746767, 0, 34013188, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-004-SEC - 平安名すみれ

### Japanese Ability
```text
{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。
{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: REDUCE_HEART_REQ(2) -> SELF (Optional)

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "CENTER", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}, BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 2, "raw_cond": "BATON_TOUCH"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(63)(1) -> PLAYER {{"filter": "GROUP_ID=3, COST_LE_4", "destination": "BATON_TOUCHED"}}
```

### Bytecode Sequences
- Ability 1: `[36, 2, 0, 536870912, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 231, 2, 112, 0, 0, 10, 2, 0, 0, 4, 63, 1, -922746767, 0, 34013188, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-005-P - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。
{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 1, "SUM_ENERGY_GE": 7, "raw_cond": "BATON_TOUCH"}}
EFFECT: SET_SCORE(2) -> PLAYER {{"wait": true}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 10, "raw_cond": "ENERGY_COUNT"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[231, 1, 112, 0, 0, 23, 2, 0, 0, 134217732, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-005-P＋ - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。
{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 1, "SUM_ENERGY_GE": 7, "raw_cond": "BATON_TOUCH"}}
EFFECT: SET_SCORE(2) -> PLAYER {{"wait": true}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 10, "raw_cond": "ENERGY_COUNT"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[231, 1, 112, 0, 0, 23, 2, 0, 0, 134217732, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-005-R＋ - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。
{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 1, "SUM_ENERGY_GE": 7, "raw_cond": "BATON_TOUCH"}}
EFFECT: SET_SCORE(2) -> PLAYER {{"wait": true}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 10, "raw_cond": "ENERGY_COUNT"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[231, 1, 112, 0, 0, 23, 2, 0, 0, 134217732, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-005-SEC - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。
{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: BATON_PASS_CHECK {{"FILTER": "GROUP_ID=3", "COUNT_EQ": 1, "SUM_ENERGY_GE": 7, "raw_cond": "BATON_TOUCH"}}
EFFECT: SET_SCORE(2) -> PLAYER {{"wait": true}}

TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 10, "raw_cond": "ENERGY_COUNT"}}
EFFECT: SWAP_CARDS(3) -> SELF
```

### Bytecode Sequences
- Ability 1: `[231, 1, 112, 0, 0, 23, 2, 0, 0, 134217732, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-006-P - 桜小路きな子

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に、名前が異なる『Liella!』のメンバーカードが3枚以上ある場合、エールにより公開された自分のカードの中から『Liella!』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"FILTER": "GROUP_ID=3, UNIQUE_NAMES", "MIN": 3, "raw_cond": "YELL_CARDS"}}
EFFECT: ACTIVATE_MEMBER(1) -> CARD_HAND {{"filter": "GROUP_ID=3, TYPE_LIVE", "raw_effect": "SELECT_YELL"}}
```

### Bytecode Sequences
- Ability 1: `[0, 3, 112, 0, 48, 29, 1, 120, 0, 6, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-006-R - 桜小路きな子

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に、名前が異なる『Liella!』のメンバーカードが3枚以上ある場合、エールにより公開された自分のカードの中から『Liella!』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"FILTER": "GROUP_ID=3, UNIQUE_NAMES", "MIN": 3, "raw_cond": "YELL_CARDS"}}
EFFECT: ACTIVATE_MEMBER(1) -> CARD_HAND {{"filter": "GROUP_ID=3, TYPE_LIVE", "raw_effect": "SELECT_YELL"}}
```

### Bytecode Sequences
- Ability 1: `[0, 3, 112, 0, 48, 29, 1, 120, 0, 6, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-007-P - 米女メイ

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分の控え室から、スコア3以下の『Liella!』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
(Once per turn)
CONDITION: UNKNOWN(308) {{"raw_cond": "IS_SELF_MOVE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=3, SCORE_LE_3", "zone": "DISCARD", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[308, 0, 0, 0, 48, 15, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-007-R - 米女メイ

### Japanese Ability
```text
{{jidou.png|自動}}{{turn1.png|ターン1回}}このメンバーがエリアを移動したとき、自分の控え室から、スコア3以下の『Liella!』のライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
(Once per turn)
CONDITION: UNKNOWN(308) {{"raw_cond": "IS_SELF_MOVE"}}
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"filter": "GROUP_ID=3, SCORE_LE_3", "zone": "DISCARD", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[308, 0, 0, 0, 48, 15, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-008-P - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}【左サイド】カードを2枚引き、手札を1枚控え室に置く。
{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。
{{live_start.png|ライブ開始時}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "RIGHT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: PLACE_UNDER(1) -> SELF (Optional)
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[20, 1, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-008-P＋ - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}【左サイド】カードを2枚引き、手札を1枚控え室に置く。
{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。
{{live_start.png|ライブ開始時}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "RIGHT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: PLACE_UNDER(1) -> SELF (Optional)
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[20, 1, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-008-R＋ - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}【左サイド】カードを2枚引き、手札を1枚控え室に置く。
{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。
{{live_start.png|ライブ開始時}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "RIGHT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: PLACE_UNDER(1) -> SELF (Optional)
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[20, 1, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-008-SEC - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}【左サイド】カードを2枚引き、手札を1枚控え室に置く。
{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。
{{live_start.png|ライブ開始時}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_PLAY
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "RIGHT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}
EFFECT: UNKNOWN(81)(2) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: PLACE_UNDER(1) -> SELF (Optional)
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`
- Ability 2: `[226, 0, 0, 4096, 0, 81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 3: `[20, 1, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-009-P - 鬼塚夏美

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにいるメンバーのコストの合計が相手より低いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(220) {TYPE=COST, {"TARGET": "PLAYER", "STAGE": true, "LESS_THAN": "OPPONENT", "raw_cond": "SUM_COST", "comparison": "GE"}}
EFFECT: SWAP_CARDS(3) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-009-R - 鬼塚夏美

### Japanese Ability
```text
{{jyouji.png|常時}}自分のステージにいるメンバーのコストの合計が相手より低いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(220) {TYPE=COST, {"TARGET": "PLAYER", "STAGE": true, "LESS_THAN": "OPPONENT", "raw_cond": "SUM_COST", "comparison": "GE"}}
EFFECT: SWAP_CARDS(3) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[11, 3, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-010-P - ウィーン・マルガレーテ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}このメンバーをウェイトにする：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1), TAP_SELF(0)
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-010-R - ウィーン・マルガレーテ

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}このメンバーをウェイトにする：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(1), TAP_SELF(0)
EFFECT: SET_SCORE(1) -> PLAYER {{"wait": true}}
```

### Bytecode Sequences
- Ability 1: `[23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-011-P - 鬼塚冬毬

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}

TRIGGER: ON_LEAVES
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-011-P＋ - 鬼塚冬毬

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}

TRIGGER: ON_LEAVES
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-011-R＋ - 鬼塚冬毬

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}

TRIGGER: ON_LEAVES
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-011-SEC - 鬼塚冬毬

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}

TRIGGER: ON_LEAVES
CONDITION: NONE {{"raw_cond": "IS_SELF_MOVE_OR_PLAY"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "OPPONENT, BASE_BLADES_LE_3", "destination": "target"}}; UNKNOWN(53)(1) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[0, 0, 0, 0, 48, 65, 1, 2, 0, 262148, 53, 1, 3, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-012-N - 澁谷かのん

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_02.png|heart02}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 2}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 1, 0, 0, 0, 12, 1, 2, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-013-N - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: PLACE_UNDER(1) -> SELF (Optional)
```

### Bytecode Sequences
- Ability 1: `[20, 1, 1, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-014-N - 嵐 千砂都

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp4-015-N - 平安名すみれ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-016-N - 葉月 恋

### Japanese Ability
```text
{{jidou.png|自動}}カードの効果によって自分のエネルギー置き場にエネルギーカードが置かれるたび、ライブ終了時まで、{{heart_06.png|heart06}}を得る。(相手のカードの効果でも発動する。)
```

### Regenerated Pseudocode
```text
TRIGGER: NONE
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 6, "duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[12, 1, 6, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-017-N - 桜小路きな子

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}【左サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（この能力は左サイドエリアにいる場合のみ発動する。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "LEFT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}, NONE {{"raw_cond": "HAS_MOVED_THIS_TURN"}}
EFFECT: SWAP_CARDS(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 0, 0, 0, 0, 48, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-018-N - 米女メイ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室から『Liella!』のカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {FROM=DISCARD, {"filter": "Liella!", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-019-N - 若菜四季

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-020-N - 鬼塚夏美

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}【右サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（この能力は右サイドエリアにいる場合のみ発動する。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(226) {{"comparison": "EQ", "val": "RIGHT_SIDE", "raw_cond": "AREA", "keyword": "PLAYED_THIS_TURN"}}, NONE {{"raw_cond": "HAS_MOVED_THIS_TURN"}}
EFFECT: SWAP_CARDS(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[226, 0, 0, 4096, 0, 0, 0, 0, 0, 48, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-021-N - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jyouji.png|常時}}自分のエネルギーが相手より多いかぎり、{{heart_06.png|heart06}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(225) {{"TARGET": "PLAYER", "raw_cond": "ENERGY_LEAD", "comparison": "LE", "diff": 0}}
EFFECT: SEARCH_DECK(1) -> SELF {{"heart_type": 6}}
```

### Bytecode Sequences
- Ability 1: `[12, 1, 6, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-022-N - 鬼塚冬毬

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を2つまで支払ってもよい：ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(1) -> PLAYER {{"per_energy_paid": 1}}
```

### Bytecode Sequences
- Ability 1: `[64, 0, 0, 536870912, 0, 3, 1, 0, 0, 0, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-023-L - Dazzling Game

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「澁谷かのん」「ウィーン・マルガレーテ」「鬼塚冬毬」のうちのメンバー1人と、これにより選んだメンバー以外の『Liella!』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。
{{live_start.png|ライブ開始時}}ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[紫ブレード]になる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"filter": "NAME_IN=['\u6f81\u8c37\u304b\u306e\u3093', '\u30a6\u30a3\u30fc\u30f3\u30fb\u30de\u30eb\u30ac\u30ec\u30fc\u30c6', '\u9b3c\u585a\u51ac\u6bec']", "destination": "target_1"}}; UNKNOWN(65)(1) -> PLAYER {{"filter": "GROUP_ID=3, NOT_TARGET=TARGET_1", "destination": "target_2"}}; SWAP_CARDS(1) -> PLAYER {{"destination": "target_1"}}; SWAP_CARDS(1) -> PLAYER {{"destination": "target_2"}}

TRIGGER: ON_LIVE_START
EFFECT: PLAY_MEMBER_FROM_HAND(5) -> PLAYER {{"filter": "NOT_BLADE_TYPE_6", "duration": "UNTIL_LIVE_END", "destination": "6", "raw_val": "ALL", "source_color": 0}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 6684673, 824448, 262148, 65, 1, 113, 117440512, 262148, 11, 1, 0, 0, 4, 11, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[39, 5, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-024-L - ノンフィクション!!

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のセンターエリアにいる『Liella!』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを＋１する。
{{live_start.png|ライブ開始時}}自分のステージの左サイドエリアにいる『Liella!』のメンバーが{{heart_02.png|heart02}}を3つ以上持つ場合、そのメンバーは、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(311) {{"PLAYER_CENTER_FILTER": "GROUP_ID=3", "raw_cond": "PLAYER_CENTER_COST_GT_OPPONENT_CENTER_COST", "area": "CENTER", "comparison": "GT", "val": "0"}}
EFFECT: META_RULE(1) -> SELF

TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(306) {{"AREA": "LEFT_SIDE", "FILTER": "GROUP_ID=3, HAS_COLOR_YELLOW_X3", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"area": "LEFT_SIDE", "filter": "GROUP_ID=3, HAS_COLOR_YELLOW_X3", "destination": "target"}}; SWAP_CARDS(2) -> PLAYER {{"destination": "target"}}
```

### Bytecode Sequences
- Ability 1: `[311, 0, 112, 0, 1073741840, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[306, 1, 117440624, 4, 536870960, 65, 1, 117440625, 4, 537133060, 11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-025-L - Special Color

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ{{icon_blade.png|ブレード}}の数は3つになる。
{{live_success.png|ライブ成功時}}自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(65)(1) -> PLAYER {{"area": "CENTER", "filter": "GROUP_ID=3", "destination": "target"}}; UNKNOWN(127)(3) -> MEMBER_SELF {TARGET=TARGET, {"raw_val": "ALL"}}

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(306) {{"AREA": "CENTER", "FILTER": "GROUP_ID=3, MOVED_THIS_TURN", "val": "1", "raw_cond": "SELECT_MEMBER"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[65, 1, 113, 0, 1074003972, 127, 3, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[306, 1, 112, 0, 1073741872, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-026-L - Wish Song

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に名前が異なる『Liella!』のメンバーカードが5枚以上ある場合、このカードのスコアを＋１する。
{{live_success.png|ライブ成功時}}自分のエネルギーが11枚以上ある場合、カードを2枚引き、手札を1枚控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: NONE {{"FILTER": "GROUP_ID=3, UNIQUE_NAMES", "MIN": 5, "raw_cond": "YELL_CARDS"}}
EFFECT: META_RULE(1) -> SELF

TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(213) {{"MIN": 11, "raw_cond": "ENERGY_COUNT"}}
EFFECT: MOVE_MEMBER(2) -> PLAYER; UNKNOWN(58)(1) -> PLAYER {{"source": "HAND", "destination": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[0, 5, 112, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[213, 11, 0, 0, 48, 10, 2, 0, 0, 4, 58, 1, 1, 12582912, 393217, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-027-L - Chance Day, Chance Way!

### Japanese Ability
```text
{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。(メンバーをそれぞれ好きなエリアに移動させる。この効果で1つのエリアに2人以上のメンバーを移動させることはできない。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_SUCCESS
CONDITION: UNKNOWN(209) {{"FILTER": "GROUP_ID=3", "raw_cond": "ALL_MEMBERS"}, ALL}
EFFECT: REVEAL_CARDS(1) -> PLAYER (Optional)
```

### Bytecode Sequences
- Ability 1: `[209, 4, 112, 0, 48, 26, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-028-L - DAISUKI FULL POWER

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}アクティブ状態の自分のエネルギーがある場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(213) {MIN=1, {"raw_cond": "HAS_ACTIVE_ENERGY", "filter": "active"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[213, 1, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-bp4-029-L - 追いかける夢の先で

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-bp4-030-L - Second Sparkle

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-pb1-001-P＋ - 澁谷かのん

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払わないかぎり、自分の手札を2枚控え室に置く。
{{live_success.png|ライブ成功時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブの合計スコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(2) -> PLAYER {{"options": ["PAY_ENERGY(2)", "DISCARD_HAND(2)"]}}
    Options:
      1: UNK(2)->PLAYER
      2: UNK(2)->PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 64, 2, 0, 0, 4, 2, 3, 0, 0, 0, 58, 2, 1, 12582912, 393217, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 6, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-001-R - 澁谷かのん

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払わないかぎり、自分の手札を2枚控え室に置く。
{{live_success.png|ライブ成功時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブの合計スコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ADD_TO_HAND(2) -> PLAYER {{"options": ["PAY_ENERGY(2)", "DISCARD_HAND(2)"]}}
    Options:
      1: UNK(2)->PLAYER
      2: UNK(2)->PLAYER {{"source": "HAND", "destination": "discard"}}

TRIGGER: ON_LIVE_SUCCESS
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[30, 2, 0, 0, 0, 2, 1, 0, 0, 0, 2, 2, 0, 0, 0, 64, 2, 0, 0, 4, 2, 3, 0, 0, 0, 58, 2, 1, 12582912, 393217, 2, 1, 0, 0, 0, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 6, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-002-P＋ - 唐 可可

### Japanese Ability
```text
{{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 12, "raw_cond": "SUM_ENERGY"}}
EFFECT: META_RULE(1) -> PLAYER {TARGET=LIVE}
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-002-R - 唐 可可

### Japanese Ability
```text
{{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 12, "raw_cond": "SUM_ENERGY"}}
EFFECT: META_RULE(1) -> PLAYER {TARGET=LIVE}
```

### Bytecode Sequences
- Ability 1: `[16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-003-P＋ - 嵐 千砂都

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 3, "ALL": true, "FILTER": "GROUP_ID=3", "raw_cond": "COUNT_STAGE"}}
EFFECT: UNKNOWN(72)(0) -> PLAYER {{"player": "ALL_PLAYERS"}}
```

### Bytecode Sequences
- Ability 1: `[203, 7, 112, 0, 48, 72, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-003-R - 嵐 千砂都

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 3, "ALL": true, "FILTER": "GROUP_ID=3", "raw_cond": "COUNT_STAGE"}}
EFFECT: UNKNOWN(72)(0) -> PLAYER {{"player": "ALL_PLAYERS"}}
```

### Bytecode Sequences
- Ability 1: `[203, 7, 112, 0, 48, 72, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-004-P＋ - 平安名すみれ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
{{live_success.png|ライブ成功時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SET_SCORE(1) -> PLAYER

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(1) -> PLAYER (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 3, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 10, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-004-R - 平安名すみれ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
{{live_success.png|ライブ成功時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SET_SCORE(1) -> PLAYER

TRIGGER: ON_LIVE_SUCCESS
EFFECT: MOVE_MEMBER(1) -> PLAYER (Optional)
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[64, 3, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 10, 1, 0, 536870912, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-005-P＋ - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER {{"mode": "WAIT", "wait": true}}
```

### Bytecode Sequences
- Ability 1: `[23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-005-R - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER {{"mode": "WAIT", "wait": true}}
```

### Bytecode Sequences
- Ability 1: `[23, 1, 0, 0, 134217732, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-006-P＋ - 桜小路きな子

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
(対戦相手のカードの効果でも発動する。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}

TRIGGER: ON_PLAY
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-006-R - 桜小路きな子

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
(対戦相手のカードの効果でも発動する。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}

TRIGGER: ON_PLAY
EFFECT: SWAP_CARDS(2) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[11, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-007-P＋ - 米女メイ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(81)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-007-R - 米女メイ

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}エネルギーを2枚アクティブにする。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: UNKNOWN(81)(2) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[81, 2, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-008-P＋ - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "target_area", "raw_effect": "SELECT_AREA", "raw_val": "OTHER_AREA"}}; UNKNOWN(72)(0) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 29, 1, 0, 0, 4, 72, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-008-R - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1) -> PLAYER; ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "target_area", "raw_effect": "SELECT_AREA", "raw_val": "OTHER_AREA"}}; UNKNOWN(72)(0) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 29, 1, 0, 0, 4, 72, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-009-P＋ - 鬼塚夏美

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにほかの『5yncri5e!』のメンバーがいる場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "FILTER": "GROUP_ID=3", "raw_cond": "COUNT_STAGE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[203, 1, 112, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-009-R - 鬼塚夏美

### Japanese Ability
```text
{{toujyou.png|登場}}自分のステージにほかの『5yncri5e!』のメンバーがいる場合、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(203) {{"MIN": 1, "TARGET": "OTHER_MEMBER", "FILTER": "GROUP_ID=3", "raw_cond": "COUNT_STAGE"}}
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[203, 1, 112, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-010-P＋ - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを＋４する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 10, "raw_cond": "SUM_ENERGY"}}
EFFECT: UNKNOWN(70)(4) -> SELF
```

### Bytecode Sequences
- Ability 1: `[70, 4, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-010-R - ウィーン・マルガレーテ

### Japanese Ability
```text
{{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを＋４する。
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
CONDITION: UNKNOWN(213) {{"MIN": 10, "raw_cond": "SUM_ENERGY"}}
EFFECT: UNKNOWN(70)(4) -> SELF
```

### Bytecode Sequences
- Ability 1: `[70, 4, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-011-P＋ - 鬼塚冬毬

### Japanese Ability
```text
{{toujyou.png|登場}}「鬼塚冬毬」以外の『Liella!』のメンバー1人をステージから控え室に置いてもよい：自分の控え室から、これにより控え室に置いたメンバーカードを1枚、そのメンバーがいたエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(57)(1) -> PLAYER {{"repro_area": true, "raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 112, 536870912, 0, 3, 3, 0, 0, 0, 58, 1, 0, 0, 4, 312, 0, 0, 0, 48, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-011-R - 鬼塚冬毬

### Japanese Ability
```text
{{toujyou.png|登場}}「鬼塚冬毬」以外の『Liella!』のメンバー1人をステージから控え室に置いてもよい：自分の控え室から、これにより控え室に置いたメンバーカードを1枚、そのメンバーがいたエリアに登場させる。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(57)(1) -> PLAYER {{"repro_area": true, "raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[65, 1, 112, 536870912, 0, 3, 3, 0, 0, 0, 58, 1, 0, 0, 4, 312, 0, 0, 0, 48, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-012-N - 澁谷かのん

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-pb1-013-N - 唐 可可

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-pb1-014-N - 嵐 千砂都

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-pb1-015-N - 平安名すみれ

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『CatChu!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "UNIT_CATCHU", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 5, 1376257, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-016-N - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『KALEIDOSCORE』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "UNIT_KALEIDOSCORE", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 5, 1507329, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-017-N - 桜小路きな子

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『5yncri5e!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(5) -> PLAYER {{"filter": "UNIT_SYNCRISE", "choose_count": 1}} (Optional)
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 1, 0, 0, 0, 41, 5, 1638401, 536870912, 65540, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-018-N - 米女メイ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-019-N - 若菜四季

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-pb1-020-N - 鬼塚夏美

### Japanese Ability
```text
{{jidou.png|自動}}このメンバーがエリアを移動するたび、カードを1枚引く。
(対戦相手のカードの効果でも発動する。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LEAVES
EFFECT: MOVE_MEMBER(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-021-N - ウィーン・マルガレーテ

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[17, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-022-N - 鬼塚冬毬

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-pb1-023-L - ディストーション

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに名前の異なる『CatChu!』のメンバーが2人以上いる場合、エネルギーを6枚までアクティブにする。その後、自分のエネルギーがすべてアクティブ状態の場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {UNIT="CATCHU", {"zone": "STAGE", "comparison": "GE", "val": "2", "raw_cond": "COUNT_MEMBER"}}
EFFECT: UNKNOWN(81)(6) -> PLAYER

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=SCORE_RULE, {"rule": "ALL_ENERGY_ACTIVE"}}; META_RULE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[203, 2, 1376256, 8388608, 52, 81, 6, 0, 0, 4, 1, 0, 0, 0, 0]`
- Ability 2: `[29, 1, 8, 0, 4, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-024-L - ニュートラル

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージに名前の異なる『KALEIDOSCORE』のメンバーが2人以上いる場合、このカードのスコアを＋１する。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(203) {{"FILTER": "UNIT_KALEIDOSCORE, UNIQUE_NAMES", "GE": 2, "val": "PLAYER", "raw_cond": "COUNT_MEMBER"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[203, 2, 1507328, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-025-L - Jellyfish

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"filter": "UNIT_SYNCRISE, STATUS=ENTERED_OR_MOVED_THIS_TURN", "destination": "count_val", "raw_effect": "COUNT_MEMBER", "raw_val": "PLAYER"}}; ACTIVATE_MEMBER(1) -> SELF {{"raw_effect": "REDUCE_HEART_COST", "raw_val": "COUNT_VAL"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1638401, 0, 4, 29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-pb1-026-L - Jump Into the New World

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-pb1-026-L＋ - Jump Into the New World

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-001-SD - 澁谷かのん

### Japanese Ability
```text
{{toujyou.png|登場}}自分のエネルギー6枚につき、カードを1枚引く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {{"destination": "count_val", "raw_effect": "COUNT_ENERGY", "raw_val": "PLAYER"}}; ACTIVATE_MEMBER(6) -> PLAYER {{"destination": "draw_count", "raw_effect": "DIV_VAL"}}; MOVE_MEMBER(1) -> PLAYER {{"raw_val": "DRAW_COUNT"}}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 0, 0, 4, 29, 6, 0, 0, 4, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-002-SD - 唐 可可

### Japanese Ability
```text
{{toujyou.png|登場}}手札からコスト4以下の『Liella!』のメンバーカードを1枚ステージに登場させてもよい。
（この効果で既にメンバーがいるエリアにも登場できる。ただし、このターンにステージに登場したメンバーがいるエリアには登場できない。）
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(74)(1) -> PLAYER {FROM=HAND, {"filter": "GROUP_ID=3, COST_LE=4"}} (Optional); UNKNOWN(57)(1) -> PLAYER {{"raw_val": "TARGET"}}
```

### Bytecode Sequences
- Ability 1: `[74, 1, -922746767, 536870912, 393220, 57, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-003-SD - 嵐 千砂都

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
EFFECT: SWAP_CARDS(5) -> SELF {{"duration": "UNTIL_LIVE_END"}}
```

### Bytecode Sequences
- Ability 1: `[58, 2, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 11, 5, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-004-SD - 平安名すみれ

### Japanese Ability
```text
{{toujyou.png|登場}}ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(60)(0) -> PLAYER {{"trigger": "CONSTANT", "condition": "IS_ON_STAGE", "effect": "BOOST_SCORE(1"}}
```

### Bytecode Sequences
- Ability 1: `[60, 0, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-005-SD - 葉月 恋

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(3)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-006-SD - 桜小路きな子

### Japanese Ability
```text
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
COST: SACRIFICE_SELF(0)
EFFECT: ORDER_DECK(1) -> CARD_HAND {{"source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[15, 1, 0, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-007-SD - 米女メイ

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『Liella!』のメンバーカードを1枚手札に加える。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1) -> CARD_HAND {{"filter": "GROUP_ID=3", "source": "discard"}}
```

### Bytecode Sequences
- Ability 1: `[64, 2, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 17, 1, 112, 14680064, 458758, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-008-SD - 若菜四季

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-009-SD - 鬼塚夏美

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーが9枚以上ある場合、自分のデッキの上からカードを5枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
CONDITION: UNKNOWN(213) {{"GE": 9, "val": "PLAYER", "raw_cond": "COUNT_ENERGY"}}
EFFECT: UNKNOWN(41)(5) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[213, 9, 0, 0, 48, 64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 5, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-010-SD - ウィーン・マルガレーテ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-011-SD - 鬼塚冬毬

### Japanese Ability
```text
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
(Once per turn)
COST: ENERGY(2)
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-012-SD - 澁谷かのん

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-013-SD - 唐 可可

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-014-SD - 嵐 千砂都

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-015-SD - 平安名すみれ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-016-SD - 葉月 恋

### Japanese Ability
```text
{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: SET_SCORE(1) -> PLAYER
```

### Bytecode Sequences
- Ability 1: `[58, 1, 0, 536870912, 6, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 23, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-017-SD - 桜小路きな子

### Japanese Ability
```text
{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。
```

### Regenerated Pseudocode
```text
TRIGGER: ON_PLAY
EFFECT: UNKNOWN(41)(3) -> CARD_HAND {{"choose_count": 1}}
```

### Bytecode Sequences
- Ability 1: `[64, 1, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 48, 41, 3, 0, 0, 65542, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-018-SD - 米女メイ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-019-SD - 若菜四季

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-020-SD - 鬼塚夏美

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-021-SD - ウィーン・マルガレーテ

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-022-SD - 鬼塚冬毬

### Japanese Ability
```text

```

### Regenerated Pseudocode
```text

```

### Bytecode Sequences

---

## PL!SP-sd1-023-SD - WE WILL!!

### Japanese Ability
```text
(エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)
```

### Regenerated Pseudocode
```text
TRIGGER: ACTIVATED
```

### Bytecode Sequences
- Ability 1: `[1, 0, 0, 0, 0]`

---

## PL!SP-sd1-024-SD - シェキラ☆☆☆

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-025-SD - 未来は風のように

### Japanese Ability
```text
(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)
```

### Regenerated Pseudocode
```text
TRIGGER: CONSTANT
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {TYPE=ALL_BLADE_AS_ANY_HEART}
```

### Bytecode Sequences
- Ability 1: `[29, 1, 1, 0, 4, 1, 0, 0, 0, 0]`

---

## PL!SP-sd1-026-SD - 私のSymphony 〜澁谷かのんVer.〜

### Japanese Ability
```text
{{live_start.png|ライブ開始時}}自分のエネルギーが9枚以上ある場合、このカードのスコアを＋１する。

(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)
```

### Regenerated Pseudocode
```text
TRIGGER: ON_LIVE_START
CONDITION: UNKNOWN(213) {{"MIN": 9, "raw_cond": "SUM_ENERGY"}}
EFFECT: META_RULE(1) -> SELF
```

### Bytecode Sequences
- Ability 1: `[213, 9, 0, 0, 48, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

---

