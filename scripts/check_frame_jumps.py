import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    compiled = json.load(f)

card_47 = compiled['live_db']['47']
ability = card_47['abilities'][0]
frames = ability['frame_program']['frames']

print("Frame sequence for card 47 ability 0:")
for f_idx, frame in enumerate(frames):
    op = frame.get('op', 'UNKNOWN')
    val = frame.get('value', 0)
    print(f"{f_idx}: {op} value={val}")
    if op == 'JUMP' or op == 'JUMP_IF_FALSE':
        target = f_idx + val
        if target < len(frames):
            target_op = frames[target].get('op', 'UNKNOWN')
            print(f"   -> jumps to {target} ({target_op})")
