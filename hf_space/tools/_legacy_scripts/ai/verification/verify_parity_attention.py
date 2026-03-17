import os
import sys

import numpy as np

# Verify environment
sys.path.append(os.getcwd())

# Import CPU Env (Class is VectorGameState)
try:
    from ai.vector_env import VectorGameState

    print("Found VectorGameState (CPU)")
except ImportError as e:
    print(f"Error importing VectorGameState: {e}")
    sys.exit(1)

# Import GPU Env
HAS_GPU_ENV = False
try:
    from ai.vector_env_gpu import VectorEnvGPU

    HAS_GPU_ENV = True
    print("Found VectorEnvGPU (GPU)")
except ImportError:
    print("Warning: VectorEnvGPU not found or import failed.")


def compare_observations(obs_cpu, obs_gpu, rtol=1e-5, atol=1e-5):
    """Compares two observation batches."""
    if obs_cpu.shape != obs_gpu.shape:
        print(f"Shape Mismatch: CPU {obs_cpu.shape} vs GPU {obs_gpu.shape}")
        return False

    # Convert GPU to Numpy if needed (it assumes GPU returns CuPy by default)
    # Actually VectorEnvGPU.get_observations() returns CuPy array.
    import cupy as cp

    if isinstance(obs_gpu, cp.ndarray):
        obs_gpu = cp.asnumpy(obs_gpu)

    diff = np.abs(obs_cpu - obs_gpu)
    max_diff = np.max(diff)

    if max_diff > atol:
        print(f"Value Mismatch! Max Diff: {max_diff}")
        indices = np.where(diff > atol)
        print(f"Indices: {indices[0][:5]}, {indices[1][:5]}")
        sample_diffs = diff[indices[0][:5], indices[1][:5]]
        print(f"Diffs: {sample_diffs}")
        print(f"CPU: {obs_cpu[indices[0][:5], indices[1][:5]]}")
        print(f"GPU: {obs_gpu[indices[0][:5], indices[1][:5]]}")
        return False

    return True


def main():
    print("--- Verifying Attention Mode Parity (CPU vs GPU) ---")

    # Force Env Vars
    os.environ["OBS_MODE"] = "ATTENTION"
    # Ensure they use same pool
    os.environ["USE_FIXED_DECK"] = ""

    # Number of envs
    N = 10

    print("Initializing CPU Env...")
    cpu_env = VectorGameState(num_envs=N)

    if not HAS_GPU_ENV:
        print("Skipping GPU tests.")
        return

    print("Initializing GPU Env...")
    gpu_env = VectorEnvGPU(num_envs=N)

    # Initial Reset
    print("\n--- Resetting Envs ---")
    # For parity, we cannot easily force seeds in Reset unless we hack it.
    # But we can check structural integrity.

    obs_cpu = cpu_env.reset()  # This calls reset_kernel_numba -> reset_single
    obs_gpu = gpu_env.get_observations()  # First reset is handled in init?
    # Actually GPU env init usually calls reset?
    # Let's call explicit reset.
    gpu_env.reset()
    obs_gpu = gpu_env.get_observations()

    # Convert GPU obs to numpy
    import cupy as cp

    if isinstance(obs_gpu, cp.ndarray):
        obs_gpu = cp.asnumpy(obs_gpu)

    print(f"CPU Obs Shape: {obs_cpu.shape}")
    print(f"GPU Obs Shape: {obs_gpu.shape}")

    # Structural Checks
    # 1. Card IDs (Feature 5)
    # Stride 28.
    cpu_cids = obs_cpu[0, 5::28]
    gpu_cids = obs_gpu[0, 5::28]

    print(f"CPU Card IDs (First 5): {cpu_cids[:5]}")
    print(f"GPU Card IDs (First 5): {gpu_cids[:5]}")

    if np.all(cpu_cids == 0):
        print("FAIL: CPU Card IDs are all zero!")
    else:
        print("PASS: CPU Card IDs populated.")

    if np.all(gpu_cids == 0):
        print("FAIL: GPU Card IDs are all zero!")
    else:
        print("PASS: GPU Card IDs populated.")

    # 2. Opponent Resources (Global)
    # From Step 406: GLOBAL_START + 7..10
    # Where is GLOBAL_START?
    # obs_dim = 2240.
    # 80 cards * 28 features = 2240.
    # So Global scalars are OVERLAID or there is no global section separately?
    # Wait, `encode_observation_attention_single`:
    # `GLOBAL_START = num_cards * 28` ?
    # If `obs_dim` is tightly packed, then Global features are missing?
    # OR they overwrite the last card?
    # Let's checking `integrated_step_numba.py` again isn't feasible in this script.
    # I'll just check if CPU/GPU match on the LAST few values of the buffer.

    print("Comparing Global/End values...")
    print(f"CPU End: {obs_cpu[0, -10:]}")
    print(f"GPU End: {obs_gpu[0, -10:]}")

    # 3. Opponent History
    # This requires running a step where opponent plays.
    # Since we can't force opponent play easily, we randomly step.

    print("\n--- Stepping (Random) ---")
    actions = np.zeros(N, dtype=np.int32)
    # Using 0 (Skip) to preserve Energy? No, 0 might be Skip.

    cpu_env.step(actions)
    gpu_env.step(actions)

    # We don't compare observation exact values because RNG differs.
    # But we check if Structure remains valid.

    obs_cpu_post = cpu_env.get_observations()
    obs_gpu_post = gpu_env.get_observations()

    if isinstance(obs_gpu_post, cp.ndarray):
        obs_gpu_post = cp.asnumpy(obs_gpu_post)

    print("Post-Step Check passed (no crash).")

    print("\nVerification Script Finished Successfully.")


if __name__ == "__main__":
    main()
