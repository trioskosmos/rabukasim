import os
import sys
import time

import numpy as np
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.vec_env import DummyVecEnv

# Ensure project root is in path
sys.path.append(os.getcwd())

from functools import partial

from ai.train_optimized import create_env

# --- Config ---
TEACHER_PATH = "checkpoints/lovelive_ppo_optimized.zip"
STUDENT_PATH = "checkpoints/student_model.pth"
TEST_SAMPLES = 1000


def run_comparison():
    # 1. Load Models
    path = TEACHER_PATH
    if not os.path.exists(path):
        checkpoints = [f for f in os.listdir("checkpoints") if f.endswith(".zip")]
        if checkpoints:
            path = os.path.join("checkpoints", checkpoints[0])

    print(f"Loading Teacher from {path}...")
    teacher = MaskablePPO.load(path, device="cuda" if torch.cuda.is_available() else "cpu")

    print(f"Loading Student from {STUDENT_PATH}...")
    # Safe load requires weights_only=False for custom classes unless registered
    student = torch.load(STUDENT_PATH, weights_only=False)
    student.to(teacher.device)

    student.eval()  # Inference mode

    # 2. Env
    env = DummyVecEnv([partial(create_env, rank=0, usage=1.0, deck_type="random_verified", opponent_type="random")])
    obs = env.reset()

    # 3. Metrics
    matches = 0
    total = 0
    t_teacher_sum = 0
    t_student_sum = 0

    print(f"Comparing on {TEST_SAMPLES} samples...")
    masks = np.array([env.envs[0].action_masks()])

    for i in range(TEST_SAMPLES):
        # Teacher Inference
        t0 = time.perf_counter()
        act_t, _ = teacher.predict(obs, action_masks=masks, deterministic=True)
        t_teacher_sum += time.perf_counter() - t0

        # Student Inference
        t0 = time.perf_counter()
        act_s, _ = student.predict(obs, action_masks=masks, deterministic=True)
        t_student_sum += time.perf_counter() - t0

        # Compare
        if act_t[0] == act_s[0]:
            matches += 1
        total += 1

        # Step (driven by teacher)
        obs, rewards, dones, infos = env.step(act_t)
        masks = np.array([env.envs[0].action_masks()])

        if total % 100 == 0:
            print(f" Progress: {total}/{TEST_SAMPLES}", end="\r")

    env.close()

    acc = matches / total
    avg_t = (t_teacher_sum / total) * 1000
    avg_s = (t_student_sum / total) * 1000

    print("\n" + "=" * 40)
    print(" DISTILLATION COMPARISON RESULTS")
    print("=" * 40)
    print(f"Accuracy (Student vs Teacher): {acc * 100:.2f}%")
    print("-" * 40)
    print(f"Teacher Latency: {avg_t:.4f} ms")
    print(f"Student Latency: {avg_s:.4f} ms")
    print(f"Speedup Factor:  {avg_t / avg_s:.2f}x")
    print("-" * 40)
    if acc < 0.8:
        print("WARNING: Low accuracy. Student might be too simple or needs more training.")
    else:
        print("SUCCESS: Student is a good approximation.")
    print("=" * 40)


if __name__ == "__main__":
    run_comparison()
