import json
import os
import random
import sys

# Add project root to path
sys.path.append(os.getcwd())

import lovecasim_engine as rust_engine


def generate_log():
    print("Generating comprehensive game log...")

    # Load Card DB for name lookups
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        card_data = json.load(f)

    member_map = {int(k): v["name"] for k, v in card_data["member_db"].items()}
    live_map = {int(k): v["name"] for k, v in card_data["live_db"].items()}

    def get_name(cid):
        if cid == -1:
            return "Empty"
        cid = int(cid)
        return member_map.get(cid) or live_map.get(cid) or f"Unknown({cid})"

    rust_db = rust_engine.PyCardDatabase(json.dumps(card_data))

    # Select low-cost cards
    # Card 33 has cost 1 (found via debug)
    m_ids = [33, 34, 35]
    l_ids = [int(k) for k in list(card_data["live_db"].keys())[:5]]

    p0_deck = (m_ids * 20)[:48]
    p1_deck = (m_ids * 20)[:48]
    p0_energy = (m_ids * 10)[:10]  # Max 10ish for energy deck
    p1_energy = (m_ids * 10)[:10]
    p0_lives = (l_ids * 3)[:12]
    p1_lives = (l_ids * 3)[:12]

    gs = rust_engine.PyGameState(rust_db)
    gs.initialize_game_with_seed(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives, 12345)

    log_lines = []
    log_lines.append("=== LoveLive TCG - Rust Engine Game Log ===")
    log_lines.append(f"Initial Phase: {gs.phase}")

    step_count = 0
    max_steps = 300

    while not gs.is_terminal() and step_count < max_steps:
        p_idx = gs.current_player
        actions = gs.get_legal_action_ids()

        if not actions:
            log_lines.append(f"\n[ERROR] No legal actions in Phase {gs.phase}!")
            break

        # Helper to describe actions
        def describe_action(act):
            if act == 0:
                return "End Phase / Finish Setup"
            elif 1 <= act <= 180:
                adj = act - 1
                h_idx, s_idx = adj // 3, adj % 3
                p = gs.get_player(p_idx)
                if h_idx < len(p.hand):
                    return f"Play {get_name(p.hand[h_idx])} to Slot {s_idx}"
                return f"Play Hand[{h_idx}] to Slot {s_idx}"
            elif 200 <= act < 400:
                adj = act - 200
                s_idx, a_idx = adj // 10, adj % 10
                return f"Activate Ability {a_idx} on Slot {s_idx}"
            elif 400 <= act < 460:
                return "Set Hand Card as Live"
            return f"Other Action {act}"

        # Log Legal Actions
        log_lines.append("  Legal Moves:")
        for act in actions:
            log_lines.append(f"    [{act}] {describe_action(act)}")

        action = random.choice(actions)

        # State Dump before Action
        log_lines.append(f"\n--- Step {step_count} (Player {p_idx}, Phase {gs.phase}, Turn {gs.turn}) ---")

        for i in range(2):
            p = gs.get_player(i)
            log_lines.append(f"Player {i} Score: {p.score}")
            log_lines.append(f"  Hand: {[get_name(c) for c in p.hand]}")
            log_lines.append(f"  Stage: {[get_name(c) for c in p.stage]}")
            log_lines.append(f"  Discard: {len(p.discard)} cards, Energy: {len(p.energy_zone)}")

        # Describe Action
        action_desc = f"Action {action}: {describe_action(action)}"
        log_lines.append(action_desc)

        # Take Step
        try:
            gs.step(action)
        except Exception as e:
            log_lines.append(f"[EXCEPTION] {e}")
            break

        step_count += 1

    if gs.is_terminal():
        log_lines.append("\n=== GAME OVER ===")
        log_lines.append(f"Winner: {gs.get_winner()} (0=P0, 1=P1, 2=Draw)")
    else:
        log_lines.append(f"\n[STOPPED] Reached max steps ({max_steps})")

    with open("game_examination.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print(f"Log generated: game_examination.txt ({step_count} steps)")


if __name__ == "__main__":
    generate_log()
