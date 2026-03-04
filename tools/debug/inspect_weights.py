import torch
import os

path = 'alphazero/training/alphanet_latest.pt'
if not os.path.exists(path):
    print(f"File not found: {path}")
else:
    sd = torch.load(path, map_location='cpu')
    print(f"--- Model Weights Statistics ({path}) ---")
    for k, v in list(sd.items())[:10]:
        if isinstance(v, torch.Tensor):
            print(f"{k:40s}: mean={v.mean():.4f}, std={v.std():.4f}, range=({v.min():.4f}, {v.max():.4f})")
