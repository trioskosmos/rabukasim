import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from alphanet import AlphaNet
from train import AlphaDataset

def debug_train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = AlphaNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    dataset = AlphaDataset("trajectories.npz")
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    print("Starting debug training loop...")
    for i, (obs, policy_targets, mask, value_targets) in enumerate(loader):
        obs = obs.to(device)
        policy_targets = policy_targets.to(device)
        mask = mask.to(device)
        value_targets = value_targets.to(device)
        
        optimizer.zero_grad()
        
        policy_preds, value_preds = model(obs, mask=mask)
        
        if torch.isnan(policy_preds).any():
            print(f"Step {i}: policy_preds has NaN FIRST! Max input obs: {obs.max().item()}, Min: {obs.min().item()}")
            break
            
        value_loss = F.mse_loss(value_preds, value_targets)
        
        log_probs = torch.log_softmax(policy_preds, dim=1)
        log_probs = log_probs.masked_fill(~mask, 0.0)
        policy_loss = -(policy_targets * log_probs).sum(dim=1).mean()
        
        loss = value_loss + policy_loss
        
        print(f"Step {i}: Total loss: {loss.item():.4f} (Val: {value_loss.item():.4f}, Pol: {policy_loss.item():.4f})")
        
        if torch.isnan(loss):
            print(f"Step {i}: LOSS IS NAN!")
            break
            
        optimizer.zero_grad()
        value_loss.backward(retain_graph=True)
        v_nan = False
        for name, p in model.named_parameters():
            if p.grad is not None and torch.isnan(p.grad).any():
                print(f"Step {i}: VALUE gradient is NaN in {name}")
                v_nan = True
                break
                
        optimizer.zero_grad()
        policy_loss.backward()
        for name, p in model.named_parameters():
            if p.grad is not None and torch.isnan(p.grad).any():
                print(f"Step {i}: POLICY gradient is NaN in {name}")
                break
        
        optimizer.step()
        break
        

if __name__ == "__main__":
    debug_train()
