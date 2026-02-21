import argparse
import json
import os
import random
import re
import sys

# Add current dir to path to find engine_rust.pyd
sys.path.append(os.getcwd())

import engine_rust


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
        if "-PE" in norm_no:
            norm_no = norm_no.split("-PE")[0] + "-PE"

        cid = card_map.get(norm_no)
        if cid is not None:
            is_energy = False
            if str(cid) in energy_db:
                is_energy = True
            else:
                cdata = member_db.get(str(cid)) or live_db.get(str(cid))
                if cdata and ("PE" in str(cdata.get("rare", "")) or "Energy" in cdata.get("name", "")):
                    is_energy = True

            if is_energy:
                energy_ids.extend([cid] * int(qty))
            else:
                main_ids.extend([cid] * int(qty))

    return main_ids, energy_ids


def run_fight():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10, help="Games per deck")
    parser.add_argument("--sims", type=int, default=100, help="MCTS simulations")
    args = parser.parse_args()

    ai_config = load_ai_weights()

    # Load cards
    cards_path = "data/cards_compiled.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        cards_json = json.dumps(data)

    card_map = {}
    for cid, cdata in data.get("member_db", {}).items():
        cno = cdata["card_no"].strip().replace("＋", "+")
        if "-PE" in cno:
            cno = cno.split("-PE")[0] + "-PE"
        card_map[cno] = int(cid)
    for cid, cdata in data.get("live_db", {}).items():
        cno = cdata["card_no"].strip().replace("＋", "+")
        card_map[cno] = int(cid)
    for cid, cdata in data.get("energy_db", {}).items():
        cno = cdata["card_no"].strip().replace("＋", "+")
        if "-PE" in cno:
            cno = cno.split("-PE")[0] + "-PE"
        card_map[cno] = int(cid)

    db = engine_rust.PyCardDatabase(cards_json)

    deck_folder = "ai/decks"
    deck_files = ["muse_cup.txt", "aqours_cup.txt", "nijigaku_cup.txt"]

    stats = {"Greedy_Wins": 0, "MCTS_Wins": 0, "Draws": 0, "Greedy_Turns": [], "MCTS_Turns": []}

    print(f"Starting Fight: Greedy vs MCTS {args.sims}")

    for deck_file in deck_files:
        path = os.path.join(deck_folder, deck_file)
        main_ids, energy_ids = parse_deck(path, card_map, data)
        if not energy_ids:
            energy_ids = [40001] * 12

        print(f"  Deck: {deck_file}")
        for i in range(args.games):
            state = engine_rust.PyGameState(db)
            state.initialize_game(main_ids, main_ids, energy_ids, energy_ids, [], [])
            state.silent = True

            # P0 is Greedy, P1 is MCTS in even games
            # P0 is MCTS, P1 is Greedy in odd games
            mcts_player = i % 2

            loop_limit = 1000
            for _ in range(loop_limit):
                if state.phase == 9:
                    break

                # Intelligent actor selection
                p0_legal = state.get_legal_action_ids_for_player(0)
                p1_legal = state.get_legal_action_ids_for_player(1)

                acting_p = state.current_player
                if not p0_legal and p1_legal:
                    acting_p = 1
                elif not p1_legal and p0_legal:
                    acting_p = 0

                legal_ids = p0_legal if acting_p == 0 else p1_legal
                if not legal_ids:
                    # If nobody can act, force a pass or try to advance (shouldn't happen)
                    break

                # If it's the MCTS player's turn, use MCTS
                if acting_p == mcts_player and state.phase >= 1:
                    suggestions = state.get_mcts_suggestions_with_config(args.sims, config=ai_config)
                    action = suggestions[0][0] if suggestions else 0
                elif state.phase == -3:  # RPS
                    action = random.choice(legal_ids)
                else:  # Greedy
                    action = state.get_greedy_action(db, acting_p, 0, config=ai_config)

                state.step(action)

            winner = state.get_winner()
            if winner == -1:
                stats["Draws"] += 1
            elif winner == mcts_player:
                stats["MCTS_Wins"] += 1
                stats["MCTS_Turns"].append(state.turn)
            else:
                stats["Greedy_Wins"] += 1
                stats["Greedy_Turns"].append(state.turn)

            print(".", end="", flush=True)
        print(" Done.")

    print("\n" + "=" * 60)
    print("FIGHT REPORT: GREEDY vs MCTS " + str(args.sims))
    print("=" * 60)
    total_games = stats["Greedy_Wins"] + stats["MCTS_Wins"] + stats["Draws"]
    print(f"Total Games : {total_games}")
    print(f"MCTS Wins   : {stats['MCTS_Wins']} ({stats['MCTS_Wins'] / total_games * 100:.1f}%)")
    print(f"Greedy Wins : {stats['Greedy_Wins']} ({stats['Greedy_Wins'] / total_games * 100:.1f}%)")
    print(f"Draws       : {stats['Draws']}")

    if stats["MCTS_Turns"]:
        print(f"MCTS Avg Turns   : {sum(stats['MCTS_Turns']) / len(stats['MCTS_Turns']):.1f}")
    if stats["Greedy_Turns"]:
        print(f"Greedy Avg Turns : {sum(stats['Greedy_Turns']) / len(stats['Greedy_Turns']):.1f}")


if __name__ == "__main__":
    run_fight()
