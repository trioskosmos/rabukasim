# Official Rules Mapping - Quick Status

**Analysis Date**: April 14, 2026  
**Overall Pattern Coverage**: 62% of official rules

---

## ✅ WELL COVERED (>80%)

| Rule Section | Coverage | Key Patterns | Notes |
|--------------|----------|---|---|
| **2.2** Card Types | 100% | `atomic_card_type_*` (3) | All types: Member, Live, Energy |
| **2.9** Hearts | 95% | `gain_hearts`, `heart_cost_*` (5) | ハート system complete |
| **2.10** Score | 95% | `score_increase`, `score_modifier` (6) | スコア system complete |
| **4.4-4.5** Member Areas | 95% | `atomic_area_*`, `place_to_stage` (12) | Left/Center/Right areas |
| **5.1** Draw Ops | 95% | `basic_action_draw`, `look_*` (8) | Deck drawing covered |
| **5.2** Reveal | 90% | `reveal_*`, `look_and_reveal` (6) | 公開 mechanics |
| **5.4** Recover | 90% | `add_from_discard` (3) | 回収 basics |
| **8.3.15** State Changes | 90% | `state_change_*`, `atomic_state_*` (8) | Wait/Active states |
| **4.5** Positions | 100% | `atomic_area_left/center/right` (3) | Area positioning |

**Total High-Coverage Patterns**: ~54

---

## ⚠️ PARTIAL COVERAGE (30-80%)

| Rule Section | Coverage | Key Gaps | Impact |
|--------------|----------|----------|--------|
| **2.1** Heart Icons | 75% | Color variants incomplete | Minor - basic colors work |
| **2.4** Groups | 80% | 8/10 groups covered | Medium - ARISE/SAINT_SNOW missing |
| **4.6** Live Card Area | 40% | Success mechanics missing | Medium - limited live tracking |
| **4.7-4.9** Energy Zones | 60% | Energy deck search missing | Medium - energy deck broken |
| **8.3.11** Yields/Appeals | 50% | Blade heart selection incomplete | Medium - blade counting works |
| **9.2-9.3** Ability Types/Triggers | 75% | Some trigger types incomplete | Medium - most triggers work |
| **10.2** Ability Effects | 60% | Conditional ability granting limited | Medium - basic granting works |

**Total Partial-Coverage Patterns**: ~40

---

## ❌ NOT COVERED (<30%)

| Rule Section | Coverage | What's Missing | Impact |
|--------------|----------|---|---|
| **2.3-2.5** Card Identity | 0% | Character names (50+), unit names (18) | **HIGH** - Personal name abilities fail |
| **8.3.14** Live Success | 0% | Win/loss conditions, score thresholds | **HIGH** - Success tracking broken |
| **11** Keywords | 20% | Batontouch (minimal), Support abilities | **HIGH** - Keywords not recognized |
| **1** Overview | 0% | Victory/defeat conditions | LOW - Meta rules |
| **3** Player Info | 0% | Owner/Master definitions | LOW - Info only |
| **6-7** Preparation/Flow | 0% | Game setup, turn phases | LOW - Structural only |
| **12** Other | 20% | Yell system, damage limits | LOW-MED - Advanced mechanics |

**Total Missing Patterns**: ~47

---

## Rule Section Breakdown

### Section 1: Game Overview (ゲームの概要)
- ❌ Victory/defeat mechanics
- ❌ Rule precedence
- ❌ Player limitations
- **Impact**: None (foundational - not pattern-based)

### Section 2: Card Information (カードの情報)
- ✅ 35/50 patterns present
- ⚠️ Missing: Character names, unit names, full group coverage
- **Key Gap**: No character-specific patterns (e.g., "「上原歩夢」")

### Section 3: Player Information (プレイヤーに関する情報)
- ❌ Owner/Master definitions
- **Impact**: None (conceptual only)

### Section 4: Zones (領域)
- ✅ 24/32 patterns covered
- ⚠️ Missing: Success pile mechanics, energy deck search
- **Key Gap**: "成功ライブカード置き場" (success pile) has no patterns

### Section 5: Specific Actions (特定行動)
- ✅ 15/18 patterns covered
- ⚠️ Missing: Shuffle variations, complex recovery
- **Status**: Nearly complete

### Section 6: Game Preparation (ゲームの準備)
- ❌ Deck building rules
- **Impact**: None (setup only)

### Section 7: Game Flow (ゲームの進行)
- ❌ Turn structure
- **Impact**: None (time-based only)

### Section 8: Live Phase (ライブフェイズ)
- ✅ 28/33 patterns covered
- ⚠️ Missing: Live success conditions, failure outcomes
- **Key Gap**: Challenge outcomes not tracked

### Section 9: Card/Ability Play (カードや能力のプレイと解決)
- ✅ 18/24 patterns covered
- ⚠️ Missing: Timing interactions, advanced triggering
- **Status**: Good coverage

### Section 10: Rule Processing (ルール処理)
- ✅ 12/20 patterns covered
- ⚠️ Missing: Automatic cleanup, end-of-phase effects
- **Status**: Partial

### Section 11: Keywords (キーワード能力)
- ⚠️ 6/20 patterns covered
- ❌ Missing: Batontouch (formal), 火力支援, 防御支援, etc.
- **Key Gap**: Only 30% keyword coverage

### Section 12: Other (その他)
- ❌ Yell mechanics
- ⚠️ Advanced effects
- **Impact**: Low - specialist features

---

## Pattern Deficiencies by Type

### Category: **CHARACTER NAMES** (Critical)
- Expected: 50+ individual character patterns
- Current: 0
- Examples needed:
  - 上原歩夢 (Uehra Ayumu)
  - 澁谷かのん (Shibuya Kanon)
  - 日野下花帆 (Hinoshita Kaho)
  - ... (47 more characters)
- **Fix**: Implement `character_*` patterns for each

### Category: **UNIT NAMES** (High Priority)
- Expected: 18 unit patterns
- Current: 0
- Examples:
  - Printemps, Lily White, BiBi
  - CYaRon!, AZALEA, Guilty Kiss
  - ... (12 more units)
- **Fix**: Implement `unit_*` patterns

### Category: **COMPLEX CONDITIONS** (High Priority)
- Expected: AND/OR/NOT logic gates
- Current: Simple conditions only
- Missing: Multi-condition chains
- **Example**: "『μ's』のメンバーがいて、かつ、手札が3枚以上の場合"
- **Fix**: Implement `conditional_and`, `conditional_or`, `conditional_not`

### Category: **KEYWORD ABILITIES** (High Priority)
- Expected: ~15 keyword types + variants
- Current: ~2 (batontouch minimal, others absent)
- Missing:
  - バトンタッチ (Batontouch) - formal patterns
  - 火力支援 (Power Support)
  - 防御支援 (Defense Support)
  - Others TBD
- **Fix**: Implement `keyword_*` patterns for each

### Category: **SUCCESS/CHALLENGE** (High Priority)
- Expected: Success conditions, outcomes
- Current: 0 specific patterns
- Missing:
  - "スコア3以上で成功"
  - "ライブ失敗時に..."
  - Challenge flow patterns
- **Fix**: Implement `live_success_*` patterns

### Category: **ENERGY DECK** (Medium Priority)
- Expected: Search, shuffle, special placement
- Current: Basic reference only (`atomic_from_energy_deck`)
- Missing: "エネルギーデッキからカード1枚を選んで"
- **Fix**: Implement `search_energy_deck`, `shuffle_energy_deck`

### Category: **CONDITIONAL ABILITY GRANT** (Medium Priority)
- Expected: Conditional ability granting with target scoping
- Current: Basic `gain_ability` only
- Missing: "『Aqours』のメンバーがいる場合、このメンバーは..."
- **Fix**: Implement `conditional_gain_ability_scoped`

---

## Test Results: Sample Abilities

| Ability Text | Pattern Match | Expected | Actual | Accuracy |
|---|---|---|---|---|
| 登場時に回収 | ✅ | Works | Works | **100%** |
| コスト3以下ウェイト | ✅ | Works | Works | **100%** |
| ハート合計+3 | ✅ | Works | Works | **100%** |
| 「上原歩夢」いる場合 | ❌ | Works | Fails | **0%** |
| 『Aqours』×3人＆スコア5以上 | ❌ | Works | Fails | **0%** |
| エネルギーデッキ検索 | ⚠️ | Works | Partial | **40%** |
| バトンタッチで登場 | ⚠️ | Works | Minimal | **20%** |
| 火力支援能力 | ❌ | Works | Fails | **0%** |

---

## Implementation Requirements

### **Must Have** (Blocking >30% of cards)
- [ ] Character name patterns (50 characters)
- [ ] Unit name patterns (18 units)
- [ ] Conditional AND/OR/NOT logic
- [ ] Live success/failure mechanics
- [ ] Formal batontouch keywords

### **Should Have** (Blocking 10-30% of cards)
- [ ] Energy deck search patterns
- [ ] Conditional ability granting
- [ ] Support keyword patterns
- [ ] Complex multi-condition chains

### **Nice to Have** (Blocking <10% of cards)
- [ ] Yell mechanics
- [ ] Damage/card limits
- [ ] Phase-specific actions
- [ ] Advanced interactions

---

## Files & Documentation

- **Full Analysis**: [RULES_TO_PATTERNS_MAPPING.md](RULES_TO_PATTERNS_MAPPING.md)
- **Source Rules**: [rules.txt](../data/rules.txt)
- **Pattern File**: [extract_abilities_to_template.py](../tools/extract_abilities_to_template.py)
- **Card Database**: [cards_compiled.json](../data/cards_compiled.json)

---

## Recommendations for Next Steps

1. **Parse metadata.json** for character/unit names and create patterns
2. **Implement AND/OR condition logic** for complex filters
3. **Add keyword ability recognition** with formal mappings
4. **Test against cards_compiled.json** to verify coverage
5. **Document discovered patterns** in canonical model
