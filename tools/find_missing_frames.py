import json
import re
from pathlib import Path

path = Path('data') / 'ability_frame_source.json'
with path.open(encoding='utf-8') as f:
    data = json.load(f)

patterns = [
    ('手札に加える', {'ADD_TO_HAND', 'RECOVER_MEMBER', 'RECOVER_LIVE', 'DRAW', 'PLAY_MEMBER_FROM_DISCARD', 'PLAY_LIVE_FROM_DISCARD', 'RECOVER_TO_HAND'}),
    ('登場させる', {'PLAY_MEMBER', 'PLAY_MEMBER_FROM_HAND', 'PLAY_MEMBER_FROM_DISCARD', 'SUMMON_MEMBER', 'RECOVER_MEMBER', 'RECOVER_LIVE', 'DEPLOY_MEMBER', 'SUMMON'}),
    ('ウェイトにする', {'MOVE_MEMBER', 'TAP_OPPONENT', 'TAP_SELF', 'WAIT', 'MOVE_TO_WAIT'}),
    ('公開する', {'REVEAL_CARDS', 'SHOW_CARDS', 'LOOK', 'REVEAL'}),
    ('控え室に置く', {'MOVE_TO_DISCARD', 'DISCARD', 'SEND_TO_DISCARD', 'DISCARD_CARD'}),
    ('手札を1枚控え室に置く', {'MOVE_TO_DISCARD', 'DISCARD'}),
    ('この能力を起動するためのコスト', {'REDUCE_COST', 'REDUCE_HEART_REQ', 'SET_HEART_COST', 'ACTIVATE_ENERGY', 'ACTIVATE_MEMBER'}),
    ('コストは2減る', {'REDUCE_COST', 'REDUCE_HEART_REQ'}),
    ('必要ハートを', {'REDUCE_HEART_REQ', 'SET_HEART_COST'}),
    ('手札にあるこのメンバーカードのコスト', {'REDUCE_COST'}),
    ('手札にあるこのカードの必要ハート', {'REDUCE_HEART_REQ'}),
    ('選んだハート', {'COLOR_SELECT', 'SELECT_MODE', 'ADD_HEARTS'}),
]

candidates = []

for idx, ability in enumerate(data['abilities']):
    text = ability.get('primary_text_jp', '')
    frames = ability.get('frames', [])
    ops = {frame.get('op') for frame in frames}
    issues = []
    for phrase, expected_ops in patterns:
        if phrase in text:
            if not ops & expected_ops:
                issues.append((phrase, expected_ops, ops))
    if issues:
        candidates.append((idx, text, frames, issues))

print('CANDIDATES', len(candidates))
for idx, text, frames, issues in candidates[:200]:
    print('---')
    print('INDEX', idx)
    print(text)
    print('OPS', sorted({f.get('op') for f in frames}))
    for phrase, expected_ops, ops in issues:
        print('MISSING', phrase, 'expected any of', sorted(expected_ops))
    print()