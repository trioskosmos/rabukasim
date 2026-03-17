import json


def format_index(rule_map_path):
    with open(rule_map_path, "r", encoding="utf-8") as f:
        rule_map = json.load(f)

    output = "\n# --- COMPREHENSIVE RULEBOOK INDEX (v1.04) ---\n"
    output += "# This index ensures 100% searchability of all official rule identifiers.\n#\n"

    for num in sorted(rule_map.keys(), key=lambda x: [int(y) for y in x.split(".")]):
        output += f"# Rule {num}: {rule_map[num]}\n"

    output += "# --- END OF INDEX ---\n"
    return output


index_text = format_index("rule_map.json")
with open("rule_index_snippet.txt", "w", encoding="utf-8") as f:
    f.write(index_text)

print("Generated rule_index_snippet.txt")
