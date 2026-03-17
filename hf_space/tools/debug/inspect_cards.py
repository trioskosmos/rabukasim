import json


def inspect():
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    targets = ["PL!SP-bp2-007-R", "PL!SP-bp2-007-P", "PL!SP-bp1-005-P", "PL!SP-bp1-005-R"]

    with open("temp_card_dump.txt", "w", encoding="utf-8") as outfile:
        for tid in targets:
            if tid in data:
                outfile.write(f"--- {tid} ---\n")
                outfile.write(json.dumps(data[tid], indent=2, ensure_ascii=False) + "\n")
            else:
                outfile.write(f"--- {tid} NOT FOUND ---\n")


if __name__ == "__main__":
    inspect()
