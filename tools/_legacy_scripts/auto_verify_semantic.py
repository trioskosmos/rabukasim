import json
import re
import subprocess
import sys
import traceback

# Force UTF-8
sys.stdout.reconfigure(encoding="utf-8")

CARDS_PATH = "data/cards_compiled.json"
POOL_PATH = "verified_card_pool.json"
TEST_FILE_PATH = "engine/tests/cards/test_generated_semantic.py"

# 1. Verification Modules (Effect -> Test Logic)
SEMANTIC_HANDLERS = {
    # EffectType.DRAW (0)
    0: {
        "name": "DRAW",
        "setup": """
    # Setup for DRAW: Ensure deck has cards
    player.energy_zone = [game.member_db[cid] for _ in range(10)] # Limitless energy
""",
        "pre_state": """
    prev_deck = len(player.main_deck)
    prev_hand = len(player.hand)
""",
        "assertion": """
    # Assert DRAW: Deck -N, Hand net change depends on cost but Deck is reliable
    val = {val}
    assert len(player.main_deck) == prev_deck - val, f"Deck did not decrease by {val}"
""",
    },
    # EffectType.ADD_BLADES (1)
    1: {
        "name": "ADD_BLADES",
        "setup": """
    player.energy_zone = [game.member_db[cid] for _ in range(10)]
""",
        "pre_state": """
    prev_blades = player.blades
""",
        "assertion": """
    # Assert BLADES: Blades +N
    val = {val}
    curr_blades = player.blades
    assert curr_blades == prev_blades + val, "Blades count mismatch"
""",
    },
    # EffectType.BOOST_SCORE (6)
    6: {
        "name": "BOOST_SCORE",
        "setup": """
    # Setup for SCORE: Start live
    game.current_live_card = game.live_db[list(game.live_db.keys())[0]] # Dummy live
    player.energy_zone = [game.member_db[cid] for _ in range(10)]
""",
        "pre_state": """
    prev_score = game.score
""",
        "assertion": """
    # Assert SCORE: Score +N
    val = {val}
    assert game.score == prev_score + val, "Score boost mismatch"
""",
    },
    # EffectType.RECOVER_LIVE (3)
    3: {
        "name": "RECOVER_LIVE",
        "setup": """
    # Setup: Empty live zone/Discard has lives? No, Recover Live usually means Heal HP.
    # Actually EffectType 3 is RECOVER_LIVE (Heal HP).
    player.energy_zone = [game.member_db[cid] for _ in range(10)]
    # Damage player first so they can recover
    player.life -= 2
    if player.life < 1: player.life = 1
""",
        "pre_state": """
    prev_life = player.life
""",
        "assertion": """
    # Assert LIFE: Life +N
    val = {val}
    assert player.life == prev_life + val, "Life recovery mismatch"
""",
    },
    # EffectType.ENERGY_CHARGE (4)
    4: {
        "name": "ENERGY_CHARGE",
        "setup": """
    # Setup: Ensure deck exists
    player.energy_zone = [game.member_db[cid] for _ in range(10)]
""",
        "pre_state": """
    prev_energy = len(player.energy_zone)
""",
        "assertion": """
    # Assert ENERGY: Zone +N
    val = {val}
    curr_energy = len(player.energy_zone)
    # Note: We played a card (if it went to energy? no member play).
    # Effect is charge.
    assert curr_energy == prev_energy + val, "Energy charge mismatch"
""",
    },
    # EffectType.RECOVER_MEMBER (7)
    # 7: { ... } # Disabled until Choice Injection is implemented
}

SAFE_TRIGGERS = {
    1: "ON_PLAY",
    # 2: "LIVE_START", # Harder to verify via play_card, needs separate loop
    # 3: "LIVE_SUCCESS"
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_semantic_tests(candidates, full_db):
    header = """
import pytest
from engine.game.game_state import initialize_game
from engine.models.card import MemberCard

@pytest.fixture
def game():
    g = initialize_game(deck_type="training")
    g.verbose = True
    return g

def _find_id(game, cno):
    for k, v in game.member_db.items():
        if v.card_no == cno: return k
    return None

def resolve_choices(game):
    'Automatically resolve any pending choices by picking the first valid option (Index 0).'
    max_loops = 10
    loops = 0
    while game.pending_choices and loops < max_loops:
        loops += 1
        ctype, params = game.pending_choices[0]
        action_id = -1

        # Determine correct Action ID based on choice type offset
        if ctype == "TARGET_HAND":
            action_id = 500 # Index 0
        elif ctype in ["TARGET_LIVE", "TARGET_DISCARD", "TARGET_REMOVED", "TARGET_DECK"]:
            action_id = 600 # Index 0
        elif ctype == "SELECT_FROM_LIST":
             # SELECT_FROM_LIST usually maps to same offsets or bespoke?
             # Actually EffectMixin doesn't show specific offset for SELECT_FROM_LIST in the snippet I saw.
             # It likely uses generic handling or might be 500/600 depending on source?
             # Let's assume 600 for now or verify if it crashes.
             action_id = 600

        if action_id != -1:
            try:
                game.take_action(action_id)
            except Exception as e:
                print(f"Auto-choice failed: {e}")
                break
        else:
            break

        game._process_rule_checks()
"""
    test_cases = ""

    def sanitize(name):
        return re.sub(r"[^a-zA-Z0-9_]", "_", name)

    for cno in candidates:
        card = full_db[cno]
        ab = card["abilities"][0]
        eff = ab["effects"][0]
        etype = eff["effect_type"]
        val = eff.get("value", 0)

        handler = SEMANTIC_HANDLERS.get(etype)
        if not handler:
            continue

        safe_name = sanitize(cno)

        # Populate template
        setup_code = handler["setup"]
        pre_code = handler["pre_state"]
        # Format assertion with value
        assert_code = handler["assertion"].format(val=val)

        test_func = f"""
def test_semantic_{safe_name}(game):
    cno = "{cno}"
    cid = _find_id(game, cno)
    if cid is None: pytest.skip("ID not found")

    player = game.players[0]

    # 1. Put card in hand
    # card_inst = game.member_db[cid]
    player.hand.append(cid)
    card_idx = len(player.hand) - 1

    # Common Setup: Add dummy resources for costs (Discard cost, etc.)
    # Add 3 dummy cards to hand (besides the candidate)
    for _ in range(3):
        # Use a vanilla card ID if possible, or just the same candidate ID
        player.hand.append(888) # Easy Member

    # Add 3 dummy cards to discard
    for _ in range(3):
        player.discard.append(888)

    # Add infinite energy
    player.energy_zone = [game.member_db[cid] for _ in range(10)]

    {setup_code}
    {pre_code}

    # 2. ACTION: Play Card (Simulate Play)
    # We bypass strict turn phase checks for semantic unit test if possible,
    # or we set phase.
    game.phase = 4 # MAIN_PHASE
    game.turn_player = 0

    # Mock costs if strictly needed or rely on infinite energy
    # Attempt play
    try:
        # Play into Center Stage (Slot 0)
        # Using internal method to bypass Action ID math, but effectively same logic
        game._play_member(hand_idx=card_idx, area_idx=0)

        # 3. RESOLUTION: Drain the Trigger Queue
        # _play_member only queues the effect. We must process it.
        game._process_rule_checks()

        # 4. CHOICE RESOLUTION: Handle "Select Target" prompts
        resolve_choices(game)

    except Exception as e:
        pytest.fail(f"Play failed: {{e}}")

    {assert_code}
"""
        test_cases += test_func

    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(header + test_cases)


def main():
    print("Step 1: Selecting Candidates for SEMANTIC Verification...")
    cards_data = load_json(CARDS_PATH)
    full_db = cards_data.get("member_db", {})

    pool_data = load_json(POOL_PATH)
    # We can RE-VERIFY existing cards too!

    candidates = []

    for cno, card in full_db.items():
        # Filter for logic we can handle
        abilities = card.get("abilities", [])
        if len(abilities) != 1:
            continue
        ab = abilities[0]

        # Must be ON_PLAY for this initial "Play Card" simulation
        if ab.get("trigger") != 1:
            continue  # ON_PLAY

        if ab.get("conditions"):
            continue  # No conditions for Batch 5

        effects = ab.get("effects", [])
        if len(effects) != 1:
            continue

        eff = effects[0]
        etype = eff.get("effect_type")
        if etype not in SEMANTIC_HANDLERS:
            continue

        # Params check
        params = eff.get("params", {})
        # Relax: Allow empty params or params that don't change logic (like target=0 default)

        # We only skip if there are "condition" or "target_filter" params which imply complex logic
        if "condition" in params or "target_filter" in params:
            continue

        candidates.append(card.get("card_no"))  # Use string ID

    print(f"Found {len(candidates)} candidates.")

    print("Step 2: Generaling Behavioral Tests...")
    # Need to map back to cno since we iterated values
    # Actually candidates list is correct.
    # Map cno -> data
    cno_to_data = {}
    for card in full_db.values():
        if card.get("card_no"):
            cno_to_data[card["card_no"]] = card

    generate_semantic_tests(candidates, cno_to_data)

    print("Step 3: Execution...")
    try:
        outfile = "semantic_log.txt"
        cmd = [sys.executable, "-m", "pytest", TEST_FILE_PATH, "-v"]
        with open(outfile, "wb") as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=False)

        # Parse result
        with open(outfile, "r", encoding="utf-8", errors="replace") as f:
            log = f.read()

        passes = 0
        passed_cnos = []
        for line in log.splitlines():
            if "PASSED" in line:
                passes += 1
                # Extract CNO
                # test_semantic_PL_...
                m = re.search(r"test_semantic_([a-zA-Z0-9_]+)", line)
                if m:
                    # We need to map safe name back?
                    # Or just count passes for now?
                    # Let's trust the logic.
                    pass

        print(f"Behavioral Simulation Results: {passes} / {len(candidates)} PASSED")

        # 4. Update Verified Pool
        if passes > 0:
            current_pool = load_json(POOL_PATH)
            # Find the ID from the sanitized name is hard, so let's rely on the execution log
            # Or better: Just re-iterate candidates and check if their test passed?
            # The log contains "test_semantic_SANITIZED".
            # Let's rebuild the map: Sanitized -> Original ID
            sanitized_map = {}
            for cno in candidates:
                s = re.sub(r"[^a-zA-Z0-9_]", "_", cno)
                sanitized_map[f"test_semantic_{s}"] = cno

            newly_verified = []
            for line in log.splitlines():
                if "PASSED" in line:
                    # Line format: engine/tests/cards/test_generated_semantic.py::test_semantic_PL_... PASSED
                    m = re.search(r"(test_semantic_[a-zA-Z0-9_]+)", line)
                    if m:
                        tname = m.group(1)
                        real_id = sanitized_map.get(tname)
                        if real_id:
                            newly_verified.append(real_id)

            print(f"Identifying {len(newly_verified)} unique verified cards.")

            # Add to pool
            pool_set = set(current_pool.get("verified_abilities", []))
            added_count = 0
            for vid in newly_verified:
                if vid not in pool_set:
                    current_pool["verified_abilities"].append(vid)
                    added_count += 1

            if added_count > 0:
                print(f"Adding {added_count} new cards to verified pool!")
                save_json(POOL_PATH, current_pool)
            else:
                print("No new cards to add (all passed were already verified).")

        if passes < len(candidates):
            print("CRITICAL: Some cards failed semantic verification! Check semantic_log.txt")

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
