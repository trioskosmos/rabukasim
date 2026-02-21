import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.utils.benchmark_decks import parse_deck


def monitor_game():
    db_path = "engine/data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)
    db = engine_rust.PyCardDatabase(db_content)

    # Use simple starter decks
    p_deck = [124, 127] * 20
    p_lives = [1024, 1025, 1027]
    p_energy = [20000] * 10

    # Setup Agents
    game = engine_rust.PyGameState(db)

    # Setup Decks (Need correct structure)
    deck0, lives0, energy0 = parse_deck(
        "ai/decks/aqours_cup.txt", db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})
    )
    deck1, lives1, energy1 = parse_deck(
        "ai/decks/muse_cup.txt", db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})
    )

    game.initialize_game(deck0, deck1, energy0, energy1, lives0, lives1)

    # Setup Agents
    mcts = engine_rust.PyHybridMCTS("ai/models/alphanet.onnx", 0.3)

    def decode_action(aid, game_p):
        if aid == 0:
            return "Pass/Confirm"
        if 1 <= aid <= 180:
            rel = aid - 1
            h_idx = rel // 3
            s_idx = rel % 3
            if h_idx < len(game_p.hand):
                cid = game_p.hand[h_idx]
                c_name = db_json["member_db"].get(str(cid), {}).get("name", "Unknown")
                return f"Play {c_name} to Slot {s_idx}"
        if 200 <= aid <= 230:
            rel = aid - 200
            s_idx = rel // 10
            return f"Activate Ability on Slot {s_idx}"
        if 300 <= aid <= 360:
            h_idx = aid - 300
            if h_idx < len(game_p.hand):
                cid = game_p.hand[h_idx]
                c_name = db_json["member_db"].get(str(cid), {}).get("name", "Unknown")
                return f"Mulligan Toggle: {c_name}"
        if 400 <= aid <= 460:
            h_idx = aid - 400
            if h_idx < len(game_p.hand):
                cid = game_p.hand[h_idx]
                c_name = db_json["live_db"].get(str(cid), {}).get("name", "Unknown")
                return f"Set Live: {c_name}"
        return f"Unknown({aid})"

    print("Starting Monitored Game...")

    step = 0
    while not game.is_terminal() and step < 400:  # High limit for trace
        cp_idx = game.current_player
        p0 = game.get_player(0)
        p1 = game.get_player(1)
        cur_p = game.get_player(cp_idx)

        print(f"\n[Step {step}] Turn {game.turn} | Player {cp_idx} | Phase {game.phase}")
        print(f"  P0 Score: {p0.score} | Hand: {len(p0.hand)} | Lives: {len(p0.success_lives)}")
        print(f"  P1 Score: {p1.score} | Hand: {len(p1.hand)} | Lives: {len(p1.success_lives)}")

        is_interactive = game.phase in [-1, 0, 4, 5]

        if is_interactive:
            # Show Hand Contents
            print(f"  Hand Context ({len(cur_p.hand)} cards):")
            for i, cid in enumerate(cur_p.hand):
                m = db_json["member_db"].get(str(cid))
                l = db_json["live_db"].get(str(cid))
                c_name = m["name"] if m else (l["name"] if l else "Unknown")
                c_type = "Member" if m else ("Live" if l else "Energy/Other")
                print(f"    [{i}] {c_name} ({c_type}) [ID: {cid}]")

            legal_ids = game.get_legal_action_ids()
            legal_desc = [decode_action(aid, cur_p) for aid in legal_ids]
            print(f"  Legal Actions ({len(legal_ids)}):")
            for aid, desc in zip(legal_ids, legal_desc):
                print(f"    - {aid}: {desc}")

            # Use Hybrid MCTS
            suggestions = mcts.get_suggestions(game, 1000)
            best_action = int(suggestions[0][0])

            print(f"  [Hybrid] Decision: {best_action} ({decode_action(best_action, cur_p)})")
            print("  Probabilities:")
            for a, s, v in suggestions[:5]:
                print(f"    - {a} ({decode_action(a, cur_p)}): Score {s:.3f} | Visits {v}")

            try:
                game.step(best_action)
            except Exception as e:
                print(f"!!! Error stepping {best_action}: {e}")
                break
        else:
            # Auto-step non-interactive phases
            game.step(0)

        step += 1

    print("\n--- MONITOR END ---")
    winner = game.get_winner()
    print(f"Final Result: {'Draw' if winner == 2 else f'Player {winner} Wins'} in {step} steps")


if __name__ == "__main__":
    monitor_game()
