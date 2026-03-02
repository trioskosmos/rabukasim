import torch
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphazero.alphanet import AlphaNet
import engine_rust

# No longer needing overnight_pure_zero for basic smoke test

def smoke_test():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Testing v1.pt on {device}...")
    
    # 1. Load Model
    model = AlphaNet().to(device)
    checkpoint = "alphazero/v1.pt"
    if not os.path.exists(checkpoint):
        print(f"ERROR: {checkpoint} not found")
        return
        
    print("Loading weights (strict=False)...")
    model.load_state_dict(torch.load(checkpoint, map_location=device), strict=False)
    model.eval()
    print("Model loaded.")

    # 2. Setup Engine
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_json = f.read()
    db_engine = engine_rust.PyCardDatabase(db_json)
    state = engine_rust.PyGameState(db_engine)
    
    # Minimal init
    p0_deck = [101] * 48 + [2001] * 12
    p1_deck = [101] * 48 + [2001] * 12
    energy = [38] * 12
    state.initialize_game(p0_deck, p1_deck, energy, energy, [], [])
    
    # 3. Predict
    print("Getting observation...")
    obs = np.array(state.to_alphazero_tensor()).astype(np.float32)
    obs_t = torch.from_numpy(obs).unsqueeze(0).to(device)
    
    legal_ids = state.get_legal_action_ids()
    mask = torch.zeros((1, 16384), dtype=torch.bool).to(device)
    for aid in legal_ids:
        mask[0, aid] = True
        
    print(f"Running forward pass with {len(legal_ids)} legal actions...")
    with torch.no_grad():
        policy, value = model(obs_t, mask=mask)
        
    print(f"Prediction successful!")
    print(f"Value: {value.item():.4f}")
    best_action = int(torch.argmax(policy).item())
    print(f"Best Action ID: {best_action} ({state.get_action_label(best_action)})")
    
    # 4. Step
    print("Executing one step...")
    state.step(best_action)
    state.auto_step(db_engine)
    print(f"Step completed. Turn: {state.turn}")
    print("SMOKE TEST PASSED.")

if __name__ == "__main__":
    smoke_test()
