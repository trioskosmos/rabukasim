import time

import engine_rust


def main():
    json_path = "data/cards_compiled.json"
    print(f"Loading cards from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        json_str = f.read()

    db = engine_rust.PyCardDatabase(json_str)
    print(f"Database loaded. Members: {db.member_count}")

    iterations = 200000
    print(f"Starting Rust benchmark for {iterations} steps...")

    gs = engine_rust.PyGameState(db)

    # Create dummy decks
    all_members = db.get_member_ids()
    # Ensure we have enough cards
    deck = (all_members * 10)[:60]
    # Simple integers for lives (must be valid IDs if checked, but initialize_game might just verify existence in DB)
    # The Rust engine expects live IDs to be checked against DB if used?
    # initialize_game just stores them.
    lives = [lid for lid in range(100000, 100010)]

    gs.initialize_game(deck, deck, [10] * 20, [10] * 20, lives, lives)

    start = time.perf_counter()

    steps = 0
    while steps < iterations:
        # Measure get_legal_actions speed
        # legal_mask = gs.get_legal_actions()
        # Iterating boolean mask in Python is slow, so commonly we use get_legal_action_ids in bindings
        # or do it in Rust.

        legal_ids = gs.get_legal_action_ids()

        if not legal_ids:
            gs.initialize_game(deck, deck, [10] * 20, [10] * 20, lives, lives)
            continue

        action = legal_ids[steps % len(legal_ids)]
        gs.step(action)

        steps += 1
        if gs.is_terminal():
            gs.initialize_game(deck, deck, [10] * 20, [10] * 20, lives, lives)

    duration = time.perf_counter() - start
    print(f"Completed {steps} steps in {duration:.4f}s")
    print(f"Average time per step: {duration * 1000 / steps:.4f} ms")
    print(f"Steps per second: {steps / duration:.2f}")


if __name__ == "__main__":
    main()
