import json
import sys
import os

# Add project root to sys.path
sys.path.append(r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy")

from compiler.canonical_schema import CanonicalAbilityAdapter

def validate_fixed_draft():
    path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\canonical_ability_model\drafts\canonical_full_draft.json"
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    errors = []
    success_count = 0
    
    for i, entry in enumerate(data):
        entry_to_validate = entry.copy()
        card_no = entry_to_validate.pop("card_no", None)
        try:
            CanonicalAbilityAdapter.validate_python(entry_to_validate)
            success_count += 1
        except Exception as e:
            errors.append(f"Entry {i} (Card {card_no}): {str(e)}")
            if len(errors) == 1:
                print(f"\nDETAILED ERROR FOR CARD {card_no}:")
                print(e)
    
    print(f"Validation summary: {success_count}/{len(data)} passed.")
    if errors:
        print("\nFirst 5 errors:")
        for err in errors[:5]:
            print(err)
    else:
        print("All entries passed strict schema validation!")

if __name__ == "__main__":
    validate_fixed_draft()
