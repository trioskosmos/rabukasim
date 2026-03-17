import collections


def find_duplicates(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    keys = []
    for i, line in enumerate(lines):
        if '"' in line and ":" in line and "{" in line:
            # Simple heuristic for keys
            parts = line.split('"')
            if len(parts) >= 2:
                key = parts[1]
                keys.append((key, i + 1))

    counts = collections.Counter(k for k, _ in keys)
    dupes = [k for k, v in counts.items() if v > 1]

    if not dupes:
        print("No duplicates found.")
        return

    print(f"Found {len(dupes)} duplicate keys:")
    for key in dupes:
        occurrences = [line_no for k, line_no in keys if k == key]
        print(f"Key: '{key}' at lines: {occurrences}")


if __name__ == "__main__":
    find_duplicates("data/manual_pseudocode.json")
