# [LEGACY] AlphaZero Training Script
# DEPRECATED: Uses old AlphaNet architecture. Use overnight_vanilla.py.
import os

import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

from alphazero.alphanet import AlphaNet


class AlphaDataset(Dataset):
    def __init__(self, data_path=None, obs=None, policy=None, mask=None, value=None):
        if data_path:
            data = np.load(data_path)
            self.obs = torch.from_numpy(data["obs"]).float()
            self.policy = torch.from_numpy(data["policy"]).float()
            self.mask = torch.from_numpy(data["mask"]).bool()
            self.value = torch.from_numpy(data["value"]).float()
        else:
            self.obs = torch.from_numpy(obs).float()
            self.policy = torch.from_numpy(policy).float()
            self.mask = torch.from_numpy(mask).bool()
            self.value = torch.from_numpy(value).float()

    def __len__(self):
        return len(self.obs)

    def __getitem__(self, idx):
        return self.obs[idx], self.policy[idx], self.mask[idx], self.value[idx].unsqueeze(0)


def train_epoch(model, loader, optimizer, device, entropy_lambda=1e-3):
    """Train for one epoch using DataLoader. Compatible with v8 action-branching architecture."""
    model.train()
    total_loss = 0
    total_value_loss = 0
    total_policy_loss = 0
    total_entropy_loss = 0

    for obs, policy_targets, mask, value_targets in loader:
        obs = obs.to(device)
        policy_targets = policy_targets.to(device)
        mask = mask.to(device)
        value_targets = value_targets.to(device)

        optimizer.zero_grad()

        policy_logits, value_preds = model(obs, mask=mask)

        # 1. Standard AlphaZero Losses
        value_loss = F.mse_loss(value_preds, value_targets)
        log_probs = F.log_softmax(policy_logits, dim=1)
        policy_loss = F.kl_div(log_probs, policy_targets, reduction="batchmean")

        # 2. Entropy Regularization (encourage exploration)
        probs = F.softmax(policy_logits, dim=1)
        entropy = -(probs * log_probs).sum(dim=1).mean()
        # Negative entropy = penalize low entropy = encourage exploration
        entropy_loss = -entropy

        loss = value_loss + policy_loss + (entropy_lambda * entropy_loss)

        if torch.isnan(loss):
            print("NaN detected in loss! Skipping batch.")
            continue

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        total_value_loss += value_loss.item()
        total_policy_loss += policy_loss.item()
        total_entropy_loss += entropy.item()

    num_batches = len(loader)
    if num_batches == 0:
        return {"loss": 0.0, "value": 0.0, "policy": 0.0, "entropy": 0.0}
    return {
        "loss": total_loss / num_batches,
        "value": total_value_loss / num_batches,
        "policy": total_policy_loss / num_batches,
        "entropy": total_entropy_loss / num_batches,
    }


def run_training(data_path="pure_zero_trajectories.npz", epochs=50, batch_size=64, lr=0.001):
    import time

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("--- Starting Training Session ---")
    print(f"Device: {device}")
    print(f"Parameters: LR={lr}, Batch={batch_size}")

    dataset = AlphaDataset(data_path)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = AlphaNet().to(device)

    checkpoint_path = "alphanet_latest.pt"
    if os.path.exists(checkpoint_path):
        print(f"Resuming from {checkpoint_path}...")
        try:
            model.load_state_dict(torch.load(checkpoint_path, map_location=device))
        except Exception as e:
            print(f"Warning: Could not load checkpoint: {e}")

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    best_loss = float("inf")
    last_checkpoint_time = time.time()
    checkpoint_interval = 30 * 60

    for epoch in range(epochs):
        stats = train_epoch(model, loader, optimizer, device)

        # Calculate Policy Accuracy on the training set (rough estimate)
        # Note: A proper validation set is better, but this syncs with pure_zero
        correct = 0
        total = 0
        with torch.no_grad():
            for obs, pol_t, mask, val_t in loader:
                obs = obs.to(device)
                pol_t = pol_t.to(device)
                mask = mask.to(device)
                p_logits, _ = model(obs, mask=mask)
                correct += (torch.argmax(p_logits, dim=1) == torch.argmax(pol_t, dim=1)).sum().item()
                total += obs.size(0)

        pol_acc = (correct / total) * 100 if total > 0 else 0.0

        print(
            f"Epoch {epoch + 1:2d} | Loss: {stats['loss']:.4f} [V:{stats['value']:.3f} P:{stats['policy']:.3f} E:{stats['entropy']:.2f}] | Acc: {pol_acc:.1f}%"
        )

        torch.save(model.state_dict(), checkpoint_path)

        current_time = time.time()
        if current_time - last_checkpoint_time > checkpoint_interval:
            backup_path = f"alphanet_checkpoint_{int(current_time)}.pt"
            torch.save(model.state_dict(), backup_path)
            print(">> Created 30-minute backup.")
            last_checkpoint_time = current_time

        if stats["loss"] < best_loss:
            best_loss = stats["loss"]
            torch.save(model.state_dict(), "alphanet_best.pt")

    print("--- Training complete ---")


if __name__ == "__main__":
    if os.path.exists("trajectories.npz"):
        run_training()
    else:
        print("Error: trajectories.npz not found. Run generate_self_play.py first.")
