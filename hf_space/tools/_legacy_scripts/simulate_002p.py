import os
import sys

sys.path.append(os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "engine_rust_src"))

try:
    import engine_rust

    print(f"Loaded engine_rust from: {engine_rust.__file__}")
except ImportError:
    print("Failed to import engine_rust")
    sys.exit(1)


def run_test():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        json_str = f.read()
    db = engine_rust.PyCardDatabase(json_str)

    # ID 467 is PL!N-bp1-002-P
    target_id = 467

    gs = engine_rust.PyGameState(db)

    # Setup:
    # Hand: [467] + dummies
    # Discard: [467]
    # Energy: [1000, 1000] (2 energy)
    p0_hand = [target_id, 1001, 1002]
    p0_discard = [target_id]
    p0_energy = [1000, 1000, 1000]  # 3 energy just in case

    gs.initialize_game(
        [1001] * 30,
        [1001] * 30,  # Decks
        p0_energy,
        [1000] * 3,  # Energy
        [],
        [],  # Lives
    )

    # Override hand/discard
    gs.set_player(0, gs.get_player(0))  # Get mutable copy logic?
    # PyPlayerState wrapper logic in py_bindings might be needed

    # Actually initialize_game sets decks. Hand is drawn in Draw phase.
    # We want to force state.
    # PyGameState exposes `set_hand_cards`?
    # Let's check py_bindings.rs in Step 2482
    # `set_hand_cards(p_idx, cards)` exists!
    # `set_discard(val)` exists on PlayerState?
    # View `py_bindings.rs` line 87: `set_discard`.
    # But `gs.set_player` overwrites the whole player?
    # `gs.get_player(0)` returns a copy. We modify it and set it back.

    p0 = gs.get_player(0)
    p0.hand = p0_hand
    p0.discard = p0_discard

    # Force energy
    p0.energy_zone = p0_energy

    gs.set_player(0, p0)

    # Set phase to Main
    gs.phase = 4  # Main
    gs.current_player = 0

    print("=== State Initialized ===")

    # 1. Check Legal Actions - Should see Play 467 from Hand (Action 1000+)
    # Hand idx 0 is 467.
    # Slots 0, 1, 2.
    # Action 1000 + 0*100 + 0*10 + 0 = 1000 (Play Hand 0 to Slot 0)

    legal = gs.get_legal_action_ids()
    print(f"Legal Actions: {legal}")

    if 1000 in legal:
        print("Action 1000 (Play from Hand) available.")
        print("Executing Action 1000...")
        gs.step(1000)  # Play 467 to Slot 0

        # Should trigger O_ORDER_DECK (OnPlay) -> Response Phase (10)
        print(f"Phase after Play: {gs.phase}")
        print(f"Pending Opcode: {gs.pending_effect_opcode}")

        # O_ORDER_DECK = 25 (enum value?)
        # Let's assume it worked if phase is Response (10).
        if gs.phase == 10:
            print("Entered Response Phase (Choice Pending).")
            # Check Choices
            # Should be Action 600, 601, 602, 603 (0..3 cards + done?)
            # My fix made it 600..count

            legal_response = gs.get_legal_action_ids()
            print(f"Legal Response Actions: {legal_response}")

            # Choose 600 (First card)
            if 600 in legal_response:
                print("Executing Action 600 (Select Card 1)...")
                gs.step(600)

                # It iterates. Should still be in Response until Done?
                # Or 3 cards look -> choose order.
                # Usually loop until count exhausted or Done?
                # Pseudocode: LOOK_AND_CHOOSE_ORDER(3)

                print(f"Phase after Choice 1: {gs.phase}")
            else:
                print("Error: Action 600 not found!")
        else:
            print("Error: Did not enter Response phase!")

    else:
        print("Error: Action 1000 not legal!")

    print("=== Test 2: Activated from Discard ===")

    # Reset State for Test 2 - Recreate GS to clear 'moved_members_this_turn' etc
    gs = engine_rust.PyGameState(db)
    gs.initialize_game(
        [1001] * 30,
        [1001] * 30,
        p0_energy,
        [1000] * 3,
        [],
        [],
    )
    p0 = gs.get_player(0)
    p0.hand = [1001]
    p0.discard = [target_id]  # Put 002-P in discard
    p0.energy_zone = p0_energy

    gs.set_player(0, p0)
    gs.phase = 4  # Main
    gs.current_player = 0

    legal_2 = gs.get_legal_action_ids()
    print(f"Legal Actions (Discard Test): {legal_2}")

    if 2001 in legal_2:
        print("Action 2001 (Activate form Discard) FOUND!")

        print("Executing 2001...")
        gs.step(2001)

        print(f"Phase: {gs.phase}, Pending Opcode: {gs.pending_effect_opcode}")
        # Expecting Response Phase for Stage Selection
        # Opcode should be PLAY_MEMBER_FROM_DISCARD or similar?
        # Actually logic says: pending_effect_opcode = O_PLAY_MEMBER_FROM_DISCARD (if bytecode executed partially?)
        # Or cost paid?
        # Cost: PAY_ENERGY(2); DISCARD_HAND(1)
        # If cost paid, then Effect executes.
        # Effect: PLAY_MEMBER_FROM_DISCARD(1) -> SELF
        # This opcode forces choice of slot.

        legal_3 = gs.get_legal_action_ids()
        print(f"Legal Actions (Stage Select): {legal_3}")
        # Should be 560, 561, 562 (Slots)

        if 560 in legal_3 or 561 in legal_3:
            print("Stage Select Actions Present!")
        else:
            print("Stage Select MISSING!")

    else:
        print("Action 2001 MISSING!")
        # Debug why? Cost?
        # Cost: PAY_ENERGY(2)
        # We gave 3 energy.
        # DISCARD_HAND(1)
        # We gave 1 card in hand.

        # Check if ability index is correct?
        # Maybe DB has it as ability 0? (If OnPlay is separate list?)
        # No, `abilities` list contains all.

    print("\n=== Test 3: O_ORDER_DECK Permutations ===")
    gs = engine_rust.PyGameState(db)
    # Setup deck.
    p0_energy = [1000, 1000, 1000]
    # Pad with 6 dummies at END (Top) because init draws 6.
    # Stack: [Bot, ..., Mid, Top, Dummy, ..., Dummy]
    p0_deck = [1003, 1002, 1001] + [1000] * 6  # 1000 is dummy ID

    gs.initialize_game(
        p0_deck,
        [1000] * 30,
        p0_energy,
        [1000] * 3,
        [],
        [],
    )
    p0 = gs.get_player(0)
    # Deck is set by init.

    p0.hand = [target_id]
    gs.set_player(0, p0)
    gs.phase = 4
    gs.current_player = 0

    print("Playing 002-P to Slot 0 (Action 1000)...")
    gs.step(1000)

    p0 = gs.get_player(0)
    print(f"Looked Cards: {p0.looked_cards}")
    # Selection: Bottom(1002), Mid(1001), Top(1003)

    print(f"Legal before Index 1: {gs.get_legal_action_ids()}")
    print("Selecting Index 1 (Value 1002) for BOTTOM...")
    gs.step(601)  # Index 1

    print(f"Legal before Index 0 (Step 2): {gs.get_legal_action_ids()}")
    # Remaining: [1001, 1003] (1002 removed from idx 1)
    # 1001 is idx 0, 1003 is idx 1.

    print("Selecting Index 0 (Value 1001) for MIDDLE...")
    gs.step(600)  # Index 0 => 1001

    print(f"Legal before Index 0 (Step 3): {gs.get_legal_action_ids()}")
    # Remaining: [1003]
    print("Selecting Index 0 (Value 1003) for TOP...")
    gs.step(600)  # Index 0 => 1003

    p0 = gs.get_player(0)
    # Pushed to deck: Bot, Mid, Top.
    # Stack: [..., Bot, Mid, Top]
    # So deck[-1] is Top.
    print(f"Deck Top 3 (Expect [1002, 1001, 1003]): {p0.deck[-3:]}")


if __name__ == "__main__":
    run_test()
