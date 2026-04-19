import json

authored = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))

print(f"Authored abilities: {len(authored['abilities'])}")

# Look at first few authored abilities to understand expected variable names
for i, auth_ab in enumerate(authored['abilities'][:5]):
    print(f"\nAuthored ability {i}:")
    print(f"  Cards: {auth_ab.get('card_refs', [])[:3]}")
    print(f"  Trigger: {auth_ab.get('trigger')}")
    print(f"  Text: {auth_ab.get('primary_text_jp', '')[:100]}")
    
    frames = auth_ab.get('frames', [])
    print(f"  Frames: {len(frames)}")
    
    for j, frame in enumerate(frames[:5]):
        print(f"\n  Frame {j}:")
        print(f"    op: {frame.get('op')}")
        print(f"    value: {frame.get('value')}")
        print(f"    slot: {frame.get('slot')}")
        print(f"    attr: {frame.get('attr')}")
        print(f"    params: {frame.get('params')}")
    
    print("\n" + "="*80)
