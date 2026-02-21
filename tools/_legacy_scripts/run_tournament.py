import json
import os
import random
import sys
from datetime import datetime

import numpy as np

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from game.network import NetworkConfig, SimpleNetwork

# --- AGENTS ---


class Agent:
    def choose_action(self, state: GameState, player_id: int) -> int:
        raise NotImplementedError


class RandomAgent(Agent):
    def choose_action(self, state: GameState, player_id: int) -> int:
        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if len(legal_indices) == 0:
            return 0
        return int(np.random.choice(legal_indices))


class NumpyRLAgent(Agent):
    """Reinforcement Learning Agent using pure Numpy neural network"""

    def __init__(self, load_path=None):
        self.config = NetworkConfig()
        self.net = SimpleNetwork(self.config)
        if load_path and os.path.exists(load_path):
            print(f"Loading RL Model from {load_path}")
            self.net.load(load_path)
        else:
            print("Initialized RL Agent with random weights (Untrained)")

    def choose_action(self, state: GameState, player_id: int) -> int:
        policy, value = self.net.predict(state)

        # Policy is already masked by get_legal_actions inside predict()
        # But let's double check legal mask to be safe against floating point errors
        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]

        if len(legal_indices) == 0:
            return 0

        # Re-normalize policy over strictly legal actions
        p_legal = policy[legal_indices]
        if p_legal.sum() > 0:
            p_legal /= p_legal.sum()
            return int(np.random.choice(legal_indices, p=p_legal))
        else:
            return int(np.random.choice(legal_indices))


class SmartHeuristicAgent(Agent):
    """Simple rule-based agent for baseline"""

    def choose_action(self, state: GameState, player_id: int) -> int:
        legal_mask = state.get_legal_actions()
        indices = np.where(legal_mask)[0]
        if len(indices) == 0:
            return 0

        # 1. Play Members (1-180)
        plays = [i for i in indices if 1 <= i <= 180]
        if plays and state.phase == Phase.MAIN:
            # Randomly pick a play 80% of time
            if random.random() < 0.8:
                return int(np.random.choice(plays))

        # 2. Live Set (400+) - Simply pick one if available
        lives = [i for i in indices if i >= 400]
        if lives and state.phase == Phase.LIVE_SET:
            return int(np.random.choice(lives))

        return int(np.random.choice(indices))


# --- TOURNAMENT ENGINE ---

from game.network import train_network

# --- TRAINING HELPERS ---


def one_hot(action, size):
    v = np.zeros(size)
    v[action] = 1.0
    return v


def run_self_play_game(agent, deck_ids, db_m, db_l, db_e, game_idx, save_replay_dir=None):
    """Run a single game of Agent vs Agent (Self-Play) and return training data"""
    gs = GameState()

    # Setup Decks (Same logic as tournament)
    main_d = []
    energy_d = []
    for cid in deck_ids:
        if cid in db_m or cid in db_l:
            main_d.append(cid)
        elif cid in db_e:
            energy_d.append(cid)
    if len(energy_d) < 10:
        energy_d.extend([2000] * (10 - len(energy_d)))  # Safety

    for p in gs.players:
        p.main_deck = list(main_d)
        p.energy_deck = list(energy_d)
        random.shuffle(p.main_deck)
        p.hand = []
        p.energy_zone = []
        p.discard = []
        p.stage = np.full(3, -1, dtype=np.int32)

    # Manual Setup (Draw 5, Energy 3)
    for _ in range(5):
        if gs.players[0].main_deck:
            gs.players[0].hand.append(gs.players[0].main_deck.pop())
        if gs.players[1].main_deck:
            gs.players[1].hand.append(gs.players[1].main_deck.pop())
    for _ in range(3):
        if gs.players[0].energy_deck:
            gs.players[0].energy_zone.append(gs.players[0].energy_deck.pop(0))
        if gs.players[1].energy_deck:
            gs.players[1].energy_zone.append(gs.players[1].energy_deck.pop(0))

    gs.phase = Phase.MULLIGAN_P1
    gs.current_player = 0
    gs.first_player = random.randint(0, 1)

    # Initial Random Seed for this Game
    current_game_seed = random.randint(0, 999999)
    random.seed(current_game_seed)
    np.random.seed(current_game_seed)

    states = []
    policies = []
    action_log = []

    max_turns = 150
    winner = -1

    while not gs.game_over and gs.turn_number < max_turns:
        gs.check_win_condition()
        if gs.game_over:
            break

        pid = gs.current_player

        # Record State
        obs = gs.get_observation()  # This is from perspective of current_player
        states.append(obs)

        # Choose Action
        action = agent.choose_action(gs, pid)
        action_log.append(action)

        # Record Policy (Hard Target: The action we chose)
        # Ideally this would be MCTS distribution, but for direct RL we reinforce "winning moves" later
        pol = one_hot(action, agent.config.action_size)
        policies.append(pol)

        gs = gs.step(action)

    if gs.game_over:
        winner = gs.winner
    else:
        winner = 2  # Draw

    # Save Replay if requested
    if save_replay_dir:
        deck_info = {"p0_deck": deck_ids, "p1_deck": deck_ids}
        replay_data = {
            "level": 3,
            "seed": current_game_seed,
            "decks": deck_info,
            "action_log": action_log,
            "timestamp": datetime.now().isoformat(),
            "p0_name": "NumpyRL",
            "p1_name": "NumpyRL",
            "winner": winner,
        }
        fname = os.path.join(save_replay_dir, f"train_gen_{game_idx}_winner_P{winner}.json")
        with open(fname, "w") as f:
            json.dump(replay_data, f)

    return (states, policies, winner)


def run_benchmark_game(agent_p0, agent_p1, p0_name, p1_name, deck_ids, db_m, db_l, db_e, game_idx, save_dir):
    """Run a single benchmark game and return winner"""
    gs = GameState()
    # ... Setup Logic (Duplicated for brevity, ideally helper) ...
    main_d = []
    energy_d = []
    for cid in deck_ids:
        if cid in db_m or cid in db_l:
            main_d.append(cid)
        elif cid in db_e:
            energy_d.append(cid)
    if len(energy_d) < 10:
        energy_d.extend([2000] * (10 - len(energy_d)))

    for p in gs.players:
        p.main_deck = list(main_d)
        p.energy_deck = list(energy_d)
        random.shuffle(p.main_deck)
        # Reset other zones
        p.hand = []
        p.energy_zone = []
        p.discard = []
        p.stage = np.full(3, -1, dtype=np.int32)

    for _ in range(5):
        if gs.players[0].main_deck:
            gs.players[0].hand.append(gs.players[0].main_deck.pop())
        if gs.players[1].main_deck:
            gs.players[1].hand.append(gs.players[1].main_deck.pop())
    for _ in range(3):
        if gs.players[0].energy_deck:
            gs.players[0].energy_zone.append(gs.players[0].energy_deck.pop(0))
        if gs.players[1].energy_deck:
            gs.players[1].energy_zone.append(gs.players[1].energy_deck.pop(0))

    gs.phase = Phase.MULLIGAN_P1
    gs.current_player = 0
    gs.first_player = random.randint(0, 1)

    seed = random.randint(0, 999999)
    random.seed(seed)
    np.random.seed(seed)

    action_log = []
    max_turns = 200

    while not gs.game_over and gs.turn_number < max_turns:
        gs.check_win_condition()
        if gs.game_over:
            break

        pid = gs.current_player
        agent = agent_p0 if pid == 0 else agent_p1
        action = agent.choose_action(gs, pid)
        action_log.append(action)
        gs = gs.step(action)

    winner = gs.winner if gs.game_over else 2

    deck_info = {"p0_deck": deck_ids, "p1_deck": deck_ids}
    replay_data = {
        "level": 3,
        "seed": seed,
        "decks": deck_info,
        "action_log": action_log,
        "timestamp": datetime.now().isoformat(),
        "p0_name": p0_name,
        "p1_name": p1_name,
        "winner": winner,
    }
    fname = os.path.join(save_dir, f"bench_{game_idx}_{p0_name}_vs_{p1_name}.json")
    with open(fname, "w") as f:
        json.dump(replay_data, f)

    return winner


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--train_games", type=int, default=50, help="Number of self-play games per epoch")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--bench_games", type=int, default=10, help="Number of benchmark games vs Baseline")
    parser.add_argument("--baseline", type=str, default="Smart", help="Baseline agent (Smart/Random)")
    args = parser.parse_args()

    # 1. Setup Directories
    REPLAY_DIR = os.path.join(os.path.dirname(__file__), "..", "replays", "tournament")
    if not os.path.exists(REPLAY_DIR):
        os.makedirs(REPLAY_DIR)

    # 2. Load Resources
    DECK_FILE = os.path.join(os.path.dirname(__file__), "..", "tests", "deck_ids.json")
    with open(DECK_FILE, "r") as f:
        deck_ids = json.load(f)

    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()
    GameState.member_db = m
    GameState.live_db = l

    # 3. Agents
    rl_agent = NumpyRLAgent()  # The STAR
    baseline_agent = SmartHeuristicAgent() if args.baseline == "Smart" else RandomAgent()

    print(f"=== STARTING TRAINING LOOP ({args.epochs} Epochs x {args.train_games} Games) ===")

    for epoch in range(args.epochs):
        print(f"\n--- Epoch {epoch + 1}/{args.epochs} ---")

        # A. Self-Play Data Collection
        print(f"Self-Playing {args.train_games} games...")
        training_batch = []
        p0_wins = 0
        p1_wins = 0
        draws = 0

        for i in range(args.train_games):
            # Save every 10th replay
            save_dir = REPLAY_DIR if i % 10 == 0 else None
            result = run_self_play_game(rl_agent, deck_ids, m, l, e, (epoch * args.train_games) + i, save_dir)

            states, policies, winner = result
            training_batch.append(result)

            if winner == 0:
                p0_wins += 1
            elif winner == 1:
                p1_wins += 1
            else:
                draws += 1

        print(f"  Results: P0:{p0_wins} P1:{p1_wins} Draw:{draws}")

        # B. Train
        print("Training Network...")
        train_network(rl_agent.net, training_batch, epochs=1)  # 1 internal epoch per batch of games

        # C. Benchmark
        print(f"Benchmarking vs {args.baseline} ({args.bench_games} games)...")
        rl_wins = 0

        for i in range(args.bench_games):
            # Alternate P0/P1 to be fair
            if i % 2 == 0:
                # RL is P0
                w = run_benchmark_game(
                    rl_agent,
                    baseline_agent,
                    "NumpyRL",
                    args.baseline,
                    deck_ids,
                    m,
                    l,
                    e,
                    (epoch * args.bench_games) + i,
                    REPLAY_DIR,
                )
                if w == 0:
                    rl_wins += 1
            else:
                # RL is P1
                w = run_benchmark_game(
                    baseline_agent,
                    rl_agent,
                    args.baseline,
                    "NumpyRL",
                    deck_ids,
                    m,
                    l,
                    e,
                    (epoch * args.bench_games) + i,
                    REPLAY_DIR,
                )
                if w == 1:
                    rl_wins += 1

        print(
            f"  RL Win Rate vs {args.baseline}: {rl_wins}/{args.bench_games} ({(rl_wins / args.bench_games) * 100:.1f}%)"
        )

    print("\nTraining Complete.")


if __name__ == "__main__":
    main()
