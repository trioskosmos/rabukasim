import sys
import json
sys.path.append('.')
from compiler.main import compile_cards, _consolidated_abilities, _v2_parser

# Overwrite sys.stdout to catch print statements
with open("data/cards.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

card_no = "PL!S-bp2-024-L"
item = raw_data[card_no]

raw_jp = str(item.get("ability", ""))
if raw_jp in _consolidated_abilities:
    entry = _consolidated_abilities[raw_jp]
    if isinstance(entry, dict):
        raw_ability = entry.get("pseudocode", raw_jp)
    else:
        raw_ability = entry
else:
    raw_ability = str(item.get("pseudocode", raw_jp))

print(f"Parsing raw_ability for {card_no}:")
print(repr(raw_ability))

abilities = _v2_parser.parse(raw_ability)
print(f"Parsed {len(abilities)} abilities")
for idx, ab in enumerate(abilities):
    print(f"  Ability {idx} triggered by {ab.trigger}")
    try:
        bytecode = ab.compile()
        print(f"  Bytecode: {bytecode}")
    except Exception as e:
        import traceback
        traceback.print_exc()
