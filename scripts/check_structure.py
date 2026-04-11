#!/usr/bin/env python3
"""
Check the structure of ability_frame_source.json
"""
import json

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

print(f"Frame source schema: {frame_data.get('schema')}")
print(f"Frame source abilities count: {len(frame_data['abilities'])}")
print(f"Frame source has ability_index field: {'ability_index' in frame_data['abilities'][0]}")

# Check the semantic dump
with open('data/ability_semantic_dump.json', 'r', encoding='utf-8') as f:
    semantic_data = json.load(f)

print(f"\nSemantic dump schema: {semantic_data.get('schema')}")
print(f"Semantic dump ability count: {semantic_data['summary']['ability_count']}")

# Check if abilities 401+ exist in frame source
print(f"\nFrame source has {len(frame_data['abilities'])} abilities")
print(f"Checking if ability 401 exists in semantic dump...")
ability_401_found = False
for ability in semantic_data['abilities']:
    if ability['ability_index'] == 401:
        ability_401_found = True
        print(f"Found ability 401 in semantic dump")
        print(f"Trigger: {ability['trigger']}")
        print(f"Text: {ability['primary_text_jp'][:100]}...")
        break

if not ability_401_found:
    print("Ability 401 not found in semantic dump")
