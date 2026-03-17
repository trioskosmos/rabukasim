import json
import os
import sys
import time

import torch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_rust
from ai.benchmark_decks import parse_deck
from ai.train import AlphaNet


def profile_detailed(num_steps=100, sims=100):
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)
    db = engine_rust.PyCardDatabase(db_content)

    # Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = "ai/models/alphanet_best.pt"
    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location=device)
        model = AlphaNet(policy_size=checkpoint.get("policy_head_fc.bias").shape[0]).to(device)
        model.load_state_dict(checkpoint)
        model.eval()
    else:
        print("Model not found, skipping inference profiling.")
        model = None

    # Decks
    deck_paths = ["ai/decks/muse_cup.txt", "ai/decks/aqours_cup.txt"]
    decks = []
    for dp in deck_paths:
        if os.path.exists(dp):
            decks.append(parse_deck(dp, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})))

    if not decks:
        return

    game = engine_rust.PyGameState(db)
    p0_deck, p0_lives = decks[0]
    p1_deck, p1_lives = decks[1]
    game.initialize_game(p0_deck, p1_deck, [0] * 10, [0] * 10, p0_lives, p1_lives)

    timers = {"encoding": [], "inference": [], "mcts": [], "engine_step": [], "get_legal": []}

    print(f"Profiling {num_steps} iterations...")

    for _ in range(num_steps):
        if game.is_terminal():
            game.initialize_game(p0_deck, p1_deck, [0] * 10, [0] * 10, p0_lives, p1_lives)

        # 1. Encoding
        t0 = time.perf_counter()
        encoded = game.encode_state(db)
        timers["encoding"].append(time.perf_counter() - t0)

        # 2. Inference
        if model:
            t0 = time.perf_counter()
            with torch.no_grad():
                state_tensor = torch.FloatTensor(encoded).unsqueeze(0).to(device)
                model(state_tensor)
            timers["inference"].append(time.perf_counter() - t0)

        # 3. MCTS
        t0 = time.perf_counter()
        suggestions = game.get_mcts_suggestions(sims, engine_rust.SearchHorizon.TurnEnd)
        timers["mcts"].append(time.perf_counter() - t0)

        # 4. Legal Actions
        t0 = time.perf_counter()
        legal = game.get_legal_action_ids()
        timers["get_legal"].append(time.perf_counter() - t0)

        # 5. Engine Step
        action = suggestions[0][0] if suggestions else 0
        t0 = time.perf_counter()
        try:
            game.step(action)
        except:
            game.initialize_game(p0_deck, p1_deck, [0] * 10, [0] * 10, p0_lives, p1_lives)
        timers["engine_step"].append(time.perf_counter() - t0)

    print("\nDetailed Bottleneck Analysis:")
    print(f"{'Process':<15} | {'Avg Time':<12} | {'Max Time':<12}")
    print("-" * 45)
    for name, values in timers.items():
        if values:
            avg = sum(values) / len(values) * 1000
            mx = max(values) * 1000
            print(f"{name:<15} | {avg:>8.2f} ms | {mx:>8.2f} ms")


if __name__ == "__main__":
    profile_detailed()
