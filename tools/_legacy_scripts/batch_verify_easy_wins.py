import json
import os
import sys

sys.path.append(os.getcwd())


def generate_strict_test_file(card_ids, output_path):
    # Load Compiled DB for existing bytecode/abilities
    compiled_path = "engine/data/cards_compiled.json"
    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_db = json.load(f)
        all_compiled = {**compiled_db.get("member_db", {}), **compiled_db.get("live_db", {})}

    test_content = [
        "import pytest",
        "from engine.game.game_state import initialize_game",
        "",
        "@pytest.fixture",
        "def game():",
        "    return initialize_game(deck_type='training')",
        "",
        "def _find_id(game, cno):",
        "    for k, v in game.member_db.items():",
        "        if v.card_no == cno:",
        "            return k",
        "    for k, v in game.live_db.items():",
        "        if v.card_no == cno:",
        "            return k",
        "    return None",
        "",
    ]

    for cno in card_ids:
        comp = None
        for k, v in all_compiled.items():
            if v["card_no"] == cno:
                comp = v
                break

        if not comp:
            continue

        abilities = comp.get("abilities", [])
        if not abilities:
            # Vanilla cards are already verified by the script usually,
            # but we can add a test just in case or skip.
            continue

        if not abilities:
            # Vanilla cards are already verified by the script usually,
            # but we can add a test just in case or skip.
            continue

        def sanitize_id(raw_id):
            # Map full-width chars and other special chars to safe ASCII
            safe_id = raw_id.replace("-", "_").replace("!", "_")
            # Handle various plus signs
            safe_id = safe_id.replace("+", "_P").replace("＋", "_P").replace("➕", "_P")
            return safe_id

        func_name = f"test_strict_{sanitize_id(cno)}"
        test_content.append(f"def {func_name}(game):")
        test_content.append(f"    cno = '{cno}'")
        test_content.append("    cid = _find_id(game, cno)")
        test_content.append("    if cid is None: pytest.skip(f'{cno} not found')")
        test_content.append("    db = game.member_db if cid in game.member_db else game.live_db")
        test_content.append("    card = db[cid]")
        test_content.append(f"    assert len(card.abilities) == {len(abilities)}")

        for i, ab in enumerate(abilities):
            test_content.append(f"    ab{i} = card.abilities[{i}]")
            test_content.append(f"    assert ab{i}.trigger == {ab['trigger']}")
            test_content.append(f"    assert len(ab{i}.conditions) == {len(ab.get('conditions', []))}")
            # Add basic effect checks
            test_content.append(f"    assert len(ab{i}.effects) == {len(ab.get('effects', []))}")
            for j, eff in enumerate(ab.get("effects", [])):
                test_content.append(f"    assert ab{i}.effects[{j}].effect_type == {eff['effect_type']}")
                test_content.append(f"    assert ab{i}.effects[{j}].value == {eff['value']}")
        test_content.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(test_content))


if __name__ == "__main__":
    with open("pending_easy_wins.json", "r", encoding="utf-8") as f:
        pending = json.load(f)

    # Take next 50 for Batch 2
    batch_ids = [p["id"] for p in pending[30:80]]
    generate_strict_test_file(batch_ids, "engine/tests/cards/batches/test_easy_wins_batch_2.py")
    print(f"Generated test_easy_wins_batch_2.py with {len(batch_ids)} cards.")
