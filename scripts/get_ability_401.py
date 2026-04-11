#!/usr/bin/env python3
"""
Get ability 401 from frame source
"""
import json
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    frame_data = json.load(f)

ability_401 = frame_data['abilities'][401]
print(f"Ability 401 from frame source:")
print(json.dumps(ability_401, ensure_ascii=False, indent=2))
