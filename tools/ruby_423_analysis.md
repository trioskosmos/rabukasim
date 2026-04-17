# Ruby 423 (PL!S-bp2-009-P | 黒澤ルビィ) Analysis

## Card Information
- **Card Number**: PL!S-bp2-009-P
- **Name**: 黒澤ルビィ (Kurosawa Ruby)
- **Card ID**: 532 (in cards_compiled.json)
- **Note**: card_id 423 is 上原歩夢, not Ruby

## Ability Text
```
{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。
```

Translation: "ACTIVATED: Move this member from stage to discard pile: Add 1 live card from your discard pile to your hand."

## Three Forms Comparison

### 1. Backup (ability_frame_source.json.backup)
```json
{
  "trigger": "ACTIVATED",
  "trigger_id": 7,
  "frames": [
    {
      "op": "MOVE_TO_DISCARD",
      "frame_index": 0,
      "value": 1,
      "slot": {
        "target_slot": "CONTEXT",
        "source_zone": "STAGE",
        "dest_zone": "DISCARD"
      }
    },
    {
      "op": "RECOVER_LIVE",
      "frame_index": 1,
      "value": 1,
      "slot": {
        "target_slot": "HAND",
        "source_zone": "DISCARD"
      }
    },
    {
      "op": "RETURN",
      "frame_index": 2
    }
  ]
}
```

### 2. Semantic (abilities_extracted_from_cards.json)
```json
{
  "full_text": "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。",
  "triggers": "起動",
  "cost": {
    "type": "move_cards",
    "source": "stage",
    "destination": "waitroom",
    "target": "this_member",
    "optional": false,
    "count": 1,
    "text": "このメンバーをステージから控え室に置く"
  },
  "costless": false,
  "effect": {
    "source": "waitroom",
    "text": "自分の控え室からライブカードを1枚手札に加える。",
    "trigger": "起動",
    "count": 1,
    "card_type": "live_card",
    "actions": [
      {
        "action": "add_to_hand",
        "text": "自分の控え室からライブカードを1枚手札に加える。",
        "source": "waitroom",
        "count": 1,
        "card_type": "live_card",
        "trigger": "起動"
      }
    ]
  }
}
```

### 3. Converted (ability_frame_source.json)
```json
{
  "trigger": "ACTIVATED",
  "trigger_id": 7,
  "frames": [
    {
      "op": "MOVE_TO_DISCARD",
      "frame_index": 0,
      "value": 1,
      "slot": {
        "source_zone": "STAGE",
        "dest_zone": "DISCARD",
        "target_slot": "CONTEXT"
      }
    },
    {
      "op": "RECOVER_LIVE",
      "frame_index": 1,
      "value": 1,
      "slot": {
        "source_zone": "DISCARD",
        "target_slot": "HAND"
      }
    },
    {
      "op": "RETURN",
      "frame_index": 2
    }
  ]
}
```

## Analysis

### Semantic Extraction Quality: **GOOD**
- ✅ Cost extracted correctly: `type: "move_cards"`, `source: "stage"`, `destination: "waitroom"`
- ✅ Effect extracted correctly: `action: "add_to_hand"`, `source: "waitroom"`, `card_type: "live_card"`
- ✅ Trigger extracted correctly: `"起動"` (ACTIVATED)
- ✅ No "note" placeholders - real actions are present

### Converter Performance: **CORRECT**
- ✅ Cost frame generated: `MOVE_TO_DISCARD` from `move_cards` cost
- ✅ Effect frame generated: `RECOVER_LIVE` from `add_to_hand` + `card_type: "live_card"` + `source: "waitroom"`
- ✅ Trigger mapped correctly: `"起動"` → `ACTIVATED`
- ✅ Frame structure matches backup (same opcodes, same slot structure)

### Comparison with Backup: **MATCHES**
- ✅ Same trigger (ACTIVATED)
- ✅ Same frame count (3 frames)
- ✅ Same frame opcodes (MOVE_TO_DISCARD, RECOVER_LIVE, RETURN)
- ✅ Same slot structure (source_zone, dest_zone, target_slot)

## Conclusion

**The converter is working correctly for Ruby 423 (PL!S-bp2-009-P).**

The semantic extraction provided complete and accurate data, and the converter generated the correct frames that match the backup exactly.

**Why the Rust test fails:**
The test `test_ruby_423_frame_sequence` is checking `card_id: 423`, but card_id 423 is 上原歩夢 (PL!N-bp5-013-N), not 黒澤ルビィ. The Ruby card has card_id 532. The test has the wrong card_id hardcoded.

**This is a test bug, not a converter bug.**
