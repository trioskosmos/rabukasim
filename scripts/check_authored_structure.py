import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
print(f'Type: {type(data)}')
if isinstance(data, dict):
    print(f'Keys: {list(data.keys())}')
if isinstance(data, list):
    print(f'Length: {len(data)}')
    if len(data) > 0:
        print(f'First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else "N/A"}')
