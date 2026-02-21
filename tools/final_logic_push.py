import json
import os
import re


def normalize(text):
    text = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r"[・、。：！\!？\?\s\(\)（）/]", "", text)
    return text


def apply_mappings():
    raw_path = "unique_abilities_for_mapping.json"
    override_path = "data/manual_pseudocode.json"

    with open(raw_path, "r", encoding="utf-8") as f:
        unique_map = json.load(f)

    overrides = {}
    if os.path.exists(override_path):
        with open(override_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)

    # Registry of Patterns (High Fidelity)
    patterns = {
        # --- Triggers ---
        "登場": "TRIGGER: ON_PLAY",
        "ライブ開始時": "TRIGGER: ON_LIVE_START",
        "ライブ成功時": "TRIGGER: ON_LIVE_SUCCESS",
        "起動": "TRIGGER: ACTIVATED",
        "常時": "TRIGGER: CONSTANT",
        "自動": "TRIGGER: AUTO",
        # --- Unit Specific ---
        "虹ヶ咲": 'GROUP="虹ヶ咲"',
        "Liella!": 'GROUP="Liella!"',
        "蓮ノ空": 'GROUP="蓮ノ空"',
        "μ's": 'GROUP="μ\'s"',
        "Aqours": 'GROUP="Aqours"',
        "スリーズブーケ": 'GROUP="スリーズブーケ"',
        "DOLLCHESTRA": 'GROUP="DOLLCHESTRA"',
        "みらくらぱーく": 'GROUP="みらくらぱーく"',
        "BiBi": 'GROUP="BiBi"',
        "Printemps": 'GROUP="Printemps"',
        "lilywhite": 'GROUP="lily white"',
        "CatChu": 'GROUP="CatChu!"',
        "KALEIDOSCORE": 'GROUP="KALEIDOSCORE"',
        "5yncri5e": 'GROUP="5yncri5e!"',
        # --- Effects ---
        "カードを1枚引く": "EFFECT: DRAW(1) -> PLAYER",
        "カードを2枚引く": "EFFECT: DRAW(2) -> PLAYER",
        "手札を1枚控え室に置く": "EFFECT: DISCARD_HAND(1) -> PLAYER",
        "エネルギーを1枚アクティブにする": 'EFFECT: ACTIVATE_MEMBER(1) -> PLAYER {FILTER="energy"}',
        "エネルギーを2枚アクティブにする": 'EFFECT: ACTIVATE_MEMBER(2) -> PLAYER {FILTER="energy"}',
        "ブレードを得る": "EFFECT: ADD_BLADES(1) -> SELF",
        "ライブの合計スコアを＋１する": "EFFECT: BOOST_SCORE(1) -> PLAYER",
        "ライブの合計スコアを＋２する": "EFFECT: BOOST_SCORE(2) -> PLAYER",
        "デッキの上からカードを5枚見る": "EFFECT: LOOK_DECK(5) -> PLAYER",
        "必要ハートを減らす": "EFFECT: REDUCE_HEART_REQ(1) -> PLAYER",
        "メンバーをウェイトにする": "EFFECT: TAP_MEMBER(1) -> TARGET",
    }

    # High Fidelity Manual Registry
    manual_registry = {
        "ライブ開始時E支払ってもよいライブ終了時までブレードブレードを得る": 'TRIGGER: ON_LIVE_START\nCOST: ENERGY(1) (Optional)\nEFFECT: ADD_BLADES(2) -> SELF {UNTIL="live_end"}',
        "エールで出たALLブレードは任意の色のハートとして扱う": 'TRIGGER: NONE\nEFFECT: META_RULE(1) -> PLAYER {REMARK="ALL_BLADE_IS_ANY_COLOR"}',
        "このターン自分のデッキがリフレッシュしていた場合このカードのスコアを＋２する": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: DECK_REFRESHED\nEFFECT: BOOST_SCORE(2) -> PLAYER",
        "登場エネルギーを支払ってもよいステージの左サイドエリアに登場しているならカードを2枚引く": 'TRIGGER: ON_PLAY\nCOST: ENERGY(2) (Optional)\nCONDITION: IS_ZONE {ZONE="left_side"}\nEFFECT: DRAW(2) -> PLAYER',
        "起動このメンバーをステージから控え室に置く自分の控え室からメンバーカードを1枚手札に加える": "TRIGGER: ACTIVATED\nCOST: SACRIFICE_SELF\nEFFECT: RECOVER_MEMBER(1) -> CARD_DISCARD",
        "ライブカードが公開されるまで自分のデッキの一番上のカードを公開し続ける": 'TRIGGER: ON_PLAY\nEFFECT: REVEAL_CARDS(99) -> PLAYER {ZONE="deck", STOP_CONDITION="LIVE", TO="hand", RESIDUE="discard"}',
        "ステージと控え室に名前の異なるLiella!のメンバーが5人以上いる場合": 'TRIGGER: ON_LIVE_START\nCONDITION: COUNT_GROUP {MIN=5, GROUP="Liella!", ZONE=["stage", "discard"], UNIQUE_NAMES=TRUE}\nEFFECT: REDUCE_HEART_REQ(99) -> PLAYER',
        "徒町小鈴が登場しておりかつ徒町小鈴よりコストの大きい村野さやかが登場している場合": 'TRIGGER: ON_LIVE_START\nCONDITION: HAS_MEMBER {NAME="徒町小鈴"}, HAS_MEMBER {NAME="村野さやか", COST_GT="徒町小鈴"}\nEFFECT: REDUCE_HEART_REQ(3) -> PLAYER',
        "センターエリアのメンバーを左サイドエリアに左サイドエリアのメンバーを右サイドエリアに右サイドエリアのメンバーをセンターエリアにそれぞれ移動させる": 'TRIGGER: ON_PLAY\nCONDITION: COUNT_GROUP {MIN=5, GROUP="5yncri5e!", EXCLUDE_OPPONENT=TRUE}\nEFFECT: FORMATION_CHANGE(1) -> ALL_PLAYERS {MODE="rotate_cw"}',
    }

    # Final logic application
    count = 0
    for jp_text, card_list in unique_map.items():
        n_jp = normalize(jp_text)

        # Check manual registry first
        pcode = None
        for m_jp, m_pcode in manual_registry.items():
            if m_jp in n_jp or n_jp in m_jp:
                pcode = m_pcode
                break

        if not pcode:
            # Fallback Construction (Triggers + Keywords)
            trigger = "TRIGGER: AUTO"
            for k, v in patterns.items():
                if k in n_jp:
                    if v.startswith("TRIGGER:"):
                        trigger = v

            # Very basic fallback that is better than nothing
            pcode = f"{trigger}\n// TODO: High-Fidelity Logic for [{n_jp[:30]}]"
            # But let's try to be better.
            # If it's a "Search" effect:
            if "見る" in n_jp and "手札に加える" in n_jp:
                pcode = f"{trigger}\nEFFECT: LOOK_AND_CHOOSE(1) -> PLAYER"
            elif "スコアを＋" in n_jp:
                pcode = f"{trigger}\nEFFECT: BOOST_SCORE(1) -> PLAYER"

        for card_no in card_list:
            if card_no not in overrides:
                overrides[card_no] = {"pseudocode": pcode}
                count += 1

    with open(override_path, "w", encoding="utf-8") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)

    print(f"Added {count} logical overrides. Total: {len(overrides)}")


if __name__ == "__main__":
    apply_mappings()
