import os
import random
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pr_server
from pr_server import init_game, serialize_state

from engine.game.game_state import Phase


def generate_large_replay():
    print("Initializing game for large replay generation...")
    init_game(deck_type="normal")

    # Simulate many turns to generate a large history
    max_turns = 20
    print(f"Simulating up to {max_turns} turns...")

    turn_count = 0
    actions = 0

    while not pr_server.game_state.game_over and turn_count < max_turns:
        # Simple random actions
        mask = pr_server.game_state.get_legal_actions()
        legal_indices = [i for i, v in enumerate(mask) if v]

        if not legal_indices:
            print("No legal actions, ending simulation.")
            break

        action = random.choice(legal_indices)
        pr_server.game_state.step(action)
        actions += 1

        # Append state to history
        pr_server.game_history.append(serialize_state())

        if pr_server.game_state.phase == Phase.ACTIVE:
            turn_count += 1
            if turn_count % 10 == 0:
                print(f"Reached Turn {turn_count} (Actions: {actions})")

    print(f"Simulation finished. Total Actions: {len(pr_server.game_history)}")

    print(f"Simulation finished. Total Actions: {len(pr_server.game_history)}")

    # Use server's save_replay to trigger auto-optimization (Level 3 if possible)
    from pr_server import save_replay

    save_replay()

    print("Replay saved via pr_server (check replays/ folder for _opt.json)")


if __name__ == "__main__":
    generate_large_replay()
