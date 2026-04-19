import json

authored = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
generated = json.load(open('data/ability_frame_source.json', encoding='utf-8'))

mismatch_count = 0
# Find matching abilities by trigger and text
for auth_ab in authored['abilities']:
    auth_trigger = auth_ab.get('trigger', '')
    auth_text = auth_ab.get('primary_text_jp', '')[:50]
    auth_cards = auth_ab.get('card_refs', [])[:2]
    
    # Find matching generated ability
    for gen_ab in generated['abilities']:
        gen_trigger = gen_ab.get('trigger', '')
        gen_text = gen_ab.get('primary_text_jp', '')[:50]
        gen_cards = gen_ab.get('card_refs', [])[:2]
        
        if auth_trigger == gen_trigger and auth_text == gen_text and auth_cards == gen_cards:
            auth_frames = auth_ab.get('frames', [])
            gen_frames = gen_ab.get('frames', [])
            
            if len(auth_frames) != len(gen_frames):
                print(f"Frame count mismatch: {auth_trigger}")
                print(f"Cards: {auth_cards}")
                print(f"Text: {auth_text}")
                print(f"Authored: {len(auth_frames)} frames, Generated: {len(gen_frames)} frames")
                print()
                mismatch_count += 1
                if mismatch_count >= 10:
                    exit()
            break
