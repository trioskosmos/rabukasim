import json
import os
import random
import sys

import numpy as np

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import engine_rust

from backend.rust_serializer import RustGameStateSerializer
from engine.game.data_loader import CardDataLoader
from engine.game.deck_utils import load_deck_from_file


def generate_random_deck(member_db, live_db, energy_db):
    m_ids = list(member_db.keys())
    l_ids = list(live_db.keys())
    random.shuffle(m_ids)
    random.shuffle(l_ids)

    main_ids = []
    # 48 members (max 4 each)
    for mid in m_ids[:15]:
        main_ids.extend([mid] * 4)
    # 12 lives (max 4 each)
    for lid in l_ids[:4]:
        main_ids.extend([lid] * 4)
    random.shuffle(main_ids)

    main_deck = main_ids[:60]
    energy_ids = list(energy_db.keys())
    energy_deck = [energy_ids[0]] * 12 if energy_ids else [40000] * 12
    # Start lives
    start_lives = [lid for lid in main_deck if lid in live_db][:3]
    if len(start_lives) < 3:
        start_lives.extend(l_ids[: 3 - len(start_lives)])

    return main_deck, energy_deck, start_lives


def select_action(legal_actions, gs):
    """Simple AI choice: pick the first legal action that isn't ID 0 unless only 0 is legal.
    Prioritizes activated abilities and member effects.
    """
    if not legal_actions:
        return None

    if len(legal_actions) == 1 and legal_actions[0]["id"] == 0:
        return 0

    # IDs:
    # 0: Pass
    # 200-229: Activate Member Ability (Stage)
    # 1000-1999: Play Card / Choice
    # 2000-2999: Activate Card Ability (Discard/Other)

    # 1. Prioritize Stage Abilities (200-229)
    stage_abilities = [a["id"] for a in legal_actions if 200 <= a["id"] <= 229]
    if stage_abilities:
        choice = random.choice(stage_abilities)
        return choice

    # 2. Prioritize Discard/Other Abilities (2000+)
    other_abilities = [a["id"] for a in legal_actions if a["id"] >= 2000]
    if other_abilities:
        choice = random.choice(other_abilities)
        return choice

    # 3. Prioritize Play actions
    actions = [a for a in legal_actions if a["id"] != 0]
    if actions:
        # Try to prefer Play Member over Mulligan/LiveSet if possible
        # Check by ID range usually (1000+)
        play_actions = [a["id"] for a in actions if 1000 <= a["id"] <= 1999]
        if play_actions:
            return random.choice(play_actions)
        else:
            return random.choice([a["id"] for a in actions])
    else:
        return 0


def run_debug_sim(seed=42):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    # 1. Load Data
    data_dir = os.path.join(PROJECT_ROOT, "data")
    cards_path = os.path.join(data_dir, "cards.json")
    loader = CardDataLoader(cards_path)
    member_db, live_db, energy_db = loader.load()

    # Load Compiled for Rust
    compiled_data_path = os.path.join(data_dir, "cards_compiled.json")
    with open(compiled_data_path, "r", encoding="utf-8") as f:
        rust_db = engine_rust.PyCardDatabase(f.read())

    serializer = RustGameStateSerializer(member_db, live_db, energy_db)

    # 2. Setup Decks
    # P0: Nijigaku Cup
    nijigaku_path = os.path.join(PROJECT_ROOT, "ai", "decks", "nijigaku_cup.txt")
    p0_main_str, p0_energy_str, _, _ = load_deck_from_file(nijigaku_path, {})  # We don't need type counts/errors here

    # Convert string IDs to internal IDs
    # Need mapping
    card_no_to_id = {}
    with open(compiled_data_path, "r", encoding="utf-8") as f:
        compiled_data = json.load(f)
        for db_name in ["member_db", "live_db", "energy_db"]:
            for internal_id, card_data in compiled_data.get(db_name, {}).items():
                card_no_to_id[card_data["card_no"]] = int(internal_id)

    def convert(deck_str):
        res = []
        for cno in deck_str:
            if cno in card_no_to_id:
                res.append(card_no_to_id[cno])
        return res

    p0_main = convert(p0_main_str)
    p0_energy = convert(p0_energy_str)
    p0_lives = [cid for cid in p0_main if cid in live_db][:3]

    # P1: Random
    p1_main, p1_energy, p1_lives = generate_random_deck(member_db, live_db, energy_db)

    # 3. Initialize Game
    gs = engine_rust.PyGameState(rust_db)
    gs.initialize_game(p0_main, p1_main, p0_energy, p1_energy, p0_lives, p1_lives)

    print("--- Simulation Started ---")
    print(f"P0: Nijigaku Cup ({len(p0_main)} cards)")
    print(f"P1: Random Deck ({len(p1_main)} cards)")

    step_count = 0
    max_steps = 200
    last_actions = []

    while not gs.is_terminal():
        state = serializer.serialize_state(gs, viewer_idx=gs.current_player)
        print(f"\n[Step {step_count}] Turn {state['turn']} Phase {state['phase']} Player P{state['active_player']}")

        # Display Action Bar
        legal_actions = state.get("legal_actions", [])
        print("  Action Bar:")
        for action in legal_actions:
            marker = "  "
            if action["id"] >= 2000:
                marker = "! "  # Highlight abilities
            print(f"    {marker}{action['id']}: {action['desc']}")

        if not legal_actions:
            print("  [ERROR] No legal actions!")
            break

        # Select and execute action
        preferred_action = select_action(legal_actions, gs)
        print(f"  >> Selected Action: {preferred_action}")

        last_actions.append(preferred_action)
        if len(last_actions) > 10:
            last_actions.pop(0)
            if len(set(last_actions)) == 1 and preferred_action != 0:
                action_desc = "Unknown"
                for la in legal_actions:
                    if la["id"] == preferred_action:
                        action_desc = la["desc"]
                        break
                print(f"  [CRITICAL] Infinite loop detected for action {preferred_action}: {action_desc}!")
                break

        # Step the game
        try:
            gs.step(preferred_action)
        except Exception as e:
            print(f"  [ERROR] Game crashed at Step {step_count}: {e}")
            break

        step_count += 1
        if step_count >= max_steps:
            print(f"\n--- Simulation Timed Out at {max_steps} steps ---")
            break

    if gs.is_terminal():
        print("\n--- Simulation Finished ---")
        print(f"Winner: P{gs.get_winner()}")
    else:
        print(f"\n--- Simulation Timed Out at {max_steps} steps ---")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run game simulations for debugging.")
    parser.add_argument("--rounds", type=int, default=1, help="Number of games to simulate.")
    parser.add_argument("--seed", type=int, default=42, help="Initial random seed.")
    parser.add_argument("--random", action="store_true", help="Use a random seed instead of fixed.")
    args = parser.parse_args()

    for i in range(args.rounds):
        seed = None if args.random else (args.seed + i)
        print(f"\n--- Simulation Round {i + 1}/{args.rounds} (Seed: {seed}) ---")
        run_debug_sim(seed=seed)


if __name__ == "__main__":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    main()
