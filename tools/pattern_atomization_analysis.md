# Pattern Atomization Analysis

## Overview
This document analyzes the current state of patterns in `extract_abilities_to_template.py`, comparing atomized patterns (with variables) vs non-atomized patterns (with hardcoded literals).

## Pattern Categories

### 1. DSL_PATTERNS (Atomized with Variables)
These patterns use template variables like ⟦SOURCE⟧, ⟦ZONE⟧, ⟦NUMBER⟧, etc.

**Example: zone_card_except_group_per_card_cost_reduce**
```python
{
    "name": "zone_card_except_group_per_card_cost_reduce",
    "regex": "\\b([^。]+)の([^。]+)にある([^。]+)以外の『([^』]+)』の([^。]+)(\\d+)枚につき、([^。]+)の([^。]+)を([^。]+)減らす",
    "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦EXCEPT_CARD⟧以外の『⟦GROUP⟧』の⟦CARD_TYPE⟧⟦NUMBER⟧枚につき、⟦TARGET⟧の⟦COST⟧を⟦MODIFIER⟧減らす",
    "structure": "Zone card except group per card cost reduce"
}
```

**Atomic Elements:**
- ⟦SOURCE⟧ - Source (e.g., 自分の, 相手の)
- ⟦ZONE⟧ - Zone (e.g., 手札, ステージ, 控え室)
- ⟦EXCEPT_CARD⟧ - Exception card type
- ⟦GROUP⟧ - Group name (e.g., μ's, 虹ヶ咲)
- ⟦CARD_TYPE⟧ - Card type (e.g., メンバーカード, ライブカード)
- ⟦NUMBER⟧ - Number/quantity
- ⟦TARGET⟧ - Target (e.g., 手札にあるこのメンバーカード)
- ⟦COST⟧ - Cost attribute
- ⟦MODIFIER⟧ - Modifier (e.g., 1, 2)

### 2. LITERAL_PATTERNS (Hardcoded Literals)
These patterns have hardcoded literals without variables.

**Example: center_turn1_wait_select_public_until_top**
```python
{
    "name": "center_turn1_wait_select_public_until_top",
    "literal": "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。",
    "template": "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。",
    "structure": "Center turn1 wait select public until top",
}
```

**Hardcoded Elements (should be atomized):**
- `{{kidou.png|起動}}` → ⟦TRIGGER⟧
- `{{center.png|センター}}` → ⟦POSITION⟧
- `{{turn1.png|ターン1回}}` → ⟦FREQUENCY⟧
- `手札を1枚控え室に置く` → ⟦COST_ACTION⟧ (手札を⟦NUMBER⟧枚控え室に置く)
- `ライブカードかコスト10以上のメンバーカード` → ⟦SELECTION_OPTIONS⟧
- `コスト10以上` → ⟦COST_CONDITION⟧ (コスト⟦NUMBER⟧以上)
- `デッキの一番上` → ⟦DECK_POSITION⟧
- `１枚ずつ` → ⟦INCREMENT⟧ (⟦NUMBER⟧枚ずつ)

## Common Atomic Elements to Extract

### Triggers (トリガー)
- `{{toujyou.png|登場}}` → ⟦TRIGGER⟧
- `{{live_start.png|ライブ開始時}}` → ⟦TRIGGER⟧
- `{{kidou.png|起動}}` → ⟦TRIGGER⟧
- `{{jyouji.png|常時}}` → ⟦TRIGGER⟧
- `{{live_success.png|ライブ成功時}}` → ⟦TRIGGER⟧
- `{{jidou.png|自動}}` → ⟦TRIGGER⟧

### Position (位置)
- `{{center.png|センター}}` → ⟦POSITION⟧
- `【左サイド】` → ⟦SIDE⟧
- `【右サイド】` → ⟦SIDE⟧
- `センターエリア` → ⟦AREA⟧
- `エリア` → ⟦AREA⟧

### Frequency (頻度)
- `{{turn1.png|ターン1回}}` → ⟦FREQUENCY⟧
- `［ターン1回］` → ⟦FREQUENCY⟧

### Zones (領域)
- `手札` → ⟦ZONE⟧
- `ステージ` → ⟦ZONE⟧
- `控え室` → ⟦ZONE⟧
- `デッキ` → ⟦ZONE⟧
- `エネルギー置き場` → ⟦ZONE⟧
- `エネルギーデッキ` → ⟦ZONE⟧
- `成功ライブカード置き場` → ⟦ZONE⟧
- `ライブカード置き場` → ⟦ZONE⟧

### Card Types (カードタイプ)
- `メンバーカード` → ⟦CARD_TYPE⟧
- `ライブカード` → ⟦CARD_TYPE⟧
- `エネルギーカード` → ⟦CARD_TYPE⟧

### Groups (グループ)
- `『μ's』` → ⟦GROUP⟧
- `『虹ヶ咲』` → ⟦GROUP⟧
- `『Aqours』` → ⟦GROUP⟧
- `『Liella!』` → ⟦GROUP⟧
- `『Saint Snow』` → ⟦GROUP⟧
- `『5yncri5e!』` → ⟦GROUP⟧
- `『蓮ノ空』` → ⟦GROUP⟧

### Numbers (数字)
- `1枚` → ⟦NUMBER⟧枚
- `2枚` → ⟦NUMBER⟧枚
- `3枚` → ⟦NUMBER⟧枚
- `コスト10` → コスト⟦COST⟧
- `コスト4以下` → コスト⟦COST⟧以下
- `6個以上` → ⟦NUMBER⟧個以上

### Resources (リソース)
- `{{icon_blade.png|ブレード}}` → ⟦RESOURCE⟧
- `{{heart_XX.png|heartXX}}` → ⟦RESOURCE⟧
- `{{icon_energy.png|E}}` → ⟦RESOURCE⟧
- `{{icon_all.png|ハート}}` → ⟦RESOURCE⟧

### Actions (アクション)
- `ウェイトにする` → ⟦STATE⟧
- `アクティブにする` → ⟦STATE⟧
- `引く` → ⟦ACTION⟧
- `置く` → ⟦ACTION⟧
- `加える` → ⟦ACTION⟧
- `得る` → ⟦ACTION⟧
- `選ぶ` → ⟦ACTION⟧
- `公開する` → ⟦ACTION⟧
- `移動する` → ⟦ACTION⟧

### States (状態)
- `ウェイト状態` → ⟦STATE⟧
- `アクティブ状態` → ⟦STATE⟧

### Conditions (条件)
- `場合` → ⟦CONDITION_MARKER⟧
- `かぎり` → ⟦CONDITION_MARKER⟧
- `～以上` → ⟦COMPARISON⟧
- `～以下` → ⟦COMPARISON⟧
- `～より多い` → ⟦COMPARISON⟧
- `～より低い` → ⟦COMPARISON⟧

### Optional Markers (オプションマーカー)
- `してもよい` → ⟦OPTIONAL⟧
- `～まで` → ⟦LIMIT⟧

## Structural Patterns

### Optional Action Pattern
Structure: `⟦COST_ACTION⟧してもよい：⟦EFFECT⟧`

**Examples:**
- `手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。`
- `エネルギーを支払ってもよい：以下から1つを選ぶ。`

### Per-Unit Pattern
Structure: `⟦TARGET⟧⟦NUMBER⟧⟧につき、⟦EFFECT⟧`

**Examples:**
- `メンバー1人につき、{{icon_blade.png|ブレード}}を得る。`
- `カード1枚につき、コストを1減らす。`

### Condition-Action Pattern
Structure: `⟦CONDITION⟧場合、⟦ACTION⟧`

**Examples:**
- `自分のステージにメンバーがいる場合、カードを1枚引く。`
- `エネルギーが10枚以上あるかぎり、{{heart_XX.png|heartXX}}を得る。`

### Zone-to-Zone Transfer Pattern
Structure: `⟦SOURCE⟧の⟦ZONE⟧から⟦CARD⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に⟦ACTION⟧`

**Examples:**
- `自分の控え室からライブカードを1枚手札に加える。`
- `デッキの上からカードを3枚控え室に置く。`

## Detailed Variable Mapping

### Numbers Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| 1枚 | ⟦NUMBER⟧枚 | 手札を1枚控え室に置く, カードを1枚引く |
| 2枚 | ⟦NUMBER⟧枚 | 手札を2枚控え室に置く, {{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る |
| 3枚 | ⟦NUMBER⟧枚 | デッキの上からカードを3枚控え室に置く |
| 5枚 | ⟦NUMBER⟧枚 | 手札が5枚になるまで |
| 6個 | ⟦NUMBER⟧個 | {{heart_02.png|heart02}}が合計6個以上 |
| 10 | ⟦COST⟧ | コスト10以上 |
| 9 | ⟦COST⟧ | コスト9以下 |
| 4 | ⟦NUMBER⟧ | 元々持つ{{icon_blade.png|ブレード}}の数がちょうど4つ |
| 6 | ⟦NUMBER⟧ | スコアの合計が６以上 |
| 9 | ⟦NUMBER⟧ | スコアの合計が９以上 |

### Groups Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| 虹ヶ咲 | ⟦GROUP⟧ | 『虹ヶ咲』のメンバー, 『虹ヶ咲』のライブカード |
| μ's | ⟦GROUP⟧ | 『μ's』のメンバーカード |
| Aqours | ⟦GROUP⟧ | 『Aqours』のメンバー |
| Liella! | ⟦GROUP⟧ | 『Liella!』のメンバーカード |
| SaintSnow | ⟦GROUP⟧ | 『SaintSnow』のメンバー |
| 5yncri5e! | ⟦GROUP⟧ | 『5yncri5e!』のメンバー |
| lilywhite | ⟦GROUP⟧ | 『lilywhite』のメンバー |

### Heart Types Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| {{heart_04.png|heart04}} | ⟦RESOURCE⟧ | {{heart_04.png|heart04}}を得る |
| {{heart_01.png|heart01}} | ⟦RESOURCE⟧ | {{heart_01.png|heart01}}を得る |
| {{heart_05.png|heart05}} | ⟦RESOURCE⟧ | {{heart_05.png|heart05}}を得る |
| {{heart_06.png|heart06}} | ⟦RESOURCE⟧ | {{heart_06.png|heart06}}を得る |
| {{heart_02.png|heart02}} | ⟦RESOURCE⟧ | {{heart_02.png|heart02}}を得る |
| {{heart_00.png|heart0}} | ⟦RESOURCE⟧ | {{heart_00.png|heart0}}減らす |
| ［赤ハート］ | ⟦RESOURCE⟧ | ［赤ハート］［赤ハート］［赤ハート］を得る |

### Card Types Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| メンバーカード | ⟦CARD_TYPE⟧ | メンバーカードを控え室に置く |
| ライブカード | ⟦CARD_TYPE⟧ | ライブカードを手札に加える |
| エネルギーカード | ⟦CARD_TYPE⟧ | エネルギーカードをアクティブにする |

### Zones Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| 手札 | ⟦ZONE⟧ | 手札を控え室に置く |
| ステージ | ⟦ZONE⟧ | ステージにいるメンバー |
| 控え室 | ⟦ZONE⟧ | 控え室に置く |
| デッキ | ⟦ZONE⟧ | デッキの上からカード |
| エネルギーデッキ | ⟦ZONE⟧ | エネルギーデッキから |
| 成功ライブカード置き場 | ⟦ZONE⟧ | 成功ライブカード置き場にあるカード |
| ライブカード置き場 | ⟦ZONE⟧ | ライブカード置き場に置く |
| エネルギー置き場 | ⟦ZONE⟧ | エネルギー置き場にエネルギーカード |

### States Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| ウェイト状態 | ⟦STATE⟧ | ウェイト状態のメンバー |
| アクティブ状態 | ⟦STATE⟧ | アクティブ状態のメンバー |

### Actions Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| ウェイトにする | ⟦STATE⟧ | メンバーをウェイトにする |
| アクティブにする | ⟦STATE⟧ | エネルギーをアクティブにする |
| 引く | ⟦ACTION⟧ | カードを引く |
| 置く | ⟦ACTION⟧ | カードを控え室に置く |
| 加える | ⟦ACTION⟧ | 手札に加える |
| 得る | ⟦ACTION⟧ | {{icon_blade.png|ブレード}}を得る |
| 選ぶ | ⟦ACTION⟧ | カードを選ぶ |
| 公開する | ⟦ACTION⟧ | カードを公開する |
| 移動する | ⟦ACTION⟧ | エリアに移動する |
| 減らす | ⟦MODIFICATION⟧ | コストを減らす |
| 無効にする | ⟦ACTION⟧ | 能力を無効にする |

### Position Markers Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| {{center.png|センター}} | ⟦POSITION⟧ | {{center.png|センター}} |
| 【左サイド】 | ⟦SIDE⟧ | 【左サイド】 |
| 【右サイド】 | ⟦SIDE⟧ | 【右サイド】 |
| センターエリア | ⟦AREA⟧ | センターエリアにいる |
| エリア | ⟦AREA⟧ | エリアを移動した |

### Comparison Operators Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| 以上 | ⟦COMPARISON⟧ | 10枚以上, 6個以上 |
| 以下 | ⟦COMPARISON⟧ | コスト10以下, コスト9以下 |
| より多い | ⟦COMPARISON⟧ | 相手より多い |
| より低い | ⟦COMPARISON⟧ | 相手より低い |
| より大きい | ⟦COMPARISON⟧ | コストの大きい |

### Condition Markers Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| 場合 | ⟦CONDITION_MARKER⟧ | メンバーがいる場合 |
| かぎり | ⟦CONDITION_MARKER⟧ | あるかぎり |
| とき | ⟦CONDITION_MARKER⟧ | 登場したとき |

### Optional Markers Found in Literal Patterns

| Hardcoded Value | Variable | Context Examples |
|----------------|----------|------------------|
| してもよい | ⟦OPTIONAL⟧ | 置いてもよい |
| ～まで | ⟦LIMIT⟧ | ライブ終了時まで, 5枚になるまで |

## Patterns That Need Immediate Atomization

### High Priority (High Frequency)

1. **toujyou_deck_top_three_discard_heart_gain** (lines 1229-1244)
   - Three nearly identical patterns differing only in heart type
   - Should be consolidated into one pattern with ⟦RESOURCE⟧ variable

2. **jidou_three_appear_draw** (lines 1361-1364, 1379-1382)
   - Identical patterns (duplicate)
   - One should be removed

3. **live_start_aqours_heart_disable_success** (lines 1391-1394)
   - Appears twice (duplicate)
   - One should be removed

4. **jyouji_energy_ten_bladeheart_gain** (line 1277) and **jyouji_energy_ten_blade_gain_three** (line 1367)
   - Similar structure, differ in resource type and count
   - Could be consolidated

### Medium Priority (Common Elements)

5. **toujyou_score_total_energy_deck_place** (line 1253)
   - Hardcoded "6以上" should be ⟦NUMBER⟧以上
   - Hardcoded "1枚" should be ⟦NUMBER⟧枚

6. **live_start_member_count_heart_reduce** (line 1295)
   - Hardcoded "5yncri5e!" should be ⟦GROUP⟧
   - Hardcoded "1人につき" should be ⟦NUMBER⟧人につき

7. **live_start_cost_total_less_draw_top** (line 1313)
   - Hardcoded "2枚" should be ⟦NUMBER⟧枚
   - Hardcoded "1枚" should be ⟦NUMBER⟧枚

8. **jyouji_higher_cost_member_blade_gain** (line 1283)
   - Hardcoded "3 blade icons" should be variable count

## Fundamental Pattern Structure Issues

### Current Problems

1. **Too Many Literal Patterns (~1000 lines)**
   - Most patterns are hardcoded literals without regex
   - Same pattern repeated with different numbers/groups
   - No systematic way to handle variations
   - Example: `toujyou_deck_top_three_discard_heart_gain`, `toujyou_deck_top_three_discard_heart_gain_01`, `toujyou_deck_top_three_discard_heart_gain_05`

2. **Imperfect DSL Patterns**
   - Regex patterns don't capture all variations
   - Many patterns have `([^。]+)` that's too broad
   - Missing specific capture groups for common elements
   - Example: `trigger_energy_colon_action` uses generic `([^。]+)` for action

3. **Annoying Triggers**
   - Triggers (`{{toujyou.png|登場}}`, etc.) are mixed into patterns
   - Makes patterns harder to match and reuse
   - Should be separated from the core ability logic
   - Already have trigger extraction functions but not fully utilized

4. **Bad Name and Structure Fields**
   - Names are descriptive but not systematic
   - Structure field is often redundant or unclear
   - No clear hierarchy or categorization
   - Example: "Center turn1 wait select public until top" - too specific

### Proposed New Pattern Structure

#### 1. Separate Triggers from Core Patterns

**Current:**
```python
{
    "name": "toujyou_hand_discard_opponent_wait",
    "regex": "\\{\\{toujyou\\.png\\|登場\\}\\}手札を(\\d+)枚控え室に置いてもよい：...",
    "literal": "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：...",
    "template": "{{toujyou.png|登場}}手札を⟦NUMBER1⟧枚控え室に置いてもよい：...",
}
```

**Proposed:**
```python
{
    "name": "hand_discard_opponent_wait",
    "triggers": ["toujyou", "live_start"],  # Separate trigger list
    "regex": "手札を(\\d+)枚控え室に置いてもよい：相手のステージにいるコスト(\\d+)以下のメンバーを(\\d+)人までウェイトにする。（ウェイト状態のメンバーが持つ\\{\\{icon_blade\\.png\\|ブレード\\}\\}は、エールで公開する枚数を増やさない。）",
    "template": "手札を⟦NUMBER1⟧枚控え室に置いてもよい：相手のステージにいるコスト⟦COST⟧以下のメンバーを⟦NUMBER2⟧人までウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）",
    "category": "optional_cost_action",
    "structure": "discard -> wait_opponent",
}
```

#### 2. Pattern Categories

Instead of arbitrary names, use systematic categories:

- `optional_cost_action` - Cost + "してもよい：" + effect
- `per_unit_effect` - "～につき" patterns
- `condition_action` - "～場合" patterns
- `zone_transfer` - Moving cards between zones
- `resource_gain` - Gaining hearts/blades
- `state_change` - Changing member states
- `score_modification` - Modifying card scores
- `cost_modification` - Modifying costs

#### 3. Hierarchical Pattern Structure

**Level 1: Core Pattern Types**
```python
CORE_PATTERNS = {
    "optional_cost_action": {
        "regex": "([^。]+)(\\d+)枚([^。]+)してもよい：([^。]+)",
        "template": "⟦COST_TYPE⟧⟦NUMBER⟧枚⟦COST_TARGET⟧してもよい：⟦EFFECT⟧",
    },
    "per_unit_effect": {
        "regex": "([^。]+)(\\d+)([^。]+)につき、([^。]+)",
        "template": "⟦TARGET⟧⟦NUMBER⟧⟦UNIT⟧につき、⟦EFFECT⟧",
    },
    "condition_action": {
        "regex": "([^。]+)(場合|かぎり)、([^。]+)",
        "template": "⟦CONDITION⟧⟦MARKER⟧、⟦ACTION⟧",
    },
}
```

**Level 2: Specialized Patterns**
```python
SPECIALIZED_PATTERNS = {
    "discard_wait_opponent": {
        "parent": "optional_cost_action",
        "regex": "手札を(\\d+)枚控え室に置いてもよい：相手のステージにいるコスト(\\d+)以下のメンバーを(\\d+)人までウェイトにする",
        "template": "手札を⟦NUMBER1⟧枚控え室に置いてもよい：相手のステージにいるコスト⟦COST⟧以下のメンバーを⟦NUMBER2⟧人までウェイトにする",
    },
    "energy_payment_gain": {
        "parent": "optional_cost_action",
        "regex": "\\{\\{icon_energy\\.png\\|E\\}\\}(\\d+)つ支払ってもよい：([^。]+)を得る",
        "template": "{{icon_energy.png|E}}⟦NUMBER⟧つ支払ってもよい：⟦RESOURCE⟧を得る",
    },
}
```

**Level 3: Instance Patterns (with specific values)**
```python
# Generated automatically from specialized patterns + data
# No need to manually specify each variation
```

#### 4. Improved Naming Convention

**Current:** `toujyou_deck_top_three_discard_heart_gain`
**Proposed:** `discard_deck_top_gain_heart` (action + source + effect)

**Current:** `kidou_turn1_discard_group_condition_livecard_add`
**Proposed:** `discard_hand_condition_add_livecard` (cost + condition + effect)

**Pattern:** `[action]_[source]_[condition]_[effect]`

#### 5. Better Structure Field

**Current:** "Center turn1 wait select public until top"
**Proposed:** `["cost:wait+discard", "action:select_until", "effect:add_to_hand"]`

Or use structured data:
```python
"structure": {
    "cost": ["wait", "discard"],
    "action": "select_until",
    "effect": "add_to_hand",
}
```

### Refactoring Plan

#### Phase 1: Extract and Normalize Triggers
1. Move all triggers to separate field
2. Create trigger registry
3. Remove triggers from pattern regex/templates
4. Update matching logic to handle triggers separately

#### Phase 2: Categorize Patterns
1. Analyze all patterns and assign categories
2. Create hierarchical pattern structure
3. Identify core patterns that can be generalized
4. Move specialized patterns to appropriate category

#### Phase 3: Consolidate Duplicate Patterns
1. Remove literal duplicates (e.g., heart gain variants)
2. Merge patterns with same structure
3. Use regex for variations instead of separate patterns

#### Phase 4: Improve Naming and Structure
1. Rename patterns using systematic convention
2. Add proper structure fields
3. Document pattern hierarchy

#### Phase 5: Test Coverage
1. Run pattern matching after each phase
2. Ensure 100% coverage maintained
3. Add tests for new pattern structure

### Example Transformation

**Before:**
```python
{
    "name": "toujyou_deck_top_three_discard_heart_gain",
    "literal": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。",
    "template": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_XX.png|heartXX}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
    "structure": "Toujyou deck top three discard heart gain",
},
{
    "name": "toujyou_deck_top_three_discard_heart_gain_01",
    "literal": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。",
    "template": "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_XX.png|heartXX}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
    "structure": "Toujyou deck top three discard heart gain 01",
},
```

**After:**
```python
{
    "name": "discard_deck_top_condition_gain_heart",
    "triggers": ["toujyou"],
    "regex": "自分のデッキの上からカードを(\\d+)枚控え室に置く。それらがすべて\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}を持つメンバーカードの場合、ライブ終了時まで、\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}を得る。",
    "template": "自分のデッキの上からカードを⟦NUMBER⟧枚控え室に置く。それらがすべて{{heart_XX.png|heartXX}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_XX.png|heartXX}}を得る。",
    "category": "condition_action",
    "structure": {
        "action": "discard_deck_top",
        "condition": "all_have_heart",
        "effect": "gain_heart_duration",
    },
},
```

This reduces 3 patterns to 1, removes hardcoded heart types, and provides better structure.

## Next Steps

1. **Phase 1: Extract and normalize triggers** - Separate triggers from patterns
2. **Phase 2: Categorize patterns** - Create hierarchical pattern structure
3. **Phase 3: Consolidate duplicate patterns** - Merge similar patterns
4. **Phase 4: Improve naming and structure** - Systematic naming
5. **Phase 5: Test coverage** - Ensure 100% coverage maintained

## Pattern Analysis for Regex Improvement

### Current Pattern Count
- **DSL_PATTERNS**: ~100 patterns (lines 72-1069) - all have regex
- **LITERAL_PATTERNS**: ~150 patterns (lines 1071-1869) - mixed (some have regex, some don't)
- **FAMILY_PATTERNS**: 8 patterns (lines 1871-1936) - different structure (prefix/contains/suffix)

### Issues Identified

#### 1. LITERAL_PATTERNS Without Regex
Many LITERAL_PATTERNS have only `literal` and `template` fields, no `regex`. These need regex added:
- turn1_cost4_member_discard_activate_ability (line 1073)
- turn1_discard_draw_live_card_add (line 1079)
- live_start_multi_member_blade_gain (line 1085)
- live_start_distinct_group_heart_gain (line 1091)
- live_start_energy_payment_per_energy_gain (line 1097)
- live_start_two_energy_blade_gain_literal (line 1103)
- live_start_two_energy_heart_gain_literal (line 1109)
- live_start_hand_names_optional_discard_per_card_gain (line 1115)
- live_start_same_card_name_heart_gain (line 1121)
- live_start_other_group_member_blade_gain (line 1127)
- live_start_energy_payment_single_blade_gain (line 1133)
- live_start_energy_payment_single_heart_gain (line 1139)
- live_start_energy_payment_multi_blade_gain (line 1145)
- live_start_no_blade_heart_condition_gain (line 1151)
- live_start_moved_member_blade_gain (line 1157)
- live_start_hand_two_card_blade_gain (line 1163)
- live_start_draw_then_place_top (line 1169)
- bullet_wait_state_member_active_blade_gain (line 1175)
- answer_otherwise_member_blade_gain (line 1181)
- jidou_zone_appearance_double_blade_gain (line 1187)
- jidou_energy_zone_bladeheart_gain (line 1193)
- live_start_energy_under_member_heart_gain (line 1199)
- toujyou_end_of_turn_blade_gain (line 1205)
- live_start_energy_to_energy_deck_red_heart_gain (line 1211)
- toujyou_center_blade_gain (line 1217)
- toujyou_right_side_energy_activate (line 1223)
- toujyou_deck_top_three_discard_heart_gain (line 1229)
- toujyou_deck_top_three_discard_heart_gain_01 (line 1235)
- toujyou_deck_top_three_discard_heart_gain_05 (line 1241)
- turn1_energy_move_area (line 1247)
- toujyou_score_total_energy_deck_place (line 1253)
- jidou_main_phase_energy_payment_hand_add (line 1259)
- center_turn1_wait_select_public_until_top (line 1265)
- And many more...

#### 2. Generic Capture Groups in DSL_PATTERNS
Many DSL_PATTERNS use `([^。]+)` which is too broad. Should be more specific:
- Numbers: `(\d+)` for specific numeric values
- Groups: `『([^』]+)』` for group names in brackets
- Card types: specific patterns like `(メンバーカード|ライブカード|エネルギーカード)`
- Heart icons: `\\{\\{heart_[0-9]{2}\\.png\\|heart[0-9]{2}\\}\\}` for heart icons
- Energy icons: `\\{\\{icon_energy\\.png\\|E\\}\\}` for energy
- Blade icons: `\\{\\{icon_blade\\.png\\|ブレード\\}\\}` for blades

#### 3. Hardcoded Values in Templates
Templates have hardcoded values that should be variables:
- Numbers: "1枚", "2枚", "3枚" → ⟦NUMBER⟧枚
- Groups: "虹ヶ咲", "μ's", "Aqours" → ⟦GROUP⟧
- Costs: "コスト4", "コスト10" → コスト⟦COST⟧
- Heart types: "heart04", "heart01" → {{heart_XX.png|heartXX}}

### Improvement Strategy

#### Batch 1: Add Regex to High-Priority LITERAL_PATTERNS
Start with patterns that have clear structure and can benefit from regex:
- Duplicate patterns (heart gain variants)
- Patterns with numbers that should be variables
- Patterns with groups that should be variables

#### Batch 2: Improve DSL_PATTERNS with Generic Capture Groups
Replace `([^。]+)` with more specific patterns where appropriate:
- Numbers → `(\d+)`
- Known card types → specific alternation
- Known groups → specific alternation or `『([^』]+)』`

#### Batch 3: Consolidate Duplicate Patterns
Merge patterns that are nearly identical:
- toujyou_deck_top_three_discard_heart_gain variants
- Similar energy payment patterns

#### Batch 4: Test Coverage After Each Batch
Run coverage check after each batch to ensure 100% is maintained.

## Next Steps

1. **Phase 1: Extract and normalize triggers** - Separate triggers from patterns
2. **Phase 2: Categorize patterns** - Create hierarchical pattern structure
3. **Phase 3: Consolidate duplicate patterns** - Merge similar patterns
4. **Phase 4: Improve naming and structure** - Systematic naming
5. **Phase 5: Test coverage** - Ensure 100% coverage maintained

## Current Task: Add Regex to LITERAL_PATTERNS

Starting with high-priority patterns that need regex.
