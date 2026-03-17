import argparse
import os

# Add project root to path
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sb3_contrib import MaskablePPO
from stable_baselines3.common.utils import get_device
from torch.utils.data import DataLoader, Dataset

sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


class BCDataset(Dataset):
    def __init__(self, path):
        print(f"Loading {path}...")
        data = np.load(path)
        self.obs = data["obs"]
        self.actions = data["actions"]
        print(f"Loaded {len(self.obs)} samples.")

    def __len__(self):
        return len(self.obs)

    def __getitem__(self, idx):
        return self.obs[idx], self.actions[idx].astype(np.int64)


def train_bc(data_path="data/bc_dataset.npz", save_path="models/bc_pretrained", epochs=10, batch_size=256, lr=1e-3):
    device = get_device("auto")
    print(f"Using device: {device}")

    # 1. Initialize Dummy Env to get shapes/Policy
    # We use COMPRESSED or STANDARD depending on env vars, defaults to STANDARD (2304)
    # The dataset MUST match the observation space used here.
    # generate_bc_data.py uses the default OBS_MODE from VectorEnv.
    # Ensure they match!

    env = VectorEnvAdapter(num_envs=1)

    # 2. Create Model (MaskablePPO)
    # We initialize a PPO model to get the policy network structure
    model = MaskablePPO("MlpPolicy", env, verbose=1, device=device, learning_rate=lr)

    policy = model.policy.to(device)
    optimizer = optim.Adam(policy.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    # 3. Data Loader
    dataset = BCDataset(data_path)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 4. Training Loop
    print("Starting BC Training...")

    for epoch in range(epochs):
        total_loss = 0
        total_acc = 0
        batches = 0

        policy.train()
        for batch_obs, batch_acts in dataloader:
            batch_obs = batch_obs.to(device).float()
            batch_acts = batch_acts.to(device)

            # Forward pass
            # PPO Policy: get_distribution(obs) -> distribution
            # We want logits.
            # policy.action_net(policy.mlp_extractor.forward_actor(features))

            features = policy.extract_features(batch_obs)
            latent_pi, _ = policy.mlp_extractor(features)
            logits = policy.action_net(latent_pi)

            # Masking?
            # In BC, we assume the heuristic action IS valid.
            # We train the net to output it.
            # We technically don't need masking for the loss, but the net should learn to not pick invalids.
            # Ideally, we should apply masks to logits before Softmax to suppress invalids?
            # But we don't have masks in the dataset (unless we generate them).
            # The heuristic action is valid by definition.
            # The network should learn to maximize logit for valid action.

            loss = loss_fn(logits, batch_acts)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            # Accuracy
            preds = torch.argmax(logits, dim=1)
            acc = (preds == batch_acts).float().mean().item()
            total_acc += acc
            batches += 1

        print(f"Epoch {epoch + 1}/{epochs} | Loss: {total_loss / batches:.4f} | Acc: {total_acc / batches:.4f}")

    # 5. Save
    print(f"Saving model to {save_path}...")
    model.save(save_path)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/bc_dataset.npz")
    parser.add_argument("--save", type=str, default="models/bc_pretrained")
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()

    train_bc(data_path=args.data, save_path=args.save, epochs=args.epochs)
