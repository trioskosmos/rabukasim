import argparse
import json
import os
import sys

# Add parent directory to path so we can import engine and backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_rust
from engine.game.data_loader import CardDataLoader
from backend.rust_serializer import RustGameStateSerializer

def main():
    parser = argparse.ArgumentParser(description="Export a Rust GameState to JSON for frontend debugging")
    parser.add_argument("--output", "-o", default="frontend_debug_state.json", help="Output JSON file path")
    parser.add_argument("--actions", "-a", nargs="*", type=int, help="List of action IDs to run before dumping state")
    args = parser.parse_args()

    # Load Databases
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cards_compiled.json")
    loader = CardDataLoader(json_path)
    py_member_db, py_live_db, py_energy_db = loader.load()
    
    with open(json_path, "r", encoding="utf-8") as f:
        json_str = f.read()

    rust_db = engine_rust.PyCardDatabase(json_str)
    
    # Initialize Game State
    gs = engine_rust.PyGameState(rust_db)
    
    # Generate generic decks
    m_pool = list(py_member_db.keys())
    l_pool = list(py_live_db.keys())
    
    import random
    deck1_m = [random.choice(m_pool) for _ in range(48)]
    deck1_l = [random.choice(l_pool) for _ in range(12)]
    
    deck2_m = [random.choice(m_pool) for _ in range(48)]
    deck2_l = [random.choice(l_pool) for _ in range(12)]
    
    # Initialize decks and energy
    # Energy IDs: typically 51001-51006 ranges or we just pass some valid ids
    p0_energy = [random.choice(m_pool) for _ in range(10)]
    p1_energy = [random.choice(m_pool) for _ in range(10)]
    
    gs.initialize_game_with_seed(
        deck1_m, deck2_m, p0_energy, p1_energy, deck1_l, deck2_l, 42
    )

    # Draw opening hand
    # Note: Game initialization automatically draws cards according to rules, but we can advance phases
    
    # Apply requested actions
    if args.actions:
        for action_id in args.actions:
            print(f"Applying action: {action_id}")
            gs.step(action_id)

    # Serialize
    serializer = RustGameStateSerializer(py_member_db, py_live_db, py_energy_db)
    # The frontend expects the JSON to match what the backend sends via websockets
    state_dict = serializer.serialize_state(gs, viewer_idx=0, mode="pve", lang="jp")
    
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)

    # Write to file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(state_dict, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
    print(f"Debug GameState JSON exported to: {args.output}")
    print("You can paste the contents of this file into the Frontend's Debug Menu.")

if __name__ == "__main__":
    main()
