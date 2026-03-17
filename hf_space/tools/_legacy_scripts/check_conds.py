from compiler.parser import AbilityParser

# SD1-007: 東條 希 - Place 5 cards from deck to discard, if live card draw 1
text_007 = "{{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。"

abilities_007 = AbilityParser.parse_ability_text(text_007)
for i, ab in enumerate(abilities_007):
    print(f"Ability {i}:")
    print(f"  Trigger: {ab.trigger.name} ({ab.trigger.value})")
    print(f"  Conditions: {len(ab.conditions)}")
    for j, cond in enumerate(ab.conditions):
        print(f"    Cond {j}: {cond.type.name} ({cond.type.value}) params={cond.params}")
    print(f"  Effects: {len(ab.effects)}")
    for j, eff in enumerate(ab.effects):
        print(f"    Eff {j}: {eff.effect_type.name} ({eff.effect_type.value}) val={eff.value}")
