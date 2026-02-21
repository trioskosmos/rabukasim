import json
import os


def fix_tap_mismatches():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manual_path = os.path.join(base_dir, "data", "manual_pseudocode.json")
    report_path = os.path.join(base_dir, "tools", "integrity_report.json")

    print(f"Loading {report_path}...")
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(f"Loading {manual_path}...")
    with open(manual_path, "r", encoding="utf-8") as f:
        manual_data = json.load(f)

    tap_mismatches = report.get("TAP_MISMATCH", [])
    fixed_count = 0

    for entry in tap_mismatches:
        card_id = entry["card_no"]  # Report uses 'card_no' which is usually the ID in our system
        text = entry["text"]
        code = entry["code"]

        # 1. Check for "Wait this member" (Self Tap)
        if "このメンバーをウェイト" in text:
            # Check if likely already handled (e.g. MODE="WAIT" is for entering, not cost)
            # But if it's "Wait this member: ...", it's a Cost.

            if "TAP_SELF" not in code:
                # Need to add TAP_SELF
                new_code = code
                if "COST:" in new_code:
                    # Append to existing cost
                    # Regex or simple replace could be tricky with multiple lines.
                    # Best to replace "COST: " with "COST: TAP_SELF; "
                    new_code = new_code.replace("COST: ", "COST: TAP_SELF; ")
                else:
                    # Prepend Cost
                    # If TRIGGER line exists, put after trigger?
                    lines = new_code.split("\n")
                    inserted = False
                    final_lines = []
                    for line in lines:
                        if line.startswith("TRIGGER:") and not inserted:
                            final_lines.append(line)
                            final_lines.append("COST: TAP_SELF")
                            inserted = True
                        elif line.startswith("EFFECT:") and not inserted:
                            # No trigger, implicit ON_PLAY? Or implicit trigger.
                            # Put Cost before Effect
                            final_lines.append("COST: TAP_SELF")
                            final_lines.append(line)
                            inserted = True
                        else:
                            final_lines.append(line)

                    if not inserted:
                        # Fallback
                        final_lines.insert(0, "COST: TAP_SELF")

                    new_code = "\n".join(final_lines)

                # Verify we didn't double up or make mess
                if "TAP_SELF" in new_code:
                    if card_id not in manual_data:
                        manual_data[card_id] = {"pseudocode": new_code}
                    else:
                        manual_data[card_id]["pseudocode"] = new_code

                    print(f"Fixed TAP_SELF for {card_id}")
                    fixed_count += 1

    print(f"Applied fixes to {fixed_count} cards.")

    print(f"Saving {manual_path}...")
    with open(manual_path, "w", encoding="utf-8") as f:
        json.dump(manual_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    fix_tap_mismatches()
