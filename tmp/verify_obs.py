import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import engine_rust
import json
import torch
from alphazero.alphanet import AlphaNet

def test_rust_tensor():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)
    state = engine_rust.PyGameState(db)
    tensor = state.to_alphazero_tensor()
    print(f"Rust Tensor Size: {len(tensor)}")
    return len(tensor)

def test_alphanet_forward():
    model = AlphaNet()
    dummy_input = torch.randn(1, 20500)
    p, v = model(dummy_input)
    print(f"AlphaNet Forward Policy Shape: {p.shape}")
    print(f"AlphaNet Forward Value Shape: {v.shape}")

if __name__ == "__main__":
    rust_size = test_rust_tensor()
    test_alphanet_forward()
    if rust_size == 20500:
        print("SUCCESS: Observation Pipeline Aligned.")
    else:
        print(f"FAILURE: Expected 20500, got {rust_size}")
