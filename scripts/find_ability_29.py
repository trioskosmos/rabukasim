#!/usr/bin/env python3
"""
Find ability 29 (東條 希) and check its frame_verification
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

# Load semantic dump for reference
with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    semantic_data = json.load(f)

# Search for the ability with the specific text
for i, ability in enumerate(semantic_data['abilities']):
    text = ability['primary_text_jp']
    if 'ライブ開始時手札を2枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る' in text:
        print(f"Found ability {i} in semantic dump")
        print(f"Text: {text}")
        print(f"\nFrame data for ability {i}:")
        frame_ability = frame_data['abilities'][i]
        print(f"Frames: {frame_ability.get('frames', [])}")
        if 'frame_verification' in frame_ability:
            print(f"\nFrame verification:")
            print(json.dumps(frame_ability['frame_verification'], indent=2, ensure_ascii=False))
        break
