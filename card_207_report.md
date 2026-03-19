# Card Report: PL!HS-bp2-020-L

## IDs
- **Engine Packed ID**: `207`
- **Logic ID**: `207`
- **Variant Index**: `0`

## Metadata (Source: cards.json)
- **Name**: Link to the FUTURE
- **Card No**: PL!HS-bp2-020-L
- **Ability (JP)**:
```
{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。
{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを＋２する。
```
- **Pseudocode (Raw)**: `None`

### Pseudocode (Consolidated DB)
```
{'pseudocode': 'TRIGGER: CONSTANT\nEFFECT: ADD_TAG("UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA") -> SELF\n\nTRIGGER: ON_LIVE_START\nEFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="STAGE", FILTER="UNIT_HASUNOSORA, UNIQUE_NAMES"}', 'units': ['CERISE_BOUQUET', 'DOLLCHESTRA', 'MIRA_CRA_PARK'], 'cards': ['PL!HS-bp2-020-L']}
```

## Cross-References
### QA Rulings: None
### Shared Ability Cards (0)
*Unique ability.*
### Rust Engine Tests (0)

> [!CAUTION]
> No known Rust tests cover this card, its ability peers, or its QA items.

## Compiled Logic (Source: cards_compiled.json)
- **Name (Compiled)**: Link to the FUTURE

### Ability 0
- **Trigger**: `6`
- **Bytecode**: `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]`

#### Decoded Bytecode
```
  00: META_RULE                 | type=CHEER_MOD, value=1, slot=[target=Context Card]
  05: RETURN                    | done

--- BYTECODE LEGEND ---
Zones: 0:Default, 1:Deck Top, 2:Deck Bottom, 3:Energy, 4:Stage, 5:Deck, 6:Hand, 7:Discard, 13:Live Set, 16:Success Pile, 17:Yell
Slots: 0:Left Stage (0), 1:Center Stage (1), 2:Right Stage (2), 4:Context Card, 6:Hand (Zone), 7:Discard (Zone), 10:Choice Target, 13:Live Slot 0, 14:Live Slot 1, 15:Live Slot 2, 20:Player Select
Comparisons: 0:EQ (==), 1:GT (>), 2:LT (<), 3:GE (>=), 4:LE (<=)
```

### Ability 1
- **Trigger**: `2`
- **Normalized Filters**:
```json
[
  {
    "target_player": 1,
    "card_type": 0,
    "group_enabled": false,
    "group_id": 0,
    "is_tapped": false,
    "has_blade_heart": false,
    "not_has_blade_heart": false,
    "unique_names": true,
    "unit_enabled": true,
    "unit_id": 13,
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
    "keyword_member": false,
    "packed_attr": 1802241,
    "packed_attr_hex": "0x00000000001B8001",
    "summary": "target=self, unit=13, unique_names"
  },
  {
    "target_player": 1,
    "card_type": 0,
    "group_enabled": false,
    "group_id": 0,
    "is_tapped": false,
    "has_blade_heart": false,
    "not_has_blade_heart": false,
    "unique_names": true,
    "unit_enabled": true,
    "unit_id": 13,
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
    "keyword_member": false,
    "packed_attr": 1802241,
    "packed_attr_hex": "0x00000000001B8001",
    "summary": "target=self, unit=13, unique_names"
  }
]
```
- **Bytecode**: `[16, 2, 1802241, 268435456, 268487424, 1, 0, 0, 0, 0]`

#### Decoded Bytecode
```
  00: BOOST_SCORE               | value=2, filter=[target=self, group=Hasunosora, unique_names, compare_accumulated], slot=[multiplier_source=STAGE, dynamic]
  05: RETURN                    | done

--- BYTECODE LEGEND ---
Zones: 0:Default, 1:Deck Top, 2:Deck Bottom, 3:Energy, 4:Stage, 5:Deck, 6:Hand, 7:Discard, 13:Live Set, 16:Success Pile, 17:Yell
Slots: 0:Left Stage (0), 1:Center Stage (1), 2:Right Stage (2), 4:Context Card, 6:Hand (Zone), 7:Discard (Zone), 10:Choice Target, 13:Live Slot 0, 14:Live Slot 1, 15:Live Slot 2, 20:Player Select
Comparisons: 0:EQ (==), 1:GT (>), 2:LT (<), 3:GE (>=), 4:LE (<=)
```

### Raw Compiled JSON Data
```json
{
  "card_id": 207,
  "card_no": "PL!HS-bp2-020-L",
  "name": "Link to the FUTURE",
  "score": 0,
  "required_hearts": [
    2,
    0,
    0,
    2,
    2,
    0,
    8
  ],
  "abilities": [
    {
      "raw_text": "TRIGGER: CONSTANT\nEFFECT: ADD_TAG(\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\") -> SELF",
      "trigger": 6,
      "effects": [
        {
          "effect_type": 29,
          "value": 1,
          "value_cond": 0,
          "target": 0,
          "params": {
            "chain_destinations": [
              "SELF"
            ],
            "destination": "self",
            "tag": "\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\"",
            "raw_val": "\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\""
          },
          "is_optional": false,
          "modal_options": [],
          "runtime_opcode": 29,
          "runtime_value": 1,
          "runtime_attr": 0,
          "runtime_slot": 4
        }
      ],
      "conditions": [],
      "costs": [],
      "modal_options": [],
      "is_once_per_turn": false,
      "bytecode": [
        29,
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
      "card_no": "PL!HS-bp2-020-L",
      "requires_selection": false,
      "choice_flags": 0,
      "choice_count": 0,
      "pseudocode": "TRIGGER: CONSTANT\nEFFECT: ADD_TAG(\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\") -> SELF",
      "filters": [],
      "option_names": [],
      "semantic_form": {
        "semantic_version": 1,
        "bytecode_layout_version": 1,
        "bytecode_layout_name": "fixed5x32-v1",
        "trigger": "CONSTANT",
        "effects": [
          {
            "type": "META_RULE",
            "value": 1,
            "target": "SELF",
            "params": {
              "chain_destinations": [
                "SELF"
              ],
              "destination": "self",
              "tag": "\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\"",
              "raw_val": "\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\""
            },
            "conditions": [],
            "optional": false,
            "description": ""
          }
        ],
        "conditions": [],
        "costs": [],
        "once_per_turn": false,
        "description": "TRIGGER: CONSTANT\nEFFECT: ADD_TAG(\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\") -> SELF",
        "instructions_summary": "Effect(META_RULE)"
      }
    },
    {
      "raw_text": "TRIGGER: ON_LIVE_START\nEFFECT: BOOST_SCORE(2) -> SELF {PER_CARD=\"STAGE\", FILTER=\"UNIT_HASUNOSORA, UNIQUE_NAMES\"}",
      "trigger": 2,
      "effects": [
        {
          "effect_type": 16,
          "value": 2,
          "value_cond": 0,
          "target": 0,
          "params": {
            "per_card": "STAGE",
            "filter": "UNIT_HASUNOSORA, UNIQUE_NAMES",
            "chain_destinations": [
              "SELF"
            ],
            "destination": "self",
            "value_enabled": true,
            "value_threshold": 1
          },
          "is_optional": false,
          "modal_options": [],
          "runtime_opcode": 16,
          "runtime_value": 2,
          "runtime_attr": 1152921504608649217,
          "runtime_slot": 268487424
        }
      ],
      "conditions": [],
      "costs": [],
      "modal_options": [],
      "is_once_per_turn": false,
      "bytecode": [
        16,
        2,
        1802241,
        268435456,
        268487424,
        1,
        0,
        0,
        0,
        0
      ],
      "card_no": "PL!HS-bp2-020-L",
      "requires_selection": false,
      "choice_flags": 0,
      "choice_count": 0,
      "pseudocode": "TRIGGER: ON_LIVE_START\nEFFECT: BOOST_SCORE(2) -> SELF {PER_CARD=\"STAGE\", FILTER=\"UNIT_HASUNOSORA, UNIQUE_NAMES\"}",
      "filters": [
        {
          "target_player": 1,
          "card_type": 0,
          "group_enabled": false,
          "group_id": 0,
          "is_tapped": false,
          "has_blade_heart": false,
          "not_has_blade_heart": false,
          "unique_names": true,
          "unit_enabled": true,
          "unit_id": 13,
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
          "keyword_member": false,
          "packed_attr": 1802241,
          "packed_attr_hex": "0x00000000001B8001",
          "summary": "target=self, unit=13, unique_names"
        },
        {
          "target_player": 1,
          "card_type": 0,
          "group_enabled": false,
          "group_id": 0,
          "is_tapped": false,
          "has_blade_heart": false,
          "not_has_blade_heart": false,
          "unique_names": true,
          "unit_enabled": true,
          "unit_id": 13,
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
          "keyword_member": false,
          "packed_attr": 1802241,
          "packed_attr_hex": "0x00000000001B8001",
          "summary": "target=self, unit=13, unique_names"
        }
      ],
      "option_names": [],
      "semantic_form": {
        "semantic_version": 1,
        "bytecode_layout_version": 1,
        "bytecode_layout_name": "fixed5x32-v1",
        "trigger": "ON_LIVE_START",
        "effects": [
          {
            "type": "BOOST_SCORE",
            "value": 2,
            "target": "SELF",
            "params": {
              "per_card": "STAGE",
              "filter": "UNIT_HASUNOSORA, UNIQUE_NAMES",
              "chain_destinations": [
                "SELF"
              ],
              "destination": "self",
              "value_enabled": true,
              "value_threshold": 1
            },
            "conditions": [],
            "optional": false,
            "description": ""
          }
        ],
        "conditions": [],
        "costs": [],
        "once_per_turn": false,
        "description": "TRIGGER: ON_LIVE_START\nEFFECT: BOOST_SCORE(2) -> SELF {PER_CARD=\"STAGE\", FILTER=\"UNIT_HASUNOSORA, UNIQUE_NAMES\"}",
        "instructions_summary": "Effect(BOOST_SCORE)"
      }
    }
  ],
  "groups": [
    4
  ],
  "units": [
    13,
    14,
    15
  ],
  "img_path": "cards_webp/PL!HS-bp2-020-L.webp",
  "rare": "L",
  "ability_text": "",
  "original_text": "{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。\n{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを＋２する。",
  "original_text_en": "[Continuous] This card is treated as 'Cerise Bouquet', 'DOLLCHESTRA', and 'Mira-Cra Park!' in all areas.\n[Live Start] Live Score +2 for this card for each 'Hasunosora' member with a different name on your stage.",
  "volume_icons": 0,
  "draw_icons": 0,
  "semantic_flags": 0,
  "synergy_flags": 0,
  "blade_hearts": [
    0,
    0,
    0,
    0,
    0,
    0,
    1
  ]
}
```