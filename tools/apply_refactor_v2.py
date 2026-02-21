import dataclasses
import json
import os
import re
import sys
from typing import List

sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.opcodes import Opcode


def decompile(bytecode: List[int]) -> List[str]:
    lines = []
    for i in range(0, len(bytecode), 4):
        chunk = bytecode[i : i + 4]
        if len(chunk) < 4:
            break
        op_val, val, attr, slot = chunk
        try:
            op_name = Opcode(op_val).name
        except ValueError:
            op_name = f"UNK({op_val})"
        lines.append(f"{op_name}({val}, A={attr}, S={slot})")
    return lines


def enum_conv(obj):
    if dataclasses.is_dataclass(obj):
        return {k: enum_conv(v) for k, v in dataclasses.asdict(obj).items()}
    elif isinstance(obj, list):
        return [enum_conv(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: enum_conv(v) for k, v in obj.items()}
    elif hasattr(obj, "value"):  # Enum
        return obj.value
    return obj


def get_corrected_pcode(raw_text: str) -> str:
    # Heuristics for the remaining cards
    text = raw_text.replace("\\n", " ")

    # 1. Color Select Patterns
    if "のうち、1つを選ぶ" in text and "ハートを1つ得る" in text:
        colors = re.findall(r"{{heart_(\d+)}}", text)
        color_map = {"01": "Pink", "02": "Red", "03": "Yellow", "04": "Green", "05": "Blue", "06": "Purple"}
        target_colors = [color_map.get(c, "Yellow") for c in colors]
        return f"TRIGGER: ACTIVATED\n(Once per turn)\nCOST: TAP_SELF (Optional)\nEFFECT: COLOR_SELECT(1) -> PLAYER {{UNTIL=LIVE_END, OPTIONS={json.dumps(target_colors)}}}"

    # 2. Simple Active Patterns
    if "アクティブにする" in text and "メンバー" in text:
        count_match = re.search(r"(\d+)枚", text)
        count = int(count_match.group(1)) if count_match else 1
        return f"TRIGGER: ON_PLAY\nEFFECT: ACTIVATE_MEMBER({count}) -> MEMBER_SELECT"

    # 3. Simple Recover Patterns
    if "控え室から" in text and "手札に加える" in text:
        return "TRIGGER: ON_PLAY\nEFFECT: RECOVER_MEMBER(1) -> PLAYER {FROM=DISCARD, TO=HAND}"

    # 4. Standard Score Boost Cost Patterns
    if "枚、控え室に置く" in text and "スコアを＋" in text:
        score_match = re.search(r"スコアを＋(\d+)", text)
        val = int(score_match.group(1)) if score_match else 1
        return f"TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(3)\nEFFECT: BOOST_SCORE({val}) -> PLAYER {{UNTIL=LIVE_END}}"

    # Fallback to existing if no clear fix found
    return None


def main():
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    parser = AbilityParserV2()
    log_entries = []
    total_updated = 0

    for db_key in ["member_db", "live_db"]:
        for card_id, card in db[db_key].items():
            # Skip already audited cards (0-250)
            if int(card_id) <= 250:
                continue

            any_card_change = False
            report = []
            report.append(f"## Card {card_id}: {card['card_no']} - {card['name']}")

            for i, ab in enumerate(card["abilities"]):
                raw_text = ab.get("raw_text", "")
                pcode = get_corrected_pcode(raw_text)

                if pcode:
                    new_abilities = parser.parse(pcode)
                    if not new_abilities:
                        continue
                    new_ab = new_abilities[0]

                    old_bc = ab.get("bytecode", [])
                    new_bc = new_ab.compile()

                    if old_bc != new_bc:
                        any_card_change = True
                        old_dec = decompile(old_bc)
                        new_dec = decompile(new_bc)

                        report.append(f"### Ability {i} (Templated Fix):")
                        report.append("```diff")
                        max_len = max(len(old_dec), len(new_dec))
                        for j in range(max_len):
                            o = old_dec[j] if j < len(old_dec) else ""
                            n = new_dec[j] if j < len(new_dec) else ""
                            if o == n:
                                report.append(f"  {o}")
                            else:
                                if o:
                                    report.append(f"- {o}")
                                if n:
                                    report.append(f"+ {n}")
                        report.append("```")

                        ab["bytecode"] = new_bc
                        ab["effects"] = [enum_conv(e) for e in new_ab.effects]
                        ab["costs"] = [enum_conv(c) for c in new_ab.costs]
                        ab["trigger"] = int(new_ab.trigger)

            if any_card_change:
                log_entries.append("\n".join(report))
                total_updated += 1

    if log_entries:
        with open("audit_changelog.md", "a", encoding="utf-8") as f:
            f.writelines("\n\n# Heuristic Batch Refactor (Cards 251-886)\n" + "\n---\n".join(log_entries))

        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print(f"Successfully processed remaining cards. {total_updated} cards hit template fixes.")
    else:
        print("No remaining cards needed template fixes.")


if __name__ == "__main__":
    main()
