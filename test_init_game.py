import json
from pathlib import Path
import engine_rust
from engine.game.deck_utils import UnifiedDeckParser

# Load database
root_dir = Path('.')
db_path = root_dir / 'data' / 'cards_vanilla.json'
if not db_path.exists(): db_path = root_dir / 'data' / 'cards_compiled.json'
with open(db_path, 'r', encoding='utf-8') as f: db_json = json.load(f)

# Load first deck
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
print(f"Member deck length: {len(deck['m'])}")
print(f"Live deck length: {len(deck['l'])}")

# Create game
db_json_str = json.dumps(db_json)
db = engine_rust.PyCardDatabase(db_json_str)
state = engine_rust.PyGameState(db)
state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], 42)

print(f"\nAfter initialization:")
print(f"P0 success_lives: {len(state.get_player(0).success_lives)}")
print(f"P1 success_lives: {len(state.get_player(1).success_lives)}")
print(f"Is terminal: {state.is_terminal()}")

pj = json.loads(state.to_json())
print(f"Current phase: {pj.get('phase')}")

# Try auto_step to see what happens
print(f"\nCalling auto_step...")
state.auto_step(db)
print(f"After auto_step:")
print(f"P0 success_lives: {len(state.get_player(0).success_lives)}")
print(f"P1 success_lives: {len(state.get_player(1).success_lives)}")
print(f"Is terminal: {state.is_terminal()}")
