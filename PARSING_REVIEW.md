# Ability Parsing Review

## Summary
- Total abilities: 598
- With issues: 298 (50%)
- Without issues: 300

## Issue Categories

### 1. Missing Cost (Expected for trigger abilities)
Many abilities marked as "Missing cost" are actually trigger abilities (登場, ライブ開始時, ライブ成功時, 常時, 自動) that don't have costs by design. These are **not issues**.

### 2. Cost has 'してもよい' but missing optional flag
**Real Issue**: Some costs contain "してもよい" but the optional flag is not set.

**Affected abilities**:
- #7: "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい"
- #16: "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい"

**Fix needed**: Add "ウェイトにしてもよい" to the optional flag check in cost_parser.py (already done for ability #50)

### 3. Raw text in conditions
**Real Issue**: Some conditions are not being parsed and are stored as raw text.

**Affected abilities**:
- #17: "このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。"

**Fix needed**: Improve condition parsing for activation restriction patterns.

### 4. Raw text in actions
**Real Issue**: Some actions are not being parsed and are stored as raw text.

**Affected abilities**:
- #594: "カードを1枚引いてもよい"

**Fix needed**: Improve action parsing for optional draw patterns.

### 5. Non-standard action types
**Note**: Some action types like "place_card" may be valid for specific card types.

**Affected abilities**:
- #8: Uses "place_card" for energy card placement

## Priority Fixes

1. **Fix optional flag for "ウェイトにしてもよい"** (abilities #7, #16)
2. **Fix condition parsing for activation restrictions** (ability #17)
3. **Fix action parsing for optional draw** (ability #594)
