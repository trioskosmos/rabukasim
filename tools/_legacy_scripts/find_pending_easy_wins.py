import json


def find_pending_easy_wins():
    report_path = "docs/MASTER_REPORT.md"
    verified_pool_path = "verified_card_pool.json"

    with open(verified_pool_path, "r", encoding="utf-8") as f:
        v_pool = json.load(f)
        verified_all = set(v_pool["verified_abilities"] + v_pool["vanilla_members"] + v_pool["vanilla_lives"])

    pending_easy_wins = []
    with open(report_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip().startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6:
                continue

            card_id = parts[1]
            status = parts[4]
            easy_win = parts[5]

            if "YES" in easy_win and card_id not in verified_all:
                pending_easy_wins.append({"id": card_id, "status": status, "complexity": parts[3]})

    print(f"Found {len(pending_easy_wins)} pending Easy Wins:")
    for card in pending_easy_wins[:30]:  # Show first 30
        print(f"{card['id']} | {card['status']} | {card['complexity']}")

    # Save the list for reference
    with open("pending_easy_wins.json", "w", encoding="utf-8") as f:
        json.dump(pending_easy_wins, f, indent=2)


if __name__ == "__main__":
    find_pending_easy_wins()
