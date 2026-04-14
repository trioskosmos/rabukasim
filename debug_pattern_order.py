import json
import re
import sys

# Load the patterns from the script
sys.path.insert(0, 'tools')
from extract_abilities_to_template import DSL_PATTERNS

# Load the abilities
data = json.load(open('data/abilities_extracted_simple.json', 'r', encoding='utf-8'))

# Get low coverage abilities
low_cov = [a for a in data['abilities'] if a['coverage'] < 0.5]

for ability in low_cov:
    print(f"\n{'='*60}")
    print(f"Ability: {ability['jp']}")
    print(f"Coverage: {ability['coverage']:.1%}")
    print(f"{'='*60}")
    
    # Test each pattern against this ability
    matches = []
    for pattern in DSL_PATTERNS:
        if pattern['name'] in ['clause_comma', 'sentence_period', 'comma_period', 'colon_action', 'parenthetical_note']:
            continue  # Skip generic patterns
        
        regex = pattern['regex']
        try:
            if re.search(regex, ability['jp']):
                matches.append(pattern['name'])
        except:
            pass
    
    print(f"\nPatterns that match this ability:")
    for i, name in enumerate(matches, 1):
        print(f"  {i}. {name}")
    
    # Show which patterns actually matched in the data
    print(f"\nPatterns that matched in data:")
    for match in ability.get('pattern_matches', []):
        print(f"  - {match['pattern_name']}: {match['matched_text']}")
