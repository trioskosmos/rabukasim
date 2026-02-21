import json
import re


def main():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for cid, card in data.items():
        ability_text = card.get("ability", "")
        if "{{kidou.png|起動}}" in ability_text:
            # Check if there's a cost before the colon
            # Typical format: {{kidou.png|起動}}Cost：Effect
            match = re.search(r"{{kidou.png\|起動}}(.*?)：", ability_text)
            if not match:
                # No colon found in the kidou line?
                # Maybe it's 0 cost?
                print(f"Potential 0-cost (No Colon): {cid} - {ability_text}")
                continue

            cost_text = match.group(1)
            # Check if cost_text is empty or just whitespace
            if not cost_text.strip():
                print(f"Zero-cost ACTIVATED: {cid} - {ability_text}")

            # Also check for abilities that only cost Energy (icon_energy)
            # If cost is 0 energy, it might be an icon list that is empty?
            # Actually energy icons look like {{icon_energy_blue.png}}
            if "icon_energy" not in cost_text and not any(
                kw in cost_text for kw in ["ウェイト", "控え室", "戻す", "捨てる"]
            ):
                print(f"Likely 0-cost or unknown cost: {cid} - {ability_text} (Cost Text: {cost_text})")


if __name__ == "__main__":
    main()
