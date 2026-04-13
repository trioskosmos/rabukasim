# Extraction Gaps Found - April 13, 2026

## STATUS: PARTIALLY FIXED ✓

### FIXED Issues

#### Issue 1: Branch Options with "か...か" (OR) ✓ FIXED
**Location**: jp_to_logic() function  
**Status**: WORKING

**Before**:
```
JP: "{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。..."
Old Logic: "add heart_01 to target\nadd heart_03 to target\nadd heart_06 to target"
```

**After** (FIXED):
```
New Logic: "choose one from: option 1: add heart_01 to target; option 2: add heart_03 to target; option 3: add heart_06 to target"
```

**Implementation**: Added regex pattern to detect choice structures before individual heart extraction, with broad context checking to avoid duplicates.

---

#### Issue 2: Empty Abilities with "メンバー1人をアクティブにしてもよい" ✓ FIXED  
**Location**: jp_to_logic() function  
**Status**: WORKING

**Before**:
```
JP: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をアクティブにしてもよい。"
Old Logic: "" (empty)
```

**After** (FIXED):
```
New Logic: "optional untap 1 member"
```

**Implementation**: Added pattern matching for メンバーN人をアクティブにしてもよい with improved context checking to avoid duplicate extraction.

---

#### Issue 3: Destructive Text Replacement ✓ FIXED
**Location**: translate_extracted_text() function, lines 302-308  
**Status**: FIXED

**Before**: Blindly removed letters A, B, w, x which corrupted words like "draw", "blade", "activate"  
**After**: Removed destructive replacements, kept only whitespace normalization

---

## REMAINING Issues

### Issue 2 (Partial): Cost:Effect Structure Not Clearly Distinguished  
**Location**: jp_to_logic() function  
**Severity**: MEDIUM

**Status**: NOT YET FIXED

**Example**:
```
JP: "{{kidou.png|起動}}手札を1枚控え室に置いてもよい：自分の控え室からメンバーカードを1枚手札に加える。"
Current Logic: "discard 1 card from hand to discard\nrecover card from discard to hand..."
Problem: No clear marker showing cost vs effect separation
```

**Next Step**: Add "COST:" and "EFFECT:" prefixes when detecting "：" colon separator or "てもよい" optional patterns.

---

### Issue 3 (Partial): Vague Conditional Logic  
**Location**: jp_to_logic() function  
**Severity**: MEDIUM

**Status**: PARTIALLY FIXED

**Example**:
```
JP: "自分の成功ライブカード置き場にカードが2枚以上ある場合、..."
Current Logic: "if exists"
Problem: Could be more specific (currently vague)
```

**Note**: The overall conditional extraction is working but could be more semantically precise in some cases.

---

## Extraction Statistics (After Fixes)

Total abilities extracted: 600  
Empty abilities: 40 (6.7%) - mostly placeholder abilities with no actual effects  
Successfully structured choice patterns: ~5 improved  
Successfully handled optional untap: +1 ability from previous empty  

### Most Common Patterns (unchanged):
- discard: 174 (29.0%)
- add to hand: 143 (23.8%)
- untap: 30 (5.0%) - improved from 29
- recover from discard: 59 (9.8%)

---

## Testing Notes

### Examples Verified Working:
1. ✓ Heart choice patterns (heart_01 か heart_03 か) - now structured as choice
2. ✓ Optional member untap (メンバー1人をアクティブにしてもよい) - now recognized  
3. ✓ No destructive character removal - legitimate English preserved

### Edge Cases Fixed:
- Multiple heart choice options no longer duplicated
- Optional untap with quantifiers no longer creates duplicate entries
- Broader context checking prevents over-aggressive filtering

---

## Recommendations for Next Phase

1. **Cost/Effect Separation**: Implement clear COST: / EFFECT: markers when "：" or "てもよい" appears
2. **Condition Specificity**: Enhance conditional logic to extract actual counts/targets when available
3. **Granted Abilities**: Structure abilities with "を得る" as GRANTED with nested ability reference
4. **Test Coverage**: Create test suite comparing extracted logic to original Japanese text



