import json


def find_card():
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    target = "PL!N-pb1-004-P＋"
    # test_strict_PL_N_pb1_004_P_ expects 3 abilities
    # Raw text:
    # {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：カードを1枚引く。
    # {{live_success.png|ライブ成功時}}これもテスト。 (Wait, I need the real text)

    # We will fetch the real text from data/cards.json
    # The key might be formatted differently, let's search values
    for k, v in data.items():
        if target in k or target in v.get("card_no", ""):
            print(f"Found {k}:")
            print(v.get("ability", "NO ABILITY"))
            return


if __name__ == "__main__":
    find_card()
