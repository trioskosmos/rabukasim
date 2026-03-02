import json
import engine_rust
import os

def verify():
    # Load real card database
    db_path = "data/cards_compiled.json"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        json_str = f.read()
    
    db = engine_rust.PyCardDatabase(json_str)
    state = engine_rust.PyGameState(db)
    
    print(f"PyGameState has to_alphazero_tensor: {hasattr(state, 'to_alphazero_tensor')}")
    
    # Initialize a basic game state
    p0_deck = [103] * 30
    p1_deck = [103] * 30
    p0_energy = [1001] * 10
    p1_energy = [1001] * 10
    p0_lives = [2001] * 3
    p1_lives = [2001] * 3
    
    state.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)
    
    # Put card 103 into stage slot 0 to verify identity metadata
    state.set_stage_card(0, 0, 103)
    
    # Extract tensor
    tensor = state.to_alphazero_tensor()
    print(f"Tensor length: {len(tensor)}") # Expected: 3910
    
    # Check one card (Stage Slot 0 is at offset 25)
    # Card Vector Structure: Identity(16) + Stats(10) + FuturePadding(6) + Bytecode(128)
    card_offset = 25
    identity_block = tensor[card_offset : card_offset + 16]
    stats_block = tensor[card_offset + 16 : card_offset + 26]
    
    print(f"Card Identity Block (Slot 0): {identity_block[:8]}")
    # index 0: Type (1.0 for Member)
    # index 1: CharID
    # index 2: Rarity
    # index 3,4: Groups
    # index 5,6: Units
    
    if len(tensor) == 3910:
        print("SUCCESS: Tensor length matches 160-float specification.")
    else:
        print(f"FAILURE: Expected 3910, got {len(tensor)}")

if __name__ == "__main__":
    verify()
