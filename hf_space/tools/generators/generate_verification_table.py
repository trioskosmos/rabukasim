import json
import os

CARDS_PATH = "data/cards_compiled.json"
TESTS_DIR = "engine/tests/cards"
OUTPUT_FILE = "engine/tests/cards/card_verification_table.md"


def load_cards():
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def find_tests_for_card(card_no):
    # exact grep for card_no in tests dir using os.walk
    found_in = []
    for root, dirs, files in os.walk(TESTS_DIR):
        for file in files:
            if file.endswith(".py") or file.endswith(".md"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if card_no in content:
                            found_in.append(file)
                except Exception:
                    pass
    return found_in


def main():
    print(f"Loading cards from {CARDS_PATH}...")
    cards = load_cards()
    print(f"Loaded {len(cards)} cards.")

    # Filter to only PL cards (Player cards) if needed, but let's do all.
    # Actually, let's sort by card_no

    # We want a list of dicts: {card_no, name, ability_summary, status, context}
    rows = []

    total = len(cards)
    for i, (card_id, card_data) in enumerate(cards.items()):
        if i % 100 == 0:
            print(f"Processing {i}/{total}...")

        card_no = card_data.get("card_no", "N/A")
        name = card_data.get("name", "N/A")

        # Check if tested
        # We look for the card_no in the test files
        test_files = find_tests_for_card(card_no)

        status = "Untested"
        start_deck_batch = "test_verification_batch" in str(test_files)

        if test_files:
            if "card_verification_log.md" in test_files and len(test_files) == 1:
                # If ONLY in the log, check the log to see if it says "Passed"
                # Ideally we parse the log, but simpler: denote as "Logged"
                status = "Logged (Manual?)"
            else:
                # Remove the log file from the list to see if there are actual code tests
                real_tests = [f for f in test_files if f != "card_verification_log.md"]
                if real_tests:
                    status = f"Test Exists ({', '.join(real_tests)})"
                else:
                    status = "Logged Only"

        # If ability text is empty / vanilla, maybe it doesn't need a test?
        # But user wants to verify text matches functionality.
        abilities = card_data.get("abilities", [])
        ability_text = card_data.get("ability_text", "Expected Vanila") or "Vanilla"
        if not abilities and (not ability_text or ability_text == "Vanilla"):
            status = "Vanilla (No Ability)"

        rows.append(
            {
                "card_no": card_no,
                "name": name,
                "text": ability_text[:50].replace("\n", " ") + "..."
                if len(ability_text) > 50
                else ability_text.replace("\n", " "),
                "status": status,
            }
        )

    # Sort
    rows.sort(key=lambda x: x["card_no"])

    # Generate Markdown
    md = "# Card Verification Table\n\n"
    md += f"Generated from `{CARDS_PATH}`.\n\n"
    md += "| Card No | Name | Ability Text | Status |\n"
    md += "| :--- | :--- | :--- | :--- |\n"

    for row in rows:
        md += f"| {row['card_no']} | {row['name']} | {row['text']} | {row['status']} |\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Table written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
