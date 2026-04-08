import json
import pathlib
import re
from collections import Counter

p = pathlib.Path(r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\ability_frame_source.json')
obj = json.loads(p.read_text(encoding='utf-8'))
print('TOPLEVEL', type(obj).__name__)
if isinstance(obj, dict):
    print('KEYS', list(obj.keys())[:20])
    for k, v in obj.items():
        if isinstance(v, list):
            print('LIST', k, len(v))
        elif isinstance(v, dict):
            print('DICT', k, len(v))

# Find the main array of entries heuristically.
entries = None
entry_container_name = None
if isinstance(obj, dict):
    for k, v in obj.items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and ('cards' in v[0] or 'signature_source' in v[0]):
            entries = v
            entry_container_name = k
            break
        if isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, list) and vv and isinstance(vv[0], dict) and ('cards' in vv[0] or 'signature_source' in vv[0]):
                    entries = vv
                    entry_container_name = f'{k}.{kk}'
                    break
            if entries is not None:
                break
elif isinstance(obj, list):
    entries = obj
    entry_container_name = 'root_list'
print('ENTRY_CONTAINER', entry_container_name, 'COUNT', len(entries) if entries is not None else None)

kw = re.compile(r'(may|optional|もよい|選んでもよい|してもよい)', re.I)

candidates = []
for e in entries or []:
    text_parts = []
    if isinstance(e, dict):
        if e.get('primary_text_jp'):
            text_parts.append(e['primary_text_jp'])
        if e.get('primary_text_en'):
            text_parts.append(e['primary_text_en'])
        for item in e.get('source_ability_texts', []) or []:
            if isinstance(item, dict):
                if item.get('jp'):
                    text_parts.append(item['jp'])
                if item.get('en'):
                    text_parts.append(item['en'])
    text = '\n'.join(text_parts)
    if not kw.search(text):
        continue
    frames = e.get('frames') or []
    frame_ops = [f.get('op') for f in frames if isinstance(f, dict)]
    opt_frames = [i for i, f in enumerate(frames) if isinstance(f, dict) and f.get('attr', {}).get('is_optional') == 1]
    candidates.append((e, text, frame_ops, opt_frames))

print('OPTIONAL_CANDIDATES', len(candidates))
for e, text, frame_ops, opt_frames in candidates[:80]:
    print('---')
    print('card_no=', e.get('card_no'), 'card_id=', e.get('card_id'), 'ability_index=', e.get('ability_index'), 'trigger=', e.get('trigger'))
    print('name=', e.get('name'))
    print('opt_frames=', opt_frames)
    print('ops=', frame_ops)
    print('text=', text[:240].replace('\n', ' '))
