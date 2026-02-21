from compiler.parser import AbilityParser

# SD1-007: 東條 希 - Place 5 cards from deck to discard, if live card draw 1
text_007 = "{{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。"

# SD1-008: 小泉 花陽 - Activate 2 energy
text_008 = "{{toujyou.png|登場}}エネルギーを2枚アクティブにする。"

print("=== SD1-007 ===")
print(f"Text: {text_007}")
abilities_007 = AbilityParser.parse_ability_text(text_007)
for i, ab in enumerate(abilities_007):
    print(f"Ability {i}: Trigger={ab.trigger.name} ({ab.trigger.value})")
    for j, eff in enumerate(ab.effects):
        print(
            f"  Effect {j}: {eff.effect_type.name} ({eff.effect_type.value}) val={eff.value} target={eff.target.name}"
        )
        if eff.params:
            print(f"    Params: {eff.params}")

print("\n=== SD1-008 ===")
print(f"Text: {text_008}")
abilities_008 = AbilityParser.parse_ability_text(text_008)
for i, ab in enumerate(abilities_008):
    print(f"Ability {i}: Trigger={ab.trigger.name} ({ab.trigger.value})")
    for j, eff in enumerate(ab.effects):
        print(
            f"  Effect {j}: {eff.effect_type.name} ({eff.effect_type.value}) val={eff.value} target={eff.target.name}"
        )
        if eff.params:
            print(f"    Params: {eff.params}")
