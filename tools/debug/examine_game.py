import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

import lovecasim_engine as rust_engine


def examine_game():
    print("--- Game State Examination ---")

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        card_data_json = f.read()

    rust_db = rust_engine.PyCardDatabase(card_data_json)

    # Simple deck setup
    m_ids = [1, 2, 3]
    l_ids = [100, 101]
    p0_deck = (m_ids * 20)[:40]
    p1_deck = (m_ids * 20)[:40]
    p0_lives = (l_ids * 5)[:12]
    p1_lives = (l_ids * 5)[:12]

    gs = rust_engine.PyGameState(rust_db)
    gs.initialize_game_with_seed(p0_deck, p1_deck, [], [], p0_lives, p1_lives, 42)

    # Process through setup phases to get to Main Phase for better examination
    print(f"Initial Phase: {gs.phase} (Setup/Mulligan)")
    gs.step(0)  # P1 Mulligan
    gs.step(0)  # P2 Mulligan
    # Now in Active -> Energy -> Draw -> Main

    print("\n--- Game State (Main Phase) ---")
    print(f"Turn: {gs.turn}")
    print(f"Current Player: {gs.current_player}")
    print(f"Phase: {gs.phase}")

    for i in range(2):
        p = gs.get_player(i)
        print(f"\nPlayer {i}:")
        print(f"  Score: {p.score}")
        print(f"  Hand:  {p.hand[:10]}... (Total: {len(p.hand)})")
        print(f"  Stage: {p.stage}")
        print(f"  Energy Zone Size: {len(p.energy_zone)}")
        print(f"  Discard Pile Size: {len(p.discard)}")

    print("\nLegal Actions (Sample):")
    actions = gs.get_legal_action_ids()
    print(f"  Total Legal Actions: {len(actions)}")
    print(f"  First 10 IDs: {actions[:10]}")


if __name__ == "__main__":
    examine_game()
