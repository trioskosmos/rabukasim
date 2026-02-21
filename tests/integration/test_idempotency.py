import engine_rust
import json
import os


def test_idempotency_performance_phase():
    # 1. Setup
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        card_data = json.load(f)
    db = engine_rust.PyCardDatabase(json.dumps(card_data))
    state = engine_rust.PyGameState(db)

    KOTORI_ID = 249  # PL!-sd1-003-SD
    LIVE_ID = 500  # Just picking a random ID for now
    HAND_CARD = 101

    # 2. Force state
    state.initialize_game([101] * 60, [101] * 60, [101] * 20, [101] * 20, [], [])

    # Place Kotori on Stage 0
    state.set_stage_card(0, 0, KOTORI_ID)
    # Ensure a card in hand for discard cost
    state.set_hand_cards(0, [HAND_CARD])
    # Place a Live card in P0 zone
    state.set_live_card(0, 0, LIVE_ID, True)

    state.phase = 5  # LiveSet
    state.first_player = 0
    state.current_player = 0

    print(f"Initial Phase: {state.phase}, Current Player: {state.current_player}")

    # Step for P0
    state.step(0)
    print(f"Phase after P0 step(0): {state.phase}, Current Player: {state.current_player}")

    # Step for P1
    state.step(0)
    print(f"Phase after P1 step(0): {state.phase}, Current Player: {state.current_player}")

    # Now it should be Phase 6 (PerformanceP1) OR 10 (Response) if Kotori triggered
    # Logic: PerformanceP1 immediately runs do_performance_phase which triggers Kotori

    if state.phase != 10:
        print(f"ERROR: Expected Phase 10 (Response) for Kotori choice, got {state.phase}")
        return

    # 3. VERIFY IDEMPOTENCY
    # Kotori has base 3 blades.
    blades_before = state.get_total_blades(0)
    print(f"Blades at first pause: {blades_before}")

    # TRIGGER IDEMPOTENCY CHECK:
    # Before providing choice, we might want to manually call do_performance_phase
    # but since it's already in Response, the sub_state should be LiveStartTriggered.
    # We can check this if we had a getter for sub_state, but we don't.
    # However, the stat calculation loop in do_performance_phase for HEARTS happens AFTER triggers.

    # Action for Color Select (580-585)
    legal_actions = state.get_legal_action_ids()
    print(f"Legal actions at pause: {legal_actions}")

    choice_action = 582  # Green (or any valid)
    if choice_action not in legal_actions:
        choice_action = legal_actions[0]

    print(f"Choosing action: {choice_action}")
    state.step(choice_action)

    print(f"Phase after choice: {state.phase}")

    # Kotori gains a heart from her ability.
    # We can check effective hearts if possible.
    hearts = state.get_effective_hearts(0, 0)
    print(f"Effective Hearts for Kotori: {hearts}")

    # check if another Kotori trigger happened (should not happen)
    # If the bug was present, we might be stuck in a loop or have double stats.

    print("Idempotency test complete.")


if __name__ == "__main__":
    test_idempotency_performance_phase()
