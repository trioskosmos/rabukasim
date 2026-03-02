import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser(description="Find cards for testing scenarios")
    parser.add_argument("--group", help="Filter by Group (e.g. MUSE, LIELLA, HASUNOSORA)")
    parser.add_argument("--unit", help="Filter by Unit (e.g. DOLLCHESTRA, BIBI)")
    parser.add_argument("--cost", type=int, help="Filter by Cost (Exact)")
    parser.add_argument("--type", choices=["MEMBER", "LIVE"], help="Filter by Card Type")
    parser.add_argument("--query", help="Text search in card name/no")
    parser.add_argument("--pseudo", help="Text search in pseudocode")
    parser.add_argument("--limit", type=int, default=10, help="Max results")

    args = parser.parse_args()

    cards_path = os.path.join(os.path.dirname(__file__), "..", "data", "cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    # Mapping for groups to series in cards.json
    group_map = {
        "MUSE": ["ラブライブ！", "μ's"],
        "AQOURS": ["サンシャイン", "Aqours"],
        "NIJIGASAKI": ["虹ヶ咲", "Nijigasaki"],
        "LIELLA": ["スーパースター", "Liella"],
        "HASUNOSORA": ["蓮ノ空", "Hasunosora"],
    }

    # Mapping for English Names to Japanese for easier searching
    name_map = {
        "HONOKA": "穂乃果",
        "ELI": "絵里",
        "KOTORI": "ことり",
        "UMI": "海未",
        "RIN": "凛",
        "MAKI": "真姫",
        "NOZOMI": "希",
        "HANAYO": "花陽",
        "NICO": "にこ",
        "CHIKA": "千歌",
        "RIKO": "梨子",
        "KANAN": "果南",
        "DIA": "ダイヤ",
        "YOU": "曜",
        "YOSHIKO": "善子",
        "YOHANE": "善子",
        "HANAMARU": "花丸",
        "MARI": "鞠莉",
        "RUBY": "ルビィ",
        "AYUMU": "歩夢",
        "KASUMI": "かすみ",
        "SHIZUKU": "しずく",
        "KARIN": "果林",
        "AI": "愛",
        "KANATA": "彼方",
        "SETSUNA": "せつ菜",
        "EMMA": "エマ",
        "RINA": "璃奈",
        "SHIORIKO": "栞子",
        "KANON": "かのん",
        "KEKE": "可可",
        "CHISATO": "千砂都",
        "SUMIRE": "すみれ",
        "REN": "恋",
        "KAHO": "花帆",
        "SAYAKA": "さやか",
        "KOZUE": "梢",
        "TSUZURI": "綴理",
        "MEGUMI": "慈",
        "RURINO": "瑠璃乃",
    }

    for cid, c in data.items():
        ctype = c.get("type", "")
        if args.type == "MEMBER" and "メンバー" not in ctype:
            continue
        if args.type == "LIVE" and "ライブ" not in ctype:
            continue

        matches = True

        # Group Check (Series)
        if args.group:
            target_series = group_map.get(args.group.upper(), [args.group])
            series = c.get("series", "")
            if not any(ts.lower() in series.lower() for ts in target_series):
                matches = False

        # Unit Check
        if args.unit:
            unit = c.get("unit", "")
            if args.unit.lower() not in unit.lower():
                matches = False

        # Cost Check
        if args.cost is not None and c.get("cost") != args.cost:
            matches = False

        # Text/Query Check
        if args.query:
            q = args.query.upper()
            target_name = name_map.get(q, args.query.lower())
            name = c.get("name", "").lower()
            card_no = c.get("card_no", "").lower()

            if target_name.lower() not in name and args.query.lower() not in name and args.query.lower() not in card_no:
                matches = False

        # Pseudocode Check
        if args.pseudo:
            # Support multiple keywords separated by space or comma
            keywords = args.pseudo.replace(",", " ").split()
            ps = c.get("pseudocode", "").lower()
            if not all(k.lower() in ps for k in keywords):
                matches = False

        if matches:
            cost_info = f" (Cost {c.get('cost')})" if "cost" in c else ""
            results.append(
                {
                    "no": c.get("card_no"),
                    "name": c.get("name"),
                    "series": c.get("series"),
                    "unit": c.get("unit"),
                    "cost_str": cost_info,
                    "type": "MEMBER" if "メンバー" in ctype else "LIVE" if "ライブ" in ctype else "ENERGY",
                }
            )

    print(f"Found {len(results)} matches:")
    for res in results[: args.limit]:
        unit_str = f" [{res['unit']}]" if res.get("unit") else ""
        print(f"  [{res['type']}] {res['no']}: {res['name']}{res['cost_str']}{unit_str} ({res['series']})")


if __name__ == "__main__":
    main()
