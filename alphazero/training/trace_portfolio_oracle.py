import json
import engine_rust
import torch
import numpy as np
import sys
from pathlib import Path

# Port is handled by PYTHONPATH environment variable

def run_portfolio_trace():
    """
    Demonstrates the Portfolio Oracle in action during a simulated game.
    Uses the 800-dim Vanilla Encoding.
    """
    print("=== RabukaSim Portfolio Oracle Trace ===")
    
    # 1. Setup Environment
    print(f"DEBUG: sys.path: {sys.path}")
    print(f"DEBUG: engine_rust path: {getattr(engine_rust, '__file__', 'No __file__')}")
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    
    # 2. Initialize Game
    print(f"DEBUG: engine_rust type: {type(engine_rust)}")
    print(f"DEBUG: PyGameState type: {type(engine_rust.PyGameState)}")
    state = engine_rust.PyGameState(db_engine)
    print(f"DEBUG: state type: {type(state)}")
    print(f"DEBUG: state methods: {dir(state)}")
    
    # Use a set of diverse cards to ensure interesting synergies
    # (IDs from Gemini.md: 30030 (Rank 5), 1179 (Rank 19))
    p0_deck = [30030, 1179, 103, 104, 105] * 12 # Fill up
    p1_deck = [103] * 60
    
    state.initialize_game(
        p0_deck[:60], p1_deck[:60],
        [1001]*12, [1001]*12,
        [], []
    )
    
    print(f"Game Initialized. Phase: {state.phase}")
    
    # 3. Simulate and Inspect Oracle
    for turn in range(5):
        if state.is_terminal(): break
        
        # Pull the 800-dim Vanilla Tensor
        tensor = state.to_vanilla_tensor()
        
        # Global features are indices 0-19
        best_ev_1 = tensor[10]
        best_ev_2 = tensor[11]
        best_ev_3 = tensor[12]
        best_raev_3 = tensor[15]
        exhaustion = tensor[16]
        
        print(f"\n[Turn {state.turn}] Phase: {state.phase}")
        print(f"  Oracle Best Raw EV (Trio): {best_ev_3:.2f}")
        print(f"  Oracle Best RA-EV (Trio):  {best_raev_3:.2f}")
        print(f"  Stage Exhaustion:          {exhaustion*100:.1f}%")
        
        # Check Participation Hints for the first 12 cards (Live Cards in deck)
        # Card 0 is at index 20, Card Feature 12 (Participation) is at 20 + 12 = 32
        participation_indices = []
        for i in range(12):
            feat_idx = 20 + (i * 13) + 12
            if tensor[feat_idx] > 0.5:
                participation_indices.append(i)
        
        if participation_indices:
            print(f"  Oracle Participation Hints (Indices): {participation_indices}")
        else:
            print("  Oracle Participation Hints: None (Low probability or no valid combos)")

        # Step greedily using MCTS to see if it follows oracle
        legal_ids = state.get_legal_action_ids()
        if not legal_ids: break
        
        suggestions = state.get_mcts_suggestions(32, 1.41, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal)
        if suggestions:
            best_action = suggestions[0][0]
            label = state.get_action_label(best_action)
            print(f"  AI Suggestion: {label}")
            state.step(best_action)
        else:
            print("  No AI suggestions, skipping turn.")
            break
            
        state.auto_step(db_engine)

    print("\n=== Trace Complete ===")

if __name__ == "__main__":
    run_portfolio_trace()
