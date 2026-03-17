import os
import re


def check_coverage(rules_file, target_file):
    with open(rules_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract patterns like 1.1, 1.2.1, 9.5.3.1 (from start of line or in parentheses)
    # Looking for lines starting with digit.digit or patterns like (9.5.3)
    rule_patterns = set(re.findall(r"(?m)^\d+(?:\.\d+)+", content))
    # Also find references in parentheses like (9.5.3.2)
    rule_patterns.update(re.findall(r"\((\d+(?:\.\d+)+)\.?\)", content))

    # Clean up trailing periods
    rule_patterns = {r.rstrip(".") for r in rule_patterns}

    with open(target_file, "r", encoding="utf-8") as f:
        target_content = f.read()

    found = []
    missing = []

    for rule in sorted(list(rule_patterns), key=lambda x: [int(y) for y in x.split(".")]):
        if f"Rule {rule}" in target_content or f"{rule}:" in target_content or f"({rule})" in target_content:
            found.append(rule)
        else:
            missing.append(rule)

    return sorted(found, key=lambda x: [int(y) for y in x.split(".")]), sorted(
        missing, key=lambda x: [int(y) for y in x.split(".")]
    )


rules_path = "rules.txt"
target_path = "game/game_state.py"

if os.path.exists(rules_path) and os.path.exists(target_path):
    found, missing = check_coverage(rules_path, target_path)
    print(f"REPORT:\nTotal Rules Identified: {len(found) + len(missing)}")
    print(f"Found in Code: {len(found)}")
    print(f"Missing in Code: {len(missing)}")
    print("\n--- MISSING RULES ---")
    for m in missing:
        print(m)
    print("\n--- FOUND RULES ---")
    for f in found:
        print(f)
else:
    print(
        f"Error: Files not found. rules exists: {os.path.exists(rules_path)}, target exists: {os.path.exists(target_path)}"
    )
