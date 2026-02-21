import json
import re


def extract_rules(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    rules = {}
    # Matches patterns like "1.2.1. [Title]" at start of line
    # Or "1.2. [Title]"
    pattern = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)")

    for line in lines:
        line = line.strip()
        match = pattern.match(line)
        if match:
            num = match.group(1).rstrip(".")
            title = match.group(2).strip()
            # If title is very long, truncate or just take the first part
            rules[num] = title

    return rules


rules = extract_rules("rules.txt")
with open("rule_map.json", "w", encoding="utf-8") as f:
    json.dump(rules, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(rules)} rules with titles.")
