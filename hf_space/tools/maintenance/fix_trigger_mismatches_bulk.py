import json
import os


def fix_trigger_mismatches():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manual_path = os.path.join(base_dir, "data", "manual_pseudocode.json")
    report_path = os.path.join(base_dir, "tools", "integrity_report.json")

    print(f"Loading {report_path}...")
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(f"Loading {manual_path}...")
    with open(manual_path, "r", encoding="utf-8") as f:
        manual_data = json.load(f)

    trigger_mismatches = report.get("TRIGGER_MISMATCH", [])
    fixed_count = 0

    for entry in trigger_mismatches:
        card_id = entry["card_no"]
        text = entry["text"]
        code = entry["code"]
        missing = entry["missing"]

        if missing == "ON_LIVE_START":
            new_code = code
            modified = False

            # Case 1: Split abilities (e.g. On Play ... \n\n Live Start ...)
            if "\n\n" in code:
                parts = code.split("\n\n")
                if len(parts) >= 2:
                    # Heuristic: If text has "登場" (On Play) then first part is ON_PLAY
                    # If text has "ライブ開始" (Live Start) then second part is ON_LIVE_START

                    # Check part 2 for existing trigger
                    if "TRIGGER:" not in parts[1]:
                        parts[1] = "TRIGGER: ON_LIVE_START\n" + parts[1]
                        modified = True

                    # Check part 1
                    if "TRIGGER:" not in parts[0] and "登場" in text:
                        parts[0] = "TRIGGER: ON_PLAY\n" + parts[0]
                        modified = True

                    if modified:
                        new_code = "\n\n".join(parts)

            # Case 2: ID starts with LL-bp1-001-R+ type cards often have this structure manually
            # Case 3: Single block but starts with Live Start text
            elif text.startswith("{{live_start") or text.startswith("ライブ開始時"):
                if "TRIGGER:" not in code:
                    new_code = "TRIGGER: ON_LIVE_START\n" + code
                    modified = True

            if modified:
                if card_id not in manual_data:
                    manual_data[card_id] = {"pseudocode": new_code}
                else:
                    manual_data[card_id]["pseudocode"] = new_code

                # print(f"Fixed ON_LIVE_START for {card_id}")
                fixed_count += 1

        elif missing == "ON_PLAY":
            # If ONLY missing ON_PLAY and starts with "登場"
            if text.startswith("{{toujyou") or text.startswith("登場"):
                if "TRIGGER:" not in code:
                    # This is implicit default, so technically not "broken" but good to be explicit
                    # if we want 100% integrity.
                    # But for now let's skip unless strictly necessary to avoid noise.
                    pass

    print(f"Applied trigger fixes to {fixed_count} cards.")

    print(f"Saving {manual_path}...")
    with open(manual_path, "w", encoding="utf-8") as f:
        json.dump(manual_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    fix_trigger_mismatches()
