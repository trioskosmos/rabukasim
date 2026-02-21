import os
import sys

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase


def detailed_debug():
    print("--- Debugging Performance Loop ---")

    # Init state
    state = GameState(verbose=True)
    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()
    GameState.member_db = m
    GameState.live_db = l

    # Setup Scenario: P1 is active in PERFORMANCE_P2
    state.phase = Phase.PERFORMANCE_P2
    state.current_player = 1
    state.first_player = 1  # So P2 (1) goes first, then P1 (0).
    # Wait, if first_player=1, then P1 is the first player.
    # P1 (Player index 1) starts.
    # Sequence: P1 -> P0.
    # So if we are in PERFORMANCE_P2 (Phase 7).
    # _advance_performance: if P2 -> P1.

    # Let's verify setup matching ELO log: "TrueRandom (1) in 7 phase".
    # Player 1 is TrueRandom. Phase is 7.

    p = state.players[1]

    # Add a live card with ON_LIVE_START trigger (e.g. Card 491 Hanamaru has LIVE_START?)
    # Hanamaru 491 has LIVE_START.
    # Add to live zone.
    p.live_zone = [400]  # Dummy ID? No, use real ID.
    # ID 400 is usually a live card?
    # Let's find a valid live card ID.
    live_ids = list(state.live_db.keys())
    valid_live = live_ids[0]
    p.live_zone = [valid_live]

    print(f"Initial Phase: {state.phase.name} ({state.phase.value})")
    print(f"Current Player: {state.current_player}")
    print(f"Live Zone: {p.live_zone}")

    # Step 0 repeatedly
    for i in range(20):
        print(f"\n--- Step {i} ---")
        print(f"Phase: {state.phase.name} ({state.phase.value})")
        if state.pending_choices:
            print(f"Pending Choices: {state.pending_choices[0]}")

        mask = state.get_legal_actions()
        print(f"Legal Actions Mask[0]: {mask[0]}")

        if mask[0]:
            print("Executing Action 0...")
            state = state.step(0)

            # Check if we are stuck in Phase 7
            if state.phase == Phase.PERFORMANCE_P2 and i > 5:
                print("STUCK IN PERFORMANCE_P2!")
        else:
            print("Action 0 not legal. Choosing random legal action...")
            # Pick first legal
            legal_indices = np.where(mask)[0]
            if len(legal_indices) > 0:
                action = legal_indices[0]
                print(f"Executing Action {action}...")
                state = state.step(action)
            else:
                print("No legal actions!")
                break


if __name__ == "__main__":
    detailed_debug()
