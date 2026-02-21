import json


def list_cards():
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter for Main IDs (exclude related cards if they are just references, but here keys are IDs)
    card_ids = sorted(list(data.keys()))

    # We want to see what comes after PL!-sd1-015-SD
    # Group by prefix?

    tested = {
        "PL!-sd1-001-SD",
        "PL!-sd1-002-SD",
        "PL!-sd1-003-SD",
        "PL!-sd1-004-SD",
        "PL!-sd1-005-SD",
        "PL!-sd1-006-SD",
        "PL!-sd1-007-SD",
        "PL!-sd1-008-SD",
        "PL!-sd1-009-SD",
        "PL!-sd1-010-SD",
        "PL!-sd1-011-SD",
        "PL!-sd1-012-SD",
        "PL!-sd1-013-SD",
        "PL!-sd1-014-SD",
        "PL!-sd1-015-SD",
    }

    candidates = [
        c for c in card_ids if c not in tested and not c.endswith("-P")
    ]  # Exclude parallel for now if they are just art swaps

    # Print next 50 candidates
    for c in candidates[:60]:
        print(c)


if __name__ == "__main__":
    list_cards()
