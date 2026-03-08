import re

with open("alphazero/training/overnight_vanilla.py", "r") as f:
    code = f.read()

# Replace map_engine_to_vanilla definition that is still lingering
code = re.sub(r'def map_engine_to_vanilla.*?return -1', '', code, flags=re.DOTALL)
code = re.sub(r'LOGIC_ID_MASK = 0x0FFF', '', code)

# Clean up mapping_info
code = re.sub(r'mapping_info = \[\]\s*for aid in legal_ids\[:8\]:\s*vid = map_engine_to_vanilla.*?\)\s*mapping_info\.append\(f"\{aid\}->\{vid\}"\)',
              r'mapping_info = []\n                for aid in legal_ids[:8]:\n                    mapping_info.append(str(aid))', code, flags=re.DOTALL)

# Clean up policy target
code = re.sub(r'vid = map_engine_to_vanilla.*?\)', 'vid = engine_id', code)
code = re.sub(r'vid = map_engine_to_vanilla\(p_data, aid, initial_decks\[state\.current_player\]\)', 'vid = aid', code)
code = re.sub(r'vid = map_engine_to_vanilla\(state_json\[\'players\'\]\[state\.current_player\], aid, initial_decks\[state\.current_player\]\)', 'vid = aid', code)

with open("alphazero/training/overnight_vanilla.py", "w") as f:
    f.write(code)
