import json
import os
import re


def update_pseudocode():
    ids_to_fix = {
        "PL!SP-bp2-002-P": "COST_GE=11",
        "PL!SP-bp2-002-R": "COST_GE=11",
        "PL!SP-bp4-002-P": "HEARTS_GE=8",
        "PL!SP-bp4-002-R": "HEARTS_GE=8",
        "PL!N-bp3-003-P": "COST_LE=4",
        "PL!N-bp3-003-R": "COST_LE=4",
        "PL!N-pb1-004-P＋": "COST_LE=9",
        "PL!N-pb1-004-R": "COST_LE=9",
    }

    file_path = "data/manual_pseudocode.json"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for cid, filter_val in ids_to_fix.items():
        if cid in data:
            pseudocode = data[cid]["pseudocode"]
            if "LOOK_AND_CHOOSE" in pseudocode and "FILTER=" not in pseudocode:
                # Replace LOOK_AND_CHOOSE(n) or LOOK_AND_CHOOSE with LOOK_AND_CHOOSE(...) {FILTER=...}
                new_pseudo = re.sub(r"(LOOK_AND_CHOOSE(?:\(\d+\))?)", f'\\1 {{FILTER="{filter_val}"}}', pseudocode)
                if new_pseudo != pseudocode:
                    data[cid]["pseudocode"] = new_pseudo
                    print(f"Updated {cid}")
                else:
                    print(f"No change for {cid}")
            else:
                print(f"Skipping {cid} (already has filter or no LAC)")
        else:
            print(f"Card {cid} not found in manual_pseudocode.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    update_pseudocode()
