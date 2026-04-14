# Pattern Fixes Documentation

## Truncation Bugs to Fix
The following truncation bugs were identified in pattern_nonatomic_analysis.json:
- "選んだカー" (1 occurrence) - truncated "カード" (card)
- "選んだハー" (4 occurrences) - truncated "ハート" (heart)
- "置いたカー" (1 occurrence) - truncated "カード" (card)
- "得たブレードハー" (1 occurrence) - truncated "ハート" (heart)

## Pattern Fixes Applied

### 1. lose_resource_and_retry (line ~627-631)
**Original regex:**
```python
r"\bその([^。]+)で([^。]+)([^。]+)を([^。]+)、もう一度([^。]+)を([^。]+)"
```
**Fixed regex:**
```python
r"\bその([^。]+)で([^。]+)を([^。]+)、もう一度([^。]+)を([^。]+)"
```
**Change:** Reduced capture groups from 6 to 5 by merging `([^。]+)([^。]+)を([^。]+)` to `([^。]+)を([^。]+)`
**Template change:** `⟦GAINED⟧⟦RESOURCE⟧` merged to `⟦GAINED_RESOURCE⟧`
**Purpose:** Prevents splitting of Japanese words with long vowel marks (ー) like "ブレードハート" → "ブレードハー"

### 2. original_heart_replacement (line ~878-883)
**Original regex:**
```python
r"\b([^。]+)が([^。]+)持つ([^。]+)は([^。]+)([^。]+)になる"
```
**Fixed regex:**
```python
r"([^。]+)、([^。]+)が([^。]+)持つ([^。]+)は([^。]+)([^。]+)になる"
```
**Change:** Added period prefix `([^。]+)、` to handle time period prefixes like "ライブ終了時まで、"
**Purpose:** Matches abilities with period prefix structure where the first part is covered by resource_selection pattern and the heart replacement clause starts with a period prefix

### 3. all_cards_type_condition_draw (line ~753-757)
**Original regex:**
```python
r"\b([^。]+)が([^。]+)([^。]+)の場合、([^。]+)を(\d+)枚([^。]+)"
```
**Fixed regex:**
```python
r"\b([^。]+)が([^。ー]+)([^。]+)の場合、([^。]+)を(\d+)枚([^。]+)"
```
**Change:** Changed `([^。]+)` to `([^。ー]+)` for the ALL capture group
**Purpose:** Prevents splitting of "あなた" → "あな" by excluding long vowel marks

### 4. per_discarded_card_draw (line ~975-979)
**Original regex:**
```python
r"\b([^。]+)により([^。]+)した([^。]+)([^。]+)を([^。]+)"
```
**Fixed regex:**
```python
r"\b([^。]+)により([^。]+)した([^。ー]+)([^。]+)を([^。]+)"
```
**Change:** Changed `([^。]+)` to `([^。ー]+)` for the COUNT capture group
**Purpose:** Prevents splitting of "カード" → "カー" by excluding long vowel marks

## Root Cause
The regex patterns use `([^。]+)` which matches any character except the Japanese period (。). This causes Japanese words with long vowel marks (ー) to be split incorrectly because the long vowel mark is treated as a separate character that can be captured independently.

## Solution
Changed specific capture groups to use `([^。ー]+)` which excludes the long vowel mark (ー) from the match, preventing words from being split at the vowel mark boundary.
