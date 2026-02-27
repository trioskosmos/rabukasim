import engine_rust
import json
import os

import engine_rust
import json
import os

def test_q203():
    print("--- [Q203] Starting Python-based Verification ---")
    
    # Load DB
    data_path = "data/cards_compiled.json"
    with open(data_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    
    db = engine_rust.PyCardDatabase(db_json)
    state = engine_rust.PyGameState(db)

    # Card IDs
    # 358: Cara Tesoro (Nijigasaki Live, Group 2)
    # 4430: Rina Tennoji (Nijigasaki Member, Group 2)
    live_id = 358
    nji_member_id = 4430
    energy_id = 3001 # Generic energy

    # Initialize Game with specific cards
    # p0_main, p1_main, p0_energy, p1_energy, p0_lives, p1_lives
    # Note: main deck should be 48+ cards for valid start if enforced, but let's try 
    p0_main = [nji_member_id] * 48
    p1_main = [nji_member_id] * 48
    p0_energy = [energy_id] * 12
    p1_energy = [energy_id] * 12
    p0_lives = [live_id] * 12
    p1_lives = [live_id] * 12

    state.initialize_game(p0_main, p1_main, p0_energy, p1_energy, p0_lives, p1_lives)
    
    # 3. Simulate Action 1
    # Move to phase where abilities can be triggered? 
    # Actually initialize_game puts it in MULLIGAN.
    # We can force the state to MAIN or just use the action IDs if the engine allows.
    
    # Let's try to trigger a Live Start directly if exposed
    # state.trigger_abilities(db, 2, ctx) # 2 = OnLiveStart
    
    # Check if we can see the new masks
    try:
        p0 = state.get_player(0)
        print(f"P0 Energy Mask: {p0.activated_energy_group_mask}")
        print(f"P0 Member Mask: {p0.activated_member_group_mask}")
        
        # Test Score initial
        print(f"Initial Score: {p0.score}")
    except Exception as e:
        print(f"Could not access masks directly: {e}")

if __name__ == "__main__":
    test_q203()

if __name__ == "__main__":
    test_q203()
