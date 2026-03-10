"""
Bootstrap AlphaZero training data by generating random games.
Filters for short games (< TURN_LIMIT full game turns) and stores
each move as a transition in the PersistentBuffer.

Runs single-process to avoid RAM exhaustion from multiple engine instances.
Reports buffer fill progress periodically.
"""

import json
import random
import sys
import time
from pathlib import Path

import numpy as np

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "alphazero" / "training"))

# Remove bad sys.path hack that was loading stale .pyd files. We rely on standard `uv run maturin develop` now.

import engine_rust
from disk_buffer import PersistentBuffer

from engine.game.deck_utils import UnifiedDeckParser

# ─── CONFIG ────────────────────────────────────────────────────────────────
MAX_BUFFER_SIZE = 500_000
OBS_DIM = 20_500
NUM_ACTIONS = 22_000
TURN_LIMIT = 10  # Only keep games where state.turn < TURN_LIMIT at end
REPORT_INTERVAL = 200  # Print progress every N total games
FLOAT16_MAX = 65_504.0  # Max safe float16 value
# ───────────────────────────────────────────────────────────────────────────


def load_decks(full_db: dict) -> list:
    parser = UnifiedDeckParser(full_db)
    decks = []
    standard_energy_ids = [38, 39, 40, 41, 42] * 4
    decks_dir = root_dir / "ai" / "decks"

    for deck_file in decks_dir.glob("*.txt"):
        try:
            with open(deck_file, "r", encoding="utf-8") as f:
                results = parser.extract_from_content(f.read())
            if not results:
                continue
            d = results[0]
            m, l, e = [], [], []
            for code in d["main"]:
                cdata = parser.resolve_card(code)
                if not cdata:
                    continue
                if cdata.get("type") == "Member":
                    m.append(cdata["card_id"])
                elif cdata.get("type") == "Live":
                    l.append(cdata["card_id"])
            for code in d["energy"]:
                cdata = parser.resolve_card(code)
                if cdata:
                    e.append(cdata["card_id"])
            if len(m) >= 30:
                decks.append(
                    {
                        "members": (m + m * 4)[:48],
                        "lives": (l + l * 4)[:12],
                        "energy": (e + standard_energy_ids * 12)[:12],
                    }
                )
        except Exception:
            continue
    return decks


def generate_random_game(db, d0: dict, d1: dict) -> tuple[list | None, int]:
    """
    Play one fully random game. Returns (transitions, final_turn).
    Returns (None, final_turn) if the game exceeded TURN_LIMIT.
    Each transition is (obs_f32, sparse_policy, mask_indices, value_f32).
    """
    try:
        state = engine_rust.PyGameState(db)
        state.initialize_game(
            d0["members"] + d0["lives"],
            d1["members"] + d1["lives"],
            d0["energy"],
            d1["energy"],
            [],
            [],
        )
        state.silent = True

        game_history = []

        while not state.is_terminal():
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                break
            if state.turn >= TURN_LIMIT * 20:  # Safety cap: ~20 actions per game-turn
                break

            action = random.choice(legal_ids)

            # Build boolean mask
            mask = np.zeros(NUM_ACTIONS, dtype=np.bool_)
            for aid in legal_ids:
                mask[aid] = True

            # Capture raw obs as float32 BEFORE stepping (clipped to float16 safe range)
            obs_raw = np.array(state.to_alphazero_tensor(), dtype=np.float32)

            game_history.append(
                {
                    "obs": obs_raw,
                    "action": action,
                    "player": state.acting_player,
                    "mask": mask,
                    "turn": state.turn,
                }
            )

            state.step(action)
            state.auto_step(db)

        final_turn = state.turn
        if final_turn >= TURN_LIMIT:
            return None, final_turn

        winner = state.get_winner()
        p0 = state.get_player(0)
        p1 = state.get_player(1)
        p0_lives = len(p0.success_lives)
        p1_lives = len(p1.success_lives)

        transitions = []
        for t in game_history:
            # Value targets
            win_prob = 1.0 if t["player"] == winner else (0.5 if winner < 0 else 0.0)
            my_lives = p0_lives if t["player"] == 0 else p1_lives
            opp_lives = p1_lives if t["player"] == 0 else p0_lives
            momentum = np.clip((my_lives - opp_lives) / 5.0, -1.0, 1.0)
            efficiency = max(0.0, 1.0 - final_turn / (TURN_LIMIT * 20))
            target_v = np.array([win_prob, float(momentum), efficiency], dtype=np.float32)

            # Clip obs to float16 safe range to avoid overflow in disk_buffer
            obs_clipped = np.clip(t["obs"], -FLOAT16_MAX, FLOAT16_MAX)

            # Sparse policy: just the chosen action with prob=1
            sparse_policy = (
                np.array([t["action"]], dtype=np.uint16),
                np.array([1.0], dtype=np.float16),
            )
            mask_indices = np.where(t["mask"])[0].astype(np.uint16)

            transitions.append((obs_clipped, sparse_policy, mask_indices, target_v))

        return transitions, final_turn

    except Exception as e:
        # Swallow individual game errors so we keep going
        print(f"  [WARN] Game error: {e}")
        return None, -1


def main():
    db_path = root_dir / "data" / "cards_compiled.json"
    if not db_path.exists():
        print("Error: cards_compiled.json not found.")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)

    print("Loading card database...")
    db = engine_rust.PyCardDatabase(open(db_path, encoding="utf-8").read())

    print("Loading decks...")
    decks = load_decks(full_db)
    if not decks:
        print("Error: No decks found in ai/decks/")
        return
    print(f"Found {len(decks)} decks.")

    buffer_dir = root_dir / "alphazero" / "training" / "experience_bootstrap"
    buffer = PersistentBuffer(
        buffer_dir,
        max_size=MAX_BUFFER_SIZE,
        obs_dim=OBS_DIM,
        num_actions=NUM_ACTIONS,
    )

    print(f"\n{'=' * 55}")
    print("AlphaZero Bootstrap - Single Process Mode")
    print(f"Target: {MAX_BUFFER_SIZE:,} transitions  |  Filter: turn < {TURN_LIMIT}")
    print(f"Buffer state: {buffer.count:,} / {MAX_BUFFER_SIZE:,} already filled")
    print(f"{'=' * 55}\n")

    total_games = 0
    short_games = 0
    total_transitions = buffer.count
    start_time = time.time()

    while total_transitions < MAX_BUFFER_SIZE:
        d0 = random.choice(decks)
        d1 = random.choice(decks)
        transitions, final_turn = generate_random_game(db, d0, d1)
        total_games += 1

        if transitions:
            short_games += 1
            for t in transitions:
                obs, sparse_policy, mask_indices, target_v = t
                buffer.add(obs, sparse_policy, target_v, mask_indices)
                total_transitions = buffer.count
                if total_transitions >= MAX_BUFFER_SIZE:
                    break

        if total_games % REPORT_INTERVAL == 0:
            elapsed = time.time() - start_time
            gps = total_games / elapsed
            hit_rate = short_games / total_games * 100
            avg_trans = (total_transitions - buffer.count + total_transitions) / max(1, short_games)
            remaining = MAX_BUFFER_SIZE - total_transitions
            eta_s = remaining / max(1, (total_transitions / elapsed)) if elapsed > 0 else 0
            print(
                f"Games: {total_games:>7,} | Short: {short_games:>6,} ({hit_rate:5.1f}%) | "
                f"Buffer: {total_transitions:>7,}/{MAX_BUFFER_SIZE:,} | "
                f"GPS: {gps:6.1f} | ETA: {eta_s / 60:.1f}min"
            )

        if total_transitions >= MAX_BUFFER_SIZE:
            break

    buffer.flush()
    elapsed = time.time() - start_time
    print(f"\n{'=' * 55}")
    print("Bootstrap Complete!")
    print(f"Total Games: {total_games:,}  |  Short Games: {short_games:,}")
    print(f"Buffer: {buffer.count:,} transitions  |  Time: {elapsed / 60:.1f}min")
    print(f"Output: {buffer_dir}")
    print(f"{'=' * 54}")


if __name__ == "__main__":
    main()
