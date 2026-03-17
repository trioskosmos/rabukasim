import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

# Add project root and relevant subdirectories to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import engine_rust

from alphazero.alphanet import AlphaNet


def analyze_json_state(json_path, model_path=None):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 1. Load Data & Engine
    print("Loading cards_compiled.json...")
    data_path = os.path.join(PROJECT_ROOT, "data", "cards_compiled.json")
    with open(data_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))

    # 2. Load Model
    model = AlphaNet().to(device)
    if not model_path:
        model_path = os.path.join(PROJECT_ROOT, "alphazero", "training", "firstrun.pt")

    if os.path.exists(model_path):
        print(f"Loading weights from {model_path}...")
        try:
            model.load_state_dict(torch.load(model_path, map_location=device))
        except Exception as e:
            print(f"Warning: Incompatible checkpoint: {e}. Trying with strict=False.")
            model.load_state_dict(torch.load(model_path, map_location=device), strict=False)
    else:
        print(f"ERROR: Checkpoint {model_path} not found!")
        return

    model.eval()
    print("Model loaded successfully.")

    # 3. Load Input State
    print(f"Applying state from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        state_json = f.read()

    state = engine_rust.PyGameState(db_engine)
    try:
        state.apply_state_json(state_json)
    except Exception as e:
        print(f"ERROR: Failed to apply state JSON: {e}")
        return

    # 4. Inference
    legal_ids = state.get_legal_action_ids()
    if not legal_ids:
        print("No legal actions found for this state.")
        return

    # Get observation tensor from engine
    obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
    obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)

    # Create mask
    mask_np = np.zeros((1, 22000), dtype=np.bool_)
    mask_np[0, legal_ids] = True
    mask = torch.from_numpy(mask_np).to(device)

    with torch.no_grad():
        policy_logits, value = model(obs, mask=mask)
        probs = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
        logits = policy_logits.cpu().numpy()[0]
        v_results = value.cpu().numpy()[0]

    # 5. Output Results
    print("\n--- Analysis Results ---")
    print(f"Phase: {state.phase} | Current Player: {state.current_player}")
    print("Model Predictions:")
    print(f"  - Win Probability: {torch.sigmoid(torch.tensor(v_results[0])).item():.4f}")
    print(f"  - Momentum:        {v_results[1]:.4f}")
    print(f"  - Efficiency:      {v_results[2]:.4f}")

    print(f"\n{'ActionID':<10} | {'Logit':>10} | {'Prob':>10} | {'Label'}")
    print("-" * 80)

    # Sort by probability
    results = []
    for aid in legal_ids:
        results.append(
            {"id": aid, "logit": float(logits[aid]), "prob": float(probs[aid]), "label": state.get_action_label(aid)}
        )

    results.sort(key=lambda x: x["prob"], reverse=True)

    for r in results:
        print(f"{r['id']:<10} | {r['logit']:>10.4f} | {r['prob']:>10.4f} | {r['label']}")

    print("-" * 80)
    print(f"Total legal actions: {len(legal_ids)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze model logits for a given board state JSON.")
    parser.add_argument("json_path", help="Path to the board state JSON file.")
    parser.add_argument("--model", help="Path to the model checkpoint (optional).")

    args = parser.parse_args()
    analyze_json_state(args.json_path, args.model)
