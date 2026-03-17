# Loveca AI Technical Specification

## 1. Neural Architecture: MLP vs. Transformer

For specialized domain problems like Tabletop Card Games (TCGs), the choice between Multilayer Perceptrons (MLP) and Transformers is a trade-off between **Data Representation** and **Inference Latency**.

### Why MLP (Multi-Layer Perceptron) Wins Here
We are using a **Dense MLP Policy** (likely `[512, 512, 512]` hidden units).

1.  **Fixed Observation Space**:
    *   Unlike natural language (where sentences vary in length), our game state is perfectly encodable into a fixed-size vector (tensor) of floats.
    *   We have exactly 3 Stage Slots, 12 Energy Slots, and a finite Hand Size.
    *   A simple MLP can learn "Slot 2 + Hand Card 4 = High Reward" efficiently because "Slot 2" is always at input index `N`. Transformers excel when "Slot 2" could be anywhere in the sequence, which is not the case here.

2.  **Inference Speed (FPS)**:
    *   **MLP**: Extremely fast matrix multiplication. Ideal for AlphaZero-style self-play where you need millions of games. On your RTX 3050 Ti, an MLP can execute in microseconds.
    *   **Transformer**: Relies on Self-Attention mechanisms ($O(n^2)$ complexity). For a game state of ~256 tokens, this calculative overhead is massive per-step. In Reinforcement Learning, **Inference Speed = Training Speed**. If the model is 10x slower to think, you train 10x slower.

3.  **Sample Efficiency**:
    *   Transformers are "data hungry." They need massive datasets to converge. MLPs converge much faster on smaller, cleaner state representations like our game board.

### When would we use a Transformer?
If we were training an AI to read the **raw text** of cards it had never seen before (Zero-Shot Learning), we would need a Transformer (LLM) to "understand" the text. But here, we have successfully compiled the cards into **Opcodes (Integers)**. Since the input is structured math, the MLP is mathematically superior for the task.

---

## 2. Infrastructure & Reliability

### Logging Locations
*   **TensorBoard Logs**: `C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/logs/ppo_tensorboard/`
    *   Contains binary event files (`events.out.tfevents...`).
    *   **Metrics**: `rollout/ep_rew_mean` (Average Win Rate), `train/loss` (Network Error), `train/fps` (Speed).
*   **Terminal Output**: Real-time stats printed to stdout.

### Crash Recovery: "What if the computer crashes?"
We use **Stable Baselines3**, which has built-in serialization.

1.  **The Checkpoints**:
    *   **Location**: `C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/checkpoints/`
    *   **Frequency**: The script saves a `.zip` file periodically (e.g., `model_500000_steps.zip`).
    *   **Content**: These zip files contain the full PyTorch state dictionary (neural weights) and the optimizer state.

2.  **Recovery Procedure**:
    *   If power fails at step 740,000, you simply load the `700_000_steps.zip` file.
    *   You lose at most the progress since the last save (e.g., ~15-30 mins of training).
    *   **To Resume**: Modify the script to `model = MaskablePPO.load("checkpoints/model_700k")` and call `model.learn()` again. It continues exactly where it left off.

## 3. Summary
*   **Architecture**: Dense MLP (Fast, Efficient for fixed-state games).
*   **Safety**: Periodic `.zip` snapshots ensure mostly zero data loss on crash.
*   **Hardware**: The architecture is tuned to saturate the 12 CPU cores (Environment) and feed the GPU (MLP) in 512-batch chunks for maximum throughput.
