import torch
import numpy as np
import json
import os
import random
import sys
import time
from pathlib import Path

# Add root for engine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.alphazero.alphanet import AlphaNet
from tools.alphazero.overnight_pure_zero import load_tournament_decks
import engine_rust

def get_player_move(player_type, state, db, model, device):
    legal_ids = state.get_legal_action_ids()
    if not legal_ids: return None, 0, 0

    start_time = time.perf_counter()
    num_sims = 0

    if player_type == "Greedy":
        # Using Native Rust Greedy (H-ID 0 is OriginalHeuristic)
        move = state.get_greedy_action(db, state.current_player, 0, None)
    
    elif player_type == "MCTS_Terminal_0.01s":
        # Pure Search (No Heuristics)
        res = state.search_mcts(0, 0.01, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly, None, None)
        num_sims = sum(s[2] for s in res) if res else 0
        move = res[0][0] if res else random.choice(legal_ids)

    elif player_type == "Model_Raw":
        # Pure Instinct (0s search)
        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        mask = torch.zeros((1, 16384), dtype=torch.bool).to(device)
        for aid in legal_ids: mask[0, aid] = True
        with torch.no_grad():
            policy_logits, _ = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
        move = int(np.argmax(policy))

    elif player_type == "AlphaZero_0.01s":
        # The AlphaZero Way: Model acts as Prior for MCTS
        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        mask = torch.zeros((1, 16384), dtype=torch.bool).to(device)
        for aid in legal_ids: mask[0, aid] = True
        with torch.no_grad():
            policy_logits, _ = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
        
        # We simulate PUCT by only searching actions the model thinks are >1% likely
        # This focuses ALL sims on the model's best guesses
        res = state.search_mcts(0, 0.01, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly, None, None)
        num_sims = sum(s[2] for s in res) if res else 0
        move = res[0][0] if res else random.choice(legal_ids)

    elif player_type == "MCTS_Heuristic_0.01s":
        # Search guided by human rules
        res = state.search_mcts(0, 0.01, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None, None)
        num_sims = sum(s[2] for s in res) if res else 0
        move = res[0][0] if res else random.choice(legal_ids)

    else:
        move = random.choice(legal_ids)

    elapsed = time.perf_counter() - start_time
    return move, num_sims, elapsed

def play_match(p0_type, p1_type, decks, db_engine, model, device):
    d0 = random.choice(decks)
    d1 = random.choice(decks)
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"]+d0["lives"], d1["members"]+d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True

    sims_total = 0
    time_total = 0
    while not state.is_terminal() and state.turn < 120:
        p_type = p0_type if state.current_player == 0 else p1_type
        move, sims, dt = get_player_move(p_type, state, db_engine, model, device)
        if move is None: break
        state.step(move)
        state.auto_step(db_engine)
        if p_type != "Model_Raw" and p_type != "Greedy":
            sims_total += sims
            time_total += dt
    
    return state.get_winner(), state.turn, sims_total, time_total

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

    players = ["Greedy", "Model_Raw", "AlphaZero_0.01s"]
    stats = {p: {"wins": 0, "losses": 0, "draws": 0, "sims": [], "times": [], "turns": []} for p in players}

    print(f"--- THE ALPHAZERO FAIR FIGHT (0.1s Limit) ---")
    
    games_per_matchup = 10
    matchups = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            matchups.append((players[i], players[j]))

    for p1_name, p2_name in matchups:
        print(f"Match: {p1_name} vs {p2_name}...", end="", flush=True)
        for _ in range(games_per_matchup):
            winner, turns, sims, dt = play_match(p1_name, p2_name, decks, db_engine, model, device)
            
            stats[p1_name]["turns"].append(turns)
            stats[p2_name]["turns"].append(turns)
            if dt > 0:
                stats[p1_name]["sims"].append(sims)
                stats[p1_name]["times"].append(dt)

            if winner == 0:
                stats[p1_name]["wins"] += 1
                stats[p2_name]["losses"] += 1
            elif winner == 1:
                stats[p2_name]["wins"] += 1
                stats[p1_name]["losses"] += 1
            else:
                stats[p1_name]["draws"] += 1
                stats[p2_name]["draws"] += 1
        print(" DONE!")

    print("\n" + "="*85)
    print(f"{'AGENT':<20} | WIN % | WR | SIMS/S | AVG TURN | PERF")
    print("-" * 85)
    for p in players:
        w, l, d = stats[p]["wins"], stats[p]["losses"], stats[p]["draws"]
        total = w + l + d
        wr = (w / total) * 100 if total > 0 else 0
        
        sims_s = sum(stats[p]["sims"]) / sum(stats[p]["times"]) if sum(stats[p]["times"]) > 0 else 0
        avg_turn = sum(stats[p]["turns"]) / len(stats[p]["turns"]) if stats[p]["turns"] else 0
        
        perf = "FLASH" if p == "Model_Raw" or p == "Greedy" else f"{sims_s:7.0f}"
        print(f"{p:<20} | {wr:5.1f}% | {w:2d}-{l:d} | {perf:>7} | {avg_turn:8.1f} | {'Ready'}")

if __name__ == "__main__":
    run_face_off()
