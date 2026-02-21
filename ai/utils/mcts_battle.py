import argparse
import concurrent.futures
import json
import multiprocessing
import os
import random
import sys

from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.utils.benchmark_decks import parse_deck


def run_single_battle(
    g_idx, sims0, sims1, time0, time1, h0, h1, m0, m1, hr0, hr1, db_content, decks, alternate=False, verbose=False
):
    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)
    game.silent = not verbose

    # Convert strings to Rust enums
    modes = {
        "blind": engine_rust.EvalMode.Blind,
        "normal": engine_rust.EvalMode.Normal,
    }
    horizons = {
        "game": engine_rust.SearchHorizon.GameEnd,
        "turn": engine_rust.SearchHorizon.TurnEnd,
    }

    m_enum0 = modes.get(m0, engine_rust.EvalMode.Blind)
    m_enum1 = modes.get(m1, engine_rust.EvalMode.Blind)
    hr_enum0 = horizons.get(hr0, engine_rust.SearchHorizon.GameEnd)
    hr_enum1 = horizons.get(hr1, engine_rust.SearchHorizon.GameEnd)

    # Select random decks
    p0_deck, p0_lives, p0_energy = random.choice(decks)
    p1_deck, p1_lives, p1_energy = random.choice(decks)

    # Alternate who goes first
    if alternate and g_idx % 2 == 1:
        game.initialize_game(p1_deck, p0_deck, p1_energy, p0_energy, p1_lives, p0_lives)
        sims = [sims1, sims0]
        time_limits = [time1, time0]
        heuristics = [h1, h0]
        m_enums = [m_enum1, m_enum0]
        hr_enums = [hr_enum1, hr_enum0]
        p1_is_p0_in_engine = True
    else:
        game.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)
        sims = [sims0, sims1]
        time_limits = [time0, time1]
        heuristics = [h0, h1]
        m_enums = [m_enum0, m_enum1]
        hr_enums = [hr_enum0, hr_enum1]
        p1_is_p0_in_engine = False

    step = 0
    p0_sims_total, p1_sims_total = 0, 0
    p0_moves, p1_moves = 0, 0

    while not game.is_terminal() and step < 1000:
        cp = game.current_player
        phase = game.phase
        # -1: MulliganP1, 0: MulliganP2, 2: Energy, 4: Main, 5: LiveSet, 8: LiveResult
        if phase in [-1, 0, 2, 4, 5, 8]:
            # Use time limit if provided, otherwise generic sims
            t_limit = time_limits[cp] if time_limits else 0.0
            n_sims = sims[cp] if t_limit <= 0.0 else 0
            suggestions = game.search_mcts(n_sims, t_limit, heuristics[cp], hr_enums[cp], m_enums[cp])
            best_action = suggestions[0][0] if suggestions else 0
            try:
                # Track sims
                total_sims = sum(s[2] for s in suggestions)
                if cp == 0:
                    p0_sims_total += total_sims
                    p0_moves += 1
                else:
                    p1_sims_total += total_sims
                    p1_moves += 1

                if verbose:
                    tqdm.write(f"  P{cp} {phase}: Action {best_action} ({total_sims} sims)")

                game.step(best_action)
            except Exception as e:
                if verbose:
                    tqdm.write(f"  Step Error (Phase {phase}): {e}")
                break
        else:
            try:
                game.step(0)
            except Exception as e:
                if verbose:
                    tqdm.write(f"  Auto-Step Error (Phase {phase}): {e}")
                break
        step += 1

    if step >= 1000:
        if verbose:
            tqdm.write(f"  Action Limit Reached (1000 steps) for Game {g_idx}")

    winner = game.get_winner()
    if alternate and p1_is_p0_in_engine:
        if winner == 0:
            actual_winner = 1
        elif winner == 1:
            actual_winner = 0
        else:
            actual_winner = 2
        p0_score = game.get_player(1).score
        p1_score = game.get_player(0).score
    else:
        actual_winner = winner
        p0_score = game.get_player(0).score
        p1_score = game.get_player(1).score

    # Save rule log for draws
    if actual_winner == 2:
        log_dir = "ai/data/draw_logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"draw_game_{g_idx}.txt")
        with open(log_path, "w", encoding="utf-8") as f_log:
            f_log.write("\n".join(game.rule_log))

    return {
        "game_id": g_idx,
        "winner": actual_winner,
        "p0_score": p0_score,
        "p1_score": p1_score,
        "turns": game.turn,
        "steps": step,
        "avg_sims_p0": p0_sims_total / max(1, p0_moves) if p0_moves > 0 else 0,
        "avg_sims_p1": p1_sims_total / max(1, p1_moves) if p1_moves > 0 else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-games", type=int, default=10)
    parser.add_argument("--sims0", type=int, default=100)
    parser.add_argument("--sims1", type=int, default=100)
    parser.add_argument("--time0", type=float, default=0.0, help="Time limit per action for P0 (seconds)")
    parser.add_argument("--time1", type=float, default=0.0, help="Time limit per action for P1 (seconds)")
    parser.add_argument("--h0", type=str, default="original", choices=["original", "simple", "resnet", "hybrid"])
    parser.add_argument("--h1", type=str, default="original", choices=["original", "simple", "resnet", "hybrid"])
    parser.add_argument("--mode0", type=str, default="blind", choices=["blind", "normal"])
    parser.add_argument("--mode1", type=str, default="blind", choices=["blind", "normal"])
    parser.add_argument("--horizon0", type=str, default="game", choices=["game", "turn"])
    parser.add_argument("--horizon1", type=str, default="game", choices=["game", "turn"])
    parser.add_argument("--alternate", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Enable move-by-move logging")
    parser.add_argument("--workers", type=int, default=min(multiprocessing.cpu_count(), 4))
    parser.add_argument("--output-file", type=str, default="ai/data/mcts_battle_results.json")
    args = parser.parse_args()

    print("Loading data and decks...")
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    deck_paths = [
        "ai/decks/aqours_cup.txt",
        "ai/decks/hasunosora_cup.txt",
        "ai/decks/liella_cup.txt",
        "ai/decks/muse_cup.txt",
        "ai/decks/nijigaku_cup.txt",
    ]
    decks = []
    for dp in deck_paths:
        if os.path.exists(dp):
            decks.append(parse_deck(dp, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})))

    if not decks:
        p_deck = [124, 127, 130, 132] * 12
        p_lives = [30000, 30001, 30002]
        p_energy = [40000] * 10
        decks = [(p_deck, p_lives, p_energy)]

    print(
        f"Starting Battle: P0({args.h0}, {args.mode0}, {args.horizon0}) vs P1({args.h1}, {args.mode1}, {args.horizon1})"
    )

    results = []
    p0_wins, p1_wins, draws = 0, 0, 0

    def save_results(results_list, path):
        if not results_list:
            return
        summary = {
            "num_games": len(results_list),
            "p0": {"sims": args.sims0, "h": args.h0, "m": args.mode0, "hr": args.horizon0},
            "p1": {"sims": args.sims1, "h": args.h1, "m": args.mode1, "hr": args.horizon1},
            "p0_wins": sum(1 for r in results_list if r["winner"] == 0),
            "p1_wins": sum(1 for r in results_list if r["winner"] == 1),
            "draws": sum(1 for r in results_list if r["winner"] not in [0, 1]),
            "avg_p0_score": sum(r["p0_score"] for r in results_list) / len(results_list),
            "avg_p1_score": sum(r["p1_score"] for r in results_list) / len(results_list),
            "games": results_list,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f_out:
            json.dump(summary, f_out, indent=2)

    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = []
            for i in range(args.num_games):
                futures.append(
                    executor.submit(
                        run_single_battle,
                        i,
                        args.sims0,
                        args.sims1,
                        args.time0,
                        args.time1,
                        args.h0,
                        args.h1,
                        args.mode0,
                        args.mode1,
                        args.horizon0,
                        args.horizon1,
                        db_content,
                        decks,
                        args.alternate,
                        args.verbose,
                    )
                )

            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Playing"):
                try:
                    res = future.result()
                    results.append(res)

                    # Determine winner string
                    winner_str = "P0 Wins" if res["winner"] == 0 else ("P1 Wins" if res["winner"] == 1 else "Draw")

                    # Print result immediately
                    tqdm.write(
                        f"Game {res['game_id']:2}: {winner_str:8} | P0: {res['p0_score']:2} - P1: {res['p1_score']:2} | Turns: {res['turns']:2}"
                    )

                    if res["winner"] == 0:
                        p0_wins += 1
                    elif res["winner"] == 1:
                        p1_wins += 1
                    else:
                        draws += 1
                except Exception as e:
                    tqdm.write(f"Game failed: {e}")

    except KeyboardInterrupt:
        print("\nInterrupted!")

    if results:
        save_results(results, args.output_file)
        print(f"\nResults Summary: P0 Wins: {p0_wins}, P1 Wins: {p1_wins}, Draws: {draws}")
        print(
            f"Avg Score: P0={sum(r['p0_score'] for r in results) / len(results):.2f}, P1={sum(r['p1_score'] for r in results) / len(results):.2f}"
        )
        print(f"Avg Turns: {sum(r['turns'] for r in results) / len(results):.2f}")
        print(
            f"Avg Sims/Action: P0={sum(r.get('avg_sims_p0', 0) for r in results) / len(results):.0f}, P1={sum(r.get('avg_sims_p1', 0) for r in results) / len(results):.0f}"
        )


if __name__ == "__main__":
    main()
