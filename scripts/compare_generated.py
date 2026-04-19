import json

generated = json.load(open('data/ability_frame_source.json', encoding='utf-8'))

print(f"Generated abilities: {len(generated['abilities'])}")

# Look at first few generated abilities to see what variable names I'm using
for i, gen_ab in enumerate(generated['abilities'][:5]):
    print(f"\nGenerated ability {i}:")
    print(f"  Cards: {gen_ab.get('card_refs', [])[:3]}")
    print(f"  Trigger: {gen_ab.get('trigger')}")
    print(f"  Text: {gen_ab.get('primary_text_jp', '')[:100]}")
    
    frames = gen_ab.get('frames', [])
    print(f"  Frames: {len(frames)}")
    
    for j, frame in enumerate(frames[:5]):
        print(f"\n  Frame {j}:")
        print(f"    op: {frame.get('op')}")
        print(f"    value: {frame.get('value')}")
        print(f"    slot: {frame.get('slot')}")
        print(f"    attr: {frame.get('attr')}")
        print(f"    params: {frame.get('params')}")
    
    print("\n" + "="*80)
