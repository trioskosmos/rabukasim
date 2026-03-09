import json
from pathlib import Path
from engine.game.deck_utils import UnifiedDeckParser

# Load database
root_dir = Path('.')
db_path = root_dir / 'data' / 'cards_vanilla.json'
if not db_path.exists(): db_path = root_dir / 'data' / 'cards_compiled.json'
with open(db_path, 'r', encoding='utf-8') as f: db_json = json.load(f)

# Load decks
decks_dir = root_dir / "ai" / "decks"
all_decks = []
parser = UnifiedDeckParser(db_json)
for df in list(decks_dir.glob("*.txt"))[:3]:  # Just first 3
    with open(df, "r", encoding="utf-8") as f:
        ext = parser.extract_from_content(f.read())
        if ext:
            m, l = [], []
            for c in ext[0]['main']:
                cd = parser.resolve_card(c)
                if cd and cd.get("type") == "Member": m.append(cd["card_id"])
                elif cd and cd.get("type") == "Live": l.append(cd["card_id"])
            deck = {"name": df.stem, "m": (m*5)[:48], "l": (l*5)[:12]}
            print(f"Deck {df.stem}:")
            print(f"  Members from parsing: {len(m)} unique")
            print(f"  Lives from parsing: {len(l)} unique")
            print(f"  Final member deck: {len(deck['m'])} cards")
            print(f"  Final live deck: {len(deck['l'])} cards")
            print(f"  Member deck: {deck['m'][:5]}...")
            print(f"  Live deck: {deck['l']}")
            all_decks.append(deck)
