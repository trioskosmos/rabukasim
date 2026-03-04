import torch
import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from alphazero.alphanet import AlphaNet

def count_parameters():
    model = AlphaNet()
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Total Parameters: {total_params:,}")
    print(f"Trainable Parameters: {trainable_params:,}")
    
    # Break down by component
    print("\n--- Component Breakdown ---")
    for name, module in model.named_children():
        params = sum(p.numel() for p in module.parameters())
        print(f"{name}: {params:,}")

if __name__ == "__main__":
    count_parameters()
