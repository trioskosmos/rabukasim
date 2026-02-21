import os
import time

import engine_rust


def run_battle():
    # Load DB
    db_path = "data/cards_compiled.json"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)

    # Models
    models = {
        "Original (New)": "original",
        "Simple (Old)": "simple",
    }

    # Battle setup
    contestants = list(models.keys())
    results = {c: {"wins": 0, "games": 0} for c in contestants}

    # Deck setup (Standard starter)
    lives0 = [30000, 30001, 30002]
    deck0 = [
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
        110,
        111,
        112,
        113,
        114,
        115,
        116,
        117,
        118,
        119,
        120,
    ] + lives0
    deck1 = deck0.copy()
    lives1 = lives0.copy()

    print(f"{'Battle':<20} | {'Winner':<20} | {'Duration'}")
    print("-" * 60)

    # Round robin (partial for speed, can adjust)
    for i in range(len(contestants)):
        for j in range(i + 1, len(contestants)):
            p0_name = contestants[i]
            p1_name = contestants[j]

            p0_agent = models[p0_name]
            p1_agent = models[p1_name]

            # Run 1 game
            start = time.time()
            game = engine_rust.PyGameState(db)
            game.initialize_game(deck0, deck1, [], [], lives0, lives1)

            step_count = 0
            while not game.is_terminal() and step_count < 1000:
                curr_p = game.current_player
                phase = game.phase
                turn = game.turn
                agent_name = p0_name if curr_p == 0 else p1_name
                agent = p0_agent if curr_p == 0 else p1_agent

                print(f"\n{'=' * 40}")
                print(f"Step {step_count} | Turn {turn} | Player {curr_p} ({agent_name}) | Phase {phase}")

                # Show Legal Actions
                legal_ids = game.get_legal_action_ids()
                print(f"  Legal Actions ({len(legal_ids)}): {legal_ids}")

                if phase in [-1, 0]:
                    sel = game.get_player(curr_p).mulligan_selection
                    print(f"  Mulligan Selection Mask: {sel:016b}")

                if isinstance(agent, engine_rust.PyHybridMCTS):
                    stats = agent.get_suggestions(game, 0, 0.5)
                else:
                    stats = game.search_mcts(0, 0.5, agent)

                # Show Top 5
                stats.sort(key=lambda x: x[2], reverse=True)
                print("  Top Actions (MCTS Visits/Score):")
                for act, score, visits in stats[:5]:
                    print(f"    - Action {act:<4}: Score {score:.4f}, Visits {visits}")

                # Trace Best Path (Next 3 steps)
                if stats and step_count % 10 == 0:
                    print("  Predicted Best Path (Simulated):")
                    try:
                        # Attempt to use copy() or fallback to manual property copy
                        if hasattr(game, "copy"):
                            temp_game = game.copy()
                        else:
                            temp_game = engine_rust.PyGameState(db)
                            temp_game.current_player = game.current_player
                            temp_game.first_player = game.first_player
                            temp_game.phase = game.phase
                            temp_game.turn = game.turn
                            temp_game.set_player(0, game.get_player(0))
                            temp_game.set_player(1, game.get_player(1))

                        path_str = []
                        trace_curr = temp_game
                        for depth in range(3):
                            p = trace_curr.current_player
                            ph = trace_curr.phase
                            t = trace_curr.turn
                            # For the first step, use the MCTS top action
                            if depth == 0:
                                best_act = stats[0][0]
                            else:
                                # Quick MCTS search for lookahead (100 sims)
                                t_stats = trace_curr.search_mcts(100, 0.0, "original")
                                if not t_stats:
                                    break
                                t_stats.sort(key=lambda x: x[2], reverse=True)
                                best_act = t_stats[0][0]

                            path_str.append(f"[T{t} P{p} Ph{ph} Act{best_act}]")
                            trace_curr.step(best_act)
                            if trace_curr.is_terminal():
                                break
                        print(f"    {' -> '.join(path_str)}")
                    except Exception as e:
                        print(f"    (Path trace failed: {e})")

                action = stats[0][0] if stats else 0
                game.step(action)
                step_count += 1

                # Check for progress
                if step_count % 10 == 0:
                    p0 = game.get_player(0)
                    p1 = game.get_player(1)
                    print(
                        f"--- P0: Lives {len(p0.success_lives)}, Hand {len(p0.hand)} | P1: Lives {len(p1.success_lives)}, Hand {len(p1.hand)}"
                    )

            winner_idx = game.get_winner()
            winner_name = "Draw"
            if winner_idx == 0:
                winner_name = p0_name
                results[p0_name]["wins"] += 1
            elif winner_idx == 1:
                winner_name = p1_name
                results[p1_name]["wins"] += 1

            results[p0_name]["games"] += 1
            results[p1_name]["games"] += 1

            elapsed = time.time() - start
            print(f"{p0_name} vs {p1_name:<10} | {winner_name:<20} | {elapsed:.1f}s")

    print("\nFinal Scoreboard:")
    for name, stats in results.items():
        wr = (stats["wins"] / stats["games"] * 100) if stats["games"] > 0 else 0
        print(f"{name:<20}: {stats['wins']}/{stats['games']} ({wr:.1f}% Win Rate)")


if __name__ == "__main__":
    run_battle()
