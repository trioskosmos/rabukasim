# Python-Rust Engine Parity Guide

## Overview
This document explains how to maintain logic parity between the Python engine (`engine/game/`) and the Rust engine (`engine_rust/src/core/`). The Rust engine is a high-performance port intended for AI training, so it must produce identical game states given identical inputs.

## Testing Framework

### Running Parity Tests
```bash
# Build Rust engine in release mode
cd engine_rust && cargo build --release

# Copy to Python-loadable location
Copy-Item -Path 'target\release\lovecasim_engine.dll' -Destination '..\lovecasim_engine.pyd' -Force

# Run parity comparison
cd .. && uv run python compare_logic.py

# Check results
cat parity_log.txt
```

## Phase Reference: Legal Actions & Auto-Skip Behavior

| Phase | Value | Legal Action IDs | Auto-Skip? | Notes |
|-------|-------|------------------|------------|-------|
| `MULLIGAN_P1` | -1 | `0` (keep), `300-359` (select cards to mulligan) | No | Bitmask action for card selection |
| `MULLIGAN_P2` | 0 | Same as P1 | No | After P2, chains to Active->Energy->Draw->Main |
| `ACTIVE` | 1 | `0` (any) | **YES** | Untaps all, immediately advances to ENERGY |
| `ENERGY` | 2 | `0` (any) | **YES** | Draws 1 energy, immediately advances to DRAW |
| `DRAW` | 3 | `0` (any) | **YES** | Draws 1 card, immediately advances to MAIN |
| `MAIN` | 4 | `0` (end), `1-180` (play member), `200-399` (ability) | No | Player decision phase |
| `LIVE_SET` | 5 | `0` (end), `400-459` (set live from hand) | No | Both players take turns |
| `PERFORMANCE_P1` | 6 | `0` (auto), `900-902` (select live) | No | First player performs |
| `PERFORMANCE_P2` | 7 | Same as P1 | No | Second player performs |
| `LIVE_RESULT` | 8 | `0` (continue) | No | Scoring, then chains to next turn's Active |
| `TERMINAL` | 9 | None | N/A | Game over |

### Action ID Ranges
```
0          = Skip / End Phase / Continue
1-180      = Play member (hand_idx * 3 + stage_slot)
200-399    = Activate ability (member_idx * 10 + ability_idx)
300-359    = Mulligan card selection
400-459    = Set live card from hand
500-599    = Choice responses (color select, etc.)
580-585    = Color select (Pink, Red, Yellow, Green, Blue, Purple)
600-699    = Target selection (opponent slots, etc.)
900-902    = Select specific live to perform
```

### Auto-Chain Behavior
When Python's `step()` is called:
1. **Active/Energy/Draw** phases execute immediately and chain to the next
2. After `LiveResult` action 0, `_finish_live_result()` is called which:
   - Increments turn
   - Alternates `first_player`
   - Chains through Active->Energy->Draw->Main

Rust must replicate this exact chaining behavior for parity.


### Issue 1: Attribute Name Mismatch
**Symptom**: Python hand size doesn't increase during Draw phase

**Root Cause**: Python's `PlayerState` uses `main_deck`, but test script set `deck`

**Fix**:
```python
# WRONG
p_p.deck = [parity_m_id] * 42

# CORRECT
p_p.main_deck = [parity_m_id] * 42
```

**Pitfall**: Always check the actual attribute names in `player_state.py`. The naming convention isn't always intuitive.

---

### Issue 2: Two-Player Phase Flow (LiveSet)
**Symptom**: Phase mismatch after LiveSet - Rust at Performance, Python still at LiveSet

**Root Cause**: Python's `_end_live_set()` alternates between players:
1. First player finishes → switch to second player (stay in LiveSet)
2. Second player finishes → advance to Performance

Rust originally jumped directly to Performance on any action 0.

**Fix** (logic.rs):
```rust
Phase::LiveSet => {
    if action == 0 {
        if self.current_player == self.first_player {
            // First player done -> switch to second
            self.current_player = 1 - self.first_player;
        } else {
            // Both done -> advance
            self.phase = Phase::PerformanceP1;
            self.current_player = self.first_player;
        }
    }
}
```

**Pitfall**: Many phases in this TCG involve **both players acting** before advancing. Always check if Python alternates players within a single phase.

---

### Issue 3: Legal Action Sets
**Symptom**: "DIVERGENCE! No common actions" error

**Root Cause**: Rust's `get_legal_actions` didn't include action 0 for Performance phase

**Fix**: Add `mask[0] = true` to Performance phase legal actions

**Pitfall**: Python often allows action 0 as a "skip/pass/default" even when it's not semantically meaningful. Rust should mirror this for parity.

---

### Issue 4: Auto-Advance vs Wait-For-Step
**Symptom**: One engine draws cards one step earlier than the other

**Root Cause**: Rust's LiveResult handler called `do_active_phase()` immediately after setting phase to Active. Python's `_finish_live_result()` only sets the phase and waits for the next `step()` call.

**Fix**: Remove auto-advance from Rust

**Pitfall**: Decide on a consistent philosophy:
- **"Step Granularity"**: Each `step()` call should represent ONE player decision point
- Both engines should wait at the same "decision gates"
- Deterministic phases (Active/Energy/Draw) should either BOTH auto-chain or BOTH wait

---

## Common Pitfalls Reference

| Category | Python | Rust | Notes |
|----------|--------|------|-------|
| Deck attribute | `main_deck` | `deck` | Different names! |
| Phase enum values | `Phase.MAIN = 4` | `Phase::Main = 4` | Usually match, verify |
| RNG | `random.shuffle()` | `Pcg64` | Will NOT match, use uniform data |
| Player switching | Complex conditions | Must replicate exactly | Check each phase handler |
| Auto-advance | Minimal | Must disable | Rust tends to auto-chain |

---

## Adding New Features (Parity Checklist)

When implementing new game logic in either engine:

1. **Identify the Python reference implementation**
   - Find the method in `action_mixin.py` or `phase_mixin.py`
   - Note exact conditions for phase transitions
   - Note player switching logic

2. **Implement in Rust with matching structure**
   - Keep control flow identical
   - Use same action ID ranges
   - Match legal action generation

3. **Update `get_legal_actions` in both**
   - Ensure same action IDs are valid in each phase
   - Check for "safety" actions (0, skip, cancel)

4. **Test with `compare_logic.py`**
   - Add more steps if testing later phases
   - Add phase-specific assertions if needed

5. **Document any intentional differences**
   - Performance optimizations (auto-skipping deterministic phases)
   - Missing features (not blocking parity tests)

---

## Current Parity Status: ✅ VERIFIED

All 20 test steps completed with **perfect parity**:
- Phases match at every step
- Hand sizes match at every step
- Turn numbers match
- Current player matches
- Energy zones match

| Phase | Status | Notes |
|-------|--------|-------|
| Mulligan P1/P2 | ✅ | Action 0 = keep hand |
| Active | ✅ | Auto-chains to Energy |
| Energy | ✅ | Auto-chains to Draw |
| Draw | ✅ | Auto-chains to Main |
| Main | ✅ | Both players take turns |
| LiveSet | ✅ | Two-player alternation fixed |
| Performance P1/P2 | ✅ | Order based on first_player |
| LiveResult | ✅ | Chains to next turn's Active |


---

## Files Reference

| Purpose | Python | Rust |
|---------|--------|------|
| Game State | `engine/game/game_state.py` | `engine_rust/src/core/logic.rs` |
| Actions | `engine/game/mixins/action_mixin.py` | `logic.rs::step()` |
| Phases | `engine/game/mixins/phase_mixin.py` | `logic.rs::do_*_phase()` |
| Legal Actions | `engine/game/mixins/action_mixin.py::get_legal_actions` | `logic.rs::get_legal_actions()` |
| Player State | `engine/game/player_state.py` | `engine_rust/src/core/player.rs` |
| Bindings | N/A | `engine_rust/src/py_bindings.rs` |
