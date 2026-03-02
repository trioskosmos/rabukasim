import json
import os
import re


def migrate_tests():
    with open("reports/old_id_map.json", "r", encoding="utf-8") as f:
        old_map = json.load(f)
    with open("reports/new_id_map.json", "r", encoding="utf-8") as f:
        new_map = json.load(f)

    # Create old_id -> new_id mapping
    # We need to be careful because multiple card_nos might have had the same old_id (if they were variants)
    # No, variants had different IDs in the old system.
    # In the new system, variants share the logic ID but have different packed IDs.

    # Map old_id -> new_id via card_no
    id_migration = {}
    for card_no, old_id in old_map.items():
        if card_no in new_map:
            id_migration[old_id] = new_map[card_no]

    print(f"Migration registry built with {len(id_migration)} ID pairs.")

    test_dir = "engine_rust_src/src"
    # Sort IDs descending to avoid partial replacements (e.g., 100 before 1)
    sorted_old_ids = sorted(id_migration.keys(), reverse=True)

    for filename in os.listdir(test_dir):
        if filename.endswith("_tests.rs") or filename == "mechanics_tests.rs" or filename == "repro.rs":
            filepath = os.path.join(test_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            orig_content = content
            # Strategy: Replace numeric literals that look like card IDs.
            # This is risky if IDs are common numbers (like 0, 1).
            # We'll target patterns like "card_id: 123", "vec![123]", "insert(123", etc.

            for old_id in sorted_old_ids:
                new_id = id_migration[old_id]
                if old_id == new_id:
                    continue

                # Match old_id preceded by common patterns
                # we look for boundary or specific context
                pattern = (
                    r"(?P<pre>card_id[:\s]+|vec!\[|\[|,|\(\s*|\sinsert\()(?P<id>"
                    + str(old_id)
                    + r")(?P<post>\s|,|\]|\))"
                )

                def replace_func(match):
                    return f"{match.group('pre')}{new_id}{match.group('post')}"

                content = re.sub(pattern, replace_func, content)

            if content != orig_content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Migrated {filename}")


if __name__ == "__main__":
    migrate_tests()
