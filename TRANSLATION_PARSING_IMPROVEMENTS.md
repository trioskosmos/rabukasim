# Translation and Parsing Improvements Needed

## Test Failure Analysis (148 remaining failures)

### 1. Cost Reduction Failures
**Failing Tests:**
- Emma's cost in hand should be 15 (17 - 2) - got 17
- Rin should reduce in hand when lilywhite in success pile - got 15
- Cost-13 blade aura should apply when 2+ cost 13+ members on stage - got 0
- Cost should be 20 - 4 = 16 - got 20

**Root Cause:** Cost reduction frames not being generated with correct filter conditions

**Effect Parser Issues:**
- `reduce_cost` action exists but may not extract all patterns (lines 1596, 3161, 3170)
- Missing patterns for:
  - "コストが減る" (cost decreases)
  - "コストがX減る" (cost decreases by X)
  - Stage-based cost reduction (e.g., "when member on stage")
  - Success pile-based cost reduction (e.g., "when card in success pile")

**Frame Converter Issues:**
- `REDUCE_COST` opcode mapping exists (line 572) but may need:
  - Better filter condition generation
  - Support for zone-based reduction (hand, stage, success_pile)
  - Support for condition-based reduction (e.g., "if member on stage")
  - Per-card reduction logic (line 579) may not be working

### 2. Score/Buff Failures
**Failing Tests:**
- Q203 niji score buff: energy+member should grant +3 - got 0
- Q203 member activation alone should grant +2 - got 0
- Q49 Oh,Love&Peace! should record +1 live score bonus - got 0
- Card 120 should have 5 blades (3 base + 2 bonus) - got 3

**Root Cause:** Buff frames not being generated or not being applied correctly

**Effect Parser Issues:**
- Score buff patterns may not be extracted correctly
- Blade buff patterns from success pile may be missing
- Multi-trigger buff stacking (energy + member) may not be handled

**Frame Converter Issues:**
- `ADD_BLADES` and `BOOST_SCORE` opcodes exist (lines 65, 77)
- May need:
  - Success pile condition support
  - Multi-trigger buff accumulation
  - Permanent vs temporary buff distinction

### 3. Suspension/Prompt Failures
**Failing Tests:**
- Should suspend for selection - got Main
- Should suspend for opponent selection - got Main
- Should suspend for PAY_ENERGY Optional - got Main
- Should pause for on-live-success discard choice - got Main

**Root Cause:** Optional cost suspension logic not working

**Frame Converter Issues:**
- Optional cost handling exists (lines 307-326) but may not generate correct suspension frames
- Need to ensure:
  - Optional costs properly suspend to Response state
  - Suspension frames have correct metadata
  - Multiple optional costs are handled correctly

### 4. Energy/Draw Failures
**Failing Tests:**
- Should have drawn until 5 cards - got 0
- Should have drawn 1 card - got 1
- Should have charged energy - got 7
- First play should add exactly 1 energy card - got 0

**Root Cause:** DRAW and ENERGY_CHARGE frames not executing correctly

**Effect Parser Issues:**
- Draw patterns may not extract count correctly
- Energy charge patterns may be missing

**Frame Converter Issues:**
- `DRAW` and `ENERGY_CHARGE` opcodes exist (lines 63, 118)
- May need better condition handling

### 5. Ability/Trigger Failures
**Failing Tests:**
- Q171 until-live-end ability should exist - got 0
- Q204 multi-name member should count as second Karin - got 0
- 717 should untap energy after baton touch - got 2

**Root Cause:** Ability granting and trigger condition evaluation

**Effect Parser Issues:**
- `gain_ability` action exists but may not handle:
  - Duration conditions (until live end)
  - Multi-name matching
  - Post-resolution effects

**Frame Converter Issues:**
- `GRANT_ABILITY` opcode exists (line 95)
- May need:
  - Duration frame support
  - Multi-name condition support
  - Post-resolution frame ordering

### 6. Condition/Requirement Failures
**Failing Tests:**
- Q110 Vienna should increase generic requirement by 1 - got 0
- Q117 Viennas should trigger penalties - got 0
- Q230 0 vs 0 should grant 2 hearts - got 0
- Q239 empty energy zone should gain 1 energy - got 0

**Root Cause:** Condition evaluation and requirement modification

**Effect Parser Issues:**
- Requirement modification patterns may be missing
- Heart granting patterns may not extract correctly

**Frame Converter Issues:**
- Need opcode for requirement modification (INCREASE_COST exists at line 99)
- Need better condition frame generation

## Priority Improvements

### High Priority (Affects many tests)
1. **Fix cost reduction frame generation** - affects Emma, Rin, cost-13 aura tests
2. **Fix optional cost suspension** - affects many prompt/suspension tests
3. **Fix buff/score frame generation** - affects Q203, Q49, Card 120 tests

### Medium Priority
4. **Fix draw/energy frame generation** - affects draw/energy tests
5. **Fix ability granting with duration** - affects Q171, Q204 tests

### Lower Priority
6. **Fix condition evaluation** - affects Q110, Q117, Q230, Q239 tests

## Specific Code Changes Needed

### effect_parser.py
1. Add cost reduction patterns:
   - "コストが([\d]+)減る"
   - Stage-based: "ステージに.*メンバーがいる場合、コストが減る"
   - Success pile-based: "成功ライブカード置き場に.*がある場合、コストが減る"

2. Add buff patterns:
   - Score buffs from specific conditions
   - Blade buffs from success pile
   - Multi-trigger buff accumulation

3. Add suspension/prompt patterns:
   - Better optional cost detection
   - Suspension state metadata

### semantic_to_frame_converter.py
1. Improve REDUCE_COST frame generation:
   - Add zone-based reduction support
   - Add condition-based reduction support
   - Fix filter condition generation

2. Improve optional cost handling:
   - Ensure suspension frames are generated
   - Fix suspension state metadata

3. Improve buff frame generation:
   - Add success pile condition support
   - Add multi-trigger buff accumulation
   - Add permanent/temporary distinction

4. Add missing opcodes:
   - Requirement modification
   - Duration frames for abilities
