import os
import sys

# Ensure engine_rust is importable
pwd = os.getcwd()
if pwd not in sys.path:
    sys.path.append(pwd)

try:
    import engine_rust

    print("Engine imported successfully.")
except ImportError as e:
    print(f"Failed to import engine_rust: {e}")
    sys.exit(1)


# Helper to load deck
def load_deck(path, db):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    m_list = []
    l_list = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Format: CARD_NO x QTY
        if " x " in line:
            parts = line.split(" x ")
            card_no = parts[0].strip()
            qty = int(parts[1].strip())

            cid = db.id_by_no(card_no)
            if cid is None:
                print(f"WARNING: Card not found in DB: {card_no}")
                continue

            if cid >= 10000:
                l_list.extend([cid] * qty)
            else:
                m_list.extend([cid] * qty)
    return m_list, l_list


root = os.getcwd()
db_path = os.path.join(root, "data", "cards_compiled.json")
print(f"Loading DB from: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")

try:
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)
    print(f"Database loaded. Members: {db.member_count}, Lives: {db.live_count}")
except Exception as e:
    print(f"DATABASE LOAD FAILED: {e}")
    sys.exit(1)

deck_path = os.path.join(root, "ai/decks/aqours_cup.txt")
print(f"Loading deck from: {deck_path}")
m_list, l_list = load_deck(deck_path, db)
print(f"Deck loaded: {len(m_list)} members, {len(l_list)} lives.")

state = engine_rust.PyGameState(db)
print("State created. Initializing...", flush=True)

state.initialize_game(m_list, m_list, [], [], l_list, l_list)
print("Initialization complete!", flush=True)

print(f"Current Phase: {state.phase}", flush=True)
print(f"Current Player: {state.current_player}", flush=True)

print("Getting greedy action (OriginalHeuristic)...", flush=True)
action = state.get_greedy_action(db, 0)  # 0 = Original
print(f"Action: {action}", flush=True)

print("Stepping...", flush=True)
state.step(action)
print(f"Step complete. New Phase: {state.phase}", flush=True)
