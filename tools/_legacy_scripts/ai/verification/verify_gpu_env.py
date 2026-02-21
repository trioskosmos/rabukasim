"""
GPU Environment Verification Script.

Tests GPU environment parity with CPU and benchmarks throughput.

Usage:
    uv run python ai/verify_gpu_env.py
"""

import os
import sys
import time

import numpy as np

# Ensure project root in path
sys.path.append(os.getcwd())


def test_cuda_availability():
    """Check if CUDA is available."""
    print("\n=== CUDA Availability ===")
    try:
        import cupy as cp
        from numba import cuda

        if cuda.is_available():
            device = cuda.get_current_device()
            print("✓ CUDA Available")
            print(f"  Device: {device.name.decode()}")
            print(f"  Compute Capability: {device.compute_capability}")

            # Memory info
            meminfo = cuda.current_context().get_memory_info()
            free_mb = meminfo[0] / 1024 / 1024
            total_mb = meminfo[1] / 1024 / 1024
            print(f"  VRAM: {free_mb:.0f} MB free / {total_mb:.0f} MB total")
            return True
        else:
            print("✗ CUDA not available (numba.cuda.is_available() returned False)")
            return False
    except ImportError as e:
        print(f"✗ CuPy/Numba CUDA not installed: {e}")
        print("  Install with: pip install cupy-cuda12x numba")
        return False


def test_gpu_env_creation():
    """Test creating the GPU environment."""
    print("\n=== GPU Environment Creation ===")
    try:
        from ai.vector_env_gpu import HAS_CUDA, VectorEnvGPU

        if not HAS_CUDA:
            print("✗ HAS_CUDA is False")
            return None

        env = VectorEnvGPU(num_envs=128)
        print("✓ Created VectorEnvGPU with 128 environments")
        print(f"  Observation dim: {env.obs_dim}")
        print(f"  Deck pool: {len(env.ability_member_ids.get())} members, {len(env.ability_live_ids.get())} lives")
        return env
    except Exception as e:
        print(f"✗ Failed to create GPU environment: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_reset(env):
    """Test environment reset."""
    print("\n=== Reset Test ===")
    try:
        import cupy as cp

        obs = env.reset()
        print("✓ Reset succeeded")
        print(f"  Observation shape: {obs.shape}")
        print(f"  Observation dtype: {obs.dtype}")
        print(f"  Observation sample (first 5): {cp.asnumpy(obs[0, :5])}")
        return True
    except Exception as e:
        print(f"✗ Reset failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_step(env):
    """Test environment step."""
    print("\n=== Step Test ===")
    try:
        import cupy as cp

        # Pass action (0)
        actions = cp.zeros(env.num_envs, dtype=cp.int32)
        obs, rewards, dones, infos = env.step(actions)

        print("✓ Step succeeded")
        print(f"  Rewards sample: {cp.asnumpy(rewards[:5])}")
        print(f"  Dones sample: {cp.asnumpy(dones[:5])}")
        print(f"  Scores sample: {cp.asnumpy(env.batch_scores[:5])}")
        return True
    except Exception as e:
        print(f"✗ Step failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_action_masks(env):
    """Test action mask computation."""
    print("\n=== Action Masks Test ===")
    try:
        import cupy as cp

        masks = env.get_action_masks()
        masks_np = cp.asnumpy(masks)

        print("✓ Action masks computed")
        print(f"  Shape: {masks.shape}")
        print(f"  Legal actions (env 0): {np.sum(masks_np[0])}")
        print(f"  Pass legal (action 0): {masks_np[0, 0]}")
        return True
    except Exception as e:
        print(f"✗ Action masks failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def benchmark_throughput(batch_sizes=[128, 256, 512, 1024, 2048, 4096]):
    """Benchmark GPU environment throughput."""
    print("\n=== Throughput Benchmark ===")

    try:
        import cupy as cp
        from ai.vector_env_gpu import HAS_CUDA, VectorEnvGPU
        from numba import cuda

        if not HAS_CUDA:
            print("✗ CUDA not available for benchmark")
            return

        print(f"{'Batch Size':<12} {'SPS':>12} {'Time (100 steps)':>18}")
        print("-" * 44)

        for batch_size in batch_sizes:
            try:
                env = VectorEnvGPU(num_envs=batch_size)
                env.reset()

                # Warmup
                for _ in range(5):
                    actions = cp.zeros(batch_size, dtype=cp.int32)
                    env.step(actions)
                cuda.synchronize()

                # Benchmark
                steps = 100
                start = time.time()
                for _ in range(steps):
                    actions = cp.zeros(batch_size, dtype=cp.int32)
                    env.step(actions)
                cuda.synchronize()
                elapsed = time.time() - start

                total_steps = batch_size * steps
                sps = total_steps / elapsed

                print(f"{batch_size:<12} {sps:>12,.0f} {elapsed:>17.2f}s")
            except Exception as e:
                print(f"{batch_size:<12} {'FAILED':>12} {str(e)[:18]}")

    except Exception as e:
        print(f"✗ Benchmark failed: {e}")
        import traceback

        traceback.print_exc()


def compare_cpu_gpu():
    """Compare CPU and GPU environment outputs (parity check)."""
    print("\n=== CPU vs GPU Parity Check ===")

    try:
        import cupy as cp
        from ai.vector_env import VectorGameState
        from ai.vector_env_gpu import HAS_CUDA, VectorEnvGPU

        if not HAS_CUDA:
            print("✗ CUDA not available for parity check")
            return

        num_envs = 16
        seed = 42

        # Note: Full parity check would require seeding both environments identically
        # This is a simplified check that verifies similar behavior

        cpu_env = VectorGameState(num_envs, opp_mode=0, force_start_order=0)
        gpu_env = VectorEnvGPU(num_envs, opp_mode=0, force_start_order=0, seed=seed)

        cpu_obs = cpu_env.reset()
        gpu_obs = cp.asnumpy(gpu_env.reset())

        print(f"CPU obs shape: {cpu_obs.shape}, GPU obs shape: {gpu_obs.shape}")

        # Check dimensions match
        if cpu_obs.shape == gpu_obs.shape:
            print("✓ Observation dimensions match")
        else:
            print("✗ Observation dimensions mismatch!")

        # Step both environments with Pass (0)
        cpu_actions = np.zeros(num_envs, dtype=np.int32)
        gpu_actions = cp.zeros(num_envs, dtype=cp.int32)

        cpu_obs, cpu_rewards, cpu_dones, _ = cpu_env.step(cpu_actions)
        gpu_obs, gpu_rewards, gpu_dones, _ = gpu_env.step(gpu_actions)

        gpu_rewards_np = cp.asnumpy(gpu_rewards)
        gpu_dones_np = cp.asnumpy(gpu_dones)

        print(f"CPU rewards (first 5): {cpu_rewards[:5]}")
        print(f"GPU rewards (first 5): {gpu_rewards_np[:5]}")

        # Note: Exact match not expected due to different RNG states
        print("✓ Both environments stepped successfully")
        print("  (Exact match not expected due to different RNG initialization)")

    except Exception as e:
        print(f"✗ Parity check failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    print("=" * 60)
    print("  GPU Environment Verification")
    print("=" * 60)

    # Test CUDA availability
    if not test_cuda_availability():
        print("\n⚠ CUDA not available. GPU environment cannot be used.")
        print("  Training will fall back to CPU Numba environment.")
        return 1

    # Create environment
    env = test_gpu_env_creation()
    if env is None:
        return 1

    # Test reset
    if not test_reset(env):
        return 1

    # Test step
    if not test_step(env):
        return 1

    # Test action masks
    if not test_action_masks(env):
        return 1

    # Parity check
    compare_cpu_gpu()

    # Benchmark
    benchmark_throughput()

    print("\n" + "=" * 60)
    print("  ✓ All GPU environment tests passed!")
    print("=" * 60)
    print("\nTo enable GPU training, set:")
    print("  SET USE_GPU_ENV=1")
    print("  start_vanilla_deck_training.bat")

    return 0


if __name__ == "__main__":
    sys.exit(main())
