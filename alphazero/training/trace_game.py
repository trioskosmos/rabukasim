import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import engine_rust

from alphazero.alphanet import AlphaNet
from alphazero.overnight_pure_zero import load_tournament_decks


def get_action_info(state, model, device, legal_ids, sims=128):
    # 1. Model Intuition
    obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
    obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
    mask = torch.zeros((1, 16384), dtype=torch.bool).to(device)
    for aid in legal_ids:
        mask[0, aid] = True

    with torch.no_grad():
        policy_logits, _ = model(obs, mask=mask)
        policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]

    # 2. MCTS Logic
    res = state.get_mcts_suggestions(sims, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly)

    return policy, res


def run_trace(use_search=False):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaNet().to(device)
    checkpoint = "alphazero/alphanettest.pt"
    if not os.path.exists(checkpoint):
        checkpoint = "alphazero/alphanet_latest.pt"

    model.load_state_dict(torch.load(checkpoint, map_location=device), strict=False)
    model.eval()

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    decks = load_tournament_decks(full_db)

    d0, d1 = decks[0], decks[1]
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True

    print(f"\n{'=' * 60}")
    print(f"TRACING GAME: {'MCTS (128 Sims)' if use_search else 'GREEDY (Intuition Only)'}")
    print(f"{'=' * 60}")

    last_turn = -1
    while not state.is_terminal() and state.turn < 100:
        if state.turn != last_turn:
            print(
                f"\n--- Turn {state.turn} (P{state.current_player}) Score: {len(state.get_player(0).success_lives)}-{len(state.get_player(1).success_lives)} ---"
            )
            last_turn = state.turn

        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            state.auto_step(db_engine)
            continue

        policy, mcts_res = get_action_info(state, model, device, legal_ids)

        if use_search:
            # Choose via MCTS
            move = mcts_res[0][0]
            print(f"MCTS Choice: {state.get_action_label(move)}")
            print("  Top 3 Candidates:")
            for i in range(min(3, len(mcts_res))):
                aid, q, n = mcts_res[i]
                p_prior = policy[aid]
                print(f"    {i + 1}. {state.get_action_label(aid):<30} | Q: {q:.3f} | N: {n:4d} | Prior: {p_prior:.1%}")
        else:
            # Choose via Max Policy
            move = int(np.argmax(policy))
            print(f"Model Instinct: {state.get_action_label(move)} (Conf: {policy[move]:.1%})")

        state.step(move)
        state.auto_step(db_engine)

    print(f"\nGame Over! Winner: Player {state.get_winner()}")


if __name__ == "__main__":
    # Run both sequentially
    run_trace(use_search=False)
    run_trace(use_search=True)
