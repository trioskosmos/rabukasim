import torch
import time
import sys
from pathlib import Path

# Add project root to find alphazero module
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from alphazero.alphanet import AlphaNet

def debug_speed():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    print("Initializing model...")
    model = AlphaNet(num_layers=10, embed_dim=512).to(device)
    model.eval()
    
    print("Creating tensors...")
    x = torch.randn(1, 20500).to(device)
    m = torch.ones(1, 22000, dtype=torch.bool).to(device)
    
    print("Starting forward pass...")
    torch.cuda.synchronize()
    start = time.time()
    
    with torch.no_grad():
        p, v = model(x, mask=m)
    
    torch.cuda.synchronize()
    end = time.time()
    
    print(f"Forward pass completed in {end - start:.4f}s")
    print(f"Policy shape: {p.shape}, Value shape: {v.shape}")

if __name__ == "__main__":
    debug_speed()
