# Lovecasim Engine: logic.rs vs rules.txt Audit Report

## 📋 Overview
This audit compares the Rust game engine's core logic (`logic.rs`) against the official game rules (`rules.txt`). The goal is to ensure 100% compliance and identify potential logical errors or "bugs" in the implementation.

## ✅ Compliance Summary
The engine is remarkably compliant with the official rules. Key areas like Win Conditions, Phase Transitions, and Deck Construction meet the specs.

| Rule Category | Rule Reference | Status | Implementation Notes |
| :--- | :--- | :--- | :--- |
| **Win Conditions** | 1.2.1, 1.2.1.1 | Correct | `check_win_condition` correctly monitors successful lives. |
| **Zone Management** | 4.x | Correct | Stage, Live Zone, Hand, Discard, and Energy Zones are handled. |
| **Live Set Phase** | 8.2.2 | Correct | Allows any card to be set; non-live cards discarded later. |
| **Performance Phase** | 8.3 | Partially Correct | Correct flow, but lacks idempotency (see Issues). |
| **Baton Touch** | 12 | Correct | Cost reduction correctly subtracts old member cost. |
| **Deck Refresh** | 10.2.3 | Correct | Discard is shuffled and placed *under* the remaining deck. |

## ❌ Identified Issues

### 1. Performance Phase Idempotency (Critical)
The most significant issue is that `do_performance_phase` is not idempotent.
- **Problem**: In the Rust engine, the performance phase is a single function. If an ability triggers a pause (e.g., for user choice), the function returns and the game state enters `Phase::Response`. When the game resumes, it re-enters `do_performance_phase` from the beginning.
- **Impact**:
    - `OnReveal` and `OnLiveStart` triggers fire multiple times.
    - Statistics (Blades, Hearts) from "Yell" and bonuses accumulate redundantly.
    - This leads to "Stat Inflation" (e.g., a card giving +1 blade might end up giving +3 if there were multiple choices during the phase).
- **Rule Violation**: Rule 8.3 implies each step happens exactly once.

### 2. Yell Redundancy (Major)
- **Problem**: `do_yell` is called every time `do_performance_phase` is re-entered.
- **Impact**: Players draw additional cards every time the phase restarts, which is not allowed by Rule 8.3.11.

### 3. Energy Reclamation (Minor)
- **Rule 10.5.3**: "Energy in empty member area -> Energy Deck".
- **Implementation**: Currently shuffles the energy deck after pushback. While safe, the rules only specify "placed in energy deck", and since our energy deck is unordered (4.9.2), pushing and shuffling is correct but heavy on RNG.

### 4. Action ID Space Constraints
- **Problem**: "Play Member with Choice" (`1000+`) only supports the first 10 cards in hand. If a player has 11+ cards and plays the 11th card, it will use the standard `1+` action and pause for response, rather than allowing an atomic "Choose & Play" action.
- **Impact**: Slight UI/Agent inconsistency for large hands.

### 5. ID Range Collision
- **Problem**: `300-309` is used for both Mulligan toggles and `O_SELECT_MODE` in the Response phase.
- **Impact**: Safe because they are phase-exclusive, but risky for future interactive Mulligan triggers. Recommended to move `O_SELECT_MODE` to the `550+` (Generic) range.

## 🛠️ Recommendations

1. **Implement Sub-Phase Tracking**: Add a `performance_sub_state` to `GameState` to track progress. (Status: **Fixed in Engine**)
2. **State Guards**: Wrap triggers and card drawing in logic that checks the sub-phase state. (Status: **Fixed in Engine**)
3. **Trigger Queue Safety**: Ensure the trigger queue is fully processed before re-entering the performance check logic. (Status: **Fixed in Engine**)
4. **Action ID cleanup**: Unify all interactive choices into the `550+` range or a single dedicated high-range block to avoid phase-based collisions.

---
*Audit performed by Antigravity on 2026-02-07*
