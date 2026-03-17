import os
import sys

# Add parent directory to path to allow importing 'engine'
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from engine.game.game_state import GameState, create_sample_cards, initialize_game

    print("Initializing game...")
    game = initialize_game(use_real_data=True)

    print(f"Member DB size: {len(GameState.member_db)}")
    print(f"Live DB size: {len(GameState.live_db)}")

    sample_members, sample_lives = create_sample_cards()
    print(f"Sample Member DB size: {len(sample_members)}")

    # Check if we are using real data or sample data
    # Real data has ID 106 as Member? Or Live?
    # Sample data: 0-47 Members, 100-111 Lives.

    if 106 in GameState.member_db:
        print("Card 106 found in member_db.")
        m = GameState.member_db[106]
        print(f"Card 106: {m.name}, Type: Member")
    else:
        print("Card 106 NOT in member_db.")

    if 106 in GameState.live_db:
        print("Card 106 found in live_db.")
        l = GameState.live_db[106]
        print(f"Card 106: {l.name}, Type: Live")

    if 111 in GameState.member_db:
        print("Card 111 found in member_db.")
    else:
        print("Card 111 NOT in member_db.")

    if 111 in GameState.live_db:
        print("Card 111 found in live_db.")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
