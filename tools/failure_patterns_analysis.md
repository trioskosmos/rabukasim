# Failure Patterns Analysis

After regenerating ability_frame_source.json from pure semantic extraction, we have 114 test failures.

## Major Patterns Identified

### 1. Score Buff Issues (~20-30 failures)
**Pattern**: Score values not being extracted correctly
- Q203: energy activation should grant the +1 live score bonus
- Q203: member activation alone currently resolves to +2 instead of +1
- Q49: Oh,Love&Peace! should record a +1 live score bonus
- 583: having at least one active energy should grant +1 live score at live start
- 709: three stage members with pairwise-distinct names and costs should grant the score bonus
- 260: paying 2 energy with a Nijigasaki stage member should grant +1 live score
- 459: live start should suspend to choose an Aqours stage member

**Root Cause**: Parser not extracting numeric values from "+1", "+2" patterns in score buff text

**Impact**: HIGH - affects many score-related abilities

### 2. Cost Reduction Issues (~10-15 failures)
**Pattern**: Cost reduction values not being extracted correctly
- Emma Verde: cost in hand should be 15 (17 - 2), but resolves to 0
- Rin: should reduce in hand when a lilywhite card is in the success live pile
- Cost should be 20 - 4 = 16

**Root Cause**: Parser not extracting numeric values from "コストは2減る" (cost reduces by 2) patterns

**Impact**: HIGH - affects cost reduction abilities

### 3. Heart Addition Issues (~10-15 failures)
**Pattern**: Heart addition values not being extracted correctly
- Q230: 0 vs 0 should be equal, granting 2 hearts
- card 157: should grant +2 hearts to the live
- card 4794: should grant +2 hearts to the live

**Root Cause**: Parser not extracting numeric values from heart addition patterns

**Impact**: HIGH - affects heart-related abilities

### 4. Condition Extraction Issues (~15-20 failures)
**Pattern**: Conditions not being extracted correctly
- Q171: the until-live-end granted ability should exist immediately after activation
- Q204: the multi-name member should count as a second Karin for the same-name live-start condition
- Q144: the effect should pause on filtered opponent-member target selection
- 672: without an A-RISE member on stage should not trigger

**Root Cause**: Parser not extracting conditions like "until live end", "multi-name", "group conditions"

**Impact**: HIGH - affects conditional abilities

### 5. Energy Activation Issues (~5-10 failures)
**Pattern**: Energy activation states not being set correctly
- card 557: Charged energy should be tapped (WAIT)
- 717: should untap the two tapped energy cards after baton touch

**Root Cause**: Parser not extracting "ウェイト状態" (wait state) condition

**Impact**: MEDIUM - affects energy-related abilities

### 6. Blade Aura Issues (~5-10 failures)
**Pattern**: Blade addition values not being extracted correctly
- Card 120: should have 3 (base) + 2 bonus from 2 cards in success pile = 5 blades
- 693: revealing cards with at least three distinct blade-heart types should add heart01

**Root Cause**: Parser not extracting blade count values from complex conditions

**Impact**: MEDIUM - affects blade-related abilities

### 7. Choice/Selection Issues (~10-15 failures)
**Pattern**: Choice branches not being handled correctly
- 558: declining the self-tap branch should start from an optional yes-or-no prompt
- 854: the draw branch should add exactly one card to hand
- 761: choosing the single-recovery mode must still recover exactly one live
- 8844: three different names on stage should grant exactly one additional heart

**Root Cause**: Parser not extracting choice branches and their conditions correctly

**Impact**: HIGH - affects choice-based abilities

## Biggest Wins (Priority Order)

### 1. Fix Numeric Value Extraction (Score, Cost, Hearts)
**Estimated Impact**: 40-50 failures
**Fix Location**: `tools/ability_extraction/effect_parser.py`
**Specific Fixes**:
- Extract +1, +2, etc. from score buff text
- Extract "コストは(\d+)減る" (cost reduces by X) - already exists but not working
- Extract heart addition values from patterns

### 2. Fix Condition Extraction
**Estimated Impact**: 15-20 failures
**Fix Location**: `tools/ability_extraction/condition_parser.py`
**Specific Fixes**:
- Extract "until live end" duration conditions
- Extract "multi-name" conditions
- Extract group conditions like "虹ヶ咲", "Liella!", etc.

### 3. Fix Choice Branch Extraction
**Estimated Impact**: 10-15 failures
**Fix Location**: `tools/ability_extraction/effect_parser.py`
**Specific Fixes**:
- Extract choice branches from "以下から1つを選ぶ" patterns
- Extract conditions for each choice branch

### 4. Fix Energy State Extraction
**Estimated Impact**: 5-10 failures
**Fix Location**: `tools/ability_extraction/effect_parser.py`
**Specific Fixes**:
- Extract "ウェイト状態" (wait state) condition for energy activation

### 5. Fix Blade Count Extraction
**Estimated Impact**: 5-10 failures
**Fix Location**: `tools/ability_extraction/effect_parser.py`
**Specific Fixes**:
- Extract blade count values from complex conditions like "success pile cards"

## Summary

The main issue is that the semantic extraction parser is not extracting numeric values and conditions correctly from ability text. The parser needs to be fixed to:
1. Extract numeric values from score, cost, heart, and blade patterns
2. Extract conditions like group membership, multi-name, duration, etc.
3. Extract choice branches and their conditions

Fixing these parser issues would resolve the majority of the 114 test failures.
