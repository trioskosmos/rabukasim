"""
Hyperparameter Search for AlphaZero Network.
Finds optimal Depth/Width by training candidates and evaluating performance.
"""

import time

import numpy as np
import torch
from game.game_state import GameState, create_sample_cards, initialize_game
from mcts import MCTS, MCTSConfig
from network import NetworkConfig  # Reuse config structure
from network_torch import TorchNetworkWrapper

# Candidates to evaluate
CANDIDATES = {
    "Small": {"hidden_size": 128, "num_layers": 3},
    "Medium": {"hidden_size": 256, "num_layers": 5},
    "Large": {"hidden_size": 512, "num_layers": 10},
}


def run_search(games_per_candidate=20, eval_games=10):
    print("Initializing Search...")

    # Init game data
    m, l = create_sample_cards()
    GameState.member_db = m
    GameState.live_db = l

    results = {}

    for name, params in CANDIDATES.items():
        print(f"\nEvaluating Candidate: {name} {params}")

        # 1. Setup Network
        dummy_game = initialize_game()
        obs_size = len(dummy_game.get_observation())

        config = NetworkConfig(
            hidden_size=params["hidden_size"],
            num_hidden_layers=params["num_layers"],
            input_size=obs_size,
            action_size=200,
            learning_rate=0.001,
        )

        try:
            wrapper = TorchNetworkWrapper(config)
        except Exception as e:
            print(f"Failed to create network for {name}: {e}")
            continue

        # 2. Generate Data (Self-Play)
        print(f"  Generating {games_per_candidate} self-play games...")
        start_t = time.time()

        training_data = []  # (state, policy, value)

        # Use simple Neural MCTS (simulations reduced for speed in search)
        from network import NeuralMCTS  # We can reuse the MCTS class logic but pass torch wrapper

        # We need to monkey-patch or adapter because NeuralMCTS expects `network.predict()`
        # My TorchNetworkWrapper has `predict()` matching the signature.
        mcts_agent = NeuralMCTS(network=wrapper, num_simulations=25)

        for _ in range(games_per_candidate):
            g = initialize_game()
            states, policies = [], []
            move_count = 0
            while not g.is_terminal() and move_count < 150:
                pol = mcts_agent.search(g)
                states.append(g.get_observation())
                policies.append(pol)
                action = np.random.choice(len(pol), p=pol)
                g = g.step(action)
                move_count += 1

            winner = g.get_winner() if g.is_terminal() else 2

            # Process game data
            for i, (s, p) in enumerate(zip(states, policies, strict=False)):
                val = 0.0
                if winner != 2:
                    val = 1.0 if (i % 2 == winner) else -1.0  # WRONG logic for player idx?
                    # winner is 0 or 1.
                    # if i%2 == 0 (Player 0 acted), and winner==0 -> +1.
                    # Correct.
                training_data.append((s, p, val))

        gen_time = time.time() - start_t
        print(f"  Gen Time: {gen_time:.1f}s")

        # 3. Train
        print("  Training...")
        # Unpack data
        all_s = np.array([x[0] for x in training_data])
        all_p = np.array([x[1] for x in training_data])
        all_v = np.array([x[2] for x in training_data])

        # 5 epochs
        final_loss = 0
        for _ep in range(5):
            # Full batch for simplicity in search
            l, pl, vl = wrapper.train_step(all_s, all_p, all_v)
            final_loss = l

        print(f"  Final Loss: {final_loss:.4f}")

        # 4. Evaluation vs Random
        print(f"  Evaluating vs Random ({eval_games} games)...")
        wins = 0
        rand_mcts = MCTS(MCTSConfig(num_simulations=10))

        for i in range(eval_games):
            g = initialize_game()
            net_player = i % 2

            while not g.is_terminal() and g.turn_number < 100:
                if g.current_player == net_player:
                    pol = mcts_agent.search(g)  # Uses updated net
                    act = np.argmax(pol)  # Deterministic for eval
                else:
                    act = rand_mcts.select_action(g)
                g = g.step(act)

            w = g.get_winner() if g.is_terminal() else 2
            if w == net_player:
                wins += 1

        print(f"  Wins: {wins}/{eval_games}")
        results[name] = {"loss": final_loss, "wins": wins, "time": gen_time}
        del wrapper  # Free GPU memory
        torch.cuda.empty_cache()

    # Report
    print("\nSearch Results:")
    print(f"{'Name':<10} | {'Loss':<8} | {'Wins':<5} | {'Time':<6}")
    print("-" * 35)
    for name, r in results.items():
        print(f"{name:<10} | {r['loss']:.4f}   | {r['wins']:<5} | {r['time']:.1f}")


if __name__ == "__main__":
    run_search()
