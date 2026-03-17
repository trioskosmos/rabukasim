# Lovecasim Deep Strategy: How to Win

To achieve consistent sub-20 turn wins, the AI (and player) must move beyond simple card play into **Resource Scaling** and **Tempo Management**.

## 1. The Energy Engine (Resource Scaling)
Common Misconception: "Energy resets every turn."
*   **The Reality**: Your **unspent capacity** (tapped status) resets, but your **Energy Zone** persists.
*   **The Growth**: You add 1 card from your Energy Deck to your Energy Zone every turn.
*   **The Strategy**: By Turn 5, you have a 5-card capacity. Do not treat energy as a "refillable pool" relative to counts, but as a **growing reservoir**.
*   **Priority**: Commit cards with "Charge" abilities early to accelerate this curve.

## 2. Baton Pass (Tempo Management)
The most misunderstood mechanic in Lovecasim. It is your primary tool for playing high-cost members early.
*   **Mechanic**: Playing a member into an occupied slot replaces the old member.
*   **The Benefit**: The cost of the new member is reduced by the **entire cost** of the member being replaced.
*   **The Math**:
    - Playing a 9-cost member on an empty stage = **9 Energy**.
    - Playing a 2-cost member first, then "Baton Passing" into a 9-cost member = **2 Energy + 7 Energy**.
*   **Strategy**: Use low-cost members (Cost 1-3) as "stepping stones" for your heavy hitters (Cost 6-9). Never leave a 9-cost card in hand waiting for turn 9; Baton Pass it on turn 4-5.

## 3. Stage Hearts vs. Yell Hearts (Certainty)
*   **Stage Hearts**: Fixed, guaranteed, and reliable.
*   **Yell Hearts**: Probabilistic and risky.
*   **The Rule of 3**: You only have 3 stage slots. Every empty slot is a massive loss of "Guaranteed Hearts."
*   **The 18-Turn Threshold**: To win by Turn 18, you must have at least one slot consistently occupied and performing by Turn 3.

## 4. The Win Condition (Success Management)
*   **Matching Colors**: Don't just play high stats. Play colors that match your specific Live cards.
*   **Success Proximity**: If you need 4 Pink hearts and 2 Blue, and you have 3 Pink and 2 Blue, you are at **80% Proximity**. The AI should value this state nearly as much as a win, as a single Yell can bridge the gap.

## 5. Optimal Heuristic Weights for AI
To reinforce this strategy, the AI uses these optimized weights:
| Element | Weight | Strategic Rationale |
| :--- | :--- | :--- |
| **Occupied Stage Slot** | +1.0 | Eliminates empty-slot inefficiency. |
| **Stage Blade** | +1.5 | Drives Yell volume and probability. |
| **Stage Heart** | +0.5 | Direct progress toward Live Success. |
| **Tapped Energy** | +0.2 | Incentivizes spending over passing. |
| **Energy Pool Size** | +0.5 | Encourages building the reservoir early. |
| **Turn Penalty** | -0.5 | Backwards optimization for speed. |
| **Graveyard Depth** | +0.1 | Populates recovery targets for searchers. |
| **Live Consistency**| +0.8 | Penalizes "Impossible" Live cards in hand. |

## 6. The Graveyard as a "Side Deck"
Advanced players treat the discard pile (控え室) not as lost cards, but as a secondary card pool.
*   **Milling**: Intentionally discarding from the deck (e.g., via Search or DRAW/DISCARD effects).
*   **The Goal**: Populate the discard with high-cost utility members (Charge, Buff) that can be retrieved by **Recover** (手札に加える) or **Reanimate** (ステージに置く) abilities.
*   **AI Heuristic**: The AI should value a non-empty graveyard if it holds cards with `FLAG_RECOVER`.

## 7. Aggressive Filtering (The Art of Letting Go)
Holding a Live card that requires 10 hearts of a color you have 0 of is a trap.
*   **Live Discard**: Use abilities that allow discarding cards to filter out these "dead draws."
*   **Milling for Speed**: Milling through the deck (Deck Velocity) allows you to find your easier-to-clear Live cards faster.
*   **Strategic Discard**: If you have two Live cards in hand, keep the one that matches your current stage power and discard the one that doesn't.
