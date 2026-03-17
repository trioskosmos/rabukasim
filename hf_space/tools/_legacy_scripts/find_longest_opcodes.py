import json
import os


def find_longest_per_opcode():
    pseudocode_path = "data/manual_pseudocode.json"
    if not os.path.exists(pseudocode_path):
        print(f"File not found: {pseudocode_path}")
        return

    with open(pseudocode_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dictionary to store opcode -> (card_no, pseudocode_length, pseudocode)
    longest_cards = {}

    import re

    # Pattern to find effects
    effect_pattern = re.compile(r"EFFECT:\s*(\w+)")

    for card_no, entry in data.items():
        pseudocode = entry.get("pseudocode", "")
        length = len(pseudocode)

        # Find all opcodes/effects in this card
        effects = effect_pattern.findall(pseudocode)

        for effect in effects:
            if effect not in longest_cards or length > longest_cards[effect][1]:
                longest_cards[effect] = (card_no, length, pseudocode)

    # Sort results for display
    sorted_opcodes = sorted(longest_cards.items())

    output_path = "tools/longest_opcodes.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_opcodes, f, indent=2, ensure_ascii=False)
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    find_longest_per_opcode()
