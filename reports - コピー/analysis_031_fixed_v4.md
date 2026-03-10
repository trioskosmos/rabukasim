# Card Report: PL!-pb1-031-L

## IDs
- **Engine Packed ID**: `111`
- **Logic ID**: `111`
- **Variant Index**: `0`

## Metadata (Source: cards.json)
- **Name**: 輝夜の城で踊りたい
- **Card No**: PL!-pb1-031-L
- **Ability (JP)**:
```
{{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：エールにより公開された自分のカードの中から、『μ's』のメンバーカードを1枚手札に加える。
```
- **Pseudocode (Raw)**: `None`

### Manual Pseudocode (Override)
```
TRIGGER: ON_LIVE_SUCCESS
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(1) {FILTER="GROUP_ID=0", SOURCE="YELL"} -> CARD_HAND
```

## Compiled Logic (Source: cards_compiled.json)
- **Name (Compiled)**: 輝夜の城で踊りたい

### Ability 0
- **Trigger**: `3`
- **Bytecode**: `[58, 1, 2, 6, 41, 1, 61456, 6, 1, 0, 0, 0]`

#### Decoded Bytecode
```
  00: MOVE_TO_DISCARD      | v=1, a=2, s=6
  04: LOOK_AND_CHOOSE      | Reveal:1, Pick:0, Filter:[Group:0], Source:15, Target:6
  08: RETURN               | v=0, a=0, s=0
```