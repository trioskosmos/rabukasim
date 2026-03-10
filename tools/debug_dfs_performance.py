import os
import sys
from pathlib import Path

# Add project root to path
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

try:
    import engine_rust
except ImportError:
    sys.path.append(str(root_path / "alphazero" / "training"))
    import engine_rust


def get_action_label(action_id, state, db):
    if action_id == 0:
        return "Pass / Done"
    return f"Action {action_id}"


def run_diagnostic():
    print("=" * 100)
    print("DFS TEACHER DIAGNOSTIC & PERFORMANCE PROFILE (VANILLA MODE)")
    print("=" * 100)

    # 1. Load Vanilla Data
    cards_path = "data/cards_vanilla_compiled.json"
    print(f"[1/3] Loading database from {cards_path}...")
    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found.")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        db = engine_rust.PyCardDatabase(f.read())

    # Enable Vanilla-specific heuristics in Rust
    db.is_vanilla = True

    # 2. Initialize Game
    print("[2/3] Initializing game...")
    state = engine_rust.PyGameState(db)
    state.debug_mode = False

    # Try to load real decks if they exist, else use placeholders
    p0_deck = [30001, 30002, 30003, 30004, 30005, 30006, 30007, 30008, 30009, 30010]
    p1_deck = [30011, 30012, 30013, 30014, 30015, 30016, 30017, 30018, 30019, 30020]
    p0_lives = [35001, 35002, 35003]
    p1_lives = [35004, 35005, 35006]

    # Vanilla card IDs are often in the 30000+ range. Let's try to find some valid once if available
    member_ids = db.get_member_ids()
    live_ids = db.get_live_ids()
    if len(member_ids) >= 40:
        p0_deck = member_ids[:20]
        p1_deck = member_ids[20:40]
    if len(live_ids) >= 6:
        p0_lives = live_ids[:3]
        p1_lives = live_ids[3:6]

    state.initialize_game(p0_deck, p1_deck, [], [], p0_lives, p1_lives)

    # 3. Simulate and Profile
    print("[3/3] Running game with DFS profiling...")
    print("-" * 100)
    print(f"{'Turn':<5} | {'Phase':<15} | {'Nodes':<8} | {'Time (s)':<10} | {'Best Val':<10} | {'Board/Live':<15}")
    print("-" * 100)

    move_count = 0
    total_nodes = 0
    total_time = 0.0
    dfs_turns = 0

    while not state.is_terminal() and state.turn < 50 and move_count < 1000:
        phase_name = state.phase_name

        if phase_name in ["Main", "LiveSet"]:
            # plan_full_turn_with_stats returns (evals, best_seq, nodes, duration, breakdown)
            evals, best_seq, nodes, duration, breakdown = state.plan_full_turn_with_stats(db)

            total_nodes += nodes
            total_time += duration
            dfs_turns += 1

            best_val = breakdown[0] + breakdown[1] if breakdown else 0.0
            breakdown_str = f"{breakdown[0]:.2f}/{breakdown[1]:.2f}" if breakdown else "N/A"

            print(
                f"{state.turn:<5} | {phase_name:<15} | {nodes:<8} | {duration:<10.3f} | {best_val:<10.2f} | {breakdown_str:<15}"
            )

            if not best_seq:
                state.step(0)
                move_count += 1
            else:
                current_phase = state.phase
                for aid in best_seq:
                    if state.phase != current_phase:
                        break
                    state.step(aid)
                    move_count += 1
            state.auto_step(db)
        else:
            # Handle other phases (Mulligan, Energy, Draw, etc.)
            legal_ids = state.get_legal_action_ids(db)
            if not legal_ids:
                state.step(0)
            else:
                state.step(legal_ids[0])
            move_count += 1
            state.auto_step(db)

    # 4. Final Stats
    print("-" * 100)
    print(f"\nPERFORMANCE SUMMARY (Stopped after {move_count} moves)")
    print(f"  Total Game Turns:   {state.turn}")
    print(f"  DFS Turns Profiled: {dfs_turns}")
    if dfs_turns > 0:
        print(f"  Avg Nodes / Turn:   {total_nodes // dfs_turns}")
        print(f"  Avg Time / Turn:    {total_time * 1000 / dfs_turns:.2f} ms")
    print(f"  Total DFS Time:     {total_time:.3f} s")
    print(f"  Winner:             P{state.get_winner()}")
    print("=" * 100)


if __name__ == "__main__":
    run_diagnostic()
