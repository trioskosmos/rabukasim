# MCTS Performance Principles: Heuristics vs. Combinatorics

In the development of the LovecaSim AI, a critical design decision was made to prioritize **Expected Value (EV)** over **Exact Combinatorics** for performance probability solving within the MCTS loop.

## The Problem: Hypergeometric Explosion
Calculating the exact probability of drawing a specific set of colored hearts from a deck without replacement follows a **Multivariate Hypergeometric Distribution**.

1. **Complexity**: Standard hypergeometric formulas require factorials. For $C$ colors, the complexity scales with $O(K^C)$.
2. **Wildcards**: The presence of Special/Star hearts adds a another layer of complexity, requiring a search tree of all possible "coverage" scenarios.
3. **Blades**: Yell multipliers (Blades) cluster successes, breaking the "one draw = one success" assumption of standard probability distributions.

## The Solution: Linear Heuristics (EV)
Instead of calculating the exact probability, the engine calculates the **Expected Yield** per color and applies a variance-aware heuristic.

### The Algorithm
1. **Linear Scan**: $O(N)$ pass through the deck to find the ratio of each color.
2. **Expected Hearts**: $\text{Expected}_c = \frac{\text{Count}_c}{N} \times K \times (1 + \text{Blades})$.
3. **Deficit Evaluation**: Compare Stage Deficit vs. Expected Yield.
4. **Soft Gradient**: 
   - If $\text{Yield} < \text{Deficit}$: Return a quadratic decay score (AI senses failure).
   - If $\text{Yield} \gg \text{Deficit}$: Return $\sim 99\%$ (AI senses security).

## Why this is "the play" for AlphaZero
- **Differentiability**: Heuristics provide a smooth gradient. A neural network can "feel" the probability improving as it plays more members, even before it reaches the 100% threshold.
- **Search Depth**: By saving milliseconds on math, the MCTS can explore thousands of more nodes, which usually leads to a much stronger AI than one with slightly more accurate "local" math but shallower search.
- **Verification**: The `explain_solver.rs` tool (located in `src/bin/`) serves as the validation layer to ensure the heuristic remains grounded in real deck data.
