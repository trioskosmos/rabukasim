import datetime
import json
import os
import re


def update_master_report():
    report_path = "docs/MASTER_REPORT.md"
    tested_cards_path = "all_tested_cards.txt"

    # 1. Map Card ID -> List of Test Files
    card_tests = {}

    # Read the grep output
    try:
        with open(tested_cards_path, "r", encoding="utf-16") as f:
            lines = f.readlines()
    except:
        with open(tested_cards_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

    for line in lines:
        if ":" not in line:
            continue
        parts = line.split(":", 1)
        filename = os.path.basename(parts[0].strip())
        ids = re.findall(r"((?:PL!|LL-)[A-Za-z0-9\-+]+)", line)
        for card_id in ids:
            if card_id not in card_tests:
                card_tests[card_id] = set()
            card_tests[card_id].add(filename)

    # Load Verified Pool
    verified_pool_path = "verified_card_pool.json"
    verified_set = set()
    vanilla_set = set()
    try:
        with open(verified_pool_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
            verified_set = set(v_data.get("verified_abilities", []))
            vanilla_set = set(v_data.get("vanilla_members", []) + v_data.get("vanilla_lives", []))
    except FileNotFoundError:
        print(f"Warning: {verified_pool_path} not found.")

    # 2. Update MASTER_REPORT.md Content
    with open(report_path, "r", encoding="utf-8") as f:
        report_lines = f.readlines()

    table_lines = []
    header_lines = []

    # Stats counters
    stats = {"Total Cards": 0, "Verified": 0, "Untested": 0, "Easy Wins Available": 0, "In Progress": 0}

    for line in report_lines:
        if not line.strip().startswith("|"):
            header_lines.append(line)
            continue

        parts = [p.strip() for p in line.split("|")]
        # Skip separator line or malformed lines
        if len(parts) < 8 or "---" in parts[1]:
            table_lines.append(line)
            continue

        # It's a data row
        if "Card No" in parts[1]:  # Header row
            table_lines.append(line)
            continue

        card_id = parts[1]
        stats["Total Cards"] += 1

        # Update Logic
        current_status = parts[4]
        new_status = current_status
        test_files = ""

        if card_id in card_tests:
            test_files = ", ".join(sorted(list(card_tests[card_id])))
            parts[6] = f"`{test_files}`"

        # Determine Status
        if card_id in verified_set:
            new_status = "**Verified** (Strict Test)"
        elif card_id in vanilla_set:
            new_status = "**Verified** (Vanilla)"
            parts[5] = "**YES (Vanilla)**"  # Force Easy Win to YES for Vanilla if not already
        elif card_id in card_tests:
            if "test_verification" in test_files:
                new_status = "**In Progress** (Verification Batch)"
            else:
                new_status = "**In Progress** (Test found)"
        else:
            if "Vanilla" in parts[3]:  # Fallback if not in vanilla set for some reason
                new_status = "**Untested**"
            else:
                new_status = "**Untested**"

        parts[4] = new_status

        # Recalculate stats for this row
        row_status = parts[4]
        if "Verified" in row_status or "Fixed" in row_status or "Hotfix" in row_status:
            stats["Verified"] += 1
        elif "In Progress" in row_status:
            stats["In Progress"] += 1
        else:
            stats["Untested"] += 1

        if "YES" in parts[5]:
            stats["Easy Wins Available"] += 1

        table_lines.append(" | ".join(parts) + "\n")

    # 3. Reconstruct Header with new stats
    new_header = []

    # Find where the stats line was
    stats_line_idx = -1
    for i, line in enumerate(header_lines):
        if "**Total Cards:**" in line:
            stats_line_idx = i
            break

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    stats_string = (
        f"**Generated:** {timestamp} | "
        f"**Total Cards:** {stats['Total Cards']} | "
        f"**Verified:** {stats['Verified']} | "
        f"**In Progress:** {stats['In Progress']} | "
        f"**Untested:** {stats['Untested']} | "
        f"**Easy Wins:** {stats['Easy Wins Available']}\n"
    )

    data_source_info = (
        "\n> **Data Sources:**\n"
        "> - **Test Coverage:** Derived from scanning `engine/tests/` via `all_tested_cards.txt`.\n"
        "> - **Verified Status:** Syncs from `verified_card_pool.json` (Strict Test + Bytecode) & `test_auto_generated_strict.py`.\n"
        "\n"
    )

    if stats_line_idx != -1:
        header_lines[stats_line_idx] = stats_string
        # Check if data source info already exists to avoid dupes
        if "> **Data Sources:**" not in "".join(header_lines):
            header_lines.insert(stats_line_idx + 1, data_source_info)
        # Update explanation if present
        if (
            data_source_info.strip() != header_lines[stats_line_idx + 1].strip()
            and "> **Data Sources:**" in header_lines[stats_line_idx + 1]
        ):
            header_lines[stats_line_idx + 1] = data_source_info

    else:
        # Fallback if header format changed
        new_header.append(stats_string)
        new_header.append(data_source_info)
        new_header.extend(header_lines)
        header_lines = new_header

    # 4. Write back
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(header_lines + table_lines)

    print(f"Updated Report Stats: {stats}")


if __name__ == "__main__":
    update_master_report()
