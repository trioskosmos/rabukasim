# Test Suite Organization

This directory contains the engine test suite, organized by purpose and scope.

## Directory Structure

### `/qa`
**Purpose**: Official Q&A rule verification tests from the official Love Live Card Game Q&A documentation.

- Tests are sourced from published Q&A documents (Q1-Q300+)
- Each test validates a specific ruling, edge case, or clarification
- Tests are grouped by complexity and rule category
- **Key files**: `batch_1.rs`, `batch_2.rs`, `batch_3.rs`, `batch_4_unmapped_qa.rs`

**Run just QA tests**:
```bash
cargo test --lib qa -- --test-threads=4
```

### `/opcodes`
**Purpose**: Comprehensive coverage tests for bytecode opcodes and operation codes.

- Tests verify individual opcode behavior in isolation
- Tests verify opcode combinations and nesting
- **Includes**:
  - Basic opcode functionality tests
  - Edge cases for each opcode
  - Opcode interaction tests
  - Stress tests for rare/complex opcode combinations

**Run just opcode tests**:
```bash
cargo test --lib opcode -- --test-threads=4
```

### `/mechanics`
**Purpose**: Game mechanics and rule engine integration tests.

- Tests verify multi-turn sequences
- Tests verify phase transitions
- Tests verify state consistency during complex gameplay
- **Includes**:
  - Card interaction chains
  - Stat/effect buff combinations
  - Trigger and response mechanics
  - Game flow and phase management

**Run just mechanics tests**:
```bash
cargo test --lib mechanics -- --test-threads=4
```

### `/edge_cases`
**Purpose**: Stress tests, regression tests, and unusual scenarios.

- Tests for rare ability bytecode sequences
- Stress tests for complex nested conditionals
- Tests for boundary conditions and limits
- Regression tests for previously-fixed bugs
- **Includes**:
  - Longest/most complex compiled abilities
  - Stress tests for deeply nested conditions
  - Memory limits and performance stress
  - Multi-ability interaction stress tests

**Run just edge case tests**:
```bash
cargo test --lib edge_cases -- --test-threads=4
```

## Test Execution Strategies

### Quick CI Pass
```bash
# ~30 seconds - Tests critical paths only
cargo test --lib qa -- --test-threads=4
```

### Full Coverage
```bash
# ~18 seconds - All tests with parallelization
cargo test --lib
```

### Single-Threaded Debugging
```bash
# ~70 seconds - For deterministic ordering/bug reproduction
cargo test --lib -- --test-threads=1
```

### Category-Specific Testing
```bash
# Run tests from specific categories
cargo test --lib qa::batch_4
cargo test --lib opcode::rare_bytecode_stress
cargo test --lib mechanics::card_interaction
cargo test --lib edge_cases::complex_ability
```

## Total Test Count: 568

- QA Tests: 163 (Official Q&A document verification)
- Opcode Tests: ~150 (Bytecode operation coverage)
- Mechanics Tests: ~180 (Game flow and interaction)
- Edge Cases: ~75 (Stress, regression, rare scenarios)

## Performance Notes

- **Parallelization**: Tests run with 4-8 threads by default
- **Speed**: 17-18 seconds for full suite (parallelized)
- **Single-threaded**: ~70 seconds (use for deterministic debugging)
- **Memory**: ~200MB during test execution

## Adding New Tests

1. **New Q&A test?** → Add to `src/qa/batch_*.rs` (existing organization)
2. **New opcode test?** → Add to `/opcodes/opcode_*.rs`
3. **New mechanics test?** → Add to `/mechanics/game_flow.rs` or similar
4. **Stress/edge case?** → Add to `/edge_cases/stress_*.rs`

Tests automatically discovered via Cargo's `#[test]` attribute macro.
