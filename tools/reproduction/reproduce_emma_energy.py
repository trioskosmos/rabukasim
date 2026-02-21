import os
import sys

# Add engine to path
sys.path.insert(0, os.path.abspath("."))

from engine_rust import PyCardDatabase, PyGameState

from engine.game.enums import Phase


def test_emma_energy_repro_baton():
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        cards_json = f.read()
    db = PyCardDatabase(cards_json)
    gs = PyGameState(db)

    # 905 is Emma (Cost 7)
    # 100 is a dummy card for energy
    # We need a cost 2 card to baton pass over.
    # Let's find one. PL!N-sd1-002 is cost 2. Card ID 899.

    p0_deck = [905] * 10
    p1_deck = [905] * 10
    p0_energy = [100] * 6  # User says they have 6 energy
    p1_energy = [100] * 6
    p0_lives = [200] * 10
    p1_lives = [200] * 10

    gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    # Skip to Main Phase
    while int(gs.phase) < int(Phase.MAIN):
        ids = gs.get_legal_action_ids()
        if not ids:
            break
        gs.step(ids[0])

    print(f"Phase at start of Main: {gs.phase}")

    # NOW set the energy for the test
    p0 = gs.get_player(0)
    p0.energy_zone = [100] * 6  # 6 cards in zone
    p0.tapped_energy = [False] * 6  # 6 untapped

    # In Python, p0.stage returns a copy, so we must set the whole array
    new_stage = list(p0.stage)
    new_stage[1] = 69  # Cost 2 card (PL!-bp3-009-P)
    p0.stage = new_stage

    # Ensure Emma is in hand at index 0
    p0.hand = [905] + list(p0.hand)[1:]
    gs.set_player(0, p0)

    print(f"Initial Untapped Energy: {gs.get_player(0).tapped_energy.count(False)}")

    # Play Emma from hand at index 0 to slot 1 (Baton Pass)
    # action_id = 1010

    print("\n--- Playing Emma Verde (Cost 7) over Cost 2 card (Net Cost 5) ---")
    try:
        gs.step(1010)
    except Exception as e:
        print(f"FAILED with error: {e}")

    player = gs.get_player(0)
    print(f"After Play - Phase: {gs.phase}")
    untapped_count = player.tapped_energy.count(False)
    print(f"After Play - Untapped Count: {untapped_count}")
    print(f"After Play - Tapped Count: {player.tapped_energy.count(True)}")

    print("\n--- Game Logs ---")
    for log in gs.rule_log:
        print(log)
    # FINAL CHECK
    expected_untapped = 3
    if untapped_count == expected_untapped:
        print(f"\nSUCCESS: Exactly {untapped_count} energy cards were reactivated. (Initial 6 - 5 + 2 = 3)")
    else:
        print(f"\nFAILURE: Expected {expected_untapped} untapped energy, found {untapped_count}")

    if untapped_count == 3:  # This was the original expected value, now it's the primary check
        print("\nSUCCESS: Exactly 3 energy cards were reactivated. (Initial 6 - 5 + 2 = 3)")
    else:
        print(f"\nFAILURE: Expected 3 untapped energy, found {untapped_count}")


if __name__ == "__main__":
    test_emma_energy_repro_baton()
