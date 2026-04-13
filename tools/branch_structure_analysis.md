# Branch Structure Analysis - Issues with Current Automation

## Overview
Analysis of longer abilities with branches reveals several critical issues with how the current automation handles complex ability structures.

## Key Issues Identified

### 1. Branch Options Not Translated (Lines 1060-1071)
**Problem**: The "choose one from" pattern captures Japanese text in options but never translates it.

**Current Code**:
```python
if "以下から1つを選ぶ。" in jp_text:
    choice_pos = jp_text.find("以下から1つを選ぶ。")
    bullet_pattern = r"・(.+)"
    bullet_matches = list(re.finditer(bullet_pattern, jp_text[choice_pos:]))
    if bullet_matches:
        options = []
        for i, match in enumerate(bullet_matches):
            option_text = match.group(1).strip()  # NO TRANSLATION HERE
            options.append(f"option {i+1}: {option_text}")
        operations.append((choice_pos, f"choose one from: {'; '.join(options)}"))
```

**Example Output** (Index 85):
```
Logic: choose one from: option 1:J[h1AD1TɒuB; option 2: ̃Xe[Wɂ邷ׂẴRXg2ȉ̃o[EFCgɂB
```

**Expected Output**:
```
Logic: choose one from: option 1: draw 1 card, discard 1 card from hand; option 2: tap all cost <= 2 members on opponent's stage
```

**Fix**: Add `translate_extracted_text()` call for each option_text.

---

### 2. Logic Disconnection Between Options and Effects
**Problem**: Branch options are captured as a single string, but there's no mechanism to connect each option to its specific effects. All subsequent operations are extracted from the entire ability, not tied to specific branch options.

**Example** (Index 31):
```
JP: 
{{live_start.png|ライブ開始}}{{icon_energy.png|E}}エネルギーを支払ってよい：以下から1つを選ぶ。
・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。
・カードを1枚引く。
{{kidou.png|起動}}{{turn1.png|ターン1回}}のメンバーをウェイトにするか、手札に置く：エネルギー1枚、アクティブにする。

Logic:
optional pay energy
choose one from: option 1: ̃Xe[WɂRXg4ȉ̃o[1lEFCgɂB; option 2: J[h1B
select opponent member  # These operations are from kidou trigger, not the branch options
tap opponent member
draw 1 card from deck to hand
tap source_card
discard 1 card from hand to discard
activate 1 energy
untap target
```

**Issue**: The operations after "choose one from" include operations from a different trigger (kidou), making it unclear which operations belong to which branch option.

**Root Cause**: The current extraction processes the entire ability text as a single unit, without distinguishing between:
- Different triggers within the same ability
- Operations that belong to specific branch options vs. operations that are separate effects

---

### 3. Multi-Trigger Ability Confusion
**Problem**: Abilities with multiple triggers have their operations combined without clear separation.

**Example** (Index 31 again):
- Trigger 1: live_start with optional pay energy and choose one from
- Trigger 2: kidou with tap member or discard card, then activate energy

**Current Behavior**: Both triggers' operations are combined in a single logic string without any indication of which operations belong to which trigger.

**Expected Behavior**: Either:
- Split into separate ability entries (one per trigger) - **This is already being done for some triggers**
- Or clearly mark which operations belong to which trigger within the logic

---

### 4. Conditional Logic Not Extracted from Branch Options
**Problem**: Branch options often contain conditions (e.g., "if opponent's stage has cost <= 4 member") but these are not extracted as separate conditional logic - they're just embedded in the option text.

**Example** (Index 86):
```
JP: 
{{toujyou.png|登場}}以下から1つを選ぶ。
・相手のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
・相手のステージにいる『SaintSnow』のメンバー1人をポジションチェンジ。(そのメンバーのエリア以外のエリアに移動。そのエリアにメンバーがいる場合、そのメンバーはそのメンバーのエリアに移動。)

Logic:
choose one from: option 1: ̃Xe[Wɂ邱̃o[ȊÓwAQOURSx̃o[1ĺACuI܂ŁA{{icon_blade.png|u[h}}𓾂B; option 2: ̃Xe[WɂwSaintSnowx̃o[1l|WV`FWB(̃o[GAȊÕGAɈړB̃GAɃo[ꍇÃo[͂̃o[GAɈړB)
add 1 blade to target
change formation
```

**Issue**: The conditions "if opponent's stage has Aqours member" and "if opponent's stage has SaintSnow member" are not extracted as conditional logic. They're just embedded in the garbled option text.

---

## Recommended Fixes

### Priority 1: Translate Branch Options
Add translation to the branch extraction code:
```python
for i, match in enumerate(bullet_matches):
    option_text = match.group(1).strip()
    option_text = translate_extracted_text(option_text)  # ADD THIS
    options.append(f"option {i+1}: {option_text}")
```

### Priority 2: Extract Conditional Logic from Branch Options
Before adding the "choose one from" operation, extract conditional logic from each option:
```python
for i, match in enumerate(bullet_matches):
    option_text = match.group(1).strip()
    # Extract conditions like "～がいる場合", "～がある場合"
    # Add as separate conditional operations before the branch operation
```

### Priority 3: Separate Multi-Trigger Operations
Ensure that operations from different triggers are clearly separated, either:
- By creating separate ability entries (already partially implemented)
- Or by adding trigger markers in the logic string

### Priority 4: Connect Branch Options to Their Effects
Develop a mechanism to associate specific effects with each branch option. This may require:
- Parsing the ability text to identify which operations belong to which option
- Using indentation or bullet point structure to determine scope
- Creating a hierarchical logic structure instead of a flat list

---

## Statistics
- Total abilities with branch structures: 116
- Abilities with "choose one from" (以下から1つを選ぶ): 9
- All 9 branch abilities have untranslated Japanese text in options
- All 9 branch abilities show logic disconnection issues
