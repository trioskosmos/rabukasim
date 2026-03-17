import os
import random
import sys
import time
import traceback

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import RandomAgent, SmartHeuristicAgent


class TrueRandomAgent:
    """Completely random agent with no heuristics"""

    def choose_action(self, state: GameState, player_id: int):
        import numpy as np

        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if len(legal_indices) == 0:
            return 0
        return int(np.random.choice(legal_indices))


def run_single_game(game_idx, seed):
    """Run a single AI game with no output during gameplay"""
    random.seed(seed)

    # Randomize AI types: 50% chance for each player to be random vs smart
    ai_types = []
    for _ in range(2):
        roll = random.random()
        if roll < 0.1:
            ai_types.append(("Random", TrueRandomAgent()))
        elif roll < 0.4:
            ai_types.append(("Smart", RandomAgent()))
        else:
            ai_types.append(("Expert", SmartHeuristicAgent()))

    max_turns = 500

    try:
        # Setup game state
        if not GameState.member_db:
            loader = CardDataLoader("data/cards.json")
            m, l, e = loader.load()
            GameState.member_db = m
            GameState.live_db = l

        state = GameState(verbose=False)

        # Setup decks
        for p in state.players:
            member_ids = list(GameState.member_db.keys())
            if not member_ids:
                raise Exception("No members found in DB")

            # 48 members + 12 lives
            p.main_deck = []
            for _ in range(48):
                p.main_deck.append(random.choice(member_ids))

            live_ids = list(GameState.live_db.keys())
            for _ in range(12):
                p.main_deck.append(random.choice(live_ids))

            random.shuffle(p.main_deck)

            # Energy
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

        # Run game silently - redirect stdout to suppress all prints
        import contextlib
        import io

        turn_count = 0
        with contextlib.redirect_stdout(io.StringIO()):
            while not state.is_terminal() and turn_count < max_turns:
                pid = state.current_player
                mask = state.get_legal_actions()

                if not any(mask):
                    phase_name = state.phase.name if hasattr(state.phase, "name") else str(state.phase)
                    raise Exception(f"No legal actions in phase {phase_name}")

                action = ai_types[pid][1].choose_action(state, pid)
                state = state.step(action)
                turn_count += 1

        # Calculate results
        p0_score = len(state.players[0].success_lives)
        p1_score = len(state.players[1].success_lives)
        winner = state.get_winner() if state.is_terminal() else None

        return {
            "success": True,
            "game_id": game_idx,
            "ai_types": (ai_types[0][0], ai_types[1][0]),
            "turns": turn_count,
            "winner": winner,
            "scores": (p0_score, p1_score),
            "stop_reason": "terminal" if state.is_terminal() else "max_turns",
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "game_id": game_idx,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "stop_reason": "crash",
        }


def run_timed_games(duration_seconds=10):
    """Run AI games for a specified duration"""
    print(f"Starting timed AI game runner for {duration_seconds} seconds...")
    print("Loading card data...\n")

    # Pre-load data
    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()
    GameState.member_db = m_db
    GameState.live_db = l_db

    start_time = time.time()
    game_count = 0
    results = []

    while time.time() - start_time < duration_seconds:
        seed = int(time.time() * 1000000) % (2**32)
        result = run_single_game(game_count, seed)
        results.append(result)

        # Print game summary immediately
        print(f"{'=' * 70}")
        print(f"GAME #{game_count + 1}")
        print(f"{'-' * 70}")

        if result["success"]:
            ai0, ai1 = result["ai_types"]
            print(f"AI Types:     P0={ai0:6s} vs P1={ai1:6s}")
            print(f"Turns:        {result['turns']}")

            if result["stop_reason"] == "terminal":
                winner = result["winner"]
                if winner == 0 or winner == 1:
                    print(f"Winner:       P{winner}")
                else:
                    print("Winner:       Draw")
            else:
                print("Stop Reason:  Timeout (max turns reached)")

            p0_score, p1_score = result["scores"]
            print(f"Final Score:  P0={p0_score} | P1={p1_score}")
        else:
            print("Stop Reason:  CRASH")
            print(f"Error:        {result['error']}")
            if "traceback" in result:
                print("\nTraceback:")
                print(result["traceback"])

        game_count += 1

    # Final summary
    elapsed = time.time() - start_time
    print(f"\n{'=' * 70}")
    print("FINAL SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total Time:       {elapsed:.2f}s")
    print(f"Total Games:      {game_count}")
    print(f"Games per Second: {game_count / elapsed:.2f}")

    successful = [r for r in results if r["success"]]
    crashed = [r for r in results if not r["success"]]

    print(f"\nSuccessful:       {len(successful)}")
    print(f"Crashed:          {len(crashed)}")

    if successful:
        terminals = [r for r in successful if r["stop_reason"] == "terminal"]
        timeouts = [r for r in successful if r["stop_reason"] == "max_turns"]
        print(f"  - Completed:    {len(terminals)}")
        print(f"  - Timeouts:     {len(timeouts)}")

        avg_turns = sum(r["turns"] for r in successful) / len(successful)
        print(f"\nAverage Turns:    {avg_turns:.1f}")

    if crashed:
        print("\nCrash Reasons:")
        error_counts = {}
        for r in crashed:
            err = r["error"]
            error_counts[err] = error_counts.get(err, 0) + 1

        for err, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  [{count}x] {err}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run AI games for a timed duration")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds (default: 10)")

    args = parser.parse_args()

    try:
        run_timed_games(args.duration)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
