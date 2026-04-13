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
