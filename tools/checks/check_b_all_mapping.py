from game.game_state import GameState, StatePool

# Initialize a dummy game to trigger data loading
gs = StatePool.get_game_state()
# Access class-level DB
live_db = GameState.live_db

target_id = -1
for cid, card in live_db.items():
    if "PL!HS-PR-010-PR" in str(card.name) or "Reflection" in str(card.name):  # Name might be Japanese
        # Actually checking by ID is hard since IDs are ints.
        # But data_loader maps them.
        # Let's search by checking `blade_hearts` or `raw_text`
        pass

# Better: Load the ID from mapping or just iterate and print matching
found = False
for cid, card in live_db.items():
    # Reflection in the mirror
    if getattr(card, "name", "") == "Reflection in the mirror":
        print(f"Found Card: {card.name} (ID: {cid})")
        print(f"blade_hearts: {card.blade_hearts} (Type: {type(card.blade_hearts)})")
        if hasattr(card, "blade_hearts") and hasattr(card.blade_hearts, "shape"):
            print(f"Shape: {card.blade_hearts.shape}")

        # Check specific index values
        # Expecting if b_all is mapped, some index is > 0
        found = True
        break

if not found:
    print("Card not found in DB.")
