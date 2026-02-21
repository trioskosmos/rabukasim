
import json

path = 'launcher/static_content/data/cards_compiled.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# The keys are 'member_db', 'live_db'
for mid, member in data['member_db'].items():
    if member.get('card_no') == 'PL!N-PR-009-PR':
        print(f"Member ID: {mid}")
        print(json.dumps(member, indent=2, ensure_ascii=False))
        break
