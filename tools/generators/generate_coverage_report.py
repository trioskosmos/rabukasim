import json
import re


def generate_report(rule_map_path, target_file_path):
    with open(rule_map_path, "r", encoding="utf-8") as f:
        rule_map = json.load(f)

    with open(target_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    report = "# Love Live! Card Game Rule Coverage Report (v1.04)\n\n"
    report += (
        "This report lists all identified rules from `rules.txt` and their current presence in `game_state.py`.\n\n"
    )
    report += "| Rule # | Description | Status | Implementation Site |\n"
    report += "| :--- | :--- | :--- | :--- |\n"

    for num in sorted(rule_map.keys(), key=lambda x: [int(y) for y in x.split(".")]):
        # Search for "Rule num" in code
        status = "❌"
        site = "-"

        # Try to find the line number
        match = re.search(f"Rule {num}\\b", content)
        if match:
            status = "✅"
            # Find line number
            line_num = content.count("\n", 0, match.start()) + 1
            site = f"[game_state.py:L{line_num}](file:///c:/Users/trios/.gemini/antigravity/scratch/loveca-copy/game/game_state.py#L{line_num})"

        report += f"| {num} | {rule_map[num]} | {status} | {site} |\n"

    return report


report_md = generate_report("rule_map.json", "game/game_state.py")
with open("rule_coverage_full.md", "w", encoding="utf-8") as f:
    f.write(report_md)

print("Report generated: rule_coverage_full.md")
