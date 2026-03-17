import json
import sys
import os

sys.path.append(r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy")

from compiler.canonical_schema import CanonicalAbilityAdapter

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\canonical_ability_model\drafts\canonical_full_draft.json"
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for entry in data:
    card_no = entry.get("card_no")
    entry_to_validate = entry.copy()
    entry_to_validate.pop("card_no", None)
    try:
        CanonicalAbilityAdapter.validate_python(entry_to_validate)
    except Exception as e:
        print(f"FAILED CARD: {card_no}")
        with open("/tmp/error.txt", "w") as ef:
            ef.write(str(e))
        print("Error saved to /tmp/error.txt")
        sys.exit(1)

print("ALL PASSED!")
