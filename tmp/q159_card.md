# Card Report: PL!N-bp1-002-P

## IDs
- **Engine Packed ID**: `235`
- **Logic ID**: `235`
- **Variant Index**: `0`

## Metadata
- **Name**: 中須かすみ
- **Card No**: PL!N-bp1-002-P
- **Ability (JP)**:
```
{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。
{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。
```

## QA Rulings (3)
**Q76**: 『
{{kidou.png|起動}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。』について。
メンバーカードがあるエリアに登場させることはできますか？
> はい、できます。
その場合、指定したエリアに置かれているメンバーカードは控え室に置かれます。
ただし、このターンに登場しているメンバーのいるエリアを指定することはできません。

**Q75**: 『
{{kidou.png|起動}}
{{icon_energy.png|E}}
{{icon_energy.png|E}}
手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。』について。
この能力で登場したメンバーを対象にこのターン手札のメンバーとバトンタッチはできますか？
> いいえ、できません。登場したターン中はバトンタッチはできません。登場した次のターン以降はバトンタッチができます。

**Q63**: 能力の効果でメンバーカードをステージに登場させる場合、能力のコストとは別に、手札から登場させる場合と同様にメンバーカードのコストを支払いますか？
> いいえ、支払いません。効果で登場する場合、メンバーカードのコストは支払いません。


## Rust Engine Tests (3)
- `batch_4_unmapped_qa.rs::test_q159_remote_on_play_cannot_pay_tap_self_cost_from_discard`
- `qa_verification_tests.rs::test_q63_effect_based_member_placement`
- `qa_verification_tests.rs::test_q75_activated_ability_from_discard`

## Compiled Logic

### Ability 0
- **Trigger**: `1`

#### Decoded Bytecode
```
  00: ORDER_DECK                | count=3, filter=[none], slot=[target=Context Card]
  05: NOP                       | value=0, filter=[none], slot=[none]
  10: RETURN                    | done

--- BYTECODE LEGEND ---
Zones: 0:Default, 1:Deck Top, 2:Deck Bottom, 3:Energy, 4:Stage, 5:Deck, 6:Hand, 7:Discard, 13:Live Set, 16:Success Pile, 17:Yell
Slots: 0:Left Stage (0), 1:Center Stage (1), 2:Right Stage (2), 4:Context Card, 6:Hand (Zone), 7:Discard (Zone), 10:Choice Target, 13:Live Slot 0, 14:Live Slot 1, 15:Live Slot 2, 20:Player Select
Comparisons: 0:EQ (==), 1:GT (>), 2:LT (<), 3:GE (>=), 4:LE (<=)
```

### Ability 1
- **Trigger**: `7`

#### Decoded Bytecode
```
None
```