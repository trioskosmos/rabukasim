# GPU Environment Training Integration Guide

This guide explains how to integrate the new `VectorEnvGPU` into the existing training pipeline (`train_optimized.py`) to achieve production-level performance.

## 1. Replacing the Environment Wrapper

Currently, `train_optimized.py` uses `BatchedSubprocVecEnv` which manages multiple CPU processes. The GPU environment is a single object that manages thousands of environments internally.

### Steps:

1.  **Import `VectorEnvGPU`**:
    ```python
    from ai.vector_env_gpu import VectorEnvGPU, HAS_CUDA
    ```

2.  **Conditional Initialization**:
    In `train()` function, replace the `BatchedSubprocVecEnv` block:

    ```python
    if HAS_CUDA and os.getenv("USE_GPU_ENV") == "1":
        print(" [GPU] Initializing GPU-Resident Environment...")
        # num_envs should be large (e.g., 4096) to saturate GPU
        env = VectorEnvGPU(num_envs=4096, seed=42)

        # VectorEnvGPU doesn't need a VecEnv wrapper usually,
        # but SB3 expects specific API. We might need a thin adapter.
        env = SB3CudaAdapter(env)
    else:
        # Existing CPU Logic
        env_fns = [...]
        env = BatchedSubprocVecEnv(...)
    ```

## 2. The `SB3CudaAdapter`

Stable Baselines 3 expects numpy arrays on CPU by default. To fully utilize the GPU env, we must intercept the data *before* SB3 tries to convert it, or use a custom Policy that accepts Torch tensors directly.

However, `MaskablePPO` in `sb3_contrib` might try to cast inputs to numpy.

**Strategy: Zero-Copy Torch Wrapper**

```python
import torch
from gymnasium import spaces

class SB3CudaAdapter:
    def __init__(self, gpu_env):
        self.env = gpu_env
        self.num_envs = gpu_env.num_envs
        # Define spaces (Mocking them for SB3)
        self.observation_space = spaces.Box(low=0, high=1, shape=(8192,), dtype=np.float32)
        self.action_space = spaces.Discrete(2000)

    def reset(self):
        # returns torch tensor on GPU
        obs, _ = self.env.reset()
        return torch.as_tensor(obs, device='cuda')

    def step(self, actions):
        # actions come from Policy (Torch Tensor on GPU)
        # Pass directly to env
        obs, rewards, dones, infos = self.env.step(actions)

        # Wrap outputs in Torch Tensors (Zero Copy)
        # obs is already CuPy/DeviceArray
        t_obs = torch.as_tensor(obs, device='cuda')
        t_rewards = torch.as_tensor(rewards, device='cuda')
        t_dones = torch.as_tensor(dones, device='cuda')

        return t_obs, t_rewards, t_dones, infos
```

## 3. PPO Policy Modifications

Standard SB3 algorithms often force `cpu()` calls. For maximum speed, you might need to subclass `MaskablePPO` or `MlpPolicy` to ensure it accepts GPU tensors without moving them.

*   **Check `rollout_buffer.py`**: SB3's rollout buffer stores data in CPU RAM by default.
*   **Optimization**: For "Isaac Gym" style training, the Rollout Buffer should live on the GPU.
    *   *Option A*: Use `sb3`'s `DictRolloutBuffer`? No, standard buffer.
    *   *Option B*: Modify SB3 or use a library designed for GPU-only training like `skrl` or `cleanrl`.
    *   *Option C (Easiest)*: Accept that `collect_rollouts` might do one copy to CPU RAM for storage, but the **Inference** (Forward Pass) stays on GPU.

## 4. Remaining Logic Gaps

The current `VectorEnvGPU` POC has simplified logic in `resolve_bytecode_device`. Before production:

1.  **Complete Opcode Support**: `O_CHARGE`, `O_CHOOSE`, `O_ADD_H` need full card movement logic (finding indices, updating arrays).
2.  **Opponent Simulation**: `step_kernel` currently simulates a random opponent. The `step_opponent_vectorized` logic from CPU env needs to be ported to a CUDA kernel.
3.  **Collision Handling**: In `resolve_bytecode_device`, we use `atomic` operations or careful logic if multiple effects try to modify the same global state (rare in this game, but `batch_global_ctx` is per-env so it's safe).

## 5. Performance Expectations

*   **Current CPU**: ~10k SPS (128 envs).
*   **Target GPU**: ~100k-500k SPS (4096+ envs).
*   **Bottleneck**: Will shift from "PCI-E Transfer" to "Policy Network Forward Pass".
