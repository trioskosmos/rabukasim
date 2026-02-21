import json
import os


def generate_manual_pseudocode():
    input_path = "data/cards.json"
    output_path = "data/manual_pseudocode.json"

    if not os.path.exists(input_path):
        # Try engine/data/
        input_path = "engine/data/cards.json"

    print(f"Reading from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    overrides = {}
    for cno, data in cards.items():
        if "pseudocode" in data and data["pseudocode"]:
            overrides[cno] = {"pseudocode": data["pseudocode"]}

    # Add fix for PL!HS-bp2-017-N
    overrides["PL!HS-bp2-017-N"] = {"pseudocode": "CONDITION: COUNT_DISCARD {MIN=10}\nEFFECT: DRAW(1) -> PLAYER"}

    print(f"Writing {len(overrides)} entries to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)
    print("Done")


if __name__ == "__main__":
    generate_manual_pseudocode()
