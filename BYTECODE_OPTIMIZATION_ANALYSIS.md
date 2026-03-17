# Bytecode Optimization Analysis - Sunny Day Song Investigation

## What We Found

**Card 669 - SUNNY DAY SONG (PL!-bp5-021-L)**
- Current bytecode: 18 instructions (90 bytes)
- The ability triggers ON_LIVE_START with conditional multi-branch logic:
  1. COUNT_STAGE {MIN=1} → DRAW(1) for both + DISCARD_HAND(1) for both
  2. COUNT_STAGE {MIN=2} → SELECT_MEMBER filtering for μ's only + ADD_HEARTS(1)  
  3. COUNT_STAGE {MIN=3} + UNIQUE_NAMES_COUNT {MIN=3} → BOOST_SCORE(1)

## Analyzed Commits

### Recent Bytecode-Related Changes (Mar 12-15, 2026)

**Commit 74972de** - "feat: refine engine serializer, compiler logic, and interpreter handlers"
- Date: Mar 12, 2026
- Files: `ability.py` (347 additions - major refactor)
- Key changes:
  - Introduced `PackedFilterSpec` dataclass for filter attribute unpacking
  - Added `unpack_a_standard()` for debugging/analysis
  - Created filter formatting utility functions (`format_filter_attr`, `explain_filter_attr`)
  - Added semantic ability representation layer
  - **No obvious bytecode instruction removal or optimization visible in diffs**

**Commit 0b67295** - "Optimize character filtering and align bytecode packing with metadata"
- Date: Mar 15, 2026  
- Files: `instruction.rs` (slot decoding optimization), `filter.rs` (character filtering)
- Key changes:
  - Runtime optimization of `DecodedSlot` - replaced named constants with hardcoded bit shifts
  - Optimized character filter decoding logic
  - **Changes are Rust runtime optimization only - NO bytecode generation changes**

## Analysis: What Actually Happened

### The Core Problem
The user stated: **"Sunny Day Song used to have 22 opcodes"** but didn't specify when or why it changed. Analysis suggests:

1. **No Direct Bytecode Reduction in Recent Commits**
   - Neither commit 74972de nor 0b67295 changed the *compilation* of bytecode
   - The changes were either:
     - Runtime optimization (how Rust decodes already-compiled bytecode)
     - Refactoring/cleanup of Python compiler code structure
     - Character filtering optimization

2. **Hypothesis: The "22 opcodes" → "18 opcodes" Reduction**
   
   If SUNNY DAY SONG went from 22 to 18 instructions (-4 instructions = -20 bytes), the optimization likely involved:
   
   **a) Conditional Branch Optimization**
   - Original: Explicit `JUMP_IF_FALSE` instructions for each condition branch
   - Optimized: Shared jump targets or removed redundant jump instructions
   
   **b) Possible: JUMP instruction coalescing**
   - Before: Each condition had its own JUMP_IF_FALSE → effect sequence → unconditional JUMP_TO_END
   - After: Combined jump targets to reduce total jumps
   
   **c) Effect Compilation Changes**
   - Before: Each effect fully compiled with conditional check overhead
   - After: Shared effect execution paths

3. **Where the Change Probably Happened (Not Visible in Recent Commits)**
   - Earlier commit (month ago?): Core `_compile_condition()` or `_compile_effect()` methods
   - The optimization is likely in how conditional branches are encoded
   - Commit 74972de expanded the compiler code significantly but refactored existing logic
   - The actual optimization may predate the recent work

### Why This Matters for Card 41 (Niko)

The optimizations mentioned likely revealed a **stale bytecode issue**, not a regression:

1. **Card 41 had correct optional flag (bit 61) all along**
   - The bytecode was generated correctly in a previous compilation
   - Optional flag was properly set: value = 536870912 (bit 29 of upper word)

2. **The "bug" was stale compiled state**
   - When opcodes were optimized to be fewer, the compilation wasn't re-run
   - `cards_compiled.json` had stale data from before the optimization
   - Recompilation with `python -m compiler.main` fixed it

3. **No regression in the optimization itself**
   - The optimization didn't *break* optional flags
   - It just reduced opcode count through more efficient encoding
   - When recompiled, Card 41 got the correct bytecode with optional flag intact

## Key Insight: Over-Optimization vs Under-Testing

The issue pattern suggests:
- ✅ Bytecode optimization was done (reduced opcodes)
- ❌ Compiled card database was not re-generated after optimization
- ❌ Tests didn't catch stale bytecode (they might test compiled output but not diffs)
- ✅ Recompilation resolved the issue

**Optimization itself was not "overdone"** - it was just that the compilation cache wasn't updated.

## Recommendations

1. **Ensure compilation is part of CI/CD** after any compiler changes
2. **Add regression tests** comparing bytecode before/after optimization
3. **Version the bytecode format** so stale caches are invalidated
4. **Consider tracking which commits changed bytecode structure** for audit trail

## Wait State vs Tap State Clarification

As user noted:
- ウェイト = **Wait** (state where member is waiting/inactive)
- タップ = **Tap** (similar inactive state)
- Both currently map to `SET_TAPPED` opcode (51) in the engine
- Card 41: Uses wait cost, compiled as TAP_SELF (semantically correct mapping)
- This is fine - the implementation is just using one opcode for both states
