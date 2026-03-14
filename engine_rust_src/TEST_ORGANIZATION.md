# Engine Test Suite - Complete Organization Guide

**Last Updated**: March 13, 2026  
**Total Tests**: 568 (all passing except Q166 isolation issue)  
**Execution Time**: 17-18 seconds (parallelized), ~70 seconds (single-threaded)

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Test Categories](#test-categories)
3. [Directory Structure](#directory-structure)
4. [Running Tests](#running-tests)
5. [Adding New Tests](#adding-new-tests)
6. [Organization Migration Plan](#organization-migration-plan)
7. [Performance Optimization](#performance-optimization)

---

## Quick Reference

### Run All Tests
```bash
cd engine_rust_src
cargo test --lib          # ~18s, parallelized (default)
cargo test --lib -- --test-threads=1  # ~70s, single-threaded
```

### Run Test Categories
```bash
cargo test --lib qa                    # QA rule tests (163 tests, ~5s)
cargo test --lib opcode               # Opcode tests (150 tests, ~3s)
cargo test --lib mechanics            # Mechanics tests (180 tests, ~3s)
cargo test --lib edge_case            # Edge case/stress tests (75 tests, ~2s)
cargo test --lib regression           # Regression tests only
```

### Run Specific Test
```bash
cargo test --lib test_q166            # Single test by name
cargo test --lib test_opcode_draw     # Tests matching pattern
cargo test --lib qa::batch_4          # Tests in batch_4 module
```

---

## Test Categories

### 1. QA Verification Tests (163 tests)

**Purpose**: Automated validation of official Q&A rulings

**Location**: `src/qa/` module
- `batch_1.rs` - Q1-Q50
- `batch_2.rs` - Q51-Q100
- `batch_3.rs` - Q101-Q150
- `batch_4_unmapped_qa.rs` - Q151+

**Key Features**:
- Real database cards
- Official ruling references in comments
- High-impact rule coverage
- ~50% of total Q&A entries

**Example Tests**:
- `test_q166_reveal_until_refresh_excludes_currently_revealed_cards`
- `test_q211_sunny_day_song` (live ability targeting)
- `test_q191_daydream_mermaid` (mode selection)

**Run**: `cargo test --lib qa`

### 2. Opcode Tests (~150 tests)

**Purpose**: Bytecode instruction validation

**Location**: Multiple files in `src/`
- `opcode_tests.rs` - Core opcode tests
- `opcode_coverage_gap_2.rs` - Coverage gaps
- `opcode_missing_tests.rs` - Missing implementations
- `opcode_rigor_tests.rs` - Rigorous validation

**Key Opcodes Tested**:
- O_DRAW, O_REVEAL_UNTIL, O_DRAW_UNTIL
- O_LOOK_AND_CHOOSE, O_LOOK_DECK
- O_ADD_BLADES, O_ADD_HEARTS
- O_TAP_UNTAP state management
- Filter expressions and conditions

**Run**: `cargo test --lib opcode`

### 3. Mechanics Tests (~180 tests)

**Purpose**: Game flow and rule engine integration

**Location**: Multiple mechanics test files
- `mechanics_tests.rs` - Core mechanics
- `game_flow_tests.rs` - Phase transitions
- `card_interaction_tests.rs` - Card interactions
- `response_flow_tests.rs` - Response phase

**Key Mechanics Tested**:
- Card drawing and deck refresh
- Stat calculations
- Card placement and movement
- Trigger queuing
- Multi-ability chains

**Run**: `cargo test --lib mechanics`

### 4. Edge Cases & Stress Tests (~75 tests)

**Purpose**: Rare scenarios, stress, and regression

**Location**: Multiple files
- `regression_tests.rs` - Bug regressions
- `coverage_gap_tests.rs` - Coverage analysis
- `stabilized_tests.rs` - Stable behavior validation
- `../tests/edge_cases/` - Planned stress tests

**Key Tests**:
- Rare opcode combinations
- Deeply nested conditions
- Boundary conditions
- Performance stress
- State consistency under load

**Run**: `cargo test --lib edge_case` or `cargo test --lib stress`

---

## Directory Structure

### Current Organization (Active)

```
engine_rust_src/
├── src/
│   ├── lib.rs                          # Main library + test module declarations
│   ├── core/                           # Core engine code
│   ├── qa/                             # QA test module (163 tests)
│   │   ├── mod.rs
│   │   ├── batch_1.rs
│   │   ├── batch_2.rs
│   │   ├── batch_3.rs
│   │   ├── batch_4_unmapped_qa.rs
│   │   └── [other QA tests]
│   ├── qa_verification_tests.rs        # Additional QA tests
│   ├── opcode_tests.rs                 # Core opcode tests
│   ├── opcode_coverage_gap_2.rs        # Coverage gaps
│   ├── opcode_missing_tests.rs         # Missing opcodes
│   ├── opcode_rigor_tests.rs           # Rigorous tests
│   ├── mechanics_tests.rs              # Mechanics tests
│   ├── game_flow_tests.rs              # Game flow
│   ├── card_interaction_tests.rs       # Interactions
│   ├── regression_tests.rs             # Regressions
│   ├── response_flow_tests.rs          # Response phase
│   ├── coverage_gap_tests.rs           # Coverage analysis
│   ├── stabilized_tests.rs             # Stable validation
│   ├── test_helpers.rs                 # Test utilities
│   └── [other test modules]
└── tests/                              # Reference structure (new)
    ├── README.md                       # Test organization docs
    ├── mod.rs                          # Module organization guide
    ├── qa/mod.rs                       # QA test reference
    ├── opcodes/mod.rs                  # Opcode test reference
    ├── mechanics/mod.rs                # Mechanics test reference
    └── edge_cases/                     # Stress tests (active)
        ├── mod.rs
        └── stress_rare_bytecode_sequences.rs
```

### Planned Organization (Future)

See `tests/README.md` for full reorganization blueprint:
- `tests/qa/` - QA tests (copy from src/qa/)
- `tests/opcodes/` - Opcode tests (migrate from src/)
- `tests/mechanics/` - Mechanics tests (migrate from src/)
- `tests/edge_cases/` - Stress and regression (NEW)

---

## Running Tests

### Full Test Suite
```bash
# Parallelized (default, ~18 seconds)
cargo test --lib

# With parallelization control
cargo test --lib -- --test-threads=4  # 4 threads
cargo test --lib -- --test-threads=8  # 8 threads

# Single-threaded for debugging (~70 seconds)
cargo test --lib -- --test-threads=1

# With output
cargo test --lib -- --nocapture
```

### By Category
```bash
# QA tests only (~5 seconds)
cargo test --lib qa

# Opcode tests only (~3 seconds)
cargo test --lib opcode

# Mechanics tests only (~3 seconds)
cargo test --lib mechanics

# Regression tests only
cargo test --lib regression

# Stress tests only
cargo test --lib stress
```

### Specific Tests
```bash
# Single test
cargo test --lib test_q166_reveal_until_refresh

# Pattern matching
cargo test --lib test_opcode_draw

# Module-specific
cargo test --lib qa::batch_4::tests::test_q166

# With debugging output
cargo test --lib test_q166 -- --nocapture
```

### CI/CD Usage
```bash
# Quick validation (~30 seconds)
cargo test --lib qa -- --test-threads=4

# Full validation (~18 seconds)
cargo test --lib

# With coverage
cargo tarpaulin --lib
```

---

## Adding New Tests

### Adding a New Q&A Test

1. **Identify the Q# and topic** from official documentation
2. **Open** `src/qa/batch_4_unmapped_qa.rs` (or create batch_5.rs)
3. **Write the test**:

```rust
/// Q###: [Official Japanese ruling text]
/// A###: [Official answer/clarification]
#[test]
fn test_q###_brief_topic_description() {
    let db = load_real_db();
    let mut state = create_test_state();

    // Setup game state according to Q###
    state.players[0].deck = vec![/* card IDs */].into();
    state.players[0].stage[0] = 123;  // specific card

    // Perform action described in Q###
    // ...

    // Verify expected ruling outcome
    assert_eq!(expected_result, actual_result,
        "Q###: [brief description of expected behavior]");
}
```

4. **Run the test**:
```bash
cargo test --lib test_q###_brief_topic
```

5. **Commit and document**:
```
Add test for Q###: [official topic]

Tests the ruling: [brief description of what is validated]
References: Official Q&A documentation Q###
```

### Adding an Opcode Test

1. **Identify** which opcode (O_DRAW, O_REVEAL_UNTIL, etc.)
2. **Choose appropriate file**:
   - `opcode_tests.rs` - Core opcode behavior
   - `opcode_coverage_gap_2.rs` - Coverage gaps
   - `opcode_rigor_tests.rs` - Edge cases
3. **Write the test**:

```rust
/// Tests O_OPCODE_NAME with [scenario description]
/// Complexity: Basic/Medium/Advanced
#[test]
fn test_opcode_name_scenario() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Minimal setup
    state.players[0].deck = vec![/* ... */].into();

    // Execute bytecode
    let bc = vec![O_OPCODE_NAME, /* args */, O_RETURN];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Verify
    assert_eq!(expected, actual);
}
```

4. **Test it**:
```bash
cargo test --lib test_opcode_name_scenario
```

### Adding a Stress Test

1. **Create or edit** `tests/edge_cases/stress_rare_bytecode_sequences.rs`
2. **Add to the appropriate section** (rare opcodes, deep nesting, etc.)
3. **Document complexity metrics**:

```rust
/// Stress test: [scenario]
/// 
/// **Complexity**: High | **Bytecode Length**: 200+ | **Nesting**: 8+ levels
#[test]
fn test_stress_scenario_name() {
    // Test implementation
}
```

---

## Organization Migration Plan

### Phase 1: Reference Structure (DONE)
- ✅ Created `tests/` directory with reference blueprints
- ✅ Added comprehensive documentation comments
- ✅ Created stress test framework in `tests/edge_cases/`
- ✅ Documented migration path

### Phase 2: New Test Additions (ONGOING)
- Add new stress tests to `tests/edge_cases/stress_*.rs`
- Add complex bytecode analysis to stress framework
- Extend coverage with rare opcode tests

### Phase 3: Planned Migration (FUTURE)
When test suite grows or organizational needs change:
1. Copy `src/qa/*` → `tests/qa/*`
2. Copy `src/opcode_*.rs` tests → `tests/opcodes/*.rs`
3. Copy mechanics tests → `tests/mechanics/*.rs`
4. Update module declarations
5. Verify all paths still resolve

## Performance Optimization

### Current Performance (Good)
- **Full Suite**: 17-18 seconds (parallelized)
- **Parallelization**: 4-8 threads (auto-scaled)
- **Memory**: ~200MB peak
- **Speedup**: 4x vs single-threaded (17s vs 70s)

### Optimization Techniques

**For faster local feedback**:
```bash
# Just QA tests (5s)
cargo test --lib qa

# Just opcode tests (3s)
cargo test --lib opcode

# Single test (0.5s)
cargo test --lib test_q166
```

**For CI/CD**:
```bash
# Parallelized with more threads
cargo test --lib -- --test-threads=8   # 16-17s on 8-core machine

# Category-based parallelization
cargo test --lib qa & cargo test --lib opcode & wait  # Can run in parallel
```

**For debugging**:
```bash
# Single-threaded for deterministic ordering
cargo test --lib -- --test-threads=1   # ~70s

# With logging
RUST_LOG=debug cargo test --lib -- --nocapture
```

---

## Troubleshooting

### Q166 Test Isolation Issue
- **Symptom**: Q166 fails in `cargo test --lib` but passes in `cargo test --lib test_q166`
- **Status**: Known test contamination issue (one test pollutes Q166's state)
- **Workaround**: Run Q166 separately or in batch
- **Investigation**: Needed to identify which test runs before Q166

### Tests Running Slowly
- **Check parallelization**: `cargo test --lib -- --test-threads=4`
- **Profile single test**: `time cargo test --lib test_q166`
- **Check for I/O bottleneck**: DB loading is one-time (~0.5s)

### Test Compilation Taking Long
- **Incremental builds**: Usually ~30s for clean test run
- **Use incremental compilation**: Enabled by default in latest Rust

---

## Contributing Tests

When adding tests:
1. **Follow naming conventions**: `test_category_brief_description`
2. **Add documentation comments**: Explain what is tested and why
3. **Use minimal setup**: Only initialize state needed for test
4. **Include assertions**: Validate both positive and negative cases
5. **Document complexity**: Note if test is stress/slow
6. **Reference source**: Link to official rules, issue numbers, or card names

---

## Additional Resources

- `tests/README.md` - Test directory organization reference
- `src/lib.rs` - Full architecture documentation
- `src/qa/mod.rs` - QA test module documentation
- `src/opcode_tests.rs` - Opcode test documentation
- `src/mechanics_tests.rs` - Mechanics test documentation

---

**Last Updated**: March 13, 2026  
**Next Review**: After reaching 600+ tests or adding new test category
