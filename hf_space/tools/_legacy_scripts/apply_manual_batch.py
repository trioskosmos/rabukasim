import json
import os
import re


def normalize(text):
    # Remove {{icon.png|Text}} and similar
    text = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
    # Remove plain {{icon.png}}
    text = re.sub(r"\{\{.*?\}\}", "", text)
    # Strip whitespace, symbols, and punctuation
    text = re.sub(r"[・、。：！\!？\?\s\(\)（）/]", "", text)
    return text


def apply_mappings(mappings):
    raw_path = "unique_abilities_for_mapping.json"
    override_path = "data/manual_pseudocode.json"

    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found.")
        return

    with open(raw_path, r"r", encoding="utf-8") as f:
        unique_map = json.load(f)

    overrides = {}
    if os.path.exists(override_path):
        with open(override_path, r"r", encoding="utf-8") as f:
            overrides = json.load(f)

    count = 0
    norm_unique_map = {normalize(k): k for k in unique_map.keys()}

    for jp_text, pcode in mappings.items():
        n_jp = normalize(jp_text)
        found = False
        # 1. Exact Normal Match
        if n_jp in norm_unique_map:
            original_key = norm_unique_map[n_jp]
            for card_no in unique_map[original_key]:
                overrides[card_no] = {"pseudocode": pcode}
                count += 1
            found = True
        else:
            # 2. Substring Normal Match
            for n_k, original_key in norm_unique_map.items():
                if n_jp in n_k or n_k in n_jp:
                    for card_no in unique_map[original_key]:
                        if card_no not in overrides:
                            overrides[card_no] = {"pseudocode": pcode}
                            count += 1
                    found = True

        if not found:
            # Debug: Print normalized version of first 3 unique keys to see what we are dealing with
            print(f"DEBUG: No match found for: [{n_jp}]")
            print(f"DEBUG: First 3 available keys: {list(norm_unique_map.keys())[:3]}")

    with open(override_path, "w", encoding="utf-8") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)

    print(f"Updated {count} cards in {override_path}")


if __name__ == "__main__":
    m = {
        # --- HIGH FREQUENCY COMMON ---
        "ライブ開始時E支払ってもよいライブ終了時までブレードブレードを得る": 'TRIGGER: ON_LIVE_START\nCOST: ENERGY(1) (Optional)\nEFFECT: ADD_BLADES(2) -> SELF {UNTIL="live_end"}',
        "登場E支払ってもよい自分のデッキの上からカードを3枚見るその中から1枚を手札に加え残りを控え室に置く": 'TRIGGER: ON_PLAY\nCOST: ENERGY(1) (Optional)\nEFFECT: LOOK_AND_CHOOSE(1) -> PLAYER {COUNT=3, ZONE="deck", TO="hand", RESIDUE="discard"}',
        "エールで出たALLブレードは任意の色のハートとして扱う": 'TRIGGER: NONE\nEFFECT: META_RULE(1) -> PLAYER {REMARK="ALL_BLADE_IS_ANY_COLOR"}',
        "登場手札を1枚控え室に置いてもよい自分のデッキの上からカードを5枚見るその中からメンバーカードを1枚公開して手札に加えてもよい残りを控え室に置く": 'TRIGGER: ON_PLAY\nCOST: DISCARD_HAND(1) (Optional)\nEFFECT: LOOK_AND_CHOOSE(1) -> PLAYER {COUNT=5, TYPE="MEMBER", ZONE="deck", TO="hand", RESIDUE="discard"}',
        "登場このメンバーよりコストが低い『DOLLCHESTRA』のメンバーからバトンタッチして登場した場合": 'TRIGGER: ON_PLAY\nCONDITION: HAS_KEYWORD {KEYWORD="BATON_TOUCH", FROM_GROUP="DOLLCHESTRA", COST_LT=TRUE}\nEFFECT: ADD_BLADES(2) -> SELF {UNTIL="live_end"}',
        "自分のエネルギーデッキからエネルギーカードを1枚ウェイト状態で置く": "TRIGGER: ON_PLAY\nEFFECT: ENERGY_CHARGE(1) -> PLAYER {TAP_SET=TRUE}",
        "ライブ開始時自分の成功ライブカード置き場にあるカード1枚につきこのカードを成功させるための必要ハートは少なくなる": "TRIGGER: ON_LIVE_START\nEFFECT: REDUCE_HEART_REQ(2) -> PLAYER {MULTIPLIER=SUCCESS_LIVE}",
        "ターン1回エールにより公開された自分のカードの中にライブカードが1枚以上あるとき": 'TRIGGER: ON_REVEAL\n(Once per turn)\nCONDITION: HAS_LIVE_CARD {ZONE="revealed"}\nEFFECT: ADD_HEARTS(1) -> PLAYER {COLOR="GREEN", UNTIL="live_end"}',
        "このメンバーが登場かエリアを移動するたびライブ終了時までブレードブレードを得る": 'TRIGGER: ON_PLAY, ON_MOVED\nEFFECT: ADD_BLADES(2) -> SELF {UNTIL="live_end"}',
        "自分のステージにほかの『5yncri5e!』のメンバーがいる場合カードを1枚引く": 'TRIGGER: ON_PLAY\nCONDITION: COUNT_GROUP {MIN=1, GROUP="5yncri5e!", EXCLUDE_SELF=TRUE}\nEFFECT: DRAW(1) -> PLAYER',
    }

    apply_mappings(m)
