import json
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    import engine_rust
except ImportError:
    # Try to find it in the release folder or current dir
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "engine_rust_src", "target", "release"))
    )
    import engine_rust


def test_rank_5_blades():
    # Load compiled cards
    cards_path = "data/cards_compiled.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        compiled_json = f.read()

    db = engine_rust.PyCardDatabase(compiled_json)
    gs = engine_rust.PyGameState(db)

    # Setup Player 0
    p0 = gs.get_player(0)

    # Rank 5 Live Card: Reflection in the mirror (ID 30030)
    # Requirements: heart04: 3, heart0: 2 (Total 5)
    p0.set_live_zone([30030, -1, -1])
    p0.set_live_zone_revealed([True, False, False])

    # Members with blades: PL!-sd1-001-SD (ID 247)
    p0.set_stage([247, 247, 247])
    p0.blade_buffs = [1, 1, 0]

    # Set energy for performance
    p0.energy_zone = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    # IMPORTANT: Sync player state back to game state
    gs.set_player(0, p0)

    # Step into Performance phase
    gs.phase = 6  # PerformanceP1
    gs.current_player = 0

    print(f"Total Blades: {gs.get_total_blades(0)}")
    total_hearts = gs.get_total_hearts(0)
    print(f"Total Hearts (Raw Array): {list(total_hearts)}")

    # Step through Performance calculation
    gs.step(0)  # Calc P0
    gs.step(0)  # Calc P1 (pass)

    # Check results
    results_str = gs.performance_results
    if results_str:
        results = json.loads(results_str)
        p0_results = results.get("0")
        if p0_results:
            lives = p0_results.get("lives", [])
            if lives:
                # print(f"DEBUG: Lives info: {lives[0]}")
                success = lives[0].get("passed", False)
                print(f"Player 0 Live 0 Success (passed): {success}")
                if success:
                    print("PASSED: Blades as Hearts works!")
                else:
                    print("FAILED: Blades did not satisfy requirements.")
                    print(f"Required: {lives[0].get('required')}")
                    print(f"Filled: {lives[0].get('filled')}")
            else:
                print("FAILED: No lives in performance results.")
        else:
            print("FAILED: No performance results for Player 0.")
    else:
        print("FAILED: Performance results empty.")


if __name__ == "__main__":
    test_rank_5_blades()
