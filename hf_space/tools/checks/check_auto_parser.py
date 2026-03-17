import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.ability import AbilityParser

text = "{{jidou.png|自動}}相手のカードが控え室に置かれるたび、カードを1枚引く。"
abilities = AbilityParser.parse_ability_text(text)

for ab in abilities:
    print(f"Trigger: {ab.trigger.name} ({ab.trigger.value})")
    print(f"Conditions: {len(ab.conditions)}")
    for cond in ab.conditions:
        print(f"Condition: {cond.type.name} Params: {cond.params}")
    for eff in ab.effects:
        print(f"Effect: {eff.effect_type.name} Params: {eff.params}")
