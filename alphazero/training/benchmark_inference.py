import torch
import time
import numpy as np
import sys
from pathlib import Path

# Add project root to find alphazero module
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from alphazero.alphanet import AlphaNet

def benchmark():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Benchmarking on: {device}")
    
    # 1. Setup Model
    model = AlphaNet(num_layers=10, embed_dim=512).to(device)
    model.eval()
    
    # 2. Setup Dummy Data (Shape: 1, 20500)
    obs_dim = 20500
    batch_size = 1
    dummy_obs = torch.randn(batch_size, obs_dim).to(device)
    dummy_mask = torch.ones(batch_size, model.num_actions, dtype=torch.bool).to(device)
    
    # Warmup
    print("Warming up GPU (5 iterations)...")
    for i in range(5):
        with torch.no_grad():
            _ = model(dummy_obs, mask=dummy_mask)
        print(f"Warmup {i+1}/5 done.")
            
    # 3. Latency Benchmark
    iters = 20
    print(f"Running latency benchmark ({iters} iterations)...")
    torch.cuda.synchronize()
    start = time.time()
    
    for i in range(iters):
        with torch.no_grad():
            _ = model(dummy_obs, mask=dummy_mask)
        if (i+1) % 5 == 0:
            print(f"Iter {i+1}/{iters} done.")
            
    torch.cuda.synchronize()
    total_time = time.time() - start
    avg_latency = (total_time / iters) * 1000 # ms
    fps = iters / total_time
    
    print("\n--- Model Benchmark Results (Batch=1) ---")
    print(f"Total Time for {iters} iterations: {total_time:.3f}s")
    print(f"Average Latency per Move: {avg_latency:.2f} ms")
    print(f"Throughput: {fps:.2f} moves/sec")
    
    # 4. Batch Benchmark (What training sees)
    batch_256 = 256
    dummy_obs_large = torch.randn(batch_256, obs_dim).to(device)
    dummy_mask_large = torch.ones(batch_256, model.num_actions, dtype=torch.bool).to(device)
    
    torch.cuda.synchronize()
    start = time.time()
    with torch.no_grad():
        _ = model(dummy_obs_large, mask=dummy_mask_large)
    torch.cuda.synchronize()
    batch_time = time.time() - start
    
    print(f"\n--- Batch Benchmark (Batch=256) ---")
    print(f"Batch Latency: {batch_time * 1000:.2f} ms")
    print(f"Effective Throughput: {batch_256 / batch_time:.2f} moves/sec")

if __name__ == "__main__":
    benchmark()
