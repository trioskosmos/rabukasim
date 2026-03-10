# Card Report: PL!-pb1-018-R

## IDs
- **Engine Packed ID**: `4199`
- **Logic ID**: `103`
- **Variant Index**: `1`

## Metadata (Source: cards.json)
- **Name**: 矢澤にこ
- **Card No**: PL!-pb1-018-R
- **Ability (JP)**:
```
{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）
```
- **Pseudocode (Raw)**: `None`

### Pseudocode (Consolidated DB)
```
{'pseudocode': 'TRIGGER: ON_PLAY\nEFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"}; PREVENT_PLAY_TO_SLOT -> SLOT \nEFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2", DESTINATION="STAGE_EMPTY", STATE="WAIT"} -> OPPONENT; PREVENT_PLAY_TO_SLOT -> SLOT', 'cards': ['PL!-pb1-018-P+', 'PL!-pb1-018-P＋', 'PL!-pb1-018-R']}
```

## Cross-References
### QA Rulings (4)
**Q181**: 『
{{toujyou.png|登場}}
自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）』について、
この能力で登場したメンバーカードが何らかの効果で控え室に移動した場合、空いたエリアにメンバーカードを出すことはできますか？
> はい。できます。

**Q170**: 『
{{toujyou.png|登場}}
自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）』について、この能力でお互いに
{{toujyou.png|登場}}
能力を持つメンバーカードを登場させました。どちらから能力を使用できますか？
> 通常フェイズを行っているプレイヤーから順番に
{{toujyou.png|登場}}
能力を使用します。

**Q169**: 『
{{toujyou.png|登場}}
自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）』について、この能力を先行で使用しました。このターン、相手はこのカードの能力で登場させたメンバーカードをバトンタッチに使用することはできますか？
> いいえできません。この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できないため、バトンタッチも使用できません。

**Q168**: 『
{{toujyou.png|登場}}
自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）』について、自分または相手の控え室にコスト2以下のメンバーカードがいない場合、どうなりますか？
> 控え室にコスト2以下のメンバーカードがいないプレイヤーはメンバーカードを登場させずに効果の処理を終了します。

### Shared Ability Cards (1)
`PL!-pb1-018-P＋`
### Rust Engine Tests (1)
- `opcode_missing_tests.rs::test_opcode_prevent_play_to_slot`

## Compiled Logic (Source: cards_compiled.json)
- **Name (Compiled)**: 矢澤にこ

### Ability 0
- **Trigger**: `1`
- **Bytecode**: `[63, 1, 1, 0, 67567620, 71, 1, 0, 0, 4, 63, 1, 2, 0, 67567620, 71, 1, 0, 0, 2, 1, 0, 0, 0, 0]`

#### Decoded Bytecode
```
  00: PLAY_MEMBER_FROM_DISCARD | v=1, a=1, s=67567620
  05: PREVENT_PLAY_TO_SLOT | v=1, a=0, s=4
  10: PLAY_MEMBER_FROM_DISCARD | v=1, a=2, s=67567620
  15: PREVENT_PLAY_TO_SLOT | v=1, a=0, s=2
  20: RETURN               | v=0, a=0, s=0

--- BYTECODE LEGEND ---
Zones: 0:Deck, 1:Deck Top, 2:Deck Bottom, 3:Energy Zone, 4:Stage, 6:Hand, 7:Discard, 8:Deck (Generic), 13:Success Live Pile, 15:Yell Cards
Slots: 0:Left Slot, 1:Center Slot, 2:Right Slot, 4:Context Area, 6:Hand (Generic), 7:Discard (Generic), 10:Choice Target
Comparisons: 0:EQ (==), 1:GT (>), 2:LT (<), 3:GE (>=), 4:LE (<=)
```