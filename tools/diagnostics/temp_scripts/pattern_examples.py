import json
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Load the extracted abilities data
data_file = Path(__file__).parent.parent.parent.parent / "data" / "abilities_extracted.json"
with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get the patterns section
patterns_data = data['dsl_pattern_analysis']['pattern_variables']

# Select grammar-based patterns to examine with their definitions
pattern_info = {
    'zone_card_count_condition_zone_to_zone_add': {
        'structure': 'Zone card count condition to zone add',
        'regex': r'([^。]+)の([^。]+)にカードが(\d+)枚以上ある場合、([^。]+)の([^。]+)から([^。]+)を(\d+)枚([^。]+)に加える',
        'template': '⟦SOURCE1⟧の⟦ZONE1⟧にカードが⟦NUMBER1⟧枚以上ある場合、⟦SOURCE2⟧の⟦ZONE2⟧から⟦CARD_TYPE⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に加える',
        'var_names': ['SOURCE1', 'ZONE1', 'NUMBER1', 'SOURCE2', 'ZONE2', 'CARD_TYPE', 'NUMBER2', 'DESTINATION'],
    },
    'zone_to_zone_add': {
        'structure': 'Zone to zone add',
        'regex': r'([^。]+)の([^。]+)から([^。]+)を(\d+)枚([^。]+)に加える',
        'template': '⟦SOURCE⟧の⟦ZONE⟧から⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える',
        'var_names': ['SOURCE', 'ZONE', 'CARD_TYPE', 'NUMBER', 'DESTINATION'],
    },
    'zone_card_presence_condition': {
        'structure': 'Zone card presence condition',
        'regex': r'([^。]+)の([^。]+)にある([^。]+)が(\d+)枚以上あるかぎり、([^。]+)を得る',
        'template': '⟦SOURCE⟧の⟦ZONE⟧にある⟦CARD⟧が⟦NUMBER⟧枚以上あるかぎり、⟦GAIN⟧を得る',
        'var_names': ['SOURCE', 'ZONE', 'CARD', 'NUMBER', 'GAIN'],
    },
    'energy_count_condition': {
        'structure': 'Energy count condition',
        'regex': r'([^。]+)の([^。]+)が(\d+)枚以上ある場合',
        'template': '⟦SOURCE⟧の⟦RESOURCE⟧が⟦NUMBER⟧枚以上ある場合',
        'var_names': ['SOURCE', 'RESOURCE', 'NUMBER'],
    },
    'zone_count_condition_card_draw': {
        'structure': 'Zone count condition card draw',
        'regex': r'([^。]+)の([^。]+)が(\d+)枚以上ある場合、([^。]+)を(\d+)枚([^。]+)',
        'template': '⟦SOURCE⟧の⟦RESOURCE⟧が⟦NUMBER1⟧枚以上ある場合、⟦CARD⟧を⟦NUMBER2⟧枚⟦ACTION⟧',
        'var_names': ['SOURCE', 'RESOURCE', 'NUMBER1', 'CARD', 'NUMBER2', 'ACTION'],
    },
    'comma_separated_action': {
        'structure': 'Comma separated action',
        'regex': r'([^。]+)、([^。]+)を([^。]+)',
        'template': '⟦CONDITION⟧、⟦TARGET⟧を⟦ACTION⟧',
        'var_names': ['CONDITION', 'TARGET', 'ACTION'],
    },
    'condition_action_period': {
        'structure': 'Condition action period',
        'regex': r'([^。]+)が([^。]+)場合、([^。]+)を([^。]+)',
        'template': '⟦SUBJECT⟧が⟦CONDITION⟧場合、⟦TARGET⟧を⟦ACTION⟧',
        'var_names': ['SUBJECT', 'CONDITION', 'TARGET', 'ACTION'],
    },
    'duration_resource_gain': {
        'structure': 'Duration resource gain',
        'regex': r'([^。]+)まで、([^。]+)を得る',
        'template': '⟦DURATION⟧まで、⟦RESOURCE⟧を得る',
        'var_names': ['DURATION', 'RESOURCE'],
    },
    'simple_resource_gain': {
        'structure': 'Simple resource gain',
        'regex': r'([^。]+)を得る',
        'template': '⟦RESOURCE⟧を得る',
        'var_names': ['RESOURCE'],
    },
    'cost_optional_duration_resource_gain': {
        'structure': 'Cost optional duration resource gain',
        'regex': r'([^。]+)支払ってもよい：([^。]+)まで、([^。]+)を得る',
        'template': '⟦COST⟧支払ってもよい：⟦DURATION⟧まで、⟦RESOURCE⟧を得る',
        'var_names': ['COST', 'DURATION', 'RESOURCE'],
    },
}

print("=" * 100)
print("GRAMMAR-BASED PATTERN MATCHING EXAMPLES")
print("=" * 100)
print()

for pattern_name, pattern_def in pattern_info.items():
    if pattern_name not in patterns_data:
        continue
    
    variables = patterns_data[pattern_name]
    if not variables:
        continue
    
    print(f"\n{'=' * 100}")
    print(f"PATTERN: {pattern_name}")
    print(f"{'=' * 100}")
    print(f"Structure: {pattern_def['structure']}")
    print(f"Regex: {pattern_def['regex']}")
    print(f"Template: {pattern_def['template']}")
    print(f"Total matches: {len(variables)}")
    print()
    
    # Show first 2 examples with reconstructed ability text
    for i, var_set in enumerate(variables[:2]):
        print(f"\n--- Example {i + 1} ---")
        print(f"Extracted variables:")
        var_names = pattern_def.get('var_names', [])
        for j, var in enumerate(var_set):
            var_name = var_names[j] if j < len(var_names) else f"[{j}]"
            print(f"  [{var_name}]: {var}")
        
        # Reconstruct the template with variables
        template = pattern_def['template']
        reconstructed = template
        for j, var in enumerate(var_set):
            var_name = var_names[j] if j < len(var_names) else f"{j}"
            reconstructed = reconstructed.replace(f'⟦{var_name}⟧', var)
        
        print(f"\nReconstructed ability: {reconstructed}")
        print()
