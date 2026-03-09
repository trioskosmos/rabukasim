import json
import engine_rust
from pathlib import Path

# Load database
root_dir = Path('.')
db_path = root_dir / 'data' / 'cards_vanilla.json'
if not db_path.exists(): db_path = root_dir / 'data' / 'cards_compiled.json'
with open(db_path, 'r', encoding='utf-8') as f: db_json = json.load(f)

# Create a simple test deck  
test_members = [173] * 60  # 60 members as per typical deck
test_lives = [38] * 12  # 12 lives as per typical deck

# Create game state
db_json_str = json.dumps(db_json)
db = engine_rust.PyCardDatabase(db_json_str)

state = engine_rust.PyGameState(db)
state.initialize_game_with_seed(test_members, test_members, [38]*12, [38]*12, test_lives, test_lives, 42)

print(f'Game initialized')
print(f'P0 starting lives: {len(state.get_player(0).success_lives)}')
print(f'P1 starting lives: {len(state.get_player(1).success_lives)}')
print(f'Is terminal: {state.is_terminal()}')

pj = json.loads(state.to_json())
print(f'Current phase: {pj.get("phase", "N/A")}')
print(f'P0 hand size: {len(pj.get("players", [{}])[0].get("hand", []))}')
print(f'P0 deck size: {len(pj.get("players", [{}])[0].get("deck", []))}')
print(f'Full state: {json.dumps(pj, indent=2)[:2000]}')
