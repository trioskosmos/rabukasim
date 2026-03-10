import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

# Add root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import engine_rust
from tools.alphazero.alphanet import AlphaNet
from tools.alphazero.overnight_pure_zero import load_tournament_decks
from tools.alphazero.train import AlphaDataset, train_epoch


def benchmark():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0004)

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    decks = load_tournament_decks(full_db)

    print("--- STARTING ONE-ITERATION BENCHMARK ---")

    # 1. TIME SELF-PLAY
    start_gen = time.time()
    new_transitions = []
    games = 8
    sims = 512

    print(f"Generating {games} games with {sims} sims/move...")
    for i in range(games):
        d0, d1 = decks[0], decks[1]
        state = engine_rust.PyGameState(db_engine)
        state.initialize_game(
            d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], []
        )
        state.silent = True

        while not state.is_terminal() and state.turn < 100:
            legal_ids = state.get_legal_action_ids()
            suggestions = state.get_mcts_suggestions(
                sims, 0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly
            )

            policy_target = np.zeros(16384, dtype=np.float32)
            total_visits = sum(s[2] for s in suggestions)
            if total_visits > 0:
                for aid, q, v in suggestions:
                    policy_target[aid] = v / total_visits

            mask = [aid in legal_ids for aid in range(16384)]
            new_transitions.append((state.to_alphazero_tensor(), policy_target, mask, 1.0))  # Dummy outcome

            if not suggestions:
                break
            state.step(suggestions[0][0])
            state.auto_step(db_engine)

    gen_time = time.time() - start_gen
    print(f"Self-Play: {gen_time:.1f}s (Total samples: {len(new_transitions)})")

    # 2. TIME TRAINING
    obs_b = np.stack([t[0] for t in new_transitions]).astype(np.float32)
    pol_b = np.stack([t[1] for t in new_transitions]).astype(np.float32)
    msk_b = np.stack([t[2] for t in new_transitions]).astype(np.bool_)
    val_b = np.array([t[3] for t in new_transitions], dtype=np.float32)

    dataset = AlphaDataset(obs=obs_b, policy=pol_b, mask=msk_b, value=val_b)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    print("Running 15 training epochs...")
    start_train = time.time()
    initial_loss = 0
    final_loss = 0

    for epoch in range(15):
        stats = train_epoch(model, loader, optimizer, device, 3e-5, 2e-3)
        if epoch == 0:
            initial_loss = stats["loss"]
        final_loss = stats["loss"]
        print(f"  Epoch {epoch + 1:2d} | Loss: {stats['loss']:.4f}")

    train_time = time.time() - start_train
    print(f"Training: {train_time:.1f}s")
    print(f"Loss Delta: {initial_loss:.4f} -> {final_loss:.4f}")

    print("\n--- RESULTS ---")
    print(f"Total Iteration Time: {gen_time + train_time:.1f}s")
    print(f"Ratio (Gen/Train): {gen_time / train_time:.2f}")


if __name__ == "__main__":
    benchmark()
