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
decks_dir =root_dir / "ai" / "decks"
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

# Create game
db_json_str = json.dumps(db_json)
db = engine_rust.PyCardDatabase(db_json_str)
state = engine_rust.PyGameState(db)
state.initialize_game_with_seed(deck["m"], deck["m"], [38]*12, [38]*12, deck["l"], deck["l"], 42)

p0 = state.get_player(0)
print("Player 0 fields:")
for attr in dir(p0):
    if not attr.startswith('_'):
        try:
            val = getattr(p0, attr)
            if not callable(val):
                if isinstance(val, (list, tuple)) and len(val) > 10:
                    print(f"  {attr}: [{len(val)} items] -> {val[:5]}...")
                else:
                    print(f"  {attr}: {val}")
        except:
            pass
