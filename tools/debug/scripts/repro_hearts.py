import numpy as np

from engine.game.player_state import PlayerState
from engine.game.state_utils import MaskedDB, create_uid
from engine.models.card import MemberCard


def verify_hearts():
    print("--- Verifying Hearts Calculation ---")

    # 1. Mock DB with 1 card
    # Hearts: [1, 1, 1, 1, 1, 1, 0]
    hearts_arr = np.array([1, 1, 1, 1, 1, 1, 0], dtype=np.int32)
    card = MemberCard(
        card_id=1,
        card_no="001",
        name="Test Card",
        cost=1,
        hearts=hearts_arr,
        blade_hearts=np.zeros(7, dtype=np.int32),
        blades=1,
    )

    raw_db = {1: card}
    masked_db = MaskedDB(raw_db)

    # 2. Verify MaskedDB Access
    uid = create_uid(1, 1)  # Instance 1 of Card 1 -> 1048577
    print(f"UID: {uid}")

    if uid in masked_db:
        print("MaskedDB contains UID: YES")
        retrieved = masked_db[uid]
        print(f"Retrieved Card Name: {retrieved.name}")
        print(f"Retrieved Hearts Type: {type(retrieved.hearts)}")
        print(f"Retrieved Hearts: {retrieved.hearts}")
    else:
        print("MaskedDB contains UID: NO (FAILURE)")
        return

    # 3. Verify PlayerState Calculation
    p = PlayerState(0)
    p.stage[0] = uid  # Set UID to stage

    # Check effective hearts
    hraw = p.get_effective_hearts(0, masked_db)
    print(f"Effective Hearts Result: {hraw}")

    # DEBUG: Check numpy int vs int
    stage_val = p.stage[0]
    print(f"Stage Value Type: {type(stage_val)}")
    print(f"Is Instance of int? {isinstance(stage_val, int)}")

    if np.sum(hraw) > 0:
        print("SUCCESS: Hearts calculated correctly.")
    else:
        print("FAILURE: Hearts are zero.")


if __name__ == "__main__":
    verify_hearts()
