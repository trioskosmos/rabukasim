import json
import sys
import time
from pathlib import Path

import engine_rust

# Add project root for engine imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from engine.game.deck_utils import UnifiedDeckParser


def load_tournament_decks(full_db):
    decks_dir = Path(__file__).parent.parent.parent / "ai" / "decks"
    parser = UnifiedDeckParser(full_db)
    loaded_decks = []

    standard_energy_ids = []
    for cid, data in parser.normalized_db.items():
        if data.get("type") == "Energy" or str(cid).startswith("LL-E"):
            standard_energy_ids.append(data.get("card_id"))
            if len(standard_energy_ids) >= 12:
                break

    for deck_file in decks_dir.glob("*.txt"):
        with open(deck_file, "r", encoding="utf-8") as f:
            content = f.read()
        results = parser.extract_from_content(content)
        if not results:
            continue
        d = results[0]
        members, lives, energy = [], [], []
        for code in d["main"]:
            cdata = parser.resolve_card(code)
            if not cdata:
                continue
            if cdata.get("type") == "Member":
                members.append(cdata["card_id"])
            elif cdata.get("type") == "Live":
                lives.append(cdata["card_id"])
        for code in d["energy"]:
            cdata = parser.resolve_card(code)
            if cdata:
                energy.append(cdata["card_id"])

        if len(members) >= 48 and len(lives) >= 12:
            loaded_decks.append(
                {
                    "name": deck_file.stem,
                    "members": (members + members * 4)[:48],
                    "lives": (lives + lives * 4)[:12],
                    "energy": (energy + standard_energy_ids * 12)[:12],
                }
            )
    return loaded_decks


def run_compare():
    print("--- Heuristic Comparison Audit (Original vs Legacy) ---")

    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)

    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    tournament_decks = load_tournament_decks(full_db)

    d0 = tournament_decks[0]
    d1 = tournament_decks[1]

    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True

    print("Advancing game to SECOND Live success...")
    success_count = 0
    max_turns = 200
    last_turn = -1

    while not state.is_terminal() and state.turn < max_turns:
        phase_names = [
            "MullP1",
            "MullP2",
            "Active",
            "Energy",
            "Draw",
            "Main",
            "LiveSet",
            "PerfP1",
            "PerfP2",
            "LiveRes",
            "Terminal",
            "Resp",
            "Setup",
        ]
        ph = phase_names[state.phase + 1] if -1 <= state.phase <= 11 else f"P{state.phase}"

        if state.turn != last_turn:
            print(f"Turn {state.turn} {ph} (Successes: {success_count})")
            last_turn = state.turn

        p0 = state.get_player(0)
        p1 = state.get_player(1)

        current_success = len(p0.success_lives) + len(p1.success_lives)
        if current_success > success_count:
            success_count = current_success
            print(f"!!! SUCCESS {success_count} !!! reached at Turn {state.turn}")
            if success_count >= 2:
                break

        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            state.auto_step(db_engine)
            continue

        # Use Original with MORE sims to advance faster/smarter
        s_mode = engine_rust.EvalMode.Normal
        sugg = state.get_mcts_suggestions(128, 0.0, engine_rust.SearchHorizon.GameEnd(), s_mode)
        action = sugg[0][0] if sugg else legal_ids[0]
        state.step(action)
        state.auto_step(db_engine)

    print(f"\n--- BENCHMARK AT Turn {state.turn}, Phase {state.phase} ---")

    # 1. Compare Speed (Evaluations per second)
    iterations = 5000

    # Original
    start = time.time()
    for _ in range(iterations):
        _ = state.evaluate(0, 0, 0)  # 0 maps to Original in py_bindings.rs
    t_original = time.time() - start

    # Legacy
    start = time.time()
    for _ in range(iterations):
        _ = state.evaluate(1, 0, 0)  # 1 maps to Legacy in py_bindings.rs
    t_legacy = time.time() - start

    print(f"Original Heuristic: {iterations} evals in {t_original:.3f}s ({iterations / t_original:.0f} evals/sec)")
    print(f"Legacy Heuristic:   {iterations} evals in {t_legacy:.3f}s ({iterations / t_legacy:.0f} evals/sec)")
    print(f"Speed Delta: {((t_original / t_legacy) - 1) * 100:+.1f}% (Original is slower if +, faster if -)")

    # 2. Compare Scores
    score_orig = state.evaluate(0, 0, 0)
    score_legacy = state.evaluate(1, 0, 0)
    print(f"\nRaw Evaluation Scores (Player {state.current_player} perspective):")
    print(f"  Original Score: {score_orig:.4f}")
    print(f"  Legacy Score:   {score_legacy:.4f}")

    # 3. Compare MCTS Suggestions (1000 sims)
    print("\nMCTS Suggestions (1000 sims):")

    print("Running MCTS with Original Heuristic...")
    s_orig = state.search_mcts(
        1000, 0.0, "original", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None
    )

    print("Running MCTS with Legacy Heuristic...")
    s_legacy = state.search_mcts(
        1000, 0.0, "legacy", engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal, None
    )

    def format_top_3(sugg):
        lines = []
        for i in range(min(3, len(sugg))):
            lbl = state.get_action_label(sugg[i][0])
            lines.append(f"    {i + 1}. {lbl} (Q: {sugg[i][1]:.3f}, N: {sugg[i][2]})")
        return "\n".join(lines)

    print(f"\nTop 3 Suggestions (Original):\n{format_top_3(s_orig)}")
    print(f"\nTop 3 Suggestions (Legacy):\n{format_top_3(s_legacy)}")

    # Save Log
    log = [
        f"Benchmark at Turn {state.turn}, Player {state.current_player}",
        f"Original Speed: {iterations / t_original:.0f} evals/sec",
        f"Legacy Speed:   {iterations / t_legacy:.0f} evals/sec",
        f"Original Score: {score_orig:.4f}",
        f"Legacy Score:   {score_legacy:.4f}",
        "\nTop Original Move:",
        state.get_action_label(s_orig[0][0]),
        "\nTop Legacy Move:",
        state.get_action_label(s_legacy[0][0]),
    ]
    with open("heuristic_comparison_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))


if __name__ == "__main__":
    run_compare()
