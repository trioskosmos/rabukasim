import json
import os
import sys

# Add current dir to path to find engine_rust.pyd
sys.path.append(os.getcwd())
import engine_rust


def compare_turn_1():
    # Load cards
    cards_path = "data/cards_compiled.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        cards_json = json.dumps(data)

    db = engine_rust.PyCardDatabase(cards_json)

    # Load a standard deck
    def load_deck(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        card_map = {}
        for cid, cdata in data.get("member_db", {}).items():
            card_map[cdata["card_no"]] = int(cid)
        for cid, cdata in data.get("live_db", {}).items():
            card_map[cdata["card_no"]] = int(cid)
        for cid, cdata in data.get("energy_db", {}).items():
            card_map[cdata["card_no"]] = int(cid)

        main_ids = []
        energy_ids = []
        for line in lines:
            if " x " in line:
                cno, qty = line.strip().split(" x ")
                cid = card_map.get(cno.strip())
                if cid:
                    if str(cid) in data.get("energy_db", {}):
                        energy_ids.extend([cid] * int(qty))
                    else:
                        main_ids.extend([cid] * int(qty))
        return main_ids, energy_ids

    main_ids, energy_ids = load_deck("ai/decks/aqours_cup.txt")

    state = engine_rust.PyGameState(db)
    state.initialize_game(main_ids, main_ids, energy_ids, energy_ids, [], [])
    state.silent = True

    # Skip setup to Turn 1 Main Phase
    # We'll step manually to reach a meaningful decision point
    while state.phase < 4:  # Main Phase
        p_ids = state.get_legal_action_ids_for_player(state.current_player)
        if not p_ids:
            break
        state.step(p_ids[0])

    print(f"\n--- Comparison at Turn {state.turn} Phase {state.phase} ---")
    p0 = state.get_player(0)
    print(f"P0 Hand: {len(p0.hand)} cards")

    ai_config = engine_rust.HeuristicConfig()

    # 1. Greedy Evaluation
    greedy_evals = state.get_greedy_evaluations(db, 0, 0, config=ai_config)
    greedy_evals.sort(key=lambda x: x[1], reverse=True)

    print("\n[Greedy] Top 5 Actions:")
    for action, score in greedy_evals[:5]:
        print(f"  Action {action}: Score {score:.4f}")

    # 2. MCTS Evaluation (Higher Sims for clarity)
    sims = 1000
    mcts_suggestions = state.get_mcts_suggestions_with_config(sims, config=ai_config)

    print(f"\n[MCTS] Top 5 Actions ({sims} sims):")
    for action, score, visits in mcts_suggestions[:5]:
        print(f"  Action {action}: Value {score:.4f} (Visits: {visits})")


if __name__ == "__main__":
    compare_turn_1()
