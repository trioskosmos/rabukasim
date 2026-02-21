import collections
import json
import re


def normalize(text):
    text = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r"[・、。：！\!？\?\s\(\)（）/]", "", text)
    return text


def main():
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        overrides = json.load(f)

    missing_freq = collections.Counter()
    missing_samples = {}

    for card_no, data in cards.items():
        ability = data.get("ability", "")
        if not ability or card_no in overrides:
            continue

        norm = normalize(ability)
        missing_freq[norm] += 1
        missing_samples[norm] = ability

    print("Top 50 missing normalized patterns:")
    for norm, count in missing_freq.most_common(50):
        print(f"[{count}] {norm[:100]}...")
        print(f"    Original sample: {missing_samples[norm][:100]}...")
        print("-" * 40)


if __name__ == "__main__":
    main()
