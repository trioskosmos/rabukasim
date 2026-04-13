import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

# Find abilities with branch structures (choice/branch)
branch_abilities = []
for i, a in enumerate(data['abilities']):
    jp = a['source_ability_texts'][0].get('jp', '')
    logic = a['source_ability_texts'][0].get('logic', '')
    
    # Look for branch indicators
    if '以下から1つを選ぶ' in jp or '選ぶ' in jp or 'option' in logic.lower():
        branch_abilities.append({
            'index': i,
            'jp': jp,
            'logic': logic
        })

print(f"Found {len(branch_abilities)} abilities with branch structures\n")

# Show detailed examples
for i, ba in enumerate(branch_abilities[:10]):  # Show first 10
    print(f"=== Example {i+1} (Index {ba['index']}) ===")
    print(f"JP: {ba['jp'][:200]}...")
    print(f"Logic: {ba['logic'][:300]}...")
    print()
