import json
import random
import sys
import time
from pathlib import Path

import engine_rust
import numpy as np
from tqdm import tqdm

# Add project root for engine imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from engine.game.deck_utils import UnifiedDeckParser

# AlphaZero configuration
ACTION_SPACE = 16384


def load_tournament_decks(db_json):
    decks_dir = Path(__file__).parent.parent.parent / "ai" / "decks"
    parser = UnifiedDeckParser(db_json)
    loaded_decks = []

    standard_energy_ids = []
    for cid, data in parser.normalized_db.items():
        if data.get("type") == "Energy" or cid.startswith("LL-E"):
            standard_energy_ids.append(data.get("card_id"))
            if len(standard_energy_ids) >= 12:
                break

    for deck_file in decks_dir.glob("*.txt"):
        with open(deck_file, "r", encoding="utf-8") as f:
            content = f.read()
        results = parser.extract_from_content(content)
        if not results:
            continue
        d = results[0]
        members, lives, energy = [], [], []
        for code in d["main"]:
            cdata = parser.resolve_card(code)
            if not cdata:
                continue
            if cdata.get("type") == "Member":
                members.append(cdata["card_id"])
            elif cdata.get("type") == "Live":
                lives.append(cdata["card_id"])
        for code in d["energy"]:
            cdata = parser.resolve_card(code)
            if cdata:
                energy.append(cdata["card_id"])

        if len(members) >= 48 and len(lives) >= 12:
            loaded_decks.append(
                {
                    "name": deck_file.stem,
                    "members": (members + members * 4)[:48],
                    "lives": (lives + lives * 4)[:12],
                    "energy": (energy + standard_energy_ids * 12)[:12],
                }
            )
    return loaded_decks


def generate_pure_trajectories(num_games=10, sims_per_move=256, output_file="pure_zero_trajectories.npz"):
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)

    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    tournament_decks = load_tournament_decks(full_db)

    dataset = []
    summary_stats = []

    for g_idx in tqdm(range(num_games), desc="Pure Zero Self-Play"):
        d0 = random.choice(tournament_decks)
        d1 = random.choice(tournament_decks)

        state = engine_rust.PyGameState(db_engine)
        state.initialize_game(
            d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], []
        )
        state.silent = True

        game_history = []
        log_file = None
        if g_idx == 0:
            log_file = open("pure_zero_log.txt", "w", encoding="utf-8")
            log_file.write(f"Starting Pure Zero Game {g_idx} ({d0['name']} vs {d1['name']})\n")

        eval_mode = engine_rust.EvalMode.TerminalOnly

        move_count = 0
        game_start_time = time.time()
        move_times = []

        while not state.is_terminal() and state.turn < 100:
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                break

            # 1. Run MCTS and measure time
            mcts_start = time.time()
            suggestions = state.get_mcts_suggestions(
                sims_per_move, 1.41, engine_rust.SearchHorizon.GameEnd(), eval_mode
            )
            mcts_end = time.time()
            move_times.append(mcts_end - mcts_start)

            policy_target = np.zeros(ACTION_SPACE, dtype=np.float32)
            total_visits = sum(s[2] for s in suggestions)

            if total_visits > 0:
                for action_id, h_score, visits in suggestions:
                    if 0 <= action_id < ACTION_SPACE:
                        policy_target[action_id] = visits / total_visits

            obs = state.to_alphazero_tensor()
            game_history.append(
                {
                    "obs": obs,
                    "policy": policy_target.tolist(),
                    "player": state.current_player,
                    "mask": [aid in legal_ids for aid in range(ACTION_SPACE)],
                }
            )

            actions = [s[0] for s in suggestions]
            counts = [s[2] for s in suggestions]

            if not actions:
                action = random.choice(legal_ids)
            else:
                action = random.choices(actions, weights=counts, k=1)[0]

            if log_file:
                log_file.write(
                    f"[T{state.turn}] Player {state.current_player} -> {state.get_action_label(action)} (Time: {mcts_end - mcts_start:.3f}s, Sims: {total_visits}, Q: {suggestions[0][1] if suggestions else 0:.3f})\n"
                )

            state.step(action)
            state.auto_step(db_engine)
            move_count += 1

        winner = state.get_winner()
        avg_move_time = sum(move_times) / len(move_times) if move_times else 0
        summary_stats.append({"game": g_idx, "turns": state.turn, "winner": winner, "avg_move_time": avg_move_time})

        if log_file:
            log_file.write(f"\nFinal Statistics for Game {g_idx}:\n")
            log_file.write(f"Turns: {state.turn}, Winner: {winner}, Avg Move Time: {avg_move_time:.3f}s\n")
            log_file.close()
            log_file = None  # Ensure we don't try to close it again in finally

        for transition in game_history:
            outcome = 0.0
            if winner != -1:
                outcome = 1.0 if transition["player"] == winner else -1.0

            dataset.append(
                {"obs": transition["obs"], "policy": transition["policy"], "mask": transition["mask"], "value": outcome}
            )

    # Save
    obs_batch = np.array([t["obs"] for t in dataset], dtype=np.float32)
    policy_batch = np.array([t["policy"] for t in dataset], dtype=np.float32)
    mask_batch = np.array([t["mask"] for t in dataset], dtype=np.bool_)
    value_batch = np.array([t["value"] for t in dataset], dtype=np.float32)

    print(f"Saving {len(dataset)} Pure Zero transitions...")
    np.savez_compressed(output_file, obs=obs_batch, policy=policy_batch, mask=mask_batch, value=value_batch)


if __name__ == "__main__":
    generate_pure_trajectories(num_games=10, sims_per_move=256)
