import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    raw_data = json.load(f)

member_db = raw_data.get('member_db', {})

# Get Umi R+ card (id=4122)
umi_card = member_db.get(4122)
if umi_card:
    print(f"Card: {umi_card.get('card_no')} - {umi_card.get('name')}")
    print(f"\nAbility Text: {umi_card.get('ability_text', 'N/A')}\n")
    
    abilities = umi_card.get('abilities', [])
    print(f"Abilities ({len(abilities)}):")
    for i, ab in enumerate(abilities):
        print(f"  [{i}] trigger={ab.get('trigger')}, effects={len(ab.get('effects', []))}")
        if ab.get('effects'):
            for j, eff in enumerate(ab['effects']):
                print(f"       [{j}] {eff}")





