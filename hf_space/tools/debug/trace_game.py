import argparse
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_rust
from ai.benchmark_decks import parse_deck


def get_action_name(action_id, game, db_json):
    """Decodes Action ID into a human-readable name."""
    if action_id == 0:
        return "Pass/End Phase"

    phase = game.phase
    p_idx = game.current_player
    p_state = game.get_player(p_idx)

    if phase in [-1, 0]:  # Mulligan
        # Action is a bitmask
        indices = [i for i in range(len(p_state.hand)) if (action_id >> i) & 1]
        return f"Mulligan: Discard indices {indices}"

    if phase == 4:  # Main
        if 1 <= action_id <= 180:
            adj = action_id - 1
            hand_idx = adj // 3
            slot_idx = adj % 3
            if hand_idx < len(p_state.hand):
                cid = p_state.hand[hand_idx]
                card = db_json["member_db"].get(str(cid), {"name": f"Unknown Member {cid}"})
                return f"Play {card['name']} to Slot {slot_idx}"
        elif 200 <= action_id < 400:
            adj = action_id - 200
            slot_idx = adj // 10
            ab_idx = adj % 10
            return f"Activate Ability {ab_idx} in Slot {slot_idx}"

    if phase == 5:  # LiveSet
        if 400 <= action_id < 500:
            hand_idx = action_id - 400
            if hand_idx < len(p_state.hand):
                cid = p_state.hand[hand_idx]
                card = db_json["live_db"].get(str(cid), {"name": f"Unknown Live {cid}"})
                return f"Set Live: {card['name']}"

    return f"Unknown Action ({action_id})"


def trace_game(sims=800):
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)
    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)

    muse_deck_path = "ai/decks/muse_cup.txt"
    with open(muse_deck_path, "r") as f:
        p_deck, p_lives, p_energy = parse_deck(
            muse_deck_path, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})
        )

    game.initialize_game(p_deck, p_deck, p_energy, p_energy, p_lives, p_lives)

    print("\n--- TRACING TURN 1 ---")

    step = 0
    while not game.is_terminal() and step < 500:
        cp = game.current_player
        phase = game.phase

        phase_names = {
            -1: "MulliganP1",
            0: "MulliganP2",
            1: "Active",
            2: "Energy",
            3: "Draw",
            4: "Main",
            5: "LiveSet",
            6: "PerfP1",
            7: "PerfP2",
            8: "LiveResult",
        }
        p_name = phase_names.get(phase, f"Phase {phase}")

        print(f"[Step {step} | Turn {game.turn} | Player {cp} | {p_name}]")

        is_interactive = phase in [-1, 0, 4, 5]

        if is_interactive:
            legal_ids = game.get_legal_action_ids()
            print(f"  Legal Actions: {legal_ids}")

            suggestions = game.get_mcts_suggestions(sims, engine_rust.SearchHorizon.TurnEnd)
            print(f"  MCTS Suggestions (Top 3): {[(s[0], round(s[1], 3)) for s in suggestions[:3]]}")
            best_action = suggestions[0][0] if suggestions else 0

            p_state = game.get_player(cp)
            tapped = sum(1 for t in p_state.tapped_energy if t)
            total = len(p_state.energy_zone)
            print(f"  Energy: {total - tapped}/{total}")
            print(f"  Hand: {p_state.hand[:8]}")
            print(f"  Stage: {p_state.stage}")
            print(f"  Action: {best_action} ({get_action_name(best_action, game, db_json)})")

            game.step(best_action)
        else:
            game.step(0)

        step += 1

    print("\n--- Game Complete ---")
    p0 = game.get_player(0)
    p1 = game.get_player(1)
    print(f"Final Scores - P0: {p0.score} ({len(p0.success_lives)}) | P1: {p1.score} ({len(p1.success_lives)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=800)
    args = parser.parse_args()
    trace_game(sims=args.sims)
