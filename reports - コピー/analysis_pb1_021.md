# Card Report: PL!SP-pb1-021-N

## IDs
- **Engine Packed ID**: `604`
- **Logic ID**: `604`
- **Variant Index**: `0`

## Metadata (Source: cards.json)
- **Name**: ウィーン・マルガレーテ
- **Card No**: PL!SP-pb1-021-N
- **Ability (JP)**:
```
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。
```
- **Pseudocode (Raw)**: `None`

### Pseudocode (Consolidated DB)
```
{'pseudocode': 'TRIGGER: ACTIVATED\nCOST: MOVE_TO_DISCARD\nEFFECT: RECOVER_MEMBER(1) -> CARD_HAND', 'cards': ['PL!-pb1-019-N', 'PL!-pb1-025-N', 'PL!-sd1-002-SD', 'PL!HS-PR-014-PR', 'PL!HS-PR-014-RM', 'PL!HS-sd1-015-SD', 'PL!N-bp4-017-N', 'PL!N-bp4-020-N', 'PL!N-sd1-006-SD', 'PL!S-PR-025-PR', 'PL!S-PR-025-RM', 'PL!S-PR-027-PR', 'PL!S-PR-027-RM', 'PL!S-bp2-016-N', 'PL!S-sd1-008-SD', 'PL!SP-bp4-015-N', 'PL!SP-bp4-019-N', 'PL!SP-pb1-021-N']}
```

## Cross-References
### QA Rulings (1)
**Q79**: 『
{{kidou.png|起動}}
このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。』などについて。
このメンバーカードが登場したターンにこの能力を使用しました。このターン中、このメンバーカードが置かれていたエリアにメンバーカードを登場させることはできますか？
> はい、できます。
起動能力のコストでこのメンバーカードがステージから控え室に置かれることにより、このエリアにはこのターンに登場したメンバーカードが置かれていない状態になるため、そのエリアにメンバーカードを登場させることができます。

### Shared Ability Cards (17)
`PL!-sd1-002-SD`, `PL!S-PR-025-PR`, `PL!S-PR-027-PR`, `PL!HS-PR-014-PR`, `PL!N-sd1-006-SD`, `PL!S-bp2-016-N`, `PL!-pb1-019-N`, `PL!-pb1-025-N`, `PL!N-bp4-017-N`, `PL!N-bp4-020-N`, `PL!SP-bp4-015-N`, `PL!SP-bp4-019-N`, `PL!HS-PR-014-RM`, `PL!S-PR-025-RM`, `PL!S-PR-027-RM`, `PL!HS-sd1-015-SD`, `PL!S-sd1-008-SD`
### Rust Engine Tests (3)
- `explain_solver.rs::main`
- `repro_flags.rs::test_q79_area_available_after_activation_cost`
- `repro_flags.rs::test_q91_onlivestart_no_trigger_without_live`

## Compiled Logic (Source: cards_compiled.json)
- **Name (Compiled)**: ウィーン・マルガレーテ

### Ability 0
- **Trigger**: `7`
- **Bytecode**: `[58, 1, 0, 0, 4, 17, 1, 1, 14680064, 458758, 1, 0, 0, 0, 0]`

#### Decoded Bytecode
```
  00: MOVE_TO_DISCARD      | v(Count):1, a(Attr/Source):0, s(Area):None, s(Slot/Target):Context Area (Raw:4)
  05: RECOVER_MEMBER       | v(Count):1, a(Filter):[Unknown(63050394783186945)], s(Source):Discard, s(Dest):Hand (Generic)
  10: RETURN               | v=0, a=0, s=0

--- BYTECODE LEGEND ---
Zones: 0:Deck, 1:Deck Top, 2:Deck Bottom, 3:Energy Zone, 4:Stage, 6:Hand, 7:Discard, 8:Deck (Generic), 13:Success Live Pile, 15:Yell Cards
Slots: 0:Left Slot, 1:Center Slot, 2:Right Slot, 4:Context Area, 6:Hand (Generic), 7:Discard (Generic), 10:Choice Target
Comparisons: 0:EQ (==), 1:GT (>), 2:LT (<), 3:GE (>=), 4:LE (<=)
```
