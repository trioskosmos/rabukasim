from compiler.parser import AbilityParser

text = """{{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。"""

abilities = AbilityParser.parse_ability_text(text)
for i, ab in enumerate(abilities):
    print(f"\nAbility {i}:")
    print(f"  Trigger: {ab.trigger}")
    for j, eff in enumerate(ab.effects):
        print(f"  Effect {j}: {eff.effect_type.name} (value={eff.value}, target={eff.target.name})")
        if eff.params:
            print(f"    Params: {eff.params}")
