
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from engine.models.opcodes import Opcode
from engine.models.ability import ConditionType, PackedFilterSpec, Ability, Condition

print(f"Opcode.CHECK_SUCCESS_PILE_COUNT: {getattr(Opcode, 'CHECK_SUCCESS_PILE_COUNT', 'MISSING')}")
print(f"Opcode.CHECK_COUNT_STAGE: {getattr(Opcode, 'CHECK_COUNT_STAGE', 'MISSING')}")

# Try to get as Enum member
try:
    print(f"Opcode(307): {Opcode(307)}")
except Exception as e:
    print(f"Opcode(307) error: {e}")

# Check packing logic for 4 characters
from engine.models.enums import CHAR_MAP
ability = Ability(raw_text="", trigger=0, effects=[])
cond = Condition(type=ConditionType.COUNT_STAGE, params={"name": "HONOKA/ELI/KOTORI/UMI"})
attr = ability._pack_filter_attr(cond)
print(f"Packed attr for 4 characters: {hex(attr)}")
from engine.models.ability import format_filter_attr
print(f"Summary: {format_filter_attr(attr)}")
decoded = PackedFilterSpec.unpack(attr)
print(f"Decoded: char1={decoded.char_id_1}, char2={decoded.char_id_2}, unit={decoded.unit_id}")
