import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import AbilityCostType
from engine.models.opcodes import Opcode

def test_silent_cost_failure():
    parser = AbilityParserV2()
    
    # TAP_MEMBER (20) and DISCARD_ENERGY (8) are missing from the mapping in engine/models/ability.py
    text = "TRIGGER: ACTIVATED\nCOST: TAP_MEMBER(0), DISCARD_ENERGY(1)\nEFFECT: DRAW(1) -> PLAYER"
    
    abilities = parser.parse(text)
    assert len(abilities) == 1
    ab = abilities[0]
    
    print(f"Abilities costs: {[c.type.name for c in ab.costs]}")
    
    bytecode = ab.compile()
    print(f"Compiled Bytecode: {bytecode}")
    
    # Each instruction is 4 bytes.
    # TAP_MEMBER opcode is 53
    # MOVE_TO_DISCARD opcode is 58
    has_tap = any(bytecode[i] == 53 for i in range(0, len(bytecode), 4))
    has_discard = any(bytecode[i] == 58 for i in range(0, len(bytecode), 4))
    
    if not has_tap:
        print("FAIL: TAP_MEMBER cost missing from bytecode")
    if not has_discard:
        print("FAIL: DISCARD_ENERGY cost missing from bytecode")
        
    if has_tap and has_discard:
        print("SUCCESS: Both costs found in bytecode")
    else:
        sys.exit(1)

if __name__ == "__main__":
    try:
        test_silent_cost_failure()
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
