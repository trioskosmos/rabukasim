import sys
import os
import json

# Add project root to path
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import engine_rust
from backend.rust_serializer import RustGameStateSerializer
from engine.game.data_loader import CardDataLoader


def test_repro_discard_1199():
    print("--- Starting Repro for Card 1199 (PL!SP-bp1-005-R) ---")

    # 1. Load Data
    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        compiled_json_str = f.read()

    # 2. Init
    rust_db = engine_rust.PyCardDatabase(compiled_json_str)
    gs = engine_rust.PyGameState(rust_db)

    # 3. Setup State
    # Card 1199 is Ren Hazuki (2-cost, Liella!)
    ren_hazuki_cid = 1199
    other_member_cid = 1  # Honoka

    p0 = gs.get_player(0)
    p0.hand = [ren_hazuki_cid, other_member_cid]
    p0.energy_zone = [40001, 40001]  # 2 energy
    p0.set_tapped_energy([False, False])
    p0.deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    gs.set_player(0, p0)

    # 4. Trigger Ability (Play Member)
    # Action ID for PlayMember in Main phase: 1 to 180 (adj = id-1, hand_idx = adj/3, slot_idx = adj%3)
    # Play ren_hazuki from hand index 0 to slot 0
    # id = (0*3 + 0) + 1 = 1
    print(f"Step 1: Playing Card {ren_hazuki_cid} from hand[0] to slot 0")
    gs.step(rust_db, 1)

    # After playing, OnPlay triggers should be in queue or active
    print(f"Phase: {gs.phase}")

    # In Response phase, we should see the discard prompt
    # List legal actions
    legal_actions = gs.get_legal_action_ids(rust_db)
    print(f"Legal Actions: {legal_actions}")

    # Action ID for SelectHand (Discard) is 300+idx
    # We want to discard hand_idx 0 (the card that was at index 1 is now at 0)
    print("Step 2: Discarding card at hand index 0")
    # Actually, after playing Ren (idx 0), Honoka (idx 1) becomes the new idx 0.
    gs.step(rust_db, 300)

    # Verify State
    p0 = gs.get_player(0)
    print(f"Hand after discard: {p0.hand}")
    print(f"Discard pile: {p0.discard}")

    if other_member_cid in p0.discard:
        print("SUCCESS: Card moved to discard.")
    else:
        print("FAILURE: Card NOT in discard pile.")


if __name__ == "__main__":
    test_repro_discard_1199()
