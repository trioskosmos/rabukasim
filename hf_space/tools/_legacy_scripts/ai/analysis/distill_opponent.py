import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sb3_contrib import MaskablePPO
from stable_baselines3.common.vec_env import DummyVecEnv

# Ensure project root is in path
sys.path.append(os.getcwd())

from functools import partial

from ai.student_model import STUDENT_HIDDEN, StudentActor
from ai.train_optimized import create_env

# --- Config ---
TEACHER_PATH = "checkpoints/lovelive_ppo_optimized.zip"  # Fallback if specific file not found
STUDENT_OUTPUT_PATH = "checkpoints/student_model.pth"
DATASET_SIZE = 50000
BATCH_SIZE = 64
EPOCHS = 10
STUDENT_HIDDEN = 32  # Tiny!

# --- Student Architecture ---
# Imported from ai.student_model


def generate_dataset(teacher, env, n_samples):
    print(f"Generating {n_samples} samples from Teacher...")
    obs_list = []
    logits_list = []  # Or actions? Cloning logits is usually better for distillation (Knowledge Distillation)
    # But SB3 MaskablePPO doesn't easily expose logits via predict.
    # We'll use Behavior Cloning (BC) on deterministic teacher actions for simplicity first.

    action_list = []
    mask_list = []

    obs = env.reset()
    count = 0

    while count < n_samples:
        # Get Teacher Action
        # We need action masks for correct prediction
        masks = np.array([env.envs[0].action_masks()])  # DummyVecEnv extraction

        actions, _ = teacher.predict(obs, action_masks=masks, deterministic=True)

        # Store Data
        obs_list.append(obs[0].copy())
        action_list.append(actions[0])
        # mask_list.append(masks[0].copy()) # Optional: might learn to respect masks implicitly or we explicitly mask during inference

        # Step
        obs, rewards, dones, infos = env.step(actions)
        count += 1

        if count % 1000 == 0:
            print(f"  Collected {count}/{n_samples}...", end="\r")

    print("\nDataset generation complete.")
    return np.array(obs_list), np.array(action_list)


def train_student():
    # 1. Load Teacher
    path = TEACHER_PATH
    if not os.path.exists(path):
        # Try finding ANY checkpoint
        checkpoints = [f for f in os.listdir("checkpoints") if f.endswith(".zip")]
        if checkpoints:
            path = os.path.join("checkpoints", checkpoints[0])
            print(f"Default checkpoint not found. Using {path}")
        else:
            print("No teacher checkpoint found! Train some PPO first.")
            return

    print(f"Loading Teacher from {path}...")
    teacher = MaskablePPO.load(path, device="cuda" if torch.cuda.is_available() else "cpu")

    # 2. Env for Rollouts
    env = DummyVecEnv([partial(create_env, rank=0, usage=1.0, deck_type="random_verified", opponent_type="random")])

    # 3. Generate Data
    X, y = generate_dataset(teacher, env, DATASET_SIZE)
    env.close()

    # 4. Init Student
    obs_dim = X.shape[1]
    # We need to know action_dim. From gym_env:
    # Action spaces: 60 (hand) + 3 (stage) + 6 (color) + ... = 1913 is the max?
    # Actually gym_env defines explicit action space size.
    # Let's peek at the teacher's action space or env action space.
    action_dim = env.action_space.n
    print(f"Initializing Student (Obs: {obs_dim}, Act: {action_dim}, Hidden: {STUDENT_HIDDEN})")

    student = StudentActor(obs_dim, action_dim).to(teacher.device)
    optimizer = optim.Adam(student.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    # 5. Train Loop
    print("Training Student...")
    X_torch = torch.as_tensor(X).float().to(teacher.device)
    y_torch = torch.as_tensor(y).long().to(teacher.device)

    dataset = torch.utils.data.TensorDataset(X_torch, y_torch)
    loader = torch.utils.data.DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    for epoch in range(EPOCHS):
        total_loss = 0
        correct = 0
        total = 0

        for bx, by in loader:
            optimizer.zero_grad()
            logits = student(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            pred = torch.argmax(logits, 1)
            correct += (pred == by).sum().item()
            total += by.size(0)

        acc = correct / total
        print(f"Epoch {epoch + 1}/{EPOCHS} | Loss: {total_loss / len(loader):.4f} | Acc: {acc:.4f}")

    # 6. Save
    print(f"Saving Student to {STUDENT_OUTPUT_PATH}")
    torch.save(student, STUDENT_OUTPUT_PATH)

    # 7. Validation: Verify Interface
    print("Verifying Student Interface...")
    # Mock inference
    s_act, _ = student.predict(X[0:1], action_masks=np.ones((1, action_dim)))
    print(f"Prediction: {s_act}")


if __name__ == "__main__":
    train_student()
