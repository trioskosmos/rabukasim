import json
import os


def audit_integrity():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    compiled_path = os.path.join(base_dir, "data", "cards_compiled.json")
    output_path = os.path.join(base_dir, "tools", "integrity_report.json")

    print(f"Loading {compiled_path}...")
    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    member_db = data.get("member_db", {})

    report = {
        "DRAW_MISMATCH": [],
        "RECOVER_MISMATCH": [],
        "TAP_MISMATCH": [],
        "SCORE_MISMATCH": [],
        "TRIGGER_MISMATCH": [],
    }

    count = 0
    for key, card in member_db.items():
        original = card.get("original_text", "")
        pseudocode = card.get("ability_text", "")  # This contains the compiled pseudocode/text
        card_no = card.get("card_no", "Unknown")

        if not original or not pseudocode:
            continue

        # 1. Draw Check
        if (
            ("引く" in original or "ドロー" in original)
            and "DRAW" not in pseudocode
            and "LOOK_AND_CHOOSE" not in pseudocode
        ):
            # LOOK_AND_CHOOSE sometimes implies drawing/adding to hand
            report["DRAW_MISMATCH"].append({"card_no": card_no, "text": original, "code": pseudocode})

        # 2. Recover/Add to Hand Check
        # "控え室" + "手札" usually means recover
        if "控え室" in original and "手札" in original and "置く" not in original:
            # "置く" might be "discard hand" which is Cost.
            # But "手札に加える" is the key.
            if "加える" in original:
                if (
                    "RECOVER" not in pseudocode
                    and "ADD_TO_HAND" not in pseudocode
                    and "PLAY_MEMBER_FROM_DISCARD" not in pseudocode
                ):
                    report["RECOVER_MISMATCH"].append({"card_no": card_no, "text": original, "code": pseudocode})

        # 3. Tap/Wait Check
        if "ウェイト" in original and "TAP" not in pseudocode:
            # Maybe self tap cost? TAP_SELF/TAP_PLAYER
            if "コスト" in original or "：" in original or ":" in original:
                # Likely a cost, usually handled as TAP_PLAYER or TAP_SELF in costs list,
                # but ability_text might show it as COST: somewhere.
                if "TAP" not in pseudocode and "ウェイト" not in pseudocode:  # Sometimes raw text leaks
                    report["TAP_MISMATCH"].append({"card_no": card_no, "text": original, "code": pseudocode})
            else:
                # Effect
                report["TAP_MISMATCH"].append({"card_no": card_no, "text": original, "code": pseudocode})

        # 4. Score Check
        if ("スコア" in original or "＋" in original) and "SCORE" not in pseudocode:
            # "＋" often used for +Score
            if "ライブの合計スコア" in original or "スコアを＋" in original:
                report["SCORE_MISMATCH"].append({"card_no": card_no, "text": original, "code": pseudocode})

        # 5. Trigger Check
        if "登場" in original and "ON_PLAY" not in pseudocode:
            report["TRIGGER_MISMATCH"].append(
                {"card_no": card_no, "missing": "ON_PLAY", "text": original, "code": pseudocode}
            )
        if "ライブ開始時" in original and "ON_LIVE_START" not in pseudocode:
            report["TRIGGER_MISMATCH"].append(
                {"card_no": card_no, "missing": "ON_LIVE_START", "text": original, "code": pseudocode}
            )

        count += 1

    print(f"Scanned {count} cards.")
    print(f"Found {len(report['DRAW_MISMATCH'])} Draw mismatches.")
    print(f"Found {len(report['RECOVER_MISMATCH'])} Recover mismatches.")
    print(f"Found {len(report['TAP_MISMATCH'])} Tap mismatches.")
    print(f"Found {len(report['SCORE_MISMATCH'])} Score mismatches.")
    print(f"Found {len(report['TRIGGER_MISMATCH'])} Trigger mismatches.")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    audit_integrity()
