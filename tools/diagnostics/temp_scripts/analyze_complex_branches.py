import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

# Find abilities with complex branch structures (choose one from)
complex_branches = []
for i, a in enumerate(data['abilities']):
    jp = a['source_ability_texts'][0].get('jp', '')
    logic = a['source_ability_texts'][0].get('logic', '')
    
    # Look for explicit "choose one from" patterns
    if '以下から1つを選ぶ' in jp or 'choose one from' in logic.lower():
        complex_branches.append({
            'index': i,
            'jp': jp,
            'logic': logic
        })

print(f"Found {len(complex_branches)} abilities with 'choose one from' structures\n")

# Show detailed examples with full content
for i, ba in enumerate(complex_branches[:5]):  # Show first 5
    print(f"=== Example {i+1} (Index {ba['index']}) ===")
    print(f"JP:\n{ba['jp']}\n")
    print(f"Logic:\n{ba['logic']}\n")
    print("=" * 80)
