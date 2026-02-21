from compiler.parser import AbilityParser

text = """{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを2枚引く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）"""

# Just call the public method
abilities = AbilityParser.parse_ability_text(text)
for i, ab in enumerate(abilities):
    print(f"\nAbility {i}:")
    for j, eff in enumerate(ab.effects):
        # We need to access EffectType names
        print(f"  Effect {j}: {eff.effect_type} (value={eff.value})")
