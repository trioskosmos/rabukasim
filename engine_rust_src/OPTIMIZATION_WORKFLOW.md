# Game Engine Performance Optimization Workflow (Board-State-First)

## Overview
Performance depends on board state complexity, not just operation type. An empty board is instant; a cluttered board with abilities triggers expensive calculations. This workflow focuses on identifying which board configurations cause slowness and why.

## Core Principle
> **A step can be instant on an empty board, but that's not how the game is played.**

We must analyze real game positions to find expensive code paths.

---

## Workflow Steps

### 1. Play Games & Capture Slow Positions
Run realistic game simulations to find positions that actually cause slowness:

```bash
cargo bench --bench micro_benchmarks -- --noplot --measurement-time 5
```

This captures:
- Full game state JSON when slowness occurs (>1μs threshold)
- Board composition (stage cards, live zone, hand sizes)
- Active effects (granted abilities, transforms, modifiers)
- Saved to: `target/slow_events.json`

### 2. Analyze Board State Patterns
Run the analyzer to see what board configurations correlate with slowness:

```bash
cargo run --bin analyze_slow_events -- target/slow_events.json
```

Look for patterns like:
- **High stage occupancy** (3 cards vs 0 cards)
- **Granted abilities** (ability stacking)
- **Active effects** (color transforms, cost modifiers)
- **Yell cards** (performance phase complexity)
- **Large hand/discard piles** (counting effects)

### 3. Map Board States to Code Paths
For each slow pattern, trace which code paths are triggered:

| Board State Pattern | Likely Expensive Code Path |
|---------------------|---------------------------|
| Cards on stage with constant abilities | `calculate_board_aura()` scanning all abilities |
| Cards in live zone during Performance | `do_performance_phase()` blade/heart calculation |
| Granted abilities present | Ability condition checking in loops |
| Color transforms active | Heart calculation with transform loops |
| Many yell cards | Yell processing and trigger dispatch |
| Large hand/discard | `per_card` counting operations |

### 4. Identify Root Cause
Don't guess - verify by checking the code:

**For `LiveSet:step` slowness (most common):**
1. `handle_liveset()` ends phase → `auto_step()` triggers
2. `auto_step()` enters `PerformanceP1/P2` phase
3. `do_performance_phase()` calculates:
   - Blades: loops stage slots, calls `get_effective_blades()`
   - Hearts: loops stage slots, calls `get_effective_hearts()`
   - Yell: processes yell cards, dispatches triggers
   - Requirements: checks each live card against requirements

**Key expensive patterns found:**
- `calculate_board_aura()` called 6× per performance phase (once per slot for blades + hearts)
- Constant ability scanning in nested loops
- `check_condition()` called for each ability frame
- `serde_json` operations in logging paths (when `!ui.silent`)

### 5. Implement Targeted Optimization
Make minimal changes based on board state analysis:

**Pattern: Redundant aura calculation**
- Fix: Calculate aura once, reuse for all slots
- File: `src/core/logic/game.rs:sync_cached_stats()`
- Impact: 6× reduction in aura calculations per performance phase

**Pattern: Ability condition checking**
- Fix: Cache ability results or use bitmask pre-filtering
- File: `src/core/logic/rules.rs:calculate_board_aura()`
- Impact: Skip condition checking for abilities that don't apply

**Pattern: Unnecessary work when silent**
- Fix: Skip logging/serialization when `ui.silent = true`
- File: `src/core/logic/performance.rs`
- Impact: Remove debug overhead from benchmark runs

### 6. Verify No Regressions
Run full test suite:
```bash
cargo test
```
All tests must pass before proceeding.

### 7. Measure Improvement
Re-run benchmark and check:
- Fewer slow events for the same board patterns
- Lower max times for problematic operations
- Consistent performance across different board states

---
Examine the captured slow events:
```bash
cargo run --bin analyze_slow_events -- target/slow_events.json
```

This recreates:
- Exact game state when slowness occurred
- Phase, turn, and action context
- Re-runs operation to verify reproducibility

## Current Findings

### Slowest Operation: `LiveSet:step`
**Occurs when:** Player ends live set phase (action 0)
**Triggers:** Performance phase processing via `auto_step()`
**Max observed:** 3.2ms during phase transition
**Typical:** 500ns - 50μs depending on board complexity

### Board State Complexity Factors

| Factor | Simple Board | Complex Board | Impact |
|--------|--------------|---------------|--------|
| Stage cards | 0 | 3 cards with abilities | 6× aura calculations |
| Granted abilities | 0 | 5+ granted | More condition checks |
| Live zone cards | 0 | 3 live cards | Requirement checking |
| Yell cards | 0 | 10+ yell cards | Trigger dispatch |
| Color transforms | None | Active | Transform loop overhead |

### Code Paths by Board State

**Empty board (fast):**
- `handle_liveset()` - ends phase (fast)
- `auto_step()` - transitions phase (fast)
- `do_performance_phase()` - no cards to process (fast)
- `sync_all_stats()` - nothing to cache (fast)

**Board with 3 stage cards + 3 live cards (slow):**
- `handle_liveset()` - ends phase (fast)
- `auto_step()` - enters Performance phase (medium)
- `do_performance_phase()` - calculates:
  - Blades: 3 slots × `get_effective_blades()` → 3× `calculate_board_aura()`
  - Hearts: 3 slots × `get_effective_hearts()` → 3× `calculate_board_aura()`
  - Each aura calc scans all stage cards × all abilities
- `sync_all_stats()` - more work to cache (medium)

## Progress Log

### Session 3: Board-State-First Analysis
- Date: 2026-03-29
- **New Approach:** Focus on board configurations, not just timing
- **Enhancements:**
  - Added `BoardAnalysis` struct to capture board state patterns
  - Tracks: stage cards, live zone, granted abilities, active effects
  - Analyzer now shows patterns across slow events
- **Key Finding:** `LiveSet:step` slowness is from `do_performance_phase()` via `auto_step()`
- **Board State Discovery:** Even "empty" boards can be slow (3.2ms) during phase transitions
- **Optimization:** Cached aura calculation in `sync_cached_stats()` - 6× reduction

### Session 2: Fix Benchmark Serialization
- Date: 2026-03-29
- **Major Finding:** `format!("{:?}", state)` was causing massive overhead
  - Debug format serialized entire game state on every slow event
  - Changed to `serde_json::to_string(&state)` for proper JSON
- **Results**: 
  - Max times reduced from **118ms → 120μs** (96% improvement!)
  - Captured 2,419 slow events with valid JSON for analysis
  - Most slow events are `LiveSet:step` during turns 35-50
- **Analyzer Improvements**:
  - Fixed `phase` type from `i32` to `String` in SlowEvent struct
  - Added step operation handling (`LiveSet:step`, `Main:step`)
  - Can now rerun and profile slow operations accurately
- **Status:** ✅ Complete - workflow is fully functional

## Updated Baseline (After Serialization Fix)

| Operation | Avg | Max | Status |
|-----------|-----|-----|--------|
| LiveSet:step | 500ns | 135μs | **SLOWEST** |
| LiveSet:get_actions | 65ns | 175μs | Spikes |
| Main:get_actions | 70ns | 104μs | Spikes |
| Main:step | 98ns | 75μs | OK |

## Current Optimization Targets (Board-State Priority)

### 1. Performance Phase Blade/Heart Calculation
**Trigger:** Cards present on stage during performance phase
**Problem:** Redundant `calculate_board_aura()` calls (6× per phase)
**Fix:** Cache aura once, use `get_effective_blades_with_aura()` for all slots
**Status:** ✅ Implemented - aura calculated once in `sync_cached_stats()`
**Next:** Verify performance improvement with full stage boards

### 2. Ability Condition Checking
**Trigger:** Cards with constant abilities on stage
**Problem:** `ability_conditions_met()` called repeatedly in loops
**Fix:** Pre-filter by opcode mask, cache results per game state change
**File:** `src/core/logic/rules.rs:calculate_board_aura()`
**Status:** Pending - need to profile with ability-heavy boards

### 3. Yell Card Processing
**Trigger:** Many yell cards accumulated during performance
**Problem:** Each yell dispatches `OnReveal` trigger individually
**Fix:** Batch yell processing, defer non-critical triggers
**File:** `src/core/logic/performance.rs:do_yell()`
**Status:** Pending

### 4. Main Phase Action Generation
**Trigger:** Large hand size + cards with complex costs
**Problem:** `get_member_cost()` recalculates for each action
**Fix:** Cache cost calculations, early exit for unplayable cards
**File:** `src/core/logic/action_gen/main_phase.rs`
**Status:** Pending

## Next Steps

1. **Create test fixtures for slow board states** - Save specific game positions that trigger slowness:
   - 3 stage cards with constant abilities
   - Full live zones (3 cards)
   - 10+ yell cards accumulated
   - Granted ability chains

2. **Profile specific board configurations** - Use saved fixtures to:
   - Verify aura caching improvement
   - Identify remaining bottlenecks in ability checking
   - Measure trigger dispatch overhead

3. **Optimize based on board state patterns** - Target specific code paths:
   - `calculate_board_aura()` condition checking
   - `do_yell()` trigger batching
   - `get_legal_actions()` cost caching

4. **Update analyzer with card database lookup** - Show actual card names in analysis output for better understanding of slow positions
