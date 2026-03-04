import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import json
import torch
import torch.optim as optim
from alphazero.alphanet import AlphaNet
from alphazero.training.overnight_pure_zero import play_one_game, load_tournament_decks, init_worker, train_fixed_steps

def run_test():
    print("Testing pure zero training loop modifications...")
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_json_str = json.dumps(full_db)
    init_worker(db_json_str)

    decks = load_tournament_decks(full_db)
    if len(decks) < 2:
        print("Not enough decks.")
        return
    d0, d1 = decks[0], decks[1]

    # Generate game
    print("Generating one game...")
    transitions = play_one_game(d0, d1, sims_per_move=10, dirichlet_alpha=0.3, dirichlet_eps=0.25)
    print(f"Generated {len(transitions)} transitions. Sample target: {transitions[-1][3]}")

    # Test training
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaNet().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=0.001)

    print("Running training step...")
    res = train_fixed_steps(model, transitions, optimizer, device, num_steps=1, batch_size=8)
    print(f"Training Result: {res}")
    print("Test Complete!")

if __name__ == "__main__":
    run_test()
