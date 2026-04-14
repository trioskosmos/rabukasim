# Variable Decomposition Coverage Improvement - Work Documentation

## Objective
Achieve 100% coverage in variable decomposition of Japanese ability texts by refining and adding regex patterns in a DSL. The goal is to iteratively examine low coverage abilities and create new, more specific patterns until full coverage is reached.

## Current Status
- Average coverage: 94.1%
- Abilities with < 50% coverage: 0
- Abilities with < 60% coverage: 4 (0.6%)
- Abilities with < 70% coverage: 23 (3.7%)
- Abilities with < 80% coverage: 51 (8.1%)
- Abilities with < 90% coverage: 81 (12.9%)

## Key Files
- `tools/extract_abilities_to_template.py` - Main DSL pattern definitions file
- `data/abilities_extracted_simple.json` - Dataset with ability texts and coverage info
- `low_abilities.txt` - Output file containing abilities with low coverage

## Scripts Created for Debugging

### 1. `check_cov.py`
Checks overall coverage statistics from the JSON dataset.
```bash
python check_cov.py
```
Output: Average coverage and count of abilities below various thresholds.

### 2. `write_abilities.py`
Writes abilities with < 50% coverage to `low_abilities.txt`.
```bash
python write_abilities.py
```

### 3. `debug_pattern_order.py`
Analyzes which patterns match a given low-coverage ability and which patterns actually matched in the data. Helps identify pattern priority issues.
```bash
python debug_pattern_order.py
```

### 4. `find_pattern_positions.py`
Prints the index positions of specified patterns in `DSL_PATTERNS` list to help with reordering.
```bash
python find_pattern_positions.py
```

### 5. `show_coverage_stats.py`
Shows detailed coverage distribution statistics.
```bash
python show_coverage_stats.py
```

### 6. `show_lowest_coverage.py`
Shows the top abilities with lowest coverage with their pattern matches.
```bash
python show_lowest_coverage.py
```

### 7. `get_lowest_abilities.py`
Shows the top 10 abilities with lowest coverage with detailed pattern matching information (with UTF-8 encoding fix for Windows).
```bash
python get_lowest_abilities.py
```

### 8. `show_below_70.py`
Shows all abilities with < 70% coverage.
```bash
python show_below_70.py
```

## Patterns Added

### 1. `trigger_hand_names_optional_discard_per_card`
Matches trigger with hand names and optional discard per card.
```python
{
    "name": "trigger_hand_names_optional_discard_per_card",
    "regex": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)手札の「([^」]+)」と「([^」]+)」と「([^」]+)」を、([^。]+)控え室に置いてもよい：([^。]+)",
    "template": "⟦TRIGGER⟧手札の「⟦NAME1⟧」と「⟦NAME2⟧」と「⟦NAME3⟧」を、⟦CONDITION⟧控え室に置いてもよい：⟦ACTION⟧。",
    "structure": "Trigger hand names optional discard per card",
},
```

### 2. `trigger_energy_optional_per_resource_score`
Matches trigger with optional energy payment per resource score.
```python
{
    "name": "trigger_energy_optional_per_resource_score",
    "regex": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)(\{?\{[^}]+\.png\|[^}]+\}\}?)+を好きな数支払ってもよい：([^。]+)支払った([^。]+)(\d+)つにつき、([^。]+)",
    "template": "⟦TRIGGER⟧⟦ENERGY⟧を好きな数支払ってもよい：⟦PREFIX⟧支払った⟦RESOURCE⟧⟦NUMBER⟧つにつき、⟦ACTION⟧。",
    "structure": "Trigger energy optional per resource score",
},
```

### 3. `trigger_position_change_area`
Matches trigger with position change area action.
```python
{
    "name": "trigger_position_change_area",
    "regex": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)(\{?\{[^}]+\.png\|[^}]+\}\}?)*：([^。]+)を『([^』]+)』か『([^』]+)』の([^。]+)が([^。]+)エリアに([^。]+)。",
    "template": "⟦TRIGGER⟧⟦ENERGY⟧：⟦TARGET⟧を『⟦GROUP1⟧』か『⟦GROUP2⟧』の⟦MEMBER⟧が⟦CONDITION⟧エリアに⟦ACTION⟧。",
    "structure": "Trigger position change area",
},
```

### 4. `auto_trigger_cost_group_baton_touch`
Matches auto trigger with cost group baton touch.
```python
{
    "name": "auto_trigger_cost_group_baton_touch",
    "regex": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)このメンバーがコスト(\d+)以上の『([^』]+)』のメンバーとバトンタッチして控え室に置かれた",
    "template": "⟦TRIGGER⟧このメンバーがコスト⟦COST⟧以上の『⟦GROUP⟧』のメンバーとバトンタッチして控え室に置かれた",
    "structure": "Auto trigger cost group baton touch",
},
```

### 5. `live_card_count_action_two_part`
Matches live card count action with two-part structure.
```python
{
    "name": "live_card_count_action_two_part",
    "regex": r"(?:\{?\{[^}]+\}\}?)?([^。]+)の([^。]+)の([^。]+)が(\d+)枚以上(?:の場合|あるか|かぎり)、([^。]+)",
    "template": "⟦SOURCE⟧の⟦CONTEXT⟧の⟦CARD⟧⟦NUMBER⟧枚以上の場合、⟦ACTION⟧。",
    "structure": "Live card count action two part",
},
```

### 6. `icon_action_after_condition`
Matches icon action after condition (e.g., `{{icon_blade.png|ブレード}}を得る。`).
```python
{
    "name": "icon_action_after_condition",
    "regex": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)+を得る。",
    "template": "⟦ICON⟧を得る。",
    "structure": "Icon action after condition",
},
```

### 7. `trigger_center_turn_member_wait`
Matches trigger with center, turn, and member wait action.
```python
{
    "name": "trigger_center_turn_member_wait",
    "regex": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)(\{?\{[^}]+\.png\|[^}]+\}\}?)(\{?\{[^}]+\.png\|[^}]+\}\}?)メンバー(\d+)人を([^。]+)する：([^。]+)",
    "template": "⟦TRIGGER⟧⟦AREA⟧⟦TURN⟧メンバー⟦NUMBER⟧人を⟦ACTION⟧する：⟦EFFECT⟧",
    "structure": "Trigger center turn member wait",
},
```

### 8. `trigger_side_energy_activation`
Matches trigger with side-specific energy activation (simplified version).
```python
{
    "name": "trigger_side_energy_activation",
    "regex": r"(\{?\{[^}]+\.png\|[^}]+\}\}?)【([^】]+)】([^。]+)。",
    "template": "⟦TRIGGER⟧【⟦SIDE⟧】⟦ACTION⟧。",
    "structure": "Trigger side energy activation",
},
```

### 9. `zone_card_score_total_energy_deck_action`
Matches zone card score total energy deck action (simplified version).
```python
{
    "name": "zone_card_score_total_energy_deck_action",
    "regex": r"自分の([^。]+)から、([^。]+)を(\d+)枚([^。]+)で([^。]+)。",
    "template": "自分の⟦ZONE⟧から、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦STATE⟧で⟦ACTION⟧。",
    "structure": "Zone card score total energy deck action",
},
```

### 10. `live_start_game_turn_score_duration_member_gain`
Matches live start with game turn condition, score modification, and duration member gain (simplified version).
```python
{
    "name": "live_start_game_turn_score_duration_member_gain",
    "regex": r"この([^。]+)の([^。]+)の場合、この([^。]+)の([^。]+)を([^。]+)し、([^。]+)まで、([^。]+)。",
    "template": "この⟦GAME⟧の⟦PHASE⟧の場合、この⟦CARD⟧の⟦ATTRIBUTE⟧を⟦MODIFIER⟧し、⟦DURATION⟧まで、⟦ACTION⟧。",
    "structure": "Live start game turn score duration member gain",
},
```

## Key Insights

### Why the Last 6% is Difficult
1. **Complex Nested Structures**: Abilities with multiple nested conditions and actions require very specific patterns
2. **Pattern Priority**: Generic patterns often match before specific ones, requiring careful ordering
3. **Icon Prefixes**: Text starting with icon patterns requires optional matching
4. **Multiple Delimiters**: Abilities use various delimiters (colon, comma, period) in complex combinations
5. **Per-Resource Conditions**: Conditions that apply per resource or per card add complexity

### Pattern Strategy That Works
1. **Make patterns more general, not more specific** - Focus on matching smaller parts of the text rather than entire complex structures
2. **Order matters** - More specific patterns should come before generic ones in the DSL_PATTERNS list
3. **Handle icon prefixes** - Use optional matching for icon patterns at the start of text
4. **Add NEW patterns instead of modifying existing ones** - This avoids breaking existing coverage
5. **Test patterns in isolation** - Use debugging scripts to verify patterns match before relying on them

## Pattern Reordering Done
- Moved `trigger_hand_names_optional_discard_per_card` and `trigger_energy_optional_per_resource_score` before `comma_separated_action` to give them higher priority
- Moved `live_card_count_action_two_part` before `live_card_count_condition_resource_gain`

## Remaining Work
- 4 abilities have < 60% coverage (need to add patterns for these)
- 23 abilities have < 70% coverage (need to add patterns for these)
- Continue adding more general patterns for the remaining low coverage cases
- Focus on simpler, more flexible patterns that match smaller parts of the text

## How to Continue
1. Run `get_lowest_abilities.py` to see the current lowest coverage abilities
2. Identify the uncovered parts of each ability
3. Add simple, general patterns to match those uncovered parts
4. Test by running `tools/extract_abilities_to_template.py`
5. Check coverage with `check_cov.py`
6. Repeat until 100% coverage is reached
