import sys
sys.path.append('.')
from compiler.parser_v2 import AbilityParserV2

parser = AbilityParserV2()
text = "TRIGGER: ON_LIVE_SUCCESS\nEFFECT: DRAW(2); DISCARD_HAND(1)"
print("Parsing text:", repr(text))

try:
    abilities = parser.parse(text)
    print(f"Parsed {len(abilities)} abilities")
    for idx, ab in enumerate(abilities):
        print(f"\nAbility {idx}:")
        print(f"  Trigger: {ab.trigger}")
        print(f"  Effects: {len(ab.effects)}")
        for e in ab.effects:
            print(f"    - {e.effect_type} / val={e.value} / params={e.params}")
        print(f"  Instructions (ordered): {len(ab.instructions)}")
        for i, inst in enumerate(ab.instructions):
            if hasattr(inst, "effect_type"):
                print(f"    {i}: [EFFECT] {inst.effect_type} val={inst.value} params={inst.params}")
            elif hasattr(inst, "type"):
                print(f"    {i}: [COND/COST] {inst.type}")
            else:
                print(f"    {i}: [UNKNOWN] {type(inst)}")
        
        # Test compilation
        print(f"  Compiled bytecode: {ab.compile()}")
except Exception as e:
    import traceback
    traceback.print_exc()
