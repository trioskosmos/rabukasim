import os
import sys

# Setup path to import backend modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from engine.game.data_loader import CardDataLoader
from engine.game.game_state import GameState

cards_path = os.path.join(PROJECT_ROOT, "engine", "data", "cards.json")
print(f"Loading cards from {cards_path}")
loader = CardDataLoader(cards_path)
m_db, l_db, e_db = loader.load()

# Update GameState class variables (since serializer might use them or we might check them)
GameState.initialize_class_db(m_db, l_db)

# Check member_db keys
if GameState.member_db:
    print(f"Member DB Size: {len(GameState.member_db)}")
    sample_keys = list(GameState.member_db.keys())[:10]
    print(f"Sample Member Keys: {sample_keys}")
    print(f"Key Type: {type(sample_keys[0])}")
else:
    print("GameState has no member_db")

# Check live_db keys
if hasattr(GameState, "live_db"):
    print(f"Live DB Size: {len(GameState.live_db)}")
    sample_keys = list(GameState.live_db.keys())[:10]
    print(f"Sample Live Keys: {sample_keys}")
else:
    print("GameState has no live_db")

# Test Serializer Logic
# The serializer does: base_id = cid_int & 0xFFFFF
cid = 200582  # Example ID from logs if available, or just guess
base_id = cid & 0xFFFFF
print(f"Test CID: {cid} -> Base ID: {base_id}")
if hasattr(GameState, "member_db"):
    if base_id in GameState.member_db:
        print(f"Found in DB! Name: {GameState.member_db[base_id].name}")
        print(f"Text: {GameState.member_db[base_id].ability_text}")
    else:
        print("Not found in DB via base_id")
