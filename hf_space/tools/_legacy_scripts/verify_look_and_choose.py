import json
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import engine_rust

from backend.rust_serializer import RustGameStateSerializer
from engine.game.data_loader import CardDataLoader


def verify():
    print("Loading data...")
    try:
        cards_path = os.path.join(PROJECT_ROOT, "data", "cards_compiled.json")
        with open(cards_path, "r", encoding="utf-8") as f:
            db_json = f.read()
        db = engine_rust.PyCardDatabase(db_json)

        loader = CardDataLoader(os.path.join(PROJECT_ROOT, "data", "cards.json"))
        m_db, l_db, e_db = loader.load()
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("Setting up Rust GameState...")
    gs = engine_rust.PyGameState(db)

    # LL-bp4-001-R＋ is ID 3
    p0_members = [3] * 20
    p1_members = [3] * 20
    p0_energy = [40000] * 12
    p1_energy = [40000] * 12
    p0_lives = [3] * 3
    p1_lives = [3] * 3

    gs.initialize_game(p0_members, p1_members, p0_energy, p1_energy, p0_lives, p1_lives)

    print("Progressing phases...")
    for i in range(50):
        phase = gs.phase
        p0_actions = gs.get_legal_action_ids_for_player(0)
        p1_actions = gs.get_legal_action_ids_for_player(1)
        curr_p = gs.current_player

        print(f"[{i}] Phase: {phase}, CurrP: {curr_p}, P0 Acts: {p0_actions}, P1 Acts: {p1_actions}")

        if phase == 4:  # MAIN
            break

        action = -1
        if p0_actions:
            action = p0_actions[0]
        elif p1_actions:
            action = p1_actions[0]
        else:
            print("No actions for either player!")
            break

        gs.step(action)

    if gs.phase != 4:
        print(f"FAILED to reach Main phase. End Phase: {gs.phase}")
        return

    print("Reached MAIN phase.")
    actions = gs.get_legal_action_ids()
    print(f"Legal actions in MAIN: {actions}")

    # Trigger choice
    choice_action = -1
    for a in actions:
        if 1000 <= a < 2000:
            choice_action = a
            break

    if choice_action != -1:
        gs.step(choice_action)
        print(f"Phase after choice trigger: {gs.phase}")

        serializer = RustGameStateSerializer(m_db, l_db, e_db)
        serialized = serializer.serialize_state(gs, viewer_idx=0)
        pending = serialized.get("pending_choice")

        print(f"Serialized Pending Choice:\n{json.dumps(pending, indent=2)}")
    else:
        print("Could not find choice action.")


if __name__ == "__main__":
    verify()
