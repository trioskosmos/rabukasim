import sys

sys.path.insert(0, "game")
from ability import AbilityParser

text = "{{toujyou.png|登場}}ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。"
abilities = AbilityParser.parse_ability_text(text)

print(f"Parsed {len(abilities)} abilities")
for i, ab in enumerate(abilities):
    print(f"Ability {i}: Trigger={ab.trigger.name}")
    for eff in ab.effects:
        print(f"  - Effect: {eff.effect_type.name} val={eff.value}")
        print(f"    Params: {eff.params}")
