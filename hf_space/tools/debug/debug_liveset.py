import lovecasim_engine as rust_engine


def debug_liveset():
    print("--- Rust LiveSet Debug ---")
    json_path = "data/cards_compiled.json"
    with open(json_path, "r", encoding="utf-8") as f:
        card_data_json = f.read()

    db = rust_engine.PyCardDatabase(card_data_json)
    gs = rust_engine.PyGameState()

    # Setup a state similar to Step 7
    # (Actually we can just set phase to LiveSet)
    # But PyGameState doesn't expose phase directly easily?
    # Let's check py_bindings.rs to see if we can set phase.

    # If we can't set phase, we just look at what happened in parity_log.txt
    # and try to reproduce the sequence of actions to reach Step 7.

    # Wait, PyGameState probably has a 'phase' property.
    try:
        gs.phase = 5  # LiveSet
        print(f"Set phase to {gs.phase}")
        # Add some cards to hand
        p0_hand = [33, 33, 33]
        # We need to set hand in Rust. Does PyGameState allow this?
    except Exception as e:
        print(f"Could not set phase directly: {e}")


if __name__ == "__main__":
    debug_liveset()
