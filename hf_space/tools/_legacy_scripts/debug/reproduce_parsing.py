import os
import sys

# Add workspace to path
sys.path.append(os.getcwd())

from compiler.parser_v2 import parse_ability_text

text = (
    "自分か相手を選ぶ。自分は、そのプレイヤーのデッキの一番上のカードを見る。自分はそのカードを控え室に置いてもよい。"
)

print(f"Parsing text: {text}")
abilities = parse_ability_text(text)

print(f"\nFound {len(abilities)} abilities.")

for i, ab in enumerate(abilities):
    print(f"\n--- Ability {i} ---")
    print(f"Trigger: {ab.trigger.name}")
    print(f"Effects: {len(ab.effects)}")
    for j, eff in enumerate(ab.effects):
        print(f"  Effect {j}: {eff.effect_type.name}")
        print(f"    Target: {eff.target.name}")
        print(f"    Value: {eff.value}")
        print(f"    Params: {eff.params}")
        print(f"    Optional: {eff.is_optional}")

    print(f"Bytecode: {ab.compile()}")
