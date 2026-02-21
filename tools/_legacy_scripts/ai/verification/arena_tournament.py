import argparse
import json
import multiprocessing as mp
import os
import random
import sys
import time

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.obs_adapters import UnifiedObservationEncoder

from ai.headless_runner import Agent, RandomAgent, SmartHeuristicAgent, TrueRandomAgent
from engine.game.game_state import GameState, Phase, initialize_game


class PPOAgent(Agent):
    def __init__(self, model_path, device="cpu"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        self.model_path = model_path
        self.device = device
        self.model = None
        self.obs_dim = None
        self.maskable = None

        # Load once to get metadata
        self._ensure_loaded()

    def _ensure_loaded(self):
        if self.model is not None:
            return

        try:
            from sb3_contrib import MaskablePPO

            self.model = MaskablePPO.load(self.model_path, device=self.device)
            self.maskable = True
        except Exception:
            try:
                from stable_baselines3 import PPO

                self.model = PPO.load(self.model_path, device=self.device)
                self.maskable = False
            except Exception as e:
                raise ValueError(f"Failed to load model at {self.model_path}: {e}")

        self.obs_dim = self.model.observation_space.shape[0]

    def choose_action(self, state, player_id):
        self._ensure_loaded()
        # Use Unified Encoder to get the right observation dimension (1D vector)
        obs = UnifiedObservationEncoder.encode(state, self.obs_dim, player_id)

        # SB3 predict expects [batch_size, obs_dim]
        obs_batch = obs.reshape(1, -1)

        # --- ACTION MASK ADAPTER ---
        # The Model expects specific masks based on Card IDs (VectorEnv logic).
        # The GameState provides masks based on Slot IDs.
        # We must construct a 'Vector-Style' mask for the model to predict correctly.

        # Re-implement vector_env.compute_action_masks logic locally for single instance
        model_action_mask = np.zeros(2000, dtype=bool)
        model_action_mask[0] = True  # Pass

        p = state.players[player_id]
        # Allow playing any card in hand (that is technically valid)
        for cid in p.hand:
            if cid > 0 and cid < 2000:
                model_action_mask[cid] = True

        try:
            if self.maskable:
                # Use our constructed mask, not state.get_legal_actions()
                action_masks = model_action_mask.reshape(1, -1)
                action, _states = self.model.predict(obs_batch, action_masks=action_masks, deterministic=True)
            else:
                action, _states = self.model.predict(obs_batch, deterministic=True)

            raw_action = int(action[0])

            # --- ACTION TRANSLATOR ---
            # Map Model's Card ID -> GameState's Slot Action
            final_action = raw_action

            if raw_action == 0:
                return 0

            # If action corresponds to a card in hand
            if raw_action in p.hand:
                hand_idx = p.hand.index(raw_action)

                # Check Phase to determine Slot Action
                if state.phase.name == "MAIN":  # Phase.MAIN
                    # Auto-select slot (0, 1, 2)
                    # Simple heuristic: First empty, or 0 if all full (baton touch not guaranteed)
                    target_slot = 0
                    if p.stage[0] == -1:
                        target_slot = 0
                    elif p.stage[1] == -1:
                        target_slot = 1
                    elif p.stage[2] == -1:
                        target_slot = 2
                    else:
                        # Logic to replace? Just pick 0 for now.
                        target_slot = 0

                    # Calculate Slot Action ID
                    # Formula from GameState: 1 + i * 3 + area
                    final_action = 1 + (hand_idx * 3) + target_slot

                elif state.phase.name == "LIVE_SET":  # Phase.LIVE_SET
                    # Formula: 400 + i
                    final_action = 400 + hand_idx

            # For Performance Phase, GameState handles it automatically, so if Model outputs Live ID,
            # we effectively map it to 0 (Pass) because GameState expects 0 to advance.
            if state.phase.name.startswith("PERFORMANCE"):
                final_action = 0

            # print(f" [Adapter] Model: {raw_action} -> GameState: {final_action} (Phase: {state.phase})")
            return final_action

        except Exception as e:
            import traceback

            error_msg = f"Match Prediction Error:\n{traceback.format_exc()}\nObs Shape: {obs_batch.shape}\n"
            if self.maskable:
                error_msg += f"Mask Shape: {action_masks.shape}\n"

            with open("tournament_errors.txt", "a", encoding="utf-8") as err_f:
                err_f.write(error_msg + "-" * 40 + "\n")

            raise e


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
        # Fallback to easy cards if pool is empty
        member_pool = [888]
        live_pool = [999]

    selected_members = list(np.random.choice(member_pool, 48, replace=True))
    selected_lives = list(np.random.choice(live_pool, 12, replace=True))

    deck = selected_members + selected_lives
    random.shuffle(deck)
    return deck


# Global cache for agents in worker processes to avoid pickling issues
_worker_agent_cache = {}


def get_cached_agent(name, config):
    global _worker_agent_cache
    if name in _worker_agent_cache:
        return _worker_agent_cache[name]

    if config["type"] == "PPO":
        agent = PPOAgent(config["path"], device="cpu")
    elif config["type"] == "SmartHeuristic":
        agent = SmartHeuristicAgent()
    elif config["type"] == "Random":
        agent = RandomAgent()
    elif config["type"] == "TrueRandom":
        agent = TrueRandomAgent()
    else:
        raise ValueError(f"Unknown agent type for {name}")

    _worker_agent_cache[name] = agent
    return agent


def run_match_worker(match_params):
    """Worker function for parallel matches."""
    p0_name, p1_name, agents_config, verified_members, verified_lives, max_turns, seed = match_params

    # Set seed for reproducibility within this match
    random.seed(seed)
    np.random.seed(seed)

    # Initialize game for this process
    initialize_game(deck_type="random_verified")

    # Use cached agents to avoid pickling/loading overhead
    p0_agent = get_cached_agent(p0_name, agents_config[p0_name])
    p1_agent = get_cached_agent(p1_name, agents_config[p1_name])

    agents = [p0_agent, p1_agent]

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
    state.phase = Phase.MAIN  # Skip Mulligan for better PPO evaluation

    while not state.game_over and state.turn_number <= max_turns:
        current_agent = agents[state.current_player]
        action = current_agent.choose_action(state, state.current_player)
        print(
            f" [DEBUG] T:{state.turn_number} P:{state.current_player} ({p0_name if state.current_player == 0 else p1_name}) chose: {action}"
        )
        state = state.step(action)
        state.check_win_condition()

    return {
        "p0_name": p0_name,
        "p1_name": p1_name,
        "p0_score": len(state.players[0].success_lives),
        "p1_score": len(state.players[1].success_lives),
        "winner": state.winner,
        "turns": state.turn_number,
    }


def run_tournament(args):
    print("Initializing Tournament...")
    # Initialize once to get card DBs for pairing logic
    initialize_game(deck_type="random_verified")
    verified_members, verified_lives = load_verified_pool()

    # Define participants and their types/paths
    agents_config = {
        "SmartHeuristic": {"type": "SmartHeuristic"},
        "Random": {"type": "Random"},
    }

    # Auto-detect latest PPO model
    vector_dir = "checkpoints/vector"
    latest_model = None
    if os.path.exists(vector_dir):
        # Find newest zip file based on modification time
        files = [os.path.join(vector_dir, f) for f in os.listdir(vector_dir) if f.endswith(".zip")]
        if files:
            latest_model = max(files, key=os.path.getmtime)
            print(
                f" [Tournament] Auto-detected latest model: {latest_model} (Modified: {time.ctime(os.path.getmtime(latest_model))})"
            )

    if latest_model:
        print(f" [Tournament] Auto-detected latest model: {latest_model}")
        agents_config["Latest_PPO"] = {"type": "PPO", "path": latest_model}

    # Filter only existing paths for PPO
    final_config = {}
    for name, config in agents_config.items():
        if config["type"] == "PPO":
            if os.path.exists(config["path"]):
                final_config[name] = config
            else:
                print(f"Warning: Model not found for {name} at {config['path']}, skipping.")
        else:
            final_config[name] = config

    agent_names = list(final_config.keys())
    pairings = []
    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            pairings.append((agent_names[i], agent_names[j]))

    total_matches = len(pairings) * args.num_games
    print(f"Tournament: {len(agent_names)} agents, {len(pairings)} pairings, {args.num_games} games/pairing.")
    print(f"Total Matches: {total_matches}")

    # Build match queue
    match_queue = []
    for p0_name, p1_name in pairings:
        for i in range(args.num_games):
            seed = random.randint(0, 1000000)
            match_queue.append((p0_name, p1_name, final_config, verified_members, verified_lives, args.max_turns, seed))

    print(f"Starting {args.parallel} parallel workers...")

    start_time = time.time()
    results = {name: {"wins": 0, "losses": 0, "draws": 0, "total_score": 0, "games": 0} for name in final_config}

    if args.parallel == 1:
        print("Running synchronously (Single Process) for debugging...")
        for i, match_params in enumerate(match_queue):
            try:
                match_res = run_match_worker(match_params)
                p0 = match_res["p0_name"]
                p1 = match_res["p1_name"]

                results[p0]["games"] += 1
                results[p1]["games"] += 1
                results[p0]["total_score"] += match_res["p0_score"]
                results[p1]["total_score"] += match_res["p1_score"]

                if match_res["winner"] == 0:
                    results[p0]["wins"] += 1
                    results[p1]["losses"] += 1
                elif match_res["winner"] == 1:
                    results[p1]["wins"] += 1
                    results[p0]["losses"] += 1
                else:
                    results[p0]["draws"] += 1
                    results[p1]["draws"] += 1

                if (i + 1) % 1 == 0:
                    print(f"Match {i + 1}/{total_matches} done.")

            except Exception as e:
                print(f"Match {i + 1} FAILED: {e}")
                import traceback

                traceback.print_exc()

    else:
        with mp.Pool(processes=args.parallel) as pool:
            # Use imap_unordered for progress tracking
            completed = 0
            for match_res in pool.imap_unordered(run_match_worker, match_queue):
                completed += 1
                p0 = match_res["p0_name"]
                p1 = match_res["p1_name"]

                results[p0]["games"] += 1
                results[p1]["games"] += 1
                results[p0]["total_score"] += match_res["p0_score"]
                results[p1]["total_score"] += match_res["p1_score"]

                if match_res["winner"] == 0:
                    results[p0]["wins"] += 1
                    results[p1]["losses"] += 1
                elif match_res["winner"] == 1:
                    results[p1]["wins"] += 1
                    results[p0]["losses"] += 1
                else:
                    results[p0]["draws"] += 1
                    results[p1]["draws"] += 1

                if completed % 10 == 0 or completed == total_matches:
                    elapsed = time.time() - start_time
                    fps = completed / elapsed
                    print(f"Progress: {completed}/{total_matches} matches done ({fps:.1f} matches/sec)")

    # Summary Table
    summary_lines = []
    summary_lines.append("\n" + "=" * 80)
    summary_lines.append(
        f"{'AGENT':<20} | {'WINS':<6} | {'LOSSES':<6} | {'DRAWS':<6} | {'WIN RATE':<10} | {'AVG SCORE':<10}"
    )
    summary_lines.append("-" * 80)

    # Sort agents by win rate
    sorted_agents = sorted(
        results.keys(),
        key=lambda x: (results[x]["wins"] / results[x]["games"]) if results[x]["games"] > 0 else 0,
        reverse=True,
    )

    for name in sorted_agents:
        data = results[name]
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
    # Windows Multiprocessing Support
    mp.set_start_method("spawn", force=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--num-games", type=int, default=20, help="Games per pairing")
    parser.add_argument("--max-turns", type=int, default=100)
    parser.add_argument("--parallel", type=int, default=os.cpu_count(), help="Number of parallel matches")
    parser.add_argument(
        "--output", type=str, default="benchmarks/tournament_results_formatted.md", help="Path to save summary results"
    )
    args = parser.parse_args()

    run_tournament(args)
