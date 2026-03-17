# AI Training Optimization Roadmap

This document outlines potential strategies to further accelerate training throughput, focusing on optimizations that require significant refactoring or architectural changes.

## 1. GPU-Resident Environment (The "Isaac Gym" Approach)
**Impact:** High (Potential 5-10x speedup for large batches)
**Difficulty:** High

Currently, the `VectorEnv` runs on CPU (Numba), and observations are copied to the GPU for the Policy Network. This CPU -> GPU transfer becomes a bottleneck at high throughputs (e.g., >100k SPS).

*   **Proposal:** Port the entire logic in `ai/vector_env.py` and `engine/game/fast_logic.py` to **Numba CUDA** or **CuPy**.
*   **Result:** The environment state remains on the GPU. `step()` returns a GPU tensor directly, which is fed into the Policy Network without transfer.
*   **Challenges:** requires rewriting Numba CPU kernels to Numba CUDA kernels (handling thread divergence, shared memory, etc.).
*   **Status:** [FEASIBILITY ANALYSIS COMPLETE]. See `ai/GPU_MIGRATION_GUIDE.md` and `ai/cuda_proof_of_concept.py` for the architectural blueprint.

## 2. Pure Numba Adapter & Zero-Copy Interface
**Impact:** Medium (10-20% speedup)
**Difficulty:** Medium

The `VectorEnvAdapter` currently performs some Python-level logic in `step_wait` (reward calculation, array copying, info dictionary construction).

*   **Proposal:** Move the reward calculation (`delta_scores * 50 - 5`) and "Auto-Reset" logic into the Numba `VectorGameState` class.
*   **Result:** `step_wait` becomes a thin wrapper that just returns views of the underlying Numba arrays.
*   **Refinement:** Use the `__array_interface__` or blind pointer passing to avoid any numpy array allocation overhead in Python.

## 3. Observation Compression & Quantization
**Impact:** Medium (Reduced memory bandwidth, larger batch sizes)
**Difficulty:** Low/Medium

The observation space is 8192 floats (`float32`). This is 32KB per environment per step. For 256 envs, that's 8MB per step.

*   **Proposal:** Most features are binary (0/1) or small integers.
    *   Return observations as `uint8` or `float16`.
    *   Use a custom SB3 `FeaturesExtractor` to cast to `float32` only *inside* the GPU network.
*   **Benefit:** Reduces memory bandwidth between CPU and GPU by 4x (`float32` -> `uint8`).

## 4. Incremental Action Masking
**Impact:** Low/Medium
**Difficulty:** Medium

`compute_action_masks` scans the entire hand every step.

*   **Proposal:** Maintain the action mask as part of the persistent state.
    *   Only update the mask when the state changes (e.g., Card Played, Energy Charged).
    *   Most steps (e.g., Opponent Turn simulation) might not change the Agent's legal actions if the Agent is waiting? (Actually, Agent acts every step in this setup).
    *   Optimization: If a card was illegal last step and state hasn't changed relevantly (e.g. energy), it's still illegal. This is hard to prove correct.

## 5. Opponent Distillation / Caching
**Impact:** Medium (Depends on Opponent Complexity)
**Difficulty:** High

If we move to smarter opponents (e.g., MCTS or Neural Net based), `step_opponent_vectorized` will become the bottleneck.

*   **Proposal:**
    *   **Distillation:** Train a tiny decision tree or small MLP to mimic the smart opponent and run it via Numba inference.
    *   **Caching:** Pre-calculate opponent moves for common states? (Input space too large).

## 6. Asynchronous Environment Stepping (Pipelining)
**Impact:** Medium
**Difficulty:** Medium

While the GPU is performing the Forward/Backward pass (Policy Update), the CPU is idle.

*   **Proposal:** Run `VectorEnv.step()` in a separate thread/process while the GPU trains on the *previous* batch.
*   **Note:** SB3's `SubprocVecEnv` tries this, but IPC overhead kills it. We need a **Threaded** Numba environment (releasing GIL) to do this efficiently in one process. Numba's `@njit(nogil=True)` enables this.

## 7. Memory Layout Optimization (AoS vs SoA)
**Impact:** Low/Medium
**Difficulty:** High (Refactor hell)

Current layout mixes Structure of Arrays (SoA) and Arrays of Structures (AoS).

*   **Proposal:** Ensure all hot arrays (`batch_global_ctx`, `batch_scores`) are contiguous in memory for the exact access pattern used by `step_vectorized`.
*   **Check:** Access `batch_global_ctx[i, :]` vs `batch_global_ctx[:, k]`. Numba prefers loop-invariant access.
