import json
import sys

with open('data/consolidated_abilities.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== Analysis of consolidated_abilities.json ===')
print(f'Total entries: {len(data)}')

# Sample and analyze
samples = list(data.items())[:200]

issues = {
    'no_frames': 0, 
    'activated_no_cost': 0, 
    'single_return_only': 0,
    'empty_pseudocode': 0,
    'mismatched_description': 0
}

for key, val in samples:
    frames = val.get('frames', [])
    trigger = val.get('trigger', '')
    pseudocode = val.get('pseudocode', '')
    
    if not frames:
        issues['no_frames'] += 1
    elif len(frames) == 1 and frames[0].get('opcode') == 'RETURN':
        issues['single_return_only'] += 1
    
    if not pseudocode:
        issues['empty_pseudocode'] += 1
    
    if trigger == 'ACTIVATED' and frames:
        # Check if any frame looks like a cost
        has_cost = any(
            f.get('opcode', '') in ['PAY_ENERGY', 'DISCARD', 'MOVE_MEMBER', 'TAP_MEMBER', 'TAP_SELF']
            or 'cost' in str(f.get('decoded', '')).lower()
            or 'discard' in str(f.get('decoded', '')).lower()
            or 'pay' in str(f.get('decoded', '')).lower()
            for f in frames
        )
        if not has_cost:
            issues['activated_no_cost'] += 1

print('\n=== Issues in first 200 entries ===')
for k, v in issues.items():
    print(f'  {k}: {v}')

# Show sample activated abilities without costs
print('\n=== Sample ACTIVATED abilities (first 10) ===')
count = 0
for key, val in samples:
    if val.get('trigger') == 'ACTIVATED' and count < 10:
        count += 1
        print(f'\n--- Entry {count} ---')
        print(f'Key: {key[:60]}')
        print(f'Pseudocode: {val.get("pseudocode", "N/A")[:60]}')
        print(f'Number of frames: {len(val.get("frames", []))}')
        print('Frames:')
        for i, fr in enumerate(val.get('frames', [])[:5]):
            op = fr.get('opcode', 'N/A')
            dec = fr.get('decoded', 'N/A')[:50] if fr.get('decoded') else 'N/A'
            print(f'  {i}: {op} - {dec}')
