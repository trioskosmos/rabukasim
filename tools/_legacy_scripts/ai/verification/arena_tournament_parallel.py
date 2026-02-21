import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from sb3_contrib import MaskablePPO

from ai.headless_runner import Agent, RandomAgent, SmartHeuristicAgent, TrueRandomAgent
from engine.game.game_state import GameState, Phase, initialize_game

# Global storage for PPO model in child processes
_ppo_model = None


class PPOAgent(Agent):
    def __init__(self, model_path, device="cpu"):  # Default to CPU for wide parallelization
        self.model_path = model_path
        self.device = device

    def choose_action(self, state, player_id):
        global _ppo_model
        if _ppo_model is None:
            # Lazy load in child process
            print(f"[{os.getpid()}] Loading PPO model from {self.model_path}...")
            _ppo_model = MaskablePPO.load(self.model_path, device=self.device)

        obs = state.get_observation()
        action_masks = state.get_legal_actions().astype(bool)
        action, _states = _ppo_model.predict(obs, action_masks=action_masks, deterministic=True)
        return int(action)


def load_verified_pool():
    pool_path = os.path.join(os.getcwd(), "verified_card_pool.json")
    if not os.path.exists(pool_path):
        raise FileNotFoundError("verified_card_pool.json not found")

    with open(pool_path, "r", encoding="utf-8") as f:
        pool = json.load(f)

    return pool.get("verified_abilities", []), pool.get("vanilla_lives", [])


def create_mirror_deck(verified_members, verified_lives, member_db, live_db):
    member_pool = []
    for cid, card in member_db.items():
        if card.card_no in verified_members:
            member_pool.append(cid)

    live_pool = []
    for cid, card in live_db.items():
        if card.card_no in verified_lives:
            live_pool.append(cid)

    if not member_pool or not live_pool:
        raise ValueError("Verified card pool is empty after matching with DB")

    selected_members = list(np.random.choice(member_pool, 48, replace=True))
    selected_lives = list(np.random.choice(live_pool, 12, replace=True))

    deck = selected_members + selected_lives
    random.shuffle(deck)
    return deck


def run_match_worker(args):
    """Worker function for parallel execution"""
    agent0_type, agent1_type, model_path, verified_members, verified_lives, max_turns, seed = args

    # Random seed for this worker/game
    random.seed(seed)
    np.random.seed(seed)

    # Initialize game data in this process
    initialize_game(deck_type="random_verified")

    # Instantiate agents
    def create_agent(agent_type):
        if agent_type == "PPO":
            return PPOAgent(model_path)
        if agent_type == "SmartHeuristic":
            return SmartHeuristicAgent()
        if agent_type == "HeuristicRandom":
            return RandomAgent()
        if agent_type == "TrueRandom":
            return TrueRandomAgent()
        return None

    agent0 = create_agent(agent_type0)  # Wait, bug in my thought, fixed below


def run_match_wrapper(p):
    # Unpack parameters
    agent0_name, agent1_name, model_path, verified_members, verified_lives, max_turns, seed = p

    # Re-initialize game data for this process
    initialize_game(deck_type="random_verified")

    # Local agent creation
    def get_agent(name):
        if name == "PPO":
            return PPOAgent(model_path)
        if name == "SmartHeuristic":
            return SmartHeuristicAgent()
        if name == "HeuristicRandom":
            return RandomAgent()
        if name == "TrueRandom":
            return TrueRandomAgent()
        return None

    a0 = get_agent(agent0_name)
    a1 = get_agent(agent1_name)

    state = GameState()
    mirror_deck = create_mirror_deck(verified_members, verified_lives, GameState.member_db, GameState.live_db)

    for p in state.players:
        p.main_deck = list(mirror_deck)
        p.energy_deck = [200] * 12
        p.hand = [p.main_deck.pop() for _ in range(5)]
        p.energy_zone = [p.energy_deck.pop() for _ in range(3)]

    first_player = random.randint(0, 1)
    state.first_player = first_player
    state.current_player = first_player
    state.phase = Phase.MULLIGAN_P1 if first_player == 0 else Phase.MULLIGAN_P2

    agents = [a0, a1]

    while not state.game_over and state.turn_number <= max_turns:
        current_agent = agents[state.current_player]
        action = current_agent.choose_action(state, state.current_player)
        state = state.step(action)
        state.check_win_condition()

    return {
        "winner": state.winner,
        "p0_score": len(state.players[0].success_lives),
        "p1_score": len(state.players[1].success_lives),
        "turns": state.turn_number,
    }


def run_tournament(args):
    print("Initializing Tournament (Parallel)...")
    verified_members, verified_lives = load_verified_pool()

    agent_names = ["PPO", "SmartHeuristic", "HeuristicRandom", "TrueRandom"]
    pairings = []
    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            pairings.append((agent_names[i], agent_names[j]))

    results = {name: {"wins": 0, "losses": 0, "draws": 0, "total_score": 0, "games": 0} for name in agent_names}

    total_matchups = len(pairings)
    print(f"Total Matchups: {total_matchups}")
    print(f"Games per Matchup: {args.num_games}")
    print(f"Total Games: {total_matchups * args.num_games}")
    print(f"Workers: {args.workers}")

    # Prepare all game tasks
    tasks = []
    for p0_name, p1_name in pairings:
        for i in range(args.num_games):
            tasks.append(
                (
                    p0_name,
                    p1_name,
                    args.model_path,
                    verified_members,
                    verified_lives,
                    args.max_turns,
                    random.randint(0, 1000000),
                )
            )

    completed_games = 0
    start_time = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(run_match_wrapper, task): task for task in tasks}

        for future in as_completed(futures):
            task_info = futures[future]
            p0_name, p1_name, _, _, _, _, _ = task_info

            try:
                res = future.result()
                p0_score = res["p0_score"]
                p1_score = res["p1_score"]
                winner = res["winner"]

                results[p0_name]["games"] += 1
                results[p1_name]["games"] += 1
                results[p0_name]["total_score"] += p0_score
                results[p1_name]["total_score"] += p1_score

                if winner == 0:
                    results[p0_name]["wins"] += 1
                    results[p1_name]["losses"] += 1
                elif winner == 1:
                    results[p1_name]["wins"] += 1
                    results[p0_name]["losses"] += 1
                else:
                    results[p0_name]["draws"] += 1
                    results[p1_name]["draws"] += 1

                completed_games += 1
                if completed_games % 10 == 0:
                    elapsed = time.time() - start_time
                    fps = completed_games / elapsed
                    print(
                        f"Progress: {completed_games}/{len(tasks)} ({(completed_games / len(tasks)) * 100:.1f}%) | FPS: {fps:.2f}",
                        end="\r",
                    )

            except Exception as e:
                print(f"Error in game {p0_name} vs {p1_name}: {e}")

    print("\n\nTournament Complete!")
    # Summary Table
    summary_lines = []
    summary_lines.append("\n" + "=" * 80)
    summary_lines.append(
        f"{'AGENT':<20} | {'WINS':<6} | {'LOSSES':<6} | {'DRAWS':<6} | {'WIN RATE':<10} | {'AVG SCORE':<10}"
    )
    summary_lines.append("-" * 80)
    for name, data in results.items():
        if data["games"] == 0:
            continue
        wr = (data["wins"] / data["games"]) * 100
        avg_s = data["total_score"] / data["games"]
        summary_lines.append(
            f"{name:<20} | {data['wins']:<6} | {data['losses']:<6} | {data['draws']:<6} | {wr:>8.1f}% | {avg_s:>10.2f}"
        )
    summary_lines.append("=" * 80)

    summary_text = "\n".join(summary_lines)
    print(summary_text)

    if args.output:
        print(f"Saving results to {args.output} (UTF-8)...")
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="checkpoints/lovelive_ppo_checkpoint_2320000_steps.zip")
    parser.add_argument("--num-games", type=int, default=20)
    parser.add_argument("--max-turns", type=int, default=100)
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    parser.add_argument("--output", type=str, help="Path to save summary results (UTF-8)")
    args = parser.parse_args()

    run_tournament(args)
