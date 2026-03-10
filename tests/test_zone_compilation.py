import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from engine.models.ability import Ability, Effect, EffectType, TargetType, TriggerType


def test_p_to_hand():
    # Construct manually to avoid parser aliases
    eff = Effect(EffectType.PLAY_MEMBER_FROM_DISCARD, params={"zone": "SUCCESS_PILE"}, target=TargetType.CARD_HAND)
    # Ability(raw_text, trigger, effects, ...)
    ability = Ability(raw_text="TEST_RAW", card_no="TEST", trigger=TriggerType.ON_PLAY, effects=[eff])

    print("\n--- Testing Success Pile Source (Manual) ---")
    bytecode = ability.compile()
    print(f"Bytecode: {bytecode}")

    found = False
    for i in range(0, len(bytecode), 5):
        if bytecode[i] == 63:  # PLAY_MEMBER_FROM_DISCARD
            slot = bytecode[i + 4]
            src_zone = (slot >> 16) & 0xFF
            print(f"Found Opcode 63, slot: {hex(slot)}, src_zone: {src_zone}")
            expected_zone = 16  # SUCCESS_PILE
            assert src_zone == expected_zone, f"Expected zone {expected_zone}, got {src_zone}"
            found = True
            break

    assert found, "Opcode 63 not found in bytecode"
    print("✓ Success Pile Source verified.")


def test_e_filter():
    # Construct MOVE_MEMBER manually
    eff = Effect(EffectType.MOVE_MEMBER, params={"zone": "ENERGY"}, target=TargetType.MEMBER_SELF)
    ability = Ability(raw_text="TEST_RAW", card_no="TEST", trigger=TriggerType.ON_PLAY, effects=[eff])

    print("\n--- Testing Energy Zone Filter (Manual) ---")
    bytecode = ability.compile()
    print(f"Bytecode: {bytecode}")

    found = False
    for i in range(0, len(bytecode), 5):
        if bytecode[i] == 20:  # MOVE_MEMBER
            a_low = bytecode[i + 2]
            a_high = bytecode[i + 3]
            attr = (a_high << 32) | (a_low & 0xFFFFFFFF)
            z_mask = (attr >> 53) & 0x1F
            print(f"Found Opcode 20, attr: {hex(attr)}, z_mask: {z_mask}")
            expected_mask = 3  # ENERGY
            assert z_mask == expected_mask, f"Expected mask {expected_mask}, got {z_mask}"
            found = True
            break

    assert found, "Opcode 20 not found in bytecode"
    print("✓ Energy Zone Filter verified.")


def test_setsuna_sid():
    # Testing Setsuna (CHARACTER filter)
    eff = Effect(EffectType.SELECT_MEMBER, params={"CHARACTER": "優木 せつ菜"}, target=TargetType.MEMBER_SELECT)
    ability = Ability(raw_text="TEST_RAW", card_no="TEST", trigger=TriggerType.ON_PLAY, effects=[eff])

    print("\n--- Testing Setsuna Special ID (Manual) ---")
    bytecode = ability.compile()

    found = False
    for i in range(0, len(bytecode), 5):
        if bytecode[i] == 65:  # SELECT_MEMBER
            a_low = bytecode[i + 2]
            a_high = bytecode[i + 3]
            attr = (a_high << 32) | (a_low & 0xFFFFFFFF)
            sid = (attr >> 58) & 0x07
            print(f"Found Opcode 65, attr: {hex(attr)}, special_id: {sid}")
            assert sid == 5, f"Expected special_id 5, got {sid}"
            found = True
            break
    assert found, "Opcode 65 not found in bytecode"
    print("✓ Setsuna Special ID (5) verified.")


def test_keyword_member_bit15():
    # Keyword Member manually
    eff = Effect(EffectType.SELECT_MEMBER, params={"KEYWORD_MEMBER": True}, target=TargetType.MEMBER_SELECT)
    ability = Ability(raw_text="TEST_RAW", card_no="TEST", trigger=TriggerType.ON_PLAY, effects=[eff])

    print("\n--- Testing Keyword Member Bit 15 (Manual) ---")
    bytecode = ability.compile()

    found = False
    for i in range(0, len(bytecode), 5):
        if bytecode[i] == 65:  # SELECT_MEMBER
            a_low = bytecode[i + 2]
            a_high = bytecode[i + 3]
            attr = (a_high << 32) | (a_low & 0xFFFFFFFF)
            kw_m = (attr >> 15) & 0x01
            print(f"Found Opcode 65, attr: {hex(attr)}, keyword_member: {kw_m}")
            assert kw_m == 1, f"Expected bit 15 to be set, got {kw_m}"
            found = True
            break
    assert found, "Opcode 65 not found in bytecode"
    print("✓ Keyword Member bit 15 verified.")


if __name__ == "__main__":
    try:
        test_p_to_hand()
        test_e_filter()
        test_setsuna_sid()
        test_keyword_member_bit15()
        print("\nAll isolated zone and bit layout tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
