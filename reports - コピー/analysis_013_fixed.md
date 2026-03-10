# Card Report: PL!-bp3-013-N

## IDs
- **Engine Packed ID**: `36`
- **Logic ID**: `36`
- **Variant Index**: `0`

## Metadata (Source: cards.json)
- **Name**: 園田海未
- **Card No**: PL!-bp3-013-N
- **Ability (JP)**:
```
{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分の成功ライブカード置き場にあるカード1枚につき、選んだハートを1つ得る。
```
- **Pseudocode (Raw)**: `None`

### Manual Pseudocode (Override)
```
TRIGGER: ON_LIVE_START
EFFECT: SELECT_MODE(1)
  OPTION: ピンク | EFFECT: ADD_HEARTS(1) {HEART_TYPE=0, PER_CARD="SUCCESS_LIVE"}
  OPTION: イエロー | EFFECT: ADD_HEARTS(1) {HEART_TYPE=2, PER_CARD="SUCCESS_LIVE"}
  OPTION: パープル | EFFECT: ADD_HEARTS(1) {HEART_TYPE=5, PER_CARD="SUCCESS_LIVE"}
```

## Compiled Logic (Source: cards_compiled.json)
- **Name (Compiled)**: 園田海未

### Ability 0
- **Trigger**: `2`
- **Bytecode**: `[30, 3, 0, 0, 2, 3, 0, 0, 2, 4, 0, 0, 2, 5, 0, 0, 12, 1, 0, 1, 2, 5, 0, 0, 12, 1, 0, 1, 2, 3, 0, 0, 12, 1, 0, 1, 2, 1, 0, 0, 1, 0, 0, 0]`

#### Decoded Bytecode
```
  00: SELECT_MODE          | v=3, a=0, s=0
  04: JUMP                 | v=3, a=0, s=0
  08: JUMP                 | v=4, a=0, s=0
  12: JUMP                 | v=5, a=0, s=0
  16: ADD_HEARTS           | v=1, a=0, s=1
  20: JUMP                 | v=5, a=0, s=0
  24: ADD_HEARTS           | v=1, a=0, s=1
  28: JUMP                 | v=3, a=0, s=0
  32: ADD_HEARTS           | v=1, a=0, s=1
  36: JUMP                 | v=1, a=0, s=0
  40: RETURN               | v=0, a=0, s=0
```