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


def main():
    if len(sys.argv) < 3:
        print("Usage: python audit_reporter.py <card_id> <new_pseudocode_file> [--apply]")
        return

    card_id = sys.argv[1]
    pcode_file = sys.argv[2]
    apply_changes = "--apply" in sys.argv

    with open(pcode_file, "r", encoding="utf-8") as f:
        new_pcode = f.read().strip()

    # Load Database
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    card_key = None
    if card_id in db["member_db"]:
        card_key = "member_db"
    elif card_id in db["live_db"]:
        card_key = "live_db"
    else:
        print(f"Error: Card {card_id} not found.")
        return

    card = db[card_key][card_id]

    # We assuming only one ability for simplicity in the CLI, or we take all in the file
    parser = AbilityParserV2()
    new_abilities = parser.parse(new_pcode)

    report = []
    report.append(f"## Card {card_id}: {card['card_no']} - {card['name']}")
    report.append(f"**Japanese Text:** `{card.get('ability_text', 'N/A').replace('\\n', ' ')}`")

    any_change = False

    for i, new_ab in enumerate(new_abilities):
        if i >= len(card["abilities"]):
            report.append(f"### Ability {i}: [NEWLY ADDED]")
            old_bc = []
        else:
            report.append(f"### Ability {i}")
            old_bc = card["abilities"][i].get("bytecode", [])

        new_bc = new_ab.compile()

        old_dec = decompile(old_bc)
        new_dec = decompile(new_bc)

        if old_bc != new_bc:
            any_change = True
            report.append("#### Bytecode Shift:")
            report.append("```diff")
            # Simple line-based diff
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

            if apply_changes:
                import dataclasses

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

                card["abilities"][i]["bytecode"] = new_bc
                card["abilities"][i]["effects"] = [enum_conv(e) for e in new_ab.effects]
                card["abilities"][i]["costs"] = [enum_conv(c) for c in new_ab.costs]
                card["abilities"][i]["conditions"] = [enum_conv(c) for c in new_ab.conditions]
                card["abilities"][i]["trigger"] = int(new_ab.trigger)
                card["abilities"][i]["is_once_per_turn"] = new_ab.is_once_per_turn
        else:
            report.append("✅ Bytecode Identical (No Shift)")

    full_report = "\n".join(report)
    print(full_report)

    # Append to log
    with open("audit_changelog.md", "a", encoding="utf-8") as f:
        f.write("\n" + full_report + "\n---\n")

    if apply_changes and any_change:
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print("\n[SUCCESS] Changes applied to cards_compiled.json")


if __name__ == "__main__":
    main()
