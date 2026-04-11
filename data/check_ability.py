import json
import sys

idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0

with open('ability_frame_source.json', encoding='utf-8') as f:
    data = json.load(f)

ab = data['abilities'][idx]
print(f'Ability #{idx}')
print(f'Text: {ab.get("primary_text_jp", "")[:100]}...')
print(f'Trigger: {ab.get("trigger")} (id={ab.get("trigger_id")})')
print(f'Frames: {len(ab.get("frames", []))}')
for i, f in enumerate(ab.get("frames", [])[:5]):
    print(f'  Frame {i}: {f.get("op")}, value={f.get("value")}')
print(f'Cards: {[r.get("name") for r in ab.get("card_refs", [])[:3]]}')
