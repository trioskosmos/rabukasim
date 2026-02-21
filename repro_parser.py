from compiler.parser_v2 import parse_ability_text
from engine.models.ability import Ability, EffectType

pseudocode = "TRIGGER: ON_PLAY\nCOST: DISCARD_HAND(1)\nEFFECT: LOOK_AND_CHOOSE(7) {filter=\"COLOR_BLUE,COLOR_YELLOW,COLOR_LTBLUE\", choose_count=3, destination=\"hand\"}\nEFFECT: SWAP_CARDS(target=\"discard\")"
print(f"Parsing pseudocode:\n{pseudocode}")
abilities = parse_ability_text(pseudocode)

if not abilities:
    print("No abilities parsed!")
else:
    effects = abilities[0].effects
    # Expected: 2nd effect is LOOK_AND_CHOOSE
    # Cost effects are separate? No, parser puts costs in .costs list.
    # Effects list contains effects.
    
    print(f"Found {len(effects)} effects.")
    for i, eff in enumerate(effects):
        print(f"Effect {i}: Type={eff.effect_type}, Val={eff.value}, Params={eff.params}")
        if eff.effect_type == EffectType.LOOK_AND_CHOOSE:
            print(f"  choose_count in params: {'choose_count' in eff.params}")
            print(f"  choose_count val: {eff.params.get('choose_count')}")

    # Test compilation logic directly
    print("Compiling ability...")
    try:
        bytecode = abilities[0].compile()
        print(f"Bytecode: {bytecode}")
    except Exception as e:
        print(f"Compilation failed: {e}")
