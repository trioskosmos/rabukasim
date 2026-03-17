import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# Add project root to path
sys.path.append(os.getcwd())

from ai.models.fast_model import FastMoveModel

from alphazero.alphanet import ACTION_SUB_TABLE, ACTION_TYPE_TABLE


class DistillDataset(Dataset):
    def __init__(self, data_path):
        data = np.load(data_path)
        obs_raw = data["obs"]
        actions_raw = data["actions"]

        # Filter out invalid actions (type -1)
        valid_mask = ACTION_TYPE_TABLE[actions_raw] >= 0
        obs_filtered = obs_raw[valid_mask]
        actions_filtered = actions_raw[valid_mask]

        print(f"Filtered {len(actions_raw) - len(actions_filtered)} invalid actions from {len(actions_raw)} total.")

        self.obs = torch.from_numpy(obs_filtered).float()
        self.actions = torch.from_numpy(actions_filtered).long()

        # Pre-compute target heads for hierarchical loss (using numpy indexing)
        self.target_types = torch.from_numpy(ACTION_TYPE_TABLE[actions_filtered]).long()
        self.target_subs = torch.from_numpy(ACTION_SUB_TABLE[actions_filtered]).long()

    def __len__(self):
        return len(self.obs)

    def __getitem__(self, idx):
        return self.obs[idx], self.target_types[idx], self.target_subs[idx]


def train(data_path, model_path="models/fast_model_distill.pt", epochs=20, batch_size=128, lr=1e-3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    dataset = DistillDataset(data_path)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = FastMoveModel().to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)

    criterion_type = nn.CrossEntropyLoss()
    criterion_sub = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        total_acc_type = 0
        total_acc_sub = 0

        for obs, target_type, target_sub in loader:
            obs, target_type, target_sub = obs.to(device), target_type.to(device), target_sub.to(device)

            # Forward
            type_logits, sub_logits, _ = model.get_heads(obs)

            # Loss
            loss_type = criterion_type(type_logits, target_type)

            # For the sub-head, we need to gather the correct type's sub-logits
            # sub_logits is (B, 1800) -> (B, 18, 100)
            sub_logits_reshaped = sub_logits.view(-1, 18, 100)
            # Gather sub-logits for the SPECIFIC TARGET TYPE
            # target_type: (B,)
            # gathered: (B, 100)
            gathered_sub_logits = sub_logits_reshaped[torch.arange(obs.size(0)), target_type]

            loss_sub = criterion_sub(gathered_sub_logits, target_sub)

            loss = loss_type + loss_sub

            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            # Accuracies
            acc_type = (torch.argmax(type_logits, dim=1) == target_type).float().mean().item()
            acc_sub = (torch.argmax(gathered_sub_logits, dim=1) == target_sub).float().mean().item()
            total_acc_type += acc_type
            total_acc_sub += acc_sub

        avg_loss = total_loss / len(loader)
        avg_acc_type = total_acc_type / len(loader)
        avg_acc_sub = total_acc_sub / len(loader)

        print(
            f"Epoch {epoch + 1}/{epochs} | Loss: {avg_loss:.4f} | Acc Type: {avg_acc_type:.4f} | Acc Sub: {avg_acc_sub:.4f}"
        )

    # Save
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/distill_data.npz")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    if os.path.exists(args.data):
        train(args.data, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
    else:
        print(f"Data file {args.data} not found. Run generate_distillation_data.py first.")
