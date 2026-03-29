import json

with open('../data/cards_compiled.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Count cards with effects but no bytecode
members = d.get('member_db', {})
count = 0
cards_affected = []
for cid, card in members.items():
    for ab in card.get('abilities', []):
        has_effects = len(ab.get('effects', [])) > 0
        has_bytecode = ab.get('bytecode') is not None and len(ab.get('bytecode', [])) > 0
        has_frames = ab.get('frame_program') is not None
        if has_effects and not has_bytecode and not has_frames:
            count += 1
            cards_affected.append((cid, card.get('card_no'), len(ab.get('effects'))))
            if count <= 10:
                print(f"Card {cid} {card.get('card_no')}: has {len(ab.get('effects'))} effects, no bytecode/frames")
                for i, ef in enumerate(ab.get('effects', [])[:2]):
                    print(f"  Effect {i}: type={ef.get('effect_type')}, value={ef.get('value')}")

print(f"\nTotal abilities with effects but no bytecode/frames: {count}")
print(f"Sample cards affected: {[c[1] for c in cards_affected[:5]]}")
