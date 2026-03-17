import argparse
import json
import os
import random
import sys
import time
import traceback
from datetime import datetime
from multiprocessing import Pool, cpu_count

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import RandomAgent


def init_worker():
    """Initializer for worker processes to load data once."""
    try:
        # print(f"Worker {os.getpid()} loading data...", end='\r')
        loader = CardDataLoader("data/cards.json")
        m_db, l_db, e_db = loader.load()
        GameState.member_db = m_db
        GameState.live_db = l_db
        # GameState.energy_db = e_db
    except Exception as e:
        print(f"Worker init failed: {e}")
        traceback.print_exc()


def run_single_game_stress(game_idx):
    """Run a single game in a worker process"""
    # Re-seed for this process
    seed = (int(time.time() * 1000) + game_idx) % 2**32
    random.seed(seed)

    agent = RandomAgent()
    max_turns = 200

    history = []

    try:
        # use_real_data=True usually reloads, but if we pass it,
        # we need to make sure it doesn't overwrite our pre-loaded DB if possible,
        # OR we rely on initialize_game checking if DB is populated.
        # Looking at game_state.py usually it has:
        # if use_real_data and not GameState.member_db: ...

        # To be safe, let's assume initialize_game might try to reload if we strictly pass use_real_data=True
        # BUT, since we populated GameState.member_db in init_worker,
        # we can pass use_real_data=False (or similar) IF initialize_game uses the existing class attributes.

        # Actually, best approach is let's trust initialize_game checks or just pass False
        # since we manually populated GameState.*_db

        # However, initialize_game(False) might use dummy data if not careful.
        # Let's verify if we need to force it.
        # If GameState.member_db is set, initialize_game(False) usually uses it?
        # Actually in parallel_runner it does:
        # state = GameState()
        # ... setup decks ...

        # Let's use GameState() directly to avoid re-loading overhead if initialize_game is heavy
        # But initialize_game prepares decks.

        # Let's just use GameState() and manually init decks like parallel_runner
        # OR fix initialize_game to check.

        # Since I cannot easily see initialize_game right now (last grep failed),
        # I will emulate parallel_runner's approach which is robust.

        if not GameState.member_db:
            # Fallback if init failed (shouldn't happen)
            loader = CardDataLoader("data/cards.json")
            m, l, e = loader.load()
            GameState.member_db = m
            GameState.live_db = l

        state = GameState(verbose=False)

        # SETUP DECKS (Simplified Logic from parallel_runner / initialize_game)
        for p in state.players:
            # Create a deck of valid cards
            member_ids = list(GameState.member_db.keys())
            if not member_ids:
                raise Exception("No members found info DB")

            # 48 members
            p.main_deck = []
            for _ in range(48):
                p.main_deck.append(random.choice(member_ids))

            # 12 lives
            live_ids = list(GameState.live_db.keys())
            for _ in range(12):
                p.main_deck.append(random.choice(live_ids))

            random.shuffle(p.main_deck)

            # Energy
            p.energy_deck = [200] * 12  # Standard energy

            # Initial Draw
            for _ in range(6):
                if p.main_deck:
                    p.hand.append(p.main_deck.pop())

            # Initial Energy
            for _ in range(3):
                if p.energy_deck:
                    p.energy_zone.append(p.energy_deck.pop(0))

        state.first_player = random.randint(0, 1)
        state.current_player = state.first_player
        state.phase = Phase.MULLIGAN_P1

        while not state.is_terminal() and state.turn_number < max_turns:
            pid = state.current_player
            mask = state.get_legal_actions()

            # Check for hang
            if not any(mask):
                phase_name = state.phase.name if hasattr(state.phase, "name") else str(state.phase)
                raise Exception(f"No legal actions available in phase {phase_name} (Turn {state.turn_number})")

            action = agent.choose_action(state, pid)

            phase_name = state.phase.name if hasattr(state.phase, "name") else str(state.phase)
            history.append({"action": int(action), "turn": state.turn_number, "phase": phase_name, "player": pid})
            if len(history) > 50:
                history.pop(0)

            state = state.step(action)

        result = {
            "id": game_idx,
            "success": True,
            "winner": state.get_winner() if state.is_terminal() else "timeout",
            "turns": state.turn_number,
            "history": history[-20:],
        }
        return result

    except Exception as e:
        # Save crash report locally from worker
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        os.makedirs("stress_reports", exist_ok=True)
        filename = f"stress_reports/crash_{timestamp}_g{game_idx}.json"

        report = {
            "timestamp": timestamp,
            "game_id": game_idx,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "history": history,
            "turn": state.turn_number if "state" in locals() else -1,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return {"id": game_idx, "success": False, "error": str(e), "report_file": filename}


def run_wrapper(args_tuple):
    return run_single_game_stress(*args_tuple)


def run_stress_test_parallel(num_games=50, max_turns=200, duration=None):
    if duration:
        print(f"Starting Optimized Parallel Stress Test: Run for {duration} seconds on {cpu_count()} cores")
        num_games = 1000000  # irrelevant large number
    else:
        print(f"Starting Optimized Parallel Stress Test: {num_games} games on {cpu_count()} cores")

    print("Initializing workers (loading data once)...")

    start_time = time.time()

    # We need an infinite generator of args if duration is set, or fixed list
    # Because pool.imap_unordered consumes an iterable.

    def arg_generator():
        i = 0
        while True:
            if duration and (time.time() - start_time > duration):
                break
            if not duration and i >= num_games:
                break
            yield (i,)
            i += 1

    results = []
    stats = {"total": 0, "success": 0, "crashes": 0, "timeouts": 0, "errors": {}}

    with Pool(cpu_count(), initializer=init_worker) as pool:
        for i, res in enumerate(pool.imap_unordered(run_wrapper, arg_generator())):
            results.append(res)
            stats["total"] += 1

            if res["success"]:
                if res["winner"] == "timeout":
                    stats["timeouts"] += 1
                else:
                    stats["success"] += 1
            else:
                stats["crashes"] += 1
                err_key = res["error"]
                stats["errors"][err_key] = stats["errors"].get(err_key, 0) + 1

            # Progress bar
            elapsed = time.time() - start_time
            if duration and elapsed > duration:
                break

            if (i + 1) % 5 == 0:
                speed = (i + 1) / elapsed if elapsed > 0 else 0
                print(
                    f"Progress: {i + 1} games | Crashes: {stats['crashes']} | Speed: {speed:.1f} games/s | Time: {elapsed:.1f}s",
                    end="\r",
                )

    total_time = time.time() - start_time

    print("\n" + "=" * 50)
    print("PARALLEL STRESS TEST COMPLETE")
    print(f"Total Games: {stats['total']}")
    print(f"Time Taken:  {total_time:.2f}s ({stats['total'] / total_time:.1f} games/s)")
    print(f"Successful:  {stats['success']}")
    print(f"Timeouts:    {stats['timeouts']}")
    print(f"Crashes:     {stats['crashes']}")

    if stats["crashes"] > 0:
        print("\nTop Errors:")
        for err, count in stats["errors"].items():
            print(f"  [{count}x] {err}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=50)
    parser.add_argument("--turns", type=int, default=200)
    parser.add_argument("--duration", type=int, default=None, help="Run for N seconds")
    args = parser.parse_args()

    try:
        run_stress_test_parallel(args.games, args.turns, args.duration)
    except KeyboardInterrupt:
        print("\nTerminated.")
