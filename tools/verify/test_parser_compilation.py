
from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import Ability, Opcode

import re
parser = AbilityParserV2()
text = "TRIGGER: ON_PLAY\nEFFECT: LOOK_AND_CHOOSE_REVEAL(3) {FILTER=\"COST_GE=11\"} -> CARD_HAND, DISCARD_REMAINDER (Optional)"

# Debug the regex
p = "LOOK_AND_CHOOSE_REVEAL(3) {FILTER=\"COST_GE=11\"} -> CARD_HAND, DISCARD_REMAINDER (Optional)"
m = re.match(r"(\w+)(?:\((.*?)\))?(?:\s*\{.*?\}\s*)?(?:\s*->\s*([\w, ]+))?(.*)", p)
if m:
    name, val, target_name, rest = m.groups()
    print(f"Regex Match: name={name}, val={val}, target_name={target_name}, rest='{rest}'")
else:
    print("Regex Failed to match")

abilities = parser.parse(text)

for ab in abilities:
    print(f"Ability: {ab.trigger}")
    for eff in ab.effects:
        print(f"  Effect: {eff.effect_type.name}, Optional: {eff.is_optional}, Target: {eff.target}, Params: {eff.params}")
        bytecode = []
        ab._compile_single_effect(eff, bytecode)
        print(f"  Compiled Bytecode: {bytecode}")
        if len(bytecode) == 4:
            op, v, a, s = bytecode
            print(f"    Op: {op}, V: {v}, A: {a} (Hex: {hex(a & 0xFFFFFFFF)}), S: {s}")
