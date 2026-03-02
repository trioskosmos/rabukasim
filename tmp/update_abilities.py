import json
import os

path = 'data/consolidated_abilities.json'
with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)

# Card 126 (Nozomi)
nozomi_jp = "{{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。"
d[nozomi_jp] = {
    "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: MOVE_TO_DISCARD(5) FROM=DECK_TOP -> REVEALED\nEFFECT: CONDITION: COUNT_REVEALED(PLAYER) {FILTER=\"TYPE_LIVE\", MIN=1}; DRAW(1)",
    "cards": ["PL!-sd1-007-SD"]
}

# Card 590 (Chisato)
chisato_jp = "{{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる。"
d[chisato_jp] = {
    "pseudocode": "TRIGGER: ON_PLAY\nCONDITION: COUNT_STAGE {MIN=3, ALL=TRUE, FILTER=\"GROUP_ID=3\"}\nEFFECT: SWAP_AREA(ROTATE_LEFT, PLAYER=ALL_PLAYERS)",
    "cards": ["PL!SP-pb1-003-P＋", "PL!SP-pb1-003-R"]
}

# Card 418 (Dia)
dia_jp = "{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。"
d[dia_jp] = {
    "pseudocode": "TRIGGER: NONE\nEFFECT: META_RULE(1) {RULE=10}",
    "cards": ["PL!S-bp2-004-P", "PL!S-bp2-004-R"]
}

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print("Updated consolidated_abilities.json with 3 new cards.")
