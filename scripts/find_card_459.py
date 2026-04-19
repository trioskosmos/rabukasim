import json

data = json.load(open('data/cards_compiled.json', encoding='utf-8'))
print("Searching for card ID 459...")
if '459' in data['member_db']:
    print(f'Found in member_db: 459')
    print(json.dumps(data['member_db']['459']['abilities'][0]['frame_program'], indent=2, ensure_ascii=False)[:3000])
elif '459' in data['live_db']:
    print(f'Found in live_db: 459')
    print(json.dumps(data['live_db']['459']['abilities'][0]['frame_program'], indent=2, ensure_ascii=False)[:3000])
else:
    print("Card 459 not found in either db")
