import json
import os
import re
import sys

# Force UTF-8 for this script's output
sys.stdout.reconfigure(encoding="utf-8")

CARDS_PATH = "data/cards_compiled.json"
POOL_PATH = "data/verified_card_pool.json"
TEST_FILE_PATH = "engine/tests/cards/batches/test_auto_generated_strict_comprehensive.py"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_test_file(candidates, _):
    # Header logic
    # We need to test Members, Lives, and Energy.
    # Lives/Energy might be in member_db? No, they are in their own DBs.
    # The game_state usually loads them into separate dicts or a unified lookup?
    # initialize_game likely sets up member_db and live_db.

    header = """
import pytest
from engine.game.game_state import initialize_game
from engine.models.ability import ConditionType

@pytest.fixture
def game():
    return initialize_game(deck_type="training")

def _find_card(game, cid):
    # Check Member DB
    if hasattr(game, "member_db"):
        if cid in game.member_db:
            return game.member_db[cid]
    # Check Live DB
    if hasattr(game, "live_db"):
        if cid in game.live_db:
            return game.live_db[cid]
    # Check Energy DB (if exists)
    if hasattr(game, "energy_db"):
        if cid in game.energy_db:
            return game.energy_db[cid]
    return None
"""
    test_cases = ""

    def sanitize(name):
        return re.sub(r"[^a-zA-Z0-9_]", "_", name)

    for card_data in candidates:
        cno = card_data.get("card_no", "Unknown")
        cid = card_data.get("card_id", 0)
        safe_name = sanitize(cno) + "_" + str(cid)

        abilities = card_data.get("abilities", [])

        # Test Function Start
        test_func = f"""
def test_strict_{safe_name}(game):
    cid = {cid}
    card = _find_card(game, cid)
    if card is None:
        pytest.skip(f"{{cid}} not found in DB")

    assert len(card.abilities) == {len(abilities)}, 'Ability count mismatch'
"""

        # Iterate Abilities
        for i, ab in enumerate(abilities):
            trig_exp = ab.get("trigger", 0)

            test_func += f"""
    # Ability {i}
    ab{i} = card.abilities[{i}]
    assert ab{i}.trigger == {trig_exp}, f'Trigger mismatch: {{ab{i}.trigger}} != {trig_exp}'
"""
            # Conditions
            raw_conds = ab.get("conditions", [])
            test_func += f"    assert len(ab{i}.conditions) == {len(raw_conds)}, 'Condition count mismatch'\n"
            for j, c in enumerate(raw_conds):
                ctype = c.get("type")
                # Params check? Maybe too brittle if dict order varies, but we can check critical ones?
                # For strict verification, we assume the compiled output is deterministic.
                # Use strict equality if possible, or just checks.
                # Checking type is a good minimal strict check.
                test_func += f"    assert ab{i}.conditions[{j}].type == {ctype}, 'Condition {j} type mismatch'\n"

                # Check integer params if simple
                cparams = c.get("params", {})
                if cparams:
                    # We skip deep param assertion for now to avoid order issues,
                    # but maybe check specific keys if critical?
                    pass

            # Effects
            raw_effs = ab.get("effects", [])
            test_func += f"    assert len(ab{i}.effects) == {len(raw_effs)}, 'Effect count mismatch'\n"
            for j, e in enumerate(raw_effs):
                etype = e.get("effect_type")
                val = e.get("value", 0)
                test_func += f"    assert ab{i}.effects[{j}].effect_type == {etype}, 'Effect {j} type mismatch'\n"
                test_func += f"    assert ab{i}.effects[{j}].value == {val}, 'Effect {j} value mismatch'\n"

        test_cases += test_func + "\n"

    # Write file
    os.makedirs(os.path.dirname(TEST_FILE_PATH), exist_ok=True)
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(header + test_cases)

    print(f"Generated {TEST_FILE_PATH}")


def main():
    print("Step 1: Loading Databases...")
    cards_data = load_json(CARDS_PATH)

    full_db_map = {}  # Unused now generally, but good for ref
    candidates = []

    # Process Members
    for _, card in cards_data.get("member_db", {}).items():
        candidates.append(card)

    # Process Lives
    for _, card in cards_data.get("live_db", {}).items():
        candidates.append(card)

    # Process Energy (Usually implicit abilities or none)
    for _, card in cards_data.get("energy_db", {}).items():
        candidates.append(card)

    print(f"Found {len(candidates)} total cards (Members, Lives, Energy).")

    print("Step 2: Generating Comprehensive Test Suite...")
    print("Step 2: Generating Comprehensive Test Suite...")
    generate_test_file(candidates, None)

    # We do NOT run the tests here to keep the script simple.
    # The user/workflow will run pytest separately.


if __name__ == "__main__":
    main()
