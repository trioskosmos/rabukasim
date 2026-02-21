import argparse
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
    # Strip everything after 'PE' for energy cards to be safe
    if "-PE" in cno:
        cno = cno.split("-PE")[0] + "-PE"
    return cno.strip().replace("＋", "+").replace("++", "+")


def parse_deck_debug(path, card_map, data):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    main_ids = []  # 48 Members + 12 Lives = 60
    energy_ids = []  # 12 Energy

    # Normalize entire content for safety? No, line by line is better
    matches = re.findall(r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)", content)
    if not matches:
        matches = re.findall(r"(\d+)\s*[xX]\s*([A-Za-z0-9!+\-＋]+)", content)
        matches = [(m[1], m[0]) for m in matches]

    member_db = data.get("member_db", {})
    live_db = data.get("live_db", {})
    energy_db = data.get("energy_db", {})

    for cno, qty in matches:
        norm_no = normalize_cno(cno)
        cid = card_map.get(norm_no)

        # Fallback for energy: if not found by exact norm, try without +
        if cid is None and "-PE+" in norm_no:
            cid = card_map.get(norm_no.replace("+", ""))
            if cid:
                norm_no = norm_no.replace("+", "")

        if cid is not None:
            # Check if it's an Energy card
            is_energy = False
            # Check Energy DB first!
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
        else:
            print(f"    WARNING: Card not found: {norm_no} (Original: {cno})")

    return main_ids, energy_ids


def run_debug_game():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true", help="Save log to file")
    parser.add_argument("--mcts", action="store_true", help="Use MCTS instead of greedy")
    parser.add_argument("--sims", type=int, default=1000, help="MCTS simulations")
    args = parser.parse_args()
    log_file = open("debug_game_log.txt", "w", encoding="utf-8")

    def flog(msg):
        print(msg)
        log_file.write(msg + "\n")

    # Load cards
    cards_path = "data/cards_compiled.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        cards_json = json.dumps(data)

    card_map = {}
    for cid, cdata in data.get("member_db", {}).items():
        card_map[normalize_cno(cdata["card_no"])] = int(cid)
    for cid, cdata in data.get("live_db", {}).items():
        card_map[normalize_cno(cdata["card_no"])] = int(cid)
    for cid, cdata in data.get("energy_db", {}).items():
        card_map[normalize_cno(cdata["card_no"])] = int(cid)

    # Print some available cards for debugging
    flog(f"Sample Card Map Keys: {list(card_map.keys())[:20]}")
    target_search = normalize_cno("PL!S-bp3-029-PE＋")
    flog(f"Search for {repr(target_search)}: {card_map.get(target_search)}")

    db = engine_rust.PyCardDatabase(cards_json)

    # Load Aqours deck
    deck_path = "ai/decks/aqours_cup.txt"
    main_ids, energy_ids = parse_deck_debug(deck_path, card_map, data)

    if not main_ids:
        flog("ERROR: DECK IS EMPTY AFTER PARSING. CHECK CARD NUMBERS.")
        return

    flog("Deck Info:")
    flog(f"  Main Deck: {len(main_ids)} cards")
    flog(f"  Energy Deck: {len(energy_ids)} cards")

    # Load AI weights
    ai_config = engine_rust.HeuristicConfig()
    weights_path = "data/ai_weights.json"
    if os.path.exists(weights_path):
        with open(weights_path, "r") as f:
            w = json.load(f)
            for k, v in w.items():
                if hasattr(ai_config, k):
                    setattr(ai_config, k, v)

    state = engine_rust.PyGameState(db)
    state.initialize_game(main_ids, main_ids, energy_ids, energy_ids, [], [])
    state.silent = False  # ENABLE LOGGING

    flog("\n--- Starting Verbose Game Trace ---")

    loop_limit = 500
    for i in range(loop_limit):
        if state.phase == 9:
            flog("Terminal Phase reached.")
            break

        # Get legal actions for both players
        p0_legal = state.get_legal_action_ids_for_player(0)
        p1_legal = state.get_legal_action_ids_for_player(1)

        if not p0_legal and not p1_legal:
            if state.phase == 9:
                break
            flog(f"  [STALL] No legal actions for either player at Turn {state.turn} Phase {state.phase}")
            break

        # Decide who acts
        acting_p = state.current_player
        if acting_p == 0:
            if not p0_legal and p1_legal:
                acting_p = 1
        else:
            if not p1_legal and p0_legal:
                acting_p = 0

        legal_ids = p0_legal if acting_p == 0 else p1_legal

        # [COMPARISON] Perform comparison at Turn 1 Main Phase for Player 0
        if state.turn == 1 and state.phase == 4 and acting_p == 0:
            flog("\n[COMPARISON] Turn 1 Main Phase - Greedy vs MCTS")

            # Greedy
            g_evals = state.get_greedy_evaluations(db, acting_p, 0, config=ai_config)
            g_evals.sort(key=lambda x: x[1], reverse=True)
            flog("  [Greedy] Top 5:")
            for act, sc in g_evals[:5]:
                flog(f"    Action {act}: {sc:.4f}")

            # MCTS
            flog(f"  [MCTS] Running {args.sims} simulations...")
            m_evals = state.get_mcts_suggestions_with_config(args.sims, config=ai_config)
            flog("  [MCTS] Top 5:")
            for act, val, visits in m_evals[:5]:
                flog(f"    Action {act}: {val:.4f} (Visits: {visits})")

            flog("[COMPARISON] End\n")

        if args.mcts and state.phase >= 1:  # Only MCTS during actual gameplay (Active, Energy, Draw, Main, etc.)
            suggestions = state.get_mcts_suggestions_with_config(args.sims, config=ai_config)
            action = suggestions[0][0] if suggestions else 0
            flog(f"  [MCTS] Top Suggestion: {action} (Value: {suggestions[0][1] if suggestions else 'N/A'})")
        elif state.phase == -3:  # RPS Phase
            import random

            action = random.choice(legal_ids) if legal_ids else 0
            flog(f"  [RPS] Randomly choosing: {action}")
        else:
            action = state.get_greedy_action(db, acting_p, 0, config=ai_config)

        # Log state summary
        p0 = state.get_player(0)
        p1 = state.get_player(1)
        flog(f"[Step {i}] Turn {state.turn} Phase {state.phase} Player {state.current_player} (Acting: {acting_p})")
        flog(
            f"  P0 Hand:{len(p0.hand)} Energy:{len(p0.energy_deck)}/{len(p0.energy_zone)} (T:{sum(p0.tapped_energy)}) Stage:{p0.stage} Score:{p0.score}"
        )
        flog(
            f"  P1 Hand:{len(p1.hand)} Energy:{len(p1.energy_deck)}/{len(p1.energy_zone)} (T:{sum(p1.tapped_energy)}) Stage:{p1.stage} Score:{p1.score}"
        )
        flog(f"  Legal Actions ({len(legal_ids)}): {legal_ids[:20]}...")
        flog(f"  AI chooses Action: {action}")

        # Step
        state.step(action)

        # Print rule logs for this step
        try:
            logs = state.rule_log
            if logs:
                for l in logs:
                    flog(f"  LOG: {l}")
                state.clear_rule_log()
        except:
            pass

    flog("\n--- Game Over ---")
    p0 = state.get_player(0)
    p1 = state.get_player(1)
    flog(f"Winner: {state.get_winner()}")
    flog(
        f"Final Scores: P0:{p0.score} (Lives:{len(p0.success_lives)}) vs P1:{p1.score} (Lives:{len(p1.success_lives)})"
    )
    log_file.close()


if __name__ == "__main__":
    run_debug_game()
