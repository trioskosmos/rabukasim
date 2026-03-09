import json
from pathlib import Path
import engine_rust
from engine.game.deck_utils import UnifiedDeckParser
import random

# Load database and setup vanilla
root_dir = Path('.')
db_path = root_dir / 'data' / 'cards_vanilla.json'
if not db_path.exists(): 
    db_path = root_dir / 'data' / 'cards_compiled.json'
with open(db_path, 'r', encoding='utf-8') as f: 
    db_json = json.load(f)

# Strip abilities for vanilla
for cat in ["member_db", "live_db"]:
    for cid, data in db_json.get(cat, {}).items():
        data["abilities"] = []
        data["ability_flags"] = 0
        if "synergy_flags" in data:
            data["synergy_flags"] &= 1

db_json_str = json.dumps(db_json)
db = engine_rust.PyCardDatabase(db_json_str)

# Load a real deck
decks_dir = root_dir / "ai" / "decks"
parser = UnifiedDeckParser(db_json)
df = list(decks_dir.glob("*.txt"))[0]
with open(df, "r", encoding="utf-8") as f:
    ext = parser.extract_from_content(f.read())
    if ext:
        m, l = [], []
        for c in ext[0]['main']:
            cd = parser.resolve_card(c)
            if cd and cd.get("type") == "Member": m.append(cd["card_id"])
            elif cd and cd.get("type") == "Live": l.append(cd["card_id"])
        deck = {"name": df.stem, "m": (m*5)[:48], "l": (l*5)[:12]}

print(f"Testing deck: {deck['name']}")
print(f"Members: {len(deck['m'])}, Lives: {len(deck['l'])}")

# Initialize game exactly like training code
state = engine_rust.PyGameState(db)
state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], 42)

print(f"\nAfter initialize_game_with_seed:")
print(f"  is_terminal: {state.is_terminal()}")
print(f"  turn: {state.turn}")
print(f"  winner: {state.get_winner()}")

# Step through the game manually
moves = 0
while not state.is_terminal() and state.turn < 25 and moves < 500:
    legal = state.get_legal_action_ids()
    if not legal:
        print(f"[Turn {state.turn}] No legal actions, calling auto_step")
        state.auto_step(db)
        legal = state.get_legal_action_ids()
        if not legal:
            print(f"[Turn {state.turn}] Still no legal actions after auto_step, breaking")
            break
    
    import json as j
    pj = j.loads(state.to_json())
    phase = pj.get('phase', -4)
    
    # Just pick random action
    action = random.choice(legal)
    print(f"[Move {moves}, Turn {state.turn}] Phase: {phase:2d}, Legal actions: {len(legal)}, Chose: {action}")
    
    state.step(action)
    state.auto_step(db)
    moves += 1
    
    if moves > 20:  # Stop after 20 moves for debugging
        break

print(f"\nFinal state:")
print(f"  is_terminal: {state.is_terminal()}")
print(f"  turn: {state.turn}")
print(f"  winner: {state.get_winner()}")
print(f"  P0 success_lives: {len(state.get_player(0).success_lives)}")
print(f"  P1 success_lives: {len(state.get_player(1).success_lives)}")
print(f"  Moves made: {moves}")
