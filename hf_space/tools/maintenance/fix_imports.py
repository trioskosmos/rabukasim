import os


def fix_imports_in_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping {filepath} (encoding error)")
        return

    original_content = content

    replacements = [
        # Base engine mappings
        ("from game.game_state", "from engine.game.game_state"),
        ("from game.ability", "from engine.models.ability"),
        ("from game.card", "from engine.models.card"),
        ("from game.player_state", "from engine.game.player_state"),
        ("from game.enums", "from engine.game.enums"),
        ("import game.game_state", "import engine.game.game_state"),
        # Sub-package mappings
        ("from game.models.card", "from engine.models.card"),
        ("from game.models.enums", "from engine.models.enums"),
        ("from game.models.ability", "from engine.models.ability"),
        # Specific classes
        ("from engine.models.ability import AbilityParser", "from compiler.parser import AbilityParser"),
        ("from game.ability import AbilityParser", "from compiler.parser import AbilityParser"),
        ("from game.parser import AbilityParser", "from compiler.parser import AbilityParser"),
        # Legacy relative imports
        ("from ..game.game_state", "from engine.game.game_state"),
    ]

    # Apply replacements
    for old, new in replacements:
        if old in content:
            # Check if we are replacing "from game.ability import AbilityParser"
            # and potentially leaving broken imports if it imported other things too.
            # Simple string replace is risky but usually efficient for these standard patterns.
            content = content.replace(old, new)

    # Fix double imports if any (e.g. if we replaced partial string)
    # Not needed with specific strings above.

    if content != original_content:
        print(f"Fixing {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


def main():
    root_tests = "tests"
    for root, dirs, files in os.walk(root_tests):
        for filename in files:
            if filename.endswith(".py"):
                fix_imports_in_file(os.path.join(root, filename))


if __name__ == "__main__":
    main()
