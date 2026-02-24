import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import AbilityCostType

def debug_ren():
    text = "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『Liella!』のカードを1枚まで公開して手札に加えてもよい。残りを控え室に置く。"
    parser = AbilityParserV2()
    abilities = parser.parse(text)
    
    print(f"Abilities found: {len(abilities)}")
    for i, ab in enumerate(abilities):
        print(f"\nAbility {i}:")
        print(f"  Trigger: {ab.trigger}")
        print(f"  Costs: {ab.costs}")
        for cost in ab.costs:
            print(f"    Cost Type: {cost.type}")
            print(f"    Optional: {cost.is_optional}")
        print(f"  Effects: {len(ab.effects)}")
        for eff in ab.effects:
            print(f"    Effect Type: {eff.effect_type}")
            print(f"    Optional: {eff.is_optional}")

if __name__ == "__main__":
    debug_ren()
