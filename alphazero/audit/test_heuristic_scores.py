import os
import sys
import json
from pathlib import Path

# Add project root for imports
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# Add Rust engine paths
search_paths = [
    root_dir / "engine_rust_src" / "target" / "release",
    root_dir / "engine_rust_src" / "target" / "debug",
]
for p in search_paths:
    if (p / "engine_rust.pyd").exists() or (p / "engine_rust.dll").exists():
        sys.path.insert(0, str(p))
        break

import engine_rust

def run_audit():
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = json.load(f)
    
    # Strip abilities
    for cat in ["member_db", "live_db"]:
        for data in db_json.get(cat, {}).values():
            data["abilities"] = []
            data["ability_flags"] = 0
            
    db_json_str = json.dumps(db_json)
    card_db = engine_rust.PyCardDatabase(db_json_str)
    
    # Create the object
    state_obj = engine_rust.PyGameState(card_db)
    
    # Initialize basic state (Method)
    state_obj.initialize_game(
        [30001]*60, [30001]*60, # Decks
        [], [], # Energy
        [40001]*12, [40001]*12 # Lives
    )
    
    # Manually force into Player 0's Main Phase (Properties)
    state_obj.phase = 4 
    state_obj.current_player = 0
    
    # Set Audit Scenario (Methods)
    # Honoka (ID 30001, Cost 1, 2 Blades, 1 Heart), Kotori (ID 30002, Cost 2), Live (ID 40001)
    state_obj.set_hand_cards(0, [30001, 30002, 40001])
    state_obj.set_energy_cards(0, [38, 38]) # 2 Untapped
    
    print("\n" + "="*70)
    print("NEW HEURISTIC AUDIT: MAIN PHASE (AGGRESSIVE)")
    print("-" * 70)
    print(f"Phase: {state_obj.phase}")
    print(f"Acting Player: {state_obj.current_player}")
    
    evals, sequence = state_obj.plan_full_turn(card_db)
    evals.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'ID':<6} | {'Action':<35} | {'Heuristic Score':<15}")
    print("-" * 70)
    for aid, score in evals:
        label = state_obj.get_action_label(aid)
        print(f"{aid:<6} | {label:<35} | {score:0.3f}")
        
    print("\nPROPOSED ACTION CHAIN:")
    if not sequence: print("  (Empty)")
    for i, aid in enumerate(sequence):
        print(f"  {i+1}. {state_obj.get_action_label(aid)}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_audit()
