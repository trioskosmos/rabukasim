import os
import sys
import json
import traceback

# --- PATH SETUP ---
# Path to the root of the project
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "engine"))

import engine_rust
from backend.rust_serializer import RustGameStateSerializer
from game.data_loader import CardDataLoader


def run_repro():
    print("=" * 60)
    print("REPRODUCTION FOR: PL!-sd1-002-SD (絢瀬 絵里)")
    print("=" * 60)

    # 1. Load Data
    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()

    compiled_path = os.path.join(PROJECT_ROOT, "data/cards_compiled.json")
    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_json_str = f.read()

    # 2. Init Engine
    rust_db = engine_rust.PyCardDatabase(compiled_json_str)
    gs = engine_rust.PyGameState(rust_db)
    serializer = RustGameStateSerializer(m_db, l_db, e_db)

    # 3. Setup Game
    # Find IDs
    target_cid = 248
    plinth_cid = 1368  # Used for padding
    energy_cid = 40000

    p0_deck = [plinth_cid] * 60
    p1_deck = [plinth_cid] * 60
    p0_energy = [energy_cid] * 60
    p1_energy = [energy_cid] * 60
    p0_lives = [l for l in l_db.keys()][:3]
    p1_lives = [l for l in l_db.keys()][:3]

    print("Initializing game...")
    gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    # 4. God Mode Setup
    p0 = gs.get_player(0)
    p0.energy_zone = [energy_cid] * 12
    p0.tapped_energy = [False] * 12
    # Ensure some cards in discard if needed
    p0.discard = [plinth_cid] * 5
    gs.set_player(0, p0)

    # Place plinths for slots
    gs.set_stage_card(0, 0, plinth_cid)
    gs.set_stage_card(0, 1, plinth_cid)
    gs.set_stage_card(0, 2, plinth_cid)

    # Target Setup
    card_type = "MEMBER"
    if card_type == "MEMBER":
        gs.set_hand_cards(0, [target_cid])
        gs.phase = 4  # Main
        play_action = 1  # Slot 0
    else:
        gs.set_hand_cards(0, [target_cid])
        gs.phase = 5  # LiveSet
        play_action = 400

    print(f"Phase: {gs.phase}")
    print(f"Target Card: {target_cid} in Hand")

    # 5. UI Visibility Check (Before Action)
    print("\n[PRE-ACTION UI VIEW]")
    view = serializer.serialize_state(gs, viewer_idx=0)
    legal = view.get("legal_actions", [])
    found_action = False
    for a in legal:
        print(f"  - Action ID {a['id']}: {a['description']}")
        if a["id"] == play_action:
            found_action = True

    if not found_action:
        print("!!! WARNING: Play action {play_action} NOT found in legal actions !!!")
    else:
        print("OK: Play action found.")

    # 6. Step
    print(f"\nExecuting Action {play_action}...")
    try:
        gs.step(play_action)
        print("Action executed successfully.")
    except Exception as e:
        print(f"!!! CRASH during step: {e}")
        traceback.print_exc()
        return

    # 7. Post-Action Analysis
    print("\n[POST-ACTION STATE]")
    p0 = gs.get_player(0)
    print(f"  Phase: {gs.phase}")
    print(f"  Hand Size: {len(p0.hand)}")
    print(f"  Discard Size: {len(p0.discard)}")
    print(f"  Score: {p0.score}")

    # UI View after (for abilities that trigger choices)
    view = serializer.serialize_state(gs, viewer_idx=0)
    legal = view.get("legal_actions", [])
    if legal:
        print("Next Legal Actions:")
        for a in legal:
            print(f"  - Action ID {a['id']}: {a['description']}")

    # TODO: Add your custom assertions here!
    # assert p0.score == 1
    # print("Assertion Passed!")


if __name__ == "__main__":
    run_repro()
