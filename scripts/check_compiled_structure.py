import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    compiled = json.load(f)

card_47 = compiled['live_db']['47']
abilities = card_47.get('abilities', [])

print(f"Card 47 keys: {list(card_47.keys())}")

if abilities:
    first_ability = abilities[0]
    print(f"\nFirst ability keys: {list(first_ability.keys())}")
    frame_program = first_ability.get('frame_program', {})
    print(f"Frame program keys: {list(frame_program.keys())}")
    
    if 'frames' in frame_program:
        frames = frame_program['frames']
        print(f"\nFirst frame structure: {frames[0] if frames else 'No frames'}")
