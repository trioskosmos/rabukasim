import os
import sys
import time

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


def main():
    print("========================================================")
    print(" LovecaSim - DIAGNOSTIC: HANG ANALYSIS (Numba Compile)  ")
    print("========================================================")

    # Use a small number of envs for diagnostic to ensure it's not OOM
    # But enough to trigger parallel logic if any
    NUM_ENVS = 16

    print(f" [Init] Creating {NUM_ENVS} parallel Numba environments...")
    start_time = time.time()
    env = VectorEnvAdapter(num_envs=NUM_ENVS)
    print(f" [Init] Created in {time.time() - start_time:.2f}s")

    print("\n [Diag] PHASE 1: COMPILING RESET()")
    print(" [Diag] This creates the initial state. If this hangs, it's the reset kernel.")
    t0 = time.time()
    obs = env.reset()
    t1 = time.time()
    print(f" [Diag] RESET FINISHED. Time taken: {t1 - t0:.2f}s")
    print(f" [Diag] Obs shape: {obs.shape}")

    print("\n [Diag] PHASE 2: COMPILING STEP()")
    print(" [Diag] This compiles the massive integrated_step_numba function.")
    print(" [Diag] EXPECTATION: This may take 30-120 seconds on first run.")

    # Create dummy actions (PASS = 0)
    actions = np.zeros(NUM_ENVS, dtype=np.int32)

    t0 = time.time()
    obs, rewards, dones, infos = env.step(actions)
    t1 = time.time()
    print(f" [Diag] STEP FINISHED. Time taken: {t1 - t0:.2f}s")

    print("\n [Diag] PHASE 3: SECOND STEP (Should be instant)")
    t0 = time.time()
    obs, rewards, dones, infos = env.step(actions)
    t1 = time.time()
    print(f" [Diag] SECOND STEP FINISHED. Time taken: {t1 - t0:.4f}s")

    print("\n [Result] If you see this, the engine is NOT hung. It was just compiling.")


if __name__ == "__main__":
    main()
