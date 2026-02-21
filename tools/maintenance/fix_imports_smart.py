import os
import re


def fix_imports_in_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print(f"Skipping {filepath} (encoding error)")
        return

    new_lines = []
    modified = False

    # Symbols to move and their destination
    move_map = {
        "MemberCard": "engine.models.card",
        "LiveCard": "engine.models.card",
        "EnergyCard": "engine.models.card",
        "Ability": "engine.models.ability",
        "Effect": "engine.models.ability",
        "EffectType": "engine.models.ability",
        "TriggerType": "engine.models.ability",
        "Condition": "engine.models.ability",
        "ConditionType": "engine.models.ability",
        "TargetType": "engine.models.ability",
        "AbilityCostType": "engine.models.ability",
        "Cost": "engine.models.ability",
        "AbilityParser": "compiler.parser",
        "Phase": "engine.game.enums",
        "Group": "engine.models.enums",
        "Unit": "engine.models.enums",
        "HeartColor": "engine.models.enums",
    }

    for line in lines:
        # Check for: from engine.game.game_state import ...
        match = re.search(r"^from engine\.game\.game_state import (.+)", line)
        if match:
            imports_str = match.group(1).strip()
            # Handle potentially comma-separated imports
            imports = [i.strip() for i in imports_str.split(",")]

            kept = []
            moved = {}
            for imp in imports:
                if not imp:
                    continue
                if imp in move_map:
                    dest = move_map[imp]
                    if dest not in moved:
                        moved[dest] = []
                    moved[dest].append(imp)
                else:
                    kept.append(imp)

            if moved:
                modified = True
                if kept:
                    new_lines.append(f"from engine.game.game_state import {', '.join(kept)}\n")

                for dest, syms in moved.items():
                    new_lines.append(f"from {dest} import {', '.join(syms)}\n")
            else:
                new_lines.append(line)
            continue

        # Check for: from engine.models.ability import ... AbilityParser ...
        match_abi = re.search(r"^from engine\.models\.ability import (.+)", line)
        if match_abi:
            imports_str = match_abi.group(1).strip()
            imports = [i.strip() for i in imports_str.split(",")]

            kept = []
            moved_parser = False

            for imp in imports:
                if imp == "AbilityParser":
                    moved_parser = True
                else:
                    kept.append(imp)

            if moved_parser:
                modified = True
                if kept:
                    new_lines.append(f"from engine.models.ability import {', '.join(kept)}\n")
                new_lines.append("from compiler.parser import AbilityParser\n")
            else:
                new_lines.append(line)
            continue

        new_lines.append(line)

    if modified:
        print(f"Fixing {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)


def main():
    root_tests = "tests"
    for root, dirs, files in os.walk(root_tests):
        for filename in files:
            if filename.endswith(".py"):
                fix_imports_in_file(os.path.join(root, filename))


if __name__ == "__main__":
    main()
