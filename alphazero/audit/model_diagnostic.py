import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

# Add root for engine
sys.path.insert(0, str(Path(__file__).parent.parent))

import engine_rust
from alphanet import AlphaNet


def analyze_model_probs():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaNet().to(device)
    checkpoint = os.path.join(os.path.dirname(__file__), "alphanet_latest.pt")
    if not os.path.exists(checkpoint):
        print(f"Model checkpoint not found at {checkpoint}!")
        return

    model.load_state_dict(torch.load(checkpoint, map_location=device))
    model.eval()

    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "cards_compiled.json")
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))

    # Load a few decks
    def load_decks():
        deck_dir = os.path.join(os.path.dirname(__file__), "..", "ai", "decks")
        print(f"Loading decks from {deck_dir}...")
        from engine.game.deck_utils import UnifiedDeckParser, load_deck_from_file

        parser = UnifiedDeckParser(full_db)
        decks = []
        files = os.listdir(deck_dir)
        print(f"Found files: {files}")
        for f in files:
            if f.endswith(".txt"):
                try:
                    path = os.path.join(deck_dir, f)
                    main, energy, counts, errs = load_deck_from_file(path, full_db)
                    if not main:
                        print(f"Empty deck or error in {f}: {errs}")
                        continue
                    # Resolve to IDs
                    members = []
                    lives = []
                    energy_ids = []

                    for cid in main:
                        cdata = parser.resolve_card(cid)
                        if not cdata:
                            continue
                        card_id = cdata["card_id"]
                        if cdata.get("type") == "Member":
                            members.append(card_id)
                        else:
                            lives.append(card_id)

                    for cid in energy:
                        cdata = parser.resolve_card(cid)
                        if cdata:
                            energy_ids.append(cdata["card_id"])

                    decks.append({"members": members, "lives": lives, "energy": energy_ids})
                    print(f"Loaded {f}")
                except Exception as e:
                    print(f"Failed to load {f}: {e}")
        return decks

    decks = load_decks()
    if not decks:
        print("No decks found!")
        return

    # Start a game and look at the first few states
    d0 = decks[0]
    d1 = decks[1]
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])

    print("--- MODEL DIAGNOSIS ---")
    for step in range(10):
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        mask = torch.zeros((1, 16384), dtype=torch.bool).to(device)
        for aid in legal_ids:
            mask[0, aid] = True

        with torch.no_grad():
            policy_logits, value = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]

        # Top 5 actions
        top_indices = np.argsort(policy)[-5:][::-1]
        print(f"\nStep {step}, Turn {state.turn}, Player {state.current_player}")
        print(f"Predicted Value: {value.item():.4f}")
        for idx in top_indices:
            print(f"Action {idx}: {policy[idx]:.4f}")

        # Step with top action
        state.step(int(top_indices[0]))
        state.auto_step(db_engine)
        if state.is_terminal():
            break


if __name__ == "__main__":
    analyze_model_probs()
