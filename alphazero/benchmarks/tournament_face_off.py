import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch

# Add root for engine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import engine_rust
from tools.alphazero.alphanet import AlphaNet
from tools.alphazero.overnight_pure_zero import load_tournament_decks


def get_player_move(player_type, state, db, model, device):
    legal_ids = state.get_legal_action_ids()
    if not legal_ids:
        return None

    if player_type == "Greedy_Heuristic":
        # Look ahead 1-step and evaluate with original heuristic
        best_aid = -1
        best_score = -999999.0
        for aid in legal_ids:
            # Clone state to avoid mutation
            temp_state = state.clone()
            temp_state.step(aid)
            temp_state.auto_step(db)
            # Evaluate from current player's perspective
            score = temp_state.evaluate("original", engine_rust.EvalMode.Normal, None)
            if score > best_score:
                best_score = score
                best_aid = aid
        return best_aid if best_aid != -1 else random.choice(legal_ids)

    elif player_type == "MCTS_Terminal_0.1s":
        # Teacher at 0.1s
        res = state.search_mcts(
            0, 0.1, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly, None, None
        )
        return res[0][0] if res else random.choice(legal_ids)

    elif player_type == "Model_Raw":
        # Student (Intuition) - effectively 0s
        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        mask = torch.zeros((1, 16384), dtype=torch.bool).to(device)
        for aid in legal_ids:
            mask[0, aid] = True

        with torch.no_grad():
            policy_logits, _ = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
        return int(np.argmax(policy))

    elif player_type == "MCTS_Heuristic_0.1s":
        # Heuristic MCTS at 0.1s
        res = state.search_mcts(
            0, 0.1, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None, None
        )
        return res[0][0] if res else random.choice(legal_ids)

    return random.choice(legal_ids)


def play_match(p0_type, p1_type, decks, db_engine, model, device):
    d0 = random.choice(decks)
    d1 = random.choice(decks)
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True

    while not state.is_terminal() and state.turn < 120:
        p_type = p0_type if state.current_player == 0 else p1_type
        move = get_player_move(p_type, state, db_engine, model, device)
        if move is None:
            break
        state.step(move)
        state.auto_step(db_engine)

    return state.get_winner()


def run_face_off():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaNet().to(device)
    checkpoint = "alphanet_latest.pt"
    if os.path.exists(checkpoint):
        model.load_state_dict(torch.load(checkpoint, map_location=device))
    model.eval()

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    decks = load_tournament_decks(full_db)

    players = ["Greedy_Heuristic", "MCTS_Terminal_0.1s", "Model_Raw", "MCTS_Heuristic_0.1s"]
    results = {p: {other: [0, 0, 0] for other in players} for p in players}  # [P1 Win, P2 Win, Draw]

    print("--- 4-WAY FACE OFF TOURNAMENT ---")
    print(f"Model: {checkpoint}")

    matchups = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            matchups.append((players[i], players[j]))

    games_per_matchup = 10

    for p1, p2 in matchups:
        print(f"Matchup: {p1} vs {p2}...", end="", flush=True)
        p1_wins = 0
        p2_wins = 0
        draws = 0

        for _ in range(games_per_matchup):
            winner = play_match(p1, p2, decks, db_engine, model, device)
            if winner == 0:
                p1_wins += 1
            elif winner == 1:
                p2_wins += 1
            else:
                draws += 1

        results[p1][p2] = [p1_wins, p2_wins, draws]
        print(f" DONE! ({p1_wins}-{p2_wins}-{draws})")

    # Summary Table
    print("\n" + "=" * 50)
    print(f"{'PLAYER':<15} |  W  |  L  |  D  | WIN %")
    print("-" * 50)

    for p in players:
        w, l, d = 0, 0, 0
        for other in players:
            if other == p:
                continue
            if other in results[p]:
                w += results[p][other][0]
                l += results[p][other][1]
                d += results[p][other][2]
            else:
                w += results[other][p][1]
                l += results[other][p][0]
                d += results[other][p][2]

        total = w + l + d
        win_rate = (w / total) * 100 if total > 0 else 0
        print(f"{p:<15} | {w:3d} | {l:3d} | {d:3d} | {win_rate:5.1f}%")


if __name__ == "__main__":
    run_face_off()
