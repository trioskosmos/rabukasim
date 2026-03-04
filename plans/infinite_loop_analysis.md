# Infinite Loop Analysis - Serialization and Actions

## Overview
Analysis of infinite loop causes in the Loveca game engine, focusing on serialization and action generation code.

## Key Findings

### 1. Infinite Loop Detection
- **Location**: [`alphazero/training/overnight_pure_zero.py:224`](alphazero/training/overnight_pure_zero.py)
- **Mechanism**: Detected when `moves_taken >= max_moves` (default: 2000 steps)
- **Output**: Logs to `alphazero/training/loops/trace_it{iteration}_g{game_num}_{reason}.json`

### 2. Trace Analysis (trace_it51_g5_Loop.json)
- **Reason**: "Loop" (not "Turn" or "Terminal")
- **Pattern Found**: 
  - Phase 10 (LiveResult) repeated with Action ID 11000 (Select Choice Index 0)
  - Actions 599-716 show repeated "Select Choice Index 0" on phase 10
  - This suggests a failure to progress past LiveResult phase

### 3. Key Files for Investigation

#### Action Generation
- [`engine_rust_src/src/core/logic/action_gen/response.rs`](engine_rust_src/src/core/logic/action_gen/response.rs)
  - Handles Response phase interactions
  - Contains fallback logic: `receiver.add_action(0)` if no actions generated (line 19-21)
  - Checks `choice_type` for various interaction types

#### Phase Handlers
- [`engine_rust_src/src/core/logic/handlers.rs`](engine_rust_src/src/core/logic/handlers.rs)
  - RPS handling (lines 54-112)
  - `handle_rps`: Detects draws and resets (line 92-96)
  - `handle_liveresult`: Processes LiveResult selections

#### Serialization
- [`engine_rust_src/src/core/logic/state.rs`](engine_rust_src/src/core/logic/state.rs)
  - `GameState` derives `Serialize, Deserialize` (line 252)
  - `CoreGameState` (line 128) contains `interaction_stack: Vec<PendingInteraction>`

- [`engine_rust_src/src/core/logic/models.rs`](engine_rust_src/src/core/logic/models.rs)
  - `PendingInteraction` struct (line 121)
  - Contains `actions: Vec<i32>` field (line 137) - potential serialization issue if actions grow infinitely

### 4. Potential Infinite Loop Causes

#### A. LiveResult Phase Loop
- When `live_result_selection_pending` is true, `auto_step` breaks early (game.rs line 869-870)
- If the AI keeps selecting the same action (11000), it may not progress

#### B. RPS Draw Loop  
- RPS draws restart RPS with `rps_choices = [-1, -1]`
- Could loop indefinitely if both players keep choosing same move

#### C. Interaction Stack Issues
- `PendingInteraction.actions` accumulates action history
- If deserialization doesn't clear this properly, could cause issues

### 5. Code Snippets

#### ResponseGenerator Fallback (response.rs:17-21)
```rust
if receiver.is_empty() {
    receiver.add_action(0);
}
```

#### Auto-Step Loop Safety (game.rs:828-885)
```rust
let mut loop_count = 0;
while loop_count < 40 {
    // Safety limit to prevent infinite auto-stepping
    loop_count += 1;
}
```

## Recommendations

1. **Investigate Phase 10/LiveResult**: Why does the game get stuck repeatedly selecting Choice 0?
2. **Check PendingInteraction.actions**: Verify this field doesn't accumulate unbounded data
3. **RPS Draw Handling**: Add a maximum draw count to prevent infinite RPS loops
4. **Logging Enhancement**: Add more detailed state logging when loops are detected
