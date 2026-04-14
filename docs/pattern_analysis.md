# DSL Pattern Analysis

## Current Ability-Level Patterns

### Good Patterns (Simple Variable Replacements)
These patterns are specific enough to be useful as-is:

1. **ability_trigger_condition_choice_options** - Very specific with multiple constraints
2. **ability_trigger_choice_options** - Specific structure with bullet options
3. **ability_trigger_only** - Just the trigger icon
4. **ability_trigger_draw_discard** - Trigger + draw X + discard Y
5. **ability_trigger_look_top** - Trigger + look at top X cards
6. **ability_trigger_discard_top** - Trigger + discard top X cards

### Patterns Needing Granularization (Too Broad)

#### 1. ability_trigger_simple (337 matches)
- **Current**: `TRIGGER EFFECT。` (effect is generic `.+`)
- **Problem**: Effect can be anything - too broad
- **Examples from data**:
  - Score modifications: "このカードのスコアを+１する"
  - State changes: "自分のステージにいるすべてのメンバーをアクティブにする"
  - Card placement: "自分のデッキの上からカードを4枚見る。その中からカードを2枚手札に加える"
  - Resource gain: "自分のステージにいる『Aqours』のメンバーは{{icon_blade.png|ブレード}}を得る"
- **Should split into**:
  - Score modification patterns
  - State change patterns (activate, wait, etc.)
  - Look/add patterns
  - Placement patterns
  - Resource gain patterns

#### 2. ability_trigger_cost (206 matches)
- **Current**: `TRIGGER COST：EFFECT。` (cost and effect are generic `.+`)
- **Problem**: Costs and effects vary widely
- **Cost examples**:
  - "手札を1枚控え室に置いてもよい"
  - "このメンバーをステージから控え室に置く"
  - "このメンバーをウェイトにし、手札を1枚控え室に置いてもよい"
  - "{{icon_energy.png|E}}支払ってもよい"
  - "{{turn1.png|ターン1回}}手札を1枚控え室に置く"
- **Effect examples**:
  - Card draw/search
  - Member staging
  - Resource gain
  - Score modification
- **Should split into**:
  - Cost-specific patterns (discard hand, discard member, pay energy, etc.)
  - Combined with effect-specific patterns

#### 3. ability_trigger_gain_until_end
- **Current**: `TRIGGER ライブ終了時まで、RESOURCEを得る。` (resource is generic `.+`)
- **Problem**: Resource varies widely
- **Examples**:
  - "{{icon_blade.png|ブレード}}" - simple blade
  - Complex conditions: "自分のステージにいる「澁谷かのん」1人は{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る"
  - Per-unit: "自分の手札2枚につき、{{icon_blade.png|ブレード}}"
  - Abilities: "「{{jyouji.png|常時}}ライブの合計スコアを+１する。」"
- **Should split into**:
  - Simple resource gain (blade, heart, etc.)
  - Per-unit resource gain
  - Ability gain
  - Conditional resource gain

#### 4. ability_trigger_condition
- **Current**: `TRIGGER CONDITIONがある場合、EFFECT。` (condition and effect are generic `.+`)
- **Problem**: Both condition and effect vary widely
- **Should split into**:
  - Card presence conditions
  - Score threshold conditions
  - Member count conditions
  - Combined with effect-specific patterns

#### 5. ability_trigger_per_unit
- **Current**: `TRIGGER UNITにつき、RESOURCEを得る。` (unit and resource are generic `.+`)
- **Problem**: Unit and resource vary
- **Should split into**:
  - Per-card patterns
  - Per-heart patterns
  - Per-energy patterns
  - Per-member patterns
  - Combined with resource-specific patterns

### Recommendation Priority
1. **Highest**: ability_trigger_simple (337 matches) - biggest impact
2. **High**: ability_trigger_cost (206 matches) - second biggest
3. **Medium**: ability_trigger_gain_until_end - moderate matches but complex variations
4. **Medium**: ability_trigger_condition - moderate matches
5. **Lower**: ability_trigger_per_unit - fewer matches

---

## New Analysis: Real Examples from Actual Ability Texts

### Analysis Method
Ran `analyze_long_abilities.py` on cards.json to find longest abilities (>100 chars) and analyze their structure.

### Key Finding: "Long" Abilities Are Often Just Repetitions
Many abilities marked as "long" are actually just multiple simple sentences repeated:

**Example: 鬼塚冬毬 (312 characters)**
```
{{jyouji.png|常時}}【左サイド】{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。
{{jyouji.png|常時}}{{center.png|センター}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。
{{jyouji.png|常時}}【右サイド】{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_05.png|heart05}}を得る。
```
- Structure: `[TRIGGER] [POSITION] [RESOURCE]を得る` repeated 3 times
- This is NOT complex - just 3 simple clauses

### Real Complex Ability Example

**Example: Bloom the smile, Bloom the dream! (303 characters)**
```
{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい。
```

**Breakdown:**
- Trigger: `{{live_start.png|ライブ開始時}}`
- Condition: `自分のステージに『蓮ノ空』のメンバーがいる場合`
- Effect: `このカードを成功させるための必要ハートは、[options]のうち、選んだ1つにしてもよい`

**Game Terms (should be captured as variables):**
- Triggers: `{{jyouji.png|常時}}`, `{{live_start.png|ライブ開始時}}`, etc.
- Zones: `自分`, `手札`, `ステージ`, `控え室`, `デッキ`
- Resources: `ハート`, `ブレード`, `エネルギー`
- Actions: `得る`, `置く`, `加える`, `見る`, `選ぶ`
- Numbers: `1`, `2`, `3`, etc.
- Groups: `『μ's』`, `『蓮ノ空』`

**Particles (NOT game terms - should NOT be captured):**
- `の`, `を`, `に`, `が`, `から`, `で`, `と`, `へ`

### Sentence Skeleton Patterns Identified

1. **Trigger + Effect**
   - `[TRIGGER] [EFFECT]`
   - Example: `{{toujyou.png|登場}}自分の控え室からライブカードを1枚手札に加える。`

2. **Conditional Effect**
   - `[CONDITION]場合、[EFFECT]`
   - `[CONDITION]とき、[EFFECT]`
   - Example: `自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。`

3. **Cost-Effect**
   - `[COST]：[EFFECT]`
   - Example: `このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。`

4. **Zone Movement**
   - `[SOURCE]から[TARGET]に[ACTION]`
   - `[SOURCE]の[TARGET]を[ACTION]`
   - Example: `自分のデッキの上からカードを5枚見る。`

5. **Selection**
   - `[OPTIONS]から[NUMBER]つ選ぶ`
   - Example: `{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。`

6. **Optional Action**
   - `[ACTION]してもよい`
   - Example: `手札を1枚控え室に置いてもよい`

7. **Per-Unit Effect**
   - `[SOURCE][NUMBER]枚につき、[EFFECT]`
   - Example: `自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}を得る。`

### What Needs To Be Done

#### Problem with Current Approach
Current patterns use broad regex like `([^。]+)` which captures entire clauses as variables. This causes:
- **Heavy overlap** between patterns
- **Variables capture clauses instead of atomic game terms**
- **Non-decomposed patterns** that don't separate game terms from grammar

#### Required Approach
1. **Create non-overlapping sentence skeletons** with fixed structure
2. **Variables should capture ONLY atomic game terms**:
   - Triggers (icon patterns)
   - Zones (手札, ステージ, etc.)
   - Resources (ハート, ブレード, etc.)
   - Actions (得る, 置く, etc.)
   - Numbers
   - Groups (『...』)
3. **Particles should NOT be captured** - they're grammar, not game state
4. **Patterns should NOT overlap** - each sentence structure should match exactly one pattern

#### Implementation Strategy
1. Start with atomic patterns for game terms (already have these)
2. Create clause patterns that compose atomic terms with fixed sentence skeletons
3. Ensure clause patterns don't use broad `([^。]+)` captures
4. Test for overlap - if two patterns match the same text, refine them
5. Iterate to 100% coverage with no overlap

#### Next Steps
1. Redesign patterns based on actual sentence structures identified above
2. Remove broad clause patterns that capture clauses instead of atomic terms
3. Add specific sentence skeleton patterns for each structure type
4. Test and iterate until 100% coverage with no overlap

---

## Detailed Sentence Skeleton Analysis: Bloom the smile, Bloom the dream!

### Original Ability
```
{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい。
```

### Component Breakdown

#### Component 1: Trigger
- **Text**: `{{live_start.png|ライブ開始時}}`
- **Skeleton**: `[TRIGGER]`
- **Game Term**: Trigger icon pattern (atomic)
- **Pattern**: `{{live_start\.png\|ライブ開始時}}`

#### Component 2: Zone Presence Condition
- **Text**: `自分のステージに『蓮ノ空』のメンバーがいる場合`
- **Skeleton**: `[SOURCE]の[ZONE]に[GROUP]の[TYPE]がいる場合`
- **Game Terms**:
  - SOURCE: `自分` (self)
  - ZONE: `ステージ` (stage)
  - GROUP: `『蓮ノ空』` (group name)
  - TYPE: `メンバー` (member)
- **Particles (NOT game terms)**: `の`, `に`, `が`
- **Pattern**: `([自分相手])の([ステージ手札控え室デッキ])に『([^』]+)』の(メンバーライブ)がいる場合`

#### Component 3: Cost Modification with Selection
- **Text**: `このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい`
- **Skeleton**: `[TARGET]を成功させるための必要ハートは、[OPTIONS]のうち、選んだ[NUMBER]つにしてもよい`
- **Game Terms**:
  - TARGET: `このカード` (this card)
  - OPTIONS: Multiple heart resource combinations
  - NUMBER: `1`
- **Particles (NOT game terms)**: `を`, `の`, `は`, `の`, `に`, `も`
- **Pattern**: `(このカード)を成功させるための必要ハートは、([^\s]+)のうち、選んだ(\d+)つにしてもよい`

### Sub-Component: Resource Options
- **Text**: `{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}`
- **Skeleton**: `[RESOURCE1]か、[RESOURCE2]か、[RESOURCE3]`
- **Game Terms**: Heart resource combinations
- **Pattern**: `([^\s]+)か、([^\s]+)か、([^\s]+)`

### Complete Sentence Skeleton
```
[TRIGGER] [SOURCE]の[ZONE]に[GROUP]の[TYPE]がいる場合、[TARGET]を成功させるための必要ハートは、[OPTIONS]のうち、選んだ[NUMBER]つにしてもよい
```

### Pattern Hierarchy
1. **Level 1 (Atomic)**: Triggers, zones, resources, actions, numbers
2. **Level 2 (Clause)**: Zone presence condition, cost modification, selection
3. **Level 3 (Sentence)**: Complete conditional effect sentence

### Key Insights
- The ability is a **single sentence** with nested components
- Variables should capture ONLY game terms, not particles
- The structure is: `TRIGGER + CONDITION + EFFECT`
- The effect itself has internal structure: `cost modification + selection + optional`
- No overlap between components - each has distinct structure
