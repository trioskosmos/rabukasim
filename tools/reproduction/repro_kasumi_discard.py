import json
import os
import sys

# Setup path
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine_rust import PyCardDatabase, PyGameState

from backend.rust_serializer import RustGameStateSerializer
from engine.models.card import EnergyCard, LiveCard, MemberCard


def verify_fixes():
    db_path = "engine/data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # PyCardDatabase expects a JSON string
    db_rust = PyCardDatabase(json.dumps(data))

    # Serializer expects model dicts
    member_db = {int(k): MemberCard(**v) for k, v in data["member_db"].items()}
    live_db = {int(k): LiveCard(**v) for k, v in data.get("live_db", {}).items()}
    energy_db = {int(k): EnergyCard(**v) for k, v in data.get("energy_db", {}).items()}

    gs = PyGameState(db_rust)

    # Initialize game
    deck = [i for i in range(100, 150)]
    energy = [i for i in range(200, 250)]
    lives = [i for i in range(300, 310)]
    gs.initialize_game(deck, deck, energy, energy, lives, lives)

    # Setup state: Kasumi (CID 467) in discard, energy available
    kasumi_cid = 467
    gs.current_player = 0
    gs.phase = 4  # Main

    p0 = gs.get_player(0)
    p0.discard = [kasumi_cid]
    p0.hand = [101]  # Dummy card for cost
    p0.energy_zone = [500, 501, 502, 503]
    p0.tapped_energy = [False] * 4
    gs.set_player(0, p0)

    serializer = RustGameStateSerializer(member_db, live_db, energy_db)

    # 1. Check Main Phase actions (Discard activation)
    state = serializer.serialize_state(gs, viewer_idx=0)
    print("\n--- Main Phase Verification ---")
    kasumi_actions = [
        a for a in state["legal_actions"] if a.get("type") == "ABILITY" and a.get("location") == "discard"
    ]

    if not kasumi_actions:
        print("FAILED: Kasumi activation action not found in legal_actions.")
    else:
        for action in kasumi_actions:
            print(f"Action {action['id']}: {action['desc']}")
            print(f"  > Text: '{action.get('text', 'N/A')}' (Expected: Empty string)")

    # 2. Check Response Phase actions (Slot selection)
    # Activate Kasumi: 2000 + 0*10 + 1 (Activated ability)
    activate_action = 2000 + 0 * 10 + 1
    gs.step(activate_action)

    if gs.phase != 10:  # Phase::Response
        print(f"FAILED: Game did not enter Response phase (Current phase: {gs.phase})")
        return

    state = serializer.serialize_state(gs, viewer_idx=0)
    print("\n--- Response Phase Verification (Slot Selection) ---")
    select_actions = [a for a in state["legal_actions"] if a.get("type") == "SELECT_STAGE"]

    if len(select_actions) != 3:
        print(f"FAILED: Expected 3 SELECT_STAGE actions, found {len(select_actions)}")

    for action in select_actions:
        print(f"Action {action['id']}: {action['desc']}")
        print(f"  > Source ID: {action.get('source_card_id')} (Expected: {kasumi_cid})")
        print(f"  > Source Name: {action.get('source_name')} (Expected: 中須 かすみ)")
        print(f"  > Text: '{action.get('text', 'N/A')}' (Expected: Empty string)")


if __name__ == "__main__":
    verify_fixes()
