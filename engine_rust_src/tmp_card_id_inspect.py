import json
from pathlib import Path
root = Path(__file__).resolve().parent
path = root / 'data' / 'cards_compiled.json'

with path.open('r', encoding='utf-8') as f:
    obj = json.load(f)
ids = []
for table in ['members', 'live', 'energy', 'stuff', 'discards']:
    if table in obj:
        ids.extend(int(k) for k in obj[table].keys())

print('max id', max(ids))
print('min id', min(ids))
print('count ids', len(ids))
print('ids > 32767', sum(1 for i in ids if i > 32767))
print('ids > 65535', sum(1 for i in ids if i > 65535))
