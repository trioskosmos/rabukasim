"""
Parallel game runner with easier live cards and detailed logging
"""

import io
import os
import random
import sys
import time
from multiprocessing import Pool, cpu_count

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import RandomAgent


def run_single_game(game_idx):
    """Run a single game in a worker process"""
    seed = 999 + game_idx
    random.seed(seed)
    np.random.seed(seed)

    # Load cards fresh in worker
    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()

    # Filter to EASY lives only (max 3 hearts total requirement)
    easy_lives = {}
    for lid, live in l_db.items():
        total_req = live.required_hearts.sum()
        if total_req <= 3:
            easy_lives[lid] = live

    if len(easy_lives) < 3:
        easy_lives = l_db

    GameState.member_db = m_db
    GameState.live_db = easy_lives
    GameState.energy_db = e_db

    state = GameState()

    # Build decks with easy lives
    for p in state.players:
        # Members
        available_members = list(m_db.keys())
        random.shuffle(available_members)
        p.main_deck = []
        for mid in available_members[:12]:
            p.main_deck.extend([mid] * 4)

        # EASY Lives
        available_lives = list(easy_lives.keys())
        random.shuffle(available_lives)
        for lid in available_lives[:3]:
            p.main_deck.extend([lid] * 4)

        random.shuffle(p.main_deck)

        # Energy
        if e_db:
            eid = list(e_db.keys())[0]
            p.energy_deck = [eid] * 12
        else:
            p.energy_deck = [200] * 12

        # Initial draw
        for _ in range(6):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())

        # Initial energy
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    state.first_player = random.randint(0, 1)
    state.current_player = state.first_player
    state.phase = Phase.MULLIGAN_P1

    # Capture detailed log AND replay states
    log_buffer = io.StringIO()
    states_history = []

    # Custom JSON-safe serializer
    def snapshot(gs, act=-1):
        """Create a JSON-safe snapshot of game state"""
        import json

        try:
            # Import serialize function
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import server

            # Inject State AND DBs to ensure serialize_card works
            old_state = getattr(server, "game_state", None)
            old_m = getattr(server, "member_db", {})
            old_l = getattr(server, "live_db", {})
            old_e = getattr(server, "energy_db", {})

            server.game_state = gs
            server.member_db = GameState.member_db
            server.live_db = GameState.live_db
            server.energy_db = getattr(GameState, "energy_db", {})

            full_state = server.serialize_state()
            server.game_state = old_state
            # Restore old DBs (good practice)
            server.member_db = old_m
            server.live_db = old_l
            server.energy_db = old_e

            # Test if it's JSON-serializable, if not use minimal
            json.dumps(full_state)
            full_state["action_taken"] = act
            return full_state
        except (TypeError, AttributeError):
            # Fallback to minimal state if serialization fails
            return {
                "turn": gs.turn_number,
                "phase": gs.phase.name,
                "current_player": gs.current_player,
                "action_taken": act,
                "players": [
                    {
                        "score": len(gs.players[0].success_lives),
                        "hand_count": len(gs.players[0].hand),
                        "deck_count": len(gs.players[0].main_deck),
                    },
                    {
                        "score": len(gs.players[1].success_lives),
                        "hand_count": len(gs.players[1].hand),
                        "deck_count": len(gs.players[1].main_deck),
                    },
                ],
            }

    # Run game
    agents = [RandomAgent(), RandomAgent()]
    turn_count = 0
    max_turns = 200
    yell_count = 0  # Track yells

    log_buffer.write(f"=== Game {game_idx + 1} (Seed: {seed}) ===\n")
    states_history.append(snapshot(state))  # Initial state

    while turn_count < max_turns:
        if state.game_over:
            break
        state.check_win_condition()
        if state.game_over:
            break

        active_pid = state.current_player
        p0 = state.players[0]
        p1 = state.players[1]

        # Track yells (score changes)
        prev_yells = len(p0.success_lives) + len(p1.success_lives)

        action = agents[active_pid].choose_action(state, active_pid)

        try:
            state = state.step(action)
            states_history.append(snapshot(state, action))

            # Check for new yells
            new_yells = len(state.players[0].success_lives) + len(state.players[1].success_lives)
            if new_yells > prev_yells:
                yell_count = new_yells
                log_buffer.write(f"Turn {state.turn_number}: YELL! Total: {yell_count}\n")
        except Exception as e:
            log_buffer.write(f"ERROR: {e}\n")
            break

        turn_count += 1

    p0_score = len(state.players[0].success_lives)
    p1_score = len(state.players[1].success_lives)

    log_buffer.write("=" * 40 + "\n")
    log_buffer.write(f"Game Over. Winner: {state.winner}. Score: {p0_score}-{p1_score}\n")

    log_content = log_buffer.getvalue()
    log_buffer.close()

    # Save replay file
    import json

    replay_data = {
        "game_id": game_idx,
        "seed": seed,
        "winner": state.winner,
        "final_score": f"{p0_score}-{p1_score}",
        "turns": turn_count,
        "states": states_history,
    }

    replay_filename = f"replays/game_{game_idx + 1}.json"
    with open(replay_filename, "w") as f:
        json.dump(replay_data, f)

    return {
        "id": game_idx,
        "winner": state.winner,
        "p0_score": p0_score,
        "p1_score": p1_score,
        "yells": p0_score + p1_score,  # Total yells
        "turns": turn_count,
        "log": log_content,
        "replay_file": replay_filename,
    }


if __name__ == "__main__":
    print("Starting Parallel Simulation (Finding High Yell Games)...")
    print(f"Using {cpu_count()} CPU cores")

    start_time = time.time()

    max_games = 500
    games_to_run = list(range(max_games))

    results = []

    with Pool(cpu_count()) as pool:
        for i, result in enumerate(pool.imap_unordered(run_single_game, games_to_run)):
            results.append(result)

            # Progress
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start_time
                best = max(results, key=lambda r: r["yells"])
                print(
                    f"[{i + 1}/{max_games}] Best Yells: {best['yells']} (Game #{best['id'] + 1}), Speed: {(i + 1) / elapsed:.1f} games/s"
                )

    total_time = time.time() - start_time

    print("\n=== Simulation Complete ===")
    print(f"Games Ran: {len(results)}")
    print(f"Total Time: {total_time:.1f}s")
    print(f"Speed: {len(results) / total_time:.1f} games/sec")

    wins0 = sum(1 for r in results if r["winner"] == 0)
    wins1 = sum(1 for r in results if r["winner"] == 1)
    draws = sum(1 for r in results if r["winner"] == 2)

    print(f"Wins: P0={wins0}, P1={wins1}, Draws={draws}")

    # Find top 5 games by YELLS
    top_games = sorted(results, key=lambda r: r["yells"], reverse=True)[:5]

    print("\n=== Top 5 Games by Yell Count ===")
    for idx, game in enumerate(top_games):
        print(
            f"{idx + 1}. Game #{game['id'] + 1}: {game['yells']} Yells, Score {game['p0_score']}-{game['p1_score']}, Winner: P{game['winner']}"
        )

        # Save log
        log_filename = f"game_log_top{idx + 1}.txt"
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(game["log"])
        print(f"   Log saved to {log_filename}")
