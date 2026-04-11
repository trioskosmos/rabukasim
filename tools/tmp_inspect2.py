import json
from pathlib import Path
p = Path(r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\ability_frame_source.json')
with p.open('r', encoding='utf-8') as f:
    data = json.load(f)
abilities = data.get('abilities', data.get('signature_groups', []))
for ab in abilities:
    ops = [frame.get('op') for frame in ab.get('frames', []) if frame.get('op')]
    if 'ADD_TO_HAND' in ops and 'MOVE_MEMBER' in ops:
        print(ab.get('primary_text_jp', '')[:120].replace('\n',' '))
        print(ops)
        print('---')
