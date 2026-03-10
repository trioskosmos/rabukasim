# AlphaZero Heuristic & Search Strategy Analysis

## 1. What is the current `OriginalHeuristic` doing?
The current `OriginalHeuristic` is a highly-tuned, monolithic linear evaluation function. It scores the board without lookahead by looking at:
- **Success Lives**: High base points + bonus for clearing.
- **Stage Presence**: Sums the "member cost" and assigns raw points for specific abilities (e.g., `FLAG_CHARGE`, `FLAG_DRAW`, center-slot synergy).
- **Proximity Math**: It uses `process_hearts` and `calculate_live_success_prob` to calculate the mathematical probability of clearing a Live card based on stage colors and the mathematical average of colors remaining in the deck. The score spikes exponentially as the probability approaches 1.0 (100%).
- **Constraints**: It penalizes holding impossible Lives and rewards an empty/milled discard pile (if a recovery card is in hand).

### Flaws & Limitations
While fast, it evaluates linearly. It says "You have 3 Red Hearts and 1 Blue Heart, so you get 400 points." It completely misses combinatorial synergies—like the fact that playing Card A allows you to trigger Card B which draws Card C. It cannot see the "shape" of the Yell step, only the mathematical averages.

---

## 2. Depth vs. Breadth (Search Horizon & RNG Noise)

**Your insight is 100% correct**: Going past the end of the turn in this game is generally harmful to MCTS quality.

1. **The RNG Noise Problem**: LovecaSim is highly non-deterministic. Every time a card attacks/performs, a random Yell card is drawn. If MCTS searches 10 turns deep (which it currently does because it hits depth 55!), it is projecting through dozens of random draws. The UCB1 value at the root node gets "washed out" by chaotic futures that are highly unlikely to actually happen.
2. **Current Horizon Bug**: I examined `mcts.rs`. The `SearchHorizon::TurnEnd()` limit is currently **only applied to Rollouts**. Because rollouts are disabled in favor of terminal evaluation, MCTS continues expanding the tree *infinitely deep* across multiple simulated turns until the 0.5s timeout is reached.
3. **The Solution**: We need to enforce `SearchHorizon::TurnEnd()` at the **Expansion** phase. If a node transitions from `Phase::End` to `Phase::Start` (i.e., the turn ticks over), that node should be marked as "Terminal for this Search" and immediately evaluated by the heuristic. This will force the 30,000 sims/sec to spread **horizontally** (extreme breadth) exploring every single micro-variation of the *current* turn to guarantee optimal play, completely eliminating future-turn RNG noise.

---

## 3. Are we ready for the Neural Network?

**Yes. Absolutely.**

The simulation engine is no longer the bottleneck. The engine can step the game state at **~630,000 steps/s** (multi-threaded) and **~139,000 steps/s** (single-threaded).
Right now, the MCTS logic (the physical act of building the tree in RAM) takes 90% of the time, while the heuristic takes <5%.

### The Transition Plan
We have the `GpuManager` architecture stubbed out in `mcts.rs` (lines 463-479). The plan to transition from the linear `OriginalHeuristic` to the Transformer/Neural Net is:

1. **Cap Depth**: Enforce `SearchHorizon::TurnEnd` during expansion to force a wide, shallow tree optimized for tactical turn-solving.
2. **State Encoding**: Implement `GameStateEncoding` (flattening the game state into a fixed-size `[f32; N]` tensor array).
3. **GPU Batching**: MCTS already collects simulation leaf nodes into `gpu_batch`. Instead of calling `eval_fn`, we blast a batch of 512 state tensors to Python via PyO3, run an ONNX/Torch inference, and return the 512 Value/Policy floats back to Rust for backpropagation.
4. **Bootstrap Training**: We can use the current `OriginalHeuristic` as the "Teacher" to generate millions of self-play games to train the "Student" Neural Network from scratch.
