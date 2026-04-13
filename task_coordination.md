# Task Coordination - DSL Granularization

**Purpose:** Coordinate parallel work across multiple agents to avoid overlap and track progress.

**Instructions:**
- When STARTING a task: Edit this file to mark the task as "IN_PROGRESS" and add your agent ID
- When FINISHING a task: Edit this file to mark the task as "COMPLETED" and add completion notes
- Check this file before starting any work to avoid conflicts

---

## Current State
- Total patterns: 70
- Total clauses: 1973
- Last updated: 2026-04-14

---

## Agent 1: Pattern Analysis
**Status:** IN_PROGRESS
**Agent ID:** Cascade

**Tasks:**
1. Analyze heart_specification (133 matches) - COMPLETED
   - Extract variables from pattern_variables
   - Categorize by heart type, context
   - Output: data/heart_specification_analysis.json
   - **Result:** Too fragmented to granularize (most heart types have 1-4 matches)

2. Analyze look_top (126 matches) - COMPLETED
   - Extract variables (source, count, destination)
   - Categorize by destination (hand vs discard)
   - Categorize by card type filters
   - Output: data/look_top_analysis.json
   - **Result:** Already specific (only varies by count number, regex only captures 1 variable)

3. Analyze basic_action_draw (124 matches) - COMPLETED
   - Extract variables (count, conditions)
   - Categorize by draw count
   - Categorize by conditions
   - Output: data/basic_action_draw_analysis.json
   - **Result:** Already specific (all 124 matches are draw 1 card)

4. Analyze add_from_discard (149 matches) - COMPLETED
   - Extract variables (card type, destination)
   - Categorize by card type
   - Categorize by destination
   - **Result:** Variables lumped (e.g., "コスト4以下の『μ's』のメンバー") - needs atomic patterns

**NEW APPROACH: Atomic Patterns Layer - COMPLETED**
- Current patterns lump semantic components into single variables
- Need atomic patterns for: cost conditions, groups, card types, zones
- Compose atomic patterns → clause patterns → ability patterns
- Automated by combining patterns in right order

**ATOMIC PATTERNS ADDED:**
- atomic_cost_below: 82 matches
- atomic_cost_above: 41 matches
- atomic_group_mus: 53 matches
- atomic_group_aqours: 46 matches
- atomic_group_nijigasaki: 85 matches
- atomic_group_renon: 40 matches
- atomic_group_liella: 61 matches
- atomic_card_type_live: 246 matches
- atomic_card_type_member: 89 matches
- atomic_zone_discard: 10 matches
- atomic_zone_deck_top: 147 matches

**Result:** Total clause patterns reduced from 70 to 64 (atomic patterns breaking down lumpy variables)

**ADDITIONAL ATOMIC PATTERNS ADDED:**
- atomic_zone_hand: 228 matches
- atomic_zone_stage: 186 matches
- atomic_zone_energy_zone: 21 matches
- atomic_card_type_energy: 30 matches
- atomic_icon_reference: 351 matches (catches all {{x.png}} patterns including heart colors)
- atomic_area_left: 3 matches
- atomic_area_center: 15 matches
- atomic_area_right: 1 matches

**Note:** Group patterns (A-RISE, Saint Snow, Sunny Passion) not matching - may not appear in data or written differently. Heart colors captured by icon_reference pattern.

---

## Agent 2: Implementation
**Status:** PENDING
**Agent ID:** 

**Tasks:**
1. Wait for Agent 1 analysis files
2. Implement granular patterns based on analysis
3. Edit tools/extract_abilities_to_template.py
4. Add specific patterns before generic fallbacks
5. Run python tools/extract_abilities_to_template.py
6. Verify output in data/abilities_extracted.json

---

## Agent 3: Verification
**Status:** PENDING
**Agent ID:** 

**Tasks:**
1. After each pattern change, run verification
2. Create check scripts to verify match diversion
3. Validate total clauses remain 1973 (no data loss)
4. Test ability_dsl_comprehensive.json still matches 500/506
5. Output verification reports

---

## Agent 4: Documentation & Cleanup
**Status:** PENDING
**Agent ID:** 

**Tasks:**
1. Update pattern documentation
2. Clean up temp analysis scripts after use
3. Ensure file path comments in scripts
4. Update TODO list
5. Commit changes (if authorized)

---

## Completed Tasks
- [x] Delete icon_embedded_action pattern
- [x] Delete icon_embedded_trigger pattern
- [x] Delete icon_embedded_live_start pattern
- [x] Granularize state_change_wait
- [x] Granularize reveal_and_add_optional
- [x] Create ability_dsl_comprehensive.json
- [x] Improve matching logic (500/506 matched)
