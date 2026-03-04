import torch
import torch.nn as nn
import time
import numpy as np
from alphazero.alphanet import AlphaNet

def benchmark_inference(device):
    print(f"\n--- Inference Benchmark ({device}) ---")
    model = AlphaNet().to(device)
    model.eval()
    
    # Warmup
    dummy_input = torch.randn(64, 20500).to(device)
    with torch.no_grad():
        for _ in range(10):
            model(dummy_input)
    
    # Latency: Batch Size 1
    input_bs1 = torch.randn(1, 20500).to(device)
    start = time.time()
    for _ in range(100):
        with torch.no_grad():
            model(input_bs1)
    latency = (time.time() - start) / 100 * 1000
    print(f"Latency (BS=1): {latency:.2f} ms")
    
    # Throughput: Batch Size 64
    input_bs64 = torch.randn(64, 20500).to(device)
    start = time.time()
    for _ in range(50):
        with torch.no_grad():
            model(input_bs64)
    throughput = (64 * 50) / (time.time() - start)
    print(f"Throughput (BS=64): {throughput:.2f} states/sec")

def benchmark_training(device):
    print(f"\n--- Training Benchmark ({device}) ---")
    model = AlphaNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    
    bs = 64
    obs = torch.randn(bs, 20500).to(device)
    mask = torch.ones(bs, 22000, dtype=torch.bool).to(device)
    pol_target = torch.randn(bs, 22000).to(device)
    val_target = torch.randn(bs, 3).to(device)
    
    # Warmup
    for _ in range(5):
        optimizer.zero_grad()
        p, v = model(obs, mask=mask)
        loss = torch.nn.functional.mse_loss(v, val_target)
        loss.backward()
        optimizer.step()
        
    start = time.time()
    num_iters = 50
    for _ in range(num_iters):
        optimizer.zero_grad()
        p, v = model(obs, mask=mask)
        loss = torch.nn.functional.mse_loss(v, val_target)
        loss.backward()
        optimizer.step()
        
    iter_time = (time.time() - start) / num_iters
    print(f"Train Step Time (BS={bs}): {iter_time*1000:.2f} ms")
    print(f"Train Throughput: {bs / iter_time:.2f} states/sec")

if __name__ == "__main__":
    devices = ["cpu"]
    if torch.cuda.is_available():
        devices.append("cuda")
        
    for device_name in devices:
        device = torch.device(device_name)
        benchmark_inference(device)
        benchmark_training(device)
        # Clear cache for next device
        if device_name == "cuda":
            torch.cuda.empty_cache()
