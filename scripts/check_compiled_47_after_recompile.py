import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    compiled = json.load(f)

card_47 = compiled['live_db']['47']
abilities = card_47.get('abilities', [])

print(f"Card 47: {card_47.get('name', 'Unknown')}")
print(f"Abilities count: {len(abilities)}")

for idx, ability in enumerate(abilities):
    print(f"\nAbility {idx}:")
    print(f"  Trigger: {ability.get('trigger', 'Unknown')}")
    frame_program = ability.get('frame_program', {})
    frames = frame_program.get('frames', [])
    print(f"  Frames count: {len(frames)}")
    
    for f_idx, frame in enumerate(frames):
        print(f"  Frame {f_idx}:")
        print(f"    opcode: {frame.get('opcode')}")
        print(f"    attr: {frame.get('attr')}")
        if frame.get('opcode') == 65:  # SELECT_MEMBER
            print(f"    >>> SELECT_MEMBER frame")
        if frame.get('opcode') == 12:  # ADD_HEARTS
            print(f"    >>> ADD_HEARTS frame")
