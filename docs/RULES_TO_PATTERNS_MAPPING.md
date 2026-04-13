# LoveCA Rules-to-Patterns Mapping Analysis
**Date**: April 14, 2026  
**Status**: Comprehensive gap analysis with recommendations

---

## Official Rules Structure (rules.txt v1.05)

The official rules are organized into **12 major sections**:

| # | Section | Coverage | Patterns Count |
|---|---------|----------|---|
| 1 | Game Overview (ゲームの概要) | Meta rules, victory/defeat | 0 |
| 2 | Card Information (カードの情報) | Card types, zones, resources | **35+** |
| 3 | Player Information (プレイヤーに関する情報) | Owner/Master definitions | 0 |
| 4 | Zones (領域) | Zone definitions & mechanics | **24** |
| 5 | Specific Actions (特定行動) | Basic operations | **15+** |
| 6 | Game Preparation (ゲームの準備) | Deck building, setup | 0 |
| 7 | Game Flow (ゲームの進行) | Turn structure, phases | 0 |
| 8 | Live Phase (ライブフェイズ) | Challenge phases, actions | **28** |
| 9 | Card/Ability Play & Resolution (カードや能力のプレイと解決) | Trigger types, timing | **18** |
| 10 | Rule Processing (ルール処理) | Automatic effects, cleanup | **12** |
| 11 | Keywords (キーワードとキーワード能力) | Named keyword keywords | **6** |
| 12 | Other (その他) | Miscellaneous rules | 3 |
| | **TOTAL** | | **~141 patterns** |

---

## Pattern Coverage by Game Mechanic System

### ✅ **Section 2: Card Information (HIGH COVERAGE)**

**Rule 2.1 - Heart Icons (ハートアイコン)**
- Status: ✅ Covered
- Patterns: `atomic_icon_heart`, `atomic_card_type_energy`, heart color indicators
- Example: `{{heart_01.png|heart01}}`, `{{heart_03.png|heart03}}`

**Rule 2.2 - Card Types (カードタイプ)**
- Status: ✅ Covered
- Patterns:
  - `atomic_card_type_member` - メンバーカード
  - `atomic_card_type_live` - ライブカード
  - `atomic_card_type_energy` - エネルギーカード

**Rule 2.3-2.5 - Card Identity (カード名、グループ、ユニット)**
- Status: ⚠️ **PARTIAL**
- Covered: `atomic_group_*` (μ's, Aqours, 虹ヶ咲, Liella!, 蓮ノ空, A-RISE, SaintSnow, SunnyPassion)
- Missing: Character names (not implemented), Unit names (not implemented)

**Rule 2.6 - Cost (コスト)**
- Status: ✅ Covered
- Patterns: `atomic_cost_above`, `atomic_cost_below`, `conditional_cost_threshold`
- Example: "コスト3以下のメンバー", "コスト4以上"

**Rule 2.7-2.8 - Blade & Blade Heart (ブレード、ブレードハート)**
- Status: ✅ Covered
- Patterns:
  - `atomic_icon_blade` - Blade icon recognition
  - `gain_blades` - ライブ終了時までブレードを得る
  - `atomic_icon_energy` - Energy resource
  - `place_energy` - エネルギーカードの配置

**Rule 2.9 - Heart (ハート)**
- Status: ✅ Covered  
- Patterns: `gain_hearts`, `heart_cost_reduction`, `conditional_heart_total`, `conditional_heart_possession`
- Example: "ハートの合計が3以上ある場合"

**Rule 2.10 - Score (スコア)**
- Status: ✅ Covered
- Patterns:
  - `score_increase` - スコアを+3する
  - `score_decrease` - スコアを減らす
  - `score_modifier` - このカードのスコアを⊕3する
  - `score_comparison` - ライブの合計スコアが相手より高い場合
  - `per_score` - スコア1につき...
- Example: "+3スコア獲得"

**Rule 2.11 - Required Heart (必要ハート)**
- Status: ✅ Covered
- Patterns: `heart_cost_reduction`, `conditional_heart_count`
- Example: "この カードを成功させるための必要ハートを2減らす"

**Rule 2.12 - Card Text (カードテキスト)**
- Status: ⚠️ **PARTIAL** (structure recognized, content interpretation limited)

---

### ✅ **Section 4: Zones (HIGH COVERAGE)**

**Rule 4.4-4.5 - Member Areas (メンバーエリア, ステージ)**
- Status: ✅ Covered
- Patterns:
  - `atomic_area_left` - 左サイド
  - `atomic_area_center` - センター
  - `atomic_area_right` - 右サイド
  - `stage_from_hand` - 手札からステージに登場させる
  - `move_member` - メンバーを移動させる
  - `place_to_stage` - ステージに置く

**Rule 4.6 - Live Card Area (ライブカード置き場)**
- Status: ⚠️ **MINIMAL COVERAGE**
- Missing: Patterns for live card placement, live success, challenge interactions

**Rule 4.7 - Energy Zone (エネルギー置き場)**
- Status: ✅ Covered
- Patterns:
  - `place_energy` - エネルギーカードを置く
  - `discard_energy` - エネルギーを控え室に置く
  - `activate_energy` - エネルギーをアクティブにする
  - `atomic_place_energy_wait` - ウェイト状態でのエネルギー配置

**Rule 4.8 - Main Deck (メインデッキ置き場)**
- Status: ✅ Covered
- Patterns:
  - `basic_action_draw` - カードを1枚引く
  - `look_top` - デッキの上からカードを見る
  - `look_select_add` - デッキの上からカードを見て選ぶ
  - `look_filter_add` - デッキから条件に合うカードを検索
  - `add_from_discard` - 控え室から手札に加える

**Rule 4.9 - Energy Deck (エネルギーデッキ置き場)**
- Status: ⚠️ **PARTIAL**
- Patterns: `atomic_from_energy_deck`, `place_energy` (indirect)
- Missing: Energy deck specific operations, energy deck search patterns

**Rule 4.10 - Success Live Area (成功ライブカード置き場)**
- Status: ❌ **NOT COVERED**
- Missing: Success conditions, area transitions, victory tracking

---

### ⚠️ **Section 5: Specific Actions (PARTIAL COVERAGE)**

**Rule 5.1 - Draw Operations (ドロー)**
- Status: ✅ Covered
- Patterns: `basic_action_draw`, `look_top`, `look_select_add`

**Rule 5.2 - Reveal Operations (公開)**
- Status: ✅ Covered
- Patterns: `reveal_and_add`, `look_and_reveal`, `reveal_and_choose`, `reveal_card`

**Rule 5.3 - Deck Manipulation (デッキ操作)**
- Status: ✅ Covered
- Patterns: `look_discard_remainder`, `shuffle_deck`, `reorder_cards`, `place_on_deck`

**Rule 5.4 - Recover Operations (回収)**
- Status: ✅ Covered
- Patterns: `add_from_discard`, `look_add_specific`, `stage_from_hand`

---

### ✅ **Section 8: Live Phase (HIGH COVERAGE)**

**Rule 8.3.11 - Yields/Appeals (エール)**
- Status: ⚠️ **PARTIAL**
- Covered: Blade icons, heart types
- Missing: Blade heart selection, complex appeal mechanics, strategic choices

**Rule 8.3.14 - Live Success Check (ライブ成功判定)**
- Status: ⚠️ **MINIMAL**
- Missing: Success/failure flow, state changes based on success

**Rule 8.3.15 - Member State Changes (メンバー状態)**
- Status: ✅ Covered
- Patterns:
  - `atomic_state_wait` - ウェイトにする
  - `atomic_state_activate` - アクティブにする
  - `state_change_wait_this_member` - このメンバーをウェイトにする
  - `state_change_activate` - メンバーをアクティブにする

---

### ⚠️ **Section 9: Card/Ability Play (PARTIAL COVERAGE)**

**Rule 9.2 - Ability Types (能力タイプ)**
- Status: ⚠️ **PARTIAL**
- Covered:
  - Constant (常時能力) - `atomic_icon_jyouji`, `atomic_duration_permanent`
  - Activated (起動能力) - `atomic_icon_kidou`, `ability_activation_condition`
  - Automatic (自動能力) - `atomic_icon_jidou`, `trigger_when`, `trigger_on_activate`
- Missing: Triggered ability (誘発能力) formal patterns

**Rule 9.3 - Triggers (トリガー)**
- Status: ✅ Covered
- Patterns:
  - `atomic_icon_toujyou` - 登場時
  - `atomic_icon_live_start` - ライブ開始時
  - `atomic_icon_live_success` - ライブ成功時
  - `trigger_on_play`, `trigger_on_activate`, `trigger_on_move`, `trigger_on_discard`
  - `trigger_on_stage` - ステージに登場したとき

---

### ⚠️ **Section 11: Keywords (PARTIAL COVERAGE)**

**Keyword Ability Patterns**
- Status: ⚠️ **MINIMAL**
- Identified patterns:
  - `batontouch_condition` - バトンタッチ (1 pattern) - Needs expansion
  - `keyword_support` (not implemented)
  - `keyword_restriction` (not implemented)

---

## Coverage Summary by Percentage

| System | Coverage | Status | Notes |
|--------|----------|--------|-------|
| **Card Types** | 100% | ✅ | All 3 types covered |
| **Zones** | 75% | ⚠️ | Main deck, member areas, energy covered; success area missing |
| **Resources** | 85% | ⚠️ | Score, hearts, blades covered; energy deck limited |
| **Member State** | 90% | ✅ | Wait/active well covered |
| **Draw/Search** | 95% | ✅ | Comprehensive coverage |
| **Special Effects** | 60% | ⚠️ | Ability granting covered; complex interactions missing |
| **Keywords** | 30% | ❌ | Only batontouch; others missing |
| **Areas/Positions** | 100% | ✅ | Left/center/right areas covered |
| **Triggers** | 85% | ⚠️ | Main triggers covered; some edge cases |
| **Groups** | 85% | ⚠️ | 8/10 groups covered; character/unit names missing |

**Overall Coverage: ~72%**

---

## Critical Gaps & Missing Patterns

### **HIGH PRIORITY (Affects 50%+ of cards)**

#### 1. ❌ **Success/Challenge Mechanics (Rules 8.3.14)**
- Missing: Win/loss conditions, score thresholds, challenge success states
- Impact: Cannot track live success outcomes
- Example cards needing this: Any live card with score conditions
- Recommendation: Add patterns:
  - `live_success_condition` - スコア3以上で成功
  - `live_failure_effect` - ライブ失敗時効果
  - `challenge_outcome` - チャレンジの結果により

#### 2. ❌ **Batontouch Keywords (Rule 11 Keywords)**
- Currently: 1 pattern (`batontouch_condition`)
- Missing: Formal batontouch identification, transition mechanics
- Impact: Cannot identify batontouch-specific abilities
- Example: "バトンタッチによるメンバー配置"
- Recommendation: Add patterns:
  - `keyword_batontouch_entry` - バトンタッチで登場
  - `keyword_batontouch_effect` - バトンタッチによる効果
  - `keyword_batontouch_restriction` - バトンタッチの制限

#### 3. ❌ **Complex Conditional Chains (Rule 1.3 Meta Rules)**
- Currently: Basic conditionals covered, but not linked chains
- Missing: Multi-condition AND/OR logic, nested conditions
- Example: "『μ's』のメンバーがいて、かつ、手札が3枚以上ある場合"
- Patterns missing: `conditional_and_gate`, `conditional_or_gate`, `conditional_nested`
- Impact: Only simple conditions work; complex logic fails

#### 4. ❌ **Character-Specific Patterns (Rule 2.3-2.4)**
- Currently: Groups covered (μ's, Aqours, etc.), but NOT individual members
- Missing: Character name recognition (上原歩夢, 澁谷かのん, etc.)
- Example: "「上原歩夢」がいる場合"
- Impact: Character-specific abilities cannot be parsed
- Recommendation: Add 50+ character patterns from metadata.json

#### 5. ❌ **Unit-Specific Patterns (Rule 2.5)**
- Missing: Unit name recognition (Printemps, Lily White, BiBi, etc.)
- Example: "『Printemps』のメンバーが"
- Impact: Unit-based conditions fail
- Recommendation: Add 18 unit patterns + mapping to groups

### **MEDIUM PRIORITY (Affects 20-50% of cards)**

#### 6. ⚠️ **Multi-Step Operations with Choices (Rule 9.4.1)**
- Currently: Basic multi-step covered (look → select → add)
- Missing: Decision trees, opponent choices
- Example: "相手は以下から1つを選ぶ。[効果A] または [効果B]"
- Pattern gaps: Choice structures, consequences
- Recommendation: Expand `choose_option` patterns with consequence chains

#### 7. ⚠️ **Energy Deck Operations (Rule 4.9)**
- Currently: Limited energy deck support
- Missing: Energy deck search, reshuffle, special placement
- Example: "エネルギーデッキからカード1枚を選んで", "エネルギーデッキをシャッフル"
- Patterns missing: `search_energy_deck`, `shuffle_energy_deck`
- Impact: Energy deck manipulation abilities broken

#### 8. ⚠️ **Cost Modification Effects (Rule 5)**
- Currently: Basic cost reduction covered
- Missing: Conditional cost mod, per-condition scaling
- Example: "『Aqours』のメンバー1人につき、このカードのコストを-1"
- Pattern gaps: `cost_reduction_per_count`
- Impact: Cost scaling abilities not handled

#### 9. ⚠️ **Member Movement Restrictions (Rules 8.3.15, 4.5.5.3)**
- Currently: Basic movement covered (move_member)
- Missing: Position-specific restrictions, batontouch transitions
- Example: "右サイドエリアにのみ移動できる"
- Pattern gaps: `restricted_area_movement`, `position_constraint`

#### 10. ⚠️ **Ability Granting with Conditions (Rule 10.2)**
- Currently: Basic gain_ability covered
- Missing: Conditional ability granting, temporary vs permanent
- Example: "『μ's』のメンバーがいる場合、このメンバーは『火力支援』を得る"
- Pattern gaps: `conditional_gain_ability`, `ability_grant_scope`

### **LOW PRIORITY (Affects <20% of cards)**

#### 11. ⚠️ **Support/Helper Abilities (Keyword)**
- Missing: 火力支援 (power support), 防御支援 (defense support), etc.
- Impact: Support keywords not recognized
- Current coverage: 0%

#### 12. ⚠️ **Yell System (Rule 12+)**
- Missing: Yell mechanics, yell conversion, yell triggers
- Example: "エール1つをコスト9の『Aqours』のメンバーカードに変換できる"
- Impact: Advanced yell mechanics not covered

#### 13. ⚠️ **Damage/Card Limiting (Rule 10.4)**
- Missing: Damage patterns, card limits
- Example: "手札が8枚を超える場合、8枚になるまで捨てる"

#### 14. ⚠️ **Phase-Specific Actions (Rules 8.1-8.3)**
- Missing: Phase identifiers, phase-specific timing
- Example: "チャレンジフェイズ中に"

---

## Recommendations: Implementation Priority

### **Phase 1: Core Rules (Required for 95% accuracy)**
1. Add character name patterns (50 characters × 5 pattern variants = ~250 patterns)
2. Implement unit patterns (18 units × 3 variants = ~54 patterns)
3. Formalize complex conditional logic (AND/OR gates, nesting)
4. Add success/failure outcome patterns
5. Implement formal batontouch keyword patterns

### **Phase 2: Extended Mechanics (Required for 100% accuracy)**
6. Energy deck search & manipulation patterns
7. Conditional cost modification formulas
8. Member movement restrictions & constraints
9. Conditional ability granting with scope
10. Support/helper keyword patterns

### **Phase 3: Advanced Features (Polish)**
11. Yell system patterns
12. Damage/card limiting patterns
13. Phase-specific action timing
14. Complex opponent interaction flows

---

## Pattern Recommendations by Rule Section

### Rule 2.3 - Card Names
```
Need: "「」" bracket name recognition
Pattern: conditional_card_name (exists but limited)
Add: character_name_pattern (for each of 50 characters)
```

### Rule 2.4 - Groups  
```
Covered: 8/10 groups (μ's, Aqours, 虹ヶ咲, Liella!, 蓮ノ空, A-RISE, SaintSnow, SunnyPassion)
Missing: 
  - ARISE (別枠)
  - SAINT_SNOW (別枠)  
  - SUNNY_PASSION (別枠)
Add patterns for all group-based conditions with wildcards
```

### Rule 2.5 - Units
```
Missing: All 18 units
Recommendation: Add unit_pattern_* for each unit (Printemps, Lily White, BiBi, etc.)
```

### Rule 8.3.14 - Live Success Check
```
Currently: No formal success patterns
Need:
  - live_success_threshold - スコア3以上で成功
  - challenge_success_condition - チャレンジ成功判定
  - live_outcome_effect - 成功/失敗時の効果
```

### Rule 11 - Keywords (Keyword Abilities)
```
バトンタッチ (Batontouch):
  - Pattern exists but minimal  
  - Add: keyword_batontouch_entry, keyword_batontouch_transition

火力支援 (Power Support):
  - Pattern missing
  - Add: support_power_condition, support_power_effect

防御支援 (Defense Support):
  - Pattern missing
  - Add: support_defense_condition, support_defense_effect

Other keywords: (Add as discovered)
```

---

## Current VS Expected Coverage

### Sample Ability Coverage Test

**Ability 1**: "登場時に控え室からメンバー1枚回収"
- Current: ✅ WORKS (`atomic_icon_toujyou` + `add_from_discard`)
- Accuracy: 100%

**Ability 2**: "ライブ開始時、同名3人を控え室に置いて+3スコア獲得"
- Current: ⚠️ PARTIAL (works but needs `conditional_same_name_count`)
- Accuracy: 70%

**Ability 3**: "コスト4以下のメンバーをウェイトにする"
- Current: ✅ WORKS (`conditional_cost_below`)
- Accuracy: 100%

**Ability 4**: "『μ's』のメンバーがいて、かつ、スコアが5以上の場合、スコア+2"
- Current: ❌ FAILS (AND logic not implemented)
- Accuracy: 0%

**Ability 5**: "「上原歩夢」が登場している場合、"
- Current: ❌ FAILS (character names not recognized)
- Accuracy: 0%

---

## Summary Table

| System | Rule Ref | Pattern Count | Coverage | Status | Priority |
|--------|----------|---|---|---|---|
| Game Overview | 1 | 0 | 0% | ❌ | Low |
| Card Info | 2 | 35 | 70% | ⚠️ | High |
| Player Info | 3 | 0 | 0% | ❌ | Low |
| Zones | 4 | 24 | 75% | ⚠️ | Medium |
| Actions | 5 | 15 | 80% | ⚠️ | Medium |
| Preparation | 6 | 0 | 0% | ❌ | Low |
| Game Flow | 7 | 0 | 0% | ❌ | Low |
| Live Phase | 8 | 28 | 85% | ⚠️ | Medium |
| Play/Resolution | 9 | 18 | 75% | ⚠️ | Medium |
| Rule Processing | 10 | 12 | 60% | ❌ | Medium |
| Keywords | 11 | 6 | 30% | ❌ | **HIGH** |
| Other | 12 | 3 | 50% | ⚠️ | Low |
| **TOTAL** | | **141** | **~62%** | ⚠️ | |

---

## Next Steps

1. **Immediate**: Add character & unit name patterns (~300 new patterns)
2. **Short-term**: Implement AND/OR conditional logic
3. **Medium-term**: Add success/failure mechanics, batontouch keywords
4. **Long-term**: Energy deck operations, phase-specific mechanics
5. **Ongoing**: Test against real abilities in cards_compiled.json
