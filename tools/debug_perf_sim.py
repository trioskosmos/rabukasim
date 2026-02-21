import os
import sys

import numpy as np

# Adjust path to import game modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.game_state import GameState, LiveCard


def run_debug_sim():
    print("=== PERFORMANCE DEBUG SIMULATION ===")
    game = GameState(verbose=True)
    p0 = game.players[0]

    # Recreate the "Total Hearts" from screenshot
    # Red: 2, Yellow: 3, Green: 2, Blue: 1, Purple: 6
    # Indicies: 0:Pink, 1:Red, 2:Yellow, 3:Green, 4:Blue, 5:Purple, 6:Any

    # We'll mock the live cards and member contributions
    # PASTEL requirements: Yellow: 1, Green: 1, Blue: 1, Purple: 1, Any: 5
    req = np.zeros(7, dtype=int)
    req[2] = 1  # Yellow
    req[3] = 1  # Green
    req[4] = 1  # Blue
    req[5] = 1  # Purple
    req[6] = 5  # Any

    live_pastel = LiveCard(
        card_id=9999,
        card_no="PASTEL",
        name="PASTEL",
        score=5,
        required_hearts=req,
        ability_text="",
        img_path="",
        group="",
        blade_hearts=np.zeros(7, dtype=int),
        volume_icons=0,
        draw_icons=0,
    )

    # Add to live zone
    p0.live_zone = [9999]
    game.live_db[9999] = live_pastel

    # Setup some dummy stage members so we can give them hearts
    # Actually, we can just mock get_effective_hearts
    # But it's easier to just give the player some hearts in their "all_blade" or similar?
    # No, let's just mock total_hearts calculation or replace it.

    # Total Hearts from screenshot:
    total_hearts = np.zeros(7, dtype=int)
    total_hearts[1] = 2  # Red
    total_hearts[2] = 3  # Yellow
    total_hearts[3] = 2  # Green
    total_hearts[4] = 1  # Blue
    total_hearts[5] = 6  # Purple

    print(f"Total Hearts Available: {total_hearts}")
    print(f"PASTEL Required: {req}")

    # Test _check_hearts_meet_requirement
    passed, reason = game._check_hearts_meet_requirement(total_hearts, req)
    print(f"\n_check_hearts_meet_requirement Result: {passed}")
    print(f"Reason: {reason}")

    # Test _consume_hearts
    if passed:
        remaining = total_hearts.copy()
        game._consume_hearts(remaining, req)
        print(f"\nRemaining after consumption: {remaining}")

    # Test simulation loop (what the UI sees)
    print("\n--- Running UI Simulation Loop Logic ---")
    sim_remaining = total_hearts.copy()

    filled = np.zeros(7, dtype=np.int32)
    used_sim = np.zeros(7, dtype=np.int32)

    # Color Reqs
    for i in range(6):
        use = min(sim_remaining[i], req[i])
        filled[i] = use
        used_sim[i] += use

        deficit = req[i] - use
        if deficit > 0:
            rainbow_available = sim_remaining[6] - used_sim[6]
            take_rainbow = min(rainbow_available, deficit)
            filled[i] += take_rainbow
            used_sim[6] += take_rainbow

    # Any Reqs
    if len(req) > 6 and req[6] > 0:
        needed_any = req[6]
        leftover_sum = sum(sim_remaining[i] - used_sim[i] for i in range(7))
        filled[6] = min(leftover_sum, needed_any)

    print(f"Filled pips for UI: {filled}")
    print(f"Is pastel satisfied? {np.all(filled >= req)}")


if __name__ == "__main__":
    run_debug_sim()
