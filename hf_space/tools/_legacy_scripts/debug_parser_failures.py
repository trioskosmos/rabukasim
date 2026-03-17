from compiler.parser import AbilityParser

test_cases = [
    {
        "id": "LL-PR-004-PR",
        "text": "{{live_start.png|ライブ開始時}}相手に何が好き？と聞く。\n回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。\n回答があなたの場合、自分と相手はカードを1枚引く。\n回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る。",
    },
    {
        "id": "PL!-bp4-005-P (Card 82)",
        "text": "{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。\n{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１する。\n{{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)",
    },
    {
        "id": "Card 647 (Onizuka Tomari)",
        "text": "{{toujyou.png|登場}}相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする：相手は自身の控え室からメンバーカードを1枚選び、公開する。自分はそのカードを手札に加える。",
    },
]

for case in test_cases:
    print(f"\n--- Testing {case['id']} ---")
    print(f"Text: {case['text']}")
    abilities = AbilityParser.parse_ability_text(case["text"])
    for i, a in enumerate(abilities):
        print(f"  Ability {i + 1}:")
        print(f"    Trigger: {a.trigger}")
        print(f"    Costs: {[c.type.name for c in a.costs]}")
        print(f"    Conditions: {[c.type.name for c in a.conditions]}")
        print(f"    Effects: {[e.effect_type.name for e in a.effects]}")
        for e in a.effects:
            if hasattr(e, "params") and e.params:
                print(f"      Effect Params: {e.params}")
