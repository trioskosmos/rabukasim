import json
import sys
sys.path.insert(0, '.')
from compiler.parser_v2 import parse_ability_text

pseudocode = '''TRIGGER: ON_PLAY
COST: TAP_MEMBER (Optional)
EFFECT: LOOK_AND_CHOOSE_ORDER(2) {REMAINDER="DISCARD"}'''

print('Parsing pseudocode:')
print(pseudocode)
print()

result = parse_ability_text(pseudocode)
print('Parsed result:')
for ability in result:
    print(json.dumps(ability.to_dict(), indent=2, ensure_ascii=False))
