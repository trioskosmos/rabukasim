import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    print("Usage: python show_pattern_matches.py <pattern_name>")
    sys.exit(1)

pattern_name = sys.argv[1]

# Load patterns to get regex
with open('tools/extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find pattern definition
pattern_match = re.search(rf'"name":\s*"{pattern_name}",.*?"regex":\s*r"([^"]+)"', content, re.DOTALL)
if not pattern_match:
    print(f"Pattern '{pattern_name}' not found")
    sys.exit(0)

regex = pattern_match.group(1)
print(f"Pattern: {pattern_name}")
print(f"Regex: {regex}")
print()

# Load abilities to find matches
with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search through all skeletons
matches = []
for structure in data['structures']:
    skeleton = structure.get('skeleton', '')
    if re.search(regex, skeleton):
        matches.append(skeleton)

print(f"Found {len(matches)} skeleton matches")
print()
print("First 20 matches:")
for i, match in enumerate(matches[:20], 1):
    print(f"  {i}. {match}")

if len(matches) > 20:
    print(f"  ... and {len(matches) - 20} more")
