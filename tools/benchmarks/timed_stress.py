import json
import os
import random
import sys
import time
from typing import List, Tuple

# Add project root to path
sys.path.append(os.getcwd())

import engine_rust

INSTANCE_SHIFT = 20
BASE_ID_MASK = 0xFFFFF


def create_uid(base_id: int, index: int) -> int:
    return (index << INSTANCE_SHIFT) | (base_id & BASE_ID_MASK)


def load_db():
    db_path = "engine/data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        json_data = f.read()
    rust_db = engine_rust.PyCardDatabase(json_data)
    data = json.loads(json_data)
    return rust_db, data["member_db"], data["live_db"], data["energy_db"]


def generate_legal_deck(member_db, live_db, energy_db) -> Tuple[List[int], List[int], List[int]]:
    available_members = list(member_db.keys())
    random.shuffle(available_members)
    member_bucket = []
    for mid in available_members:
        for i in range(4):
            member_bucket.append(create_uid(int(mid), i))
        if len(member_bucket) >= 100:
            break
    while len(member_bucket) < 48:
        member_bucket.extend(member_bucket)
    p_m = member_bucket[:48]

    available_lives = list(live_db.keys())
    random.shuffle(available_lives)
    live_bucket = []
    for lid in available_lives:
        for i in range(4):
            live_bucket.append(create_uid(int(lid), i))
        if len(live_bucket) >= 40:
            break
    while len(live_bucket) < 12:
        live_bucket.extend(live_bucket)
    # The deck usually contains some lives, let's mix them
    deck = p_m + live_bucket[:12]
    random.shuffle(deck)

    eid = random.choice(list(energy_db.keys())) if energy_db else 40000
    p_e = [int(eid)] * 12

    p_l = [create_uid(int(lid), 100) for lid in available_lives[:3]]
    while len(p_l) < 3:
        p_l.append(create_uid(1, 200 + len(p_l)))

    return deck, p_e, p_l


def run_timed_stress(duration_secs=10):
    rust_db, m_db, l_db, e_db = load_db()

    start_time = time.time()
    games_played = 0
    crashes = 0
    total_turns = 0

    print(f"Running timed stress test for {duration_secs} seconds (Step-by-step mode)")

    while time.time() - start_time < duration_secs:
        seed = random.randint(0, 0xFFFFFFFF)
        random.seed(seed)

        try:
            p0_m, p0_e, p0_l = generate_legal_deck(m_db, l_db, e_db)
            p1_m, p1_e, p1_l = generate_legal_deck(m_db, l_db, e_db)

            gs = engine_rust.PyGameState(rust_db)
            gs.initialize_game(p0_m, p1_m, p0_e, p1_e, p0_l, p1_l)

            # Step by step simulation
            action_count = 0
            MAX_ACTIONS = 2000

            while not gs.is_terminal() and action_count < MAX_ACTIONS:
                mask = gs.get_legal_actions()
                indices = [i for i, val in enumerate(mask) if val]
                if not indices:
                    break

                action = int(random.choice(indices))
                gs.step(action)
                action_count += 1

            games_played += 1
            total_turns += gs.turn

        except Exception as e:
            crashes += 1
            print(f"CRASH (Seed: {seed}): {e}")

    elapsed = time.time() - start_time
    print(f"\n--- Final Results ---\nTime: {elapsed:.2f}s\nGames: {games_played}\nCrashes: {crashes}")
    if games_played > 0:
        print(f"Avg Turns: {total_turns / games_played:.2f}")


if __name__ == "__main__":
    run_timed_stress(10)
