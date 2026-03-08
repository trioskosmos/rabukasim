import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from alphazero.vanilla_net import HighFidelityAlphaNet

class AlphaDataset(Dataset):
    def __init__(self, data_path):
        data = np.load(data_path)
        self.obs = torch.from_numpy(data['obs']).float()
        self.policy = torch.from_numpy(data['policy']).float()
        self.mask = torch.from_numpy(data['mask']).bool()
        self.value = torch.from_numpy(data['value']).float()
            
    def __len__(self):
        return len(self.obs)
        
    def __getitem__(self, idx):
        return self.obs[idx], self.policy[idx], self.mask[idx], self.value[idx].unsqueeze(0)

def train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0
    total_value_loss = 0
    total_policy_loss = 0
    
    for obs, policy_targets, mask, value_targets in loader:
        obs = obs.to(device)
        policy_targets = policy_targets.to(device)
        mask = mask.to(device)
        value_targets = value_targets.to(device)
        
        optimizer.zero_grad()
        
        policy_logits, value_preds = model(obs, mask=mask)
        
        # AlphaZero Losses
        value_loss = F.mse_loss(value_preds, value_targets)
        log_probs = F.log_softmax(policy_logits, dim=1)
        policy_loss = F.kl_div(log_probs, policy_targets, reduction='batchmean')
        
        loss = value_loss + policy_loss
        
        if torch.isnan(loss):
            continue
            
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item()
        total_value_loss += value_loss.item()
        total_policy_loss += policy_loss.item()

    num_batches = len(loader)
    if num_batches == 0:
        return {"loss": 0.0, "value": 0.0, "policy": 0.0}
    return {
        "loss": total_loss / num_batches,
        "value": total_value_loss / num_batches,
        "policy": total_policy_loss / num_batches,
    }

def run_training(data_path="vanilla_trajectories.npz", epochs=100, batch_size=32, lr=0.001):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"--- Starting Vanilla Training Session ---")
    print(f"Device: {device}")
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    dataset = AlphaDataset(data_path)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    model = HighFidelityAlphaNet(input_dim=800, num_actions=128).to(device)
    
    checkpoint_dir = Path("alphazero/checkpoints")
    checkpoint_dir.mkdir(exist_ok=True, parents=True)
    checkpoint_path = checkpoint_dir / "vanilla_latest.pt"
    
    if checkpoint_path.exists():
        print(f"Resuming from {checkpoint_path}...")
        try:
            model.load_state_dict(torch.load(str(checkpoint_path), map_location=device))
        except Exception as e:
            print(f"Warning: Could not load checkpoint: {e}")
        
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    
    for epoch in range(epochs):
        stats = train_epoch(model, loader, optimizer, device)
        
        # Calculate Policy Accuracy
        correct = 0
        total = 0
        with torch.no_grad():
            for obs, pol_t, mask, val_t in loader:
                obs = obs.to(device)
                pol_t = pol_t.to(device)
                mask = mask.to(device)
                p_logits, _ = model(obs, mask=mask)
                # Filter out illegal moves for accuracy calculation
                p_logits[~mask] = -1e9
                correct += (torch.argmax(p_logits, dim=1) == torch.argmax(pol_t, dim=1)).sum().item()
                total += obs.size(0)
        
        pol_acc = (correct / total) * 100 if total > 0 else 0.0
            
        print(f"Epoch {epoch+1:3d} | Loss: {stats['loss']:.4f} [V:{stats['value']:.3f} P:{stats['policy']:.3f}] | Acc: {pol_acc:.1f}%")
        
        if (epoch + 1) % 10 == 0:
            torch.save(model.state_dict(), str(checkpoint_path))
        
    torch.save(model.state_dict(), str(checkpoint_path))
    print(f"--- Training complete. Final model saved to {checkpoint_path} ---")

if __name__ == "__main__":
    run_training()
