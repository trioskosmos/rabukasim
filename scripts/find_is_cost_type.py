import re

with open('tools/ability_extraction/effect_parser.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')
    
for i, line in enumerate(lines):
    if 'is_cost_type' in line and 'true' in line.lower():
        print(f"Line {i}: {line.strip()}")
