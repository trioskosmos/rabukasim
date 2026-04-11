import json
import re

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    content = f.read()
    data = json.loads(content)

abilities = data.get('abilities', [])

# Find ability #387
ab = abilities[387]
print(f"Ability #387 text: {ab.get('primary_text_jp', '')[:200]}")
print(f"Trigger: {ab.get('trigger')}")
print(f"Frames: {ab.get('frames', [])}")

# Search for a unique part of the text
text_part = "エールにより公開された"
if text_part in content:
    idx = content.find(text_part)
    line_num = content[:idx].count('\n') + 1
    print(f"Found at line: {line_num}")
else:
    print("Text not found directly")
    # Try with unicode escape
    import unicodedata
    print(f"Looking for: {repr(text_part)}")
