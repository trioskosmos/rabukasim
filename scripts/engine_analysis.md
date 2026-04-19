# Rust Engine Variable Name Analysis

## What the Engine Actually Reads

### Param Keys (case-insensitive)
- "FILTER", "gt", "lt", "min", "max", "eq", "raw_cond", "RAW_COND"
- "MIN", "MAX", "EQ", "GE", "LE", "count", "COUNT", "threshold", "THRESHOLD", "value", "VALUE"
- "heart_count", "HEART_COUNT", "min_count", "MIN_COUNT", "player", "PLAYER", "keyword", "KEYWORD"
- "multiplier", "heart_type", "raw_effect", "base_value", "divisor", "offset", "type", "rule", "from"

### Slot Keys
- "target_slot": e.g., "CONTEXT", "STAGE_0", "STAGE_1", "HAND"
- "source_zone": e.g., "HAND", "DECK_TOP", "STAGE", "DISCARD"
- "dest_zone": e.g., "DISCARD", "DECK"
- "comparison": e.g., "GE", "LE", "EQ"
- "remainder_zone": e.g., "DISCARD"

### Attr Keys (encoded in filter_attr)
- "target_player": "SELF", "OPPONENT", "BOTH" (encoded as bits 0-1)
- "zone_mask": "Guest+Friend", "ALL", "ANY_STAGE"
- "card_type": "LIVE", "MEMBER", "ENERGY_CARD"
- "group_enabled", "group_id": for group filtering
- "color_mask": for heart color filtering
- "heart_type": "HEART01", "HEART02", etc., or "SELECTED"
- "is_optional": for optional operations
- "compare_accumulated": for accumulated comparisons
- "once_per_turn": for once-per-turn restrictions

### Zone Names (must match engine's Zone enum)
- "DECK", "DECK_TOP", "DECK_BOTTOM"
- "HAND", "STAGE", "DISCARD"
- "SUCCESS_PILE", "ENERGY", "YELL"

## My Generated Frames

My generated frames use the correct keys:
- slot: {'target_slot': 'CONTEXT', 'source_zone': 'STAGE', 'dest_zone': 'DISCARD'}
- attr: {'target_player': 'SELF', 'zone_mask': 'Guest+Friend', 'is_optional': 1}
- params: {'choose_count': 1}

My ZONE_MAP matches the engine's expectations:
- "deck": "DECK"
- "deck_top": "DECK_TOP"
- "deck_bottom": "DECK_BOTTOM"
- "hand": "HAND"
- "stage": "STAGE"
- "discard": "DISCARD"

## Conclusion

Variable names are NOT the issue. My generated frames use the correct keys that the engine reads.

The issue must be elsewhere - likely:
1. Semantic extraction not matching ability text (missing actions, wrong triggers)
2. Frame generation logic not handling specific patterns correctly
3. Value formats or types not matching what engine expects
