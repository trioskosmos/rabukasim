# GPU Parity Test Conversion Plan

## Overview
Convert existing Rust CPU tests to GPU parity tests automatically.

## Source Test Files Analysis

### 1. Test File Locations
- `engine_rust_src/src/opcode_tests.rs` - Core opcode tests
- `engine_rust_src/src/mechanics_tests.rs` - Game mechanics tests
- `engine_rust_src/src/untested_opcode_tests.rs` - Previously untested opcodes
- `engine_rust_src/src/opcode_missing_tests.rs` - Gap coverage tests
- `engine_rust_src/src/opcode_rigor_tests.rs` - Rigorous edge case tests
- `engine_rust_src/src/ability_tests.rs` - Ability interaction tests

### 2. Common Test Pattern
```rust
#[test]
fn test_opcode_XXX() {
    let db = create_test_db();  // or load_real_db()
    let mut state = create_test_state();
    // Setup state...
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    let bc = vec![OPCODE, v, a, s, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);
    // Assertions...
}
```

### 3. GPU Parity Test Pattern
```rust
// In test_gpu_parity_suite.rs
let sN_bc = vec![OPCODE, v, a, s, O_RETURN, 0, 0, 0];
add_card(&mut unit_db, 20NN, "NAME", vec![], vec![(TriggerType::OnPlay, sN_bc, vec![])]);
// ... after GPU manager creation ...
let mut state = create_test_state();
// Setup state...
state.core.players[0].hand = vec![20NN].into();
if !run_parity_check(&unit_manager, &unit_db, &state, Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id(), "UN NAME") { mismatch_count += 1; }
```

## Conversion Strategy

### Phase 1: Extract Test Metadata
Create a script that:
1. Parses Rust source files using syn crate
2. Extracts test function names, bytecode vectors, and setup code
3. Identifies assertions that can be converted to parity checks

### Phase 2: Generate GPU Test Code
For each extracted test:
1. Convert `resolve_bytecode` calls to `PlayMember` actions
2. Map assertions to `compare_states` checks
3. Handle special cases (interactions, choices)

### Phase 3: Handle Complex Cases
Some tests require special handling:
- **Interaction-based tests**: Need choice propagation
- **Real DB tests**: Need card ID mapping
- **Multi-step tests**: Need sequential actions

## Implementation Plan

### Step 1: Create Test Extraction Tool
```rust
// tools/extract_tests.rs
struct ExtractedTest {
    name: String,
    bytecode: Vec<i32>,
    setup_code: String,
    assertions: Vec<String>,
    uses_real_db: bool,
}
```

### Step 2: Generate Parity Test Code
```rust
// tools/generate_parity_tests.rs
fn generate_parity_test(test: ExtractedTest) -> String {
    // Generate add_card call
    // Generate state setup
    // Generate run_parity_check call
}
```

### Step 3: Integrate with Build
Add to Cargo.toml:
```toml
[[bin]]
name = "generate_parity_tests"
path = "tools/generate_parity_tests.rs"
```

## Current Issues to Address

### 1. O_BOOST_SCORE Mismatch
- CPU: `live_score_bonus += v`
- GPU: `score += v`
- Fix: Add `live_score_bonus` field to GPU state or change CPU behavior

### 2. Interaction-Based Opcodes
- O_TAP_OPPONENT, O_MOVE_TO_DISCARD require choice handling
- Need to implement choice propagation from `forced_action`

### 3. State Field Parity
- Some CPU fields not in GPU state
- Need to audit and add missing fields

## Next Steps
1. Fix O_BOOST_SCORE parity issue
2. Create extraction tool prototype
3. Generate tests for simple opcodes first
4. Gradually handle complex cases
