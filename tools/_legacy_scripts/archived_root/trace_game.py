import json
import os
import random
import sys
import time
import traceback

# Add current directory to path so we can import engine_rust if it is here
sys.path.append(os.getcwd())

# Also try adding engine_rust_src/target/debug/ or release/ if user built it there manually
# But typically maturin installs into site-packages or local venv

try:
    import engine_rust
except ImportError:
    print("Cannot import engine_rust. Make sure it is built and installed.")
    # Fallback for dev: if we are in root and engine_rust consists of .pyd or .so in current dir
    pass


def main():
    # Load data
    data_path = "data/cards_compiled.json"
    if not os.path.exists(data_path):
        # Try looking up one level
        data_path = "../data/cards_compiled.json"

    if not os.path.exists(data_path):
        print(f"Cannot find {data_path}")
        return

    print(f"Loading {data_path}...")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            json_str = f.read()
    except Exception as e:
        print(f"Failed to read file: {e}")
        return

    try:
        # Check if PyCardDatabase accepts string
        db = engine_rust.PyCardDatabase(json_str)
        print(f"Database loaded. Members: {db.member_count}, Lives: {db.live_count}")
    except Exception as e:
        print(f"Failed to load DB from JSON: {e}")
        traceback.print_exc()
        return

    # Initialize game
    try:
        game = engine_rust.PyGameState(db)
    except Exception as e:
        print(f"Failed to create GameState: {e}")
        return

    # Create a simple deck from available cards
    # We need member cards
    try:
        card_data = json.loads(json_str)
        live_db = card_data.get("live_db", {})
        member_db = card_data.get("member_db", {})

        live_ids = [c["card_id"] for c in live_db.values()]
        member_ids = [c["card_id"] for c in member_db.values()]

        # Sort for determinism
        live_ids.sort()
        member_ids.sort()

        print(f"Found {len(member_ids)} members and {len(live_ids)} lives in JSON")
    except Exception as e:
        print(f"Error parsing JSON manually: {e}")
        return

    if len(member_ids) < 40:
        print("Not enough members for a deck (need 40)")
        if len(member_ids) == 0:
            return
        # Pad
        p0_deck = (member_ids * (40 // len(member_ids) + 1))[:40]
    else:
        p0_deck = member_ids[:40]

    p1_deck = p0_deck.copy()  # Mirror match

    if len(live_ids) < 3:
        print("Not enough lives (need 3)")
        if len(live_ids) == 0:
            return
        p0_lives = (live_ids * 3)[:3]
    else:
        p0_lives = live_ids[:3]

    p1_lives = p0_lives.copy()

    print("Initializing Game with Decks...")
    try:
        # initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)
        # Note: energy decks are empty in this example, assuming standard energy rules or using main deck?
        # Standard rules use separate energy deck?
        # The signature expects Vec<u32>.
        game.initialize_game(p0_deck, p1_deck, [], [], p0_lives, p1_lives)
    except Exception as e:
        print(f"Failed to initialize game: {e}")
        traceback.print_exc()
        return

    print("Game Initialized. Starting loop...")

    turn_limit = 100
    start_time = time.time()

    step_count = 0
    while not game.is_terminal() and game.turn <= turn_limit:
        step_count += 1
        current_turn = game.turn
        phase = game.phase
        player = game.current_player

        # print(f"Step {step_count}: Turn {current_turn} Phase {phase} Player {player}")

        action = 0

        # Determine action
        if player == 0:
            # Agent using MCTS
            # Use a Phase check to see if we should run MCTS
            # MCTS on non-interactive phases is wasteful but harmless if legal actions are 0 or 1

            try:
                # 50 simulations
                suggestions = game.get_mcts_suggestions(50)
                if suggestions:
                    best_action, score, visits = suggestions[0]
                    action = best_action
                    print(f"T{current_turn} P{player} Ph{phase}: MCTS chose {action} (Score: {score:.2f}, N={visits})")
                else:
                    # Fallback or simple step
                    # Get legal actions
                    legal = game.get_legal_action_ids()
                    if legal:
                        action = legal[0]  # Deterministic fallback
                        print(f"T{current_turn} P{player} Ph{phase}: MCTS empty, using {action}")
                    else:
                        action = 0
            except Exception as e:
                print(f"MCTS Error: {e}")
                traceback.print_exc()
                break
        else:
            # Opponent (Player 1)
            # Random
            legal = game.get_legal_action_ids()
            if legal:
                action = random.choice(legal)
                # print(f"T{current_turn} P{player} Ph{phase}: Opponent Random {action}")
            else:
                action = 0

        # Apply action
        try:
            game.step(action)
        except Exception as e:
            print(f"Error applying action {action}: {e}")
            traceback.print_exc()
            break

    end_time = time.time()
    duration = end_time - start_time

    print(f"Game Finished. Winner: {game.get_winner()}")
    print(
        f"Duration: {duration:.2f}s for {step_count} steps ({(step_count / duration) if duration > 0 else 0:.1f} steps/sec)"
    )


if __name__ == "__main__":
    main()
