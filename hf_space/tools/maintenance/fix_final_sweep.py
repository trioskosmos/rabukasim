import os
import re


def fix_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping {filepath} (encoding error)")
        return

    original_content = content

    # 1. Fix Imports
    # from game.data_loader -> from engine.game.data_loader
    content = re.sub(r"from game\.data_loader", r"from engine.game.data_loader", content)
    content = re.sub(r"import game\.data_loader", r"import engine.game.data_loader", content)

    # from game.card_loader -> from engine.game.data_loader? (if exists)

    # from game.rules -> from engine.game.rules (unlikely but check)
    content = re.sub(r"from game\.rules", r"from engine.game.rules", content)  # if applicable

    # Fix import loops or mis-imports for AbilityParser if specific pattern
    # "from engine.models.ability import AbilityParser" is WRONG -> "from compiler.parser import AbilityParser"
    # This was handled by previous script but maybe missed simple regex cases

    # 2. Fix Schema: group="..." -> groups=["..."]
    # For MemberCard(...) and LiveCard(...) calls
    # Pattern: group="Value" -> groups=["Value"]
    # We must be careful not to replace search params in API calls, only in Card constructors
    # But usually tests instantiate cards directly.
    # Safe regex: group="([^"]+)" -> groups=["\1"]

    # We want to target lines that look like keyword args.
    # Limitation: This regex is simple. If group="A", unit="B"_ it works.
    content = re.sub(r'group="([^"]+)"', r'groups=["\1"]', content)
    content = re.sub(r"group='([^']+)'", r"groups=['\1']", content)

    # 3. Fix: group=Variable -> groups=[Variable]
    # This is harder to verify context, but let's look for group=some_var
    # Avoid applying if it's already groups=
    # This might be risky if 'group' is used for searchparams.
    # Let's inspect known failures: test_yell_colors.py uses Positional args for MemberCard!
    # MemberCard(101, "Blue Yeller", "Group", ...)
    # Wait, the signature of MemberCard has changed?
    # Let's check MemberCard definition in engine/models/card.py first.

    if content != original_content:
        print(f"Fixing {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


def main():
    root_tests = "tests"
    for root, dirs, files in os.walk(root_tests):
        for filename in files:
            if filename.endswith(".py"):
                fix_file(os.path.join(root, filename))


if __name__ == "__main__":
    main()
