# <u>**THE TESTS ARE NOT WRONG. THE ENGINE IS MOSTLY RIGHT. ACTUALLY READ WHAT THE TESTS ARE LOOKING FOR. ACTUALLY READ WHAT CARDS AND ABILITIES ARE RELEVANT. ACTUALLY READ THE FRAMES AND THE ABILITY TEXT, COMPARE AND REASON. ACTUALLY EXAMINE IF EVERY PART IS ACCEPTED IN THE ENGINE. DO NOT OVERMASSAGE. ADD USEFUL TERMS AS ALTERNATIVES TO CURRENT ONES.**</u>

## Build Pipeline

### Data Flow

1. **Raw Cards** → `data/cards.json`
   - Source of truth for all card data
   - Contains card names, abilities, costs, etc.

2. **Semantic Extraction** → `data/abilities_extracted_from_cards.json`
   - Tool: `tools/ability_extraction/` (Python)
   - Extracts abilities from raw cards into semantic format
   - Parses ability text into structured data (triggers, conditions, actions)
   - **THIS IS WHERE MANY BUGS ORIGINATE**
   - **IMPORTANT: Try to avoid spamming the translator. Use it for converting to frames, but the bulk of the work should be in parsing.**

3. **Semantic to Frame Conversion** → `data/ability_frame_source.json`
   - Tool: `tools/semantic_to_frame_converter.py` (Python)
   - Converts semantic abilities to frame format
   - Maps semantic actions to frame opcodes
   - Generates slot/attr/params for each frame
   - **THIS IS WHERE I'VE BEEN MAKING CHANGES**

4. **Card Compilation** → `data/cards_compiled.json`
   - Tool: `engine/compiler/main.py` (Python)
   - Compiles raw cards with frame programs
   - Merges frame data into card database
   - Generates final card database for Rust engine

5. **Rust Engine** → `engine_rust_src/`
   - Loads `data/cards_compiled.json`
   - Executes frame programs via interpreter
   - Tests verify correct behavior

### File Paths

```
C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\
├── data/
│   ├── cards.json                              # Raw card data
│   ├── abilities_extracted_from_cards.json     # Semantic extraction output
│   ├── ability_frame_source.json              # Frame generation output
│   ├── ability_frame_source_authored.json      # Authored frames (reference)
│   ├── cards_compiled.json                    # Compiled card database
│   └── card_id_mapping.json                   # Card ID mappings
├── tools/
│   ├── semantic_to_frame_converter.py         # Semantic → Frame conversion
│   └── ability_extraction/                    # Semantic extraction tool
├── engine/
│   └── compiler/
│       └── main.py                             # Card compilation
└── engine_rust_src/
    └── src/
        ├── core/logic/interpreter/            # Rust frame interpreter
        └── qa/batch_card_specific.rs          # Rust tests
```

## Approach to Fixing Frames

### Step 1: Identify Failing Test
- Run with `--nocapture` to see detailed output
- Run `cargo test --lib` to get list of failures MAKE SURE YOU WRITE ALL TO A FILE AND READ THE FILE DO SEE THE DEBUG AND KNOW WHAT TO FIX
- Pick a specific failing test and work from there


### Step 2: Read the Test
- Find test in `engine_rust_src/src/qa/batch_card_specific.rs`
- Understand what the test is checking
- Identify which card/ability is being tested
- Note the expected vs actual behavior

### Step 3: Read the Card and Ability
- Find card in `data/cards_compiled.json`
- Get card_no and ability_index from test
- Read the ability text from raw cards or semantic data
- **ACTUALLY READ THE ABILITY TEXT - EVERY STAGE**

### Step 4: Read the Generated Frames
- Look at the frames for the card/ability in `data/cards_compiled.json`
- Compare to authored frames in `data/ability_frame_source_authored.json` if available
- Check if frames match the ability text stages

### Step 5: Compare and Reason
- For each stage in ability text, check if frame exists
- Check if opcode is correct for the action
- Check if slot/attr/params are correct for the action
- **CONSIDER WHO GETS TO DO THE EFFECT (target_player)**
- **CONSIDER SOURCE/DESTINATION VARIABLES**

### Step 6: Check Engine Acceptance
- Read Rust interpreter code in `engine_rust_src/src/core/logic/interpreter/`
- Check what variable names the engine actually reads
- Verify frame uses correct keys (case-insensitive for params)
- Verify zone names match engine's Zone enum
- Verify value formats match engine expectations

### Step 7: Fix Frame Generation
- Update `tools/semantic_to_frame_converter.py`
- Fix specific issue (not overmassaging)
- Regenerate frames: `python tools/semantic_to_frame_converter.py`
- Rebuild cards: `python -c "from engine.compiler import main; main.compile_cards('data/cards.json', 'data/cards_compiled.json', quiet=False, export_profile='runtime')"`
- Test: `cargo test <specific_test> -- --nocapture`

## Engine Variable Names (What It Actually Reads)

### Param Keys (case-insensitive)
- `FILTER`, `gt`, `lt`, `min`, `max`, `eq`, `raw_cond`, `RAW_COND`
- `MIN`, `MAX`, `EQ`, `GE`, `LE`, `count`, `COUNT`, `threshold`, `THRESHOLD`, `value`, `VALUE`
- `heart_count`, `HEART_COUNT`, `min_count`, `MIN_COUNT`, `player`, `PLAYER`, `keyword`, `KEYWORD`
- `multiplier`, `heart_type`, `raw_effect`, `base_value`, `divisor`, `offset`, `type`, `rule`, `from`, `choose_count`

### Slot Keys
- `target_slot`: "CONTEXT", "STAGE_0", "STAGE_1", "STAGE_2", "HAND"
- `source_zone`: "HAND", "DECK_TOP", "DECK", "STAGE", "DISCARD", "ENERGY"
- `dest_zone`: "DISCARD", "DECK", "HAND", "STAGE", "ENERGY"
- `comparison`: "GE", "LE", "EQ", "GT", "LT"
- `remainder_zone`: "DISCARD", "HAND", "DECK"

### Attr Keys (encoded in filter_attr)
- `target_player`: "SELF", "OPPONENT", "BOTH" (encoded as bits 0-1)
- `zone_mask`: "Guest+Friend", "ALL", "ANY_STAGE"
- `card_type`: "LIVE", "MEMBER", "ENERGY_CARD"
- `group_enabled`, `group_id`: for group filtering
- `color_mask`: for heart color filtering
- `heart_type`: "HEART01", "HEART02", "HEART03", "HEART04", "HEART05", "HEART06", "SELECTED", "ANY"
- `is_optional`: for optional operations
- `compare_accumulated`: for accumulated comparisons
- `once_per_turn`: for once-per-turn restrictions
- `not_self`: for excluding self from counts

### Zone Names (must match engine's Zone enum)
- `DECK`, `DECK_TOP`, `DECK_BOTTOM`
- `HAND`, `STAGE`, `DISCARD`
- `SUCCESS_PILE`, `ENERGY`, `YELL`

## Common Issues

### Semantic Extraction Bugs
- Missing actions in semantic data
- Wrong trigger in semantic data
- Missing conditions in semantic data
- **FIX: Fix semantic extraction tool (NOT frame converter)**

### Frame Generation Bugs
- Wrong opcode for action
- Missing slot/attr/params
- Wrong zone names
- Wrong variable names
- **FIX: Fix semantic_to_frame_converter.py**

### Engine Interpreter Bugs
- A LAST CASE SCENARIO. IT IS MORE LIKELY THE FAULT OF A PYTHON CONVERTER. YOU BETTER HAVE GOOD REASON FOR THIS.


## Current Status

(UPDATE AS NEEDED)

## Next Steps

1. Pick a specific failing test
2. Read the test to understand what it's checking
3. Read the card/ability text
4. Read the generated frames
5. Compare frames to ability text (every stage)
6. Check if engine accepts the frame format
7. Fix the specific issue in frame generation
8. Test the fix
9. Repeat for other failing tests

## DO NOT OVERMASSAGE

- Make minimal, targeted fixes
- Fix only what's actually broken
- Don't add "just in case" logic
- Don't change things that are working
- Focus on specific test failures
