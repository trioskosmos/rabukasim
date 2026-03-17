import os
import sys
import time

import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.vec_env import DummyVecEnv

# Ensure project root is in path
sys.path.append(os.getcwd())

from functools import partial

from ai.batched_env import BatchedSubprocVecEnv
from ai.train_optimized import create_env

# We use the existing environment logic
# We want to measure:
# 1. Rollout Time (affected by n_steps)
# 2. Train Time (affected by batch_size)


def benchmark_run(n_steps, batch_size, n_cpu):
    print(f"--- Benchmarking Steps={n_steps}, Batch={batch_size}, CPU={n_cpu} ---")

    # Setup Env
    env_fns = [
        partial(create_env, rank=i, usage=1.0, deck_type="random_verified", opponent_type="random")
        for i in range(n_cpu)
    ]

    # Use Batched if using distinct CPUs, else Dummy for speed if 1 cpu
    # For hyperparam tuning, accurate timing requires the real env
    if n_cpu > 1:
        env = BatchedSubprocVecEnv(env_fns)
    else:
        env = DummyVecEnv(env_fns)

    # Setup Model
    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=0,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=1,  # Keep epochs low just to measure throughput per epoch time
        device="cuda" if torch.cuda.is_available() else "cpu",
    )

    t0 = time.perf_counter()

    # Run 1 complete cycle (Rollout + Train)
    # Total timesteps = n_steps * n_envs
    # SB3 '.learn' runs at least one rollout.
    total_timesteps = n_steps * n_cpu

    model.learn(total_timesteps=total_timesteps)

    elapsed = time.perf_counter() - t0
    fps = total_timesteps / elapsed

    print(f"Done. Time: {elapsed:.2f}s | FPS: {fps:.2f}")

    env.close()
    return fps


def main():
    if len(sys.argv) >= 4:
        # CLI Mode: python script.py <N_STEPS> <BATCH_SIZE> <N_CPU>
        n_steps = int(sys.argv[1])
        batch = int(sys.argv[2])
        n_cpu = int(sys.argv[3])

        try:
            # Force Distilled for consistent env speed
            os.environ["USE_DISTILLED_OPPONENT"] = "1"
            fps = benchmark_run(n_steps, batch, n_cpu)

            with open("hyperparam_results.txt", "a") as f:
                f.write(f"{n_steps},{batch},{n_cpu},{fps:.2f}\n")
        except Exception as e:
            print(f"FAIL: {e}")
            sys.exit(1)
    else:
        print("Usage: python ai/tune_hyperparams.py <N_STEPS> <BATCH_SIZE> <N_CPU>")


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    main()
