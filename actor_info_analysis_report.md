# Actor/Player Information Analysis Report

## Summary
Analysis of 598 abilities in abilities_extracted_from_cards.json for actor/player information presence.

## Overall Statistics
- **Actions with actor info**: 496 (83%)
- **Actions without actor info**: 101 (17%)
- **Conditions with actor info**: 0 (0%)
- **Conditions without actor info**: 1

## Actor Pattern Breakdown

### Implicit Self (119 abilities)
Card abilities where actor is implicitly "you" (the card's controller). No explicit marker needed.
- Example: "カードを1枚引き、手札を1枚控え室に置く。"
- These have `source` field in effect structure
- **Status**: Acceptable - implicit self is standard for card abilities

### Explicit Self (253 abilities)
Explicitly marked as self/自分 with source/player field.
- Example: "このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。"
- **Status**: Good - properly structured

### Explicit Opponent (25 abilities)
Explicitly marked as opponent/相手.
- Example: "このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。"
- **Status**: Good - properly structured

### Ambiguous (137 abilities)
Has text indicator (自分) but no source/player field in effect structure.
- Example: "手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。"
- **Status**: These have `target: "self"` in conditions, so actor info is present but nested
- **Recommendation**: Acceptable - actor info is captured in condition target field

### Both Players (64 abilities)
Both players involved.
- Example: "自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。"
- **Status**: Need to verify proper structure

## Critical Issues Found

### 1. Abilities mentioning opponent but lacking target field (10 cases)
These abilities mention "相手" in text but don't have explicit `target` field in effect structure.

Examples:
- "自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。"
- "このメンバーがエリアを移動するたび、カードを1枚引く。(対戦相手のカードの効果でも発動する。)"

**Status**: Some of these are "both players" abilities that need proper target/actor fields

### 2. Simple actions with no actor specified (18 cases)
Simple card abilities without explicit actor in text or effect.
- Example: "{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。"
- Example: "エネルギーを2枚アクティブにする。"

**Status**: Acceptable - these are implicit self abilities (card's controller)

## Recommendations

1. **For implicit self abilities**: No changes needed. Card abilities where the controller performs the action is a reasonable default.

2. **For ambiguous cases with 自分**: The actor info is captured in condition's `target: "self"` field. This is acceptable.

3. **For both players abilities**: Should have explicit `target` or `source` fields to distinguish between self and opponent actions.

4. **For abilities with notes like "(対戦相手のカードの効果でも発動する。)"**: These should be structured as separate metadata fields, not embedded in text.

## Regression Test Candidates

Consider adding tests for:
1. Both players abilities to ensure proper target/actor fields
2. Abilities with opponent mentions to verify target field presence
3. Abilities with conditional actor (e.g., "対戦相手のカードの効果でも発動する")
