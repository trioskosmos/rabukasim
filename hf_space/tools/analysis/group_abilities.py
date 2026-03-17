import json
import os
from collections import defaultdict


def normalize_ability(text):
    if not text:
        return ""
    # Basic normalization: strip whitespace
    return text.strip()


def analyze_abilities():
    cards_path = r"data\cards.json"
    pseudocode_path = r"data\manual_pseudocode.json"

    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    with open(pseudocode_path, "r", encoding="utf-8") as f:
        manual_pseudocode = json.load(f)

    # Group cards by normalized ability text
    ability_groups = defaultdict(list)
    for card_id, card_data in cards.items():
        ability = card_data.get("ability", "")
        if ability:
            norm_ability = normalize_ability(ability)
            ability_groups[norm_ability].append(card_id)

    report_lines = ["# Ability Pseudocode Grouping Report\n"]

    conflict_count = 0
    total_groups = len(ability_groups)

    for ability, card_ids in ability_groups.items():
        # Collect pseudocodes for this group
        group_pseudocodes = {}
        for cid in card_ids:
            if cid in manual_pseudocode:
                pcode = manual_pseudocode[cid].get("pseudocode", "").strip()
                if pcode:
                    group_pseudocodes[cid] = pcode

        unique_pcodes = set(group_pseudocodes.values())

        report_lines.append(f"## Ability: {ability[:100]}...")
        report_lines.append(f"**Cards:** {', '.join(card_ids)}")

        if len(unique_pcodes) > 1:
            conflict_count += 1
            report_lines.append("\n> [!WARNING]")
            report_lines.append("> **Conflict Detected!** Multiple different pseudocodes found in this group.\n")

            for cid, pcode in group_pseudocodes.items():
                report_lines.append(f"- **{cid}**: `{pcode}`")

            # Pick best one: heuristic - longest non-empty
            best_pcode = max(unique_pcodes, key=len)
            report_lines.append(f"\n**Selected Best (Longest):**\n```\n{best_pcode}\n```")
        elif len(unique_pcodes) == 1:
            pcode = list(unique_pcodes)[0]
            report_lines.append(f"\n**Consolidated Pseudocode:**\n```\n{pcode}\n```")
        else:
            report_lines.append("\n*No manual pseudocode found for this ability.*")

        report_lines.append("\n---\n")

    summary = [
        "## Summary",
        f"- Total Unique Abilities: {total_groups}",
        f"- Groups with Conflicts: {conflict_count}",
        f"- Groups without Conflicts: {total_groups - conflict_count}\n",
    ]

    final_content = "\n".join(summary + report_lines)

    os.makedirs("reports", exist_ok=True)
    with open(r"reports\ability_pseudocode_groups.md", "w", encoding="utf-8") as f:
        f.write(final_content)

    print("Report generated: reports\\ability_pseudocode_groups.md")
    print(f"Total groups: {total_groups}, Conflicts: {conflict_count}")


if __name__ == "__main__":
    analyze_abilities()
