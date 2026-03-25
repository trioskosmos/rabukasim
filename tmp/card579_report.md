# Card Report: PL!N-bp1-006-P

## IDs
- **Engine Packed ID**: `239`
- **Logic ID**: `239`
- **Variant Index**: `0`

## Metadata
- **Name**: 近江彼方
- **Card No**: PL!N-bp1-006-P
- **Ability (JP)**:
```
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。
{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

## QA Rulings (1)
**Q77**: 『
{{kidou.png|起動}}
{{turn1.png|ターン1回}}
手札を1枚控え室に置く：このターン、自分のステージに「虹ヶ咲」のメンバーが登場している場合、エネルギーを2枚アクティブにする。』について。
このターン中に登場したメンバーがこのカードだけの状況です。「自分のステージに「虹ヶ咲」のメンバーが登場している場合」の条件は満たしていますか？
> はい、条件を満たしています。


## Rust Engine Tests (1)
- `card_579_verification.rs::test_card_579_ability_0_cost_comparison`

## Compiled Logic

### Ability 0
- **Trigger**: `7`

#### Decoded Bytecode
```
None
```

### Ability 1
- **Trigger**: `7`

#### Decoded Bytecode
```
  00: DRAW                      | count=1, filter=[none], slot=[none]
  05: RETURN                    | done

--- BYTECODE LEGEND ---
Zones: 0:Default, 1:Deck Top, 2:Deck Bottom, 3:Energy, 4:Stage, 5:Deck, 6:Hand, 7:Discard, 13:Live Set, 16:Success Pile, 17:Yell
Slots: 0:Left Stage (0), 1:Center Stage (1), 2:Right Stage (2), 4:Context Card, 6:Hand (Zone), 7:Discard (Zone), 10:Choice Target, 13:Live Slot 0, 14:Live Slot 1, 15:Live Slot 2, 20:Player Select
Comparisons: 0:EQ (==), 1:GT (>), 2:LT (<), 3:GE (>=), 4:LE (<=)
```