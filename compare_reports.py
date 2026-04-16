import json

# Compare actual JSON outputs
try:
    with open('data/abilities_extracted_from_cards_baseline.json', 'r', encoding='utf-8') as f:
        baseline = json.load(f)
    
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        current = json.load(f)
    
    # Compare the full JSON structures
    if baseline == current:
        print('Match: True - JSON outputs are identical')
    else:
        print('Match: False - JSON outputs differ')
        
        # Find differences
        baseline_abilities = {ab['triggerless_text']: ab for ab in baseline['unique_abilities']}
        current_abilities = {ab['triggerless_text']: ab for ab in current['unique_abilities']}
        
        # Check for missing or added abilities
        missing = set(baseline_abilities.keys()) - set(current_abilities.keys())
        added = set(current_abilities.keys()) - set(baseline_abilities.keys())
        
        if missing:
            print(f'Missing abilities: {len(missing)}')
            for text in sorted(missing)[:5]:
                print(f'  - {text[:50]}...')
        
        if added:
            print(f'Added abilities: {len(added)}')
            for text in sorted(added)[:5]:
                print(f'  - {text[:50]}...')
        
        # Check for differences in common abilities
        common = set(baseline_abilities.keys()) & set(current_abilities.keys())
        diff_count = 0
        for text in common:
            if baseline_abilities[text] != current_abilities[text]:
                diff_count += 1
                if diff_count <= 5:
                    print(f'Difference in: {text[:50]}...')
                    print(f'  Baseline cost: {baseline_abilities[text].get("cost")}')
                    print(f'  Current cost: {current_abilities[text].get("cost")}')
        
        if diff_count > 5:
            print(f'... and {diff_count - 5} more differences')
        
        print(f'Total differences: {len(missing)} missing, {len(added)} added, {diff_count} changed')
        
except FileNotFoundError as e:
    print(f'Error: {e}')
    print('Baseline file not found. Run: Copy-Item data/abilities_extracted_from_cards.json data/abilities_extracted_from_cards_baseline.json')
