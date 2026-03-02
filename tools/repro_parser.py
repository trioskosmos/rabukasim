import os
import sys

sys.path.append(os.getcwd())
from compiler.parser_v2 import AbilityParserV2

pseudocode = 'LOOK_AND_CHOOSE_REVEAL(3, choose_count=1) {TARGET=HAND, REMAINDER="DISCARD"}'
print(f"Parsing: {pseudocode}")

parser = AbilityParserV2()
abilities = parser.parse(pseudocode)

print(f"Result Abilities: {len(abilities)}")
for i, ab in enumerate(abilities):
    print(f"Ability {i}: Trigger={ab.trigger}")
    for eff in ab.effects:
        print(f"  Effect: {eff.effect_type} Val={eff.value} Params={eff.params}")
