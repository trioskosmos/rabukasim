#!/usr/bin/env python3
"""
Detailed action profiler - runs 100 games and analyzes action timing.
Tracks which actions are fastest/slowest and which cards produce them.
Detects softlocks and terminates stuck games.
"""

import argparse
import sys
import time
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.perf_optimizations import disable_debug_logging, enable_torch_optimizations

# Enable optimizations first
disable_debug_logging()
enable_torch_optimizations()

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig
import numpy as np

@dataclass
class ActionRecord:
    action_id: int
    phase: int
    strategy: str
    duration: float
    card_id: int | None
    action_type: str  # "member", "life", "school", "vanilla", "intro", "other"


def classify_action(action_id: int) -> tuple[str, int | None]:
    """Classify action and extract card ID if applicable."""
    if 1000 <= action_id < 1100:
        return "member", (action_id - 1000) % 50  # Card slot in member area
    elif 600 <= action_id < 700:
        return "life", (action_id - 600)
    elif 900 <= action_id < 1000:
        return "yell", (action_id - 900)
    elif 400 <= action_id < 500:
        return "school", (action_id - 400)
    elif 200 <= action_id < 300:
        return "vanilla", (action_id - 200)
    elif 300 <= action_id < 400:
        return "intro", (action_id - 300)
    else:
        return "other", action_id


def get_card_from_state(state, action_id: int, rust_db):
    """Try to get card info from the game state based on action."""
    try:
        # Get card info from action_id
        action_type, card_ref = classify_action(action_id)
        
        # Try to get actual card ID if in member area
        if action_type == "member":
            # Member area action
            p0_members = list(state.player[0].members)
            if card_ref < len(p0_members):
                return p0_members[card_ref], action_type
        
        return card_ref, action_type
    except:
        return None, classify_action(action_id)[0]


def play_game_with_profiling(comp: VanillaComparison, seed: int, strategy: str, timeout: float = 5.0) -> dict:
    """Play a game and profile action timing. Timeout detects softlocks."""
    random_seed = seed
    
    try:
        game = comp._new_game(random_seed)
        selected_deck = comp.decks[seed % len(comp.decks)]
        initial_deck = selected_deck["initial_deck"]
        
        actions = []  # List of ActionRecord
        step = 0
        max_steps = 500
        last_action_time = time.time()
        softlock = False
        softlock_reason = None
        
        while not game.is_terminal() and step < max_steps:
            phase = int(game.phase)
            cp = int(game.current_player)
            
            # Check for softlock (no progress for timeout)
            if time.time() - last_action_time > timeout:
                softlock = True
                softlock_reason = f"No progress for {timeout}s at step {step}, phase {phase}"
                break
            
            # Skip auto phases quickly
            if phase in [-1, 0, 2, 4, 5, 8]:
                legal_ids = [int(x) for x in game.get_legal_action_ids()]
                if not legal_ids:
                    game.auto_step(comp.rust_db)
                    step += 1
                    continue
                
                strategy_func = {
                    "neural": comp._choose_neural_action,
                    "turnseq": comp._choose_turnseq_action,
                    "mcts": comp._choose_mcts_action,
                    "random": comp._choose_random_action,
                }.get(strategy, comp._choose_random_action)
                
                start_time = time.time()
                
                try:
                    if strategy == "mcts":
                        action = strategy_func(game, legal_ids, 0.1)  # Short time limit
                    elif strategy == "neural":
                        action = strategy_func(game, legal_ids, initial_deck, 0.1)
                    elif strategy == "turnseq":
                        action = strategy_func(game, legal_ids, 0.1)
                    else:  # random
                        action = strategy_func(game, legal_ids)
                except Exception as e:
                    print(f"    Strategy error: {e}, taking random action")
                    action = int(legal_ids[0])
                
                elapsed = time.time() - start_time
                action_type, card_ref = classify_action(int(action))
                
                actions.append(ActionRecord(
                    action_id=int(action),
                    phase=phase,
                    strategy=strategy,
                    duration=elapsed,
                    card_id=card_ref,
                    action_type=action_type,
                ))
                
                last_action_time = time.time()
                
                try:
                    game.step(int(action))
                except Exception as e:
                    print(f"    Step error: {e}")
                    break
                    
            elif phase in (-3, -2):
                legal_ids = [int(x) for x in game.get_legal_action_ids()]
                if legal_ids:
                    game.step(int(min(legal_ids)))
            else:
                try:
                    game.step(0)
                except:
                    pass
            
            step += 1
        
        winner = int(game.get_winner()) if game.is_terminal() else -1
        turns = int(game.turn)
        
        return {
            "seed": seed,
            "strategy": strategy,
            "winner": winner,
            "turns": turns,
            "steps": step,
            "terminal": game.is_terminal(),
            "softlock": softlock,
            "softlock_reason": softlock_reason,
            "actions": actions,
        }
    
    except Exception as e:
        return {
            "seed": seed,
            "strategy": strategy,
            "winner": -1,
            "turns": 0,
            "steps": 0,
            "terminal": False,
            "softlock": True,
            "softlock_reason": str(e),
            "actions": [],
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--strategy", choices=["neural", "turnseq", "mcts", "random"], default="random")
    parser.add_argument("--timeout", type=float, default=5.0, help="Softlock timeout in seconds")
    args = parser.parse_args()
    
    config = ComparisonConfig(time_per_move=0.1, num_games=1)
    comp = VanillaComparison(config)
    
    print(f"Running {args.games} games with '{args.strategy}' strategy")
    print(f"Softlock timeout: {args.timeout}s")
    print("=" * 80)
    print()
    
    all_actions = []
    action_timings = defaultdict(list)
    action_by_card = defaultdict(list)
    games_with_softlock = 0
    successful_games = 0
    
    for game_num in range(args.games):
        print(f"Game {game_num + 1}/{args.games}...", end=" ", flush=True)
        
        result = play_game_with_profiling(comp, 5000 + game_num, args.strategy, args.timeout)
        
        if result["softlock"]:
            print(f"[SOFTLOCK] {result['softlock_reason']}")
            games_with_softlock += 1
        else:
            print(f"Done ({result['turns']} turns, {len(result['actions'])} actions)")
            successful_games += 1
        
        for action in result["actions"]:
            all_actions.append(action)
            action_timings[action.action_type].append(action.duration)
            if action.card_id is not None:
                action_by_card[f"{action.action_type}:{action.card_id}"].append(action.duration)
    
    print()
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()
    
    print(f"Games completed: {successful_games}/{args.games}")
    if games_with_softlock > 0:
        print(f"Games with softlock: {games_with_softlock}")
    print(f"Total actions profiled: {len(all_actions)}")
    print()
    
    # Summary by action type
    print("ACTION TYPE SUMMARY")
    print("-" * 80)
    action_stats = {}
    
    for action_type in sorted(action_timings.keys()):
        times = action_timings[action_type]
        if times:
            min_t = min(times)
            max_t = max(times)
            avg_t = np.mean(times)
            median_t = np.median(times)
            p95_t = np.percentile(times, 95)
            p99_t = np.percentile(times, 99)
            
            action_stats[action_type] = {
                "count": len(times),
                "min": min_t,
                "max": max_t,
                "avg": avg_t,
                "median": median_t,
                "p95": p95_t,
                "p99": p99_t,
            }
            
            print(f"{action_type:12s} | count={len(times):5d} | "
                  f"avg={avg_t*1000:7.2f}ms | min={min_t*1000:7.2f}ms | max={max_t*1000:7.2f}ms | "
                  f"p95={p95_t*1000:7.2f}ms | p99={p99_t*1000:7.2f}ms")
    
    print()
    print("FASTEST ACTIONS")
    print("-" * 80)
    
    fastest = sorted(all_actions, key=lambda a: a.duration)[:10]
    print(f"{'#':<3} {'Type':<10} {'Card':<8} {'Duration (ms)':<15} {'Phase':<8} {'Strategy':<10}")
    print("-" * 80)
    for i, action in enumerate(fastest):
        print(f"{i+1:<3} {action.action_type:<10} {str(action.card_id):<8} "
              f"{action.duration*1000:>6.2f}{' '*8} {action.phase:<8} {action.strategy:<10}")
    
    print()
    print("SLOWEST ACTIONS")
    print("-" * 80)
    
    slowest = sorted(all_actions, key=lambda a: a.duration, reverse=True)[:10]
    print(f"{'#':<3} {'Type':<10} {'Card':<8} {'Duration (ms)':<15} {'Phase':<8} {'Strategy':<10}")
    print("-" * 80)
    for i, action in enumerate(slowest):
        print(f"{i+1:<3} {action.action_type:<10} {str(action.card_id):<8} "
              f"{action.duration*1000:>6.2f}{' '*8} {action.phase:<8} {action.strategy:<10}")
    
    print()
    print("SLOWEST CARD ACTIONS (by card type)")
    print("-" * 80)
    
    card_stats = []
    for card_action, times in sorted(action_by_card.items()):
        if len(times) >= 3:  # Only cards with 3+ actions
            avg_t = np.mean(times)
            max_t = max(times)
            card_stats.append((card_action, avg_t, max_t, len(times)))
    
    card_stats.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'Action Type:Card':<20} {'Avg (ms)':<12} {'Max (ms)':<12} {'Count':<8}")
    print("-" * 80)
    for card_action, avg_t, max_t, count in card_stats[:15]:
        print(f"{card_action:<20} {avg_t*1000:>8.2f}{' '*3} {max_t*1000:>8.2f}{' '*3} {count:>8}")
    
    print()
    print("=" * 80)
    print("PROFILE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
