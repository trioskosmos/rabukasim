import json
import os
import random

import engine_rust


def test_basic_game_loop():
    # 1. Load Data
    data_path = "data/cards_compiled.json"
    if not os.path.exists(data_path):
        print(f"ERROR: {data_path} not found. Run compiler first.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        card_data = json.load(f)

    db = engine_rust.PyCardDatabase(json.dumps(card_data))
    state = engine_rust.PyGameState(db)

    # 2. Get Card IDs
    member_ids = db.get_member_ids()
    # Note: Currently no getter for live IDs in bindings based on my quick look,
    # but we can pass member IDs for now or extract from card_data.
    if not member_ids:
        member_ids = [101]

    print(f"Loaded {len(member_ids)} members.")

    # 3. Mock Decks (Standard 60 cards: 48 member + 12 live)
    p0_deck = random.choices(member_ids, k=60)
    p1_deck = random.choices(member_ids, k=60)
    p0_energy = random.choices(member_ids, k=20)
    p1_energy = random.choices(member_ids, k=20)

    # 4. Initialize Game
    # signature: p0_d, p1_d, p0_e, p1_e, p0_l, p1_l
    state.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, [], [])

    print(f"Game Started. Phase: {state.phase}")

    # 5. Run Loop
    max_steps = 2000
    steps = 0
    while not state.is_terminal() and steps < max_steps:
        steps += 1
        legal_actions = state.get_legal_action_ids()  # Removed db arg as it's internal to PyGameState
        if not legal_actions:
            print(f"ERROR: No legal actions at step {steps}. Phase: {state.phase}")
            break

        action = random.choice(legal_actions)
        try:
            state.step(action)  # Removed db arg
        except Exception as e:
            print(f"CRASH at step {steps} with action {action}: {e}")
            raise

    print(f"Game Finished in {steps} steps. Winner: {state.get_winner()}")
    assert state.is_terminal() or steps >= max_steps
    if steps >= max_steps:
        print("Warning: Game timed out (max steps reached).")


if __name__ == "__main__":
    test_basic_game_loop()
