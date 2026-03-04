import os
import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
# Ensure PYTHONPATH is also set for engine_rust.pyd detection
os.environ["PYTHONPATH"] = f".;{os.environ.get('PYTHONPATH', '')}"

import torch
import torch.optim as optim
import engine_rust
from alphazero.alphanet import AlphaNet

def test_training_step():
    print("--- Pipeline Verification ---")
    
    # 1. Load Data
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)
    print("1. Card Database Loaded.")

    # 2. Initialize Model (Hierarchical Head)
    model = AlphaNet()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    print(f"2. AlphaNet Initialized (Global Dim: {model.global_dim}).")

    # 3. Get Real observation from Engine
    state = engine_rust.PyGameState(db)
    obs = torch.tensor(state.to_alphazero_tensor()).unsqueeze(0) # (1, 20500)
    print(f"3. Rust Observation Generated (Shape: {obs.shape}).")
    
    # Verify normalization (should be roughly in 0-1 range)
    print(f"   Obs Max: {obs.max().item():.3f}, Obs Mean: {obs.mean().item():.3f}")

    # 4. Target Values (Mock for verification)
    # Target value = 1.0 (Win), Target Action = 0 (Pass)
    target_v = torch.tensor([[1.0]])
    target_p = torch.zeros(1, 16384)
    target_p[0, 0] = 1.0 

    # 5. Forward Pass
    print("4. Executing Forward Pass...")
    p_logits, v_pred = model(obs)
    
    # 6. Compute Loss
    v_loss = torch.nn.functional.mse_loss(v_pred, target_v)
    # Simple cross entropy for policy
    p_log_probs = torch.nn.functional.log_softmax(p_logits, dim=1)
    p_loss = -torch.sum(p_log_probs * target_p)
    total_loss = v_loss + p_loss
    print(f"5. Total Loss: {total_loss.item():.4f}")

    # 7. Backward Pass (Proof of learning capability)
    print("6. Executing Backward Pass...")
    optimizer.zero_grad()
    total_loss.backward()
    
    # Check if gradients exist in the heads
    type_grad = model.policy_type_head[0].weight.grad.abs().mean().item()
    sub_grad = model.policy_sub_head[2].weight.grad.abs().mean().item()
    
    print(f"7. Gradient Check:")
    print(f"   - Type Head Avg Grad: {type_grad:.8f}")
    print(f"   - Sub Head Avg Grad: {sub_grad:.8f}")

    if total_loss.item() > 0 and type_grad > 0:
        print("\nSUCCESS: The pipeline is functional. Gradients are flowing to the new Hierarchical Head.")
    else:
        print("\nFAILURE: Gradient flow issue.")

if __name__ == "__main__":
    test_training_step()
