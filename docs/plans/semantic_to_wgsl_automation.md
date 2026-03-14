# Semantic Tests to WGSL Porting Analysis

## Current Semantic Test Architecture

### Structure Overview
```rust
SemanticCardTruth {
    id: String,           // Card ID like "PL!N-bp1-001-PR"
    abilities: Vec<SemanticAbility>
}

SemanticAbility {
    trigger: String,      // "OnPlay", "OnLiveStart", etc.
    condition: Option<String>,
    sequence: Vec<SemanticSegment>
}

SemanticSegment {
    text: String,         // Human-readable description
    deltas: Vec<SemanticDelta>
}

SemanticDelta {
    tag: String,          // "hand", "deck", "score", "energy"
    value: serde_json::Value  // +1, -2, etc.
}
```

### Test Execution Flow
1. Setup environment (Standard, Minimal, NoEnergy, etc.)
2. Trigger event (OnPlay, OnLiveStart, etc.)
3. Execute bytecode via CPU interpreter
4. Compare state deltas against expected semantic deltas

## Challenges for WGSL Porting

### 1. State Comparison Location
- **CPU Tests**: Compare states in Rust after execution
- **GPU Tests**: GPU only executes; comparison must be on CPU side
- **Solution**: Already implemented in `run_parity_check()` - CPU compares GPU output

### 2. Interaction Resolution
- **CPU Tests**: `resolve_interaction()` handles choices dynamically
- **GPU Tests**: Uses `forced_action` for deterministic choices
- **Gap**: Complex multi-choice interactions differ

### 3. Delta Format Translation
- **Semantic**: High-level deltas like `hand:+1`, `deck:-2`
- **GPU State**: Low-level struct fields like `hand_len`, `deck[0..31]`
- **Solution**: Create translation layer

## Automation Possibility Assessment

### What Can Be Automated (HIGH)

1. **Test Case Generation**
   ```python
   # Pseudocode for generator
   def generate_gpu_test_from_semantic(card_truth):
       test = GpuParityTest()
       test.card_id = card_truth.id
       test.trigger = map_trigger(card_truth.abilities[0].trigger)
       test.expected_deltas = card_truth.abilities[0].sequence[0].deltas
       return test
   ```

2. **Environment Setup Translation**
   ```rust
   // TestEnvironment -> GpuGameState initialization
   fn setup_gpu_env(env: TestEnvironment) -> GpuGameState {
       let mut state = GpuGameState::default();
       match env {
           TestEnvironment::Standard => { /* full setup */ },
           TestEnvironment::NoEnergy => { state.player0.energy_count = 0; },
           // ...
       }
       state
   }
   ```

3. **Delta Assertion Translation**
   ```rust
   fn assert_gpu_deltas(expected: &[SemanticDelta], gpu_state: &GpuGameState) {
       for delta in expected {
           match delta.tag.as_str() {
               "hand" => assert_hand_delta(delta, gpu_state),
               "deck" => assert_deck_delta(delta, gpu_state),
               // ...
           }
       }
   }
   ```

### What Cannot Be Automated (LOW)

1. **Complex Interaction Chains**
   - Multi-step choices with context-dependent options
   - Requires human analysis of interaction flow

2. **Missing GPU State Fields**
   - `live_score_bonus` (U11 Boost Score issue)
   - Need manual struct updates

3. **Opcode Coverage Gaps**
   - Some opcodes not implemented in WGSL
   - Need manual shader implementation

## Recommended Approach

### Phase 1: Automated Test Generator (2-3 days)
Create a tool that:
1. Reads `semantic_truth_v3.json`
2. Generates `test_gpu_parity_semantic.rs` with test cases
3. Maps semantic deltas to GPU state assertions

### Phase 2: Delta Translation Layer (1-2 days)
Create `gpu_semantic_bridge.rs`:
```rust
pub struct GpuSemanticBridge;

impl GpuSemanticBridge {
    pub fn apply_deltas_to_expected(state: &mut GpuGameState, deltas: &[SemanticDelta]);
    pub fn compare_actual_vs_expected(actual: &GpuGameState, expected: &GpuGameState) -> Vec<String>;
}
```

### Phase 3: Missing Field Additions (1 day)
Add missing fields to `GpuPlayerState`:
- `live_score_bonus: i32`
- Update WGSL shader accordingly

### Phase 4: Integration (1 day)
- Run generated tests
- Fix failures
- Document coverage

## Estimated Effort

| Task | Difficulty | Automation % |
|------|------------|--------------|
| Test case generation | Medium | 90% |
| Environment setup | Easy | 100% |
| Delta translation | Medium | 80% |
| Interaction handling | Hard | 20% |
| Missing fields | Easy | 50% |

**Overall**: ~70% of the work can be automated.

## Example: Generated Test

```rust
// Auto-generated from semantic_truth_v3.json
#[test]
fn test_gpu_parity_card_4340_reveal_until() {
    let mut state = create_test_state();
    state.core.players[0].deck = vec![9, 10, 73, 11, 12].into();
    state.core.players[0].hand = vec![4340].into();

    let expected_deltas = vec![
        SemanticDelta { tag: "deck".to_string(), value: json!(-3) },
        SemanticDelta { tag: "discard".to_string(), value: json!(+2) },
    ];

    let mut gpu_state = state.to_gpu(&db);
    gpu_state.forced_action = ACTION_BASE_HAND + 0;

    let mut results = vec![GpuGameState::default(); 1];
    manager.run_single_step(&[gpu_state], &mut results);

    assert_gpu_deltas(&expected_deltas, &results[0]);
}
```

## Conclusion

**Yes, semantic tests can be largely automated for WGSL parity testing.**

The key insight is that:
1. The semantic test format is already structured data (JSON)
2. GPU parity framework already exists (`run_parity_check`)
3. Delta comparison can be translated to GPU state field comparison

The main manual work is:
1. Adding missing GPU state fields
2. Handling complex interaction chains
3. Implementing missing WGSL opcodes
