import torch
import numpy as np
import json
import os
import sys
from pathlib import Path

# Fix paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "alphazero" / "training"))

from alphazero.alphanet import AlphaNet
from overnight_pure_zero import load_tournament_decks
import engine_rust

def get_player_move(player_type, state, db, model, device):
    legal_ids = state.get_legal_action_ids()
    if not legal_ids: return None

    if player_type == "Model_Greedy":
        obs_numpy = np.array(state.to_alphazero_tensor()).astype(np.float32)
        obs = torch.from_numpy(obs_numpy).unsqueeze(0).to(device)
        mask_np = np.zeros((1, 22000), dtype=np.bool_)
        mask_np[0, legal_ids] = True
        mask = torch.from_numpy(mask_np).to(device)
            
        with torch.no_grad():
            policy_logits, _ = model(obs, mask=mask)
            policy = torch.softmax(policy_logits, dim=1).cpu().numpy()[0]
        
        policy[~mask_np[0]] = -1.0
        return int(np.argmax(policy))

    # Fallback to Heuristic Greedy if not Model
    return state.get_greedy_action(db, state.current_player, 0, None)

def trace_100_actions():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Load Model (dummy or latest)
    model = AlphaNet().to(device)
    checkpoint = str(PROJECT_ROOT / "alphazero" / "training" / "alphanet_latest.pt")
    if os.path.exists(checkpoint):
        model.load_state_dict(torch.load(checkpoint, map_location=device), strict=False)
        print(f"Loaded {checkpoint}")
    else:
        print("No checkpoint found, using random weights (testing logic loop)")
    model.eval()

    # Load Data
    data_path = str(PROJECT_ROOT / "data" / "cards_compiled.json")
    with open(data_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    decks = load_tournament_decks(full_db)
    
    # Initialize game
    d0 = decks[0]
    d1 = decks[1]
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"]+d0["lives"], d1["members"]+d1["lives"], d0["energy"], d1["energy"], [], [])
    
    # ACTION TRACE
    print("\n--- TRACING 100 ACTIONS ---")
    action_count = 0
    while not state.is_terminal() and action_count < 100:
        p_type = "Model_Greedy" # Test with model
        legal_ids = state.get_legal_action_ids()
        move = get_player_move(p_type, state, db_engine, model, device)
        
        p_str = f"P{state.current_player} ({p_type})"
        label = state.get_action_label(move) if move is not None else "None"
        
        # Only print first 10 legal actions to save space
        legal_labels = [f"{m}({state.get_action_label(m)})" for m in legal_ids[:10]]
        if len(legal_ids) > 10:
            legal_labels.append("...")
            
        print(f"[Action {action_count}] [Turn {state.turn}] {p_str}")
        print(f"  Move: {move} ({label})")
        print(f"  Legal ({len(legal_ids)}): {legal_labels}")
        
        if move is None:
            print("  No move returned!")
            break
            
        state.step(move)
        state.auto_step(db_engine)
        action_count += 1

    if state.is_terminal():
        print(f"\nGame Ended. Winner: {state.get_winner()}")
    else:
        print("\nTrace limit reached (100 actions).")

if __name__ == "__main__":
    trace_100_actions()
