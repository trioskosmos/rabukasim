"""
GPU-Resident Environment Proof-of-Concept
=========================================

This file demonstrates how the current CPU-based Numba VectorEnv
would be translated to a GPU-based Numba CUDA implementation.

Usage:
    This is a design reference. It requires a CUDA-capable GPU and the
    `cudatoolkit` library to run.

    To run (if hardware available):
    $ python ai/cuda_proof_of_concept.py
"""

import time

import numpy as np

try:
    from numba import cuda, float32, int32
    from numba.cuda.random import create_xoroshiro128p_states, xoroshiro128p_uniform_float32

    HAS_CUDA = True
except ImportError:
    print("Warning: Numba CUDA not installed or hardware not found.")
    HAS_CUDA = False

    # Mock objects for linting/viewing
    class MockCuda:
        def jit(self, *args, **kwargs):
            return lambda x: x

        def grid(self, x):
            return 0

        def device_array(self, *args, **kwargs):
            return np.zeros(*args)

        def to_device(self, x):
            return x

        def synchronize(self):
            pass

    cuda = MockCuda()

# Constants
CTX_VALUE = 20
SC = 0
HD = 3
DK = 6

# =============================================================================
# 1. Device Functions (The "Inner Logic")
# =============================================================================
# Instead of @njit, we use @cuda.jit(device=True)
# These functions can ONLY be called from other CUDA kernels/functions.


@cuda.jit(device=True)
def resolve_bytecode_device(bytecode, flat_ctx, global_ctx, p_hand, p_deck):
    """
    Equivalent to engine/game/fast_logic.py:resolve_bytecode
    Adapted for CUDA:
    - No recursion (CUDA doesn't support it well, though Numba has limited support).
    - Minimal stack usage.
    """
    # Simple example opcode implementation
    ip = 0
    blen = bytecode.shape[0]

    while ip < blen:
        op = bytecode[ip, 0]
        v = bytecode[ip, 1]

        # O_DRAW (Opcode 10)
        if op == 10:
            # Check Deck Count
            if global_ctx[DK] >= v:
                global_ctx[DK] -= v
                global_ctx[HD] += v
                # Real implementation would move card IDs in p_hand/p_deck arrays

        # O_RETURN (Opcode 1)
        elif op == 1:
            return 0

        ip += 1
    return 0


# =============================================================================
# 2. Kernels (The "Parallel Loops")
# =============================================================================
# Instead of `for i in prange(num_envs)`, the GPU launches thousands of threads.
# Each thread calculates its ID and processes one environment.


@cuda.jit
def step_kernel(
    rng_states, batch_stage, batch_global_ctx, batch_hand, batch_deck, bytecode_map, bytecode_index, actions
):
    """
    CUDA Kernel to step N environments in parallel.
    One thread = One Environment.
    """
    # 1. Calculate Thread ID
    # This replaces the `for i in range(num_envs)` loop
    i = cuda.grid(1)

    # Bounds check (in case we launched more threads than envs)
    if i >= batch_global_ctx.shape[0]:
        return

    # 2. Apply Action
    act_id = actions[i]

    # Lookup bytecode
    # (Simplified for POC)
    if act_id > 0:
        # Get map index
        map_idx = bytecode_index[act_id, 0]

        # Get bytecode sequence
        # Note: Accessing large global arrays is fine, but caching in shared memory
        # is better for performance if many threads access the same data.
        code_seq = bytecode_map[map_idx]

        # Call Device Function
        resolve_bytecode_device(
            code_seq,
            batch_global_ctx[i],  # Passing slice creates a local view?
            # Numba CUDA handles array slicing carefully.
            batch_global_ctx[i],  # using global_ctx as flat_ctx for demo
            batch_hand[i],
            batch_deck[i],
        )

    # 3. Randomness (Opponent Logic)
    # CUDA requires explicit RNG states
    rand_val = xoroshiro128p_uniform_float32(rng_states, i)
    if rand_val > 0.5:
        # Simulate opponent doing something
        pass


# =============================================================================
# 3. Host Controller (The "Driver")
# =============================================================================


class CudaVectorEnv:
    def __init__(self, num_envs=4096):
        if not HAS_CUDA:
            pass  # Continue with mocks

        self.num_envs = num_envs

        # 1. Allocate Data on GPU (Device Arrays)
        # This is "Zero-Copy" residence. Data lives on VRAM.
        self.d_batch_stage = cuda.device_array((num_envs, 3), dtype=np.int32)
        self.d_batch_global_ctx = cuda.device_array((num_envs, 128), dtype=np.int32)
        self.d_batch_hand = cuda.device_array((num_envs, 60), dtype=np.int32)
        self.d_batch_deck = cuda.device_array((num_envs, 60), dtype=np.int32)

        # Bytecode maps also go to GPU (Read-Only)
        # Assuming we loaded them like in vector_env.py
        self.d_bytecode_map = cuda.to_device(np.zeros((100, 64, 4), dtype=np.int32))
        self.d_bytecode_index = cuda.to_device(np.zeros((2000, 4), dtype=np.int32))

        # RNG States
        if HAS_CUDA:
            self.rng_states = create_xoroshiro128p_states(num_envs, seed=1234)
        else:
            self.rng_states = None

        # Threads per Block (Hyperparameter)
        self.threads_per_block = 128
        self.blocks_per_grid = (num_envs + (self.threads_per_block - 1)) // self.threads_per_block

    def step(self, actions):
        """
        1. Copy Actions to GPU (Small transfer: 4KB for 1024 envs)
        2. Launch Kernel
        3. (Optional) Return Observation Pointer
        """
        # Transfer actions to GPU
        d_actions = cuda.to_device(actions)

        # Launch Kernel
        step_kernel[self.blocks_per_grid, self.threads_per_block](
            self.rng_states,
            self.d_batch_stage,
            self.d_batch_global_ctx,
            self.d_batch_hand,
            self.d_batch_deck,
            self.d_bytecode_map,
            self.d_bytecode_index,
            d_actions,
        )

        # Synchronize (Wait for finish)
        cuda.synchronize()

        # In a real "Isaac Gym" setup, we wouldn't copy back.
        # We would return the device array handle to PyTorch.
        # return self.d_batch_global_ctx

        # For POC, we copy back to show it works
        # If mock, this fails because mock device_array is numpy
        if HAS_CUDA:
            return self.d_batch_global_ctx.copy_to_host()
        else:
            return self.d_batch_global_ctx


if __name__ == "__main__":
    print("Initializing CUDA Env Proof of Concept...")
    if HAS_CUDA:
        try:
            env = CudaVectorEnv(num_envs=1024)
            actions = np.zeros(1024, dtype=np.int32)

            start = time.time()
            res = env.step(actions)
            end = time.time()

            print(f"Step completed in {end - start:.6f}s")
        except Exception as e:
            print(f"Runtime Error: {e}")
    else:
        print("Skipping run (No CUDA), verifying syntax only.")
        env = CudaVectorEnv(num_envs=10)
        print("Mock env initialized.")
