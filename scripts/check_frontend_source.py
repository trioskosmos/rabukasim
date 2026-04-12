#!/usr/bin/env python3
"""
Check which file the frontend is reading from by comparing ability 249 data
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Check ability_frame_source.json
print("=== ability_frame_source.json ===")
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_source = json.load(f)
ability_249_source = frame_source['abilities'][249]
print(f"Text: {ability_249_source.get('primary_text_jp', '')[:80]}...")
print(f"Frames: {len(ability_249_source.get('frames', []))}")
for frame in ability_249_source.get('frames', []):
    print(f"  Frame {frame['frame_index']}: {frame['op']}")

# Check ability_frame_source.compact.json
print("\n=== ability_frame_source.compact.json ===")
try:
    with open('data/ability_frame_source.compact.json', 'r', encoding='utf-8') as f:
        compact = json.load(f)
    if 'abilities' in compact:
        ability_249_compact = compact['abilities'][249]
        print(f"Frames: {len(ability_249_compact.get('frames', []))}")
        for frame in ability_249_compact.get('frames', []):
            print(f"  Frame {frame['frame_index']}: {frame['op']}")
    else:
        print("No 'abilities' key in compact file")
except FileNotFoundError:
    print("File not found")

# Check cards_compiled.json
print("\n=== cards_compiled.json ===")
try:
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        cards_compiled = json.load(f)
    # Search for card_id 29 (東條 希)
    found = False
    for card in cards_compiled:
        if card.get('card_id') == 29:
            found = True
            print(f"Found card: {card.get('name')}")
            if 'abilities' in card:
                for i, ability in enumerate(card['abilities']):
                    print(f"  Ability {i}:")
                    if 'frames' in ability:
                        print(f"    Frames: {len(ability['frames'])}")
                        for frame in ability['frames']:
                            print(f"      Frame {frame['frame_index']}: {frame['op']}")
            break
    if not found:
        print("Card ID 29 not found")
except FileNotFoundError:
    print("File not found")

# Check ability_runtime_entrypoints.json
print("\n=== ability_runtime_entrypoints.json ===")
try:
    with open('data/ability_runtime_entrypoints.json', 'r', encoding='utf-8') as f:
        runtime = json.load(f)
    # Search for ability 249
    if '249' in runtime:
        print(f"Found ability 249: {runtime['249']}")
    else:
        print("Ability 249 not found")
except FileNotFoundError:
    print("File not found")
