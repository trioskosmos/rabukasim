# GPU Migration Guide: Moving VectorEnv to Numba CUDA

## 1. The Core Question: "Aren't we already using Numba?"

Yes, the current `VectorEnv` uses **Numba CPU (`@njit`)**. While Numba is famous for compiling Python to machine code, it has two distinct backends:

1.  **CPU Backend (`@njit`)**: Compiles to x86/AVX/ARM assembly. Uses OpenMP (`parallel=True`) for multi-threading. Data usually lives in standard RAM (Numpy arrays).
2.  **CUDA Backend (`@cuda.jit`)**: Compiles to PTX (NVidia GPU assembly). Runs on the GPU. Data **must** live in VRAM (Device Arrays).

**The bottleneck today** is not the execution speed of the logic itself, but the **PCI-E Bus**.
*   **Current Flow**: `CPU Logic` -> `CPU RAM` -> `PCI-E Copy` -> `GPU VRAM (Policy Net)` -> `PCI-E Copy` -> `CPU RAM` -> ...
*   **Target Flow (Isaac Gym Style)**: `GPU Logic` -> `GPU VRAM` -> `Policy Net` -> `GPU VRAM` -> ...

Porting to Numba CUDA eliminates the PCI-E transfer, potentially unlocking 100k+ steps per second for massive batches.

## 2. Architecture Comparison

### Current (CPU Parallel)
```python
@njit(parallel=True)
def step_vectorized(...):
    for i in prange(num_envs):  # CPU Threads
        # Process Env i
```
*   **Memory**: Host RAM (Numpy).
*   **Parallelism**: ~16-64 threads (CPU Cores).
*   **Observation**: Generated on CPU, copied to GPU.

### Proposed (GPU Massive Parallel)
```python
@cuda.jit
def step_kernel(...):
    i = cuda.grid(1)  # GPU Thread ID
    if i < num_envs:
        # Process Env i
```
*   **Memory**: Device VRAM (CuPy / Numba DeviceArray).
*   **Parallelism**: ~10,000+ threads.
*   **Observation**: Stays on VRAM. Passed to PyTorch via `__cuda_array_interface__`.

## 3. Implementation Challenges & Solutions

### A. Memory Management (The "Zero Copy" Goal)
You cannot pass standard Numpy arrays to `@cuda.jit` kernels efficiently without triggering a transfer.
*   **Solution**: Use `cupy` arrays or `numba.cuda.device_array` for the master state (`batch_stage`, `batch_hand`, etc.).
*   **PyTorch Integration**: PyTorch can wrap these arrays zero-copy using `torch.as_tensor(cupy_array)` or `torch.utils.dlpack.from_dlpack`.

### B. The "Warp Divergence" Problem
GPUs execute instructions in "Warps" (groups of 32 threads). If Thread 1 executes `if A:` and Thread 2 executes `else B:`, **both** threads execute **both** paths (masking out the inactive one).
*   **Risk**: The `resolve_bytecode` VM is a giant switch-case loop. If Env 1 runs Opcode 10 (Draw) and Env 2 runs Opcode 20 (Attack), they diverge.
*   **Mitigation**: The high throughput of GPUs (thousands of cores) usually overcomes this inefficiency. Even at 10% efficiency due to divergence, a 4090 GPU (16k cores) might beat a 32-core CPU.
*   **Advanced Fix**: Sort environments by "Next Opcode" before execution (sorting on GPU is fast). This ensures threads in a warp execute the same instruction. (Complex to implement).

### C. Random Numbers
`np.random` does not work in CUDA kernels.
*   **Solution**: Use `numba.cuda.random.xoroshiro128p`.
*   **Requirement**: You must initialize and maintain an array of RNG states (one per thread).

### D. Recursion & Dynamic Allocation
Numba CUDA does not support recursion or list allocations (`[]`).
*   **Status**: The current `fast_logic.py` is already largely iterative and uses fixed arrays, so this is **Ready for Porting**.

## 4. Migration Roadmap

### Phase 1: Data Structures
Convert `VectorGameState` to allocate memory on GPU.
```python
# ai/vector_env_gpu.py
import cupy as cp

class VectorGameStateGPU:
    def __init__(self, num_envs):
        self.batch_stage = cp.full((num_envs, 3), -1, dtype=cp.int32)
        # ... all other arrays as cp.ndarray
```

### Phase 2: Kernel Rewrite
Rewrite `step_vectorized` as a kernel.
*   Replace `prange` with `cuda.grid(1)`.
*   Move `resolve_bytecode` to a `@cuda.jit(device=True)` function.

### Phase 3: PPO Adapter
Update the RL training loop (`train_optimized.py`) to accept GPU tensors.
```python
# In PPO Rollout Buffer
def collect_rollouts(self):
    # obs is already on GPU!
    with torch.no_grad():
        action, value, log_prob = self.policy(obs)

    # action is on GPU. Pass directly to env.step()
    next_obs = env.step(action)
```

## 5. Feasibility Verdict

**High Feasibility.** The codebase is already "Numba-Friendly" (no objects, flat arrays). The transition is primarily syntactic (`prange` -> `kernel`) and infrastructural (Numpy -> CuPy).

**Estimated Effort**: 1-2 weeks for a skilled GPU engineer.
**Expected Gain**: 5x-10x throughput scaling for batch sizes > 4096.
