import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.ability import AbilityParser

text = "{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。"

print(f"Parsing Text: {text}")
abilities = AbilityParser.parse_ability_text(text)

with open("parser_debug.log", "w", encoding="utf-8") as f:
    f.write(f"Parsed {len(abilities)} abilities.\n")
    for i, ab in enumerate(abilities):
        f.write(f"Ability {i}: Trigger={ab.trigger}\n")
        f.write(f"Effects: {[int(e.effect_type) for e in ab.effects]}\n")
        for e in ab.effects:
            f.write(f"  - {int(e.effect_type)} ({e.effect_type.name}): Val={e.value}, Params={e.params}\n")
