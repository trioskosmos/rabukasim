import json

# Load authored frame source
with open('data/ability_frame_source_authored.json', 'r', encoding='utf-8') as f:
    authored_source = json.load(f)

# Load compiled cards
with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    compiled = json.load(f)

# Find card 47 in authored source
authored_card_47 = None
for idx, ability in enumerate(authored_source['abilities']):
    source_texts = ability.get('source_ability_texts', [])
    for source_text in source_texts:
        card_examples = source_text.get('card_examples', [])
        for example in card_examples:
            # Check for "PL!S-47" or similar pattern
            if '-47-' in example or example.startswith('47') or ' 47 ' in example:
                authored_card_47 = ability
                print(f"Found card 47 in example: {example}")
                break
        if authored_card_47:
            break
    if authored_card_47:
        break

if authored_card_47 is None:
    print("Could not find card 47 in authored frame source")
    print("Searching for any card with '47' in examples...")
    for idx, ability in enumerate(authored_source['abilities']):
        source_texts = ability.get('source_ability_texts', [])
        for source_text in source_texts:
            card_examples = source_text.get('card_examples', [])
            for example in card_examples:
                if '47' in str(example):
                    print(f"  Found '47' in: {example}")
                    authored_card_47 = ability
                    break
            if authored_card_47:
                break
        if authored_card_47:
            break

# Find card 47 in compiled
compiled_card_47 = compiled['live_db']['47']

print(f"\nCompiled card 47 name: {compiled_card_47.get('name', 'Unknown')}")

if authored_card_47 is None:
    print("\nCard 47 not found in authored frame source")
    print("This means the compiler is using semantic frames, not authored frames")
    print("Need to fix semantic_to_frame_converter.py instead of authored frame source")
    exit(0)

print("Authored frame source for card 47:")
print(f"  Frames count: {len(authored_card_47.get('frames', []))}")
if authored_card_47.get('frames'):
    print(f"  First SELECT_MEMBER frame: {authored_card_47['frames'][0]}")

print("\nCompiled card 47:")
print(f"  Abilities count: {len(compiled_card_47.get('abilities', []))}")
if compiled_card_47.get('abilities'):
    first_ability = compiled_card_47['abilities'][0]
    print(f"  First ability frames count: {len(first_ability.get('frame_program', {}).get('frames', []))}")
    if first_ability.get('frame_program', {}).get('frames'):
        print(f"  First SELECT_MEMBER frame: {first_ability['frame_program']['frames'][0]}")

print("\nAre they using the same frames?")
authored_frames = authored_card_47.get('frames', [])
compiled_frames = compiled_card_47['abilities'][0]['frame_program']['frames']
print(f"  Authored frames count: {len(authored_frames)}")
print(f"  Compiled frames count: {len(compiled_frames)}")
print(f"  Same structure: {len(authored_frames) == len(compiled_frames)}")
