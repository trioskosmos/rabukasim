import json

import engine_rust


def setup_test_gs():
    cards_json = {
        "members": {
            str(i): {
                "card_id": i,
                "card_no": f"M{i}",
                "name": f"M{i}",
                "rarity": "N",
                "group": "Aqours",
                "unit": "CYaRon!",
                "hearts": [0] * 7,
                "blades": 1,
                "hand_count": 0,
                "deck_count": 0,
                "abilities": [],
            }
            for i in range(1, 51)
        },
        "lives": {
            str(i): {
                "card_id": i,
                "card_no": f"L{i}",
                "name": f"L{i}",
                "rarity": "N",
                "group": "Aqours",
                "points": 1,
                "hearts": [1, 0, 0, 0, 0, 0, 0],
                "abilities": [],
            }
            for i in range(101, 111)
        },
    }
    db = engine_rust.PyCardDatabase(json.dumps(cards_json))
    gs = engine_rust.PyGameState(db)
    return gs, db


def test_draw_until():
    print("Testing O_DRAW_UNTIL...")
    print(f"engine_rust file: {engine_rust.__file__}")
    print(f"PyPlayerState attributes: {[x for x in dir(engine_rust.PyPlayerState) if 'buff' in x]}")
    gs, db = setup_test_gs()
    # Provide 20 cards in deck to avoid exhaustion
    deck = list(range(1, 21))
    gs.initialize_game(deck, [], deck, [], [], [])

    p0 = gs.get_player(0)
    p0.hand = []
    gs.set_player(0, p0)

    ps_before = gs.get_player(0)
    print(f"  Hand size BEFORE: {len(ps_before.hand)}")

    gs.phase = 4  # Main

    # O_DRAW_UNTIL(3): opcode 66, v=3
    bytecode = [66, 3, 0, 0, 201, 0, 0, 0]
    gs.debug_execute_bytecode(bytecode, 0, -1, -1, -1, -1, 0)

    ps_after = gs.get_player(0)
    print(f"  Hand size AFTER: {len(ps_after.hand)}")
    assert len(ps_after.hand) == 3


def test_pay_energy():
    print("Testing O_PAY_ENERGY...")
    gs, db = setup_test_gs()
    p0 = gs.get_player(0)
    p0.energy_zone = [1, 2, 3]
    p0.tapped_energy = [False, False, False]
    gs.set_player(0, p0)

    # O_PAY_ENERGY(2): opcode 64, v=2
    bytecode = [64, 2, 0, 0, 201, 0, 0, 0]
    gs.debug_execute_bytecode(bytecode, 0, -1, -1, -1, -1, 0)

    ps = gs.get_player(0)
    print(f"  Energy: {len(ps.energy_zone)}, Discard: {len(ps.discard)}")
    assert len(ps.energy_zone) == 1
    assert len(ps.discard) == 2


def test_swap_area():
    print("Testing O_SWAP_AREA (with buff swap check)...")
    gs, db = setup_test_gs()
    gs.set_stage_card(0, 0, 1)
    gs.set_stage_card(0, 1, 2)

    # Set some buffs on Slot 0 using METHODS
    p0 = gs.get_player(0)
    hb = [[0] * 7 for _ in range(3)]
    hb[0] = [5, 0, 0, 0, 0, 0, 0]  # 5 Red hearts on Slot 0
    p0.set_heart_buffs(hb)
    p0.set_blade_buffs([10, 0, 0])  # 10 blades on Slot 0
    gs.set_player(0, p0)

    # O_SWAP_AREA(0, 1): opcode 72, a=0, s=1
    bytecode = [72, 0, 0, 1, 201, 0, 0, 0]
    gs.debug_execute_bytecode(bytecode, 0, -1, -1, -1, -1, 0)

    ps = gs.get_player(0)
    print(f"  Slot 0 member: {ps.stage[0]} (Blades: {ps.get_blade_buffs()[0]})")
    print(f"  Slot 1 member: {ps.stage[1]} (Blades: {ps.get_blade_buffs()[1]})")

    assert ps.stage[0] == 2
    assert ps.stage[1] == 1
    assert ps.get_blade_buffs()[1] == 10
    assert ps.get_heart_buffs()[1][0] == 5


def test_play_from_discard():
    print("Testing O_PLAY_MEMBER_FROM_DISCARD...")
    gs, db = setup_test_gs()
    p0 = gs.get_player(0)
    p0.discard = [1, 2]  # M1 and M2
    gs.set_player(0, p0)

    # O_PLAY_MEMBER_FROM_DISCARD to Slot 2
    # Choice Index = 0 (M1), Target Slot = 2, Opcode 63
    bytecode = [63, 0, 0, 0, 201, 0, 0, 0]
    gs.debug_execute_bytecode(bytecode, 0, -1, -1, 2, 0, 0)

    # Dump rule log for debugging
    for line in gs.rule_log:
        print(f"  LOG: {line}")

    ps = gs.get_player(0)
    print(f"  Stage Slot 2: {ps.stage[2]}, Discard: {list(ps.discard)}")
    assert ps.stage[2] == 1
    assert list(ps.discard) == [2]


def test_reveal():
    print("Testing O_REVEAL...")
    gs, db = setup_test_gs()
    deck = list(range(1, 11))
    gs.initialize_game(deck, [], deck, [], [], [])

    # O_REVEAL(2): opcode 40, v=2
    bytecode = [40, 2, 0, 0, 201, 0, 0, 0]
    gs.debug_execute_bytecode(bytecode, 0, -1, -1, -1, -1, 0)

    log = gs.rule_log
    reveal_log = [l for l in log if "REVEAL 2 cards" in l]
    print(f"  Reveal logs found: {len(reveal_log)}")
    assert len(reveal_log) > 0


if __name__ == "__main__":
    try:
        test_draw_until()
        test_pay_energy()
        test_swap_area()
        test_play_from_discard()
        test_reveal()
        print("\nALL BATCH 1 TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback

        traceback.print_exc()
