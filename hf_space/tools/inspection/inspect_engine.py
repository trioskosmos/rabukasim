import os
import sys

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import engine_rust


def inspect_engine():
    print(f"engine_rust module: {engine_rust}")

    # Try to load RUST_DB
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    compiled_data_path = os.path.join(DATA_DIR, "cards_compiled.json")

    if not os.path.exists(compiled_data_path):
        print(f"Error: {compiled_data_path} not found")
        return

    with open(compiled_data_path, "r", encoding="utf-8") as f:
        db = engine_rust.PyCardDatabase(f.read())

    gs = engine_rust.PyGameState(db)
    print(f"gs type: {type(gs)}")
    print(f"gs dir: {dir(gs)}")

    # Check for pending_choices
    if hasattr(gs, "pending_choices"):
        print("gs has pending_choices")
        print(f"Value: {gs.pending_choices}")
    else:
        print("gs does NOT have pending_choices")
        # Look for methods that might return it
        for attr in dir(gs):
            if "choice" in attr.lower():
                print(f"Found related attribute: {attr}")


if __name__ == "__main__":
    inspect_engine()
