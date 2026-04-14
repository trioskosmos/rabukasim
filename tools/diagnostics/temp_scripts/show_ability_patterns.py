import json
import sys
import re
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Load the simple abilities data
simple_file = Path(__file__).parent.parent.parent.parent / "data" / "abilities_extracted_simple.json"
with open(simple_file, 'r', encoding='utf-8') as f:
    simple_data = json.load(f)

# Load pattern definitions from the main script
script_file = Path(__file__).parent.parent.parent / "extract_abilities_to_template.py"
with open(script_file, 'r', encoding='utf-8') as f:
    script_content = f.read()

# Extract pattern definitions - better approach
pattern_definitions = {}
# Find the DSL_PATTERNS list and parse it
dsl_start = script_content.find('DSL_PATTERNS = [')
if dsl_start != -1:
    # Find the end of the list
    bracket_count = 0
    i = dsl_start + len('DSL_PATTERNS = [')
    dsl_block_start = i
    
    while i < len(script_content):
        if script_content[i] == '[':
            bracket_count += 1
        elif script_content[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                dsl_block = script_content[dsl_block_start:i]
                break
        i += 1
    
    # Extract patterns using a more robust regex
    pattern_regex = r'{{\s*"name":\s*"([^"]+)",\s*"regex":\s*r"(.*?)",\s*"template":\s*"(.*?)",\s*"structure":\s*"(.*?)"\s*}},'
    for match in re.finditer(pattern_regex, dsl_block, re.DOTALL):
        pattern_name = match.group(1)
        pattern_regex_str = match.group(2).replace('\\', '')  # Remove escape backslashes for regex
        pattern_definitions[pattern_name] = {
            'regex': pattern_regex_str,
            'template': match.group(3),
            'structure': match.group(4)
        }

# Function to match patterns against an ability
def match_patterns(ability_text):
    matches = []
    for pattern_name, pattern_def in pattern_definitions.items():
        try:
            regex = pattern_def['regex']
            match = re.search(regex, ability_text)
            if match:
                matches.append({
                    'name': pattern_name,
                    'structure': pattern_def['structure'],
                    'template': pattern_def['template'],
                    'matched_text': match.group(0),
                    'groups': match.groups()
                })
        except Exception as e:
            pass
    return matches

# Show first 10 abilities with their pattern matches
print("=" * 100)
print("ABILITY PATTERN MATCHING OUTPUT")
print("=" * 100)
print()

for i, ability in enumerate(simple_data['abilities'][:10]):
    ability_text = ability['jp']
    card_examples = ability['card_examples'][:3]  # Show first 3 card examples
    count = ability['count']
    
    print(f"\n{'=' * 100}")
    print(f"ABILITY {i + 1}")
    print(f"{'=' * 100}")
    print(f"Text: {ability_text}")
    print(f"Cards: {count} cards (examples: {', '.join(card_examples)})")
    print()
    
    # Match patterns
    matches = match_patterns(ability_text)
    
    if matches:
        print(f"Pattern matches ({len(matches)}):")
        for j, match in enumerate(matches):
            print(f"\n  Pattern {j + 1}: {match['name']}")
            print(f"    Structure: {match['structure']}")
            print(f"    Matched: {match['matched_text']}")
            print(f"    Template: {match['template']}")
            if match['groups']:
                print(f"    Extracted variables:")
                for k, group in enumerate(match['groups']):
                    print(f"      [{k}]: {group}")
    else:
        print("No pattern matches")
    
    print()

print(f"\n{'=' * 100}")
print(f"Showing first 10 of {len(simple_data['abilities'])} total abilities")
print(f"{'=' * 100}")
