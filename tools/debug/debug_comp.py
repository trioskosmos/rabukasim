from compiler.parser_v2 import AbilityParserV2
import json

parser = AbilityParserV2()
text = "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。"
abilities = parser.parse(text)

for ab in abilities:
    print(f"Trigger: {ab.trigger}")
    for eff in ab.effects:
        print(f"  Effect Type: {eff.effect_type}")
        print(f"  Target: {eff.target}")
        print(f"  Value: {eff.value}")
        print(f"  Params: {eff.params}")
