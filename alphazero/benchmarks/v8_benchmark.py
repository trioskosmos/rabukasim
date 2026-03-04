import torch
import numpy as np
import json
import os
import random
import sys
import time
from pathlib import Path

# Add project root and relevant subdirectories to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "alphazero" / "training"))

from alphazero.alphanet import AlphaNet
from overnight_pure_zero import load_tournament_decks
import engine_rust

def get_player_move(player_type, state, db, model, device, sims=128):
    legal_ids = state.get_legal_action_ids()
    if not legal_ids: return None

    if player_type == "Heuristic_Greedy":
        # Native Rust Greedy (Original Heuristic)
        return state.get_greedy_action(db, state.current_player, 0, None)
    
    elif player_type == "Model_Greedy":
        # 0-step intuition from the neural network
        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        
        # Create mask efficiently on CPU first
        mask_np = np.zeros((1, 22000), dtype=np.bool_)
        if legal_ids:
            mask_np[0, legal_ids] = True
        mask = torch.from_numpy(mask_np).to(device)
            
        with torch.no_grad():
            # v8 has action branching, but for argmax we care about the final index
            policy_logits, _ = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
        
        # Mask illegal again just in case
        policy[~mask_np[0]] = -1.0
                
        return int(np.argmax(policy))

    elif player_type == "Heuristic_MCTS":
        # Search guided by Original Heuristic
        # eval_mode=1 is Normal
        res = state.get_mcts_suggestions(sims, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal)
        return res[0][0] if res else random.choice(legal_ids)

    elif player_type == "Model_MCTS":
        # Search using TerminalOnly (which is what the model was trained against)
        # eval_mode=2 is TerminalOnly
        res = state.get_mcts_suggestions(sims, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly)
        return res[0][0] if res else random.choice(legal_ids)

    return random.choice(legal_ids)

def play_match(p0_type, p1_type, decks, db_engine, model, device, sims=128, debug=False):
    d0 = random.choice(decks)
    d1 = random.choice(decks)
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"]+d0["lives"], d1["members"]+d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = not debug

    while not state.is_terminal() and state.turn < 20:
        p_type = p0_type if state.current_player == 0 else p1_type
        move = get_player_move(p_type, state, db_engine, model, device, sims=sims)
        if move is None: break
        
        if debug:
            p_str = f"P{state.current_player} ({p_type})"
            label = state.get_action_label(move)
            legal_ids = state.get_legal_action_ids()
            labels = [f"{m} ({state.get_action_label(m)})" for m in legal_ids]
            print(f"[Turn {state.turn}] {p_str} Legal ({len(legal_ids)}): {labels[:20]}..." if len(labels) > 20 else labels)
            print(f"[Turn {state.turn}] {p_str} picked: {move} ({label})")
            
        state.step(move)
        state.auto_step(db_engine)
    
    return state.get_winner(), state.turn

def run_benchmark():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Load Model
    model = AlphaNet().to(device)
    root_dir = Path(__file__).resolve().parent.parent.parent
    checkpoint = str(root_dir / "alphazero" / "training" / "firstrun.pt")
    if not os.path.exists(checkpoint):
        print(f"ERROR: Checkpoint {checkpoint} not found!")
        # Try fallback
        checkpoint = "alphazero/training/alphanet_latest.pt"
        if not os.path.exists(checkpoint):
            print("No checkpoints found. Exiting.")
            return
            
    print(f"Loading weights from {checkpoint}...")
    try:
        model.load_state_dict(torch.load(checkpoint, map_location=device))
    except Exception as e:
        print(f"Incompatible checkpoint: {e}. Trying with strict=False.")
        model.load_state_dict(torch.load(checkpoint, map_location=device), strict=False)
    
    print("Model loaded successfully.")
    model.eval()

    # Load Data
    print("Loading cards_compiled.json...")
    data_path = str(root_dir / "data" / "cards_compiled.json")
    with open(data_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    
    print("Initializing engine database...")
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    
    print("Loading tournament decks...")
    decks = load_tournament_decks(full_db)
    print(f"Loaded {len(decks)} decks.")

    # Scenarios
    # Each row: (Label, P0_Type, P1_Type, Games)
    scenarios = [
        ("NO SEARCH: Model vs Heuristic", "Model_Greedy", "Heuristic_Greedy", 5),
        ("NO SEARCH: Heuristic vs Model", "Heuristic_Greedy", "Model_Greedy", 5),
        ("WITH SEARCH: Model vs Heuristic (128 Sims)", "Model_MCTS", "Heuristic_MCTS", 5),
        ("WITH SEARCH: Heuristic vs Model (128 Sims)", "Heuristic_MCTS", "Model_MCTS", 5),
        ("INTUITION TEST: Model(0) vs Heuristic(128)", "Model_Greedy", "Heuristic_MCTS", 5),
    ]

    print("\nStarting Tournament...")
    
    for label, p0_type, p1_type, num_games in scenarios:
        print(f"\n--- {label} ---")
        p0_wins = 0
        p1_wins = 0
        draws = 0
        turns_hist = []
        
        start_time = time.time()
        for i in range(num_games):
            winner, turns = play_match(p0_type, p1_type, decks, db_engine, model, device, sims=128, debug=False)
            if winner == 0: p0_wins += 1
            elif winner == 1: p1_wins += 1
            else: draws += 1
            turns_hist.append(turns)
            
            if (i+1) % 5 == 0:
                print(f" Game {i+1}/{num_games}... ({p0_wins}-{p1_wins}-{draws})")
        
        elapsed = time.time() - start_time
        wr = (p0_wins / num_games) * 100
        avg_turns = sum(turns_hist) / len(turns_hist)
        
        report = f"Result: P0 {p0_wins} | P1 {p1_wins} | Draws {draws}\n"
        report += f"P0 Win Rate: {wr:.1f}%\n"
        report += f"Avg Turns: {avg_turns:.1f}\n"
        report += f"Time: {elapsed:.1f}s ({num_games/elapsed:.2f} games/sec)\n"
        print(report)

        # Write ONLY this summary to the report file
        out_dir = root_dir / "reports"
        out_dir.mkdir(exist_ok=True)
        with open(out_dir / "v8_benchmark_summary.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- {label} ---\n")
            f.write(report)

if __name__ == "__main__":
    run_benchmark()
