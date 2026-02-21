import re


def analyze_rule_depth(rules_file, target_file, output_file):
    # 1. Load Rules
    with open(rules_file, "r", encoding="utf-8") as f:
        rules_content = f.read()

    # Extract rule numbers and their text description
    # Pattern: start of line, digits.digits..., space, text
    # e.g. "1.1. ゲーム人数"
    rule_map = {}
    lines = rules_content.split("\n")
    current_rule = None

    for line in lines:
        match = re.match(r"^(\d+(?:\.\d+)+)\.?\s+(.*)", line.strip())
        if match:
            r_num, r_desc = match.groups()
            # Normalize rule number (remove trailing dot if any)
            r_num = r_num.rstrip(".")
            rule_map[r_num] = r_desc
        elif line.strip() and current_rule:
            # Append continuation of description if needed (simplified for now)
            pass

    # 2. Analyze Target File
    with open(target_file, "r", encoding="utf-8") as f:
        target_lines = f.readlines()

    # Find where the Appendix starts
    appendix_start = len(target_lines)
    for i, line in enumerate(target_lines):
        if "### RULEBOOK v1.04 INDEX ###" in line or "COMPREHENSIVE RULEBOOK INDEX" in line:
            appendix_start = i
            break

    print(f"Appendix starts at line {appendix_start}")

    results = []

    # Keywords for "Reasoning"
    definition_keywords = ["とは", "意味します", "指します", "情報です", "名称です", "イラスト"]
    visual_keywords = ["アイコン", "表記", "ロゴ", "枠", "色"]
    physical_keywords = ["スリーブ", "向き", "裏面"]

    for r_num in sorted(rule_map.keys(), key=lambda x: [int(y) for y in x.split(".")]):
        desc = rule_map[r_num]

        status = "❌ Missing"
        reason = "Not found in code or index"
        loc = "-"

        # Check in MAIN BODY
        in_main = False
        main_line = -1
        for i in range(appendix_start):
            if (
                f"Rule {r_num}" in target_lines[i]
                or f"({r_num})" in target_lines[i]
                or f"Rule {r_num}:" in target_lines[i]
            ):
                in_main = True
                main_line = i + 1
                break

        # Check in APPENDIX
        in_appendix = False
        for i in range(appendix_start, len(target_lines)):
            if f"Rule {r_num}" in target_lines[i]:
                in_appendix = True
                break

        if in_main:
            status = "✅ Logic"
            reason = "Implemented in Game Engine"
            loc = f"Line {main_line}"
        elif in_appendix:
            status = "⚠️ Index Only"
            loc = "Appendix"

            # Guess Reason
            if any(k in desc for k in definition_keywords):
                reason = "Definition / Descriptive"
            elif any(k in desc for k in visual_keywords):
                reason = "Visual / Asset Spec"
            elif any(k in desc for k in physical_keywords):
                reason = "Physical Component Spec"
            elif r_num.startswith("1."):  # General Overview
                reason = "General Concept / Game Structure"
            elif r_num.startswith("2."):  # Card Info
                reason = "Data Structure / Asset Definition"
            elif r_num.startswith("4."):  # Zones
                reason = "Zone Definition (Implicit in State)"
            elif r_num.startswith("11."):  # Keywords
                reason = "Keyword Definition"
            else:
                reason = "See Index for Details"

        results.append(
            {
                "rule": r_num,
                "desc": desc[:50] + "..." if len(desc) > 50 else desc,
                "status": status,
                "reason": reason,
                "loc": loc,
            }
        )

    # 3. Generate Markdown Report
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Detailed Rule Implementation Report (v1.04)\n\n")
        f.write("Analysis of `game_state.py` distinguishing active logic from indexed references.\n\n")
        f.write("| Rule | Status | Type/Reason | Line # | Description snippet |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")

        for r in results:
            # Make line number a link if possible
            loc_str = r["loc"]
            if "Line" in loc_str:
                line_num = loc_str.split(" ")[1]
                loc_str = f"[{loc_str}](file:///c:/Users/trios/.gemini/antigravity/scratch/loveca-copy/game/game_state.py#L{line_num})"

            f.write(f"| {r['rule']} | {r['status']} | {r['reason']} | {loc_str} | {r['desc']} |\n")

    print(f"Analysis complete. Report written to {output_file}")


if __name__ == "__main__":
    analyze_rule_depth("rules.txt", "game/game_state.py", "rule_coverage_depth.md")
