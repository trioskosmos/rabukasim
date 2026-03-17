import json


def build_card_pool():
    # 1. Working Ability Cards (from verification log)
    # Extracting these manually based on the log provided previously
    working_ability_cards = [
        "PL!-sd1-001-SD",
        "PL!-sd1-002-SD",
        "PL!-sd1-003-SD",
        "PL!-sd1-004-SD",
        "PL!-sd1-005-SD",
        "PL!-sd1-006-SD",
        "PL!-sd1-007-SD",
        "PL!-sd1-008-SD",
        "PL!-sd1-009-SD",
        "PL!-sd1-011-SD",
        "PL!-sd1-012-SD",
        "PL!-sd1-015-SD",
        "PL!-bp3-009-P+",
        "PL!-bp3-011-N",
        "PL!-bp3-012-PR",
        "PL!-bp3-024-L",
        "PL!N-bp1-003-SEC",
        "PL!S-pb1-001-R",
        "PL!N-bp4-027-L",
        "PL!HS-bp1-005-P/R",
    ]

    # 2. Add Vanilla Cards
    compiled_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"
    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    vanilla_members = []
    vanilla_lives = []

    # Check members
    members = data.get("member_db", {})
    for cid, card in members.items():
        if not card.get("abilities") or len(card.get("abilities", [])) == 0:
            vanilla_members.append(card.get("card_no"))

    # Check lives
    lives = data.get("live_db", {})
    for cid, card in lives.items():
        if not card.get("abilities") or len(card.get("abilities", [])) == 0:
            vanilla_lives.append(card.get("card_no"))

    # Combined Pool
    pool = {
        "verified_abilities": working_ability_cards,
        "vanilla_members": vanilla_members,
        "vanilla_lives": vanilla_lives,
    }

    with open("verified_card_pool.json", "w", encoding="utf-8") as f:
        json.dump(pool, f, indent=4, ensure_ascii=False)

    print(
        f"Pool Built! {len(working_ability_cards)} Abilities, {len(vanilla_members)} Vanilla Members, {len(vanilla_lives)} Vanilla Lives."
    )


if __name__ == "__main__":
    build_card_pool()
