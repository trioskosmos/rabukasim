import json
import re

# translations map: Normalized Japanese -> English
# Note: Using normalized text to match variations
translations_map = {
    # [14]
    "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。": "[Activate] Put this member from the stage into the waiting room: Add 1 Live card from your waiting room to your hand.",
    # [8]
    "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。": "[Activate] Put this member from the stage into the waiting room: Add 1 Member card from your waiting room to your hand.",
    # [7]
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 3 cards of your deck. Add 1 of them to your hand, and put the rest into the waiting room.",
    # [6]
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may pay (E): This member gets +2 Blades until the end of the live phase.",
    # [5]
    "(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)": "(When checking Heart requirements, ALL Blades revealed by Yell are treated as Hearts of any color.)",
    # [4]
    "{{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。": "[On Play] Draw 1 card, then put 1 card from your hand into the waiting room.",
    # [4] PL!N-bp3-009-R+
    "{{live_start.png|ライブ開始時}}控え室にあるメンバーカード2枚を好きな順番でデッキの一番下に置いてもよい：それらのカードのコストの合計が、6の場合、カードを1枚引く。合計が8の場合、ライブ終了時まで、{{icon_all.png|ハート}}を得る。合計が25の場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": '[Live Start] You may put 2 Member cards from your waiting room on the bottom of your deck in any order: If the total cost of those cards is 6, draw 1 card. If the total is 8, this member gets [Heart] until the end of the live phase. If the total is 25, this member gets "[Continuous] Live Score +1" until the end of the live phase.',
    # [4] PL!-bp4-005-R+
    "{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを1枚手札に加える。\n{{jyouji.png|常時}}{{center.png|センター}}ライブの合計スコアを＋１する。\n{{live_start.png|ライブ開始時}}自分のステージに{{icon_blade.png|ブレード}}を5つ以上持つ『μ's』のメンバーがいない場合、このメンバーはセンターエリア以外にポジションチェンジする。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)": "[On Play] Add 1 Member card with Cost 2 or less from your waiting room to your hand.\n[Continuous] [Center] Live Score +1.\n[Live Start] If you have no \"μ's\" members with 5 or more Blades on your stage, switch this member's position to a non-Center area.",
    # [4] PL!N-bp4-004-R+
    "{{live_start.png|ライブ開始時}}カードを1枚引く。相手のステージにいるコスト9以下のメンバーを1人までウェイトにする。\n{{live_start.png|ライブ開始時}}相手のステージにいるウェイト状態のメンバーの数まで、自分の控え室にある『虹ヶ咲』のメンバーカードを選ぶ。それらを好きな順番でデッキの上に置く。": "[Live Start] Draw 1 card. You may set up to 1 member with Cost 9 or less on your opponent's stage to Waiting state.\n[Live Start] Choose 'Nijigasaki' Member cards from your waiting room up to the number of members in Waiting state on your opponent's stage. Put them on the top of your deck in any order.",
    # [2] PL!N-bp1-002-R+
    "{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。\n{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。": "[On Play] Look at the top 3 cards of your deck. Put any number of them back on top of your deck in any order, and put the rest into the waiting room.\n[Activate] (E)(E), Put 1 card from your hand into the waiting room: Play this card from your waiting room onto the stage. This ability can only be used while this card is in the waiting room.",
    # [2] PL!N-bp1-003-R+
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。\n{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。": "[On Play] You may put 1 card from your hand into the waiting room: Add 1 'Nijigasaki' Live card from your waiting room to your hand.\n[Live Start] You may pay (E): Declare 1 Heart color. This member gets that Heart until the end of the live phase.",
    # [2] PL!N-bp1-006-R+
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：このターン、自分のステージに『虹ヶ咲』のメンバーが登場している場合、エネルギーを2枚アクティブにする。\n{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：カードを1枚引く。": "[Activate] [Turn 1] Put 1 card from your hand into the waiting room: If a 'Nijigasaki' member entered your stage this turn, activate 2 Energy.\n[Activate] [Turn 1] (E)(E): Draw 1 card.",
    # [2] PL!N-bp1-012-R+
    "{{jyouji.png|常時}}自分のライブ中のカードが3枚以上あり、その中に『虹ヶ咲』のライブカードを1枚以上含む場合、{{icon_all.png|ハート}}{{icon_all.png|ハート}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。\n{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。": "[Continuous] If you have 3 or more live cards in progress, including at least 1 'Nijigasaki' Live card, this member gets [Heart][Heart][Blade][Blade].\n[Activate] [Turn 1] (E)(E)(E): Add 1 Live card from your waiting room to your hand.",
}


def normalize(text):
    text = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r"[・、。：！\!？\?\s\(\)（）/]", "", text)
    return text


with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

with open("data/manual_translations_en.json", "r", encoding="utf-8") as f:
    existing = json.load(f)

# Create normalized map of our new translations for matching
norm_map = {normalize(k): v for k, v in translations_map.items()}

count = 0
for cid, card in cards.items():
    text = card.get("ability")
    if not text or text == "なし":
        continue

    # Check if we have a translation for this text (normalized)
    norm = normalize(text)
    if norm in norm_map and cid not in existing:
        existing[cid] = norm_map[norm]
        count += 1

with open("data/manual_translations_en.json", "w", encoding="utf-8") as f:
    json.dump(existing, f, indent=4, ensure_ascii=False)

print(f"Added {count} new translations to manual_translations_en.json")
