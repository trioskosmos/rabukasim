from engine.game.game_state import GameState, Phase


def test_auto_phase():
    print("--- Testing Auto Phase Transitions ---")
    gs = GameState()
    gs.players[0].main_deck = [1, 2, 3, 4, 5]
    gs.players[0].energy_deck = [200, 201]

    # Start at ACTIVE phase (transitions to ENERGY)
    gs.phase = Phase.ACTIVE
    gs.current_player = 0
    print(f"Start Phase: {gs.phase}")

    # Step 0 (Pass/Auto) -> Should go to ENERGY
    gs = gs.step(0)
    print(f"After Step(0) (Expected ENERGY): {gs.phase}")

    if gs.phase == Phase.ENERGY:
        # Step 0 -> Should go to DRAW
        gs = gs.step(0)
        print(f"After Step(0) (Expected DRAW): {gs.phase}")

    if gs.phase == Phase.DRAW:
        # Step 0 -> Should go to MAIN
        gs = gs.step(0)
        print(f"After Step(0) (Expected MAIN): {gs.phase}")

    if gs.phase == Phase.MAIN:
        print("SUCCESS: Reached MAIN phase.")
    else:
        print(f"FAILURE: Stuck in {gs.phase}")


if __name__ == "__main__":
    test_auto_phase()
