import json
import os
import re
from collections import Counter


def normalize(text):
    if not text:
        return ""
    # Remove icon tags like {{toujyou.png|登場}} -> 登場
    norm = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
    # Remove remaining tags {{icon_energy.png}}
    norm = re.sub(r"\{\{.*?\}\}", "", norm)
    # Remove punctuation and whitespace
    norm = re.sub(r"[・、。：！\!？\?\s\(\)（）/]", "", norm)
    return norm


def analyze_abilities():
    cards_path = "data/cards.json"
    pseudo_path = "data/manual_pseudocode.json"
    compiled_path = "data/cards_compiled.json"

    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found.")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    pseudo_db = {}
    if os.path.exists(pseudo_path):
        with open(pseudo_path, "r", encoding="utf-8") as f:
            pseudo_db = json.load(f)

    compiled_db = {}
    if os.path.exists(compiled_path):
        with open(compiled_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Map card_no to opcodes/bytecode
            for idx, member in data.get("member_db", {}).items():
                card_no = member.get("card_no")
                if card_no:
                    # Collect bytecode for all abilities
                    opcodes = []
                    for ability in member.get("abilities", []):
                        opcodes.append(",".join(map(str, ability.get("bytecode", []))))
                    compiled_db[card_no] = " | ".join(opcodes)
            for idx, live in data.get("live_db", {}).items():
                card_no = live.get("card_no")
                if card_no:
                    opcodes = []
                    for ability in live.get("abilities", []):
                        opcodes.append(",".join(map(str, ability.get("bytecode", []))))
                    compiled_db[card_no] = " | ".join(opcodes)

    all_abilities = []
    cid_map = {}

    for cid, card in cards.items():
        text = card.get("ability")
        if text and text != "なし":
            norm = normalize(text)
            all_abilities.append(norm)
            if norm not in cid_map:
                cid_map[norm] = []
            cid_map[norm].append((cid, text))

    counts = Counter(all_abilities)

    report_path = "reports/all_unique_abilities.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Unique Abilities Frequency Report\n\n")
        f.write(f"Total unique normalized abilities: {len(counts)}\n\n")
        f.write("| Count | Representative CID | Normalized Text | Pseudocode | Opcodes | Original Example |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")

        for norm, count in counts.most_common():
            cid, original = cid_map[norm][0]

            pseudo = pseudo_db.get(cid, {}).get("pseudocode", "N/A")
            opcodes = compiled_db.get(cid, "N/A")

            # Formatting for markdown table
            safe_pseudo = pseudo.replace("\n", "<br>").replace("|", "\\|")
            safe_original = original.replace("\n", "<br>").replace("|", "\\|")

            f.write(f"| {count} | {cid} | {norm} | {safe_pseudo} | `{opcodes}` | {safe_original} |\n")

    print(f"Report generated: {report_path}")


if __name__ == "__main__":
    analyze_abilities()
