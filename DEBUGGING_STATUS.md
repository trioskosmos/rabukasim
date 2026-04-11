# Debugging Status: Cargo Test Failures

## Objective
Achieve zero failures in `cargo test` by fixing frame source definitions.

## Current State (Frame Mode)
- **Passed**: 685 tests
- **Failed**: 14 tests
- **Build command**: `python tools/build_cards.py --sync-launcher-assets --ability-source-mode frame`
- **Test command**: `cargo test` (in `engine_rust_src`)

## File Paths

### Build & Test Files
- **Build script**: `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\tools\build_cards.py`
- **Rust test suite**: `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\`

### Compiler Files
- **Main compiler (frame mode)**: `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine\compiler\main.py`
- **Semantic processor (broken)**: `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine\compiler\semantic_processor.py`

### Data Files
- **Authored frame source**: `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\ability_frame_source.json`
- **Compiled card data**: `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json`
- **Card ID mapping**: `c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\card_id_mapping.json`

## Remaining 14 Failures (Frame Mode)

### High Priority
1. **test_q196_select_member_empty** (2 instances)
   - Card 332: 桜坂しずく (PL!N-pb1-003-P+)
   - Ability text: "Activation: Pay EE: Put this card from hand to discard: Draw 1 card, until live end, 1 Nijigasaki member on your stage gains blade. This ability can only be activated when this card is in hand."
   - Issue: SUM_VALUE check at ip=0 fails when no Nijigasaki member on stage, preventing ability from executing. Test expects ability to resolve (draw 1 card) even when no member selected.
   - Current frames: SUM_VALUE → PAY_ENERGY → DRAW → SELECT_MEMBER → JUMP_IF_FALSE → RETURN

2. **test_q203_niji_score_buff** (2 instances)
   - Issue: Score buff timing/activation order

3. **test_q214_zero_score_live_recovery**
   - Issue: Energy cost logic for live recovery

4. **test_q236_revealing_base_dream_believers**
   - Issue: Name matching for variant recovery

5. **test_live_260_live_start_paying_energy_with_nijigasaki_grants_score_bonus**
   - Issue: Energy activation score bonus

### Medium Priority
6. **test_ability_64_kurosawa_dia_flavor_choice**
7. **test_ability_64_option1_aqours_blade**
8. **test_ability_64_option2_saintsnow_position_change**
   - Issue: Choice logic for ability 64

9. **test_condition_cost_compare**
10. **test_condition_heart_compare**
    - Issue: Comparison operators (GE, GT, LE, LT, EQ, NE)

11. **test_position_change_text_frames_include_explicit_destination_metadata**
    - Issue: Position change metadata

12. **test_optional_interaction_actions_real_card**
    - Issue: Optional interaction handling

## Recent Changes

### main.py (Frame Mode Compiler)
- Added `_post_process_frames()` function to insert JUMP_IF_FALSE after SELECT_MEMBER when followed by target-dependent effects (ADD_BLADES, ADD_HEARTS, ACTIVATE_MEMBER)
- This was intended to fix Q196 but the issue is more complex - the SUM_VALUE check at the beginning is the real problem

### semantic_processor.py (Semantic Mode - Broken)
- Added `_LOOK_AND_CHOOSE_COUNT_PATTERNS` regex patterns for inferring choose_count
- Removed CONDITIONAL opcode fallback (was generating unexecutable frames)
- **Status**: Semantic mode produces 132 failures, not usable

## Next Steps
1. Fix test_q196 by removing or correcting the SUM_VALUE check in the frame source for card 332
2. Fix remaining 13 failures by comparing ability text to frame source
3. Rebuild and retest after each fix
