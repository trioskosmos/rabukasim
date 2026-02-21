import os
import sys
import time

import torch
from stable_baselines3 import PPO

sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


def benchmark_config(num_envs, batch_size, total_steps=20000):
    print(f"--- Benchmarking Envs={num_envs}, Batch={batch_size} ---")

    try:
        # Create Env
        env = VectorEnvAdapter(num_envs=num_envs)

        # Create Model (Cheap MLP to simulate training overhead)
        model = PPO(
            "MlpPolicy",
            env,
            verbose=0,
            n_steps=128,  # Reduced memory footprint
            batch_size=batch_size,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )

        # Warmup
        env.reset()

        # Run Collection Loop (Simulate learn 'n_steps')
        # We just want to measure SPS of the collection phase primarily,
        # or the whole loop? The user cares about Training SPS.
        # So we run learn() for a short bit.

        start = time.perf_counter()
        model.learn(total_timesteps=total_steps, progress_bar=False)
        dur = time.perf_counter() - start

        sps = total_steps / dur
        print(f"-> SPS: {sps:,.0f} (Dur: {dur:.2f}s)")

        env.close()
        del model
        return sps

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"-> Failed: {e}")
        return 0


def run_tuning():
    configs = [
        # (Envs, BatchSize)
        (1024, 1024),
        (2048, 2048),
        (4096, 4096),
        (4096, 8192),
        (8192, 8192),
        (8192, 16384),
        (16384, 16384),
    ]

    best_sps = 0
    best_cfg = None

    print("Beginning Hyperparameter Tuning...")
    for n_envs, bs in configs:
        sps = benchmark_config(n_envs, bs)
        if sps > best_sps:
            best_sps = sps
            best_cfg = (n_envs, bs)

    if best_cfg:
        print("\n===============================")
        print(f"WINNER: Envs={best_cfg[0]}, Batch={best_cfg[1]}")
        print(f"Peak SPS: {best_sps:,.0f}")
        print("===============================")
    else:
        print("\n===============================")
        print("FAILED: No successful configurations found.")
        print("===============================")


if __name__ == "__main__":
    run_tuning()
