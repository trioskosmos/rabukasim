from game.ability import AbilityParser

text = "必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。"
abilities = AbilityParser.parse_ability_text(text)

print(f"Text: {text}")
print(f"Parsed Abilities: {len(abilities)}")
for i, ab in enumerate(abilities):
    print(f"[{i}] Trigger: {ab.trigger.name}")
    for eff in ab.effects:
        print(f"    Effect: {eff.effect_type.name} Params: {eff.params}")
