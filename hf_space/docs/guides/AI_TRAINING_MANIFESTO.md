# Love Live! OCG: AI Training Manifesto

## 1. The Methodology: "Parallel Curriculum PPO"
We are using **Proximal Policy Optimization (PPO)** with a **Masked Policy**.

### Why PPO?
*   **Stability**: It prevents the AI from changing its strategy too wildly (which causes "forgetting").
*   **Sample Efficiency**: It learns reasonably fast without needing Google-scale data centers.

### The Curriculum (The Lesson Plan)
1.  **Phase 1: Basic Math (Now)**
    *   **Deck**: Random "Vanilla" Decks (No complex abilities).
    *   **Goal**: Learn that `Pink Heart Card` -> `Pink Heart Live`.
    *   **opponent**: Random Agent.
2.  **Phase 2: Ability Discovery**
    *   **Deck**: Full Database Random Decks.
    *   **Goal**: Learn that `Draw Card` -> `More Options` -> `Win`.
3.  **Phase 3: Meta Evolution**
    *   **Opponent**: Previous version of Self.
    *   **Goal**: Find combos that beat "standard" play.

## 2. Infrastructure (Where everything lives)
*   **The Brain**: `checkpoints/` (Saved every 100k steps).
*   **The Logs**: `logs/ppo_tensorboard/` (Graphs of Win Rate).
*   **The Logic**: `engine/` (Python code).
*   **The Gym**: `ai/gym_env.py` (The training room).

## 3. How to Monitor
1.  **Terminal**: Watch the `ep_rew_mean` (Reward) and `fps` (Speed).
2.  **Visual**:
    ```powershell
    tensorboard --logdir logs/ppo_tensorboard/
    ```
    Then open `http://localhost:6006`.
