import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from ai.network import NeuralMCTS
from ai.network_torch import TorchNetworkWrapper
from ai.train import NetworkConfig


def generate_nn_replay(model_path=None, simulations=20, live=False, deck_type="normal"):
    print(f"Initializing Neural Replay Generation (Live: {live}, Deck: {deck_type})...")

    # 1. Setup Network and MCTS
    config = NetworkConfig()
    network = TorchNetworkWrapper(config)

    if model_path and os.path.exists(model_path):
        print(f"Loading model from {model_path}...")
        network.load(model_path)
    else:
        print("Using uninitialized network (Random baseline)...")

    mcts = NeuralMCTS(network, num_simulations=simulations)

    # 2. Initialize Game
    print("Setting up game environment...")
    server.init_game(deck_type=deck_type)

    replay_data = {
        "game_id": int(time.time()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "winner": None,
        "states": [],
    }

    max_moves = 500
    move_count = 0

    print("Running Neural vs Neural Match...")

    last_state_hash = None
    stuck_count = 0
    last_sync_time = 0

    while not server.game_state.is_terminal() and move_count < max_moves:
        # Capture current serialized state for UI
        state_snapshot = server.serialize_state()

        # 1. Get Legal Actions
        legal_mask = server.game_state.get_legal_actions()

        # 2. Get MCTS policy
        raw_policy = mcts.search(server.game_state)

        # 3. Policy Masking (Apply mask and re-normalize)
        masked_policy = raw_policy * legal_mask
        if np.sum(masked_policy) > 0:
            masked_policy /= np.sum(masked_policy)
        else:
            # Fallback: uniform over legal actions
            masked_policy = legal_mask / np.sum(legal_mask)

        # 3b. Apply Dirichlet Noise (Exploration)
        if args.noise > 0 and move_count < 30:  # Only add noise in opening
            legal_indices = np.where(masked_policy > 0)[0]
            if len(legal_indices) > 0:
                noise = np.random.dirichlet([args.noise] * len(legal_indices))
                # Mix noise into the legal probability mass
                # current mass on legal is 1.0 (since masked_policy is normalized)
                masked_policy[legal_indices] = 0.75 * masked_policy[legal_indices] + 0.25 * noise

        # 3c. Dynamic Temperature Scaling
        # policy = policy ** (1/T) / sum(policy ** (1/T))
        p0_score = len(server.game_state.players[0].success_lives)
        p1_score = len(server.game_state.players[1].success_lives)

        # User Policy: Low temp when point is scored ("Serious Mode")
        if p0_score > 0 or p1_score > 0:
            current_temp = 0.1
        elif move_count < args.temp_steps:
            current_temp = args.temp
        else:
            current_temp = 0.1  # Default low temp for mid/endgame

        if current_temp == 0:
            # Greedy
            pass  # Logic falls through to greedy/non-skip below which effectively acts as argmax
        else:
            # Apply Temperature
            # Logits -> Softmax with Temp
            # Since we have probs, we can approximate: p_i = p_i^(1/T) / sum(...)
            masked_policy = np.power(masked_policy, 1.0 / current_temp)
            masked_policy /= np.sum(masked_policy)

        # 4. Action Selection
        if current_temp > 0.1:  # High randomness selection
            action = int(np.random.choice(len(masked_policy), p=masked_policy))
        else:
            # Low temp/Greedy Selection (Prefer non-skip actions logic)
            # Get sorted indices by probability (descending)
            sorted_indices = np.argsort(masked_policy)[::-1]

            # Find best non-skip action
            legal_non_skip = [i for i in sorted_indices if i != 0 and masked_policy[i] > 0]

            if legal_non_skip:
                # Prefer non-skip actions
                action = int(legal_non_skip[0])
            elif masked_policy[0] > 0:
                # Only skip if it's the only legal action
                action = 0
            else:
                # Fallback to any legal action
                action = int(sorted_indices[0])

        # Log top 3 for transparency
        # If we sampled, we should verify "action" is in top 3 logic or adjust logging?
        # Let's verify what we picked against the policy

        # Re-sort based on adjusted policy for display
        sorted_indices = np.argsort(masked_policy)[::-1]
        top_indices = sorted_indices[:3]
        top_details = ", ".join([f"A{idx}: {masked_policy[idx]:.2f}" for idx in top_indices if masked_policy[idx] > 0])

        # Record action in snapshot
        state_snapshot["action_taken"] = action
        state_snapshot["p0_agent"] = f"NeuralMCTS (T={current_temp})"
        state_snapshot["p1_agent"] = f"NeuralMCTS (T={current_temp})"

        # Optimize: Serialize ONCE per loop
        serialized_state = server.make_serializable(state_snapshot)

        # Add to replay
        replay_data["states"].append(serialized_state)

        # API Sync if live (Async + Throttled)
        current_time = time.time()
        if live and current_time - last_sync_time > 0.1:  # Max 10 updates per second
            import threading

            import requests

            def sync_thread(data):
                try:
                    requests.post("http://localhost:5000/api/sync_state", json=data, timeout=0.1)
                except:
                    pass

            # Fire and forget
            threading.Thread(target=sync_thread, args=(serialized_state,), daemon=True).start()
            last_sync_time = current_time

        # Stuck Detection
        state_str = json.dumps(serialized_state, sort_keys=True)
        if last_state_hash == state_str:
            stuck_count += 1
            if stuck_count > 3:
                # Force a different legal action if stuck
                legal_indices = np.where(legal_mask)[0]
                action = int(np.random.choice(legal_indices))
                print(f"\nSTUCK DETECTED (Phase {server.game_state.phase.name}). Forcing random action {action}")
                stuck_count = 0
        else:
            stuck_count = 0
        last_state_hash = state_str

        server.game_state = server.game_state.step(action)

        # Get state info
        p0_score = len(server.game_state.players[0].success_lives)
        p1_score = len(server.game_state.players[1].success_lives)
        p0_deck = len(server.game_state.players[0].main_deck)
        p1_deck = len(server.game_state.players[1].main_deck)

        print(
            f"Move {move_count}: Phase {server.game_state.phase.name}, Score: {p0_score}-{p1_score}, Decks: {p0_deck}/{p1_deck}, Top: [{top_details}]",
            end="\r",
        )
        move_count += 1

        # Removed sleep for max speed

    # Capture final terminal state
    final_snapshot = server.serialize_state()
    final_snapshot["action_taken"] = -1

    if live:
        try:
            import requests

            requests.post(
                "http://localhost:5000/api/sync_state", json=server.make_serializable(final_snapshot), timeout=1
            )
        except:
            pass

    replay_data["states"].append(server.make_serializable(final_snapshot))

    winner = server.game_state.get_winner()
    replay_data["winner"] = int(winner)

    # Final Scores
    f_p0_score = len(server.game_state.players[0].success_lives)
    f_p1_score = len(server.game_state.players[1].success_lives)

    # Save to file
    out_dir = Path("replays")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"nn_replay_{time.strftime('%Y%m%d_%H%M%S')}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(replay_data, f, ensure_ascii=False)

    print(f"\nMatch complete in {move_count} moves.")
    print(f"Final Score: P0: {f_p0_score}, P1: {f_p1_score}")

    # Log Reward
    p0_reward = server.game_state.get_reward(0)
    print(f"Final Reward (P0): {p0_reward}")
    replay_data["final_reward_p0"] = p0_reward

    print(f"Winner: Player {winner}")
    print(f"Replay saved to: {out_file}")

    return str(out_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Enable live sync to web UI")
    parser.add_argument("--simulations", type=int, default=50, help="Number of MCTS simulations")

    # Exploration parameters
    parser.add_argument("--noise", type=float, default=0.3, help="Dirichlet noise alpha (0 to disable)")
    parser.add_argument("--temp", type=float, default=1.0, help="Initial temperature")
    parser.add_argument("--temp-steps", type=int, default=30, help="Number of steps to keep initial temperature")

    # Deck configuration
    parser.add_argument("--deck-type", type=str, default="normal", help="Deck type: normal, vanilla, easy")

    args = parser.parse_args()

    # Look for the latest checkpoint
    checkpoint_dir = Path("checkpoints")
    latest_model = None
    if checkpoint_dir.exists():
        models = sorted(list(checkpoint_dir.glob("model_iter*.pt")))
        if models:
            latest_model = str(models[-1])

    generate_nn_replay(model_path=latest_model, simulations=args.simulations, live=args.live, deck_type=args.deck_type)
