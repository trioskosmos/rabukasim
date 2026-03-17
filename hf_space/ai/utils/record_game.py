import argparse
import json
import os
import random
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


def record_game(output_file, sims=200):
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)
    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)

    muse_deck_path = "ai/decks/muse_cup.txt"
    p_deck, p_lives, p_energy = parse_deck(
        muse_deck_path, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})
    )

    game.initialize_game(p_deck, p_deck, p_energy, p_energy, p_lives, p_lives)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"--- GAME RECORD: MCTS ({sims} sims) vs RANDOM ---\n")
        f.write(f"Deck: {muse_deck_path}\n\n")

        step = 0
        while not game.is_terminal() and step < 1000:
            cp = game.current_player
            phase = game.phase
            p_state = game.get_player(cp)

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

            f.write(f"[Step {step} | Turn {game.turn} | Player {cp} ({'MCTS' if cp == 0 else 'RANDOM'}) | {p_name}]\n")

            is_interactive = phase in [-1, 0, 4, 5]

            if is_interactive:
                tapped = sum(1 for t in p_state.tapped_energy if t)
                total_en = len(p_state.energy_zone)
                f.write(f"  Energy: {total_en - tapped}/{total_en}\n")
                f.write(f"  Hand: {p_state.hand}\n")
                f.write(f"  Stage: {p_state.stage}\n")
                f.write(f"  Live Zone: {p_state.live_zone} (Revealed: {p_state.live_zone_revealed})\n")
                f.write(f"  Score: {p_state.score}\n")

                if cp == 0:
                    suggestions = game.get_mcts_suggestions(sims, engine_rust.SearchHorizon.TurnEnd)
                    action = suggestions[0][0] if suggestions else 0
                else:
                    legal = game.get_legal_action_ids()
                    action = random.choice(legal) if legal else 0

                f.write(f"  Action: {action} ({get_action_name(action, game, db_json)})\n")
                game.step(action)
            else:
                game.step(0)

            f.write("\n")
            step += 1

        f.write("\n--- GAME COMPLETE ---\n")
        p0 = game.get_player(0)
        p1 = game.get_player(1)
        f.write(f"Final Outcome: winner={game.get_winner()}\n")
        f.write(f"P0 (MCTS): Score {p0.score}, Success Lives: {len(p0.success_lives)}\n")
        f.write(f"P1 (RANDOM): Score {p1.score}, Success Lives: {len(p1.success_lives)}\n")

    print(f"Game record saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="game_record.txt")
    parser.add_argument("--sims", type=int, default=200)
    args = parser.parse_args()
    record_game(args.output, sims=args.sims)
