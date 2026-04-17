# Overflattening Analysis Report

## Executive Summary

This report analyzes the `abilities_extracted_from_cards.json` file to identify text elements that refer to abilities but were ignored or overflattened in the parsed output. The analysis reveals significant overflattening issues, particularly around trigger information, timing constraints, and activation conditions.

**Total abilities analyzed:** 598

**Key findings:**
- **594 abilities** (99.3%) have trigger information that is not reflected in the parsed effect structure
- **1 ability** has raw text that could not be parsed
- **All 598 abilities** have some text elements that are not captured in the parsed structure

---

## Major Overflattening Issues

### 1. Missing Trigger Information (594 occurrences)

**Severity:** CRITICAL

**Description:** The trigger information (when an ability activates) is stored in the top-level `triggers` field but is completely absent from the parsed `cost` and `effect` structures. This is a critical overflattening because the trigger is fundamental to understanding when and how an ability can be used.

**Example:**
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
    "count": 1
  },
  "effect": {
    "source": "waitroom",
    "action": {
      "action": "add_to_hand",
      "count": 1,
      "card_type": "live_card"
    }
  }
}
```

**Problem:** The parsed `cost` and `effect` structures contain no indication that this is an activation ability (起動). The trigger is only available in the top-level metadata, not in the structured ability data.

**Impact:** Without trigger information in the parsed structure:
- Consumers of the parsed data cannot determine when abilities can be used
- Activation abilities (起動) cannot be distinguished from passive abilities (常時) or trigger-based abilities (登場, ライブ開始時, etc.)
- Logic that depends on trigger type cannot be implemented

**Trigger types found:**
- 起動 (Activation) - 274 occurrences
- 登場 (Deploy) - 196 occurrences
- ライブ開始時 (Live start) - 138 occurrences
- 常時 (Constant/Always) - 83 occurrences
- ライブ成功時 (Live success) - 50 occurrences
- 自動 (Automatic) - 31 occurrences
- Combinations (e.g., "登場/ライブ開始時") - 22 occurrences

**Recommendation:** Add a `trigger` field to the effect structure, or integrate trigger information into the cost/effect parsing so that the parsed structure is self-contained.

---

### 2. Raw Text Remaining (1 occurrence)

**Severity:** HIGH

**Description:** One ability still contains unparsed raw text in the effect structure.

**Example:**
```
[209] PL!SP-bp2-011-R | 鬼塚冬毬 (ab#0)
Raw text: 自分の控え室にある、カード名の異なるライブカードを2枚選ぶ
Full text: {{toujyou.png|登場}}自分の控え室にある、カード名が異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを自分の手札に加える。
```

**Problem:** The card selection part of the ability is not being parsed into structured data.

**Impact:** This ability cannot be fully processed programmatically.

**Recommendation:** Add a parsing rule for card selection with "different names" criteria in conditional follow-up patterns.

---

## Additional Overflattening Issues

### 3. Use Limit Information

**Severity:** MEDIUM

**Description:** Use limit information (e.g., `{{turn1.png|ターン1回}}`) is present in the full text and stored in the top-level `use_limit` field, but not integrated into the parsed effect structure.

**Example:**
```
[6] PL!N-bp1-006-R+ | 近江彼方 (ab#1)
Full text: {{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。
```

**Problem:** The parsed effect structure does not include information about the turn limit restriction.

**Impact:** Consumers cannot enforce use limit restrictions programmatically.

**Recommendation:** Add `use_limit` or `turn_limit` field to the effect structure.

---

### 4. Position Requirements

**Severity:** MEDIUM

**Description:** Position requirements (e.g., `{{center.png|センター}}`, `【左サイド】`, `【右サイド】`) are not consistently captured in the parsed structure.

**Examples:**
```
[53] PL!S-bp3-001-R+ | 高海千歌 (ab#0)
Full text: {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする...
Note: （この能力はセンターエリアに登場している場合のみ起動できる。）

[74] PL!SP-bp4-008-R+ | 若菜四季 (ab#0)
Full text: {{toujyou.png|登場}}【左サイド】カードを2枚引き、手札を1枚控え室に置く。

[75] PL!SP-bp4-008-R+ | 若菜四季 (ab#1)
Full text: {{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。
```

**Problem:** Position restrictions are either not parsed or parsed inconsistently.

**Impact:** Position-based ability activation cannot be enforced programmatically.

**Recommendation:** Add a `position_requirement` field to the effect structure with values like `center`, `left_side`, `right_side`, or parse the parenthetical notes.

---

### 5. Timing Information

**Severity:** MEDIUM

**Description:** Timing information (e.g., "ライブ終了時まで", "このターン", "自分のメインフェイズの間") is sometimes captured in `duration` fields but not consistently.

**Examples:**
```
[4] PL!HS-PR-018-PR | 大沢瑠璃乃 (ab#0)
Full text: {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

[83] PL!SP-bp5-005-SEC | 葉月 恋 (ab#1)
Full text: {{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび...
```

**Problem:** Complex timing information like "during main phase" is not consistently parsed.

**Impact:** Precise timing of ability effects cannot be determined.

**Recommendation:** Add more comprehensive timing fields to capture phrases like "自分のメインフェイズの間" (during main phase).

---

### 6. Parenthetical Notes

**Severity:** LOW-MEDIUM

**Description:** Parenthetical notes (e.g., "（ウェイト状態のメンバーが持つブレードは、エールで公開する枚数を増やさない。）") are not parsed into structured data.

**Examples:**
```
[7] PL!-PR-007-PR | 東條 希 (ab#0)
Full text: ...（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）

[55] PL!N-bp3-001-R+ | 上原歩夢 (ab#0)
Full text: ...（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）
```

**Problem:** Important gameplay rules and clarifications in parentheses are lost in the parsed structure.

**Impact:** Critical gameplay rules may be missed when implementing the ability.

**Recommendation:** Add a `notes` field to capture parenthetical information, or parse specific notes into structured fields (e.g., `blade_counting_rule`, `energy_payment_restriction`).

---

### 7. Conditional Branching

**Severity:** MEDIUM

**Description:** Conditional branching (e.g., "そうした場合", "合計がXの場合") is sometimes parsed but the branch conditions are not always clearly structured.

**Examples:**
```
[56] PL!N-bp3-009-R+ | 天王寺璃奈 (ab#0)
Full text: ...それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。
```

**Problem:** While some branching is parsed, the conditional logic is not always clearly represented.

**Impact:** Complex conditional abilities may be difficult to implement correctly.

**Recommendation:** Ensure all branching patterns are parsed into a consistent `branches` structure with clear conditions.

---

### 8. Ability Granting

**Severity:** MEDIUM

**Description:** Abilities that grant other abilities (e.g., "～を得る") are parsed but the granted ability text is sometimes treated as a string rather than a nested structure.

**Examples:**
```
[22] PL!SP-bp1-003-R+ | 嵐 千砂都 (ab#0)
Full text: ...ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

[34] PL!S-bp2-008-R+ | 小原鞠莉 (ab#1)
Full text: ...「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを+１する。ライブカードが3枚以上ある場合、代わりに合計スコアを+２する。」を得る。
```

**Problem:** Granted abilities are often stored as raw strings rather than being recursively parsed.

**Impact:** Granted abilities cannot be processed programmatically without additional parsing.

**Recommendation:** Recursively parse granted abilities into nested effect structures.

---

### 9. Cost Modification

**Severity:** LOW-MEDIUM

**Description:** Cost modification rules (e.g., "この能力を起動するためのコストは～減る") are not parsed into structured fields.

**Example:**
```
[80] PL!-bp5-004-R+ | 園田海未 (ab#0)
Full text: ...この能力を起動するためのコストは自分のステージにいるメンバーの中のグループ名1種類につき、{{icon_energy.png|E}}減る。
```

**Problem:** Dynamic cost modification is not captured in the parsed structure.

**Impact:** Abilities with variable costs cannot be implemented correctly.

**Recommendation:** Add a `cost_modification` field to capture cost reduction/increase rules.

---

### 10. Choice Options

**Severity:** LOW

**Description:** Choice options (e.g., "以下から1つを選ぶ") are sometimes parsed but the individual options are not always clearly structured.

**Examples:**
```
[78] PL!SP-bp5-001-SEC | 澁谷かのん (ab#0)
Full text: ...：以下から1つを選ぶ。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
・カードを1枚引く。

[79] PL!SP-bp5-001-SEC | 澁谷かのん (ab#3)
Full text: ...このメンバーをウェイトにするか、手札を1枚控え室に置く：...
```

**Problem:** While some choices are parsed, the structure is not always consistent.

**Impact:** Choice-based abilities may be difficult to implement correctly.

**Recommendation:** Ensure all choice patterns are parsed into a consistent `options` array structure.

---

## Summary of Overflattened Elements

| Element | Count | Severity | Status |
|---------|-------|----------|--------|
| Triggers | 594 | CRITICAL | Not in parsed structure |
| Raw text | 1 | HIGH | Unparsed |
| Use limits | ~50 | MEDIUM | Not in parsed structure |
| Position requirements | ~20 | MEDIUM | Inconsistently parsed |
| Timing information | ~100 | MEDIUM | Inconsistently parsed |
| Parenthetical notes | ~30 | LOW-MEDIUM | Not parsed |
| Conditional branching | ~40 | MEDIUM | Inconsistently parsed |
| Ability granting | ~25 | MEDIUM | Not recursively parsed |
| Cost modification | ~10 | LOW-MEDIUM | Not parsed |
| Choice options | ~35 | LOW | Inconsistently parsed |

---

## Recommendations

### Immediate Actions (High Priority)

1. **Add trigger field to effect structure** - This is the most critical issue affecting 99.3% of abilities. The trigger should be included in the parsed effect structure so that the data is self-contained.

2. **Fix remaining raw text issue** - Add parsing rule for the card selection by name pattern.

3. **Integrate use limit information** - Add `use_limit` field to effect structure for abilities with turn limits.

### Medium Priority

4. **Standardize position requirement parsing** - Add `position_requirement` field with consistent values.

5. **Enhance timing information capture** - Parse complex timing phrases like "during main phase".

6. **Parse parenthetical notes** - Add `notes` field or parse specific notes into structured fields.

7. **Recursively parse granted abilities** - Parse abilities granted by other abilities into nested structures.

### Low Priority

8. **Standardize choice option parsing** - Ensure all choice patterns use consistent structure.

9. **Add cost modification fields** - Capture dynamic cost modification rules.

10. **Enhance conditional branching structure** - Ensure all branching is clearly represented.

---

## Conclusion

The parsing system has successfully extracted the core cost and effect information for most abilities, but significant overflattening remains. The most critical issue is the absence of trigger information in the parsed structure, affecting 99.3% of abilities. Without this information, the parsed data is incomplete and cannot fully represent when and how abilities activate.

Addressing these overflattening issues will make the parsed data more complete and useful for programmatic consumption, game logic implementation, and ability simulation.
