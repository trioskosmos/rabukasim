import argparse
import os
import sys
import time

import numpy as np
import torch

# Fix path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def evaluate():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=str, default="checkpoints/vector/numba_ppo_6362624_steps.zip", help="Path to PPO model"
    )
    parser.add_argument(
        "--agent", type=str, default="ppo", choices=["ppo", "random", "heuristic"], help="Agent type to evaluate"
    )
    parser.add_argument(
        "--opponent",
        type=str,
        default="heuristic",
        choices=["random", "heuristic"],
        help="Opponent type (Built-in Numba)",
    )
    parser.add_argument("--episodes", type=int, default=200, help="Total episodes to collect")
    parser.add_argument("--envs", type=int, default=100, help="Number of parallel environments")
    parser.add_argument("--fair", action="store_true", help="Run 50% games with Agent going first, 50% second")
    args = parser.parse_args()

    agent_type = args.agent.lower()
    opp_type = args.opponent.lower()
    model_path = args.model
    num_envs = args.envs
    max_episodes = args.episodes

    opp_mode = 0 if opp_type == "heuristic" else 1

    opp_mode = 0 if opp_type == "heuristic" else 1

    orders_to_run = []
    if args.fair:
        print(f"--- DUAL EVALUATION MODE: {agent_type.upper()} VS {opp_type.upper()} (Switching Order) ---")
        orders_to_run.append({"order": 0, "eps": max_episodes // 2, "label": "AGENT FIRST (P1)"})
        orders_to_run.append({"order": 1, "eps": max_episodes // 2, "label": "AGENT SECOND (P2)"})
    else:
        print(f"--- EVALUATING AGENT: {agent_type.upper()} VS OPPONENT: {opp_type.upper()} ---")
        orders_to_run.append({"order": -1, "eps": max_episodes, "label": "RANDOM ORDER"})

    all_results = []

    for run_cfg in orders_to_run:
        target_eps = run_cfg["eps"]
        order_flag = run_cfg["order"]
        label = run_cfg["label"]

        print(f"\n >>> STARTING SUB-RUN: {label} for {target_eps} episodes...")
        env = VectorEnvAdapter(num_envs=num_envs, opp_mode=opp_mode, force_start_order=order_flag)

        # --- WARMUP / COMPILATION ---
        print(" [Init] Compiling Numba functions (Reset)... This may take 30s+")
        env.reset()
        if run_cfg == orders_to_run[0]:  # Only compile step once really needed, but reset depends on args
            print(" [Init] Compiling Numba functions (Step)... This may take 60s+")
            dummy_actions = np.zeros(num_envs, dtype=np.int32)
            env.step(dummy_actions)
            print(" [Init] Compilation complete!")

        model = None
        if agent_type == "ppo":
            if not os.path.exists(model_path):
                print(f"Model {model_path} not found.")
                return
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading PPO model: {model_path} on {device}")
            model = MaskablePPO.load(model_path, env=env, device=device)

        print(f"Starting {target_eps} evaluation games ({num_envs} parallel)...")
        obs = env.reset()

        total_rewards = np.zeros(num_envs)
        wins = 0
        total_episodes = 0
        start_time = time.time()

        # Track stats
        ep_rewards = []
        ep_scores = []
        ep_opp_scores = []
        step_counter = 0
        last_print_time = time.time()

        while total_episodes < target_eps:
            action_masks = env.action_masks()

            if agent_type == "ppo":
                action, _ = model.predict(obs, action_masks=action_masks, deterministic=True)
            elif agent_type == "random":
                action = np.zeros(num_envs, dtype=np.int32)
                for i in range(num_envs):
                    legal = np.where(action_masks[i])[0]
                    if len(legal) > 0:
                        action[i] = np.random.choice(legal)
                    else:
                        action[i] = 0
            elif agent_type == "heuristic":
                # Re-implementing a minimal heuristic for evaluation:
                # 1. Play Member (prioritize higher cost in hand)
                # 2. Set Live (if zone has space)
                # 3. Activate (if available and not tapped)
                # 4. Pass
                action = np.zeros(num_envs, dtype=np.int32)
                for i in range(num_envs):
                    legal = np.where(action_masks[i])[0]

                    # Heuristic logic
                    live_set = [a for a in legal if 400 <= a <= 459]
                    member_play = [a for a in legal if 1 <= a <= 180]
                    activate = [a for a in legal if 200 <= a <= 202]

                    if live_set:
                        action[i] = live_set[0]
                    elif member_play:
                        # Pick highest cost member if possible
                        # This is just a rough proxy for a "good" move
                        action[i] = member_play[-1]
                    elif activate:
                        action[i] = activate[0]
                    else:
                        action[i] = 0

            obs, rewards, dones, infos = env.step(action)
            step_counter += num_envs

            if time.time() - last_print_time > 2.0:
                elapsed = time.time() - start_time
                fps = step_counter / elapsed if elapsed > 0 else 0
                # Peek into global ctx for turn number
                avg_turn = np.mean(env.game_state.batch_global_ctx[:, 54])
                print(
                    f" [Running] {total_episodes}/{target_eps} eps. Speed: {fps:.0f} steps/s | Avg Turn: {avg_turn:.1f}"
                )
                last_print_time = time.time()

            total_rewards += rewards

            for i in range(num_envs):
                if dones[i]:
                    inf = infos[i]
                    ep_rewards.append(total_rewards[i])
                    agent_s = inf.get("terminal_score_agent", 0)
                    opp_s = inf.get("terminal_score_opp", 0)
                    ep_scores.append(agent_s)
                    ep_opp_scores.append(opp_s)

                    if agent_s > opp_s:
                        wins += 1

                    total_rewards[i] = 0
                    total_episodes += 1
                    if total_episodes >= target_eps:
                        break

        duration = time.time() - start_time
        win_rate = (wins / total_episodes) * 100 if total_episodes > 0 else 0
        avg_reward = np.mean(ep_rewards) if ep_rewards else 0
        avg_score = np.mean(ep_scores) if ep_scores else 0
        avg_opp_score = np.mean(ep_opp_scores) if ep_opp_scores else 0

        print("\n" + "=" * 40)
        print(f" RESULTS FOR {label}:")
        print("=" * 40)
        print(f"Total Episodes:  {total_episodes}")
        print(f"Win Rate:        {win_rate:.1f}%")
        print(f"Avg Reward:      {avg_reward:.2f}")
        print(f"Avg Score:       {avg_score:.2f}")
        print(f"Avg Opp Score:   {avg_opp_score:.2f}")
        print(f"Duration:        {duration:.1f}s")
        print("=" * 40 + "\n")

        all_results.append(
            {
                "label": label,
                "win_rate": win_rate,
                "avg_score": avg_score,
                "avg_opp_score": avg_opp_score,
                "episodes": total_episodes,
                "wins": wins,
            }
        )

        env.close()

    if args.fair:
        total_eps = sum(r["episodes"] for r in all_results)
        total_wins = sum(r["wins"] for r in all_results)
        agg_win_rate = (total_wins / total_eps) * 100 if total_eps > 0 else 0

        print("\n" + "=" * 60)
        print(f" === OVERALL FAIR EVALUATION ({total_eps} games) ===")
        print("=" * 60)
        for r in all_results:
            print(
                f" {r['label']:<20} | WR: {r['win_rate']:.1f}% | Agent: {r['avg_score']:.2f} | Opp: {r['avg_opp_score']:.2f}"
            )
        print("-" * 60)
        print(f" AGGREGATE WIN RATE:   {agg_win_rate:.1f}%")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    evaluate()
