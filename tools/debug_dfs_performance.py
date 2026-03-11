import os
import sys
from pathlib import Path

# Add project root to path and prioritize it for engine_rust.pyd
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

try:
    import engine_rust
    print(f"DEBUG: engine_rust loaded from {engine_rust.__file__}")
    # Verify attribute existence
    db_test = engine_rust.PyCardDatabase("{}")
    has_v = hasattr(db_test, 'is_vanilla')
    print(f"DEBUG: PyCardDatabase has is_vanilla: {has_v}")
    if not has_v:
        print("WARNING: is_vanilla missing! Check if engine_rust.pyd in root is correct.")
except ImportError:
    print("Error: engine_rust not found in project root or path.")
    sys.exit(1)


def get_action_label(action_id, state, db):
    try:
        return state.get_verbose_action_label(action_id, db)
    except:
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

    print(f"DEBUG: Initial state - is_terminal: {state.is_terminal()}, turn: {state.turn}, phase: {state.phase_name} ({state.phase})")

    import random

    while not state.is_terminal() and state.turn < 50 and move_count < 1000:
        p_idx = state.current_player
        player = state.get_player(p_idx)
        hand_len = len(player.hand)
        deck_len = len(player.deck)
        live_len = sum(1 for cid in player.live_zone if cid > 0)
        
        print(f"DEBUG: Loop start - Move: {move_count}, Turn: {state.turn}, P{p_idx} Hand: {hand_len}, Deck: {deck_len}, Live: {live_len}, Phase: {state.phase_name} ({state.phase})")
        phase_name = state.phase_name
        # print(f"DEBUG: Move {move_count}, Turn {state.turn}, Phase {phase_name}")

        if phase_name in ["Main", "LiveSet"]:
            # ... (DFS logic)
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
            legal_ids = state.get_legal_action_ids()
            if not legal_ids:
                print(f"DEBUG: No legal actions in {phase_name} at move {move_count}")
                try:
                    state.step(0)
                except Exception as e:
                    print(f"DEBUG: Step(0) failed in {phase_name}: {e}")
                    break
            else:
                if phase_name == "Rps":
                    aid = random.choice(legal_ids)
                else:
                    aid = legal_ids[0]

                label = get_action_label(aid, state, db)
                if move_count < 20 or move_count % 50 == 0:
                    print(f"DEBUG: Move {move_count} ({phase_name}): {label}")
                state.step(aid)
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
