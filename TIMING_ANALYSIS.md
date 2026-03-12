# Timing Analysis: Why Games Take Longer Than Sequence Counts Suggest

## The User's Observation
- Sequence counts are small: 46, 136, 82, 4, 1 sequences
- These resolve in 0.000-0.009 seconds
- "This should mean games are instant right?"

## The Discrepancy Explained

### Part 1: Sequence ENUMERATION vs EXECUTION

**Sequence Enumeration (counting):**
```
- 46 sequences counted in 0.000s ✓
- 136 sequences counted in 0.001s ✓
- 82 sequences counted in 0.009s ✓
```

**Full Turn EXECUTION (enumeration + moves + LiveSet + ability resolution + auto-step):**
```
Random moves game results:
- Turn 1:  22 seqs → 1ms total
- Turn 2: 136 seqs → 150ms total (!!)
- Turn 3:  39 seqs → 118ms total
- Turn 10: 222 seqs → 113ms total
- Turn 11: 82 seqs → 118ms total
- Turn 16: 66 seqs → 66ms total
- Turn 20: 1 seq  → 0ms total
```

**Average across full game:**
- 20 Main turns with random moves: **0.738 seconds total**
- Per-turn average: **36.2ms per turn**

### Part 2: Where The Time Really Goes

Per-turn breakdown for early game (Turn 2):
```
Sequence enumeration:  0.001s
Main phase execution:  0.001s
LiveSet selection:     0.0s
Ability triggering:    ~0.15s  ← THE BOTTLENECK
Auto-step phases:      0.0s
────────────────────────────
Turn total:            0.15s (150ms)
```

**The hidden costs:**
1. **Ability triggering** (OnPlay, OnLeaves, TurnStart, TurnEnd) is very expensive
   - Each state.step() can trigger 5-10+ ability calls
   - Each ability check must evaluate board state
2. **State cloning** overhead in exact sequence enumeration
   - Each branch of the tree requires cloning the game state
   - Cloning includes All card objects, their states, zones, etc.
3. **Board complexity** increases mid-game
   - More cards on field = more ability triggers
   - More live cards = more complex LiveSet calculations

### Part 3: Comparison with Planned-Move Game

**Planned moves game** (with DFS search):
- 18 turns in 2.93 seconds 
- Per-turn: ~163ms average
- BUT the game ended faster (18 vs 20 turns of random)

**Why is planned slower per-turn despite fewer total turns?**
- DFS search adds significant overhead (board evaluation, alpha-beta pruning)
- BUT better moves lead to earlier game termination (fewer total turns)
- Net result: Sometimes faster overall despite slower individual turns

### Part 4: The "best_val always -inf" Issue

This is concerning. If the best value is always negative infinity, it suggests:
1. The evaluation function might be broken
2. The search might be returning invalid values
3. The board state might be malformed during searches

**This needs investigation - it could explain why games aren't playing well.**

## Summary

| Metric | Random Moves | Planned Moves |
|--------|--------------|---------------|
| Sequence enumeration time | 0.001-0.056s per turn | 0.001-0.213s per turn |
| Total game time (20ish turns) | 0.74s | 2.93s |
| Per-turn average | 36ms | 163ms |
| Bottleneck | Ability triggering + board complexity | DFS search evaluation + ability triggering |

## Conclusion

**YES, sequence enumeration is very fast (0.000-0.001s), but game turns are NOT instant because:**

1. **Enumeration is just counting** - doesn't include executing the moves
2. **Execution requires ability triggering** - which is the real cost
3. **Board complexity grows** - early turns are 1-5ms, late turns can be 100-150ms
4. **State cloning** in the exact sequencer adds overhead

**A 20-turn game with random moves takes ~0.74s, which is reasonable.** The issue isn't speed - it's that `best_val` is always -inf, which suggests the DFS evaluation or board scoring is broken.

### Recommendation

Focus on fixing:
1. Why `best_val` returns -inf
2. Whether the board evaluation function is working correctly
3. Whether the planned moves are actually better than random

The speed IS fine now - the issue is the game quality.
