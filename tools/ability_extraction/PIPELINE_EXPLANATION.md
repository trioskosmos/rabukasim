# Ability Extraction Pipeline Documentation

## Overview
The ability extraction pipeline converts raw card ability text from `data/cards.json` into structured semantic representations, then converts those into frame opcodes for the Rust game engine.

## Files in tools/ability_extraction/

### Core Parser Files

1. **extract_card_abilities.py** (10,447 bytes)
   - **Purpose:** Main entry point for extracting abilities from cards.json
   - **Input:** `data/cards.json`
   - **Output:** `data/abilities_extracted_from_cards.json`
   - **Key Functions:**
     - `extract_trigger(text)`: Extracts trigger icons (e.g., {{kidou.png|起動}}, {{toujyou.png|登場}})
     - `extract_abilities_from_card(card_id, card)`: Splits ability text by newline, handles continuation lines
     - `extract_all_abilities(cards_file)`: Groups abilities by full_text, calls semantic parsers
   - **Process:**
     1. Reads cards.json
     2. Splits each card's ability text by newline
     3. Extracts triggers (kidou, toujyou, jidou, etc.)
     4. Removes trigger icons to get triggerless_text
     5. Calls parse_cost() for cost parsing
     6. Calls parse_effect() for semantic effect parsing
     7. Groups identical abilities across cards
     8. Outputs unique abilities with card examples

2. **effect_parser.py** (193,600 bytes)
   - **Purpose:** Parses effect text into semantic action structures
   - **Input:** Triggerless effect text (e.g., "自分の控え室から、コストの合計が4以下になるようにメンバーカードを2枚までステージに登場させる")
   - **Output:** Semantic effect dict (e.g., `{"action": "deploy_to_stage", "count": 2, "source": "waitroom", ...}`)
   - **Key Functions:**
     - `parse_effect_backwards(text)`: Main entry, parses text backwards to extract variables
     - `_strip_waitroom_source(text, result)`: Extracts "控え室から" → source: "waitroom", handles cost sum limits
     - `_normalize_parsed_tree(value)`: Fills in default values for actions
   - **Patterns Handled:**
     - Draw cards, add to hand, discard, place card
     - Energy activation, pay energy
     - Deploy to stage, move member
     - Look at cards, reveal
     - Cost reduction, heart cost modification
     - Selection, filtering
     - Conditions (card count, energy, score, etc.)

3. **condition_parser.py** (56,675 bytes)
   - **Purpose:** Parses condition clauses in ability text
   - **Input:** Condition text (e.g., "自分の手札が5枚以上の場合")
   - **Output:** Condition dict (e.g., `{"type": "card_count", "zone": "hand", "value": 5, "operator": ">="}`)
   - **Key Functions:**
     - `parse_condition(text)`: Main entry for condition parsing
     - `_extract_target(text)`: Extracts target (self/opponent)
   - **Patterns Handled:**
     - Card count conditions
     - Energy conditions
     - Score conditions
     - Heart count conditions
     - Blade count conditions
     - Different card/group names
     - Member presence/absence

4. **extract_costs.py** (66,680 bytes)
   - **Purpose:** Parses cost text into structured cost representation
   - **Input:** Cost text (e.g., "{{icon_energy.png|E}}{{icon_energy.png|E}}{{heart_00.png|heart0}}")
   - **Output:** Cost dict (e.g., `{"energy": 2, "hearts": {"00": 1}}`)
   - **Key Functions:**
     - `parse_cost(text)`: Main entry for cost parsing
   - **Patterns Handled:**
     - Energy costs
     - Heart costs (by color)
     - Blade costs
     - Tap costs
     - Discard costs

### Utility Files

5. **parser_utils.py** (5,986 bytes)
   - **Purpose:** Shared utility functions for parsers
   - **Functions:** Helper regex patterns, text normalization

6. **test_parsers.py** (12,739 bytes)
   - **Purpose:** Unit tests for individual parsers
   - **Usage:** Run to verify parser correctness on specific ability texts

7. **analyze_notes.py** (4,391 bytes)
   - **Purpose:** Analyze parsing failures and generate notes
   - **Usage:** Debug tool for understanding parser issues

8. **extract_from_frame_source.py** (2,864 bytes)
   - **Purpose:** Extract abilities from existing frame source (reverse engineering)
   - **Usage:** For analyzing authored frames

## Full Pipeline Flow

### Step 1: Extract Abilities (extract_card_abilities.py)
```
data/cards.json
    ↓
Split ability text by newline
    ↓
Extract triggers (kidou, toujyou, jidou, etc.)
    ↓
Remove trigger icons → triggerless_text
    ↓
Split cost from effect (if "：" present)
    ↓
Parse cost (extract_costs.py)
    ↓
Parse effect (effect_parser.py)
    ↓
Group identical abilities by full_text
    ↓
Output: data/abilities_extracted_from_cards.json
```

### Step 2: Convert to Frames (semantic_to_frame_converter.py)
```
data/abilities_extracted_from_cards.json
    ↓
For each unique ability:
    ↓
Convert trigger to trigger_id (ON_PLAY=1, ACTIVATED=6, etc.)
    ↓
Convert cost to cost frames (PAY_ENERGY, TAP_SELF, etc.)
    ↓
Convert effect actions to frames:
    - deploy_to_stage → PLAY_MEMBER_FROM_HAND/DISCARD
    - draw_cards → DRAW
    - add_to_hand → RECOVER_LIVE/ADD_TO_HAND
    - etc.
    ↓
Convert conditions to condition frames:
    - card_count → COUNT_CARDS
    - energy → CALC_SUM_COST
    - etc.
    ↓
Output: data/ability_frame_source.json
```

### Step 3: Compile Cards (build_cards.py)
```
data/ability_frame_source.json
    ↓
Merge with card data from cards.json
    ↓
Convert string opcodes to numeric codes (e.g., "DRAW" → 13)
    ↓
Convert trigger names to numeric IDs
    ↓
Output: data/cards_compiled.json (for Rust engine)
```

## Test Loop

### Running Tests
```bash
cd engine_rust_src
cargo test
```

### Test Output Analysis
**IMPORTANT DEBUGGING RULES:**
- **ALWAYS run every Rust test, never a subset** - use `cargo test --lib` not `cargo test --lib repro::card_XXX`
- **ALWAYS write full debug output to a text file** - use `cargo test --lib > test_output.txt 2>&1`
- **ALWAYS use Python scripts for analysis, not Select-String/grep** - write Python scripts to parse test output

1. Run `cargo test --lib > test_output.txt 2>&1` to execute ALL Rust unit tests and capture full output
2. Use Python script to parse test_output.txt and identify failing tests
3. Group failures by pattern (cost reduction, live start, multi-pick, etc.)
4. Identify specific card IDs causing failures
5. Find those cards in ability_frame_source.json
6. Compare generated frames vs authored frames
7. Fix parser or converter to match structure (not content)
8. Re-run pipeline: `python tools/build_cards.py`
9. Re-run tests with full output: `cargo test --lib > test_output.txt 2>&1`
10. Use Python script to compare before/after failure counts
11. Repeat until 0 failures

### Current Test Status
- **Before fixes:** 536 passed; 157 failed
- **After cost reduction fix:** 545 passed; 148 failed (+9 tests)
- **After semantic extraction fixes:** 572 passed; 121 failed (+27 tests total from initial state)
- **Goal:** 0 failures

### Recent Fixes Applied
1. Cost parsing bug (extract_costs.py) - Fixed parse_cost to handle pre-split text
2. Frame converter bug (semantic_to_frame_converter.py) - Fixed this_member stage->waitroom costs to generate RETURN instead of MOVE_TO_DISCARD
3. Duplicate RETURN bug (semantic_to_frame_converter.py) - Fixed converter to not add trailing RETURN if cost already has RETURN
4. SET_TAPPED for wait destination (semantic_to_frame_converter.py) - Added handling for this_member stage->wait to use SET_TAPPED opcode
5. "その中から" pattern (effect_parser.py) - Added handling for "look at cards, then select from them" pattern
6. Comma-separated action parsing (effect_parser.py) - Fixed parsing of actions like "draw 2, discard 1"
7. Multi-sentence effects (effect_parser.py) - Added handling for choose_heart pattern followed by additional sentences
8. Fixed undefined result references (semantic_to_frame_converter.py) - Removed references to undefined variables
9. Reverted note detection fix (effect_parser.py) - Fixed regression where actions with trailing notes were incorrectly parsed
10. "これにより無効にした場合" fix (condition_parser.py) - Added specific check to prevent incorrect comparison parsing
11. "発動させる" pattern fix (condition_parser.py) - Added specific check to prevent incorrect comparison parsing
12. "その後、" separator fix (effect_parser.py) - Added handling for "then" separator in multi-action effects
13. "自分と相手はそれぞれ" pattern fix (effect_parser.py) - Fixed to set target to 'both_players'
14. "その後、" pattern fix (effect_parser.py) - Fixed to always treat as multi-action sequence (not conditional)

## Key Patterns to Fix

### Current Failing Test Patterns (121 failures)

#### test_suite failures (86)
- **ability_frame_audit_tests:**
  - test_ability_55_kurosawa_ruby_missing_saintsnow_filter - Missing group filter
  - test_ability_64_* - Multiple option parsing issues (flavor choice, blade, position change)
  - test_card_574_self_discards_without_stage_selection - Self-discard targeting issues
- **ability_tests:**
  - test_ability_64_* - Option parsing for ability 64 (Kurosawa Ruby)
  - test_card_574_self_discards_without_stage_selection - Stage selection missing

#### repro failures (33)
- **card_10_cost_bug (6 failures):**
  - Cost reduction hand size variations
  - Cost reduction opcode per card filter
  - Baton touch cost handling
  - Playability cost verification
- **card_579_verification (2 failures):**
  - Ability 0 cost comparison
  - Ability 1 heart filter
- **card_420 (2 failures):**
  - Cost sum limit
  - Multi-pick from discard
- **card_4558 (4 failures):**
  - Multiple ability issues (on_live_start pay_energy, live_success recover_live)
- **Other repro failures:**
  - card_459 live_start member selection
  - card_874 self-discard
  - Various softlock and interaction resumption issues

#### core failures (2)
- logic tests - general engine logic issues

### 1. Cost Reduction (FIXED)
- **Issue:** Hand-based cost reduction not extracting zone mask and not_self filter
- **Fix:** Added to semantic_to_frame_converter.py lines 576-580
- **Result:** 9 more tests passing

### 2. Card 420 - Cost Sum Limit (IN PROGRESS)
- **Issue:** "コストの合計が4以下になるように" not extracting value_threshold, is_le, is_cost_type
- **Fix attempts:**
  - Added cost sum extraction to _strip_waitroom_source (effect_parser.py)
  - Added deploy_to_stage source check (effect_parser.py)
- **Status:** Semantic extraction still showing source: "stage" instead of "waitroom"
- **Next:** Need to fix semantic extraction or frame converter

## Common Issues

### Import Errors
- **Problem:** condition_parser.py missing or corrupted
- **Fix:** `git checkout HEAD -- tools/ability_extraction/`

### Branch Mismatches
- **Problem:** ability-rewrite branch has different API
- **Fix:** Stay on HEAD branch, don't mix branches

### Encoding Issues
- **Problem:** UTF-8 vs UTF-8-sig vs UTF-16
- **Fix:** Use encoding='utf-8' consistently

## File Sizes (for reference)
- effect_parser.py: 193,600 bytes (largest, most complex)
- condition_parser.py: 56,675 bytes
- extract_costs.py: 66,680 bytes
- extract_card_abilities.py: 10,447 bytes
