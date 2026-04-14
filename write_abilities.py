import json

data = json.load(open('data/abilities_extracted_simple.json', 'r', encoding='utf-8'))

low_cov = [a for a in data['abilities'] if a['coverage'] < 0.5]

with open('low_abilities.txt', 'w', encoding='utf-8') as f:
    for ability in low_cov:
        f.write(f"=== Coverage: {ability['coverage']:.1%} ===\n")
        f.write(f"Full ability: {ability['jp']}\n")
        f.write(f"Pattern matches:\n")
        for match in ability.get('pattern_matches', []):
            f.write(f"  {match['pattern_name']}: {match['matched_text']}\n")
        f.write("\n")
