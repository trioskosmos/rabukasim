import json
import os
import re
import sys

# Add current dir to path to find engine_rust.pyd
sys.path.append(os.getcwd())

import engine_rust


def normalize_cno(cno):
    if not cno:
        return ""
    return cno.strip().replace("＋", "+").replace("++", "+")  # Handle double plus just in case


def load_ai_weights():
    weights_path = "data/ai_weights.json"
    if os.path.exists(weights_path):
        with open(weights_path, "r") as f:
            weights_data = json.load(f)

        config = engine_rust.HeuristicConfig()
        for key, value in weights_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    return engine_rust.HeuristicConfig()


def parse_deck(path, card_map, data):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    main_ids = []  # 48 Members + 12 Lives = 60
    energy_ids = []  # 12 Energy

    matches = re.findall(r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)", content)
    if not matches:
        matches = re.findall(r"(\d+)\s*[xX]\s*([A-Za-z0-9!+\-＋]+)", content)
        matches = [(m[1], m[0]) for m in matches]

    member_db = data.get("member_db", {})
    live_db = data.get("live_db", {})
    energy_db = data.get("energy_db", {})

    for cno, qty in matches:
        norm_no = cno.strip().replace("＋", "+").replace("++", "+")
        # Strip everything after 'PE' for energy cards
        if "-PE" in norm_no:
            norm_no = norm_no.split("-PE")[0] + "-PE"

        cid = card_map.get(norm_no)
        # Fallback for energy
        if cid is None and "-PE+" in norm_no:
            cid = card_map.get(norm_no.replace("+", ""))

        if cid is not None:
            is_energy = False
            if str(cid) in energy_db:
                is_energy = True
            else:
                cdata = member_db.get(str(cid)) or live_db.get(str(cid))
                if cdata:
                    rare = str(cdata.get("rare", ""))
                    if "PE" in rare or "Energy" in cdata.get("name", "") or "-PE" in norm_no:
                        is_energy = True

            if is_energy:
                energy_ids.extend([cid] * int(qty))
            else:
                main_ids.extend([cid] * int(qty))

    return main_ids, energy_ids


def run_benchmark():
    ai_config = load_ai_weights()

    # Load cards
    cards_path = "data/cards_compiled.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        cards_json = json.dumps(data)

    card_map = {}
    for cid, cdata in data.get("member_db", {}).items():
        cno = cdata["card_no"].strip().replace("＋", "+").replace("++", "+")
        if "-PE" in cno:
            cno = cno.split("-PE")[0] + "-PE"
        card_map[cno] = int(cid)
    for cid, cdata in data.get("live_db", {}).items():
        cno = cdata["card_no"].strip().replace("＋", "+").replace("++", "+")
        card_map[cno] = int(cid)
    for cid, cdata in data.get("energy_db", {}).items():
        cno = cdata["card_no"].strip().replace("＋", "+").replace("++", "+")
        if "-PE" in cno:
            cno = cno.split("-PE")[0] + "-PE"
        card_map[cno] = int(cid)

    db = engine_rust.PyCardDatabase(cards_json)

    deck_folder = "ai/decks"
    deck_files = ["aqours_cup.txt", "hasunosora_cup.txt", "liella_cup.txt", "muse_cup.txt", "nijigaku_cup.txt"]

    results = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10, help="Games to play per deck")
    parser.add_argument("--mcts", action="store_true", help="Use MCTS instead of greedy")
    parser.add_argument("--sims", type=int, default=100, help="MCTS simulations per move")
    args = parser.parse_args()

    games_per_deck = args.games

    print(f"Starting Benchmark: {len(deck_files) * games_per_deck} Games ({games_per_deck} per deck)")

    for deck_file in deck_files:
        path = os.path.join(deck_folder, deck_file)
        main_ids, energy_ids = parse_deck(path, card_map, data)

        print(f"  Testing deck: {deck_file} (Main:{len(main_ids)}, Energy:{len(energy_ids)})...", end="", flush=True)

        deck_results = []
        for i in range(games_per_deck):
            state = engine_rust.PyGameState(db)
            state.initialize_game(main_ids, main_ids, energy_ids, energy_ids, [], [])
            state.silent = True

            loop_limit = 2000
            for _ in range(loop_limit):
                if state.phase == 9:
                    break

                # Intelligent actor selection
                p0_legal = state.get_legal_action_ids_for_player(0)
                p1_legal = state.get_legal_action_ids_for_player(1)

                acting_p = state.current_player
                if acting_p == 0:
                    if not p0_legal and p1_legal:
                        acting_p = 1
                else:
                    if not p1_legal and p0_legal:
                        acting_p = 0

                if args.mcts:
                    suggestions = state.get_mcts_suggestions_with_config(args.sims, config=ai_config)
                    action = suggestions[0][0] if suggestions else 0
                else:
                    action = state.get_greedy_action(db, acting_p, 0, config=ai_config)
                state.step(action)

            p0 = state.get_player(0)
            p1 = state.get_player(1)

            deck_results.append(
                {
                    "turn": state.turn,
                    "winner": state.get_winner(),
                    "score0": p0.score,
                    "score1": p1.score,
                    "lives0": len(p0.success_lives),
                    "lives1": len(p1.success_lives),
                }
            )

        print(" Done.")
        results.append((deck_file, deck_results))

    # Analysis
    print("\n" + "=" * 60)
    print("BENCHMARK REPORT")
    print("=" * 60)

    total_turns = []
    total_scores = []

    for deck_name, res_list in results:
        turns = [r["turn"] for r in res_list]
        scores = [max(r["score0"], r["score1"]) for r in res_list]
        lives = [max(r["lives0"], r["lives1"]) for r in res_list]

        avg_turn = sum(turns) / len(turns)
        avg_score = sum(scores) / len(scores)
        avg_lives = sum(lives) / len(lives)

        print(f"Deck: {deck_name}")
        print(f"  Turn Range: {min(turns)} - {max(turns)} (Avg: {avg_turn:.1f})")
        print(f"  Score Range: {min(scores)} - {max(scores)} (Avg: {avg_score:.1f})")
        print(f"  Lives Range: {min(lives)} - {max(lives)} (Avg: {avg_lives:.1f})")

        total_turns.extend(turns)
        total_scores.extend(scores)

    print("\nOVERALL (100 Games)")
    print(f"  Global Turn Range: {min(total_turns)} - {max(total_turns)} (Avg: {sum(total_turns) / 100:.1f})")
    print(f"  Global Score Range: {min(total_scores)} - {max(total_scores)} (Avg: {sum(total_scores) / 100:.1f})")


if __name__ == "__main__":
    run_benchmark()
