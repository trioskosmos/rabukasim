import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Search for a pattern by name in extract_abilities_to_template.py
if len(sys.argv) < 2:
    print("Usage: python search_pattern.py <pattern_name>")
    sys.exit(1)

pattern_name = sys.argv[1]

with open('tools/extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the pattern definition
import re
pattern_regex = rf'"name":\s*"{pattern_name}",'
matches = list(re.finditer(pattern_regex, content))

if not matches:
    print(f"Pattern '{pattern_name}' not found")
    sys.exit(0)

print(f"Found {len(matches)} matches for '{pattern_name}':")
print()

for i, match in enumerate(matches, 1):
    start = max(0, match.start() - 100)
    end = min(len(content), match.end() + 300)
    snippet = content[start:end]
    print(f"Match {i}:")
    print(snippet)
    print("-" * 80)
