import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_rust
from engine.game.data_loader import CardDataLoader
from backend.rust_serializer import RustGameStateSerializer

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

def main():
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cards_compiled.json")
    loader = CardDataLoader(json_path)
    py_member_db, py_live_db, py_energy_db = loader.load()
    
    with open(json_path, "r", encoding="utf-8") as f:
        json_str = f.read()
    rust_db = engine_rust.PyCardDatabase(json_str)

    serializer = RustGameStateSerializer(py_member_db, py_live_db, py_energy_db)
    
    dumps = ["verify_buff_logic", "test_group_cd", "test_score_compare"]
    
    for name in dumps:
        raw_path = f"{name}_raw.json"
        if not os.path.exists(raw_path):
            print(f"Skipping {raw_path} - not found.")
            continue
            
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_json = f.read()
            
        gs = engine_rust.PyGameState(rust_db)
        gs.apply_state_json(raw_json)
        
        state_dict = serializer.serialize_state(gs, viewer_idx=0, mode="pve", lang="en")
        
        out_path = f"{name}_frontend.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
            
        print(f"Converted {name} -> {out_path}")

if __name__ == "__main__":
    main()
