import json

with open('data/cards_compiled.json', encoding='utf-8') as f:
    raw_data = json.load(f)

member_db = raw_data.get('member_db', {})

# Get Umi R+ card (id=4122 as string)
print(f"Checking member_db for ID 4122...")
if '4122' in member_db:
    umi_card = member_db['4122']
    print(f"Card: {umi_card.get('card_no')} - {umi_card.get('name')}")
    print(f"AbilityText: {umi_card.get('ability_text', 'N/A')}\n")
    
    abilities = umi_card.get('abilities', [])
    print(f"Abilities ({len(abilities)}):")
    for i, ab in enumerate(abilities):
        print(f"  [{i}] trigger={ab.get('trigger')}")
        if ab.get('effects'):
            print(f"       Effects: {ab['effects']}")
else:
    print("ID 4122 not found!")
    print(f"Available IDs sample: {list(member_db.keys())[:20]}")







