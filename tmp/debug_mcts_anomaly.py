import os
import sys
import random
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Find engine_rust
base_dir = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy"
search_paths = [
    os.path.join(base_dir, "engine_rust_src", "target", "dev-release"),
    os.path.join(base_dir, "engine_rust_src", "target", "release"),
]
for p in search_paths:
    if os.path.exists(os.path.join(p, "engine_rust.pyd")) or os.path.exists(os.path.join(p, "engine_rust.dll")):
        sys.path.insert(0, p)
        break

import engine_rust

# Load DB
with open(os.path.join(base_dir, "data/cards_compiled.json"), "r", encoding="utf-8") as f:
    db_content = f.read()
G_DB = engine_rust.PyCardDatabase(db_content)

def run_debug_match():
    state = engine_rust.PyGameState(G_DB)
    
    # Generic deck
    # aqours_cup.txt deck parsing example
    # cid 0 is usually an energy, cid 1-100 members, cid 1000+ lives
    
    # Let's use some IDs we're reasonably sure exist
    # If not, it will fail, which is also helpful
    
    d_m = [1] * 40
    d_e = [500] * 12
    d_l = [1000] * 12
    
    state.initialize_game_with_seed(
        d_m, d_m,
        d_e, d_e,
        d_l, d_l,
        42
    )
    
    print(f"Initial Phase: {state.phase}")
    
    turns = 0
    # Advance through Setup/Rps/TurnChoice/Mulligan
    while state.phase < 1 and turns < 200:
        acting_p = state.acting_player
        legal = state.get_legal_action_ids()
        print(f"Phase {state.phase}, Acting: {acting_p}, Legal moves: {len(legal)}")
        if not legal: break
        state.step(legal[0])
        turns += 1
        
    print(f"Reached Mulligan/Active, Phase: {state.phase}")
    
    # Run a few gameplay turns
    for _ in range(20):
        if state.phase == 9: break
        
        acting_p = state.acting_player
        legal = state.get_legal_action_ids()
        if not legal: break
        
        # MCTS check
        mcts_results = state.search_mcts(num_sims=128, heuristic_type="original")
        mcts_action = mcts_results[0][0] if mcts_results else legal[0]
        mcts_eval = mcts_results[0][1] if mcts_results else 0.5
        
        # Random check
        random_choice = random.choice(legal)
        
        print(f"Turn {state.turn}, Phase {state.phase}, Acting P{acting_p}")
        print(f"  Moves Available: {len(legal)}")
        print(f"  MCTS Choice: {mcts_action} (Eval: {mcts_eval:.4f})")
        print(f"  Random Choice: {random_choice}")
        
        # Step with MCTS
        state.step(mcts_action)

    print(f"Match Results. Winner: {state.get_winner()}")

if __name__ == "__main__":
    run_debug_match()
