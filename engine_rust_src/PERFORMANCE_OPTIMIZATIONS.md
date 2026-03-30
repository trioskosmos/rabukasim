# Performance Optimization Guide

This document explains how to use and understand the performance optimizations in the LOVECA engine.

## Key Principle: Signal Over Absolute Numbers

**IMPORTANT:** Games are played with random card draws and AI decisions. This means:
- **Benchmark numbers will vary** between runs due to different game paths
- **Use metrics as signals** for what can be improved, not as absolute targets
- **Compare before/after** on the same seed or with statistical averaging
- **Focus on outliers** (max times) more than averages

Example: If one run shows 250K steps/sec and another shows 230K steps/sec, this is normal variation. What matters is:
- Did the max step time decrease?
- Are there fewer operations exceeding thresholds?
- Is the worst-case path faster?

## Running Performance Benchmarks

### Quick Throughput Test
```bash
cargo run --bin bench_throughput --release
```
This runs 100 games and reports steps/sec. Good for quick iteration.

### Detailed Benchmark Suite
```bash
cargo bench --bench micro_benchmarks -- --noplot
```
This captures detailed timing for all operations and identifies slow outliers.

### Single Game Profiling
```bash
cargo run --bin profile_game --release
```
Runs a single game with detailed per-step timing.

## Silent Mode: The Primary Optimization

All UI and debug overhead is automatically eliminated when `state.ui.silent = true`:

- No JSON building for UI elements
- No debug print statements
- No performance history tracking
- Minimal logging overhead

**This is the default for benchmarks.**

## Architectural Optimizations

### 1. Pre-computed Card Metadata (`MemberCard`)

The engine pre-computes expensive properties at card load time:

```rust
// In card_db.rs - MemberCard fields
pub has_constant_score_boost: bool,  // Does card have O_BOOST_SCORE abilities?
pub unconditional_score_boost: i32,    // Pre-computed boost value (no conditions)
pub ability_opcodes_mask: u128,        // Which opcodes are present (bitmask)
pub trigger_mask: u32,                 // Which triggers are present (bitmask)
```

**Usage:** During score calculation, cards without `has_constant_score_boost` are skipped entirely, avoiding expensive ability scanning.

### 2. Ability Mask Fast Path

```rust
// In performance.rs - skip cards without score boosts
if !m.has_constant_score_boost {
    continue;  // Skip expensive ability scanning
}
```

Cards without `O_BOOST_SCORE` abilities are skipped during performance phase calculations.

### 3. Conditional vs Unconditional Fast Path

```rust
// Fast path: unconditional boosts (no condition checking needed)
if m.unconditional_score_boost > 0 {
    constant_bonuses.insert(cid, m.unconditional_score_boost);
}

// Only check conditional abilities (expensive condition checking)
if ab.conditions.is_empty() {
    continue;  // Already counted above
}
```

Abilities without conditions use the pre-computed value. Only conditional abilities require expensive `check_condition()` calls.

### 4. Granted Abilities Fast Path

```rust
// Skip granted abilities scanning if empty
if !state.players[p].granted_abilities.is_empty() {
    // ... expensive processing ...
}
```

Empty granted ability lists skip all processing.

## Understanding Benchmark Output

### Throughput Benchmark
```
Completed 100 games (19429 steps)
Performance: 252,270 steps/sec
```

**Interpretation:**
- **Steps/sec**: Total game steps executed per second
- **Games count**: How many complete games finished
- **Higher is better**, but variance is expected

### Micro-Benchmarks (Slow Event Detection)
```
Operation: LiveSet:step
  Count: 1,247
  Avg: 892ns
  Max: 23,502μs  ← Focus here!
  Operations >100μs: 12
```

**Interpretation:**
- **Max time**: The worst-case step - this is your optimization target
- **Operations > threshold**: How many operations exceeded the threshold
- **Focus on reducing max and outliers**, not just average

## Optimization Workflow

1. **Run benchmark** to establish baseline
2. **Identify outliers** (operations exceeding thresholds)
3. **Analyze root cause** (which code path is slow?)
4. **Implement optimization** (add pre-computed fields, add fast paths)
5. **Re-run benchmark** to verify improvement
6. **Check tests pass** (`cargo test`)

## Current Optimizations Status

| Optimization | Status | Location |
|--------------|--------|----------|
| Silent mode (no UI overhead) | ✅ Active | `state.ui.silent` check |
| Pre-computed `has_constant_score_boost` | ✅ Active | `card_db.rs`, `performance.rs` |
| Pre-computed `unconditional_score_boost` | ✅ Active | `card_db.rs`, `performance.rs` |
| Ability mask fast path | ✅ Active | `ability_opcodes_mask` checks |
| Granted abilities fast path | ✅ Active | Empty list check |
| Aura calculation caching | ✅ Active | `sync_cached_stats()` |
| Debug print suppression | ✅ Active | `debug_mode` guards |

## Performance Debugging Tips

### Find Slow Operations
```bash
# Run with slow event capture
cargo bench --bench micro_benchmarks -- --noplot

# Analyze captured events
cargo run --bin analyze_slow_events -- target/slow_events.json
```

### Profile Specific Code
Add this to any function:
```rust
let start = Instant::now();
// ... code ...
let elapsed = start.elapsed();
if elapsed.as_micros() > 100 {
    eprintln!("Slow: {}μs", elapsed.as_micros());
}
```

### Check for UI Overhead in Silent Mode
Search for unguarded operations:
```bash
grep -n "serde_json::json!" src/core/logic/*.rs | grep -v "silent"
grep -n "eprintln!" src/core/logic/*.rs | grep -v "debug_mode"
```

## Expected Performance Characteristics

With current optimizations:
- **Typical step**: 500ns - 2μs
- **Complex board** (3 stage cards, full live zone): 5-20μs
- **Maximum observed**: 20-30μs (ability-heavy positions)
- **Throughput**: 200K-300K steps/sec (varies by game randomness)

**Remember:** Numbers vary between runs. Use them as signals for improvement, not absolute targets.

## Future Optimization Opportunities

1. **Condition result caching** - Cache `check_condition()` results across calls
2. **Ability batch processing** - Group similar abilities for vectorized processing
3. **Board state hashing** - Cache calculations based on board hash
4. **SIMD operations** - Vectorize card filtering operations

## Testing Optimizations

Always verify correctness:
```bash
# Run full test suite
cargo test

# Run specific game logic tests
cargo test game::

# Run with optimizations but verify behavior
cargo test --release
```

**Optimization rule:** Make it work, make it right, make it fast - in that order.
