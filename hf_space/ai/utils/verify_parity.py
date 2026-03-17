import os
import sys

import numpy as np
import torch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.models.training_config import POLICY_SIZE
from ai.training.train import AlphaNet


def verify_parity():
    # 1. Setup Models
    model_path_pt = "ai/models/alphanet_best.pt"
    model_path_onnx = "ai/models/alphanet.onnx"

    device = torch.device("cpu")
    checkpoint = torch.load(model_path_pt, map_location=device)
    state_dict = checkpoint["model_state"] if "model_state" in checkpoint else checkpoint

    model_pt = AlphaNet(policy_size=POLICY_SIZE)
    model_pt.load_state_dict(state_dict)
    model_pt.eval()

    nmcts_rust = engine_rust.PyNeuralMCTS(model_path_onnx)

    # 2. Setup Game
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)

    # Simple init
    p0_deck = [124, 127] * 20
    p1_deck = [124, 127] * 20
    p0_lives = [1024, 1025, 1027]
    p1_lives = [1024, 1025, 1027]
    game.initialize_game(p0_deck, p1_deck, [20000] * 10, [20000] * 10, p0_lives, p1_lives)

    # 3. Compare Encoding
    obs_rust = np.array(game.get_observation(), dtype=np.float32)

    # 4. Compare Inference
    with torch.no_grad():
        logits_pt, val_pt = model_pt(torch.from_numpy(obs_rust).unsqueeze(0))
        logits_pt = logits_pt.numpy()[0]
        val_pt = val_pt.numpy()[0][0]

    print(f"Observation Size: {len(obs_rust)}")
    print(f"Value (Python): {val_pt:.6f}")

    # Note: We need a way to get raw evaluate results from Rust for deep parity
    # But for now, we'll check suggestions as a proxy
    num_sims = 100
    suggestions = nmcts_rust.get_suggestions(game, num_sims)

    print("\nTop Python Actions (Logits):")
    top_pt = np.argsort(logits_pt)[::-1][:5]
    for i in top_pt:
        print(f"  Action {i:4d}: {logits_pt[i]:.4f}")

    print("\nRust Suggestions (1 simulation):")
    for action, score, visits in suggestions[:5]:
        print(f"  Action {action:4d}: Score {score:.4f}, Visits {visits}")


if __name__ == "__main__":
    verify_parity()
