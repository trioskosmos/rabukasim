import gc
import glob
import os
import random
import sys

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ai.models.network_torch import TransformerCardNet


class ChunkDataset(Dataset):
    """Dataset for a single chunk of data."""

    def __init__(self, states, policies, winners, scores, turns):
        self.states = torch.as_tensor(states, dtype=torch.float32)
        self.policies = torch.as_tensor(policies, dtype=torch.float32)
        self.winners = torch.as_tensor(winners, dtype=torch.float32).view(-1, 1)
        self.scores = torch.as_tensor(scores, dtype=torch.float32).view(-1, 1)
        self.turns = torch.as_tensor(turns, dtype=torch.float32).view(-1, 1)

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return (self.states[idx], self.policies[idx], self.winners[idx], self.scores[idx], self.turns[idx])


def get_data_from_files(files):
    """Loads and concatenates data from a list of files."""
    all_states, all_policies, all_winners = [], [], []
    all_scores, all_turns = [], []

    for f in files:
        data = np.load(f)
        all_states.append(data["states"])
        all_policies.append(data["policies"])
        all_winners.append(data["winners"])
        all_scores.append(data["scores"])
        all_turns.append(data["turns_left"])

    return (
        np.concatenate(all_states),
        np.concatenate(all_policies),
        np.concatenate(all_winners),
        np.concatenate(all_scores),
        np.concatenate(all_turns),
    )


def train(data_pattern, epochs=20, batch_size=16384, lr=0.001, resume_path=None):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device} with batch size {batch_size}")

    # Locate all matching files
    all_files = sorted(glob.glob(data_pattern))
    if not all_files:
        print(f"Error: No files found matching {data_pattern}")
        return

    print(f"Found {len(all_files)} data chunks.")

    # Reserve ~10% of files for validation (exclusive)
    # If only 1 file, use it for BOTH training and validation
    if len(all_files) == 1:
        train_files = val_files = all_files
    else:
        val_count = max(1, len(all_files) // 10)
        # Ensure at least one training file exists
        if val_count >= len(all_files):
            val_count = 0

        rand_gen = random.Random(42)
        shuffled_files = all_files.copy()
        rand_gen.shuffle(shuffled_files)

        train_files = shuffled_files[:-val_count] if val_count > 0 else shuffled_files
        val_files = shuffled_files[-val_count:] if val_count > 0 else shuffled_files

    print(f"Split: {len(train_files)} training files, {len(val_files)} validation files.")

    # Initialize model
    model = TransformerCardNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, "min", patience=3, factor=0.5)

    # Loss functions
    policy_loss_fn = nn.CrossEntropyLoss(reduction="none")
    win_loss_fn = nn.BCELoss()
    mse_loss_fn = nn.MSELoss()

    best_val_loss = float("inf")
    start_epoch = 0

    # Resume Logic
    if resume_path and os.path.exists(resume_path):
        print(f" -> Resuming from checkpoint: {resume_path}")
        checkpoint = torch.load(resume_path, map_location=device)
        model.load_state_dict(checkpoint["model_state"])
        if "optimizer_state" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state"])
        if "scheduler_state" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler_state"])
        start_epoch = checkpoint.get("epoch", -1) + 1
        best_val_loss = checkpoint.get("val_loss", float("inf"))
        print(f" -> Starting from epoch {start_epoch + 1}")

    try:
        for epoch in range(start_epoch, epochs):
            model.train()
            train_losses = {"poly": 0, "win": 0, "score": 0, "turn": 0}
            correct_policy = 0
            total_policy = 0

            current_train_files = train_files.copy()
            random.shuffle(current_train_files)

            pbar = tqdm(current_train_files, desc=f"Epoch {epoch + 1}/{epochs}")
            for f_idx, f_path in enumerate(pbar):
                try:
                    s, pol, w, sc, tn = get_data_from_files([f_path])
                    chunk_dataset = ChunkDataset(s, pol, w, sc, tn)
                    chunk_loader = DataLoader(chunk_dataset, batch_size=batch_size, shuffle=True)

                    for states, target_p, target_w, target_s, target_t in chunk_loader:
                        states = states.to(device)
                        target_p = target_p.to(device)
                        target_w = target_w.to(device)
                        target_s = target_s.to(device)
                        target_t = target_t.to(device)

                        optimizer.zero_grad()

                        # Forward pass
                        p_soft, w_pred, s_pred, t_pred = model(states)

                        # 1. Policy Loss (Weighted)
                        # Avoid log(0) by using logits or CrossEntropy internally
                        # But TransformerCardNet returns softmax, so we use NLL or manual CE
                        # For simplicity, let's use the probabilities directly or re-logit
                        p_loss_raw = -torch.sum(target_p * torch.log(p_soft + 1e-8), dim=1)

                        # Weight non-pass actions higher
                        target_argmax = torch.max(target_p, dim=1)[1]
                        weights = torch.ones(states.size(0), device=device)
                        weights[target_argmax != 0] = 5.0
                        p_loss = (p_loss_raw * weights).mean()

                        # 2. Value Losses
                        loss_win = win_loss_fn(w_pred, target_w)
                        loss_score = mse_loss_fn(s_pred, target_s)
                        loss_turn = mse_loss_fn(t_pred, target_t)

                        total_loss = p_loss + loss_win + loss_score + loss_turn
                        total_loss.backward()
                        optimizer.step()

                        train_losses["poly"] += p_loss.item()
                        train_losses["win"] += loss_win.item()
                        train_losses["score"] += loss_score.item()
                        train_losses["turn"] += loss_turn.item()

                        _, pred_action = torch.max(p_soft, 1)
                        _, target_action = torch.max(target_p, 1)
                        correct_policy += (pred_action == target_action).sum().item()
                        total_policy += states.size(0)

                    pbar.set_postfix(
                        {
                            "acc": f"{100 * correct_policy / total_policy:.1f}%",
                            "win": f"{train_losses['win'] / (f_idx + 1):.3f}",
                        }
                    )

                    del chunk_dataset, chunk_loader, s, pol, w, sc, tn
                    gc.collect()
                except Exception as e:
                    print(f"Error processing chunk {f_path}: {e}")
                    continue

            # Validation
            model.eval()
            val_losses = {"poly": 0, "win": 0, "score": 0, "turn": 0}
            val_correct = 0
            val_total = 0
            num_batches_val = 0

            print(f" [Epoch {epoch + 1}] Validating...")
            with torch.no_grad():
                for f_path in val_files:
                    try:
                        s, pol, w, sc, tn = get_data_from_files([f_path])
                        val_chunk = ChunkDataset(s, pol, w, sc, tn)
                        val_loader = DataLoader(val_chunk, batch_size=batch_size, shuffle=False)

                        for states, target_p, target_w, target_s, target_t in val_loader:
                            states = states.to(device)
                            target_p = target_p.to(device)
                            target_w = target_w.to(device)
                            target_s = target_s.to(device)
                            target_t = target_t.to(device)

                            p_soft, w_pred, s_pred, t_pred = model(states)

                            p_loss_raw = -torch.sum(target_p * torch.log(p_soft + 1e-8), dim=1)
                            val_losses["poly"] += p_loss_raw.mean().item()
                            val_losses["win"] += win_loss_fn(w_pred, target_w).item()
                            val_losses["score"] += mse_loss_fn(s_pred, target_s).item()
                            val_losses["turn"] += mse_loss_fn(t_pred, target_t).item()

                            num_batches_val += 1
                            _, pred_action = torch.max(p_soft, 1)
                            _, target_action = torch.max(target_p, 1)
                            val_correct += (pred_action == target_action).sum().item()
                            val_total += states.size(0)

                        del val_chunk, val_loader, s, pol, w, sc, tn
                        gc.collect()
                    except Exception as e:
                        print(f"Error validating chunk {f_path}: {e}")

            if val_total > 0:
                avg_val_win = val_losses["win"] / num_batches_val
                avg_val_total = (val_losses["poly"] + val_losses["win"] + val_losses["score"]) / num_batches_val

                scheduler.step(avg_val_total)

                print(f"Epoch {epoch + 1} | Val WinLoss: {avg_val_win:.4f} | Acc: {100 * val_correct / val_total:.1f}%")

                checkpoint = {
                    "model_state": model.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "val_loss": avg_val_total,
                    "epoch": epoch,
                }
                torch.save(checkpoint, f"ai/models/transformer_epoch_{epoch + 1}.pt")

                if avg_val_total < best_val_loss:
                    best_val_loss = avg_val_total
                    torch.save(checkpoint, "ai/models/transformer_best.pt")

    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current state to ai/models/alphanet_interrupted.pt...")
        # Save complete state for resumption
        interrupted_state = {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict() if "scheduler" in locals() else None,
            "epoch": epoch if "epoch" in locals() else 0,
            "val_loss": best_val_loss,
        }
        torch.save(interrupted_state, "ai/models/alphanet_interrupted.pt")

    torch.save(model.state_dict(), "ai/models/alphanet_final.pt")
    print(f"Training complete. Best Val Loss: {best_val_loss:.4f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="ai/data/alphazero_nightly_chunk_*.npz")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16384)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument(
        "--resume", type=str, help="Path to checkpoint to resume from (e.g. ai/models/alphanet_interrupted.pt)"
    )
    args = parser.parse_args()

    if not os.path.exists("ai/models"):
        os.makedirs("ai/models")

    train(args.data, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, resume_path=args.resume)
