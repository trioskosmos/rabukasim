import os
import random
import sys
import time

import numpy as np

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ai.headless_runner import RandomAgent, SmartHeuristicAgent, initialize_game


def run_match(p0_agent, p1_agent, seed, num_games=10, custom_deck=None, max_turns=200):
    p0_wins = 0
    p1_wins = 0
    draws = 0

    total_turns = 0
    p0_total_score = 0
    p1_total_score = 0

    start_time = time.time()

    for i in range(num_games):
        # Setup specific seed for this game
        game_seed = seed + i
        random.seed(game_seed)
        np.random.seed(game_seed)

        # Initialize
        state = initialize_game(use_real_data=True, cards_path="engine/data/cards.json")

        if custom_deck:
            # Use provided custom deck list
            # 48 members, 12 lives (usually)
            # But custom_deck is just a list of IDs.
            # We need to split them or just assign them?
            # Player.main_deck expects a list of IDs.
            for p in state.players:
                p.main_deck = list(custom_deck)  # Copy it
                random.shuffle(p.main_deck)  # Shuffle differently each game
                p.energy_deck = [200] * 12
        else:
            # Setup Random Decks
            member_keys = list(state.member_db.keys())
            live_keys = list(state.live_db.keys())

            for p in state.players:
                # 48 members, 12 lives
                m_list = random.choices(member_keys, k=48)
                l_list = random.choices(live_keys, k=12)
                p.main_deck = m_list + l_list
                random.shuffle(p.main_deck)
                p.energy_deck = [200] * 12

        # Initial Draw
        for p in state.players:
            # Draw 5
            for _ in range(5):
                if p.main_deck:
                    p.hand.append(p.main_deck.pop(0))
            # Charge 3
            for _ in range(3):
                p.energy_zone.append(p.energy_deck.pop(0))

        # Run Game
        turn_count = 0
        while not state.game_over and turn_count < max_turns:
            state.check_win_condition()
            if state.game_over:
                break

            pid = state.current_player
            agent = p0_agent if pid == 0 else p1_agent

            try:
                action = agent.choose_action(state, pid)
                state = state.step(action)
            except Exception as e:
                print(f"Game {i} Error: {e}")
                state.game_over = True
                state.winner = 1 - pid  # Disqualify crasher
                break

            turn_count += 1

        # Stats
        if state.winner == 0:
            p0_wins += 1
        elif state.winner == 1:
            p1_wins += 1
        else:
            draws += 1

        total_turns += state.turn_number
        p0_total_score += len(state.players[0].success_lives)
        p1_total_score += len(state.players[1].success_lives)

    duration = time.time() - start_time

    return {
        "p0_wins": p0_wins,
        "p1_wins": p1_wins,
        "draws": draws,
        "avg_turns": total_turns / num_games,
        "p0_avg_score": p0_total_score / num_games,
        "p1_avg_score": p1_total_score / num_games,
        "duration": duration,
        "games_per_sec": num_games / duration,
    }


def print_results(label, res):
    print(f"\n=== {label} ===")
    print(f"P0 Wins: {res['p0_wins']} | P1 Wins: {res['p1_wins']} | Draws: {res['draws']}")
    print(f"Avg Turns: {res['avg_turns']:.1f}")
    print(f"Avg Score: P0 {res['p0_avg_score']:.1f} - P1 {res['p1_avg_score']:.1f}")
    print(f"Speed: {res['games_per_sec']:.2f} games/sec (Total: {res['duration']:.2f}s)")


def print_markdown_summary(results):
    print("\n### Tournament Results Summary")
    print("| Matchup | Avg Turns | P0 Win Rate | P1 Win Rate | Avg Score Diff (P0-P1) | Speed (g/s) |")
    print("|---|---|---|---|---|---|")

    for label, res in results.items():
        total_games = res["p0_wins"] + res["p1_wins"] + res["draws"]
        p0_rate = (res["p0_wins"] / total_games) * 100
        p1_rate = (res["p1_wins"] / total_games) * 100
        score_diff = res["p0_avg_score"] - res["p1_avg_score"]

        print(
            f"| {label} | {res['avg_turns']:.1f} | {p0_rate:.1f}% | {p1_rate:.1f}% | {score_diff:+.1f} | {res['games_per_sec']:.2f} |"
        )


def run_match_worker(args):
    """
    Worker function for multiprocessing.
    args: (match_label, p0_name, p1_name, seed, num_games, custom_deck, max_turns)
    """
    label, p0_name, p1_name, seed, num_games, custom_deck, max_turns = args

    # Re-instantiate agents within the process to avoid pickling issues
    # and ensure fresh state
    agents = {
        "Random": RandomAgent(),
        "Smart": SmartHeuristicAgent(),
    }

    p0_agent = agents[p0_name]
    p1_agent = agents[p1_name]

    # Run the match (using the existing logic, copied inline or reused if refined)
    # We reuse the logic from run_match but we need to ensure run_match is accessible.
    # It is defined in this module, so we can call it.

    res = run_match(p0_agent, p1_agent, seed, num_games, custom_deck, max_turns)
    return label, res


if __name__ == "__main__":
    import argparse
    import multiprocessing

    # Enable freeze check for Windows
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=20, help="Games per match")
    parser.add_argument("--max_turns", type=int, default=200, help="Max turns per game")
    parser.add_argument("--quick", action="store_true", help="Run only fast agents")
    parser.add_argument("--workers", type=int, default=0, help="Number of worker processes (0=Auto)")
    args = parser.parse_args()

    SEED = 42

    # Define Matchups
    matchups = [
        ("Random", "Random"),
        ("Random", "Smart"),
        ("Smart", "Random"),  # Check swapping
        ("Smart", "Smart"),
    ]

    print(f"Starting Tournament with {args.games} games per match (Max Turns: {args.max_turns})...")

    # Load Custom Deck
    custom_deck_ids = []
    try:
        import json

        # Load ID Map & Build DB for Extractor
        with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        card_map = {}  # No -> ID
        extractor_db = {}  # No -> Dict with type

        if "member_db" in data:
            for c in data["member_db"].values():
                card_map[c["card_no"]] = c["card_id"]
                extractor_db[c["card_no"]] = c | {"type": "メンバー"}

        if "live_db" in data:
            for c in data["live_db"].values():
                card_map[c["card_no"]] = c["card_id"]
                extractor_db[c["card_no"]] = c | {"type": "ライブ"}

        # Add mapping for + vs ＋
        for k in list(card_map.keys()):
            if "+" in k:
                full_k = k.replace("+", "＋")
                card_map[full_k] = card_map[k]
                extractor_db[full_k] = extractor_db[k]

        # Import Extractor
        try:
            from tools.deck_extractor import extract_deck_data
        except ImportError:
            try:
                from deck_extractor import extract_deck_data
            except ImportError:
                # Fallback if path issues
                import sys

                sys.path.append("tools")
                from deck_extractor import extract_deck_data

        # Load Deck Text
        with open("tests/decktest.txt", "r", encoding="utf-8") as f:
            content = f.read()

        print("Loading custom deck from tests/decktest.txt using deck_extractor...")
        main_ids_str, energy_ids_str, types, errors = extract_deck_data(content, extractor_db)

        if errors:
            print("Deck Errors:", errors)

        # Convert String IDs to Int IDs
        for no in main_ids_str:
            cid = card_map.get(no)
            if cid:
                custom_deck_ids.append(cid)
            else:
                print(f"WARNING: ID {no} not found in map")

        # Also handle Energy Deck if needed?
        # Benchmark usually creates default energy deck [200]*12.
        # But if custom deck specifies energy members, we might want them.
        # For simplicity, we stick to main deck for now, or use standard energy.

        print(f"Loaded {len(custom_deck_ids)} cards via extractor.")

    except Exception as e:
        print(f"Failed to load custom deck: {e} - Using Random Decks")
        import traceback

        traceback.print_exc()
        custom_deck_ids = None

    # Prepare Tasks
    tasks = []
    for p0_name, p1_name in matchups:
        label = f"{p0_name} vs {p1_name}"

        # Reduce games for Super matches to save time unless explicitly high
        # In multiprocessing, we can arguably run full games, but keep logic for consistency
        games = args.games

        tasks.append((label, p0_name, p1_name, SEED, games, custom_deck_ids, args.max_turns))

    print(f"Scenarios: {len(tasks)}")
    print("Running in parallel...")

    workers = args.workers if args.workers > 0 else (multiprocessing.cpu_count() - 1 or 1)
    print(f"Using {workers} worker processes.")

    all_results = {}

    with multiprocessing.Pool(processes=workers) as pool:
        # map_async + get allows catching exceptions
        results = pool.map(run_match_worker, tasks)

        for label, res in results:
            all_results[label] = res
            print_results(label, res)

    import json

    with open("benchmark_report.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print_markdown_summary(all_results)
