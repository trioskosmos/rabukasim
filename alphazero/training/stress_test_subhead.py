import random
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# Add engine path
search_paths = [
    root_dir / "engine_rust_src" / "target" / "release",
    root_dir / "engine_rust_src" / "target" / "debug",
]
for p in search_paths:
    if (p / "engine_rust.pyd").exists() or (p / "engine_rust.dll").exists():
        sys.path.insert(0, str(p))
        break

import engine_rust

from alphazero.alphanet import ACTION_TYPE_RANGES, ACTION_TYPE_TABLE


def run_subindex_stress_test(num_games=50):
    print(f"Starting Sub-Index Stress Test ({num_games} games)...")

    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)

    # Track violations per type
    violations = {}  # type_idx -> list of (aid, raw_sub)
    type_names = {r[2]: f"Type {r[2]} (Base {r[0]})" for r in ACTION_TYPE_RANGES}

    # Dummy deck setup
    d0 = {"members": [1] * 48, "lives": [1] * 12, "energy": [38] * 12}
    d1 = {"members": [1] * 48, "lives": [1] * 12, "energy": [38] * 12}

    total_legal_checked = 0

    for g in range(num_games):
        state = engine_rust.PyGameState(db)
        state.initialize_game(
            d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], []
        )
        state.silent = True

        while not state.is_terminal() and state.turn < 50:
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                break

            for aid in legal_ids:
                total_legal_checked += 1
                t_idx = ACTION_TYPE_TABLE[aid]

                # Calculate the RAW (unclamped) sub-index
                # We need to find the specific range start for this type
                # Note: This is a bit rough as types can have multiple ranges, but for audit it works.
                range_start = -1
                for start, end, tid in ACTION_TYPE_RANGES:
                    if aid >= start and aid < end and tid == t_idx:
                        range_start = start
                        break

                if range_start == -1:
                    continue  # Should not happen

                raw_sub = aid - range_start

                # Check if this type uses a complex mapping
                if t_idx == 10:  # ActivateMember
                    slot = raw_sub // 100
                    ab = (raw_sub % 100) // 10
                    mapped_sub = slot * 10 + ab
                elif t_idx == 11:  # StageChoice
                    slot = raw_sub // 100
                    rem = raw_sub % 100
                    ab = rem // 10
                    choice = rem % 10
                    mapped_sub = slot * 20 + ab * 5 + choice
                else:
                    mapped_sub = raw_sub

                if mapped_sub >= 100:
                    if t_idx not in violations:
                        violations[t_idx] = set()
                    violations[t_idx].add((aid, mapped_sub))

            state.step(random.choice(legal_ids))
            state.auto_step(db)

        if (g + 1) % 10 == 0:
            print(f"  Completed {g + 1}/{num_games} games...")

    print("\n--- STRESS TEST RESULTS ---")
    print(f"Total legal actions audited: {total_legal_checked}")

    if not violations:
        print("✅ SUCCESS: No legal actions found exceeding sub-index 99.")
    else:
        print("⚠️  WARNING: Illegal sub-indices detected!")
        for t_idx, items in violations.items():
            name = type_names.get(t_idx, f"Type {t_idx}")
            print(f"\n{name}:")
            # Sort by mapped sub for readability
            sorted_items = sorted(list(items), key=lambda x: x[1])
            for aid, sub in sorted_items[:10]:  # Show first 10
                print(f"  AID {aid:5d} -> Mapped Sub {sub}")
            if len(sorted_items) > 10:
                print(f"  ... and {len(sorted_items) - 10} more.")


if __name__ == "__main__":
    run_subindex_stress_test()
