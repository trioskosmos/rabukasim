import json
import subprocess
import sys

# Force UTF-8 for this script's output
sys.stdout.reconfigure(encoding="utf-8")

CARDS_PATH = "data/cards_compiled.json"
POOL_PATH = "verified_card_pool.json"
TEST_FILE_PATH = "engine/tests/cards/test_auto_generated_strict.py"

# ENUM MAPPINGS (Sync with engine/models/ability.py)
SAFE_EFFECTS = {
    0: "DRAW",
    1: "ADD_BLADES",
    2: "ADD_HEARTS",
    6: "BOOST_SCORE",
    13: "ENERGY_CHARGE",
    8: "BUFF_POWER",
    30: "ADD_TO_HAND",
    26: "REVEAL_CARDS",
    7: "RECOVER_MEMBER",
}

SAFE_TRIGGERS = {1: "ON_PLAY", 2: "LIVE_START", 3: "LIVE_SUCCESS", 7: "ACTIVATED", 6: "CONSTANT"}

SAFE_CONDITIONS = {1: "TURN_1", 16: "COST_CHECK", 10: "GROUP_FILTER"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_test_file(candidates, full_db):
    # ... header ...
    header = """
import pytest
from engine.game.game_state import initialize_game
from engine.models.ability import ConditionType

@pytest.fixture
def game():
    return initialize_game(deck_type="training")

def _find_id(game, cno):
    for k, v in game.member_db.items():
        if v.card_no == cno: return k
    return None
"""
    test_cases = ""
    import re

    def sanitize(name):
        return re.sub(r"[^a-zA-Z0-9_]", "_", name)

    for cno in candidates:
        card = full_db[cno]
        ab = card["abilities"][0]
        trig_exp = ab["trigger"]

        safe_name = sanitize(cno)

        # Conditions Assertion Block
        raw_conds = ab.get("conditions", [])
        cond_checks = ""
        if raw_conds:
            cond_checks += f"\n    # Assert Conditions (Count: {len(raw_conds)})"
            cond_checks += f"\n    assert len(ab.conditions) == {len(raw_conds)}, 'Condition count mismatch'"
            for i, c in enumerate(raw_conds):
                ctype = c.get("type")
                cond_checks += (
                    f"\n    assert ab.conditions[{i}].condition_type == {ctype}, 'Condition {i} type mismatch'"
                )
        else:
            cond_checks = "\n    # Assert No Condition\n    assert not ab.conditions, 'Expected no conditions'"

        # Effects Assertion Block
        raw_effs = ab.get("effects", [])
        eff_checks = ""
        if raw_effs:
            eff_checks += f"\n    # Assert Effects (Count: {len(raw_effs)})"
            eff_checks += f"\n    assert len(ab.effects) == {len(raw_effs)}, 'Effect count mismatch'"
            for i, e in enumerate(raw_effs):
                etype = e.get("effect_type")
                val = e.get("value", 0)
                eff_checks += f"\n    eff{i} = ab.effects[{i}]"
                eff_checks += f"\n    assert eff{i}.effect_type == {etype}, 'Effect {i} type mismatch'"
                eff_checks += f"\n    assert eff{i}.value == {val}, 'Effect {i} value mismatch'"
        else:
            eff_checks = "\n    pytest.fail('No effects parsed')"

        test_func = f"""
def test_strict_{safe_name}(game):
    cno = "{cno}"
    cid = _find_id(game, cno)
    if cid is None:
        pytest.skip(f"{{cno}} not found in DB")

    card = game.member_db[cid]

    # Strict Assertions
    if not card.abilities:
        pytest.fail("No abilities parsed")

    ab = card.abilities[0]

    # Assert Trigger
    assert ab.trigger == {trig_exp}, f"Trigger mismatch: expected {trig_exp}, got {{ab.trigger}}"
    {cond_checks}
    {eff_checks}
"""
        test_cases += test_func

    # ... write file ...
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(header + test_cases)


def run_verification():
    try:
        # Run pytest and redirect to file
        outfile = "verification_output.txt"
        cmd = [sys.executable, "-m", "pytest", TEST_FILE_PATH, "-v"]

        print(f"DEBUG: Running command: {cmd}")

        try:
            # Use binary mode so subprocess can write bytes directly
            with open(outfile, "wb") as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=False)
        except Exception as e:
            print(f"Subprocess failed: {e}")
            traceback.print_exc()

        # Read file
        try:
            with open(outfile, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()
        except Exception as e:
            output = f"Error reading output: {e}"

        # Mock result object for compatibility
        class MockResult:
            def __init__(self, out):
                self.stdout = out
                self.stderr = ""

        return MockResult(output)
    except Exception:
        traceback.print_exc()
        return None


import traceback


# Global exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    traceback.print_exception(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_exception


def main():
    # try: <--- REMOVED
    print("Step 1: Identifying Candidates...")
    cards_data = load_json(CARDS_PATH)
    # ... (rest of function)
    pool_data = load_json(POOL_PATH)

    current_pool = set(pool_data.get("verified_abilities", []))
    current_vanilla = set(pool_data.get("vanilla_members", []) + pool_data.get("vanilla_lives", []))

    full_db_map = {}  # card_no -> data
    candidates = []

    for _, card in cards_data.get("member_db", {}).items():
        cno = card.get("card_no")
        if not cno:
            continue

        full_db_map[cno] = card

        if cno in current_vanilla:
            continue

        # We DO Check existing verified_abilities to ensure they pass strict test if they are simple
        # if cno in current_pool: continue

        # strict strict filter
        abilities = card.get("abilities", [])
        if len(abilities) != 1:
            continue  # ONLY SINGLE ABILITY FOR NOW

        ab = abilities[0]
        if ab.get("trigger", 0) not in SAFE_TRIGGERS:
            continue

        # Condition Check
        raw_conds = ab.get("conditions", [])
        safe_conds = True
        for c in raw_conds:
            ctype = c.get("type")
            if ctype not in SAFE_CONDITIONS:
                safe_conds = False
                break
        if not safe_conds:
            continue

        effects = ab.get("effects", [])
        if not effects:
            continue

        # Safe Effect Check (ALL must be safe)
        safe_effects = True
        for e in effects:
            etype = e.get("effect_type")
            if etype not in SAFE_EFFECTS:
                safe_effects = False
                break
        if not safe_effects:
            continue

        # Check params safety
        safe_params = True
        for e in effects:
            params = e.get("params", {})
            # We strictly exclude nested logic for now
            if "condition" in params or "target_filter" in params:
                safe_params = False
                break
        if not safe_params:
            continue

        candidates.append(cno)

    print(f"Found {len(candidates)} candidates for Strict Verification (including existing).")
    if not candidates:
        print("No new candidates found.")
        return

    print("Step 2: Generating Test Suite...")
    generate_test_file(candidates, full_db_map)

    print("Step 3: Running Strict Verification Tests...")
    test_result = run_verification()

    # Parse output to find passing tests
    # We look for "test_strict_PL_... PASSED"
    # Actually pytest output is standard.
    # Simple regex on stdout
    import re

    passing_cnos = []

    # Regex: test_strict_(.*?) PASSED
    # Need to reconstruct CNO from the safe name?
    # Better: The test name includes the ID safely.
    # Let's simple mapping: safe_name -> real_cno

    # safe_to_real = {cno.replace('!','_').replace('-','_'): cno for cno in candidates}
    def sanitize(name):
        return re.sub(r"[^a-zA-Z0-9_]", "_", name)

    safe_to_real = {sanitize(cno): cno for cno in candidates}

    output_text = test_result.stdout if test_result.stdout else ""
    # print head of output
    print("DEBUG: Pytest Output Head:\n" + output_text[:500] + "\n...")

    for line in output_text.splitlines():
        if "PASSED" in line:
            # Found a pass line, try to parse
            # Format: [gw7] [  2%] PASSED engine/tests/...::test_strict_NAME
            match = re.search(r"test_strict_([a-zA-Z0-9_]+)", line)
            if match:
                safe_name = match.group(1).strip()
                if safe_name in safe_to_real:
                    passing_cnos.append(safe_to_real[safe_name])
                else:
                    print(f"DEBUG: Parsed '{safe_name}' but not in safe_to_real candidates.")
            else:
                print(f"DEBUG: PASSED line found but regex failed: {line}")

    print(f"Step 4: Analysis Complete. {len(passing_cnos)} / {len(candidates)} passed verification.")

    failures = set(candidates) - set(passing_cnos)
    if failures:
        print(f"Failed Strict Verification (Removing from pool if present): {len(failures)}")
        print(list(failures)[:10])

        # Remove failures from pool
        original_len = len(pool_data["verified_abilities"])
        pool_data["verified_abilities"] = [c for c in pool_data["verified_abilities"] if c not in failures]
        removed_count = original_len - len(pool_data["verified_abilities"])
        if removed_count > 0:
            print(f"Removed {removed_count} failed cards from pool.")

    # Update Pool with passes
    if passing_cnos:
        before_len = len(pool_data["verified_abilities"])
        pool_data["verified_abilities"].extend(passing_cnos)
        pool_data["verified_abilities"] = list(set(pool_data["verified_abilities"]))
        added_count = len(pool_data["verified_abilities"]) - before_len

        save_json(POOL_PATH, pool_data)
        print(f"FAILED SAFE update: Net change +{added_count} cards. Pool saved to {POOL_PATH}")
    else:
        # Save anyway if we removed stuff
        if failures:
            save_json(POOL_PATH, pool_data)
            print("Pool updated (Removals only).")
    # except Exception: <--- REMOVED
    #    traceback.print_exc()


if __name__ == "__main__":
    main()
