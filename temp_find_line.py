import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
for i, line in enumerate(lines):
    if '"card_id": 462' in line and '"ability_index": 1' in line:
        print(f"Line {i+1}: {line.strip()}")
    if '"ability_index": 1' in line and i > 0:
        prev_lines = ''.join(lines[max(0,i-3):i+1])
        if '462' in prev_lines:
            print(f"Context around line {i+1}:")
            print(prev_lines)
            print("---")
