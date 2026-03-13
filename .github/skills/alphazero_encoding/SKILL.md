## Architecture Distinction: MUST READ
There are two distinct AlphaZero encoding paths in this project. **Always confirm which one is being targeted.**

1.  **Vanilla AlphaZero (The "Simple" Path)**:
    - **Dimensions**: 800 floats (Global[20] + 60 Cards[13]).
    - **Purpose**: High-fidelity, low-complexity training for MLP/Transformer models.
    - **Rust Binding**: `game.to_vanilla_tensor()`
    - **Strategy**: Includes the **Portfolio Oracle** (RA-EV combinatorial search).

2.  **Relational AlphaZero (The "Deep" Path)**:
    - **Dimensions**: ~20,500 floats (Global[100] + 120 Entities[170]).
    - **Purpose**: Complex entity tracking and relational reasoning (Graph-like).
    - **Rust Binding**: `game.to_alphazero_tensor()`

> [!IMPORTANT]
> The **Portfolio Oracle** logic lives in the **Vanilla** path. Use `to_vanilla_tensor` when you want the AI to see synergistic "North Star" hints without the overhead of the massive relational vector.

## Overview
This encoding is designed for **Abilityless (Vanilla)** training. It augments the raw game state with a pre-computed "Portfolio Synergy Oracle" to help the AI optimize card selection and heart resource management.

## Input Tensor (800 Floats)
- **Global Features (20 floats)**:
    - `0-9`: Standard state (Phase, Turn, Scores, Hand/Energy/Yell counts).
    - `10-12`: Best 1, 2, and 3-card **Expected Value (Raw)** based on current hearts.
    - `13-15`: Best 1, 2, and 3-card **RA-EV** ($Score \times P^{1.5}$) for risk-aversion.
    - `16`: **Exhaustion Metric** (Heart requirement of the best trio / Total available hearts).
    - `17`: **Spare Capacity** (Remaining hearts after playing the best trio).
- **Card Features (60 * 13 floats)**:
    - Detailed per-card stats for 60 cards in the `initial_deck`.
    - **Feature 12 (Participation Bit)**: 1.0 if the card is part of the absolute best RA-EV portfolio.

### 1. Vanilla Architecture (800-dim)
- **Input**: 800 floats (20 global + 60 cards * 13 features).
- **Abilities**: **Strictly Abilityless**. This encoding ignores card bytecode and logic. It focuses on RAW stats (Hearts, Costs) and the Portfolio Oracle's RA-EV hints.
- **Goal**: Fast, "simple" training for base strategic competence and synergistic sequencing.
- **Oracle**: Includes risk-adjusted expected value (RA-EV) from combinatorial $\binom{12}{1} + \binom{12}{2} + \binom{12}{3}$ search.

## Strategic Guidelines
1. **The 220 Combinations**: The search iterates through all $\binom{12}{3}$ trios, plus pairs and singles, to find the global optimum from the 12 Live Cards in the deck.
2. **RA-EV Weighting**: The $P^{1.5}$ factor biases the "Oracle" toward safety. The AI uses this as a feature but can override it based on the game's termination rewards (learning to gamble when losing).
3. **Usage**:
    - **Binary**: `engine_rust::core::alphazero_encoding_vanilla`
    - **Net**: `alphazero/vanilla_net.py` (HighFidelityAlphaNet)

## Benchmarks
- **Overhead**: Negligible (<1%) compared to the 791 baseline.
- **Latency**: Sub-millisecond on modern CPUs due to small-vec optimizations in the combinatorial search.

## Blind Spots (Important)
The Portfolio Oracle is a **Strategic Ceiling** hint. It does NOT consider:
1. **Affordability**: Energy is for members, but space/timing still matters for Lives.
2. **Current Hand Only**: It scans the **Initial Deck (12 Lives)** to give the AI a "North Star". This teaches the AI to **Value and Hold** certain cards that are part of high-yield synergies, even if the other pieces are still in the deck.
3. **Non-Reversibility**: The cumulative heart math ($Subset \times P$) naturally profiles the best combination, allowing the AI to commit to a 1, 2, or 3-card play with maximum information.
