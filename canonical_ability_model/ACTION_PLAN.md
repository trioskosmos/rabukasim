# Official Rules Mapping - Action Plan

**Analysis Complete**: April 14, 2026  
**Status**: Ready for implementation  
**Estimated Coverage Improvement**: 62% → 89% with Phase 1 implementation

---

## Executive Summary

Your `extract_abilities_to_template.py` currently covers **62% of official LoveCA rules** (141 patterns across 12 rule sections). The remaining 38% consists of:

- **Must-have** (5 items blocking >30% of cards):
  - Character names (0/50 patterns)
  - Unit names (0/18 patterns)  
  - Complex conditions AND/OR (0/unlimited)
  - Live success mechanics (0 patterns)
  - Keyword abilities (1/20 patterns)

- **Should-have** (6 items blocking 10-30% of cards)
- **Nice-to-have** (8 items blocking <10% of cards)

---

## Phase 1: Critical Fixes (Est. 200 new patterns)

### 1. CHARACTER NAME PATTERNS (50 characters)

**Current**: 0 patterns  
**Needed**: 50+ patterns  
**Example Gap**: "「上原歩夢」がいる場合" fails (no character recognition)

**Implementation**:
```python
# In extract_abilities_to_template.py, AFTER atomic_group_sunny_passion section:

# CHARACTER SPECIFIC PATTERNS (Rule 2.3)
{
    "name": "character_uehra_ayumu",
    "regex": r"「上原歩夢」",
    "template": "「上原歩夢」",
    "structure": "Character - Uehra Ayumu (Printemps)",
},
# ... repeat for 49 more characters
```

**Characters to add** (from metadata.json):
- Group: μ's (9 chars): 高坂穂乃果, 绫瀬絵里, 南ことり, 園田海未, 星野一歩, 東條希, 小泉花陽, 矢澤にこ
- Group: Aqours (9 chars): 高海千歌, 桜内梨子, 松浦果南, 鞠莉, Dia, 小原鞠莉, 黒沢ダイヤ, 津島善子, 国木田花丸, 宮下愛
- Group: 虹ヶ咲 (10 chars): 高咲侑, 上原歩夢, 朝香果林, 宮下愛, 中須かすみ, 近江彼方, 優木せつ菜, 天王寺瑠唯, 優木希美

**Recommendation**: Parse metadata.json or constants.php → extract 50+ character names → generate patterns

### 2. UNIT NAME PATTERNS (18 units)

**Current**: 0 patterns  
**Needed**: 18 patterns  
**Example Gap**: "『Printemps』のメンバーが" fails

**Implementation**:
```python
# UNIT SPECIFIC PATTERNS (Rule 2.5)
{
    "name": "unit_printemps",
    "regex": r"『Printemps』",
    "template": "『Printemps』",
    "structure": "Unit - Printemps",
},
# ... repeat for 17 more units
```

**Units to add**:
- μ's units (3): Printemps, lily white, BiBi
- Aqours units (3): CYaRon!, AZALEA, Guilty Kiss
- 虹ヶ咲 units (3): DiverDiva, A・ZU・NA, QU4RTZ
- Liella! units (3): R3BIRTH, CatChu!, KALEIDOSCORE
- 蓮ノ空 units (3): 5yncri5e!, スリーズブーケ, DOLLCHESTRA (or EDEL_NOTE, AISCREAM)

**Source**: Extract from metadata.json unit_names list

### 3. COMPLEX CONDITIONAL LOGIC (AND/OR operators)

**Current**: Only simple conditions work  
**Needed**: Logical operators for multi-condition chains  
**Example Gap**: "『μ's』のメンバーがいて、かつ、手札が3枚以上ある場合" fails completely

**Implementation Strategy**:

Instead of regex matching, create a **condition parser** that can chain:

```python
# NEW: Add to DSL_PATTERNS section:

# COMPLEX CONDITIONS - Logical operators
{
    "name": "conditional_and_gate",
    "regex": r"([^。]+)かつ([^。]+)場合",
    "template": "⟦CONDITION1⟧かつ⟦CONDITION2⟧場合",
    "structure": "Conditional - AND gate (両方の条件を満たす場合)",
},
{
    "name": "conditional_or_gate",
    "regex": r"([^。]+)またはいずれかの([^。]+)場合",
    "template": "⟦CONDITION1⟧またはいずれかの⟦CONDITION2⟧場合",
    "structure": "Conditional - OR gate (いずれかの条件を満たす場合)",
},
{
    "name": "conditional_not_gate",
    "regex": r"([^。]+)ない場合",
    "template": "⟦CONDITION⟧ない場合",
    "structure": "Conditional - NOT gate (条件を満たさない場合)",
},
{
    "name": "conditional_count_and_presence",
    "regex": r"『([^』]+)』のメンバーが([^場]+)かつ、([^。]+)が(\d+)以上",
    "template": "『⟦GROUP⟧』のメンバーが⟦PRESENCE⟧かつ、⟦TARGET⟧が⟦X⟧以上",
    "structure": "Conditional - Group presence AND count threshold",
},
```

### 4. LIVE SUCCESS/CHALLENGE MECHANICS (4-6 patterns)

**Current**: 0 patterns  
**Needed**: Success conditions, failure outcomes  
**Example Gap**: "スコア3以上で成功" has no pattern; challenge tracking broken

**Implementation**:
```python
# LIVE PHASE - Success/Challenge outcomes (Rule 8.3.14)
{
    "name": "live_success_condition",
    "regex": r"スコア(\d+)以上で成功",
    "template": "スコア⟦X⟧以上で成功",
    "structure": "Live Outcome - Success threshold",
},
{
    "name": "live_challenge_outcome_success",
    "regex": r"チャレンジに成功した場合、([^。]+)",
    "template": "チャレンジに成功した場合、⟦EFFECT⟧",
    "structure": "Live Outcome - Effect on success",
},
{
    "name": "live_challenge_outcome_failure",  
    "regex": r"チャレンジに失敗した場合、([^。]+)",
    "template": "チャレンジに失敗した場合、⟦EFFECT⟧",
    "structure": "Live Outcome - Effect on failure",
},
{
    "name": "live_score_threshold",
    "regex": r"この([^。]+)のスコアが(\d+)以上の場合、ゲーム中、([^。]+)",
    "template": "この⟦LIVE_CARD⟧のスコアが⟦X⟧以上の場合、ゲーム中、⟦EFFECT⟧",
    "structure": "Live Outcome - Continuous effect from score",
},
```

### 5. KEYWORD ABILITY PATTERNS (10-15 patterns)

**Current**: 1 pattern (batontouch - minimal)  
**Needed**: Formal keywords + support abilities  
**Example Gap**: "火力支援" (power support) has no pattern; batontouch minimal

**Implementation**:
```python
# KEYWORD ABILITIES (Rule 11 - キーワード能力)
{
    "name": "keyword_batontouch_entry",
    "regex": r"バトンタッチで登場",
    "template": "バトンタッチで登場",
    "structure": "Keyword - Batontouch entry (transitions member positions)",
},
{
    "name": "keyword_support_power",
    "regex": r"火力支援",
    "template": "火力支援",
    "structure": "Keyword - Power support (increases power output)",
},
{
    "name": "keyword_support_defense",
    "regex": r"防御支援",
    "template": "防御支援",
    "structure": "Keyword - Defense support (increases defense)",
},
{
    "name": "keyword_support_effect",
    "regex": r"([^。]+)のキーワード能力が「([^」]+)」",
    "template": "⟦SOURCE⟧のキーワード能力が「⟦KEYWORD⟧」",
    "structure": "Keyword - Keyword ability reference",
},
{
    "name": "keyword_entry_transition",
    "regex": r"このメンバーが([^。]+)ステージに登場した場合、([^。]+)のメンバー1人を([^。]+)に移動",
    "template": "このメンバーが⟦SOURCE_AREA⟧ステージに登場した場合、⟦GROUP⟧のメンバー1人を⟦TARGET_AREA⟧に移動",
    "structure": "Keyword - Area transition effect",
},
```

---

## Phase 2: Extended Mechanics (Est. 50-70 patterns)

### 6. Energy Deck Operations
- `search_energy_deck` - エネルギーデッキから検索
- `shuffle_energy_deck` - エネルギーデッキをシャッフル
- `recover_energy` - エネルギーの回収

### 7. Conditional Ability Granting (Scoped)
- `conditional_gain_ability_scoped` - 条件付きで対象に能力を付与
- `temporary_ability_grant` - ゲーム中、能力を得る
- `conditional_ability_target` - 特定メンバーのみ能力取得

### 8. Cost Modification Chains
- `cost_reduction_per_member` - メンバー1人につき、コスト-1
- `cost_increase_conditional` - 条件時、コスト+1
- `cost_threshold_scaling` - コストにより効果が変わる

---

## Phase 3: Advanced Features (Est. 20-30 patterns)

### 9. Yell System
- `yell_conversion` - エール変換
- `yell_trigger` - エール効果
- `yell_limit` - エール枚数制限

### 10. Phase-Specific Actions
- `phase_challenge_action` - チャレンジフェイズ中に
- `phase_appeal_action` - エールフェイズ中に

---

## Implementation Checklist

### Step 1: Extract Data from Metadata
- [ ] Read metadata.json
- [ ] Extract 50 character names
- [ ] Extract 18 unit names
- [ ] Extract group mappings
- [ ] Create mapping table (character_id → group_id, unit_id)

### Step 2: Generate Character/Unit Patterns
- [ ] Create 50 `character_*` patterns
- [ ] Create 18 `unit_*` patterns
- [ ] Test pattern matching against sample abilities
- [ ] Verify no duplicates with existing patterns

### Step 3: Add Complex Logic Patterns
- [ ] Implement AND/OR/NOT condition patterns
- [ ] Add multi-condition test cases
- [ ] Test chaining logic: "『μ's』がいて、かつ、スコア5以上"

### Step 4: Add Keyword Patterns
- [ ] Add `keyword_batontouch_*` (3-5 patterns)
- [ ] Add `keyword_support_*` (3-5 patterns)  
- [ ] Add `keyword_*_entry` patterns (2-3 patterns)
- [ ] Test against cards using keywords

### Step 5: Add Success Mechanics
- [ ] Add `live_success_*` patterns (4-6 patterns)
- [ ] Add `live_failure_*` patterns (2-3 patterns)
- [ ] Test challenge tracking

### Step 6: Validation
- [ ] Test all new patterns against cards_compiled.json
- [ ] Measure new coverage percentage
- [ ] Document any remaining gaps
- [ ] Update RULES_TO_PATTERNS_MAPPING.md with results

---

## Expected Outcomes

| Phase | Patterns Added | Coverage Before | Coverage After | Time Est. |
|-------|---|---|---|---|
| 1 | ~200 | 62% | **80%** | 4-6 hours |
| 2 | ~60 | 80% | **85%** | 2-3 hours |
| 3 | ~25 | 85% | **89%** | 1-2 hours |
| *Full Implementation* | ~285 | 62% | **95%** | 8-12 hours |

---

## Testing Strategy

After each phase, run:

```bash
# Test pattern matching on sample cards
python tools/extract_abilities_to_template.py

# Verify output in data/abilities_extracted.json
# Check for:
# 1. Character names recognized
# 2. Complex conditions parsed
# 3. Keywords identified
# 4. Success mechanics tracked
```

---

## Critical Issues to Address

### Issue 1: Character Name Coverage
**Problem**: Abilities like "「穂乃果」がいる場合" fail because character names aren't in patterns  
**Solution**: Add 50 character patterns + implement character → group mapping  
**Blocker**: YES (affects ~15-20% of cards)

### Issue 2: AND/OR Conditions  
**Problem**: Multi-condition abilities like "X がいて、かつ、Y の場合" parse incorrectly  
**Solution**: Implement conditional operator recognition  
**Blocker**: YES (affects ~10-15% of cards)

### Issue 3: Keyword Recognition
**Problem**: Batontouch, support, and other keywords not recognized  
**Solution**: Add formal keyword patterns from rules.txt section 11  
**Blocker**: YES (affects ~20% of cards)

### Issue 4: Success Mechanics
**Problem**: Win/loss conditions and challenge outcomes not tracked  
**Solution**: Add live_success_* and live_failure_* patterns  
**Blocker**: MEDIUM (affects ~8-10% of cards)

---

## Files to Modify

1. **[extract_abilities_to_template.py](../tools/extract_abilities_to_template.py)** - Add ~200 new patterns in DSL_PATTERNS section
2. **[RULES_TO_PATTERNS_MAPPING.md](./RULES_TO_PATTERNS_MAPPING.md)** - Already created, update with progress
3. **[metadata.json](../data/metadata.json)** - Reference for data extraction (read-only)
4. **[cards_compiled.json](../data/cards_compiled.json)** - For test validation (read-only)

---

## Success Criteria

- [ ] Character name patterns: 0 → 50 (100% of characters)
- [ ] Unit name patterns: 0 → 18 (100% of units)
- [ ] Complex condition support: Partial → Full (AND/OR/NOT)
- [ ] Keyword coverage: 20% → 85%
- [ ] Success mechanics: 0% → 80%
- [ ] Overall coverage: 62% → 89%
- [ ] No regression on existing patterns
- [ ] All patterns documented with rule references

---

## Next Immediate Actions

1. **TODAY**: 
   - Review this action plan
   - Extract character/unit names from metadata.json
   
2. **TOMORROW**:
   - Generate character/unit pattern templates
   - Add patterns to extract_abilities_to_template.py
   - Test coverage percentage

3. **THIS WEEK**:
   - Implement AND/OR/NOT conditions
   - Add keyword patterns
   - Run comprehensive validation

---

## Questions/Clarifications Needed

Before implementation, clarify:

1. Should character patterns match both full names (上原歩夢) and possibly shortened versions?
2. Are there keyword type categorizations beyond batontouch/support?
3. Should success mechanics track intermediate score for partial successes?
4. Do energy deck operations need full search/sort capabilities?

---

**Status**: ✅ Analysis Complete - Ready for Phase 1 Implementation
