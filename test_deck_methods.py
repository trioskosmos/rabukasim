import json
from pathlib import Path
import engine_rust
from engine.game.deck_utils import UnifiedDeckParser
import random

# Load database and setup
root_dir = Path('.')
db_path = root_dir / 'data' / 'cards_vanilla.json'
if not db_path.exists(): 
    db_path = root_dir / 'data' / 'cards_compiled.json'
with open(db_path, 'r', encoding='utf-8') as f: 
    db_json = json.load(f)

# Strip abilities for vanilla (like in training)
for cat in ["member_db", "live_db"]:
    for cid, data in db_json.get(cat, {}).items():
        data["abilities"] = []
        data["ability_flags"] = 0
        if "synergy_flags" in data:
            data["synergy_flags"] &= 1

db_json_str = json.dumps(db_json)
db = engine_rust.PyCardDatabase(db_json_str)

# Generate a combined 60-card deck (48 members + 12 lives)
# Method 1: Current approach (separate member and live decks)
member_list = [10] * 48  # Simple member cards
live_list = [38] * 12     # Simple live cards
seed = 42

print("=== METHOD 1: Separate member and live decks ===")
state1 = engine_rust.PyGameState(db)
state1.initialize_game_with_seed(member_list, member_list, [38]*12, [38]*12, live_list, live_list, seed)
p1_player = state1.get_player(0)
print(f"Initial hand size: {len(p1_player.hand)}")
print(f"Initial deck size: {len(p1_player.deck)}")
print(f"Initial_deck total size: {len(p1_player.initial_deck)}")
print(f"Members in initial_deck: {sum(1 for x in p1_player.initial_deck if x != 38)}")
print(f"Lives (38) in initial_deck: {sum(1 for x in p1_player.initial_deck if x == 38)}")
print(f"success_lives: {p1_player.success_lives}")
print()

# Method 2: Try combining into one deck
print("=== METHOD 2: Combined 60-card deck (members + lives mixed) ===")
combined_deck = member_list + live_list
# Shuffle to mix them
random.Random(seed).shuffle(combined_deck)
state2 = engine_rust.PyGameState(db)
state2.initialize_game_with_seed(combined_deck, combined_deck, [38]*12, [38]*12, [], [], seed)
p2_player = state2.get_player(0)
print(f"Initial hand size: {len(p2_player.hand)}")
print(f"Initial deck size: {len(p2_player.deck)}")
print(f"Initial_deck total size: {len(p2_player.initial_deck)}")
print(f"Members in initial_deck: {sum(1 for x in p2_player.initial_deck if x != 38)}")
print(f"Lives (38) in initial_deck: {sum(1 for x in p2_player.initial_deck if x == 38)}")
print(f"success_lives: {p2_player.success_lives}")
print()

# Method 3: Put live cards at the end of deck
print("=== METHOD 3: Live cards at end of combined deck ===")
combined_deck3 = member_list + live_list  # Don't shuffle, keep lives at end
state3 = engine_rust.PyGameState(db)
state3.initialize_game_with_seed(combined_deck3, combined_deck3, [38]*12, [38]*12, [], [], seed)
p3_player = state3.get_player(0)
print(f"Initial hand size: {len(p3_player.hand)}")
print(f"Initial deck size: {len(p3_player.deck)}")
print(f"Initial_deck total size: {len(p3_player.initial_deck)}")
print(f"Members in initial_deck: {sum(1 for x in p3_player.initial_deck if x != 38)}")
print(f"Lives (38) in initial_deck: {sum(1 for x in p3_player.initial_deck if x == 38)}")
print(f"success_lives: {p3_player.success_lives}")
