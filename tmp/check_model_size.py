import torch
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.alphazero.alphanet import AlphaNet

def check_size():
    model = AlphaNet()
    path = "model_size_test.pt"
    torch.save(model.state_dict(), path)
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"Model File Size: {size_mb:.2f} MB")
    
    # Analyze where the weights are
    total_params = sum(p.numel() for p in model.parameters())
    policy_params = sum(p.numel() for p in model.policy_head.parameters())
    print(f"Total Parameters: {total_params:,}")
    print(f"Policy Head Parameters: {policy_params:,} ({policy_params/total_params*100:.1f}%)")
    
    # os.remove(path)

if __name__ == "__main__":
    check_size()
