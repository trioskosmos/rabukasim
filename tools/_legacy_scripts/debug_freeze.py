import os
import sys

import numpy as np

# Add path to import game modules
sys.path.append(os.getcwd())

from game.game_state import GameState, Phase


# Mock loader
def mock_loader():
    # Helper to create mock cards
    from game.game_state import LiveCard, MemberCard

    m_db = {}
    l_db = {}
    e_db = {}

    # Create a member card
    m = MemberCard(
        card_id=1,
        name="Test Member",
        cost=1,
        hearts=np.array([1, 0, 0, 0, 0, 0]),
        blade_hearts=np.array([0, 0, 0, 0, 0, 0]),
        blades=1,
        img_path="test.png",
    )
    m_db[1] = m

    # Create a live card
    l = LiveCard(
        card_id=100, name="Test Live", score=10, required_hearts=np.array([1, 0, 0, 0, 0, 0, 0]), img_path="live.png"
    )
    l_db[100] = l

    return m_db, l_db, e_db


# Patch GameState
m_db, l_db, e_db = mock_loader()
GameState.member_db = m_db
GameState.live_db = l_db


def test_live_set_fix():
    print("--- Testing LIVE_SET Fix ---")
    gs = GameState()
    gs.phase = Phase.LIVE_SET
    gs.active_player.hand = [1, 1, 100, 1]  # 3 Members, 1 Live
    gs.active_player.live_zone = []

    mask = gs.get_legal_actions()

    # Action indices for LIVE_SET are 400 + i
    # P0 hand indices: 0 (Mem), 1 (Mem), 2 (Live), 3 (Mem)
    # 400->False, 401->False, 402->True, 403->False

    mem_action = 400 + 0
    live_action = 400 + 2

    print(f"Member Action (400) Legal: {mask[mem_action]}")
    print(f"Live Action (402) Legal: {mask[live_action]}")

    if mask[mem_action]:
        print("FAIL: Member card allowed in LIVE_SET")
    else:
        print("PASS: Member card blocked in LIVE_SET")

    if mask[live_action]:
        print("PASS: Live card allowed in LIVE_SET")
    else:
        print("FAIL: Live card blocked in LIVE_SET")


def test_live_result_transition():
    print("\n--- Testing LIVE_RESULT Transition ---")
    gs = GameState()
    gs.phase = Phase.LIVE_RESULT
    gs.turn_number = 1

    # Setup some dummy state so it doesn't crash on calculation
    gs.players[0].passed_lives = []
    gs.players[1].passed_lives = []

    print(f"Before Step: Phase={gs.phase}, Turn={gs.turn_number}")

    # Step(0) should be legal (auto-advance)
    mask = gs.get_legal_actions()
    if not mask[0]:
        print("FAIL: Action 0 not legal in LIVE_RESULT")
        return

    # Execute step 0 (which calls _do_live_result internally)
    # Note: step(0) calls _do_live_result which sets phase to ACTIVE
    new_gs = gs.step(0)

    print(f"After Step: Phase={new_gs.phase}, Turn={new_gs.turn_number}")

    if new_gs.phase == Phase.ACTIVE:
        print("PASS: Transitioned to ACTIVE")
    else:
        print(f"FAIL: Stayed in {new_gs.phase}")

    if new_gs.turn_number == 2:
        print("PASS: Turn incremented correctly (1 -> 2)")
    elif new_gs.turn_number == 3:
        print("FAIL: Double turn increment detected (1 -> 3)")
    else:
        print(f"FAIL: Weird turn number {new_gs.turn_number}")


def test_main_phase_stuck():
    print("\n--- Testing MAIN Phase Stuck ---")
    gs = GameState()
    gs.phase = Phase.MAIN
    gs.active_player.hand = [1]  # 1 Member
    gs.active_player.stage = np.full(3, -1)
    gs.active_player.energy_zone = []  # 0 Energy

    # Cost is 1, Energy is 0 -> Cannot play.
    # Should only have Pass (0).

    mask = gs.get_legal_actions()

    play_action = 1 + 0 * 3 + 0  # Hand[0] to Area 0

    print(f"Play Action Legal: {mask[play_action]}")
    print(f"Pass Action Legal: {mask[0]}")

    if mask[play_action]:
        print("FAIL: Allowed playing card without energy")

    if mask[0]:
        print("PASS: Pass action available")
    else:
        print("FAIL: Pass action NOT available (STUCK!)")


if __name__ == "__main__":
    test_live_set_fix()
    test_live_result_transition()
    test_main_phase_stuck()
