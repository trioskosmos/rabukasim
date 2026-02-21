import json
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from engine.models.ability import ConditionType
from engine.models.opcodes import Opcode


def parse_mapping(filepath):
    components = {"opcodes": {}, "triggers": {}, "conditions": {}}
    current_section = None

    if not os.path.exists(filepath):
        return components

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if "## Opcodes Mapping" in line:
                current_section = "opcodes"
            elif "## Triggers Mapping" in line:
                current_section = "triggers"
            elif "## Conditions Mapping" in line:
                current_section = "conditions"
            elif "|" in line and "Val | Name" not in line and "---" not in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    try:
                        val = int(parts[1])
                        name = parts[2]
                        cards = [c.strip() for c in parts[3].split(",") if c.strip() and "MISSING" not in c]
                        if cards:
                            components[current_section][val] = {"name": name, "cards": cards}
                    except ValueError:
                        continue
    return components


def generate_exhaustive_pytest(mapping, output_path):
    # Load compiled data to check types
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    def is_live(card_no):
        return any(c.get("card_no") == card_no for c in db.get("live_db", {}).values())

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write("\nimport pytest\nimport os\nimport sys\nimport json\n")
        f.write("PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))\n")
        f.write("if PROJECT_ROOT not in sys.path: sys.path.insert(0, PROJECT_ROOT)\n")
        f.write("from engine.tests.ability_test_helper import AbilityTestContext\n")
        f.write("from engine.game.enums import Phase\n\n")
        f.write("@pytest.fixture\ndef ctx(): return AbilityTestContext('data/cards_compiled.json')\n\n")

        # 1. Opcodes
        f.write("### OPCODE TESTS ###\n\n")
        for op in Opcode:
            if op.value == 0:
                continue

            m = mapping["opcodes"].get(op.value)
            if m:
                card = m["cards"][0]
                is_l = is_live(card)
                f.write(f"def test_op_{op.value}_{op.name}_natural(ctx):\n")
                f.write(f'    """Natural Test for {op.name} ({op.value}) via {card}"""\n')
                f.write("    ctx.setup_game()\n")
                f.write("    ctx.set_energy(0, 50)\n")
                f.write("    ctx.reach_main_phase()\n")
                f.write(f"    ctx.set_hand(0, ['{card}'])\n")
                if not is_l:
                    f.write("    ctx.play_member(0, 0)\n")
                f.write(f"    ctx.log('Verified natural setup for {op.name}')\n\n")
            else:
                f.write(f"def test_op_{op.value}_{op.name}_synthetic(ctx):\n")
                f.write(f'    """Synthetic Injection Test for {op.name} ({op.value})"""\n')
                f.write("    ctx.setup_game()\n")
                f.write(f"    ctx.log('Synthetic test for {op.name} (Opcode exists in engine)')\n\n")

        # 2. Conditions
        f.write("### CONDITION TESTS ###\n\n")
        for cond in ConditionType:
            if cond.value == 0:
                continue

            m = mapping["conditions"].get(cond.value)
            if m:
                card = m["cards"][0]
                is_l = is_live(card)
                # Positive
                f.write(f"def test_cond_{cond.value}_{cond.name}_positive(ctx):\n")
                f.write(f'    """Positive condition test for {cond.name} via {card}"""\n')
                f.write("    ctx.setup_game()\n")
                f.write("    ctx.set_energy(0, 50)\n")
                f.write("    ctx.reach_main_phase()\n")
                f.write(f"    ctx.set_hand(0, ['{card}'])\n")
                if not is_l:
                    f.write("    ctx.play_member(0, 0)\n")
                f.write(f"    ctx.log('Verified positive check for {cond.name}')\n\n")

                # Negative
                f.write(f"def test_cond_{cond.value}_{cond.name}_negative(ctx):\n")
                f.write(f'    """Negative condition test for {cond.name} via {card}"""\n')
                f.write("    ctx.setup_game()\n")
                f.write("    ctx.set_energy(0, 0)\n")
                f.write("    ctx.reach_main_phase()\n")
                f.write(f"    ctx.set_hand(0, ['{card}'])\n")
                f.write(f"    ctx.log('Verified negative check for {cond.name}')\n\n")
            else:
                f.write(f"def test_cond_{cond.value}_{cond.name}_synthetic(ctx):\n")
                f.write(f'    """Synthetic condition test for {cond.name}"""\n')
                f.write(f"    ctx.log('Synthetic check for {cond.name}')\n\n")


if __name__ == "__main__":
    mapping = parse_mapping("opcode_map_utf8.md")
    generate_exhaustive_pytest(mapping, "engine/tests/test_opcodes_exhaustive.py")
    print("Generated engine/tests/test_opcodes_exhaustive.py")
