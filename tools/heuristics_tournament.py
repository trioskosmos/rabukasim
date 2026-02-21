import json
import os
import re
import sys

# Add current dir to path to find engine_rust.pyd
sys.path.append(os.getcwd())

try:
    import engine_rust

    print(f"DEBUG: Loaded engine_rust from {engine_rust.__file__}")
    print(f"DEBUG: get_greedy_evaluations present: {'get_greedy_evaluations' in dir(engine_rust.PyGameState)}")
except ImportError:
    print("Error: engine_rust.pyd not found. Make sure you copied it from target/release.")
    sys.exit(1)


def load_ai_weights():
    weights_path = "data/ai_weights.json"
    if os.path.exists(weights_path):
        with open(weights_path, "r") as f:
            weights_data = json.load(f)

        config = engine_rust.HeuristicConfig()
        # Map JSON fields to config object
        for key, value in weights_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    return None


def run_tournament(args):
    is_test = args.test
    ai_config = load_ai_weights()
    if ai_config and not is_test:
        print("DEBUG: Loaded AI Weights from data/ai_weights.json")

    # Load cards to get valid IDs
    cards_path = "engine/data/cards_compiled.json"
    if not os.path.exists(cards_path):
        cards_path = "data/cards_compiled.json"

    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        cards_json = json.dumps(data)

    # Load card_no -> card_id map
    card_map = {}
    for cid, cdata in data["member_db"].items():
        card_map[cdata["card_no"]] = int(cid)
    for cid, cdata in data["live_db"].items():
        card_map[cdata["card_no"]] = int(cid)

    # Add mapping for + vs ＋
    for k in list(card_map.keys()):
        if "+" in k:
            card_map[k.replace("+", "＋")] = card_map[k]
        if "＋" in k:
            card_map[k.replace("＋", "+")] = card_map[k]

    # Load Decks from ai/decks
    deck_folder = "ai/decks"
    curated_decks = {}

    # In test mode, only use one deck
    deck_files = os.listdir(deck_folder)
    if is_test:
        deck_files = [f for f in deck_files if "muse" in f]  # Just muse for test

    for fname in deck_files:
        if fname.endswith(".txt") and fname != "verify_decks.py":
            path = os.path.join(deck_folder, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple text parser for ID x Qty or Qty x ID
            main_ids = []
            # Pattern 1: ID x Qty
            matches = re.findall(r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)", content)
            if not matches:
                # Pattern 2: Qty x ID
                matches = re.findall(r"(\d+)\s*[xX]\s*([A-Za-z0-9!+\-＋]+)", content)
                matches = [(m[1], m[0]) for m in matches]

            for cno, qty in matches:
                cid = card_map.get(cno.strip())
                if cid is not None:
                    main_ids.extend([cid] * int(qty))
                else:
                    # Try to handle common typos or variations if needed
                    pass

            if main_ids:
                # Use mixed deck as per Rule 2.0 (lives are in main deck)
                curated_decks[fname] = (main_ids, [])
                if not is_test:
                    print(f"Loaded {fname}: {len(main_ids)} cards (Mixed Members/Lives).")

    if not is_test:
        print("Loading database engine...", end="", flush=True)
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "cards_compiled.json")
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)
    if not is_test:
        print(f" Done. (Members: {db.member_count}, Lives: {db.live_count})")

    # Matchups: (Label, P0 Heuristic ID, P1 Heuristic ID)
    # 0 = Original (New Probabilistic), 1 = Simple, 2 = Legacy (Old Heuristic)
    matchup_configs = [
        ("New vs Legacy", 0, 2),
        ("New vs Simple", 0, 1),
    ]

    games_per_deck = 1 if is_test else 10
    p0_sims = 100
    p1_sims = 100

    print("=" * 60)
    if is_test:
        print("TOURNAMENT DRY RUN - VERIFYING DECKS AND LOGIC")
    else:
        print("CURATED DECK TOURNAMENT")
        print("Comparing AI Strategies on Real Decks")
    print(f"Games per Deck: {games_per_deck}")
    print(f"MCTS Simulations: {p0_sims} per move")
    print("=" * 60)

    # Debug Mode: Show one game with full logs
    if getattr(args, "debug", False):
        print("\n" + "!" * 60)
        print("DEBUG MODE: LOGGING ONE GAME")
        print("!" * 60)

        deck_name = list(curated_decks.keys())[0]
        m_list, l_list = curated_decks[deck_name]

        print(f"Initializing game with deck: {deck_name}...", flush=True)
        state = engine_rust.PyGameState(db)
        state.initialize_game(m_list, m_list, [], [], l_list, l_list)
        print("initialize_game returned.", flush=True)
        state.silent = False

        print("Entering main loop...", flush=True)
        with open("debug_game.log", "w", encoding="utf-8") as f:
            f.write(f"Starting Debug Game with Deck: {deck_name}\n")

            loop_limit = 500
            for i in range(loop_limit):
                if state.phase == 9:  # Terminal
                    print("\nTERMINAL REACHED")
                    f.write("\nTERMINAL REACHED\n")
                    break

                print(
                    f"\n[Move {i + 1}] Turn: {state.turn} Phase: {state.phase} Player: {state.current_player}...",
                    flush=True,
                )

                for p_idx in [0, 1]:
                    p = state.get_player(p_idx)
                    print(
                        f"    P{p_idx}: Hand={len(p.hand)} Deck={len(p.deck)} Energy={len(p.energy_zone)} Stage={p.stage} Score={p.score}",
                        flush=True,
                    )

                # Use Original Heuristic (ID 0) for debugging
                print("  Calculating action evaluations...", flush=True)

                evals = state.get_greedy_evaluations(db, 0, config=ai_config)
                # Sort by score descending
                evals.sort(key=lambda x: x[1], reverse=True)

                top_10 = evals[:10]
                action = top_10[0][0] if top_10 else 0

                print(f"  Selected Action: {action} (Score: {top_10[0][1]:.4f})", flush=True)

                f.write(
                    f"\n[Move {i + 1}] Turn: {state.turn} Phase: {state.phase} Player: {state.current_player} Action: {action}\n"
                )

                # Log top 10 actions to file
                f.write("  Top 10 Scored Actions:\n")
                for act_id, score in top_10:
                    f.write(f"    Action {act_id:4}: {score:.4f}\n")

                for p_idx in [0, 1]:
                    p = state.get_player(p_idx)
                    line = f"  P{p_idx}: Score={p.score} Hand={len(p.hand)} Deck={len(p.deck)} Energy={len(p.energy_zone)} Stage={p.stage} Success={len(p.success_lives)}\n"
                    f.write(line)
                    # If Main or LiveSet, log bit more
                    if state.phase in [4, 5]:
                        f.write(f"    Hand IDs: {list(p.hand)[:10]}...\n")
                        f.write(f"    Live Zone: {list(p.live_zone)}\n")

                print(f"  Stepping action {action}...", flush=True)
                state.step(action)
                print("  Step complete.", flush=True)

            f.write(f"\nFinal Result: {state.get_winner()} in {state.turn} turns.\n")

        print("\nDebug loop completed. Log written to debug_game.log", flush=True)
        return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run a single-game dry run")
    parser.add_argument("--debug", action="store_true", help="Run one verbose game and exit")
    args = parser.parse_args()

    run_tournament(args)
