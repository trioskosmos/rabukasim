import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

print("Abilities with only trigger conditions (no operations):\n")

trigger_only_count = 0
for i, a in enumerate(data['abilities']):
    logic = a['source_ability_texts'][0].get('logic', '')
    jp = a['source_ability_texts'][0].get('jp', '')
    
    # Check if logic only has "if" statements and no actual operations
    if logic:
        lines = [line.strip() for line in logic.split('\n') if line.strip()]
        # Check if all lines start with "if" or "optional"
        if all(line.startswith(('if', 'optional')) for line in lines):
            trigger_only_count += 1
            if trigger_only_count <= 10:
                print(f"Index {i}:")
                print(f"  Trigger: {a.get('trigger', 'N/A')}")
                print(f"  JP: {jp[:150]}...")
                print(f"  Logic: {logic[:200]}...")
                print()

print(f"\nTotal trigger-only abilities: {trigger_only_count}")
