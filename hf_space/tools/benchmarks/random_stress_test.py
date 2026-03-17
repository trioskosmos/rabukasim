"""
Run 100 Random AI vs Random AI games.
Uses 'legal' deck construction rules (similar to backend/server.py).
"""

import json
import random
import time
from typing import List, Tuple

# Ensure project root is in sys.path
import engine_rust

# --- CONFIG ---
NUM_GAMES = 100
MCTS_SIMS = 50  # Low count for speed, just testing for crashes/legality
INSTANCE_SHIFT = 20
BASE_ID_MASK = 0xFFFFF


def create_uid(base_id: int, index: int) -> int:
    """Create a unique instance ID."""
    return (index << INSTANCE_SHIFT) | (base_id & BASE_ID_MASK)


def load_db():
    compiled_data_path = "engine/data/cards_compiled.json"
    with open(compiled_data_path, "r", encoding="utf-8") as f:
        json_data = f.read()

    # Python dict lookup for deck building
    data = json.loads(json_data)
    member_db = {int(k): v for k, v in data.get("member_db", {}).items()}
    live_db = {int(k): v for k, v in data.get("live_db", {}).items()}
    energy_db = {int(k): v for k, v in data.get("energy_db", {}).items()}

    # Rust DB for the engine
    rust_db = engine_rust.PyCardDatabase(json_data)

    return rust_db, member_db, live_db, energy_db


def generate_legal_deck(member_db, live_db, energy_db) -> Tuple[List[int], List[int], List[int]]:
    """
    Generates a legal random deck:
    - 48 Member cards (max 4 copies of same card_no)
    - 12 Live cards (max 4 copies, usually)
    - 12 Energy cards (typically same type for now)
    - 3 Starting Energy
    """

    # 1. Select Members (48)
    # Group members by card_no to handle "max 4 copies" correctly if IDs differ per art?
    # In this system, card_id IS the unique card definition. So max 4 per card_id.

    available_members = list(member_db.keys())
    random.shuffle(available_members)

    main_deck_members = []

    # We need to fill 48 slots.
    # Simple strategy: keep picking a random card and adding 4 copies until full.

    member_bucket = []
    for mid in available_members:
        # Add 4 copies
        for i in range(4):
            uid = create_uid(mid, i)
            member_bucket.append(uid)

        if len(member_bucket) >= 100:  # optimization
            break

    # If we still don't have enough (very small DB), repeat
    while len(member_bucket) < 48:
        # Just duplicate what we have
        member_bucket.extend(member_bucket)

    # Slice to exactly 48
    main_deck_members = member_bucket[:48]

    # 2. Select Lives (12)
    available_lives = list(live_db.keys())
    if not available_lives:
        # Fallback if no lives loaded?
        print("WARNING: No lives found in DB!")
        return [], [], []

    random.shuffle(available_lives)

    main_deck_lives = []
    live_bucket = []

    for lid in available_lives:
        for i in range(4):
            uid = create_uid(lid, i)
            live_bucket.append(uid)
        if len(live_bucket) >= 40:
            break

    while len(live_bucket) < 12:
        live_bucket.extend(live_bucket)

    main_deck_lives = live_bucket[:12]

    # Combined Main Deck
    main_deck = main_deck_members + main_deck_lives
    random.shuffle(main_deck)

    # 3. Energy Deck (10 cards in rules usually? server says 12. Let's use 10-12.)
    # Server uses 12.
    if energy_db:
        # Pick one energy type randomly
        eid = random.choice(list(energy_db.keys()))
        energy_deck = [eid] * 12
    else:
        energy_deck = [40000] * 12

    # 4. Lives (for Live Zone) - these are distinct from main deck lives in some implementations,
    # or drawn from main deck?
    # In server.py: "p1_l = live_ids[:3]" for custom decks, but for regular init_game logic:
    # It extracts lives from data or just keys?
    # Wait, server.py `init_game` sets `p.main_deck` with members+lives.
    # Rust `initialize_game` signature takes: (p0_deck, p1_deck, p0_start_energy, p1_start_energy, p0_lives, p1_lives)
    # The `p0_lives` arg is for the Starting Live Zone (3 cards).
    # The `p0_deck` contains the library (Members + Lives that will optionally go to hand/stage).

    # So we need 3 separate lives for the Live Zone.
    # We can pick random lives from DB for this.
    start_lives = []
    random.shuffle(available_lives)
    for lid in available_lives[:3]:
        # Create a unique instance for these too
        # Use a high index shift to avoid collision with deck?
        # Or just use index 100+
        start_lives.append(create_uid(lid, 100))

    while len(start_lives) < 3:
        if available_lives:
            start_lives.append(create_uid(available_lives[0], 101 + len(start_lives)))
        else:
            # Fallback
            start_lives.append(create_uid(1, 200))

    return main_deck, energy_deck, start_lives


def run_stress_test():
    rust_db, m_db, l_db, e_db = load_db()

    wins = [0, 0, 0]  # p0, p1, draw
    crashes = 0
    total_turns = 0

    print(f"Starting Stress Test: {NUM_GAMES} games")

    start_time = time.time()

    # Use a fixed master seed for the whole run if desired, or just log random ones
    master_seed = int(time.time())
    print(f"Master Seed: {master_seed}")
    random.seed(master_seed)

    for i in range(NUM_GAMES):
        game_seed = random.randint(0, 2**32 - 1)
        print(f"--- Game {i + 1} (Seed: {game_seed}) ---")

        # Reseed for this iteration so deck gen is reproducible from this seed
        random.seed(game_seed)

        try:
            # Generate Decks
            p0_deck, p0_energy, p0_lives = generate_legal_deck(m_db, l_db, e_db)
            p1_deck, p1_energy, p1_lives = generate_legal_deck(m_db, l_db, e_db)

            # Init Game
            gs = engine_rust.PyGameState(rust_db)
            # gs.set_time_limit(1000) # Optional timeout per move?

            # The signature might vary based on recent changes.
            # Checking server.py: gs.initialize_game(p0_m, p1_m, p0_e, p1_e, p0_l, p1_l)
            # Note: initialize_game might use the global random state?
            # If the rust engine uses its own RNG, we might need to seed it if possible.
            # But the decks are passed in, so at least that part is deterministic from python side.

            gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

            # Step-by-step execution to catch hangs
            action_count = 0
            MAX_ACTIONS = 5000
            action_history = []

            while not gs.is_terminal() and action_count < MAX_ACTIONS:
                mask = gs.get_legal_actions()
                indices = [i for i, val in enumerate(mask) if val]

                if not indices:
                    print(
                        f"  STUCK: No legal actions at Turn {gs.turn}, Phase {gs.phase}, Player {getattr(gs, 'current_player', '?')}"
                    )
                    if hasattr(gs, "pending_ctx") and gs.pending_ctx:
                        print(f"    Pending Context active for player {gs.pending_ctx.player_id}")
                    break

                # Pick random action
                action = int(random.choice(indices))
                action_history.append((gs.turn, gs.phase, action))
                if len(action_history) > 20:
                    action_history.pop(0)

                try:
                    gs.step(action)
                    action_count += 1
                except Exception as e:
                    print(f"  Action Error at Action {action_count}: {e}")
                    raise e

            if action_count >= MAX_ACTIONS:
                print(f"  POTENTIAL INFINITE LOOP at Seed: {game_seed}, Turn {gs.turn}")
                print("  Last 20 actions:")
                for t, p, a in action_history:
                    print(f"    Turn {t}, Phase {p}, Action {a}")
                crashes += 1
                winner = -1
            else:
                winner = gs.get_winner()
                turns = gs.turn

            if winner < 0:
                wins[2] += 1  # Draw or timeout
            else:
                wins[winner] += 1

            total_turns += turns

            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                print(
                    f"Game {i + 1}/{NUM_GAMES} | P0: {wins[0]} P1: {wins[1]} Draw: {wins[2]} | Avg Turns: {total_turns / (i + 1):.1f} | Time: {elapsed:.1f}s"
                )

        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            break
        except Exception as e:
            crashes += 1
            print(f"CRASH in Game {i + 1} (Seed: {game_seed}): {e}")
            import traceback

            traceback.print_exc()

    print("\n--- Final Results ---")
    print(f"Total Games: {NUM_GAMES}")
    print(f"P0 Wins: {wins[0]}")
    print(f"P1 Wins: {wins[1]}")
    print(f"Draws: {wins[2]}")
    print(f"Crashes: {crashes}")
    print(f"Total Time: {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    run_stress_test()
