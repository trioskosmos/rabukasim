import json
data = json.load(open('data/cards_compiled.json', encoding='utf-8'))
card590 = data['member_db']['590']
print("===== CARD 590 FIX STATUS =====")
print("Number of abilities:", len(card590['abilities']))
if card590['abilities']:
    print("\nAbility 0 pseudocode (first 150 chars):")
    print(card590['abilities'][0]['pseudocode'][:150])
