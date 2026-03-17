import sys
from pathlib import Path

# Add project root to sys.path first!
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

print("Step 0: sys.path updated")
import engine_rust
import torch

print(f"DEBUG: engine_rust loaded from {engine_rust.__file__}")

import json
import random

print("Step 1: Imports done")

from alphazero.vanilla_net import HighFidelityAlphaNet

# Configuration
FIXED_SEEDS = [101]  # Just one for debug
NUM_ACTIONS = 128
OBS_DIM = 800


def map_engine_to_vanilla(p_data, engine_id, initial_deck):
    # Simplified for debug
    if engine_id == 0:
        return 0
    if 20000 <= engine_id <= 20002:
        return 0  # RPS
    return -1


def run_benchmark(model_path=None):
    device = torch.device("cpu")  # Use CPU for debug speed

    # 1. Load DB
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)

    # 2. Load Model
    model = HighFidelityAlphaNet(input_dim=OBS_DIM, num_actions=NUM_ACTIONS).to(device)
    model.eval()

    # 3. Load Decks (Minimal)
    all_decks = [{"name": "debug", "cards": list(db.get_member_ids() * 60)[:60]}]
    energy = [38] * 12

    print("--- Running Debug Benchmark ---")

    for deck in all_decks:
        for seed in FIXED_SEEDS:
            state = engine_rust.PyGameState(db)
            print(f"DEBUG: State BEFORE init - Turn: {state.turn}, Phase: {state.phase}")
            state.initialize_game_with_seed(deck["cards"], deck["cards"], energy, energy, [], [], seed)
            print(
                f"DEBUG: State AFTER init - Turn: {state.turn}, Phase: {state.phase}, Terminal: {state.is_terminal()}"
            )

            initial_decks = [list(state.get_player(0).initial_deck), list(state.get_player(1).initial_deck)]
            print(f"DEBUG: Initial Deck len: {len(initial_decks[0])}")

            moves = 0
            while not state.is_terminal() and state.turn < 25 and moves < 100:
                legal = state.get_legal_action_ids()
                if not legal:
                    print("DEBUG: No legal actions!")
                    break

                # Simple greedy
                p_data = json.loads(state.to_json())["players"][state.current_player]
                v_to_e = {}
                for aid in legal:
                    vid = map_engine_to_vanilla(p_data, aid, initial_decks[state.current_player])
                    if vid != -1:
                        v_to_e[vid] = aid

                if not v_to_e:
                    action = random.choice(legal)
                    print(f"DEBUG: No mapped actions, picked random: {action}")
                else:
                    action = v_to_e[0]  # Just pick first

                state.step(action)
                state.auto_step(db)
                moves += 1
                if moves % 10 == 0:
                    print(f"DEBUG: Move {moves}, Turn: {state.turn}, Phase: {state.phase}")

            print(f"  [GAME DONE] Turns: {state.turn}, Moves: {moves}")


if __name__ == "__main__":
    run_benchmark()
