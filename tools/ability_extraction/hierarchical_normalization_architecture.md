# Hierarchical Super Group Normalization Architecture

## Concept

Hierarchical super group normalization consolidates frequently co-occurring variable patterns into parent placeholders while preserving semantic detail through component breakdown.

## Architecture

### Parent Level (Super Groups)
High-level placeholders that represent patterns that always appear together:
- `[card]` - all card-related patterns
- Future: `[location]`, `[entity]`, etc.

### Child Level (Components)
Each super group can break down into its constituent patterns when needed:
- `[card]` → `[card_type]`, `[player_card]`, `[grouped_card]`, `[zone_card]`, etc.
- Component metadata tracked in `modifier_info` for analysis

## Example: Card Score Condition

### Original Japanese Text
```
自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合
```
(If the total score of cards in your success live card area is 6 or higher)

### Hierarchical Template
```
[card][card][opt_mod][value_type:score][opt_mod]合計が[number]以上
```

### Component Breakdown
- First `[card]` → cards in zone (成功ライブカード置き場にあるカード)
- Second `[card]` → cards being scored (カードのスコア)
- `[opt_mod]` → optional modifiers (の)
- `[value_type:score]` → score attribute (スコア)
- `[number]` → threshold value (６)

### Semantic Preservation
The hierarchical structure preserves the specific condition meaning:
- **High level**: `[card][card][opt_mod][value_type:score][opt_mod]合計が[number]以上` (card score threshold condition)
- **Game mechanic**: "if zone condition then action" - conditional structure based on zone state
- **Breakdown**: Cards in zone + card scores + threshold comparison
- **Detail**: Specific zone (成功ライブカード置き場), specific threshold (６以上)

### Pattern Recognition
The template `[card][card][opt_mod][value_type:score][opt_mod]合計が[number]以上` represents:
- **Conditional structure**: "if zone is this condition then action"
- **Zone-based condition**: Cards in specific zone with score threshold
- **Game mechanic**: Conditional effects triggered by zone state
- **Pattern matching**: All abilities with similar conditional structures consolidate to same high-level pattern

## Benefits

### 1. Pattern Compression
- Reduces template diversity while preserving semantic meaning
- Example: 30+ card patterns → single `[card]` super group
- Compression ratio: 481/529 templates

### 2. Semantic Analysis
- High-level pattern matching across abilities
- Component breakdown when specific details needed
- Preserves relationships between variables

### 3. Flexibility
- Analyze at super group level for broad patterns
- Drill down to component level for specific analysis
- Metadata tracking enables both views

## Implementation

### Config Structure
```json
{
  "super_groups": {
    "card": {
      "placeholder": "[card]",
      "patterns": [
        "[card_type]",
        "[player_card]",
        "[grouped_card]",
        "[zone_card]",
        "[opt_mod][card_type]",
        "[card_type][number]",
        // ... 30+ patterns
      ],
      "occurrences": 2000,
      "semantic": "all card-related patterns"
    }
  }
}
```

### Normalization Logic
1. Apply individual variable replacements first
2. Apply super group normalization (consolidates patterns to parent)
3. Track component metadata in `modifier_info`
4. Output both compressed template and component breakdown

### Output Format
```json
{
  "template": "[card][card][opt_mod][value_type:score][opt_mod]合計が[number]以上",
  "modifiers": [
    {
      "pattern": "[card_type]",
      "replacement": "[card]",
      "supergroup": "card",
      "semantic": "all card-related patterns"
    }
  ]
}
```

## Verification

### Test Case Analysis
The template `[card][card][opt_mod][value_type:score][opt_mod]合計が[number]以上` represents:
- **Condition**: Card score threshold in specific zone
- **Meaning**: "Total score of cards in success live card area ≥ 6"
- **Preserved**: Zone specificity, score attribute, threshold comparison
- **Compressed**: All card references to `[card]` for pattern matching
- **Breakdown**: Component metadata enables reconstruction of specific meaning

### Conclusion
The hierarchical architecture successfully:
- Consolidates patterns for compression
- Preserves semantic detail through breakdown
- Enables both high-level and detailed analysis
- Maintains relationships between variables
