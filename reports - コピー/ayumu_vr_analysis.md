# Card Report: PL!N-bp5-001-AR

## IDs
- **Engine Packed ID**: `751`
- **Logic ID**: `751`
- **Variant Index**: `0`

## Metadata (Source: cards.json)
- **Name**: 上原歩夢
- **Card No**: PL!N-bp5-001-AR
- **Ability (JP)**:
```
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードが持つブレードハートの中に[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}のうち、3種類以上ある場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。6種類以上ある場合、さらにライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```
- **Pseudocode (Raw)**: `None`

### Pseudocode (Consolidated DB)
```
{'pseudocode': 'TRIGGER: ON_REVEAL (Once per turn)\nCONDITION: COUNT_BLADE_HEART_TYPES(3) {FROM=REVEAL_ZONE}\nEFFECT: ADD_HEARTS(1) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}\nCONDITION: COUNT_BLADE_HEART_TYPES(6) {FROM=REVEAL_ZONE}\nEFFECT: GRANT_ABILITY(SELF) {TRIGGER="CONSTANT", EFFECT="BOOST_SCORE(1)", DURATION="UNTIL_LIVE_END"}', 'ids': ['PL!N-bp5-001-AR']}
```

## Cross-References
### QA Rulings: None
### Shared Ability Cards (3)
`PL!N-bp5-001-P`, `PL!N-bp5-001-R＋`, `PL!N-bp5-001-SEC`
### Rust Engine Tests (0)

> [!CAUTION]
> No known Rust tests cover this card, its ability peers, or its QA items.

## Compiled Logic (Source: cards_compiled.json)
- **Name (Compiled)**: 上原歩夢

### Ability 0
- **Trigger**: `9`
- **Bytecode**: `[302, 3, 0, 0, 48, 12, 1, 1, 0, 4, 302, 6, 0, 0, 48, 60, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

#### Decoded Bytecode
```
  00: CHECK_COUNT_BLADE_HEART_TYPES | v(Val):3, a(Filter):[None], s(Comp):GE (>=), s(Area):None(0), s(Raw_Slot):48
  05: ADD_HEARTS           | v(Count):1, a(Attr/Source):1, s(Area):None, s(Slot/Target):Context Area (Raw:4)
  10: CHECK_COUNT_BLADE_HEART_TYPES | v(Val):6, a(Filter):[None], s(Comp):GE (>=), s(Area):None(0), s(Raw_Slot):48
  15: GRANT_ABILITY        | v(Unused):1, a(Source_CID):0, s(Target_Slot):Context Area
  20: RETURN               | v=0, a=0, s=0

--- BYTECODE LEGEND ---
Zones: 0:Deck, 1:Deck Top, 2:Deck Bottom, 3:Energy Zone, 4:Stage, 6:Hand, 7:Discard, 8:Deck (Generic), 13:Success Live Pile, 15:Yell Cards
Slots: 0:Left Slot, 1:Center Slot, 2:Right Slot, 4:Context Area, 6:Hand (Generic), 7:Discard (Generic), 10:Choice Target
Comparisons: 0:EQ (==), 1:GT (>), 2:LT (<), 3:GE (>=), 4:LE (<=)
```

### Raw Compiled JSON Data
```json
{
  "card_id": 751,
  "card_no": "PL!N-bp5-001-AR",
  "name": "上原歩夢",
  "cost": 5,
  "hearts": [
    0,
    0,
    0,
    0,
    0,
    0,
    0
  ],
  "blade_hearts": [
    0,
    0,
    0,
    0,
    0,
    0,
    0
  ],
  "blades": 4,
  "groups": [
    2
  ],
  "units": [
    7
  ],
  "abilities": [
    {
      "raw_text": "TRIGGER: ON_REVEAL (Once per turn)\nCONDITION: COUNT_BLADE_HEART_TYPES(3) {FROM=REVEAL_ZONE}\nEFFECT: ADD_HEARTS(1) {HEART_TYPE=1, DURATION=\"UNTIL_LIVE_END\"}\nCONDITION: COUNT_BLADE_HEART_TYPES(6) {FROM=REVEAL_ZONE}\nEFFECT: GRANT_ABILITY(SELF) {TRIGGER=\"CONSTANT\", EFFECT=\"BOOST_SCORE(1)\", DURATION=\"UNTIL_LIVE_END\"}",
      "trigger": 9,
      "effects": [
        {
          "effect_type": 12,
          "value": 1,
          "value_cond": 0,
          "target": 1,
          "params": {
            "heart_type": 1,
            "duration": "UNTIL_LIVE_END"
          },
          "is_optional": false,
          "modal_options": []
        },
        {
          "effect_type": 60,
          "value": 1,
          "value_cond": 0,
          "target": 1,
          "params": {
            "trigger": "CONSTANT",
            "effect": "BOOST_SCORE(1)",
            "duration": "UNTIL_LIVE_END"
          },
          "is_optional": false,
          "modal_options": []
        }
      ],
      "conditions": [
        {
          "type": 302,
          "params": {
            "FROM": "REVEAL_ZONE",
            "val": "3",
            "raw_cond": "COUNT_BLADE_HEART_TYPES"
          },
          "is_negated": false,
          "value": 3,
          "attr": 0
        }
      ],
      "costs": [],
      "modal_options": [],
      "is_once_per_turn": true,
      "bytecode": [
        302,
        3,
        0,
        0,
        48,
        12,
        1,
        1,
        0,
        4,
        302,
        6,
        0,
        0,
        48,
        60,
        1,
        0,
        0,
        4,
        1,
        0,
        0,
        0,
        0
      ],
      "instructions": [
        {
          "type": 302,
          "params": {
            "FROM": "REVEAL_ZONE",
            "val": "3",
            "raw_cond": "COUNT_BLADE_HEART_TYPES"
          },
          "is_negated": false,
          "value": 3,
          "attr": 0
        },
        {
          "effect_type": 12,
          "value": 1,
          "value_cond": 0,
          "target": 1,
          "params": {
            "heart_type": 1,
            "duration": "UNTIL_LIVE_END"
          },
          "is_optional": false,
          "modal_options": []
        },
        {
          "type": 302,
          "params": {
            "FROM": "REVEAL_ZONE",
            "val": "6",
            "raw_cond": "COUNT_BLADE_HEART_TYPES"
          },
          "is_negated": false,
          "value": 6,
          "attr": 0
        },
        {
          "effect_type": 60,
          "value": 1,
          "value_cond": 0,
          "target": 1,
          "params": {
            "trigger": "CONSTANT",
            "effect": "BOOST_SCORE(1)",
            "duration": "UNTIL_LIVE_END"
          },
          "is_optional": false,
          "modal_options": []
        }
      ],
      "card_no": "PL!N-bp5-001-AR",
      "requires_selection": false,
      "choice_flags": 0,
      "choice_count": 0,
      "pseudocode": "TRIGGER: ON_REVEAL (Once per turn)\nCONDITION: COUNT_BLADE_HEART_TYPES(3) {FROM=REVEAL_ZONE}\nEFFECT: ADD_HEARTS(1) {HEART_TYPE=1, DURATION=\"UNTIL_LIVE_END\"}\nCONDITION: COUNT_BLADE_HEART_TYPES(6) {FROM=REVEAL_ZONE}\nEFFECT: GRANT_ABILITY(SELF) {TRIGGER=\"CONSTANT\", EFFECT=\"BOOST_SCORE(1)\", DURATION=\"UNTIL_LIVE_END\"}",
      "filters": [
        {
          "target_player": 0,
          "card_type": 0,
          "group_enabled": false,
          "group_id": 0,
          "is_tapped": false,
          "has_blade_heart": false,
          "not_has_blade_heart": false,
          "unique_names": false,
          "unit_enabled": false,
          "unit_id": 0,
          "value_enabled": false,
          "value_threshold": 0,
          "is_le": false,
          "is_cost_type": false,
          "color_mask": 0,
          "char_id_1": 0,
          "char_id_2": 0,
          "zone_mask": 0,
          "special_id": 0,
          "is_setsuna": false,
          "compare_accumulated": false,
          "is_optional": false,
          "keyword_energy": false,
          "keyword_member": false
        },
        {
          "target_player": 0,
          "card_type": 0,
          "group_enabled": false,
          "group_id": 0,
          "is_tapped": false,
          "has_blade_heart": false,
          "not_has_blade_heart": false,
          "unique_names": false,
          "unit_enabled": false,
          "unit_id": 0,
          "value_enabled": false,
          "value_threshold": 0,
          "is_le": false,
          "is_cost_type": false,
          "color_mask": 0,
          "char_id_1": 0,
          "char_id_2": 0,
          "zone_mask": 0,
          "special_id": 0,
          "is_setsuna": false,
          "compare_accumulated": false,
          "is_optional": false,
          "keyword_energy": false,
          "keyword_member": false
        }
      ]
    }
  ],
  "img_path": "cards_webp/PL!N-bp5-001-AR.webp",
  "rare": "AR",
  "ability_text": "TRIGGER: ON_REVEAL (Once per turn)\nCONDITION: COUNT_BLADE_HEART_TYPES(3) {FROM=REVEAL_ZONE}\nEFFECT: ADD_HEARTS(1) {HEART_TYPE=1, DURATION=\"UNTIL_LIVE_END\"}\nCONDITION: COUNT_BLADE_HEART_TYPES(6) {FROM=REVEAL_ZONE}\nEFFECT: GRANT_ABILITY(SELF) {TRIGGER=\"CONSTANT\", EFFECT=\"BOOST_SCORE(1)\", DURATION=\"UNTIL_LIVE_END\"}",
  "original_text": "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードが持つブレードハートの中に[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}のうち、3種類以上ある場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。6種類以上ある場合、さらにライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。",
  "original_text_en": "",
  "volume_icons": 0,
  "draw_icons": 0,
  "semantic_flags": 24,
  "ability_flags": 9,
  "synergy_flags": 0,
  "cost_flags": 0,
  "faq": []
}
```
