import os
import sys
import time

import numpy as np
import torch

# Ensure project root is in path
sys.path.append(os.getcwd())

import torch.nn.functional as F
import torch.optim as optim

from ai.environments.rust_env_lite import RustEnvLite
from ai.models.training_config import INPUT_SIZE, POLICY_SIZE
from ai.training.train import AlphaNet


def benchmark():
    print("========================================================")
    print(" LovecaSim AlphaZero Benchmark (Lite Rust Env)          ")
    print("========================================================")

    # Configuration
    NUM_ENVS = int(os.getenv("BENCH_ENVS", "256"))
    TOTAL_STEPS = int(os.getenv("BENCH_STEPS", "200"))
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f" [Bench] Device:  {DEVICE}")
    print(f" [Bench] Envs:    {NUM_ENVS}")
    print(f" [Bench] Steps:   {TOTAL_STEPS}")
    print(f" [Bench] Obs Dim: {INPUT_SIZE}")

    # 1. Initialize Simplified Environment
    print(" [Bench] Initializing Rust Engine (Lite)...")
    env = RustEnvLite(num_envs=NUM_ENVS)
    obs = env.reset()

    # 2. Initialize Model
    print(" [Bench] Initializing AlphaNet...")
    model = AlphaNet(policy_size=POLICY_SIZE).to(DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=1e-4)

    obs_tensor = torch.zeros((NUM_ENVS, INPUT_SIZE), dtype=torch.float32).to(DEVICE)
    obs_tensor.requires_grad = True  # Enable grad for stress testing

    # 3. Benchmark Loop
    print(" [Bench] Starting Training Loop...")
    start_time = time.time()
    total_samples = 0

    for step in range(1, TOTAL_STEPS + 1):
        # A. Sync Obs to GPU
        with torch.no_grad():
            obs_tensor.copy_(torch.from_numpy(obs))

        # B. Inference
        policy_logits, value = model(obs_tensor)

        # C. Action Selection (Sample from logits)
        # Gradient is detached for sampling
        with torch.no_grad():
            probs = F.softmax(policy_logits, dim=1)
            actions = torch.multinomial(probs, 1).cpu().numpy().flatten().astype(np.int32)

        # D. Environment Step
        obs, rewards, dones, done_indices = env.step(actions)

        # E. Dummy Training Step (Simulate backward pass stress)
        if step % 5 == 0:
            optimizer.zero_grad()
            # Dummy target for benchmarking
            p_loss = policy_logits.mean()
            v_loss = value.mean()
            loss = p_loss + v_loss
            loss.backward()
            optimizer.step()

        total_samples += NUM_ENVS

        if step % 50 == 0 or step == TOTAL_STEPS:
            elapsed = time.time() - start_time
            sps = total_samples / elapsed if elapsed > 0 else 0
            print(f" [Bench] Step {step}/{TOTAL_STEPS} | SPS: {sps:.0f}")

    end_time = time.time()
    duration = end_time - start_time
    final_sps = total_samples / duration

    print("\n========================================================")
    print(" [Result] Benchmark Completed!")
    print(f" [Result] Total Time:    {duration:.2f}s")
    print(f" [Result] Total Samples: {total_samples}")
    print(f" [Result] Final SPS:     {final_sps:.2f}")
    print("========================================================")


if __name__ == "__main__":
    benchmark()
