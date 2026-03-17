import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from compiler.parser import AbilityParser
from engine.models.ability import ConditionType

text = "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る その中からハートに{{heart_04.png|heart04}}を2個以上持つメンバーカードか、必要ハートの合計が2以上の『Liella!』のライブカードを1枚公開して手札に加えてもよい。残りのカードは控え室に置く。"

print(f"Parsing Text: {text}")

abilities = AbilityParser.parse_ability_text(text)

print(f"Found {len(abilities)} abilities.")

for i, ab in enumerate(abilities):
    print(f"\nAbility {i + 1}:")
    print(f"  Trigger: {ab.trigger}")
    print(f"  Conditions: {len(ab.conditions)}")
    print(f"  Effects: {len(ab.effects)}")
    for eff in ab.effects:
        print(f"    - Type: {eff.effect_type}")
        print(f"      Val: {eff.value}")
    for cond in ab.conditions:
        print(f"    - Type: {cond.type}")
        print(f"      Params: {cond.params}")
        if cond.type == ConditionType.COUNT_HEARTS:
            print(f"      -> Gating Flag: {cond.params.get('gating')}")
