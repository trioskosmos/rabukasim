import json
import os

CARDS_PATH = "data/cards_compiled.json"
TESTS_DIR = "engine/tests/cards"
REPORT_DIR = "verification_reports"
OUTPUT_FILE = os.path.join(REPORT_DIR, "card_status_table.md")

if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)


def load_cards():
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def find_tests_for_card(card_no):
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


def analyze_complexity(card):
    abilities = card.get("abilities", [])
    text = card.get("ability_text", "")

    if not abilities:
        if not text or text == "Vanilla":
            return "Vanilla"
        # Special case: Text exists but no abilities (Rule reminders or issues)
        return "Text-Only (Issue?)"

    if len(abilities) == 1:
        # Check effects complexity
        effs = abilities[0].get("effects", [])
        if len(effs) == 1:
            return "Simple (1 Effect)"

    return "Complex"


def main():
    print(f"Loading cards from {CARDS_PATH}...")
    full_data = load_cards()

    all_cards = []

    # Process member_db
    if "member_db" in full_data:
        print(f"Processing member_db ({len(full_data['member_db'])} items)...")
        for cid, card in full_data["member_db"].items():
            all_cards.append(card)

    # Process live_db
    if "live_db" in full_data:
        print(f"Processing live_db ({len(full_data['live_db'])} items)...")
        for cid, card in full_data["live_db"].items():
            all_cards.append(card)

    print(f"Total cards found: {len(all_cards)}")

    rows = []

    for i, card_data in enumerate(all_cards):
        if i % 200 == 0:
            print(f"Analyzing {i}...")

        card_no = card_data.get("card_no", "N/A")
        name = card_data.get("name", "N/A")

        # Check status
        test_files = find_tests_for_card(card_no)

        status = "**Untested**"

        real_tests = [f for f in test_files if f.endswith(".py")]
        if real_tests:
            status = f"Tested in `{real_tests[0]}`"
            if len(real_tests) > 1:
                status += f" (+{len(real_tests) - 1})"
        elif "card_verification_log.md" in test_files:
            status = "Logged Only"

        complexity = analyze_complexity(card_data)
        ability_text = card_data.get("ability_text", "") or ""
        short_text = (
            ability_text.replace("\n", " ")[:40] + "..." if len(ability_text) > 40 else ability_text.replace("\n", " ")
        )

        # Identify Easy Wins: Untested AND (Vanilla OR Simple)
        is_easy_win = "No"
        if "Untested" in status:
            if complexity == "Vanilla":
                is_easy_win = "**YES (Vanilla)**"
            elif complexity == "Simple (1 Effect)":
                is_easy_win = "YES (Simple)"

        rows.append(
            {
                "card_no": card_no,
                "name": name,
                "complexity": complexity,
                "status": status,
                "easy_win": is_easy_win,
                "text": short_text,
            }
        )

    # Sort by Card No
    rows.sort(key=lambda x: x["card_no"])

    # Generate Markdown
    md = "# Card Verification Table\n\n"
    md += f"Total Cards: {len(all_cards)}\n\n"
    md += "| Card No | Name | Complexity | Status | Easy Win? | Text Preview |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"

    for row in rows:
        md += f"| {row['card_no']} | {row['name']} | {row['complexity']} | {row['status']} | {row['easy_win']} | {row['text']} |\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Table written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
