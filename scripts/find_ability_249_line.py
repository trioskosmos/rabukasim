#!/usr/bin/env python3
"""
Find the line number of ability 249 in ability_frame_source.json
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the frame source
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Search for the ability 249 text
target_text = "ライブ開始時手札を2枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る"

# Find all occurrences
import re
matches = list(re.finditer(re.escape(target_text), content))

print(f"Found {len(matches)} occurrences of the text")
for i, match in enumerate(matches):
    # Get line number
    line_num = content[:match.start()].count('\n') + 1
    print(f"Occurrence {i+1}: Line {line_num}")
    
    # Get surrounding context
    start = max(0, match.start() - 200)
    end = min(len(content), match.end() + 200)
    context = content[start:end]
    print(f"Context: ...{context[:100]}...")
