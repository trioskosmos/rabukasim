# GPU Parity Test Improvement Plan

## Current State Analysis

### 1. Existing Test Infrastructure

#### CPU-Only Parity Tests (`parity_tests.rs`)
- 31 tests that simulate WGSL behavior on CPU
- Tests opcodes like `O_DRAW`, `O_ADD_HEARTS`, `O_BOOST_SCORE`, etc.
- **Limitation**: Does not execute actual WGSL shader on GPU

#### GPU Parity Suite (`test_gpu_parity_suite.rs`)
- Uses `GpuManager` to execute WGSL shaders on real GPU
- Compares CPU `GameState` vs GPU `GpuGameState`
- **Limitation**: Only 6 unit tests + 3 production card tests

### 2. Gap Analysis

| Opcode | CPU Test | GPU Test | Notes |
|--------|----------|----------|-------|
| O_SET_HEART_COST | `untested_opcode_tests.rs` | ❌ Missing | Need to add |
| O_SEARCH_DECK | ❌ Simplified | ❌ Simplified | GPU draws instead of search |
| O_LOOK_DECK | `opcode_tests.rs` | ❌ Missing | GPU simplified |
| O_TRANSFORM_COLOR | `parity_tests.rs` | ❌ Missing | Need to add |

## Improvement Plan

### Phase 1: Add O_SET_HEART_COST GPU Parity Test

Following SKILL.md Section 4 "Porting a CPU Test to GPU":

```rust
// In test_gpu_parity_suite.rs

// S-UNIT-7: O_SET_HEART_COST (CPU Mirror: test_opcode_set_heart_cost)
// v = amount to set, s = color index
let s7_bc = vec![O_SET_HEART_COST, 3, 0, 2, O_RETURN, 0, 0, 0]; // Set color 2 cost to 3
add_card(&mut unit_db, 2007, "SET_HEART_COST", vec![], vec![(TriggerType::OnPlay, s7_bc, vec![])]);
```

### Phase 2: Extend run_parity_check

Add heart_req_additions comparison:

```rust
fn run_parity_check(...) -> bool {
    // ... existing checks ...

    // Check Heart Requirements
    for i in 0..2 {
        if cpu_state.players[0].heart_req_additions[i] != gpu_final.player0.heart_req_additions[i] {
            println!("  [FAIL] {}: Heart req additions mismatch at {}", name, i);
            mismatch = true;
        }
    }
}
```

### Phase 3: Automated Test Generation

Create a tool to automatically generate GPU parity tests from CPU tests:

```python
# tools/generate_gpu_parity_tests.py
# Scans opcode_tests.rs for test cases
# Generates corresponding test_gpu_parity_suite.rs entries
```

## Recommended Next Steps

1. **Immediate**: Add `O_SET_HEART_COST` test to `test_gpu_parity_suite.rs`
2. **Short-term**: Extend `run_parity_check` to compare all `GpuPlayerState` fields
3. **Long-term**: Create automated test generation from CPU tests

## Better Approach: Unified Test Framework

Consider creating a unified test framework:

```rust
#[derive(Clone)]
struct ParityScenario {
    name: &'static str,
    opcode: i32,
    v: i32, a: i32, s: i32,
    initial_state: fn(&mut GameState),
    assertions: fn(&GameState, &GpuGameState),
}

#[test]
fn test_all_parity_scenarios() {
    let scenarios = vec![
        ParityScenario {
            name: "O_SET_HEART_COST",
            opcode: O_SET_HEART_COST,
            v: 3, a: 0, s: 2,
            initial_state: |s| { /* setup */ },
            assertions: |cpu, gpu| { /* verify */ },
        },
        // ... more scenarios
    ];

    for scenario in scenarios {
        run_parity_scenario(&scenario);
    }
}
```

This approach:
- Reduces boilerplate
- Makes it easy to add new tests
- Ensures consistent coverage
