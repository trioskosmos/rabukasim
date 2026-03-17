import json
from collections import OrderedDict


def deduplicate_json(filename):
    # We use a custom object_pairs_hook to detect duplicates while parsing
    dupes = []
    seen = set()

    def detect_dupes(pairs):
        res = OrderedDict()
        for k, v in pairs:
            if k in seen:
                dupes.append(k)
            seen.add(k)
            res[k] = v
        return res

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f, object_pairs_hook=detect_dupes)

    if dupes:
        print(f"Deduplicating {len(dupes)} keys: {list(set(dupes))}")
    else:
        print("No duplicates detected during parse.")
        return

    # Write back clean JSON
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Successfully deduplicated {filename}")


if __name__ == "__main__":
    deduplicate_json("data/manual_pseudocode.json")
