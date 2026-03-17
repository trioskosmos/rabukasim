import os
import sys

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from engine.models.ability import Ability, AbilityCostType, Cost, Effect, EffectType, TargetType, TriggerType


def debug_compile():
    # Helper to print bytecode with opcode names
    from engine.models.opcodes import Opcode

    op_map = {v.value: k for k, v in Opcode.__members__.items()}

    def print_bytecode(bc):
        print("\n--- Bytecode ---")
        # Ensure bc is a list or array
        if not isinstance(bc, (list, np.ndarray)):
            print(f"Bytecode is not list/array: {type(bc)}")
            return

        print(f"Raw Bytecode Length: {len(bc)}")

        # Iterate in chunks of 4
        for i in range(0, len(bc), 4):
            if i + 3 >= len(bc):
                print(f"Incomplete trailing bytes: {bc[i:]}")
                break

            op = bc[i]
            val = bc[i + 1]
            attr = bc[i + 2]
            target = bc[i + 3]
            op_name = op_map.get(op, f"UNKNOWN({op})")
            print(f"[{i // 4:<2}] OP: {op:<3} ({op_name:<15}) | V: {val:<3} | A: {attr:<3} | S: {target:<3}")

    # Reconstruct Card 134 Ability based on User JSON
    #         {
    #           "raw_text": "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る その中から1枚を手札に加え、残りを控え室に置く",
    #           "trigger": 1,
    #           "effects": [
    #             { "effect_type": 4, "value": 3, "target": 0, "params": { "from": "discard", "zone_accounted": true }, "is_optional": true },
    #             { "effect_type": 27, "value": 1, "target": 0, "params": { "source": "looked", "on_fail": "discard", "from": "discard", "zone_accounted": true }, "is_optional": false }
    #           ],
    #           "costs": [
    #             { "type": 3, "value": 1, "params": {}, "is_optional": true }
    #           ],
    #           "is_once_per_turn": false
    #         }

    print("--- Reconstructing Ability ---")

    # Cost: Discard 1 from Hand (Optional)
    cost1 = Cost(type=AbilityCostType.DISCARD_HAND, value=1, is_optional=True)

    # Effect 1: Look at 3 cards from Deck
    eff1 = Effect(effect_type=EffectType.LOOK_DECK, value=3, target=TargetType.SELF)
    eff1.params = {"from": "discard", "zone_accounted": True}
    eff1.is_optional = True  # NOTE: Logic might handle this differently?

    # Effect 2: Add 1 to hand from looked cards
    eff2 = Effect(effect_type=EffectType.ADD_TO_HAND, value=1, target=TargetType.SELF)
    eff2.params = {"source": "looked", "on_fail": "discard", "from": "discard", "zone_accounted": True}

    ability = Ability(
        raw_text="Test Ability", trigger=TriggerType.ON_PLAY, effects=[eff1, eff2], costs=[cost1], conditions=[]
    )

    print("Compiling...")
    try:
        bytecode = ability.compile()
        print_bytecode(bytecode)
    except Exception as e:
        print(f"Compilation Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_compile()
