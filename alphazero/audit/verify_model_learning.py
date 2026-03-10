import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import engine_rust
from tools.alphazero.alphanet import AlphaNet


def analyze_learning():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaNet().to(device)

    checkpoint_path = "alphanet_latest.pt"
    if not os.path.exists(checkpoint_path):
        print("No model found.")
        return

    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))

    def load_decks():
        from tools.alphazero.overnight_pure_zero import load_tournament_decks

        return load_tournament_decks(full_db)

    decks = load_decks()
    d0 = random.choice(decks)
    d1 = random.choice(decks)

    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])

    print("--- AI vs Random/MCTS Analysis ---")

    matches = 0
    total_steps = 0

    while not state.is_terminal() and state.turn < 20:
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        # 1. MCTS Best Move (The "Truth" for this experiment)
        eval_mode = engine_rust.EvalMode.TerminalOnly
        # Give it a bit more search for better ground truth
        suggestions = state.search_mcts(
            512, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), eval_mode, None, None
        )
        if not suggestions:
            break

        mcts_best_id = suggestions[0][0]
        mcts_label = state.get_action_label(mcts_best_id)

        # 2. Model Prediction
        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        mask = torch.zeros((1, 16384), dtype=torch.bool).to(device)
        for aid in legal_ids:
            mask[0, aid] = True

        with torch.no_grad():
            policy_logits, value_pred = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]

        model_best_id = np.argmax(policy)
        model_label = state.get_action_label(int(model_best_id))

        print(f"[Turn {state.turn}]")
        print(f"  MCTS Truth : {mcts_label} (Sims: {suggestions[0][2]})")
        print(f"  AI Guess   : {model_label} (Prob: {policy[model_best_id]:.3f})")
        print(f"  Value Pred : {value_pred.item():.3f}")

        if mcts_best_id == model_best_id:
            matches += 1
            print("  ✅ MATCH!")
        else:
            # Check if model's choice was at least in the top half of MCTS suggestions
            mcts_ids = [s[0] for s in suggestions]
            if model_best_id in mcts_ids:
                rank = mcts_ids.index(model_best_id)
                print(f"  ❌ MISMATCH (Model choice ranked #{rank + 1} by MCTS)")
            else:
                print("  ❌ MISMATCH (Model choice was not selected by MCTS)")

        total_steps += 1
        state.step(mcts_best_id)
        state.auto_step(db_engine)

    accuracy = (matches / total_steps) * 100 if total_steps > 0 else 0
    print(f"\nSummary: AI Prediction Accuracy against MCTS: {accuracy:.1f}%")
    print(f"Over {total_steps} turns.")


if __name__ == "__main__":
    main_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(main_dir))
    analyze_learning()
