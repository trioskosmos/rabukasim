import engine_rust
import numpy as np


def analyze_obs():
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()

    db = engine_rust.PyCardDatabase(db_json)
    state = engine_rust.PyGameState(db)

    # Initialize with a standard deck (ids ~1-60)
    # Energy ids ~38-40
    p0_deck = [1] * 48 + [101] * 12
    p1_deck = [2] * 48 + [102] * 12
    state.initialize_game(p0_deck, p1_deck, [38] * 40, [38] * 40, [], [])

    obs = state.to_alphazero_tensor()

    print(f"Observation Size: {len(obs)}")
    print(f"Min: {np.min(obs)}")
    print(f"Max: {np.max(obs)}")
    print(f"Unique values: {len(np.unique(obs))}")

    # Check if int16 can hold it (with scale/offset if needed)
    # Range is -32768 to 32767
    can_fit_int16 = (np.min(obs) >= -32768) and (np.max(obs) <= 32767)
    print(f"Can fit in int16 without scaling? {can_fit_int16}")

    # If not, how many unique values actually exist?
    # Usually game states are just IDs, counts, flags.
    # Large numbers are likely Score/Stats which might need float or scaling.


if __name__ == "__main__":
    analyze_obs()
