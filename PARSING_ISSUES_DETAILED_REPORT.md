# Comprehensive Parsing Issues Report

## Executive Summary

This report documents the parsing issues found in `abilities_extracted_from_cards.json` after analyzing 598 unique abilities. The analysis identified several categories of parsing failures where text is not correctly mapped to opcodes and variables in the output script.

## Issue Categories

### 1. Energy Cost Missing Type (53 occurrences)

**Issue:** Energy costs are parsed as `{'energy': X}` without a `type` field, making them incomplete cost structures.

**Example:**
```json
"Cost": {'energy': 1}
```

**Expected:**
```json
"Cost": {'type': 'pay_energy', 'energy': 1}
```

**Root Cause:** The cost parser (`cost_parser.py`) is not setting a `type` field for energy-only costs. It should set `type: 'pay_energy'` to match the pattern used for other cost types like `move_cards` and `reveal_cards`.

**Impact:** This makes the cost structure inconsistent and harder to process programmatically. Consumers of the JSON need to check for an `energy` field without a `type` to handle this case.

**Affected Abilities:** 53 abilities with energy-only costs (e.g., PL!HS-PR-018-PR, PL!N-bp1-006-R+, PL!N-bp1-012-R+, etc.)

---

### 2. Condition Missing Type (24 occurrences)

**Issue:** Conditions are parsed without a `type` field, leaving them as incomplete condition structures.

**Example:**
```json
"Effect": {'condition': {'target': 'self'}, 'duration': 'until_end_of_live', 'actions': [...]}
```

**Expected:**
```json
"Effect": {'condition': {'type': 'trigger_condition', 'target': 'self', ...}, ...}
```

**Root Cause:** The condition parser (`condition_parser.py`) is failing to identify the specific condition type in certain cases. This happens when:
- Complex trigger conditions involving multiple clauses (e.g., "自分のカードの効果によって、このメンバーがエリアを移動するか自分のエネルギー置き場にエネルギーが置かれたとき")
- Conditions that should be parsed as specific types but fall through to generic parsing

**Impact:** Without a `type` field, the condition cannot be properly interpreted by downstream processing. The condition's purpose is unclear.

**Affected Abilities:** 24 abilities with incomplete conditions (e.g., PL!SP-bp5-004-SEC, PL!S-bp5-004-P, PL!HS-PR-019-PR, etc.)

**Specific Cases:**
1. **Effect-triggered conditions:** "自分のカードの効果によって、このメンバーがエリアを移動するか自分のエネルギー置き場にエネルギーが置かれたとき" - Should be parsed as `effect_trigger` or similar
2. **Card placement conditions:** "自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合" - Should parse the condition about the cards placed
3. **Generic conditions:** Various conditions that only have `target: 'self'` without specifying what condition

---

### 3. Action Missing Action Field (17 occurrences total)

**Issue:** Actions in the `actions` array are missing the `action` field, leaving them as incomplete action structures.

**Subcategories:**
- Action 0 missing action field: 5 occurrences
- Action 1 missing action field: 9 occurrences  
- Action 2 missing action field: 3 occurrences

**Examples:**

**Duration-only action (should be merged with previous action):**
```json
"Effect": {'actions': [{'action': 'choose_heart', ...}, {'duration': 'until_end_of_live'}, ...]}
```

**Multiplier-only action (should be merged with following action):**
```json
"Effect": {'actions': [..., {'multiplier': True, 'per_unit': 1, 'unit_type': 'card', 'target': 'self'}, {'action': 'gain_resource'}]}
```

**Multi-target marker (should be merged with following action):**
```json
"Effect": {'actions': [{'target': 'both_players', 'multi_target': True}, {'action': 'add_to_hand', ...}]}
```

**Root Cause:** The effect parser (`effect_parser.py`) is splitting complex actions into separate array elements when they should be merged as modifiers of a single action. This happens with:
- Duration modifiers (e.g., "ライブ終了時まで")
- Multiplier modifiers (e.g., "～につき")
- Target modifiers (e.g., "自分と相手はそれぞれ")

**Impact:** These "actions" without an `action` field are not valid actions - they're modifiers that should be part of the preceding or following action. This breaks the action structure and makes processing difficult.

**Affected Abilities:** 17 abilities with incomplete actions (e.g., PL!-bp3-012-PR, PL!-bp3-009-R+, PL!N-bp5-012-P, etc.)

---

### 4. Raw Text in Actions (6 occurrences)

**Issue:** Complex effect patterns are not being parsed and fall back to `raw_text`, losing all structured information.

**Cases:**

#### Case 1: Complex Trigger with Payment (葉月 恋)
**Text:** "自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび、{{icon_energy.png|E}}支払ってもよい。そうした場合、それらのカードの中から1枚手札に加える。"

**Current Output:**
```json
"Effect": {'actions': [{'raw_text': '自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび、{{icon_energy.png|E}}支払ってもよい'}, {'action': 'add_to_hand', 'count': 1, 'conditional': True}]}
```

**Expected Structure:**
```json
"Effect": {
  "trigger": {
    "type": "whenever",
    "condition": "自分のカードが1枚以上いずれかの領域から控え室に置かれる",
    "timing": "自分のメインフェイズの間"
  },
  "actions": [{
    "action": "pay_energy",
    "optional": true,
    "count": 1
  }, {
    "action": "add_to_hand",
    "count": 1,
    "source": "discarded_cards",
    "conditional": true
  }]
}
```

**Root Cause:** The effect parser doesn't have a pattern for "whenever" triggers with payment options. It should detect "～たび、～支払ってもよい" as a trigger with optional payment.

---

#### Case 2: Card Selection with Variable Payment (桜坂しずく)
**Text:** "自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、そのライブカードを手札に加える。"

**Current Output:**
```json
"Effect": {'actions': [{'raw_text': '自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい'}, {'action': 'add_to_hand', 'card_type': 'live_card', 'conditional': True}]}
```

**Expected Structure:**
```json
"Effect": {
  "actions": [{
    "action": "select_card",
    "source": "waitroom",
    "card_type": "live_card",
    "count": 1
  }, {
    "action": "pay_energy",
    "optional": true,
    "amount": "selected_card_score",
    "conditional": true
  }, {
    "action": "add_to_hand",
    "source": "selected_card",
    "conditional": true
  }]
}
```

**Root Cause:** The effect parser doesn't have a pattern for "select card, then pay variable amount based on selected card's property". It should detect "～選び、その～に等しい数の～を支払ってもよい" as a variable payment pattern.

---

#### Case 3: Area Selection (若菜四季)
**Text:** "その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。"

**Current Output:**
```json
"Effect": {'actions': [{'action': 'draw_cards', 'count': 1}, {'raw_text': '、登場したエリアとは別の自分のエリア1つを選ぶ'}]}
```

**Expected Structure:**
```json
"Effect": {
  "actions": [{
    "action": "draw_cards",
    "count": 1
  }, {
    "action": "select_area",
    "source": "stage",
    "exclude": "deployed_area",
    "count": 1,
    "target": "self"
  }, {
    "action": "move_member",
    "source": "this_member",
    "destination": "selected_area"
  }]
}
```

**Root Cause:** The effect parser doesn't have a pattern for area selection. It should detect "～エリア1つを選ぶ" as an area selection action.

---

#### Case 4: Card Selection by Name (鬼塚冬毬)
**Text:** "自分の控え室にある、カード名が異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。"

**Current Output:**
```json
"Effect": {'actions': [{'raw_text': '自分の控え室にある、カード名が異なるライブカードを2枚選ぶ'}, {'count': 1, 'conditional': True}]}
```

**Expected Structure:**
```json
"Effect": {
  "actions": [{
    "action": "select_card",
    "source": "waitroom",
    "card_type": "live_card",
    "count": 2,
    "selection_criteria": "different_names"
  }, {
    "action": "opponent_selects",
    "from": "selected_cards",
    "count": 1,
    "target": "opponent"
  }, {
    "action": "add_to_hand",
    "source": "opponent_selected_card",
    "conditional": true
  }]
}
```

**Root Cause:** The effect parser doesn't have a pattern for "select cards with criteria, then opponent selects from them". It should detect "～カード名が異なる～選ぶ" as a selection with criteria.

---

#### Case 5: Optional Draw (黒澤ダイヤ)
**Text:** "カードを1枚引いてもよい。そうした場合、手札2枚を好きな順番でデッキの上に置く。"

**Current Output:**
```json
"Effect": {'actions': [{'raw_text': 'カードを1枚引いてもよい'}, {'action': 'place_on_deck', 'destination': 'deck_top', 'order': 'any', 'conditional': True}]}
```

**Expected Structure:**
```json
"Effect": {
  "actions": [{
    "action": "draw_cards",
    "count": 1,
    "optional": true
  }, {
    "action": "place_on_deck",
    "source": "hand",
    "count": 2,
    "destination": "deck_top",
    "order": "any",
    "conditional": true
  }]
}
```

**Root Cause:** The effect parser doesn't have a pattern for optional draw followed by conditional action. It should detect "～引いてもよい。そうした場合" as an optional action with conditional follow-up.

---

#### Case 6: Cost Missing Source (柊摩央)
**Text:** "エネルギー2枚をエネルギーデッキに置く：自分の控え室にあるライブカードを1枚手札に加える。"

**Current Output:**
```json
"Cost": {'type': 'move_cards', 'destination': 'energy_deck', 'card_type': 'energy_card', 'count': 2}
```

**Expected:**
```json
"Cost": {'type': 'move_cards', 'source': 'energy_zone', 'destination': 'energy_deck', 'card_type': 'energy_card', 'count': 2}
```

**Root Cause:** The cost parser is not extracting the source for energy card movements. It should detect "エネルギー" without a specified location as coming from `energy_zone`.

---

## Summary of Fixes Needed

### Priority 1: Structural Fixes (High Impact)

1. **Fix energy cost type field:** Add `type: 'pay_energy'` to all energy-only costs in `cost_parser.py`
2. **Fix condition type field:** Ensure all conditions have a `type` field in `condition_parser.py`
3. **Fix action field merging:** Merge modifier-only "actions" with the actual action they modify in `effect_parser.py`

### Priority 2: Pattern Matching Fixes (Medium Impact)

4. **Add whenever trigger pattern:** Parse "～たび、～支払ってもよい" as trigger with optional payment
5. **Add variable payment pattern:** Parse "～選び、その～に等しい数の～を支払ってもよい" as variable payment
6. **Add area selection pattern:** Parse "～エリア1つを選ぶ" as area selection action
7. **Add selection criteria pattern:** Parse "～カード名が異なる～選ぶ" as selection with criteria
8. **Add optional draw pattern:** Parse "～引いてもよい。そうした場合" as optional action with conditional follow-up
9. **Fix energy cost source:** Add source field for energy card costs in `cost_parser.py`

## Implementation Plan

1. Modify `cost_parser.py` to add `type: 'pay_energy'` to energy costs and add source field for energy movements
2. Modify `condition_parser.py` to ensure all conditions have a type field, add missing condition types
3. Modify `effect_parser.py` to merge modifier-only actions with their target actions
4. Add new parsing patterns to `effect_parser.py` for the 5 raw_text cases
5. Re-run extraction to verify all fixes
6. Re-audit to confirm no remaining issues
