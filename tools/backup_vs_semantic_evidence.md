# Evidence: Backup vs Semantic Extraction Differences

## Data Sources
- **Backup**: `launcher/static_content/data/ability_frame_source.json.backup` (598 abilities)
- **Semantic**: `data/abilities_extracted_from_cards.json` (598 unique_abilities)
- **Converted**: `data/ability_frame_source.json` (598 abilities - output of converter)

## Key Finding: Same Count, Different Content

### Ability Count Comparison
- Backup: 598 abilities
- Semantic: 598 unique_abilities
- Converted: 598 abilities

### Text Overlap (Normalized)
- Only in backup (normalized): 113
- Only in semantic (normalized): 113
- Common (normalized): 485

## Concrete Example: BiBi Tap Ability

### Backup (ability_frame_source.json.backup)
```
primary_text_jp: "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）\n{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。"
trigger: LIVE_START
trigger_id: 2
frames: [IS_CENTER, JUMP_IF_FALSE, SELECT_MEMBER, TAP_MEMBER, ...]
```

### Semantic (abilities_extracted_from_cards.json)
```
full_text: "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）"
triggers: "ライブ開始時, 登場"
cost: {
  "type": "move_cards",
  "source": "stage",
  "destination": "wait",
  "target": "member",
  "optional": true,
  "count": 1,
  "group": "BiBi",
  "position": "center"
}
effect: {
  "condition": {
    "type": "state",
    "value": "active",
    "operator": "=="
  },
  "actions": [
    {
      "action": "note",
      "text": "『BiBi』のメンバー1人をウェイトにしてもよい..."
    }
  ]
}
```

### Analysis of This Example
The semantic extraction HAS this ability with the same text. The triggers are listed as "ライブ開始時, 登場" (comma-separated) instead of the backup's single "LIVE_START" trigger. The effect only contains a "note" action, not the actual tap actions.

## Issue: Effect Actions Missing

The semantic extraction is extracting the text and triggers correctly, but the `effect.actions` array often contains only "note" actions instead of the actual semantic actions (like "member_to_wait", "tap_opponent", etc.).

This means the converter receives:
- Correct text
- Correct triggers
- Correct cost data
- **BUT** incorrect/missing effect actions

The converter can only convert what it receives. If the semantic extraction doesn't extract the actual actions (only "note" placeholders), the converter can't generate the correct frames.

## Conclusion

The converter is working correctly. The problem is in the semantic extraction pipeline (`tools/ability_extraction/`), which is not extracting the actual effect actions - it's only extracting "note" placeholders instead of the real semantic actions like "member_to_wait", "draw_cards", etc.
