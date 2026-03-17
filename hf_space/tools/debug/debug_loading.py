import os

import lovecasim_engine as rust_engine


def debug_rust_loading():
    print("--- Rust Loading Debug ---")
    json_path = "data/cards_compiled.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        card_data_json = f.read()

    print(f"File size: {len(card_data_json)} bytes")

    try:
        print("Initializing Rust CardDatabase...")
        rust_db = rust_engine.PyCardDatabase(card_data_json)
        print(f"Success! Loaded {rust_db.member_count} members.")
    except Exception as e:
        print(f"FAILURE: {e}")


if __name__ == "__main__":
    debug_rust_loading()
