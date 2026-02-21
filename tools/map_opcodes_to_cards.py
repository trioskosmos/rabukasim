import json
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from engine.models.ability import ConditionType, TriggerType
from engine.models.opcodes import Opcode


def find_cards_for_components():
    base_path = os.getcwd()
    cards_path = os.path.join(base_path, "data", "cards_compiled.json")

    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    opcode_map = {op.value: {"name": op.name, "cards": []} for op in Opcode}
    trigger_map = {t.value: {"name": t.name, "cards": []} for t in TriggerType}
    condition_map = {c.value: {"name": c.name, "cards": []} for c in ConditionType}

    def process_card(card):
        card_id = card.get("card_no", "unknown")
        for ability in card.get("abilities", []):
            # 1. Triggers
            t_val = ability.get("trigger")
            if t_val in trigger_map and card_id not in trigger_map[t_val]["cards"]:
                if len(trigger_map[t_val]["cards"]) < 2:
                    trigger_map[t_val]["cards"].append(card_id)

            # 2. Conditions
            for cond in ability.get("conditions", []):
                c_val = cond.get("type")
                if c_val in condition_map and card_id not in condition_map[c_val]["cards"]:
                    if len(condition_map[c_val]["cards"]) < 2:
                        condition_map[c_val]["cards"].append(card_id)

            # 3. Opcodes (from bytecode)
            bytecode = ability.get("bytecode", [])
            for i in range(0, len(bytecode), 4):
                op_val = bytecode[i]
                base_op = op_val % 1000
                if base_op in opcode_map and card_id not in opcode_map[base_op]["cards"]:
                    if len(opcode_map[base_op]["cards"]) < 2:
                        opcode_map[base_op]["cards"].append(card_id)

    # Process all databases
    for db_name in ["member_db", "live_db", "energy_db"]:
        for card in data.get(db_name, {}).values():
            process_card(card)

    # Generate Markdown Output
    output = []
    output.append("## Opcodes Mapping")
    output.append("| Val | Name | Cards |")
    output.append("|---|---|---|")
    for val, d in sorted(opcode_map.items()):
        if d["cards"]:
            output.append(f"| {val} | {d['name']} | {', '.join(d['cards'])} |")
        elif val > 0:
            output.append(f"| {val} | {d['name']} | **MISSING** |")

    output.append("\n## Triggers Mapping")
    output.append("| Val | Name | Cards |")
    output.append("|---|---|---|")
    for val, d in sorted(trigger_map.items()):
        if d["cards"]:
            output.append(f"| {val} | {d['name']} | {', '.join(d['cards'])} |")
        else:
            output.append(f"| {val} | {d['name']} | **MISSING** |")

    output.append("\n## Conditions Mapping")
    output.append("| Val | Name | Cards |")
    output.append("|---|---|---|")
    for val, d in sorted(condition_map.items()):
        if d["cards"]:
            output.append(f"| {val} | {d['name']} | {', '.join(d['cards'])} |")
        elif val > 0:
            output.append(f"| {val} | {d['name']} | **MISSING** |")

    return "\n".join(output)


if __name__ == "__main__":
    result = find_cards_for_components()
    with open("opcode_map_utf8.md", "w", encoding="utf-8") as f:
        f.write(result)
    print("Regenerated opcode_map_utf8.md")
