import os
import random
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pr_server
from pr_server import Phase, init_game, save_replay, serialize_state


def compare_compression_run():
    print("--- Running Headless Game for Compression Comparison ---")

    # 1. Init Game
    init_game(deck_type="normal")
    print(f"Game Initialized (Seed: {pr_server.current_seed})")

    # 2. Simulate Turns (Medium Game)
    max_turns = 20
    turn_count = 0
    actions = 0

    print(f"Simulating game (up to {max_turns} turns)...")

    while not pr_server.game_state.game_over and turn_count < max_turns:
        mask = pr_server.game_state.get_legal_actions()
        legal = [i for i, v in enumerate(mask) if v]

        if not legal:
            break

        # Random action
        a = random.choice(legal)

        # IMPORTANT: Log for Level 3
        pr_server.action_log.append(a)

        # Execute
        pr_server.game_state.step(a)
        actions += 1

        # Record history
        pr_server.game_history.append(serialize_state())

        if pr_server.game_state.phase == Phase.ACTIVE:
            turn_count += 1

    print(f"Simulation Complete. {actions} actions, {len(pr_server.game_history)} frames.")

    # 3. Save Replay (Triggers both Standard and Optimized save)
    # We capture stdout to parse the filenames if needed, or just look at directory
    save_replay()

    # 4. Find most recent files
    files = sorted([f for f in os.listdir("replays") if f.endswith(".json") and "replay_" in f])
    if not files:
        print("Error: No replays found.")
        return

    # Last created should be the ones
    # They come in pairs: replay_X.json and replay_X_opt.json
    # Filter by time
    full_paths = [os.path.join("replays", f) for f in files]
    full_paths.sort(key=os.path.getmtime, reverse=True)

    latest_opt = None
    latest_std = None

    for p in full_paths:
        if "_opt.json" in p and not latest_opt:
            latest_opt = p
        elif "_opt.json" not in p and not latest_std:
            latest_std = p

        if latest_opt and latest_std:
            break

    if not latest_opt or not latest_std:
        print("Could not find pair of recent replays.")
        return

    # 5. Compare
    s_std = os.path.getsize(latest_std)
    s_opt = os.path.getsize(latest_opt)

    print("\n" + "=" * 40)
    print("COMPARISON RESULTS")
    print("=" * 40)
    print(f"Standard File:  {os.path.basename(latest_std)}")
    print(f"Size:           {s_std / 1024:.2f} KB")
    print("-" * 40)
    print(f"Optimized File: {os.path.basename(latest_opt)}")
    print(f"Size:           {s_opt / 1024:.2f} KB")
    print("Level:          3 (Action Log)")
    print("=" * 40)
    print(f"SAVINGS:        {(1 - s_opt / s_std) * 100:.2f}%")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    compare_compression_run()
