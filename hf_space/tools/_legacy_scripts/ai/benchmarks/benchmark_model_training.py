import os
import sys
import time

import numpy as np
import torch

sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv
from ai.student_model import StudentActor
from ai.vector_env import VectorGameState

# Hardware setup (Matches production)
torch.set_num_threads(1)
if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")


def benchmark_training():
    print("--- Production Training Benchmark (Extreme) ---")
    print(f"Device: {device}")

    obs_dim = 320
    action_dim = 1000
    model = StudentActor(obs_dim, action_dim).to(device)
    model.eval()

    # --- Benchmark A: Python Engine (Sequential) ---
    py_steps = 200
    print(f"\n[A] Benchmarking Python Engine (1 Env, {py_steps} steps)...")
    env = LoveLiveCardGameEnv(deck_type="normal", opponent_type="random")
    obs, _ = env.reset()

    start = time.perf_counter()
    for _ in range(py_steps):
        with torch.no_grad():
            action, _ = model.predict(obs.reshape(1, -1))
        obs, reward, done, truncated, info = env.step(int(action[0]))
        if done or truncated:
            obs, _ = env.reset()
    py_dur = time.perf_counter() - start
    py_sps = py_steps / py_dur
    print(f"Python SPS: {py_sps:.2f} steps/sec")

    # --- Benchmark B: Numba Vector Engine (Batch) ---
    batch_size = 1024
    nb_steps = 1024 * 100  # 100 iterations
    print(f"\n[B] Benchmarking Numba Vector Engine (Batch {batch_size}, {nb_steps} steps)...")
    vec_env = VectorGameState(batch_size)
    vec_env.reset()
    obs = vec_env.get_observations()

    # Warmup
    vec_env.step(np.ones(batch_size, dtype=np.int32))

    start = time.perf_counter()
    iters = nb_steps // batch_size
    for _ in range(iters):
        with torch.no_grad():
            actions, _ = model.predict(obs)
        vec_env.step(actions.astype(np.int32))
        obs = vec_env.get_observations()
    nb_dur = time.perf_counter() - start
    nb_sps = nb_steps / nb_dur
    print(f"Numba Vector SPS: {nb_sps:.2f} steps/sec")

    print("\n" + "=" * 40)
    print(f"TRAINING SPEEDUP: {nb_sps / py_sps:.2f}x")
    print("=" * 40)
    print(f"Numba Latency (inc. Torch): {1e9 / nb_sps:,.0f} ns/step")
    print(f"Python Latency (inc. Torch): {1e9 / py_sps:,.0f} ns/step")


if __name__ == "__main__":
    benchmark_training()
