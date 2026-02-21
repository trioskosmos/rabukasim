import dataclasses
import json
import os
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python bulk_audit_updater.py <updates_json_file>")
        return

    updates_file = sys.argv[1]
    with open(updates_file, "r", encoding="utf-8") as f:
        updates = json.load(f)

    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    parser = AbilityParserV2()
    log_entries = []

    for card_id, pcode in updates.items():
        card_id_str = str(card_id)
        card_key = None
        if card_id_str in db["member_db"]:
            card_key = "member_db"
        elif card_id_str in db["live_db"]:
            card_key = "live_db"

        if not card_key:
            print(f"Skipping {card_id}: Not found")
            continue

        card = db[card_key][card_id_str]
        new_abilities = parser.parse(pcode)

        report = []
        report.append(f"## Card {card_id}: {card['card_no']} - {card['name']}")

        any_change = False

        # We only update if parsed abilities count matches or if we explicitly want to overwrite
        # For simplicity in bulk, we'll try to match by index
        for i, new_ab in enumerate(new_abilities):
            if i >= len(card["abilities"]):
                card["abilities"].append({})  # Dynamic adding if needed

            old_bc = card["abilities"][i].get("bytecode", [])
            new_bc = new_ab.compile()

            if old_bc != new_bc:
                any_change = True
                old_dec = decompile(old_bc)
                new_dec = decompile(new_bc)

                report.append(f"### Ability {i} Shift:")
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

                # Update DB
                card["abilities"][i]["bytecode"] = new_bc
                card["abilities"][i]["effects"] = [enum_conv(e) for e in new_ab.effects]
                card["abilities"][i]["costs"] = [enum_conv(c) for c in new_ab.costs]
                card["abilities"][i]["conditions"] = [enum_conv(c) for c in new_ab.conditions]
                card["abilities"][i]["trigger"] = int(new_ab.trigger)
                card["abilities"][i]["is_once_per_turn"] = new_ab.is_once_per_turn

        if any_change:
            log_entries.append("\n".join(report))

    if log_entries:
        with open("audit_changelog.md", "a", encoding="utf-8") as f:
            f.writelines("\n\n" + "\n---\n".join(log_entries))

        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print(f"Successfully processed {len(updates)} cards. {len(log_entries)} cards changed.")
    else:
        print(f"Processed {len(updates)} cards. No changes needed.")


if __name__ == "__main__":
    main()
