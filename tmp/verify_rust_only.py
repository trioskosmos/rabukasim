import engine_rust
import json

def test_rust_tensor():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)
    state = engine_rust.PyGameState(db)
    tensor = state.to_alphazero_tensor()
    print(f"Rust Tensor Size: {len(tensor)}")
    if len(tensor) == 20500:
        print("SUCCESS: 20,500 dimension verified.")
    else:
        print(f"FAILURE: Got {len(tensor)}")

if __name__ == "__main__":
    test_rust_tensor()
