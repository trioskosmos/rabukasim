import json
import os

CARDS_PATH = "data/cards_compiled.json"
TESTS_DIR = "engine/tests/cards"
REPORT_DIR = "verification_reports"
OUTPUT_FILE = "verification_reports/full_card_verification_report.md"
LOG_FILE = "engine/tests/cards/card_verification_log.md"

if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)


def load_cards():
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def parse_verification_log():
    """Parses manual status from markdown log(s). Consolidates duplicates."""
    statuses = {}

    # List of possible log files
    log_files = [
        "engine/tests/cards/card_verification_log.md",
        "docs/reports/card_verification_log.md",
        "merge/card_verification_log.md",
    ]

    for log_path in log_files:
        if not os.path.exists(log_path):
            continue

        print(f"Parsing log file: {log_path}...")
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Warning: Failed to read {log_path}: {e}")
            continue

        for line in lines:
            # Look for lines with card IDs (PL! or LL-)
            if line.strip().startswith("|") and ("PL!" in line or "LL-" in line):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) > 4:
                    card_no = parts[1]
                    status_raw = parts[4]

                    # Clean markdown bold
                    status = status_raw.replace("**", "").strip()
                    if card_no:
                        # Prioritize explicitly positive statuses
                        if card_no in statuses:
                            if "Passed" in status or "Verified" in status or "Fixed" in status:
                                statuses[card_no] = status
                        else:
                            statuses[card_no] = status
    return statuses


def find_tests_for_card(card_no):
    found_in = []
    for root, dirs, files in os.walk(TESTS_DIR):
        for file in files:
            if file.endswith(".py"):
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
        if not text:
            return "Vanilla (No Text)"
        if text == "Vanilla":
            return "Vanilla"
        # Check if text is just rules reminder (bracketed)
        if text.startswith("(") and text.endswith(")"):
            return "Vanilla (Reminder Text)"

        return "Text-Only (Parsing Issue?)"

    if len(abilities) == 1:
        # Check effects complexity
        effs = abilities[0].get("effects", [])
        if len(effs) == 1:
            eff = effs[0]
            if eff.get("effect_type") == 12:  # DRAW
                return "Simple (Draw)"
            if eff.get("effect_type") == 29:  # ACTIVATED
                return "Simple (Active)"
            return "Simple (1 Effect)"

    return "Complex"


def main():
    print(f"Loading cards from {CARDS_PATH}...")
    full_data = load_cards()
    manual_statuses = parse_verification_log()

    all_cards = []

    if "member_db" in full_data:
        for cid, card in full_data["member_db"].items():
            all_cards.append(card)
    if "live_db" in full_data:
        for cid, card in full_data["live_db"].items():
            all_cards.append(card)

    print(f"Total cards found: {len(all_cards)}")

    rows = []

    for i, card_data in enumerate(all_cards):
        card_no = card_data.get("card_no", "N/A")
        name = card_data.get("name", "N/A")

        test_files = find_tests_for_card(card_no)

        # Determine Status
        # Priority: Manual Log > Test File Existence > Untested
        status = "**Untested**"

        if card_no in manual_statuses:
            status = f"**{manual_statuses[card_no]}**"
        elif test_files:
            # Check if any test file suggests verification
            verified_keywords = ["strict", "verified", "behavior"]
            if any(k in f for f in test_files for k in verified_keywords):
                status = "**Verified** (Automated)"
            else:
                status = "**In Progress** (Test found)"

        files_str = ", ".join([f"`{f}`" for f in test_files]) if test_files else ""

        complexity = analyze_complexity(card_data)

        # Identify Easy Wins: Untested AND (Vanilla OR Simple)
        is_easy_win = "No"
        if "Untested" in status:
            if "Vanilla" in complexity:
                is_easy_win = "**YES (Vanilla)**"
            elif "Simple" in complexity:
                is_easy_win = "YES (Simple)"

        ability_text = card_data.get("ability_text", "") or ""
        short_text = ability_text.replace("\n", "<br>")

        # Escape pipes for markdown table
        short_text = short_text.replace("|", "\|")

        rows.append(
            {
                "card_no": card_no,
                "name": name,
                "complexity": complexity,
                "status": status,
                "easy_win": is_easy_win,
                "files": files_str,
                "text": short_text,
            }
        )

    rows.sort(key=lambda x: x["card_no"])

    # Stats
    total = len(rows)
    passed = sum(1 for r in rows if "Passed" in r["status"] or "Fixed" in r["status"] or "Verified" in r["status"])
    untested = sum(1 for r in rows if "Untested" in r["status"])
    easy_wins = sum(1 for r in rows if "YES" in r["easy_win"])

    md = "# Full Card Verification Report\n\n"
    md += f"**Generated:** {os.environ.get('USERNAME', 'User')} | **Total Cards:** {total} | **Verified:** {passed} | **Untested:** {untested} | **Easy Wins Available:** {easy_wins}\n\n"
    md += "This report combines manual verification logs with automatic test file detection.\n\n"
    md += "| Card No | Name | Complexity | Status | Easy Win? | Test Files | Ability Text (Compiled) |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"

    for row in rows:
        md += f"| {row['card_no']} | {row['name']} | {row['complexity']} | {row['status']} | {row['easy_win']} | {row['files']} | {row['text']} |\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Card Table written to {OUTPUT_FILE}")

    # Combine with other reports
    master_report_path = "docs/MASTER_REPORT.md"

    # Define special files to handle separately (and exclude from generic iterator)
    baseline_path = "docs/reports/baseline_coverage.md"
    log_path = "docs/reports/card_verification_log.md"
    special_files = ["baseline_coverage.md", "card_verification_log.md"]

    with open(master_report_path, "w", encoding="utf-8") as f:
        f.write("# Love Live TCG Engine - Master Verification Report\n\n")
        f.write(f"**Generated:** {os.environ.get('USERNAME', 'User')} | **Date:** {os.environ.get('DATE', '')}\n\n")

        # 1. Card Status (The generated table)
        f.write("## Section 1: Card Implementation Status\n\n")
        f.write(md)
        f.write("\n\n---\n\n")

        # 2. Baseline Coverage
        if os.path.exists(baseline_path):
            f.write("## Section 2: Baseline Coverage Metrics\n\n")
            with open(baseline_path, "r", encoding="utf-8") as bf:
                f.write(bf.read())
            f.write("\n\n---\n\n")

        # 3. Other Reports (Excluding special ones)
        reports_dir = "docs/reports"
        if os.path.exists(reports_dir):
            f.write("## Section 3: Incident & Fix Reports\n\n")
            for r_file in os.listdir(reports_dir):
                if r_file.endswith(".md") and r_file not in special_files:
                    f.write(f"### Report: {r_file}\n\n")
                    with open(os.path.join(reports_dir, r_file), "r", encoding="utf-8") as rf:
                        f.write(rf.read())
                    f.write("\n\n")

        # 4. Detailed Verification Log (Historical Data)
        if os.path.exists(log_path):
            f.write("\n\n---\n\n## Section 4: Detailed Verification Logs\n\n")
            with open(log_path, "r", encoding="utf-8") as lf:
                f.write(lf.read())

    print(f"Master Report written to {master_report_path}")


if __name__ == "__main__":
    main()
