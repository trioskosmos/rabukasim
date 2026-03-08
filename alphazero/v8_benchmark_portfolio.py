import torch
import time
from vanilla_net import HighFidelityAlphaNet

def benchmark(input_dim, batch_size=64, iterations=100):
    model = HighFidelityAlphaNet(input_dim=input_dim)
    model.eval()
    
    x = torch.randn(batch_size, input_dim)
    
    # Warmup
    for _ in range(10):
        _ = model(x)
        
    start_time = time.time()
    for _ in range(iterations):
        _ = model(x)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / iterations
    return avg_time

if __name__ == "__main__":
    print("Benchmarking Training Speed (Forward Pass)...")
    
    # We compare 791 (Previous High-Fi) vs 800 (New Portfolio-Aware)
    time_791 = benchmark(791)
    time_800 = benchmark(800)
    
    print(f"Avg Time (791 dim): {time_791:.6f}s")
    print(f"Avg Time (800 dim): {time_800:.6f}s")
    
    diff = (time_800 - time_791) / time_791 * 100
    print(f"Overhead: {diff:.2f}%")
    
    if abs(diff) < 5:
        print("Success: Performance impact is negligible (<5%).")
    else:
        print(f"Note: Performance diff is {diff:.2f}%.")
