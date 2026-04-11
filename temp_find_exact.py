import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    content = f.read()
    data = json.loads(content)

abilities = data.get('abilities', [])

# Find ability #387
ab = abilities[387]
print(f"Ability #387 text: {ab.get('primary_text_jp', '')[:150]}")
print(f"Trigger: {ab.get('trigger')}")
print(f"Card refs: {ab.get('card_refs', [])}")

# Find line number by searching for unique text
import re
text_start = ab.get('primary_text_jp', '')[:50]
if text_start:
    # Escape special regex chars
    escaped = re.escape(text_start)
    match = re.search(escaped, content)
    if match:
        # Count newlines before match
        line_num = content[:match.start()].count('\n') + 1
        print(f"Approximate line number: {line_num}")
